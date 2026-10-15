const API_URL = process.env.CHAT_API_URL ?? "http://localhost:8000";

export async function GET() {
  try {
    const upstream = await fetch(`${API_URL}/api/providers`, {
      signal: AbortSignal.timeout(15_000),
      cache: "no-store",
    });
    if (!upstream.ok) {
      return Response.json({ providers: [], default: null }, { status: 502 });
    }
    return Response.json(await upstream.json());
  } catch {
    return Response.json({ providers: [], default: null }, { status: 503 });
  }
}
