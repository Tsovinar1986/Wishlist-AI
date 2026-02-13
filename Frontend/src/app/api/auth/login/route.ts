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
      let errorMsg =
        typeof raw === "string" ? raw : Array.isArray(raw) ? raw[0] : undefined;
      if (!errorMsg && res.status >= 500) {
        errorMsg = "Server problem. Try again later.";
      }
      if (!errorMsg) {
        errorMsg = "Login failed.";
      }
      return NextResponse.json(
        { error: errorMsg },
        { status: res.status >= 500 ? 502 : res.status }
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
      { error: "Backend unavailable. Try again later." },
      { status: 503 }
    );
  }
}
