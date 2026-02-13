"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type ButtonVariant = "default" | "outline";

export function CreateWishlistForm({
  onSuccess,
  onCancel,
}: {
  onSuccess?: () => void;
  onCancel?: () => void;
}) {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setLoading(true);
    try {
      const res = await fetch("/api/wishlists", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title.trim(),
          description: null,
          deadline: null,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const raw = (data as { detail?: string | string[] }).detail;
        const msg = typeof raw === "string" ? raw : Array.isArray(raw) ? raw[0] : (data as { error?: string }).error;
        toast.error(msg || "Не удалось создать список");
        return;
      }
      const id = (data as { id?: string }).id;
      setTitle("");
      toast.success("Wishlist created");
      onSuccess?.();
      if (id) router.push(`/dashboard/wishlists/${id}`);
      else router.refresh();
    } catch {
      toast.error("Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="wishlist-title">Название</Label>
        <Input
          id="wishlist-title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Например: День рождения"
          autoFocus
        />
      </div>
      <div className="flex gap-2">
        <Button type="submit" disabled={loading || !title.trim()}>
          {loading ? "Создаём…" : "Создать"}
        </Button>
        {onCancel && (
          <Button type="button" variant="ghost" onClick={onCancel}>
            Отмена
          </Button>
        )}
      </div>
    </form>
  );
}

export function CreateWishlistButton({
  variant = "default",
}: {
  variant?: ButtonVariant;
}) {
  const [open, setOpen] = useState(false);
  const router = useRouter();

  if (!open) {
    return (
      <Button variant={variant} onClick={() => setOpen(true)}>
        Create wishlist
      </Button>
    );
  }

  return (
    <CreateWishlistForm
      onSuccess={() => setOpen(false)}
      onCancel={() => setOpen(false)}
    />
  );
}
