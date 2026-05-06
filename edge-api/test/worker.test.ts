import assert from "node:assert/strict";
import test from "node:test";
import worker, { type Env } from "../src/index.js";

class MemoryKV {
  private readonly values = new Map<string, string>();

  async get(key: string): Promise<string | null> {
    return this.values.get(key) ?? null;
  }

  async put(key: string, value: string): Promise<void> {
    this.values.set(key, value);
  }

  async delete(key: string): Promise<void> {
    this.values.delete(key);
  }

  async list() {
    return {
      keys: [...this.values.keys()].map((name) => ({ name })),
      list_complete: true,
      cacheStatus: null,
    };
  }

  async getWithMetadata() {
    return {
      value: null,
      metadata: null,
      cacheStatus: null,
    };
  }
}

function makeEnv(): Env {
  return {
    APP_NAME: "devops-core-edge-api",
    COURSE_NAME: "DevOps Core",
    ENVIRONMENT: "test",
    API_TOKEN: "test-token",
    ADMIN_EMAIL: "admin@example.com",
    SETTINGS: new MemoryKV() as unknown as KVNamespace,
  };
}

async function jsonResponse(path: string, env = makeEnv(), init?: RequestInit) {
  const response = await worker.fetch(new Request(`https://example.test${path}`, init), env);
  return {
    response,
    body: (await response.json()) as Record<string, unknown>,
  };
}

test("health endpoint returns ok JSON", async () => {
  const { response, body } = await jsonResponse("/health");

  assert.equal(response.status, 200);
  assert.equal(body.status, "ok");
  assert.equal(body.app, "devops-core-edge-api");
});

test("edge endpoint exposes Cloudflare metadata fields with local fallbacks", async () => {
  const { response, body } = await jsonResponse("/edge");

  assert.equal(response.status, 200);
  assert.equal(body.colo, "local-dev");
  assert.equal(body.country, "local-dev");
  assert.ok("asn" in body);
  assert.ok("httpProtocol" in body);
});

test("counter persists increments through KV binding", async () => {
  const env = makeEnv();
  const first = await jsonResponse("/counter", env);
  const second = await jsonResponse("/counter", env);

  assert.equal(first.body.visits, 1);
  assert.equal(second.body.visits, 2);
});

test("settings endpoint stores and reads a KV value", async () => {
  const env = makeEnv();
  const write = await jsonResponse("/settings", env, {
    method: "POST",
    body: JSON.stringify({ value: "Lab 17 persistent value" }),
    headers: { "content-type": "application/json" },
  });
  const read = await jsonResponse("/settings", env);

  assert.equal(write.response.status, 201);
  assert.equal(read.response.status, 200);
  assert.equal(read.body.value, "Lab 17 persistent value");
});

test("unknown routes return 404", async () => {
  const { response, body } = await jsonResponse("/missing");

  assert.equal(response.status, 404);
  assert.equal(body.error, "Not Found");
});
