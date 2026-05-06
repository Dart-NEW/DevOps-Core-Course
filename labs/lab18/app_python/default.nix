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

  meta = with pkgs.lib; {
    description = "DevOps Info Service packaged as a reproducible Nix derivation";
    mainProgram = "devops-info-service";
    platforms = platforms.linux;
  };
}
