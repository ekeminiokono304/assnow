import hashlib
import hmac
import json
import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import bookings as bk
from . import flow, whatsapp
from .auth import check_password, make_token, require_admin, require_cron
from .config import FREQUENCIES, SERVICES, get_settings
from .db import Base, engine, get_db
from .models import Booking, MessageLog, Quote
from .pricing import estimate
from .schemas import BookingIn, LoginIn, QuoteIn, QuoteOut, StatusIn
from .util import fmt_date, naira, normalise_phone

log = logging.getLogger("assnow")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


# ---------------------------------------------------------------- CORS
# The production frontend is always allowed, even if CORS_ORIGINS is missing or
# mistyped on Render. Anything in settings.cors_origins is added on top.
DEFAULT_ORIGINS = [
    "https://assnow.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
]
# Vercel preview deployments, e.g. https://assnow-git-main-<team>.vercel.app
VERCEL_PREVIEW_REGEX = r"https://assnow-[a-z0-9-]+\.vercel\.app"


def _cors_origins() -> list[str]:
    raw = get_settings().cors_origins or []
    if isinstance(raw, str):  # tolerate "a,b,c" as well as a list
        raw = raw.split(",")
    extra = [o.strip().rstrip("/") for o in raw if o and o.strip()]  # no trailing slashes
    return list(dict.fromkeys(DEFAULT_ORIGINS + extra))  # de-duplicate, keep order


app = FastAPI(title="As Snow Cleaning & Pest Control API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_origin_regex=VERCEL_PREVIEW_REGEX,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

_hits: dict[str, deque] = defaultdict(deque)


def _rate_limit(key: str, limit: int, window: int) -> None:
    now, q = time.time(), _hits[key]
    while q and q[0] < now - window:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    q.append(now)


@app.get("/health")
def health():
    return {"ok": True, "whatsapp": "live" if get_settings().live_whatsapp else "mock"}


# ---------------------------------------------------------------- public: quotes
@app.post("/api/quotes", response_model=QuoteOut)
def create_quote(body: QuoteIn, request: Request, db: Session = Depends(get_db)):
    _rate_limit(f"quote:{request.client.host if request.client else 'x'}", 10, 3600)
    low, high = estimate(body.service, body.property_size, body.rooms, body.frequency)
    if body.website:  # honeypot tripped: pretend success, store nothing
        return QuoteOut(id=0, est_low=low, est_high=high, frequency=body.frequency, message="Thank you!")
    q = Quote(name=body.name.strip(), phone=normalise_phone(body.phone), service=body.service,
              property_size=body.property_size, rooms=body.rooms, address=body.address.strip(),
              preferred_date=body.preferred_date, frequency=body.frequency, est_low=low, est_high=high)
    db.add(q)
    db.commit()
    db.refresh(q)
    pref = fmt_date(q.preferred_date) if q.preferred_date else "flexible"
    ok = whatsapp.notify_owner(
        db,
        f"New quote request #{q.id}\n\n"
        f"Customer: {q.name}\nPhone: +{q.phone}\n\n"
        f"Service: {SERVICES[q.service]}\n"
        f"Property: {q.property_size.capitalize()}, {q.rooms} room(s)\n"
        f"Location: {q.address}\n"
        f"Preferred date: {pref}\n"
        f"Frequency: {FREQUENCIES[q.frequency]}\n\n"
        f"Estimated price: {naira(low)} – {naira(high)}\n\n"
        f"Please contact the customer on WhatsApp to confirm the final price and schedule.",
        [f"Quote #{q.id}", f"{SERVICES[q.service]} ({q.address})", f"{naira(low)}-{naira(high)}", f"{q.name} +{q.phone}"])
    q.owner_notified = 1 if ok else 0
    db.commit()
    return QuoteOut(
        id=q.id, est_low=low, est_high=high, frequency=q.frequency,
        message=f"Thank you, {q.name.strip().split()[0]}. Your quote request has been received. "
                "Our team will contact you on WhatsApp shortly to confirm the final price and schedule.")


# ---------------------------------------------------------------- admin
@app.post("/api/admin/login")
def admin_login(body: LoginIn, request: Request):
    _rate_limit(f"login:{request.client.host if request.client else 'x'}", 8, 900)
    if not check_password(body.password):
        raise HTTPException(status_code=401, detail="Wrong password")
    return {"token": make_token()}


def _quote_dict(q: Quote) -> dict:
    return {"id": q.id, "name": q.name, "phone": q.phone, "service": q.service, "property_size": q.property_size,
            "rooms": q.rooms, "address": q.address, "preferred_date": q.preferred_date, "frequency": q.frequency,
            "est_low": q.est_low, "est_high": q.est_high, "status": q.status, "created_at": q.created_at}


def _booking_dict(b: Booking) -> dict:
    return {"id": b.id, "name": b.name, "phone": b.phone, "service": b.service, "scheduled_date": b.scheduled_date,
            "address": b.address, "frequency": b.frequency, "status": b.status, "source": b.source,
            "reminder_sent_at": b.reminder_sent_at, "parent_id": b.parent_id, "quote_id": b.quote_id}


@app.get("/api/admin/quotes", dependencies=[Depends(require_admin)])
def admin_quotes(db: Session = Depends(get_db), limit: int = Query(100, le=500)):
    return [_quote_dict(q) for q in db.scalars(select(Quote).order_by(Quote.id.desc()).limit(limit))]


@app.get("/api/admin/bookings", dependencies=[Depends(require_admin)])
def admin_bookings(db: Session = Depends(get_db), limit: int = Query(200, le=500)):
    return [_booking_dict(b) for b in
            db.scalars(select(Booking).order_by(Booking.scheduled_date.desc(), Booking.id.desc()).limit(limit))]


@app.get("/api/admin/reminders", dependencies=[Depends(require_admin)])
def admin_reminders(db: Session = Depends(get_db)):
    return [_booking_dict(b) for b in bk.upcoming_reminders(db)]


@app.get("/api/admin/messages", dependencies=[Depends(require_admin)])
def admin_messages(db: Session = Depends(get_db), limit: int = Query(60, le=300)):
    rows = db.scalars(select(MessageLog).order_by(MessageLog.id.desc()).limit(limit))
    return [{"id": m.id, "direction": m.direction, "phone": m.phone, "body": m.body, "mode": m.mode,
             "created_at": m.created_at} for m in rows]


@app.post("/api/admin/bookings", dependencies=[Depends(require_admin)])
def admin_create_booking(body: BookingIn, db: Session = Depends(get_db)):
    if body.service not in SERVICES or body.frequency not in FREQUENCIES:
        raise HTTPException(422, "Invalid service or frequency")
    b = bk.create_booking(db, phone=normalise_phone(body.phone), service=body.service,
                          scheduled_date=body.scheduled_date, address=body.address, name=body.name,
                          frequency=body.frequency, source="admin")
    return _booking_dict(b)


@app.patch("/api/admin/bookings/{booking_id}", dependencies=[Depends(require_admin)])
def admin_update_booking(booking_id: int, body: StatusIn, db: Session = Depends(get_db)):
    b = db.get(Booking, booking_id)
    if not b:
        raise HTTPException(404, "Booking not found")
    try:
        nxt = bk.set_status(db, b, body.status)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"booking": _booking_dict(b), "next_booking": _booking_dict(nxt) if nxt else None}


