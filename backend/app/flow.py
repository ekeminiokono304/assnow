"""WhatsApp conversation flow: service -> date -> address -> confirm, plus reminder replies."""
import re
from datetime import timedelta

from sqlalchemy.orm import Session

from . import bookings, whatsapp
from .config import BUSINESS, SERVICES
from .models import Booking, Conversation
from .util import fmt_date, parse_date, today_local

SERVICE_KEYS = list(SERVICES)
RESTART_WORDS = {"hi", "hello", "hey", "menu", "start", "book", "booking", "restart", "hello!", "hi!"}
CANCEL_WORDS = {"cancel", "stop", "exit", "quit"}
YES = {"yes", "y", "confirm", "ok", "okay", "yep", "1", "book", "sure", "correct"}
NO = {"no", "n", "nope", "2", "change"}


def _menu_text() -> str:
    lines = [f"{i}. {label}" for i, label in enumerate(SERVICES.values(), 1)]
    return "Which service would you like to book?\n" + "\n".join(lines) + "\n\nReply with a number (1-4)."


def _get(db: Session, phone: str) -> Conversation:
    c = db.get(Conversation, phone)
    if not c:
        c = Conversation(phone=phone, state="idle", data={})
        db.add(c)
        db.commit()
    return c


def _set(db: Session, c: Conversation, state: str, data: dict | None = None) -> None:
    c.state = state
    if data is not None:
        c.data = data
    db.commit()


def _match_service(text: str) -> str | None:
    t = text.strip().lower()
    if t.isdigit() and 1 <= int(t) <= len(SERVICE_KEYS):
        return SERVICE_KEYS[int(t) - 1]
    hits = []
    for key, label in SERVICES.items():
        words = label.lower().split()
        if t == label.lower() or t == key or label.lower() in t or (t in words and len(t) > 3):
            hits.append(key)
    return hits[0] if len(hits) == 1 else None  # ambiguous ("cleaning") -> ask again


