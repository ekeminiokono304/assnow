"""Booking lifecycle: creation, completion (auto-creating the next recurring visit) and reminders."""
import calendar
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import whatsapp
from .config import FREQUENCY_DAYS, SERVICES, get_settings
from .models import Booking
from .util import fmt_date, today_local

ACTIVE = ("pending", "confirmed", "reschedule_requested")
VALID_STATUSES = ("pending", "confirmed", "reschedule_requested", "completed", "cancelled")


def add_interval(d: date, frequency: str) -> date:
    if frequency == "monthly":
        month = d.month % 12 + 1
        year = d.year + (1 if d.month == 12 else 0)
        return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))
    return d + timedelta(days=FREQUENCY_DAYS[frequency])


def create_booking(db: Session, *, phone: str, service: str, scheduled_date: date, address: str,
                   name: str | None = None, frequency: str = "once", source: str = "whatsapp",
                   quote_id: int | None = None, parent_id: int | None = None) -> Booking:
    b = Booking(phone=phone, name=name, service=service, scheduled_date=scheduled_date, address=address,
                frequency=frequency, source=source, quote_id=quote_id, parent_id=parent_id)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def complete_booking(db: Session, b: Booking) -> Booking | None:
    """Mark completed; if recurring, create the next visit (idempotent). Returns the new booking, if any."""
    b.status = "completed"
    db.commit()
    if b.frequency == "once":
        return None
    existing = db.scalar(select(Booking).where(Booking.parent_id == b.id))
    if existing:
        return existing
    nxt = add_interval(b.scheduled_date, b.frequency)
    floor = today_local() + timedelta(days=1)
    while nxt < floor:  # visit was logged late: roll forward to the next future slot
        nxt = add_interval(nxt, b.frequency)
    return create_booking(db, phone=b.phone, name=b.name, service=b.service, scheduled_date=nxt,
                          address=b.address, frequency=b.frequency, source="recurring",
                          quote_id=b.quote_id, parent_id=b.id)


def set_status(db: Session, b: Booking, status: str) -> Booking | None:
    """Apply a status change. Returns the auto-created next booking when completing a recurring one."""
    if status not in VALID_STATUSES:
        raise ValueError("Invalid status")
    if status == "completed":
        return complete_booking(db, b)
    b.status = status
    db.commit()
    return None


def due_for_reminder(db: Session, today: date | None = None) -> list[Booking]:
    target = (today or today_local()) + timedelta(days=1)
    return list(db.scalars(
        select(Booking).where(Booking.scheduled_date == target,
                              Booking.status.in_(("pending", "confirmed")),
                              Booking.reminder_sent_at.is_(None))
        .order_by(Booking.id)))


def upcoming_reminders(db: Session, days: int = 7) -> list[Booking]:
    """What will be reminded in the next N days (for the admin view)."""
    today = today_local()
    return list(db.scalars(
        select(Booking).where(Booking.scheduled_date > today,
                              Booking.scheduled_date <= today + timedelta(days=days + 1),
                              Booking.status.in_(("pending", "confirmed")))
        .order_by(Booking.scheduled_date, Booking.id)))


def run_reminders(db: Session, today: date | None = None) -> dict:
    """Send the day-before reminder for every due booking. Safe to run repeatedly (idempotent)."""
    s = get_settings()
    sent = failed = 0
    for b in due_for_reminder(db, today):
        ok = whatsapp.send_template(
            db, b.phone, s.tpl_reminder,
            [b.name or "there", SERVICES.get(b.service, b.service), fmt_date(b.scheduled_date), b.address],
            [f"confirm:{b.id}", f"reschedule:{b.id}"])
        if ok:
            b.reminder_sent_at = datetime.now(timezone.utc)
            db.commit()
            sent += 1
        else:
            failed += 1
    return {"sent": sent, "failed": failed}
