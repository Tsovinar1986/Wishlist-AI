import { NextRequest, NextResponse } from "next/server";
import { AUTH_COOKIE_NAME, AUTH_COOKIE_MAX_AGE, getBackendUrl } from "@/lib/auth-cookie";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, password } = body;
    if (!email || !password) {
      return NextResponse.json(
        { error: "Email and password required" },
        { status: 400 }
      );
    }
    const backend = getBackendUrl();
    if (process.env.NODE_ENV === "production" && (!backend || backend.includes("localhost"))) {
      return NextResponse.json(
        { error: "Backend not configured. Set NEXT_PUBLIC_API_URL in Vercel." },
        { status: 503 }
      );
    }
    const res = await fetch(`${backend}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = (await res.json().catch(() => ({}))) as {
      detail?: string | string[];
      access_token?: string;
    };
    if (!res.ok) {
      const raw = data.detail;
      const errorMsg =
        typeof raw === "string" ? raw : Array.isArray(raw) ? raw[0] : undefined;
      return NextResponse.json(
        { error: errorMsg || "Login failed" },
        { status: res.status }
      );
    }
    const access_token = data.access_token;
    if (!access_token) {
      return NextResponse.json({ error: "No token in response" }, { status: 502 });
    }
    const response = NextResponse.json({ ok: true });
    response.cookies.set(AUTH_COOKIE_NAME, access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: AUTH_COOKIE_MAX_AGE,
      path: "/",
    });
    return response;
  } catch (e) {
    console.error("Login API error:", e);
    return NextResponse.json(
      { error: "Server error. Check NEXT_PUBLIC_API_URL and backend availability." },
      { status: 500 }
    );
  }
}