def handle_message(db: Session, phone: str, text: str = "", button_id: str = "", name: str | None = None) -> None:
    """Entry point for every inbound customer message."""
    text = (text or "").strip()
    low = text.lower()

    # 1) Buttons from the reminder template / interactive replies
    if button_id and ":" in button_id:
        action, _, bid = button_id.partition(":")
        if action in ("confirm", "reschedule") and bid.isdigit():
            return _handle_reminder_reply(db, phone, action, int(bid))
    if button_id in ("book_yes", "book_no"):
        low = "yes" if button_id == "book_yes" else "no"

    c = _get(db, phone)

    if low in CANCEL_WORDS:
        _set(db, c, "idle", {})
        return _say(db, phone, "No problem, I've cancelled that. Send *Hi* any time to book again.")

    if c.state in ("idle", "") or low in RESTART_WORDS:
        _set(db, c, "service", {"name": name})
        greet = f"Hello{', ' + name if name else ''}! 👋 Welcome to {BUSINESS['name']}.\n\n"
        return _say(db, phone, greet + _menu_text())

    data = dict(c.data or {})

    if c.state == "service":
        svc = _match_service(low)
        if not svc:
            return _say(db, phone, "Sorry, I didn't get that. " + _menu_text())
        data["service"] = svc
        _set(db, c, "date", data)
        return _say(db, phone, f"Great, *{SERVICES[svc]}*. 📅 What date would you like?\n"
                               "You can say *tomorrow*, *Friday*, or a date like *25/10*.")

    if c.state == "date":
        d = parse_date(low)
        if not d:
            return _say(db, phone, "I couldn't read that date. Try *tomorrow*, *Friday* or *25/10*.")
        if d < today_local() + timedelta(days=1):
            return _say(db, phone, "Please pick a date from tomorrow onwards.")
        data["date"] = d.isoformat()
        _set(db, c, "address", data)
        return _say(db, phone, "📍 What's the full address (street, area, landmark)?")

    if c.state == "address":
        if len(text) < 6:
            return _say(db, phone, "Please send the full address so our team can find you.")
        data["address"] = text[:250]
        _set(db, c, "confirm", data)
        d = parse_date(data["date"])
        summary = (f"Please confirm your booking:\n\n• Service: {SERVICES[data['service']]}\n"
                   f"• Date: {fmt_date(d)}\n• Address: {data['address']}\n")
        return _say_buttons(db, phone, summary, [("book_yes", "Yes, confirm"), ("book_no", "Start over")])

    if c.state == "confirm":
        if low in YES or low.startswith("yes"):
            d = parse_date(data["date"])
            b = bookings.create_booking(db, phone=phone, name=data.get("name") or name,
                                        service=data["service"], scheduled_date=d, address=data["address"])
            _set(db, c, "idle", {})
            whatsapp.notify_owner(
                db, f"📥 New WhatsApp booking #{b.id}\n{SERVICES[b.service]} on {fmt_date(d)}\n"
                    f"{b.address}\nCustomer: {b.name or 'n/a'} +{phone}",
                [f"Booking #{b.id}", SERVICES[b.service], fmt_date(d), f"+{phone}"])
            return _say(db, phone, f"✅ Booked! Your reference is *#{b.id}*.\n"
                                   "Our team will message you to confirm the time. "
                                   "We'll also remind you the day before.")
        if low in NO or low.startswith("no") or "start over" in low:
            _set(db, c, "service", {"name": data.get("name") or name})
            return _say(db, phone, "Okay, let's start again.\n\n" + _menu_text())
        return _say_buttons(db, phone, "Shall I confirm this booking?",
                            [("book_yes", "Yes, confirm"), ("book_no", "Start over")])

    if c.state == "reschedule":
        d = parse_date(low)
        b = db.get(Booking, data.get("booking_id", 0))
        if not d or d < today_local() + timedelta(days=1):
            return _say(db, phone, "Please send a new date from tomorrow onwards, e.g. *Friday* or *25/10*.")
        if not b or b.phone != phone:
            _set(db, c, "idle", {})
            return _say(db, phone, "Sorry, I couldn't find that booking. Send *Hi* to book again.")
        b.scheduled_date, b.status, b.reminder_sent_at = d, "pending", None
        db.commit()
        _set(db, c, "idle", {})
        whatsapp.notify_owner(db, f"🔁 Booking #{b.id} rescheduled to {fmt_date(d)} (+{phone})",
                              [f"Booking #{b.id} rescheduled", SERVICES[b.service], fmt_date(d), f"+{phone}"])
        return _say(db, phone, f"Done ✅ Booking *#{b.id}* moved to *{fmt_date(d)}*. We'll remind you the day before.")

    _set(db, c, "idle", {})
    return _say(db, phone, "Send *Hi* to start a booking.")


def _handle_reminder_reply(db: Session, phone: str, action: str, booking_id: int) -> None:
    b = db.get(Booking, booking_id)
    if not b or b.phone != phone or b.status not in bookings.ACTIVE:
        return _say(db, phone, "Sorry, that booking is no longer active. Send *Hi* to make a new one.")
    if action == "confirm":
        b.status = "confirmed"
        db.commit()
        whatsapp.notify_owner(db, f"✅ Booking #{b.id} confirmed by customer (+{phone})",
                              [f"Booking #{b.id} confirmed", SERVICES[b.service], fmt_date(b.scheduled_date), f"+{phone}"])
        return _say(db, phone, f"Thank you! ✅ Booking *#{b.id}* is confirmed for *{fmt_date(b.scheduled_date)}*. See you then!")
    b.status = "reschedule_requested"
    db.commit()
    c = _get(db, phone)
    _set(db, c, "reschedule", {"booking_id": b.id})
    whatsapp.notify_owner(db, f"⚠️ Booking #{b.id} reschedule requested (+{phone})",
                          [f"Booking #{b.id} reschedule requested", SERVICES[b.service], fmt_date(b.scheduled_date), f"+{phone}"])
    return _say(db, phone, "No problem. 📅 What new date works for you? (e.g. *Friday* or *25/10*)")


def _say(db: Session, phone: str, body: str) -> None:
    whatsapp.send_text(db, phone, body)


def _say_buttons(db: Session, phone: str, body: str, buttons: list[tuple[str, str]]) -> None:
    whatsapp.send_buttons(db, phone, body, buttons)
