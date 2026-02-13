# Railway setup — do this so the app stops crashing

The backend **must** have a database. Without it, the app can crash or return "Server problem."

## 1. Add PostgreSQL (in the same project)

1. Railway dashboard → your project (e.g. **striking-achievement**).
2. Click **+ New** → **Database** → **PostgreSQL**.
3. Wait until the service shows as running.

## 2. Set variables on WISHLIST-AI (backend service)

1. Click the **WISHLIST-AI** service (the one that keeps crashing).
2. Open the **Variables** tab.
3. Add:

   | Variable        | How to set |
   |-----------------|------------|
   | **DATABASE_URL** | **New Variable** → **Add a reference** → choose the **PostgreSQL** service → select **`DATABASE_URL`**. (Or copy the URL from the Postgres service Variables and paste it.) |
   | **SECRET_KEY**   | Any long random string (e.g. 32+ characters). |
   | **APP_ENV**      | `production` |
   | **CORS_ORIGINS** | Your Vercel app URL, e.g. `https://wishlist-ai.vercel.app` (no trailing slash). |

4. Save. Railway will redeploy.

## 3. Build settings (if not already set)

- **Settings** tab → **Root Directory**: set to **`Backend`**  
  **or**  
- **Settings** → **Dockerfile path**: set to **`Dockerfile.backend`** (if building from repo root).

Save and redeploy if you change these.

## 4. Check

- After deploy, open **https://wishlist-ai-production.up.railway.app/health**.
- You should see `{"status":"ok","db":"ok"}`. If you see `"db":"unavailable"`, DATABASE_URL is still wrong or Postgres is not linked.
- Then try **Register** on your Vercel app.

---

**Why it was crashing:** The app needs a database. Without `DATABASE_URL` (or with a wrong one), the service could fail or be marked unhealthy. The app is now set up to stay up and return 200 on `/health`; add Postgres and set the variables above so it works.
