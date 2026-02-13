import { NextRequest, NextResponse } from "next/server";
import { AUTH_COOKIE_NAME, getBackendUrl } from "@/lib/auth-cookie";

/**
 * Proxy for Pusher channel auth. Pusher JS sends POST with form body (socket_id, channel_name, channel_data).
 * We forward to the backend with the JWT from the httpOnly cookie so private/presence channels are authorized.
 */
export async function POST(request: NextRequest) {
  try {
    const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;
    const backend = getBackendUrl();
    const authUrl = `${backend}/api/pusher/auth`;

    // Pusher JS sends application/x-www-form-urlencoded
    const contentType = request.headers.get("content-type") ?? "";
    let body: string;
    if (contentType.includes("application/x-www-form-urlencoded")) {
      body = await request.text();
    } else {
      const form = await request.formData().catch(() => null);
      if (!form) {
        return NextResponse.json({ detail: "Missing form body" }, { status: 400 });
      }
      body = new URLSearchParams(
        [...form.entries()].filter(([, v]) => v != null) as [string, string][]
      ).toString();
    }

    const headers: Record<string, string> = {
      "Content-Type": "application/x-www-form-urlencoded",
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(authUrl, {
      method: "POST",
      headers,
      body,
    });

    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      return NextResponse.json(data, { status: res.status });
    }
    return NextResponse.json(data);
  } catch (e) {
    console.error("Pusher auth proxy error:", e);
    return NextResponse.json(
      { detail: "Failed to authorize channel. Check backend (NEXT_PUBLIC_API_URL)." },
      { status: 503 }
    );
  }
}
