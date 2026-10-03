# WhatsApp templates to submit to Meta

Submit these in **WhatsApp Manager → Message templates → Create template**.
Category for both: **Utility**. Language: **English** (code `en`). Names must match `TPL_*` in `.env`.

Why templates? WhatsApp only allows free-form messages within 24 hours of the customer's last message.
Reminders and owner alerts are business-initiated, so they must use approved templates.

---

## 1. `clean_reminder`  (customer reminder, sent the day before a visit)

**Body**

```
Hi {{1}}, a quick reminder from As Snow Cleaning & Pest Control. 🧼

Your {{2}} is scheduled for {{3}} at {{4}}.

Please confirm so our team can plan, or let us know if you need a different date.
```

**Buttons** (type: *Quick reply*, in this order, because the API sends payloads `confirm:<id>` and `reschedule:<id>` by index):

1. `Confirm`
2. `Reschedule`

**Sample values for Meta's review form:** {{1}} = Ngozi · {{2}} = Home Cleaning · {{3}} = Friday 9 October 2026 · {{4}} = 12 Gbagada Expressway, Lagos

---

## 2. `new_lead_alert`  (owner alert for new quotes, bookings and customer replies)

**Body**

```
As Snow alert: {{1}}

Service: {{2}}
Details: {{3}}
Customer: {{4}}
```

No buttons.

**Sample values:** {{1}} = Quote #12 · {{2}} = Pest Control (Gbagada) · {{3}} = ₦82,000-₦109,500 · {{4}} = Ada Obi +2348031112222

---

### Tips for fast approval
- Keep the category as Utility and don't add promotional wording or discount offers.
- Don't edit the placeholders: the code fills exactly {{1}}–{{4}} as above.
- Approval usually takes minutes to a day. Until it's approved, leave `WHATSAPP_TOKEN` empty (mock mode) or the sends will fail and show as `error` in the admin log.
