# Fix "Backend unavailable" or "Server error"

If you see **"Backend unavailable. Try again later."** or **"Server error"** / **"Server problem. Try again later."**, the frontend cannot use the backend. Follow these steps in order. You do them in **Railway** and **Vercel** (not in code).

---

## Part 1: Railway — get the backend running and get a URL

### Step 1.1 — Open your backend service

1. Go to [railway.com](https://railway.com) and open your project.
2. Click the **WISHLIST-AI** service (backend).

### Step 1.2 — Set how Railway builds the app (if it’s crashing)

- Go to **Settings**.
- Either:
  - Set **Root Directory** to **`Backend`** (exactly, capital B),  
  **or**
  - Set **Dockerfile path** (or builder to Dockerfile) to **`Dockerfile.backend`**.
- Save (e.g. **Deploy** or the save button).

### Step 1.3 — Required variables

- Open the **Variables** tab.
- Make sure you have at least:
  - **`DATABASE_URL`** — from Railway PostgreSQL (add a PostgreSQL service and copy its URL) or your own DB URL.
  - **`SECRET_KEY`** — any long random string (e.g. 32+ characters).
  - **`APP_ENV`** = **`production`**.

If you add or change variables, Railway will redeploy.

### Step 1.4 — Get a public URL

- In **Settings** → **Networking** → **Public Networking**.
- Click **Generate Domain**.
- Copy the URL. For this project it is: **`https://wishlist-ai-production.up.railway.app`**  
  **No trailing slash.**  
  This is your **backend URL**.

### Step 1.5 — Wait for a successful deployment

- In **Deployments**, wait until the latest deployment is **Success** / **Active** (not Crashed).
- If it’s still failing, open **View logs** for that deployment and fix the error (often missing `DATABASE_URL` or wrong Root Directory/Dockerfile).

---

## Part 2: Vercel — point the frontend to your backend

### Step 2.1 — Set the backend URL

1. Go to [vercel.com](https://vercel.com) → your **wishlist-ai** project.
2. **Settings** → **Environment Variables**.
3. Add or edit:
   - **Key:** `NEXT_PUBLIC_API_URL`
   - **Value:** `https://wishlist-ai-production.up.railway.app` (no trailing slash).
4. Save.

### Step 2.2 — Redeploy

- Go to **Deployments**.
- Open the **⋯** menu on the latest deployment → **Redeploy**.
- Wait until the new deployment is ready.

---

## Part 3: CORS (only if you still get errors)

- In **Railway** → WISHLIST-AI service → **Variables**.
- Add or set **`CORS_ORIGINS`** = your Vercel app URL (e.g. `https://wishlist-nwwc8i8nw-tsovinar-babakhanyans-projects.vercel.app`) — **no trailing slash**.

---

## If you still see "Server error" or "Server problem"

- The backend is reachable but **returning 500** (crashed or DB error). In **Railway** → WISHLIST-AI → **Deployments** → **View logs** for the latest deployment. Check for:
  - Missing or wrong **DATABASE_URL** (add a PostgreSQL service and copy its URL into Variables).
  - Python/import errors — fix Root Directory = `Backend` or Dockerfile path = `Dockerfile.backend`.

## Done

Open your Vercel app URL and try **Register** or **Login** again. You should no longer see "Backend unavailable" or "Server error."

**Summary:**  
Backend URL from Railway (Step 1.4) → into Vercel as `NEXT_PUBLIC_API_URL` (Step 2.1) → Redeploy Vercel (Step 2.2).
