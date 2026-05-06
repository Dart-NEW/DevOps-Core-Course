# Lab 18 - Reproducible Builds with Nix

## Environment

Host platform:

```text
Linux McLaren 6.17.0-23-generic x86_64 GNU/Linux
Docker 29.4.0
```

Host Nix status:

```text
$ nix --version
nix: command not found

$ sudo -n true
sudo: a password is required
```

Because host-level Nix installation requires sudo and `/nix`, the lab was executed with the official `nixos/nix` Docker image. This still uses real Nix builds, Nix store paths, `nix-build`, `dockerTools`, and flakes, without modifying the host system.

```bash
docker run --rm nixos/nix:latest nix --version
# nix (Nix) 2.34.7
```

Persistent Nix runner used for reproducibility checks:

```bash
docker create --name lab18-nix \
  -v "$PWD":/work \
  -w /work/labs/lab18/app_python \
  nixos/nix:latest sleep infinity
docker start lab18-nix
```

## Task 1 - Reproducible Python App

The Lab 1 Python app was copied to:

```text
labs/lab18/app_python/
```

Important files:

```text
app.py
requirements.txt
Dockerfile
default.nix
docker.nix
flake.nix
flake.lock
```

### `default.nix`

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.python313Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";

  propagatedBuildInputs = with pkgs.python313Packages; [
    flask
    prometheus-client
    distro
  ];

  nativeBuildInputs = [
    pkgs.makeWrapper
  ];

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/share/devops-info-service
    cp app.py $out/share/devops-info-service/app.py

    makeWrapper ${pkgs.python313}/bin/python $out/bin/devops-info-service \
      --add-flags "$out/share/devops-info-service/app.py" \
      --prefix PYTHONPATH : "$PYTHONPATH" \
      --set PYTHONUNBUFFERED 1

    runHook postInstall
  '';
}
```

Field notes:

| Field | Meaning |
|---|---|
| `python313Packages.buildPythonApplication` | Builds the app with a Nix-managed Python 3.13 dependency set. |
| `pname` / `version` | Stable package identity used in the store path name. |
| `src = ./.` | Uses the copied Lab 1 app directory as source. |
| `format = "other"` | The app has no `setup.py` or `pyproject.toml`. |
| `propagatedBuildInputs` | Runtime Python dependencies: Flask, Prometheus client, and distro. |
| `makeWrapper` | Creates a runnable `devops-info-service` command that invokes the pinned Python interpreter. |

### Build and Run

```bash
docker exec lab18-nix sh -lc 'nix-build --option sandbox false'
```

Final reproducibility check:

```text
path1=/nix/store/g0163dlpih15sw1x0prxwyfz2k67fqzk-devops-info-service-1.0.0
path2=/nix/store/g0163dlpih15sw1x0prxwyfz2k67fqzk-devops-info-service-1.0.0
hash1=53b78e5dcf0758575409b3134931c108f4b3e01c9b25471dea109b37cb50a008
hash2=53b78e5dcf0758575409b3134931c108f4b3e01c9b25471dea109b37cb50a008
```

The same expression produced the same store path and output hash across repeated builds.

The app also ran successfully from the Nix build:

```text
HTTP/1.1 200 OK
Server: Werkzeug/3.1.4 Python/3.13.11