@app.patch("/api/admin/quotes/{quote_id}", dependencies=[Depends(require_admin)])
def admin_update_quote(quote_id: int, body: StatusIn, db: Session = Depends(get_db)):
    q = db.get(Quote, quote_id)
    if not q:
        raise HTTPException(404, "Quote not found")
    if body.status not in ("new", "contacted", "booked", "lost"):
        raise HTTPException(422, "Invalid status")
    q.status = body.status
    db.commit()
    return _quote_dict(q)


@app.post("/api/admin/quotes/{quote_id}/book", dependencies=[Depends(require_admin)])
def admin_quote_to_booking(quote_id: int, db: Session = Depends(get_db)):
    q = db.get(Quote, quote_id)
    if not q:
        raise HTTPException(404, "Quote not found")
    if not q.preferred_date:
        raise HTTPException(422, "Quote has no preferred date; create the booking manually.")
    b = bk.create_booking(db, phone=q.phone, name=q.name, service=q.service, scheduled_date=q.preferred_date,
                          address=q.address, frequency=q.frequency, source="quote", quote_id=q.id)
    q.status = "booked"
    db.commit()
    return _booking_dict(b)


# ---------------------------------------------------------------- scheduler hook
@app.post("/internal/run-reminders", dependencies=[Depends(require_cron)])
def run_reminders(db: Session = Depends(get_db)):
    """Call once a day (GitHub Actions / cron-job.org). Idempotent: never double-sends."""
    return bk.run_reminders(db)


# ---------------------------------------------------------------- WhatsApp webhook
@app.get("/webhook/whatsapp")
def webhook_verify(request: Request):
    p = request.query_params
    if p.get("hub.mode") == "subscribe" and p.get("hub.verify_token") == get_settings().whatsapp_verify_token:
        return Response(content=p.get("hub.challenge", ""), media_type="text/plain")
    raise HTTPException(403, "Verification failed")


_seen: deque = deque(maxlen=2000)


@app.post("/webhook/whatsapp")
async def webhook_receive(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    secret = get_settings().whatsapp_app_secret
    if secret:
        sig = request.headers.get("x-hub-signature-256", "")
        expected = "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise HTTPException(403, "Bad signature")
    try:
        payload = json.loads(raw or b"{}")
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                names = {c.get("wa_id"): c.get("profile", {}).get("name") for c in value.get("contacts", [])}
                for m in value.get("messages", []):
                    if m.get("id") in _seen:
                        continue
                    _seen.append(m.get("id"))
                    phone = m.get("from", "")
                    text, button_id = "", ""
                    if m.get("type") == "text":
                        text = m["text"].get("body", "")
                    elif m.get("type") == "interactive":
                        br = m["interactive"].get("button_reply") or m["interactive"].get("list_reply") or {}
                        button_id, text = br.get("id", ""), br.get("title", "")
                    elif m.get("type") == "button":  # quick-reply on a template
                        button_id, text = m["button"].get("payload", ""), m["button"].get("text", "")
                    else:
                        text = ""
                    db.add(MessageLog(direction="in", phone=phone, body=text or f"[{m.get('type')}]", mode="live"))
                    db.commit()
                    flow.handle_message(db, phone, text=text, button_id=button_id, name=names.get(phone))
    except Exception:  # always 200 so Meta doesn't retry-storm; the error is logged
        log.exception("webhook processing failed")
    return {"status": "ok"}
