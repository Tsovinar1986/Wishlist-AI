"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const rawFrom = searchParams.get("from") || "/dashboard";
  const from = rawFrom.startsWith("/") && !rawFrom.startsWith("//") ? rawFrom : "/dashboard";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedEmail = email.trim();
    if (!trimmedEmail || !password) {
      toast.error("Введите email и пароль");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: trimmedEmail, password }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg =
          typeof (data as { detail }).detail === "string"
            ? (data as { detail: string }).detail
            : Array.isArray((data as { detail?: string[] }).detail)
              ? (data as { detail: string[] }).detail[0]
              : (data as { error?: string }).error;
        toast.error(msg || "Неверный email или пароль");
        return;
      }
      toast.success("Добро пожаловать!");
      router.push(from.startsWith("/") ? from : "/dashboard");
    } catch {
      toast.error("Ошибка подключения. Попробуйте снова.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl">Log in</CardTitle>
          <CardDescription>Enter your email and password</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-4">
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Signing in…" : "Log in"}
            </Button>
            <p className="text-sm text-[var(--muted)] text-center">
              Don&apos;t have an account?{" "}
              <Link href="/register" className="text-[var(--primary)] hover:underline">
                Register
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
      <p className="mt-6 text-sm text-[var(--muted)] text-center max-w-sm">
        You can open a shared wishlist by link without logging in.
      </p>
    </main>
  );
}
