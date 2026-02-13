import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { AUTH_COOKIE_NAME, getBackendUrl } from "@/lib/auth-cookie";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { CreateWishlistForm } from "@/components/create-wishlist-button";
import { WishlistCard } from "@/components/wishlist-card";
import { EmptyWishlistsState } from "@/components/empty-wishlists";
import { PushoverSettings } from "@/components/pushover-settings";

type User = { id: string; email: string; name: string; created_at: string };
type Wishlist = {
  id: string;
  owner_id: string;
  title: string;
  description: string | null;
  public_slug: string;
  deadline: string | null;
  created_at: string;
  items_count: number;
};

async function getMe(token: string): Promise<User | null> {
  try {
    const backend = getBackendUrl();
    const res = await fetch(`${backend}/api/users/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

async function getWishlists(token: string): Promise<Wishlist[]> {
  try {
    const backend = getBackendUrl();
    const res = await fetch(`${backend}/api/wishlists`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

export default async function DashboardPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get(AUTH_COOKIE_NAME)?.value;
  if (!token) redirect("/login");

  const [user, wishlists] = await Promise.all([
    getMe(token),
    getWishlists(token),
  ]);
  if (!user) redirect("/login");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold sm:text-3xl">
          Добро пожаловать, {user.name || user.email}!
        </h1>
        <p className="text-[var(--muted)] mt-1">Ваши вишлисты:</p>
      </div>

      <PushoverSettings />

      {wishlists.length === 0 ? (
        <EmptyWishlistsState />
      ) : (
        <>
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {wishlists.map((w) => (
              <li key={w.id}>
                <WishlistCard
                  id={w.id}
                  title={w.title}
                  description={w.description}
                  public_slug={w.public_slug}
                  items_count={w.items_count ?? 0}
                />
              </li>
            ))}
          </ul>

          <Dialog>
            <DialogTrigger asChild>
              <Button size="lg" className="w-full sm:w-auto">
                + Создать новый вишлист
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Новый вишлист</DialogTitle>
              </DialogHeader>
              <CreateWishlistForm />
            </DialogContent>
          </Dialog>
        </>
      )}
    </div>
  );
}
