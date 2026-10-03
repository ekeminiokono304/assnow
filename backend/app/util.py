import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from .config import get_settings

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}


def today_local() -> date:
    return datetime.now(ZoneInfo(get_settings().timezone)).date()


def normalise_phone(raw: str) -> str:
    """Return digits-only international format (WhatsApp style), defaulting to Nigeria."""
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 11:  # 0806 138 0762
        digits = "234" + digits[1:]
    elif len(digits) == 10 and digits[0] in "789":  # 806 138 0762
        digits = "234" + digits
    return digits


def valid_phone(raw: str) -> bool:
    d = normalise_phone(raw)
    return 10 <= len(d) <= 15


def parse_date(text: str, today: date | None = None) -> date | None:
    """Parse friendly dates. Returns None if it can't. Caller checks it isn't in the past."""
    today = today or today_local()
    t = (text or "").strip().lower()
    if not t:
        return None
    if t in ("today",):
        return today
    if t in ("tomorrow", "tmrw", "tmr"):
        return today + timedelta(days=1)
    t_clean = re.sub(r"\b(next|this|on|the)\b", " ", t)
    t_clean = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", t_clean).strip()
    for i, wd in enumerate(WEEKDAYS):
        if t_clean.startswith(wd) or t_clean.startswith(wd[:3] + " ") or t_clean == wd[:3]:
            delta = (i - today.weekday()) % 7
            return today + timedelta(days=delta or 7)
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", t_clean)
    if m:
        return _safe(int(m[1]), int(m[2]), int(m[3]))
    m = re.fullmatch(r"(\d{1,2})[/.\-](\d{1,2})(?:[/.\-](\d{2,4}))?", t_clean)
    if m:
        d, mo = int(m[1]), int(m[2])
        y = int(m[3]) if m[3] else today.year
        if y < 100:
            y += 2000
        res = _safe(y, mo, d)
        if res and not m[3] and res < today:
            res = _safe(y + 1, mo, d)
        return res
    m = re.fullmatch(r"(\d{1,2})\s*([a-z]{3,9})(?:\s+(\d{4}))?", t_clean) or None
    if m and m[2][:3] in MONTHS:
        y = int(m[3]) if m[3] else today.year
        res = _safe(y, MONTHS[m[2][:3]], int(m[1]))
        if res and not m[3] and res < today:
            res = _safe(y + 1, MONTHS[m[2][:3]], int(m[1]))
        return res
    m = re.fullmatch(r"([a-z]{3,9})\s+(\d{1,2})(?:\s+(\d{4}))?", t_clean)
    if m and m[1][:3] in MONTHS:
        y = int(m[3]) if m[3] else today.year
        res = _safe(y, MONTHS[m[1][:3]], int(m[2]))
        if res and not m[3] and res < today:
            res = _safe(y + 1, MONTHS[m[1][:3]], int(m[2]))
        return res
    return None


def _safe(y: int, m: int, d: int) -> date | None:
    try:
        return date(y, m, d)
    except ValueError:
        return None


def fmt_date(d: date) -> str:
    return f"{d.strftime('%A')} {d.day} {d.strftime('%B %Y')}"


def naira(n: int) -> str:
    return f"₦{n:,}"
