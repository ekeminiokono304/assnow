from datetime import date, timedelta

from sqlalchemy import select

from app import bookings as bk
from app import flow
from app.models import Booking, Conversation, MessageLog
from app.pricing import estimate
from app.util import normalise_phone, parse_date, today_local

QUOTE = {"name": "Ada", "phone": "0803 111 2222", "service": "home_cleaning", "property_size": "medium",
         "rooms": 3, "address": "12 Gbagada Rd, Lagos", "frequency": "weekly"}


# ---------------------------------------------------------------- helpers
def test_phone_normalisation():
    assert normalise_phone("0806 138 0762") == "2348061380762"
    assert normalise_phone("+234 806 138 0762") == "2348061380762"
    assert normalise_phone("8061380762") == "2348061380762"


def test_parse_date():
    today = date(2026, 10, 3)  # Saturday
    assert parse_date("tomorrow", today) == date(2026, 10, 4)
    assert parse_date("friday", today) == date(2026, 10, 9)
    assert parse_date("next saturday", today) == date(2026, 10, 10)
    assert parse_date("2026-10-20", today) == date(2026, 10, 20)
    assert parse_date("25/10", today) == date(2026, 10, 25)
    assert parse_date("1/1", today) == date(2027, 1, 1)
    assert parse_date("5 nov", today) == date(2026, 11, 5)
    assert parse_date("nov 5th", today) == date(2026, 11, 5)
    assert parse_date("banana", today) is None


def test_pricing():
    low, high = estimate("home_cleaning", "medium", 3, "once")
    assert (low, high) == (45000, 60000)  # base 40000 + 2*5000 = 50000 -> x0.9 / x1.2
    wl, wh = estimate("home_cleaning", "medium", 3, "weekly")
    assert wl < low and wh < high


# ---------------------------------------------------------------- quotes
def test_quote_saves_estimates_and_alerts_owner(client, db):
    r = client.post("/api/quotes", json=QUOTE)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["est_low"] < body["est_high"] and body["id"] > 0
    out = db.scalars(select(MessageLog).where(MessageLog.direction == "out")).all()
    assert len(out) == 1 and out[0].phone == "2348061380762" and "Ada" in out[0].body


def test_quote_validation(client):
    assert client.post("/api/quotes", json={**QUOTE, "service": "nope"}).status_code == 422
    assert client.post("/api/quotes", json={**QUOTE, "phone": "12"}).status_code == 422
    assert client.post("/api/quotes", json={**QUOTE, "rooms": 0}).status_code == 422


def test_quote_honeypot_stores_nothing(client, admin):
    client.post("/api/quotes", json={**QUOTE, "website": "http://spam"})
    assert client.get("/api/admin/quotes", headers=admin).json() == []


# ---------------------------------------------------------------- admin auth
def test_admin_requires_auth(client):
    assert client.get("/api/admin/quotes").status_code == 401
    assert client.get("/api/admin/quotes", headers={"Authorization": "Bearer junk"}).status_code == 401
    assert client.post("/api/admin/login", json={"password": "bad"}).status_code == 401


def test_admin_lists(client, admin):
    client.post("/api/quotes", json=QUOTE)
    assert len(client.get("/api/admin/quotes", headers=admin).json()) == 1
    assert client.get("/api/admin/bookings", headers=admin).json() == []
    assert client.get("/api/admin/reminders", headers=admin).json() == []
    assert len(client.get("/api/admin/messages", headers=admin).json()) == 1


# ---------------------------------------------------------------- WhatsApp flow
def chat(db, phone, *texts):
    for t in texts:
        flow.handle_message(db, phone, text=t, name="Chidi")


def last_out(db, phone):
    return db.scalars(select(MessageLog).where(MessageLog.phone == phone).order_by(MessageLog.id.desc())).first().body


def test_full_booking_flow(db):
    phone = "2348090000001"
    chat(db, phone, "hi", "3", "tomorrow", "5 Allen Avenue, Ikeja")
    assert "confirm your booking" in last_out(db, phone)
    chat(db, phone, "yes")
    b = db.scalars(select(Booking)).one()
    assert (b.service, b.phone, b.status) == ("pest_control", phone, "pending")
    assert b.scheduled_date == today_local() + timedelta(days=1) and b.name == "Chidi"
    assert "Booked" in last_out(db, "2348061380762") or "New WhatsApp booking" in last_out(db, "2348061380762")
    assert db.get(Conversation, phone).state == "idle"


