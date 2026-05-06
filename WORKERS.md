# Lab 17 - Cloudflare Workers Edge Deployment

## 1. Deployment Summary

Worker project:
- Source: `edge-api/`
- Worker name: `devops-core-edge-api`
- Public URL: `https://devops-core-edge-api.oleynik-moak.workers.dev`
- Runtime: Cloudflare Workers, TypeScript, Wrangler

Main routes:
- `GET /` - app, course, environment, route list, timestamp
- `GET /health` - health status
- `GET /edge` - edge metadata from `request.cf`
- `GET /config` - plaintext configuration and secret configuration status
- `GET /counter` - persisted KV visit counter
- `GET /settings` - persisted KV value
- `POST /settings` - write a persisted KV value

Configuration:
- Plaintext vars in `edge-api/wrangler.jsonc`: `APP_NAME`, `COURSE_NAME`, `ENVIRONMENT`
- Secrets expected in Cloudflare: `API_TOKEN`, `ADMIN_EMAIL`
- KV binding: `SETTINGS`
- `workers_dev: true` enables the required `workers.dev` URL.

Plaintext variables are visible in the committed Wrangler configuration, so they are suitable only for non-sensitive settings. Secret values must be created with `wrangler secret put`; they are injected into the Worker environment and must not be committed to Git.

## 2. Evidence

Local validation completed on 2026-05-06:

```bash
cd edge-api
npm run check
npx wrangler deploy --dry-run
npx wrangler dev --ip 127.0.0.1 --port 8787
```

Cloudflare authentication and remote resource status in this workspace:

```bash
npx wrangler whoami
# Logged in as oleynik.moak@gmail.com

npx wrangler secret list
# ADMIN_EMAIL secret_text
# API_TOKEN secret_text

npx wrangler deploy --dry-run
# env.SETTINGS (cd4645e1da974785ad22515fecb94256) KV Namespace
```

The Worker code, KV namespace binding, two Cloudflare secrets, and `workers.dev` public route are ready.

Successful production deploy:

```text
Uploaded devops-core-edge-api
Deployed devops-core-edge-api triggers
https://devops-core-edge-api.oleynik-moak.workers.dev
Current Version ID: ae617661-e5f7-417b-85f6-8ea7dea3a3b8
```

Local endpoint evidence:

```bash
curl -i http://127.0.0.1:8787/health
# HTTP/1.1 200 OK
# {"status":"ok","app":"devops-core-edge-api","environment":"lab17","timestamp":"2026-05-06T14:56:24.353Z"}

curl -i http://127.0.0.1:8787/edge
# HTTP/1.1 200 OK
# {"app":"devops-core-edge-api","colo":"ARN","country":"RU","city":"Kazan","asn":197765,"httpProtocol":"HTTP/1.1","tlsVersion":"TLSv1.3","timezone":"Europe/Moscow"}

curl -i http://127.0.0.1:8787/counter
# HTTP/1.1 200 OK
# {"key":"visits","visits":1,"persistedBy":"Workers KV"}

curl -i -X POST http://127.0.0.1:8787/settings \
  -H 'content-type: application/json' \
  -d '{"value":"Lab 17 persistent value"}'
# HTTP/1.1 201 Created
# {"key":"lab17-message","value":"Lab 17 persistent value","persistedBy":"Workers KV"}

curl -i http://127.0.0.1:8787/settings
# HTTP/1.1 200 OK
# {"key":"lab17-message","value":"Lab 17 persistent value"}
```

Expected deployed route checks:

```bash
curl https://devops-core-edge-api.oleynik-moak.workers.dev/health
curl https://devops-core-edge-api.oleynik-moak.workers.dev/edge
curl https://devops-core-edge-api.oleynik-moak.workers.dev/counter
curl -X POST https://devops-core-edge-api.oleynik-moak.workers.dev/settings \
  -H 'content-type: application/json' \
  -d '{"value":"Lab 17 persistent value"}'
curl https://devops-core-edge-api.oleynik-moak.workers.dev/settings
```

Production `/health` response:

```json
{
  "status": "ok",
  "app": "devops-core-edge-api",
  "environment": "lab17",
  "timestamp": "2026-05-06T15:16:38.686Z"
}
```

Production `/edge` response:

```json
{
  "app": "devops-core-edge-api",
  "colo": "FRA",
  "country": "DE",
  "city": "Frankfurt am Main",
  "asn": 20473,
  "httpProtocol": "HTTP/2",
  "tlsVersion": "TLSv1.3",
  "timezone": "Europe/Berlin"
}
```

The concrete values depend on the requester and Cloudflare colo. This response proves Cloudflare supplies fields such as `colo`, `country`, `asn`, protocol, and TLS version at the edge.

Production `/config` response confirmed both secrets are configured:

```json
{
  "app": "devops-core-edge-api",
  "course": "DevOps Core",
  "environment": "lab17",
  "secrets": {
    "API_TOKEN": "configured",
    "ADMIN_EMAIL": "configured"
  }
}
```

