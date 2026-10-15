// BACKEND_URL is injected by the Vercel service binding; the fallback is for local development.
const API_URL = process.env.BACKEND_URL ?? process.env.CHAT_API_URL ?? "http://localhost:8000";
const MAX_BODY_BYTES = 100_000;

export async function POST(request: Request) {
  const raw = await request.text();
  if (raw.length > MAX_BODY_BYTES) {
    return Response.json({ detail: "Request is too large." }, { status: 413 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${API_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: raw,
      signal: AbortSignal.timeout(90_000),
      cache: "no-store",
    });
  } catch {
    return Response.json(
      { detail: "The chat service is unavailable right now." },
      { status: 503 },
    );
  }

  const body = await upstream.json().catch(() => null);
  if (upstream.ok && body && typeof body.reply === "string") {
    return Response.json({ reply: body.reply });
  }

  const detail =
    body && typeof body.detail === "string"
      ? body.detail
      : "The request could not be processed.";
  return Response.json({ detail }, { status: upstream.status >= 500 ? 502 : upstream.status });
}