def test_flow_rejects_bad_input_and_restarts(db):
    phone = "2348090000002"
    chat(db, phone, "hello", "9")
    assert "didn't get that" in last_out(db, phone)
    chat(db, phone, "fumigation", "yesterday-ish")
    assert "couldn't read" in last_out(db, phone)
    chat(db, phone, "2020-01-01")
    assert "tomorrow onwards" in last_out(db, phone)
    chat(db, phone, "cancel")
    assert db.get(Conversation, phone).state == "idle"
    assert db.scalars(select(Booking)).all() == []


def test_confirm_no_restarts(db):
    phone = "2348090000003"
    chat(db, phone, "hi", "1", "friday", "10 Yaba Road, Lagos", "no")
    assert db.get(Conversation, phone).state == "service"


# ---------------------------------------------------------------- reminders
def make_booking(db, days=1, freq="weekly", phone="2348090000009"):
    return bk.create_booking(db, phone=phone, name="Ngozi", service="home_cleaning",
                             scheduled_date=today_local() + timedelta(days=days), address="1 Test St, Lagos",
                             frequency=freq)


def test_reminders_sent_once_with_buttons(db):
    b = make_booking(db, days=1)
    make_booking(db, days=3)
    assert bk.run_reminders(db) == {"sent": 1, "failed": 0}
    assert bk.run_reminders(db) == {"sent": 0, "failed": 0}  # idempotent
    msg = last_out(db, b.phone)
    assert "template:clean_reminder" in msg and f"confirm:{b.id}" in msg and f"reschedule:{b.id}" in msg
    assert db.get(Booking, b.id).reminder_sent_at is not None


def test_reminder_endpoint_needs_secret(client, db):
    make_booking(db)
    assert client.post("/internal/run-reminders").status_code == 401
    r = client.post("/internal/run-reminders", headers={"x-cron-secret": "cron"})
    assert r.json()["sent"] == 1


def test_confirm_reply(db):
    b = make_booking(db)
    flow.handle_message(db, b.phone, button_id=f"confirm:{b.id}")
    assert db.get(Booking, b.id).status == "confirmed"


def test_reschedule_reply_flow(db):
    b = make_booking(db)
    bk.run_reminders(db)
    flow.handle_message(db, b.phone, button_id=f"reschedule:{b.id}")
    assert db.get(Booking, b.id).status == "reschedule_requested"
    chat(db, b.phone, "in 5 days?")  # unparseable -> asks again
    assert "new date" in last_out(db, b.phone)
    new = today_local() + timedelta(days=9)
    chat(db, b.phone, new.isoformat())
    row = db.get(Booking, b.id)
    assert row.scheduled_date == new and row.status == "pending" and row.reminder_sent_at is None


def test_reply_for_someone_elses_booking_is_rejected(db):
    b = make_booking(db)
    flow.handle_message(db, "2348099999999", button_id=f"confirm:{b.id}")
    assert db.get(Booking, b.id).status == "pending"


# ---------------------------------------------------------------- recurring
def test_completing_creates_next_recurring_once(client, db, admin):
    b = make_booking(db, days=1, freq="biweekly")
    r1 = client.patch(f"/api/admin/bookings/{b.id}", json={"status": "completed"}, headers=admin).json()
    nxt = r1["next_booking"]
    assert nxt["scheduled_date"] == str(b.scheduled_date + timedelta(days=14)) and nxt["parent_id"] == b.id
    assert nxt["source"] == "recurring" and nxt["status"] == "pending"
    r2 = client.patch(f"/api/admin/bookings/{b.id}", json={"status": "completed"}, headers=admin).json()
    assert r2["next_booking"]["id"] == nxt["id"]  # no duplicate
    assert len(db.scalars(select(Booking)).all()) == 2


def test_one_time_does_not_recur(client, db, admin):
    b = make_booking(db, freq="once")
    r = client.patch(f"/api/admin/bookings/{b.id}", json={"status": "completed"}, headers=admin).json()
    assert r["next_booking"] is None


def test_late_completion_rolls_forward_to_future(db):
    b = make_booking(db, days=-30, freq="weekly")
    nxt = bk.complete_booking(db, b)
    assert nxt.scheduled_date >= today_local() + timedelta(days=1)