{
  "status": "healthy",
  "timestamp": "2026-05-06T15:57:36.315972+00:00",
  "uptime_seconds": 1
}
```

### Store Path Format

Example:

```text
/nix/store/g0163dlpih15sw1x0prxwyfz2k67fqzk-devops-info-service-1.0.0
```

Meaning:

| Part | Meaning |
|---|---|
| `/nix/store` | Nix's immutable package store. |
| `g0163dlp...` | Hash derived from build inputs, dependencies, source, and build instructions. |
| `devops-info-service` | Package name from `pname`. |
| `1.0.0` | Package version. |

Same inputs produce the same hash and same store path. If source code, dependencies, or build instructions change, Nix creates a new store path instead of mutating the old one.

### Pip vs Nix

Quick unpinned pip test:

```text
requirements-unpinned.txt: flask
freeze1=Flask==3.1.3
freeze2=Flask==3.1.3
```

Both runs happened minutes apart, so they resolved the same current Flask version. The important limitation remains: `flask` without a lock or hash means "latest compatible version at install time." Over time, or on machines with different Python versions, the resulting environment can drift.

| Aspect | Lab 1 pip + venv | Lab 18 Nix |
|---|---|---|
| Python version | Depends on host or image | Pinned by nixpkgs |
| Direct dependencies | Can be pinned in `requirements.txt` | Pinned by nixpkgs revision |
| Transitive dependencies | Resolved by pip at install time | Locked in Nix closure |
| Build isolation | Virtualenv only | Nix sandbox and store closure |
| Binary cache | No content-addressed package cache | Yes, cacheable by store path |
| Rebuild result | Environment can drift | Same inputs give same path/hash |

Reflection: If Lab 1 had used Nix from the start, every student and CI runner would get the same Python version and dependency closure, instead of relying on whatever Python/pip resolver state happened to exist locally.

## Task 2 - Reproducible Docker Images

### Lab 2 Dockerfile

The traditional Lab 2 image uses:

```dockerfile
FROM python:3.13-slim AS builder
...
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
...
FROM python:3.13-slim
...
CMD ["python", "app.py"]
```

This is a good Dockerfile for ordinary containerization, but it still depends on mutable external inputs such as a base image tag and `pip install` at build time.

### `docker.nix`

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [
    app
  ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    Env = [
      "HOST=0.0.0.0"
      "PORT=5000"
      "PYTHONUNBUFFERED=1"
    ];
    ExposedPorts = {
      "5000/tcp" = {};
    };
    WorkingDir = "/";
  };

  created = "1970-01-01T00:00:01Z";
}
```

Key point: the image uses the exact Nix-built app derivation and a fixed creation timestamp. It has no Docker base image.

### Nix Image Build

```text
docker_store=/nix/store/b00jf1cwqwdq71blaczr67rqgsyz0chf-devops-info-service-nix.tar.gz
sha256=29b06db11d32efb18aa56ce17fecdf178d7b8c5aaddd29c3ab06d681cb4bbd5e
compressed tarball size=77M
Docker image size=187MB
created=1970-01-01T00:00:01Z
```

Repeated Nix Docker builds:

```text
docker_hash1=29b06db11d32efb18aa56ce17fecdf178d7b8c5aaddd29c3ab06d681cb4bbd5e
docker_hash2=29b06db11d32efb18aa56ce17fecdf178d7b8c5aaddd29c3ab06d681cb4bbd5e
```

The tarball is bit-for-bit identical.

### Traditional Docker Rebuild Comparison

Two no-cache Lab 2 Docker builds:

```text
nocache1 created=2026-05-06T18:51:48.041405975+03:00 size=133612956
docker save hash=00836609f5d75fa88b8171185b4dfd325cc3b4dacb90a7a5ea3d74a95ab89881

nocache2 created=2026-05-06T18:51:59.475240507+03:00 size=133612956
docker save hash=c222ae1457a2ada0e9a06b328f99a49ac9e6cd6669253ae92c73c659edee3ae3
```

The application source did not change, but timestamps and rebuild-time layers produced different saved image hashes.

### Runtime Comparison

Containers were run side by side using different host ports because port 5000 was already in use:

```bash
docker run -d -p 5002:5000 --name lab2-container lab2-app:nocache1
docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0
```

Both health endpoints worked:

```text
Lab 2 container:
HTTP/1.1 200 OK
Server: Werkzeug/3.1.8 Python/3.13.13

Nix container:
HTTP/1.1 200 OK
Server: Werkzeug/3.1.4 Python/3.13.11
```

The Python patch versions differ because the traditional image uses the current `python:3.13-slim` base, while Nix uses the pinned Python from nixpkgs.

### Image and Layer Comparison

```text
lab2-app:nocache1                 134MB
devops-info-service-nix:1.0.0     187MB
```

The Nix image is larger in this specific run because the app closure includes full Nix store paths for Python and runtime libraries. The benefit is not size here; it is deterministic construction and exact dependency auditing.

Traditional Docker history excerpt:

```text
CREATED         CREATED BY
6 minutes ago   CMD ["python" "app.py"]
6 minutes ago   HEALTHCHECK ...
6 minutes ago   COPY /opt/venv /opt/venv
6 minutes ago   RUN useradd -m -u 1000 appuser
```

Nix Docker history excerpt:

```text
CREATED   CREATED BY   COMMENT
N/A                    store paths: ['/nix/store/ylklim4w...-customisation-layer']
N/A                    store paths: ['/nix/store/g0163...-devops-info-service-1.0.0']
N/A                    store paths: ['/nix/store/pni2...-python3.13-flask-3.1.2']
N/A                    store paths: ['/nix/store/0z5s...-python3.13-werkzeug-3.1.4']
```

Why traditional Dockerfiles cannot easily achieve bit-for-bit reproducibility:

- base image tags can move unless pinned by digest;
- `RUN pip install` resolves packages at build time;
- image metadata and layer timestamps vary;
- build context and cache behavior affect output;
- OS package repositories change over time.

Nix improves this by building from immutable store paths with a fixed timestamp and a declared closure.

Practical scenarios where this matters:

- CI/CD promotion where the exact artifact must be rebuilt after audit;
- security incident response where dependency versions must be proven;
- rollback where the previous artifact must be reconstructed exactly;
- regulated environments where build provenance matters.

## Bonus - Nix Flakes

### `flake.nix`

```nix
{
  description = "DevOps Info Service - reproducible Nix build for Lab 18";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system} = {
        default = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix { inherit pkgs; };
      };

      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python313
          python313Packages.flask
          python313Packages.prometheus-client
          python313Packages.distro
          python313Packages.pytest
          python313Packages.pytest-cov
        ];
      };
    };
}
```

### `flake.lock` Evidence

```json
{
  "locked": {
    "lastModified": 1778003029,
    "narHash": "sha256-q/nkKLDtHIyLjZpKhWk3cSK5IYsFqtMd6UtXF3ddjgA=",
    "owner": "NixOS",
    "repo": "nixpkgs",
    "rev": "0c88e1f2bdb93d5999019e99cb0e61e1fe2af4c5",
    "type": "github"
  },
  "original": {
    "ref": "nixos-25.11"
  }
}
```

The lock file pins the exact nixpkgs revision and NAR hash.

Flake builds were executed with `path:` because untracked files inside a Git repository are invisible to flakes until committed:

```bash
nix --extra-experimental-features "nix-command flakes" \
  build path:/work/labs/lab18/app_python

nix --extra-experimental-features "nix-command flakes" \
  build path:/work/labs/lab18/app_python#dockerImage
```

Outputs:

```text
FLAKE_APP=/nix/store/fvn1sdnbvb6kp44zcxw58b915i64qmk8-devops-info-service-1.0.0
FLAKE_DOCKER=/nix/store/dkgwqq2r7md4i0vd6g3x86g5wmqz9jhb-devops-info-service-nix.tar.gz
flake docker hash=fb9fcaecd4be18091bd460217bea643dbd99fc78ab109f1b3d56f07200c6cf8c
```

### Dev Shell

```text
$ nix develop path:/work/labs/lab18/app_python --command python --version
Python 3.13.12

$ nix develop path:/work/labs/lab18/app_python --command python -c "import flask; print(flask.__version__)"
3.1.2
```

Compared with Lab 1's `venv`, `nix develop` gives the same Python and dependency closure to everyone who uses the same `flake.lock`.

### Lab 10 Helm vs Flakes

| Aspect | Lab 10 Helm values | Lab 18 Flakes |
|---|---|---|
| Pins image tag | Yes | Can consume a reproducible Nix-built image |
| Pins Python version | No | Yes |
| Pins transitive dependencies | No | Yes |
| Pins build tools | No | Yes |
| Protects against mutable tags | Only if using digests | Yes, via locked inputs and store paths |
| Dev environment | No | Yes, via `nix develop` |

Best combined approach:

1. Build the image with Nix.
2. Push it by immutable digest.
3. Reference that digest in Helm values.

That combines Helm's Kubernetes deployment model with Nix's reproducible artifact model.

## Final Result

- Task 1 completed: Python app builds with Nix and repeated builds produce identical store paths and hashes.
- Task 2 completed: Docker image builds with `dockerTools`, runs successfully, and repeated tarball builds are identical.
- Bonus completed: `flake.nix`, `flake.lock`, flake builds, and dev shell are present and tested.

Files to review:

```text
labs/lab18/app_python/default.nix
labs/lab18/app_python/docker.nix
labs/lab18/app_python/flake.nix
labs/lab18/app_python/flake.lock
labs/submission18.md
```
