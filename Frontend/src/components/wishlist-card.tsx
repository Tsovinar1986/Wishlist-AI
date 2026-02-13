"use client";

import { useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getPublicWishlistUrl } from "@/lib/auth-cookie";

type WishlistCardProps = {
  id: string;
  title: string;
  description: string | null;
  public_slug: string;
  items_count: number;
};

export function WishlistCard({
  id,
  title,
  description,
  public_slug,
  items_count,
}: WishlistCardProps) {
  const [copied, setCopied] = useState(false);

  const shareUrl = getPublicWishlistUrl(public_slug);

  const copyShareLink = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!shareUrl) return;
    navigator.clipboard.writeText(shareUrl).then(() => {
      setCopied(true);
      toast.success("Ссылка скопирована");
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {
      toast.error("Не удалось скопировать");
    });
  };

  return (
    <Link href={`/dashboard/wishlists/${id}`} className="block h-full">
      <Card className="h-full transition-colors hover:border-[var(--primary)]">
        <CardHeader className="pb-2">
          <CardTitle className="text-base line-clamp-2 break-words">{title || "Без названия"}</CardTitle>
          {description && String(description).trim() && (
            <CardDescription className="line-clamp-2">
              {description}
            </CardDescription>
          )}
          <p className="text-xs text-[var(--muted)]">
            {(() => {
              const n = Math.max(0, Math.floor(Number(items_count) || 0));
              return n === 0 ? "Нет подарков" : `${n} ${n === 1 ? "подарок" : n < 5 ? "подарка" : "подарков"}`;
            })()}
          </p>
        </CardHeader>
        <CardContent className="pt-0">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={copyShareLink}
            className="w-full sm:w-auto"
          >
            {copied ? "Скопировано!" : "Поделиться ссылкой"}
          </Button>
        </CardContent>
      </Card>
    </Link>
  );
}