def test_monthly_interval_clamps_month_end():
    assert bk.add_interval(date(2026, 1, 31), "monthly") == date(2026, 2, 28)
    assert bk.add_interval(date(2026, 12, 15), "monthly") == date(2027, 1, 15)


def test_quote_to_booking(client, admin):
    pref = (today_local() + timedelta(days=5)).isoformat()
    q = client.post("/api/quotes", json={**QUOTE, "preferred_date": pref}).json()
    b = client.post(f"/api/admin/quotes/{q['id']}/book", headers=admin).json()
    assert b["scheduled_date"] == pref and b["source"] == "quote" and b["frequency"] == "weekly"


# ---------------------------------------------------------------- webhook
def test_webhook_verification(client):
    ok = client.get("/webhook/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": "assnow-verify",
                                                 "hub.challenge": "1234"})
    assert ok.status_code == 200 and ok.text == "1234"
    assert client.get("/webhook/whatsapp", params={"hub.mode": "subscribe", "hub.verify_token": "x",
                                                   "hub.challenge": "1"}).status_code == 403


def wa_payload(msg, name="Tunde"):
    return {"entry": [{"changes": [{"value": {"contacts": [{"wa_id": msg["from"], "profile": {"name": name}}],
                                              "messages": [msg]}}]}]}


def test_webhook_text_and_template_button(client, db):
    phone = "2348070000001"
    r = client.post("/webhook/whatsapp", json=wa_payload(
        {"from": phone, "id": "wamid.1", "type": "text", "text": {"body": "hi"}}))
    assert r.status_code == 200
    assert "Welcome" in last_out(db, phone) and "Tunde" in last_out(db, phone)

    b = make_booking(db, phone=phone)
    client.post("/webhook/whatsapp", json=wa_payload(
        {"from": phone, "id": "wamid.2", "type": "button", "button": {"payload": f"confirm:{b.id}", "text": "Confirm"}}))
    db.expire_all()
    assert db.get(Booking, b.id).status == "confirmed"

    client.post("/webhook/whatsapp", json=wa_payload(
        {"from": phone, "id": "wamid.3", "type": "interactive",
         "interactive": {"type": "button_reply", "button_reply": {"id": f"reschedule:{b.id}", "title": "Reschedule"}}}))
    db.expire_all()
    assert db.get(Booking, b.id).status == "reschedule_requested"


def test_webhook_ignores_duplicates_and_garbage(client, db):
    msg = {"from": "2348070000002", "id": "wamid.dup", "type": "text", "text": {"body": "hi"}}
    client.post("/webhook/whatsapp", json=wa_payload(msg))
    client.post("/webhook/whatsapp", json=wa_payload(msg))
    assert len(db.scalars(select(MessageLog).where(MessageLog.direction == "out")).all()) == 1
    assert client.post("/webhook/whatsapp", content=b"not json").status_code == 200


def test_webhook_signature_enforced(client, monkeypatch):
    import hashlib
    import hmac as h
    monkeypatch.setenv("WHATSAPP_APP_SECRET", "s3cret")
    body = b'{"entry": []}'
    assert client.post("/webhook/whatsapp", content=body, headers={"x-hub-signature-256": "sha256=bad"}).status_code == 403
    sig = "sha256=" + h.new(b"s3cret", body, hashlib.sha256).hexdigest()
    assert client.post("/webhook/whatsapp", content=body, headers={"x-hub-signature-256": sig}).status_code == 200


def test_template_params_are_sanitised(db, monkeypatch):
    from app import whatsapp
    monkeypatch.setenv("WHATSAPP_MODE", "live")
    monkeypatch.setenv("WHATSAPP_TOKEN", "t")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "1")
    sent = {}
    monkeypatch.setattr(whatsapp, "_post", lambda payload: (sent.update(payload) or (True, "")))
    whatsapp.send_template(db, "2348000000000", "clean_reminder", ["A\nB\t C", ""], ["confirm:1"])
    params = sent["template"]["components"][0]["parameters"]
    assert params[0]["text"] == "A B C" and params[1]["text"] == "-"
    assert sent["template"]["components"][1]["parameters"][0]["payload"] == "confirm:1"
    assert db.scalars(select(MessageLog).order_by(MessageLog.id.desc())).first().mode == "live"
