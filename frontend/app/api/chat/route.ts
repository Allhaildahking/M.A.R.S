import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  let payload: unknown;

  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ error: "Request body must be valid JSON." }, { status: 400 });
  }

  if (
    typeof payload !== "object" ||
    payload === null ||
    typeof (payload as { message?: unknown }).message !== "string"
  ) {
    return NextResponse.json({ error: "A message is required." }, { status: 400 });
  }

  const message = (payload as { message: string }).message.trim();
  if (!message || message.length > 8000) {
    return NextResponse.json(
      { error: "Message must contain 1 to 8000 characters." },
      { status: 400 },
    );
  }

  const apiUrl = process.env.MARS_API_URL;
  const apiToken = process.env.MARS_API_TOKEN;

  if (!apiUrl || !apiToken) {
    return NextResponse.json(
      { error: "MARS API is not configured for this deployment." },
      { status: 503 },
    );
  }

  const body = payload as { conversation_id?: unknown; mode?: unknown };
  const mode = body.mode === "dev" ? "dev" : "standard";
  let upstream: Response;
  try {
    upstream = await fetch(new URL("/v1/chat", apiUrl), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiToken}`,
      },
      body: JSON.stringify({
        message,
        mode,
        conversation_id:
          typeof body.conversation_id === "string" ? body.conversation_id : null,
      }),
      cache: "no-store",
    });
  } catch {
    return NextResponse.json(
      { error: "MARS backend could not be reached." },
      { status: 502 },
    );
  }

  const responseBody = await upstream.json().catch(() => null);
  if (!upstream.ok) {
    const detail =
      typeof responseBody?.detail === "string"
        ? responseBody.detail
        : "MARS could not complete the request.";
    return NextResponse.json({ error: detail }, { status: upstream.status });
  }

  return NextResponse.json(responseBody, { status: 200 });
}
