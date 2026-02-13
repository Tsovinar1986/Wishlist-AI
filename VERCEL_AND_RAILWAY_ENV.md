# Vercel + Railway: env vars so frontend and backend work together

Use these values so the **Vercel** frontend talks to the **Railway** backend.

---

## Where to get the Railway URL (for Vercel)

Your backend must be **exposed** so Vercel can call it. The deployment panel shows "Unexposed service" until you add a domain.

1. **Railway** → open your project → click the **WISHLIST-AI** (backend) service.
2. Open the **Settings** tab.
3. Go to **Networking** → **Public Networking**.
4. Click **Generate Domain**. Railway will create a URL like `https://wishlist-ai-production-xxxx.up.railway.app`.
5. **Copy that URL** (no trailing slash). That is your **Railway weblink** for the backend.
6. **Vercel** → your project → **Settings** → **Environment Variables** → set **`NEXT_PUBLIC_API_URL`** to that URL.
7. **Redeploy** the Vercel project so it uses the new value.

The backend must be **running** (not crashed) for this URL to work. If the service is crashed, fix the deployment first, then use the URL from step 5 in Vercel.

---

## 1. Vercel (Frontend) — Environment Variables

**Where:** Vercel → your project → **Settings** → **Environment Variables**

Add these (Production + Preview if you want):

| Key | Value |
|-----|--------|
| `NEXT_PUBLIC_API_URL` | `https://wishlist-ai-production.up.railway.app` |
| `NEXT_PUBLIC_SITE_URL` | `https://YOUR_VERCEL_APP.vercel.app` *(replace with your real Vercel app URL)* |

Then **Redeploy** (Deployments → ⋯ → Redeploy).

---

## 2. Railway (Backend) — Environment Variables

**Where:** Railway → your backend service → **Variables**

Add or set:

| Key | Value |
|-----|--------|
| `DATABASE_URL` | `postgresql+asyncpg://...` *(from Railway PostgreSQL or your DB)* |
| `SECRET_KEY` | *(long random string for JWT)* |
| `APP_ENV` | `production` |
| `CORS_ORIGINS` | `https://YOUR_VERCEL_APP.vercel.app` *(your Vercel frontend URL; no trailing slash)* |

Optional (if you use them):

- `PUSHER_APP_ID`, `PUSHER_KEY`, `PUSHER_SECRET`, `PUSHER_CLUSTER`
- `PUSHOVER_APP_TOKEN`

**Important:** Do **not** put Railway API tokens (e.g. for deploy) in these variables. Use them only in Railway dashboard or CLI for deployment. The UUID you have is for Railway auth — keep it secret and never add it as `NEXT_PUBLIC_*` or commit it.

---

## 3. Railway: monorepo and “Error creating build plan with Railpack”

This repo is a monorepo (Frontend + Backend). Railway must build **only** the backend.

### Where to set Root Directory (step by step)

**Important:** Root Directory is set on the **service**, not on the **project**. You configure the **WISHLIST-AI** service, not the “industrious-nature” project.

1. Open your **project** (e.g. industrious-nature) on [railway.com](https://railway.com).
2. On the project canvas, **click the WISHLIST-AI service** (the backend tile/card). The main panel should show that service (Deployments, Variables, Metrics, **Settings**).
3. Click the **Settings** tab at the top of that panel (next to Deployments, Variables, Metrics).
4. On the Settings page, **scroll down**. Look for a section about **build** or **source**:
   - **Root Directory** — a text field (often empty or “.”). Type **`Backend`** there (capital B, no leading slash).
   - It can appear under a “Source” subsection, or near “Build command” and “Watch paths” on the same page.
5. After typing `Backend`, save: click **Deploy** (top right) or the save/update button so the change is applied.

If you still don’t see “Root Directory”:
- Scroll the **entire** Settings page (it may be at the bottom).
- Look for **Source** — Root Directory is inside Source in some layouts.
- You’re in the right place if you see “Build command”, “Watch paths”, or “Generate Domain” on the same page.

### Alternative: use the Dockerfile (no Root Directory needed)

If the UI doesn’t show Root Directory, you can build from a Dockerfile instead. This repo has a **`Dockerfile.backend`** in the **project root**. In the same **Service → Settings** page:

- Find **Dockerfile path** (or “Build” / “Builder”) and set it to **`Dockerfile.backend`**,  
  **or**
- Set the builder to **Dockerfile** and set the path to **`Dockerfile.backend`**.

Then Railway will build the backend from that Dockerfile and you don’t need to set Root Directory.

### Why this is needed

The `Backend/` folder has a Procfile and nixpacks.toml so Railpack can build the FastAPI app. If the service builds from the **repo root**, Railpack sees both Next.js and Python and can fail with “Error creating build plan with Railpack”. Setting Root Directory to `Backend` (or using `Dockerfile.backend`) fixes that.

---

## 4. One-time checklist

- [ ] **Railway:** Root Directory = `Backend`; Backend deployed; Variables set (especially `DATABASE_URL`, `SECRET_KEY`, `APP_ENV=production`, `CORS_ORIGINS` = your Vercel URL).
- [ ] **Vercel:** `NEXT_PUBLIC_API_URL` = `https://wishlist-backend.up.railway.app` and `NEXT_PUBLIC_SITE_URL` = your Vercel app URL.
- [ ] **Redeploy** both after changing env (Railway redeploys on save; Vercel → Redeploy).

After this, the server part (backend on Railway + frontend on Vercel) works together.
