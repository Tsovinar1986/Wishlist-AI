import { NextRequest, NextResponse } from "next/server";
import { AUTH_COOKIE_NAME, AUTH_COOKIE_MAX_AGE, getBackendUrl } from "@/lib/auth-cookie";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, password, name } = body;
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
    const registerRes = await fetch(`${backend}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        name: name || email.split("@")[0],
      }),
    });
    const registerData = (await registerRes.json().catch(() => ({}))) as {
      detail?: string | string[];
    };
    if (!registerRes.ok) {
      const raw = registerData.detail;
      const errorMsg =
        typeof raw === "string" ? raw : Array.isArray(raw) ? raw[0] : undefined;
      return NextResponse.json(
        { error: errorMsg || "Registration failed" },
        { status: registerRes.status }
      );
    }
    const loginRes = await fetch(`${backend}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const loginData = (await loginRes.json().catch(() => ({}))) as {
      access_token?: string;
    };
    if (!loginRes.ok) {
      return NextResponse.json({ ok: true }); // registered but login failed; user can go to login
    }
    const access_token = loginData.access_token;
    if (!access_token) {
      return NextResponse.json({ ok: true });
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
    console.error("Register API error:", e);
    return NextResponse.json({ error: "Server error" }, { status: 500 });
  }
}
