"""WhatsApp Cloud API client with a mock mode.

Mock mode (default until WHATSAPP_TOKEN + WHATSAPP_PHONE_NUMBER_ID are set) never
touches the network: every message is written to message_log with mode='mock', which
the admin page displays. Live mode posts to the Graph API.
"""
import logging

import httpx
from sqlalchemy.orm import Session

from .config import get_settings
from .models import MessageLog

log = logging.getLogger("assnow.whatsapp")


def _record(db: Session, phone: str, body: str, mode: str, direction: str = "out") -> None:
    db.add(MessageLog(direction=direction, phone=phone, body=body, mode=mode))
    db.commit()


def _post(payload: dict) -> tuple[bool, str]:
    s = get_settings()
    url = f"https://graph.facebook.com/{s.graph_api_version}/{s.whatsapp_phone_number_id}/messages"
    try:
        r = httpx.post(url, json=payload, headers={"Authorization": f"Bearer {s.whatsapp_token}"}, timeout=15)
        if r.status_code >= 300:
            log.error("WhatsApp send failed %s: %s", r.status_code, r.text[:300])
            return False, r.text[:300]
        return True, ""
    except httpx.HTTPError as e:  # network problems must never crash the API
        log.error("WhatsApp send error: %s", e)
        return False, str(e)


def _send(db: Session, to: str, payload: dict, preview: str) -> bool:
    s = get_settings()
    if not to:
        return False
    if not s.live_whatsapp:
        _record(db, to, preview, "mock")
        return True
    ok, err = _post({"messaging_product": "whatsapp", "to": to, **payload})
    _record(db, to, preview if ok else f"{preview}  [FAILED: {err}]", "live" if ok else "error")
    return ok


def send_text(db: Session, to: str, body: str) -> bool:
    return _send(db, to, {"type": "text", "text": {"body": body, "preview_url": False}}, body)


def send_buttons(db: Session, to: str, body: str, buttons: list[tuple[str, str]]) -> bool:
    """Interactive reply buttons (max 3, title max 20 chars). Only valid inside the 24h window."""
    payload = {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "action": {"buttons": [{"type": "reply", "reply": {"id": i, "title": t[:20]}} for i, t in buttons[:3]]},
        },
    }
    preview = body + "\n" + "  ".join(f"[{t}]" for _, t in buttons)
    return _send(db, to, payload, preview)


def send_template(db: Session, to: str, name: str, body_params: list[str],
                  quick_reply_payloads: list[str] | None = None) -> bool:
    """Send an approved template. Required for business-initiated messages outside the 24h window."""
    s = get_settings()
    # Meta rejects template params containing newlines/tabs or long runs of spaces.
    body_params = [" ".join(str(p).split())[:900] or "-" for p in body_params]
    components = [{"type": "body", "parameters": [{"type": "text", "text": p} for p in body_params]}]
    for idx, payload in enumerate(quick_reply_payloads or []):
        components.append({"type": "button", "sub_type": "quick_reply", "index": str(idx),
                           "parameters": [{"type": "payload", "payload": payload}]})
    data = {"type": "template", "template": {"name": name, "language": {"code": s.tpl_language},
                                             "components": components}}
    preview = f"[template:{name}] " + " | ".join(body_params)
    if quick_reply_payloads:
        preview += "  buttons=" + ",".join(quick_reply_payloads)
    return _send(db, to, data, preview)


def notify_owner(db: Session, text: str, params: list[str]) -> bool:
    """Alert the owner. Uses the approved template in live mode (owner may be outside the 24h window)."""
    s = get_settings()
    if not s.owner_whatsapp:
        log.warning("OWNER_WHATSAPP not set; owner not notified")
        return False
    if s.live_whatsapp:
        return send_template(db, s.owner_whatsapp, s.tpl_owner_alert, params)
    return send_text(db, s.owner_whatsapp, text)
