"use client";

/**
 * Public wishlist view at /w/[slug]. No auth required.
 * Fetches wishlist + items by slug, shows reserve/contribute buttons.
 */
import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { api, type PublicWishlist, type PublicItem } from "@/lib/api";
import { subscribeWishlist } from "@/lib/ws-client";

export default function PublicWishlistPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [data, setData] = useState<PublicWishlist | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reserveItem, setReserveItem] = useState<PublicItem | null>(null);
  const [contributeAmount, setContributeAmount] = useState("");
  const [guestName, setGuestName] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const applyWsUpdate = useCallback((itemId: string, reservedTotal: number, contributorsCount: number) => {
    const safeTotal = Number(reservedTotal);
    const safeCount = Math.max(0, Math.floor(Number(contributorsCount) || 0));
    setData((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        items: prev.items.map((i) =>
          i.id === itemId ? { ...i, reserved_total: safeTotal, contributors_count: safeCount } : i
        ),
      };
    });
  }, []);

  useEffect(() => {
    const safeSlug = typeof slug === "string" ? slug.trim() : "";
    if (!safeSlug) {
      setError("Неверная ссылка на список");
      setLoading(false);
      return;
    }
    api<PublicWishlist>(`/api/public/wishlists/by-slug/${encodeURIComponent(safeSlug)}`)
      .then(setData)
      .catch((err) => {
        console.error("Failed to load wishlist:", err);
        if (err instanceof Error) {
          setError(err.message.includes("подключиться") ? err.message : err.message);
        } else {
          setError("Список не найден или сервер недоступен");
        }
      })
      .finally(() => setLoading(false));
  }, [slug]);

  useEffect(() => {
    if (!data?.id) return;
    const unsubscribe = subscribeWishlist(data.id, {
      onMessage: (msg) => {
        if (msg.type === "item_reserved" || msg.type === "contribution_added") {
          applyWsUpdate(msg.item_id, msg.reserved_total, msg.contributors_count);
        }
      },
    });
    return unsubscribe;
  }, [data?.id, applyWsUpdate]);

  const reserveFull = async (item: PublicItem) => {
    if (!data) return;
    const price = item.price ?? 0;
    if (price <= 0) return;
    setSubmitting(true);
    try {
      await api(`/api/wishlists/${data.id}/items/${item.id}/reservations`, {
        method: "POST",
        body: JSON.stringify({
          amount: price,
          is_full_reservation: true,
          guest_name: guestName.trim() || undefined,
        }),
      });
      applyWsUpdate(item.id, price, 1);
      setReserveItem(null);
      setGuestName("");
      toast.success("Подарок зарезервирован");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setSubmitting(false);
    }
  };

  const contribute = async (item: PublicItem) => {
    if (!data) return;
    const amount = Math.round(parseFloat(contributeAmount.replace(",", ".").replace(/\s/g, "")) * 100) / 100;
    if (isNaN(amount) || amount <= 0) {
      toast.error("Введите корректную сумму");
      return;
    }
    const price = item.price ?? 0;
    const current = Number(item.reserved_total) || 0;
    const remainingAmount = price > 0 ? Math.max(0, price - current) : amount;
    if (price > 0 && amount > remainingAmount) {
      toast.error(`Можно добавить не больше ${remainingAmount.toFixed(0)} ₽`);
      return;
    }
    setSubmitting(true);
    try {
      await api(`/api/wishlists/${data.id}/items/${item.id}/reservations`, {
        method: "POST",
        body: JSON.stringify({
          amount,
          is_full_reservation: false,
          guest_name: guestName.trim() || undefined,
        }),
      });
      const newTotal = Math.round((current + amount) * 100) / 100;
      const newCount = (Number(item.contributors_count) || 0) + 1;
      applyWsUpdate(item.id, newTotal, newCount);
      setReserveItem(null);
      setContributeAmount("");
      setGuestName("");
      toast.success("Вклад внесён");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--primary)] border-t-transparent" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4">
        <div className="max-w-md text-center">
          <p className="text-lg font-semibold text-[var(--foreground)] mb-2">
            {error || "Список не найден"}
          </p>
          <p className="text-sm text-[var(--muted)] mb-4">
            Возможные причины:
            <br />
            • Ссылка неверна или список удалён
            <br />
            • Сервер недоступен
            <br />
            • Проблема с подключением
          </p>
          <Link href="/" className="inline-block rounded-xl bg-[var(--primary)] px-6 py-2 text-white font-medium hover:opacity-90">
            На главную
          </Link>
        </div>
      </div>
    );
  }

  const remaining = (item: PublicItem) => {
    const p = Number(item.price) ?? 0;
    if (p <= 0) return null;
    const reserved = Number(item.reserved_total) || 0;
    return Math.max(0, p - reserved);
  };

  return (
    <div className="min-h-screen">
      <header className="border-b border-[var(--border)] bg-[var(--muted-soft)]">
        <div className="mx-auto max-w-2xl px-4 py-4">
          <h1 className="text-2xl font-bold break-words">{data.title || "Список желаний"}</h1>
          {data.description && (
            <p className="mt-1 text-sm text-[var(--muted)]">{data.description}</p>
          )}
          <p className="mt-2 text-xs text-[var(--muted)]">
            Выберите подарок или скиньтесь — владелец списка не увидит, кто что выбрал.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-2xl px-4 py-6">
        {!(Array.isArray(data.items) && data.items.length > 0) ? (
          <div className="rounded-2xl border border-dashed border-[var(--border)] p-8 text-center text-[var(--muted)]">
            В этом списке пока нет подарков.
          </div>
        ) : (
          <ul className="space-y-6">
            {(data.items || []).map((item) => {
              const rem = remaining(item);
              const priceNum = Number(item.price) ?? 0;
              const reservedNum = Number(item.reserved_total) || 0;
              const isFullyReserved = priceNum > 0 && reservedNum >= priceNum;
              const isReserveOpen = reserveItem?.id === item.id;

              return (
                <li
                  key={item.id}
                  className="rounded-xl border border-[var(--border)] bg-[var(--muted-soft)] overflow-hidden"
                >
                  <div className="flex gap-4 p-4">
                    {item.image_url ? (
                      <img
                        src={item.image_url}
                        alt=""
                        className="h-24 w-24 rounded-lg object-cover flex-shrink-0 bg-[var(--border)]"
                        onError={(e) => {
                          e.currentTarget.style.display = "none";
                        }}
                      />
                    ) : null}
                    <div className="flex-1 min-w-0">
                      <h2 className="font-semibold line-clamp-2 break-words">{item.title || "Без названия"}</h2>
                      <div className="mt-1.5 flex flex-wrap items-center gap-2">
                        {item.price != null && (
                          <>
                            <span className="inline-flex items-center rounded-full bg-[var(--border)] px-2.5 py-0.5 text-xs font-medium text-[var(--foreground)]">
                              {item.price.toFixed(0)} ₽
                            </span>
                            {(Number(item.reserved_total) || 0) > 0 && (
                              <>
                                <span className="inline-flex items-center rounded-full bg-[var(--primary-soft)] px-2.5 py-0.5 text-xs font-medium text-[var(--primary)]">
                                  Собрано {(Number(item.reserved_total) || 0).toFixed(0)} ₽
                                </span>
                                {(Number(item.contributors_count) || 0) > 0 && (
                                  <span className="inline-flex items-center rounded-full bg-[var(--muted-soft)] px-2.5 py-0.5 text-xs text-[var(--muted)]">
                                    {(() => {
                                      const c = Math.max(0, Math.floor(Number(item.contributors_count) || 0));
                                      return `${c} ${c === 1 ? "участник" : c < 5 ? "участника" : "участников"}`;
                                    })()}
                                  </span>
                                )}
                              </>
                            )}
                          </>
                        )}
                      </div>
                      {item.product_url && (
                        <a
                          href={item.product_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-[var(--primary)] hover:underline"
                        >
                          Ссылка на товар
                        </a>
                      )}
                    </div>
                  </div>
                  {(item.price == null || item.price > 0) && (
                    <div className="px-4 pb-4">
                      {item.price != null && item.price > 0 && (
                        <div className="mb-3 overflow-hidden rounded-full bg-[var(--border)] h-2.5">
                          <div
                            className={`h-full rounded-full transition-[width] duration-500 ease-out ${isFullyReserved ? "bg-[var(--accent)]" : "bg-[var(--primary)]"}`}
                            style={{
                              width: priceNum > 0 ? `${Math.min(100, (reservedNum / priceNum) * 100)}%` : "0%",
                            }}
                          />
                        </div>
                      )}
                      {isFullyReserved ? (
                        <div className="inline-flex items-center gap-1.5 rounded-full bg-[var(--accent)]/15 px-3 py-1.5 text-sm font-medium text-[var(--accent)]">
                          <span className="size-1.5 rounded-full bg-[var(--accent)]" aria-hidden />
                          Подарок зарезервирован
                        </div>
                      ) : (
                        <>
                          {!isReserveOpen ? (
                            <div className="flex flex-wrap gap-2">
                              {item.allow_contributions && rem !== null && rem > 0 && (
                                <button
                                  type="button"
                                  onClick={() => setReserveItem(item)}
                                  className="rounded-lg bg-[var(--primary)] px-3 py-1.5 text-sm font-medium text-white"
                                >
                                  Скинуться
                                </button>
                              )}
                              {rem !== null && rem > 0 && (
                                <button
                                  type="button"
                                  onClick={() => {
                                    setReserveItem(item);
                                    setContributeAmount("");
                                  }}
                                  className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-sm"
                                >
                                  Зарезервировать полностью
                                </button>
                              )}
                            </div>
                          ) : null}
                          {isReserveOpen && (
                            <div className="rounded-lg border border-[var(--border)] bg-[var(--background)] p-3 space-y-2">
                              <input
                                type="text"
                                placeholder="Ваше имя (по желанию)"
                                value={guestName}
                                onChange={(e) => setGuestName(e.target.value)}
                                className="w-full rounded border border-[var(--input)] px-3 py-2 text-sm"
                              />
                              {item.allow_contributions && rem !== null && rem > 0 && (
                                <input
                                  type="text"
                                  inputMode="decimal"
                                  placeholder={`Сумма (осталось ${rem.toFixed(0)} ₽)`}
                                  value={contributeAmount}
                                  onChange={(e) => setContributeAmount(e.target.value)}
                                  className="w-full rounded border border-[var(--input)] px-3 py-2 text-sm"
                                />
                              )}
                              <div className="flex gap-2">
                                {item.allow_contributions && rem !== null && rem > 0 && (
                                  <button
                                    type="button"
                                    disabled={submitting}
                                    onClick={() => contribute(item)}
                                    className="rounded-lg bg-[var(--primary)] px-3 py-1.5 text-sm text-white disabled:opacity-50"
                                  >
                                    Внести вклад
                                  </button>
                                )}
                                <button
                                  type="button"
                                  disabled={submitting}
                                  onClick={() => reserveFull(item)}
                                  className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-sm disabled:opacity-50"
                                >
                                  Резерв на всю сумму
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setReserveItem(null);
                                    setContributeAmount("");
                                    setGuestName("");
                                  }}
                                  className="text-sm text-[var(--muted)]"
                                >
                                  Отмена
                                </button>
                              </div>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </main>
    </div>
  );
}