KV persistence verification:

```text
POST /settings -> {"key":"lab17-message","value":"Lab 17 persisted through redeploy","persistedBy":"Workers KV"}
npx wrangler deploy -> Current Version ID: ae617661-e5f7-417b-85f6-8ea7dea3a3b8
GET /settings  -> {"key":"lab17-message","value":"Lab 17 persisted through redeploy"}
GET /counter   -> {"key":"visits","visits":2,"persistedBy":"Workers KV"}
```

Production log evidence from `npx wrangler tail devops-core-edge-api --format pretty`:

```text
GET https://devops-core-edge-api.oleynik-moak.workers.dev/edge - Ok @ 5/6/2026, 6:17:40 PM
  (log) request { method: 'GET', path: '/edge', colo: 'FRA', country: 'DE' }
GET https://devops-core-edge-api.oleynik-moak.workers.dev/health - Ok @ 5/6/2026, 6:17:40 PM
  (log) request { method: 'GET', path: '/health', colo: 'FRA', country: 'DE' }
```

Metrics to capture in the Cloudflare dashboard:
- Worker request count
- Error count
- Invocation duration or CPU time

Deployment history / rollback commands:

```bash
npx wrangler deployments list
npx wrangler rollback
```

Deployment history observed in Cloudflare:

```text
2026-05-06T15:06:41.312Z Upload        version 886fc3c4-b7e6-427f-8ae4-4e3ab194883f
2026-05-06T15:06:44.213Z Secret Change version 5ea733ba-21ee-417a-b57c-edb2e1a41540
2026-05-06T15:06:55.220Z Secret Change version 4f9252c3-3349-4da4-8d7f-5ff67eb7d73b
2026-05-06T15:07:20.112Z Deployment    version 52d74f3c-bbed-4362-8810-9196efaf43eb
2026-05-06T15:17:07.068Z Deployment    version ae617661-e5f7-417b-85f6-8ea7dea3a3b8
```

For grading evidence, add screenshots or terminal captures after deployment:
- Cloudflare Worker dashboard overview
- `/edge` JSON response
- `wrangler tail` log line or dashboard logs
- deployment history from `npx wrangler deployments list`

Dashboard screenshots:
- Account metrics: `edge-api/docs/screenshots/lab17-account-metrics.png`
- Worker overview, route, metrics, logs, and KV binding: `edge-api/docs/screenshots/lab17-worker-overview.png`

## 3. Kubernetes vs Cloudflare Workers

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|--------------------|
| Setup complexity | Requires cluster, manifests or Helm, networking, ingress, RBAC, and resource management. | Requires account, Worker project, Wrangler config, and bindings. |
| Deployment speed | Usually slower because images must be built, pushed, scheduled, and rolled out. | Usually fast because code is deployed directly to the Workers edge runtime. |
| Global distribution | You choose and operate regions or clusters yourself. | Cloudflare automatically runs the Worker across its global edge network. |
| Cost for small apps | Can be expensive because clusters and nodes exist even with little traffic. | Usually cheaper for small APIs because there is no always-on VM or node pool. |
| State/persistence model | StatefulSets, PVCs, databases, object storage, and external managed services. | Bindings such as KV, Durable Objects, D1, R2, and external APIs. |
| Control/flexibility | High control over runtime, containers, networking, sidecars, and long-running workloads. | More constrained runtime with limits and no arbitrary Docker container hosting. |
| Best use case | Complex services, custom runtimes, internal platforms, long-running workloads. | Lightweight globally distributed HTTP APIs, edge logic, auth gates, redirects, and low-latency reads. |

## 4. When to Use Each

Use Kubernetes when the application needs custom containers, background workers, advanced networking, service meshes, persistent volumes, or a platform for many internal services.

Use Cloudflare Workers when the workload is an HTTP-oriented edge API, request transformation, authentication/authorization middleware, webhook receiver, cache-aware endpoint, or globally distributed lightweight service.

My recommendation for this lab API is Cloudflare Workers: it is small, stateless except for KV, and benefits from a public global edge endpoint without cluster operations.

## 5. Reflection

Workers felt easier than Kubernetes because there is no cluster bootstrap, no Docker image build, no node sizing, and no manual region selection.

Workers felt more constrained because it is not a Docker host. The app must fit the Workers runtime, and persistence must be accessed through Cloudflare bindings or external services instead of local disks or arbitrary containers.

Because Workers is not a Docker host, the Lab 2 image is not deployed here. The operational concerns are preserved in a Workers-native way: routes, health checks, config, secrets, persistence, logs, deployment history, and a public URL.

## 6. Commands Used

```bash
cd edge-api
npm install
npm run check
npx wrangler login
npx wrangler whoami
npx wrangler kv namespace create SETTINGS
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
npx wrangler deploy
npx wrangler deployments list
npx wrangler tail
```
