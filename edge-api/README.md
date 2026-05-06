# DevOps Core Edge API

Cloudflare Workers API for Lab 17.

## Routes

- `GET /` - deployment information and route list
- `GET /health` - health check
- `GET /edge` - Cloudflare request metadata such as colo, country, ASN, protocol, and TLS version
- `GET /config` - plaintext variable values plus secret configuration status
- `GET /counter` - KV-backed visit counter
- `GET /settings` - read a persisted KV value
- `POST /settings` - store a persisted KV value with JSON body `{"value":"..."}`

## Local Commands

```bash
npm install
npm run check
npm run dev
```

## Cloudflare Commands

```bash
npx wrangler login
npx wrangler whoami
npx wrangler kv namespace create SETTINGS
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
npx wrangler deploy
npx wrangler deployments list
npx wrangler tail
```

Replace the placeholder KV namespace ID in `wrangler.jsonc` before deploying.
