export interface Env {
  APP_NAME: string;
  COURSE_NAME: string;
  ENVIRONMENT: string;
  API_TOKEN?: string;
  ADMIN_EMAIL?: string;
  SETTINGS: KVNamespace;
}

type JsonBody = Record<string, unknown>;

function json(body: JsonBody, init: ResponseInit = {}): Response {
  return Response.json(body, {
    headers: {
      "cache-control": "no-store",
      ...init.headers,
    },
    status: init.status,
    statusText: init.statusText,
  });
}

function secretStatus(value: string | undefined): "configured" | "missing" {
  return value ? "configured" : "missing";
}

async function incrementCounter(env: Env): Promise<Response> {
  const key = "visits";
  const raw = await env.SETTINGS.get(key);
  const previous = Number.parseInt(raw ?? "0", 10);
  const visits = Number.isFinite(previous) ? previous + 1 : 1;

  await env.SETTINGS.put(key, String(visits));

  return json({
    key,
    visits,
    persistedBy: "Workers KV",
  });
}

async function readStoredMessage(env: Env): Promise<Response> {
  const key = "lab17-message";
  const value = await env.SETTINGS.get(key);

  if (!value) {
    return json(
      {
        key,
        value: null,
        hint: "Store a value with POST /settings first.",
      },
      { status: 404 },
    );
  }

  return json({ key, value });
}

async function writeStoredMessage(request: Request, env: Env): Promise<Response> {
  let payload: { value?: unknown };

  try {
    payload = (await request.json()) as { value?: unknown };
  } catch {
    return json({ error: "Request body must be JSON." }, { status: 400 });
  }

  if (typeof payload.value !== "string" || payload.value.trim().length === 0) {
    return json({ error: "Field 'value' must be a non-empty string." }, { status: 400 });
  }

  const key = "lab17-message";
  await env.SETTINGS.put(key, payload.value.trim());

  return json({ key, value: payload.value.trim(), persistedBy: "Workers KV" }, { status: 201 });
}

async function handleRequest(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  const cf = request.cf;

  console.log("request", {
    method: request.method,
    path: url.pathname,
    colo: cf?.colo,
    country: cf?.country,
  });

  if (request.method === "GET" && url.pathname === "/") {
    return json({
      app: env.APP_NAME,
      course: env.COURSE_NAME,
      environment: env.ENVIRONMENT,
      message: "Hello from Cloudflare Workers",
      routes: ["/", "/health", "/edge", "/counter", "/settings"],
      timestamp: new Date().toISOString(),
    });
  }

  if (request.method === "GET" && url.pathname === "/health") {
    return json({
      status: "ok",
      app: env.APP_NAME,
      environment: env.ENVIRONMENT,
      timestamp: new Date().toISOString(),
    });
  }

  if (request.method === "GET" && url.pathname === "/edge") {
    return json({
      app: env.APP_NAME,
      colo: cf?.colo ?? "local-dev",
      country: cf?.country ?? "local-dev",
      city: cf?.city ?? null,
      asn: cf?.asn ?? null,
      httpProtocol: cf?.httpProtocol ?? null,
      tlsVersion: cf?.tlsVersion ?? null,
      timezone: cf?.timezone ?? null,
    });
  }

  if (request.method === "GET" && url.pathname === "/config") {
    return json({
      app: env.APP_NAME,
      course: env.COURSE_NAME,
      environment: env.ENVIRONMENT,
      secrets: {
        API_TOKEN: secretStatus(env.API_TOKEN),
        ADMIN_EMAIL: secretStatus(env.ADMIN_EMAIL),
      },
      note: "Plaintext vars are committed in wrangler.jsonc; secrets are injected by Cloudflare and are not stored in Git.",
    });
  }

  if (request.method === "GET" && url.pathname === "/counter") {
    return incrementCounter(env);
  }

  if (request.method === "GET" && url.pathname === "/settings") {
    return readStoredMessage(env);
  }

  if (request.method === "POST" && url.pathname === "/settings") {
    return writeStoredMessage(request, env);
  }

  return json(
    {
      error: "Not Found",
      path: url.pathname,
    },
    { status: 404 },
  );
}

export default {
  fetch(request: Request, env: Env): Promise<Response> {
    return handleRequest(request, env);
  },
};
