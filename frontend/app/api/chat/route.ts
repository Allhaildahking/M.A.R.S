import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

async function readJson(response: Response): Promise<unknown | null> {
  const raw = await response.text();
  if (!raw) return null;
  try {
    return JSON.parse(raw) as unknown;
  } catch {
    return null;
  }
}

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
      { error: "MARS backend could not be reached. Check the backend deployment." },
      { status: 502 },
    );
  }

  const responseBody = await readJson(upstream);
  if (!upstream.ok) {
    const detail =
      typeof responseBody === "object" &&
      responseBody !== null &&
      "detail" in responseBody &&
      typeof responseBody.detail === "string"
        ? responseBody.detail
        : `MARS backend returned a non-JSON or unrecognised error (HTTP ${upstream.status}).`;
    return NextResponse.json({ error: detail }, { status: upstream.status });
  }

  if (typeof responseBody !== "object" || responseBody === null) {
    return NextResponse.json(
      { error: `MARS backend returned an invalid response (HTTP ${upstream.status}).` },
      { status: 502 },
    );
  }

  const answer =
    "answer" in responseBody && typeof responseBody.answer === "string"
      ? responseBody.answer
      : "response" in responseBody
        ? responseBody.response
        : undefined;
  if (typeof answer !== "string") {
    return NextResponse.json(
      { error: "MARS backend returned an unexpected response shape." },
      { status: 502 },
    );
  }

  return NextResponse.json({
    answer,
    conversation_id:
      "conversation_id" in responseBody ? responseBody.conversation_id ?? null : null,
    provider:
      "provider" in responseBody && typeof responseBody.provider === "string"
        ? responseBody.provider
        : "unknown",
  });
}
