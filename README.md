# As Snow Cleaning & Pest Control: website + WhatsApp booking

* **Website** (Next.js + Tailwind): landing page, instant-quote form, floating "Book on WhatsApp" button, password-protected `/admin`.
* **API** (FastAPI + Postgres/Supabase): quotes with price estimates, WhatsApp Cloud API webhook and booking chat, day-before reminders, recurring bookings.
* **Mock mode**: until WhatsApp credentials are added, every message is saved to the admin **WhatsApp log** instead of being sent, so you can demo everything without Meta.

```
frontend/   Next.js site            backend/    FastAPI API (+ tests/)
docs/       Meta template texts     .github/    free daily reminder scheduler
render.yaml Render deploy blueprint
```

## 1. Run locally (5 minutes)

```bash
# API
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # for local dev delete the DATABASE_URL line -> uses SQLite
uvicorn app.main:app --reload   # http://localhost:8000  (docs at /docs)

# Website (new terminal)
cd frontend
cp .env.example .env.local
npm install && npm run dev      # http://localhost:3000
```
Admin: http://localhost:3000/admin (password = `ADMIN_PASSWORD`). Run the tests with `cd backend && pytest`.

**Try the WhatsApp chat without WhatsApp:** simulate a customer message.
```bash
curl -X POST localhost:8000/webhook/whatsapp -H 'content-type: application/json' -d \
'{"entry":[{"changes":[{"value":{"messages":[{"from":"2348030000000","id":"m1","type":"text","text":{"body":"hi"}}]}}]}]}'
```
Then open Admin → **WhatsApp log** to see the bot's reply. Repeat with `"3"`, `"tomorrow"`, an address, `"yes"` (use a new `id` each time).

## 2. Deploy (all free tiers)

### a) Database: Supabase
1. Create a project at supabase.com. **Project Settings → Database → Connection string → Session pooler**; copy the URI. This is `DATABASE_URL`.
2. Tables are created automatically on first API start. (Or paste `backend/schema.sql` into the SQL editor. It also turns on row-level security so the public Supabase REST API can't read your data.)

### b) API: Render (or Railway)
1. Push this folder to a GitHub repo.
2. **Render → New → Blueprint** → pick the repo (`render.yaml` is picked up). Fill the prompted variables (see `backend/.env.example`). Set `CORS_ORIGINS` to your Vercel URL.
   *Railway instead:* New project → Deploy from repo → root directory `backend`, start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, same variables.
3. Check `https://YOUR-API/health` returns `{"ok":true,"whatsapp":"mock"}`.
> Render's free tier sleeps after ~15 min idle (first request takes ~30–60 s). The reminder workflow below wakes it daily; for production use a paid instance (~$7/mo) so customers' WhatsApp messages are never delayed.

### c) Website: Vercel
1. **Vercel → Add New Project** → same repo, **Root Directory = `frontend`**.
2. Environment variables: `NEXT_PUBLIC_API_URL` = your Render URL, `NEXT_PUBLIC_WHATSAPP_NUMBER` = `2348061380762`.
3. Deploy. Then go back to Render and make sure `CORS_ORIGINS` contains the final Vercel (or custom domain) URL.

### d) Daily reminders: GitHub Actions (free)
In the GitHub repo → **Settings → Secrets and variables → Actions**, add `API_URL` (Render URL) and `CRON_SECRET` (same value as on Render). `.github/workflows/reminders.yml` then calls `POST /internal/run-reminders` every day at 08:00 Lagos time. It's idempotent (never double-sends), and you can trigger it manually from the Actions tab. Any cron service (cron-job.org) works too: `POST /internal/run-reminders` with header `x-cron-secret`.

## 3. Go live on WhatsApp
1. developers.facebook.com → **Create app → Business** → add the **WhatsApp** product. Create/verify a Meta Business account (this can take days, so start early).
2. Add the business phone number (it can't also be logged in on the regular WhatsApp app). Copy the **Phone number ID** and create a **permanent token** (System User → generate token with `whatsapp_business_messaging` + `whatsapp_business_management`).
3. **Webhook**: Callback URL `https://YOUR-API/webhook/whatsapp`, Verify token = your `WHATSAPP_VERIFY_TOKEN`; subscribe to the **messages** field. Put the app secret in `WHATSAPP_APP_SECRET` so signatures are checked.
4. Submit the two templates in `docs/whatsapp-templates.md` and wait for **Approved**.
5. Set `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `OWNER_WHATSAPP` on Render and redeploy. `/health` now says `"whatsapp":"live"`.
6. Test: message the business number "hi"; make a quote; mark a booking for tomorrow and run the Action manually.

## How it works
* **Quote**: `POST /api/quotes` validates, saves the lead, computes the range from `backend/app/config.py`, alerts the owner on WhatsApp, and returns the estimate.
* **Chat flow**: hi → service (1–4) → date ("tomorrow", "Friday", "25/10") → address → confirm → booking saved + owner alerted. "cancel" resets.
* **Reminders**: the daily job finds bookings for tomorrow (status pending/confirmed, not yet reminded) and sends the `clean_reminder` template with **Confirm / Reschedule** buttons. *Confirm* marks the booking confirmed; *Reschedule* asks for a new date in chat, moves the booking, and resets the reminder.
* **Recurring**: in Admin → Bookings set a visit to **completed**; for weekly / every-2-weeks / monthly customers the next visit is created automatically (once, even if you click twice).

## Before you hand it to the client
* **Prices** are placeholders: edit `backend/app/config.py` (`PRICING`, discounts, range). Quote and chat labels live there too; the website lists in `frontend/src/lib/site.ts` must use the same keys.
* **Service areas** in `site.ts` are placeholders. Replace with the real ones.
* **Reviews**: the page shows the 5.0 / 170 Google rating. Add real testimonials to `TESTIMONIALS` in `site.ts` (nothing is invented). Verify the rating is still accurate.
* Set strong `ADMIN_PASSWORD`, `SECRET_KEY`, `CRON_SECRET`.
* Add the customer's own logo/photos and a custom domain in Vercel.

## Costs
Free: Vercel, Supabase, GitHub Actions, WhatsApp service replies. Paid: Meta charges per business-initiated template message (small per-message rate in Nigeria; check Meta's current pricing), a domain (optional), and a non-sleeping API instance (recommended for production).
