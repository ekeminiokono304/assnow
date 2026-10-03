"""Central configuration: environment settings + the editable pricing table.

Edit PRICING / BUSINESS below to change quotes without touching any other code.
All prices are in Nigerian Naira (NGN) and are PLACEHOLDERS: replace them with
the owner's real rates before going live.
"""
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


@dataclass
class Settings:
    database_url: str = field(default_factory=lambda: _env("DATABASE_URL", "sqlite:///./assnow.db"))
    admin_password: str = field(default_factory=lambda: _env("ADMIN_PASSWORD", "change-me"))
    secret_key: str = field(default_factory=lambda: _env("SECRET_KEY", "dev-secret-change-me"))
    cron_secret: str = field(default_factory=lambda: _env("CRON_SECRET", "change-me-too"))
    cors_origins: list = field(
        default_factory=lambda: [o.strip() for o in _env("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
    )
    timezone: str = field(default_factory=lambda: _env("TIMEZONE", "Africa/Lagos"))

    # WhatsApp Cloud API. Mock mode is used automatically when no token is set.
    whatsapp_mode: str = field(default_factory=lambda: _env("WHATSAPP_MODE", "auto"))  # auto | mock | live
    whatsapp_token: str = field(default_factory=lambda: _env("WHATSAPP_TOKEN"))
    whatsapp_phone_number_id: str = field(default_factory=lambda: _env("WHATSAPP_PHONE_NUMBER_ID"))
    whatsapp_verify_token: str = field(default_factory=lambda: _env("WHATSAPP_VERIFY_TOKEN", "assnow-verify"))
    whatsapp_app_secret: str = field(default_factory=lambda: _env("WHATSAPP_APP_SECRET"))
    owner_whatsapp: str = field(default_factory=lambda: _env("OWNER_WHATSAPP"))  # e.g. 2348061380762
    graph_api_version: str = field(default_factory=lambda: _env("GRAPH_API_VERSION", "v21.0"))

    # Approved template names (see README / docs/whatsapp-templates.md)
    tpl_reminder: str = field(default_factory=lambda: _env("TPL_REMINDER", "clean_reminder"))
    tpl_owner_alert: str = field(default_factory=lambda: _env("TPL_OWNER_ALERT", "new_lead_alert"))
    tpl_language: str = field(default_factory=lambda: _env("TPL_LANGUAGE", "en"))

    @property
    def live_whatsapp(self) -> bool:
        if self.whatsapp_mode == "mock":
            return False
        if self.whatsapp_mode == "live":
            return True
        return bool(self.whatsapp_token and self.whatsapp_phone_number_id)


def get_settings() -> Settings:
    # Re-read on each call so tests can monkeypatch the environment.
    return Settings()


BUSINESS = {
    "name": "As Snow Cleaning & Pest Control",
    "city": "Lagos",
    "reminder_hour_note": "Reminders go out the day before the visit.",
}

# Services offered. key -> label shown to customers.
SERVICES = {
    "home_cleaning": "Home Cleaning",
    "office_cleaning": "Office Cleaning",
    "pest_control": "Pest Control",
    "fumigation": "Fumigation",
}

PROPERTY_SIZES = {
    "small": "Small (studio / 1-bed / small shop)",
    "medium": "Medium (2-3 bed / small office)",
    "large": "Large (4+ bed / duplex / big office)",
}

FREQUENCIES = {
    "once": "One-time",
    "weekly": "Weekly",
    "biweekly": "Every 2 weeks",
    "monthly": "Monthly",
}
FREQUENCY_DAYS = {"weekly": 7, "biweekly": 14, "monthly": 30}

# Base price by service and property size (NGN) + extra per room beyond the first.
PRICING = {
    "home_cleaning": {"base": {"small": 25000, "medium": 40000, "large": 65000}, "per_room": 5000},
    "office_cleaning": {"base": {"small": 35000, "medium": 60000, "large": 100000}, "per_room": 7000},
    "pest_control": {"base": {"small": 30000, "medium": 50000, "large": 80000}, "per_room": 4000},
    "fumigation": {"base": {"small": 40000, "medium": 70000, "large": 110000}, "per_room": 6000},
}

# Estimate shown as a range around the computed price.
RANGE_LOW = 0.90
RANGE_HIGH = 1.20

# Discount applied to recurring plans.
RECURRING_DISCOUNT = {"once": 0.0, "weekly": 0.15, "biweekly": 0.10, "monthly": 0.05}

# Round displayed estimates to the nearest N naira.
ROUND_TO = 500

SERVICE_AREAS = [
    "Gbagada", "Yaba", "Surulere", "Ikeja", "Maryland", "Ojota",
    "Anthony", "Lekki", "Victoria Island", "Ikoyi", "Ajah", "Magodo",
]

# Fixed-hour "slots" are not collected; the team confirms the exact time by WhatsApp.
