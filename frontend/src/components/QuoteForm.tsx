"use client";
import { FormEvent, useState } from "react";
import { API_URL, BOOK_MESSAGE, FREQUENCIES, PROPERTY_SIZES, SERVICES, waLink } from "@/lib/site";
import { Icon, WhatsAppIcon } from "./Icons";

type Result = { id: number; est_low: number; est_high: number; frequency: string; message: string };
const naira = (n: number) => "₦" + n.toLocaleString("en-NG");

function tomorrowISO() {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return d.toISOString().slice(0, 10);
}

function friendlyError(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.loc) {
    const f = String(detail[0].loc[detail[0].loc.length - 1]).replace("_", " ");
    return `Please check the ${f} field.`;
  }
  return "Something went wrong. Please try again or message us on WhatsApp.";
}

export default function QuoteForm() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<Result | null>(null);
  const [freq, setFreq] = useState("once");
  const [summary, setSummary] = useState("");

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setBusy(true);
    const f = new FormData(e.currentTarget);
    const body = {
      name: String(f.get("name") || ""),
      phone: String(f.get("phone") || ""),
      service: String(f.get("service")),
      property_size: String(f.get("property_size")),
      rooms: Number(f.get("rooms") || 1),
      address: String(f.get("address") || ""),
      preferred_date: f.get("preferred_date") ? String(f.get("preferred_date")) : null,
      frequency: freq,
      website: String(f.get("website") || ""),
    };
    try {
      const r = await fetch(`${API_URL}/api/quotes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(friendlyError(data.detail));
      setSummary(`${SERVICES.find((s) => s.key === body.service)?.title}, ${body.rooms} room(s), ${body.address}`);
      setResult(data);
    } catch (err) {
      setError(
        err instanceof TypeError
          ? "Couldn't reach the server. Check your network and try again, or message us on WhatsApp."
          : (err as Error).message,
      );
    } finally {
      setBusy(false);
    }
  }

  if (result) {
    const recurring = result.frequency !== "once";
    return (
      <div className="rounded-3xl border border-snow-200 bg-snow-50 p-6 text-center sm:p-8" role="status">
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-snow-600 text-white">
          <Icon name="check" />
        </div>
        <h3 className="text-xl font-bold">Your instant estimate</h3>
        <p className="mt-2 text-3xl font-extrabold text-snow-700 sm:text-4xl">
          {naira(result.est_low)} – {naira(result.est_high)}
        </p>
        <p className="mt-1 text-sm text-ink/70">{recurring ? "per visit, recurring discount applied" : "for one visit"}</p>
        <p className="mx-auto mt-4 max-w-md text-ink/80">{result.message}</p>
        <a
          className="btn mt-5 bg-wa text-white hover:bg-wa-dark"
          target="_blank"
          rel="noopener noreferrer"
          href={waLink(`${BOOK_MESSAGE}\nQuote #${result.id}: ${summary}. Estimate ${naira(result.est_low)}-${naira(result.est_high)}.`)}
        >
          <WhatsAppIcon /> Continue on WhatsApp
        </a>
        <button className="mt-3 block w-full text-sm text-snow-700 underline" onClick={() => setResult(null)}>
          Get another quote
        </button>
        <p className="mt-4 text-xs text-ink/50">Estimate only. The final price is confirmed after we check the details.</p>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-4 rounded-3xl border border-snow-200 bg-white p-5 shadow-sm sm:p-8" noValidate={false}>
      {/* honeypot: hidden from people, bots fill it in */}
      <input name="website" tabIndex={-1} autoComplete="off" aria-hidden="true" className="hidden" />

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="label" htmlFor="service">Service</label>
          <select id="service" name="service" required className="field" defaultValue="home_cleaning">
            {SERVICES.map((s) => (<option key={s.key} value={s.key}>{s.title}</option>))}
          </select>
        </div>
        <div>
          <label className="label" htmlFor="property_size">Property size</label>
          <select id="property_size" name="property_size" required className="field" defaultValue="medium">
            {PROPERTY_SIZES.map((s) => (<option key={s.key} value={s.key}>{s.label}</option>))}
          </select>
        </div>
        <div>
          <label className="label" htmlFor="rooms">Number of rooms</label>
          <input id="rooms" name="rooms" type="number" inputMode="numeric" min={1} max={50} defaultValue={3} required className="field" />
        </div>
        <div>
          <label className="label" htmlFor="preferred_date">Preferred date</label>
          <input id="preferred_date" name="preferred_date" type="date" min={tomorrowISO()} className="field" />
        </div>
      </div>

      <div>
        <label className="label" htmlFor="address">Address / area</label>
        <input id="address" name="address" required minLength={3} maxLength={250} placeholder="e.g. 12 Gbagada Expressway, Gbagada" className="field" autoComplete="street-address" />
      </div>

      <fieldset>
        <legend className="label">How often?</legend>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {FREQUENCIES.map((f) => (
            <label key={f.key} className={`cursor-pointer rounded-xl border px-3 py-2.5 text-center text-sm transition ${freq === f.key ? "border-snow-600 bg-snow-100 font-semibold text-snow-700" : "border-snow-200 hover:bg-snow-50"}`}>
              <input type="radio" name="frequency" value={f.key} checked={freq === f.key} onChange={() => setFreq(f.key)} className="sr-only" />
              {f.label}
              {f.note && <span className="block text-xs font-normal text-wa-dark">{f.note}</span>}
            </label>
          ))}
        </div>
      </fieldset>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="label" htmlFor="name">Your name</label>
          <input id="name" name="name" required minLength={2} maxLength={100} className="field" autoComplete="name" />
        </div>
        <div>
          <label className="label" htmlFor="phone">Phone (WhatsApp)</label>
          <input id="phone" name="phone" type="tel" inputMode="tel" required placeholder="0803 123 4567" className="field" autoComplete="tel" />
        </div>
      </div>

      {error && <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}

      <button disabled={busy} className="btn w-full bg-snow-600 text-lg text-white hover:bg-snow-700 disabled:opacity-60">
        {busy ? "Calculating…" : "Get my instant quote"}
      </button>
    </form>
  );
}
