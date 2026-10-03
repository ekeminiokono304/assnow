from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from .config import FREQUENCIES, PROPERTY_SIZES, SERVICES
from .util import valid_phone


class QuoteIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=7, max_length=32)
    service: str
    property_size: str
    rooms: int = Field(ge=1, le=50)
    address: str = Field(min_length=3, max_length=255)
    preferred_date: date | None = None
    frequency: str = "once"
    website: str = ""  # honeypot: real users leave this empty

    @field_validator("service")
    @classmethod
    def _svc(cls, v):
        if v not in SERVICES:
            raise ValueError("Unknown service")
        return v

    @field_validator("property_size")
    @classmethod
    def _size(cls, v):
        if v not in PROPERTY_SIZES:
            raise ValueError("Unknown property size")
        return v

    @field_validator("frequency")
    @classmethod
    def _freq(cls, v):
        if v not in FREQUENCIES:
            raise ValueError("Unknown frequency")
        return v

    @field_validator("phone")
    @classmethod
    def _phone(cls, v):
        if not valid_phone(v):
            raise ValueError("Enter a valid phone number")
        return v


class QuoteOut(BaseModel):
    id: int
    est_low: int
    est_high: int
    frequency: str
    message: str


class LoginIn(BaseModel):
    password: str


class StatusIn(BaseModel):
    status: str


class BookingIn(BaseModel):
    phone: str
    service: str
    scheduled_date: date
    address: str
    name: str | None = None
    frequency: str = "once"
