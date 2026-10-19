import { NextResponse } from "next/server";

export const runtime = "nodejs";

export async function GET() {
  const apiUrl = process.env.MARS_API_URL;
  if (!apiUrl) {
    return NextResponse.json(
      { status: "disconnected", service: "mars-api" },
      { status: 503 },
    );
  }

  try {
    const response = await fetch(new URL("/health", apiUrl), { cache: "no-store" });
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      return NextResponse.json(
        { status: "unavailable", service: "mars-api" },
        { status: 503 },
      );
    }
    return NextResponse.json(body);
  } catch {
    return NextResponse.json(
      { status: "unavailable", service: "mars-api" },
      { status: 503 },
    );
  }
}
