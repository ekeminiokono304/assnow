from datetime import date, datetime, timezone

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(32), index=True)
    service: Mapped[str] = mapped_column(String(32))
    property_size: Mapped[str] = mapped_column(String(16))
    rooms: Mapped[int] = mapped_column(Integer)
    address: Mapped[str] = mapped_column(String(255))
    preferred_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    frequency: Mapped[str] = mapped_column(String(16), default="once")
    est_low: Mapped[int] = mapped_column(Integer)
    est_high: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16), default="new")  # new | contacted | booked | lost
    owner_notified: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    phone: Mapped[str] = mapped_column(String(32), index=True)
    service: Mapped[str] = mapped_column(String(32))
    scheduled_date: Mapped[date] = mapped_column(Date, index=True)
    address: Mapped[str] = mapped_column(String(255))
    frequency: Mapped[str] = mapped_column(String(16), default="once")
    # pending | confirmed | reschedule_requested | completed | cancelled
    status: Mapped[str] = mapped_column(String(24), default="pending", index=True)
    source: Mapped[str] = mapped_column(String(16), default="whatsapp")  # whatsapp | quote | admin | recurring
    quote_id: Mapped[int | None] = mapped_column(ForeignKey("quotes.id"), nullable=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("bookings.id"), nullable=True)
    reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Conversation(Base):
    """Per-customer WhatsApp conversation state for the booking flow."""

    __tablename__ = "conversations"

    phone: Mapped[str] = mapped_column(String(32), primary_key=True)
    state: Mapped[str] = mapped_column(String(24), default="idle")
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class MessageLog(Base):
    """Every outbound/inbound WhatsApp message (and mock sends) for debugging + admin view."""

    __tablename__ = "message_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    direction: Mapped[str] = mapped_column(String(8))  # in | out
    phone: Mapped[str] = mapped_column(String(32), index=True)
    body: Mapped[str] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(String(8), default="mock")  # mock | live | error
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
