"use client";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { API_URL } from "@/lib/site";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Tab = "quotes" | "bookings" | "reminders" | "messages";
const TABS: { key: Tab; label: string }[] = [
  { key: "quotes", label: "Quotes" },
  { key: "bookings", label: "Bookings" },
  { key: "reminders", label: "Upcoming reminders" },
  { key: "messages", label: "WhatsApp log" },
];
const BOOKING_STATUSES = ["pending", "confirmed", "reschedule_requested", "completed", "cancelled"];
const QUOTE_STATUSES = ["new", "contacted", "booked", "lost"];
const SERVICE: Record<string, string> = { home_cleaning: "Home cleaning", office_cleaning: "Office cleaning", pest_control: "Pest control", fumigation: "Fumigation" };
const naira = (n: number) => "₦" + n.toLocaleString("en-NG");
const when = (s: string) => new Date(s).toLocaleString("en-NG", { dateStyle: "medium", timeStyle: "short" });

function store(get: boolean, v?: string): string {
  try { if (get) return sessionStorage.getItem("assnow_token") || ""; v ? sessionStorage.setItem("assnow_token", v) : sessionStorage.removeItem("assnow_token"); } catch { /* storage unavailable */ }
  return "";
}

export default function AdminPanel() {
  const [token, setToken] = useState("");
  const [tab, setTab] = useState<Tab>("quotes");
  const [rows, setRows] = useState<any[]>([]);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => { setToken(store(true)); }, []);

  const call = useCallback(async (path: string, init?: RequestInit) => {
    const r = await fetch(`${API_URL}${path}`, { ...init, headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}`, ...(init?.headers || {}) } });
    if (r.status === 401) { store(false); setToken(""); throw new Error("Session expired. Please log in again."); }
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Request failed");
    return data;
  }, [token]);

  const load = useCallback(async (keepMsg = false) => {
    if (!token) return;
    setLoading(true); if (!keepMsg) setMsg("");
    try { setRows(await call(`/api/admin/${tab}`)); } catch (e) { setMsg((e as Error).message); } finally { setLoading(false); }
  }, [token, tab, call]);

  useEffect(() => { load(); }, [load]);

  async function login(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const pw = String(new FormData(e.currentTarget).get("password"));
    setMsg("");
    try {
      const r = await fetch(`${API_URL}/api/admin/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ password: pw }) });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.detail || "Login failed");
      store(false, d.token); setToken(d.token);
    } catch (err) { setMsg(err instanceof TypeError ? "Can't reach the server." : (err as Error).message); }
  }

  async function act(fn: () => Promise<any>, ok: string) {
    try { const r = await fn(); setMsg(ok + (r?.next_booking ? ` Next visit created for ${r.next_booking.scheduled_date}.` : "")); await load(true); }
    catch (e) { setMsg((e as Error).message); }
  }

  if (!token) {
    return (
      <form onSubmit={login} className="mx-auto mt-24 max-w-sm space-y-4 rounded-2xl border border-snow-200 p-6">
        <h1 className="text-xl font-bold">Staff login</h1>
        <input name="password" type="password" required placeholder="Admin password" className="field" autoFocus />
        {msg && <p role="alert" className="text-sm text-red-600">{msg}</p>}
        <button className="btn w-full bg-snow-600 text-white hover:bg-snow-700">Log in</button>
      </form>
    );
  }

  const Select = ({ value, options, onChange }: { value: string; options: string[]; onChange: (v: string) => void }) => (
    <select value={value} onChange={(e) => onChange(e.target.value)} className="rounded-lg border border-snow-200 bg-white px-2 py-1 text-sm">
      {options.map((o) => (<option key={o} value={o}>{o.replace("_", " ")}</option>))}
    </select>
  );

  return (
    <div className="mx-auto max-w-6xl px-4 py-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-extrabold">As Snow · Admin</h1>
        <div className="flex gap-2">
          <button onClick={() => load()} className="rounded-lg border border-snow-200 px-3 py-1.5 text-sm hover:bg-snow-50">Refresh</button>
          <button onClick={() => { store(false); setToken(""); }} className="rounded-lg border border-snow-200 px-3 py-1.5 text-sm hover:bg-snow-50">Log out</button>
        </div>
      </div>
      <div className="mb-4 flex gap-1 overflow-x-auto">
        {TABS.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)} className={`whitespace-nowrap rounded-full px-4 py-2 text-sm font-medium ${tab === t.key ? "bg-snow-600 text-white" : "bg-snow-100 text-snow-700"}`}>{t.label}</button>
        ))}
      </div>
      {msg && <p role="status" className="mb-3 rounded-lg bg-snow-50 px-3 py-2 text-sm">{msg}</p>}
      {loading && <p className="text-sm text-ink/60">Loading…</p>}
      {!loading && rows.length === 0 && <p className="py-10 text-center text-ink/50">Nothing here yet.</p>}

      <div className="space-y-3 md:hidden" />
      <div className="overflow-x-auto">
        {rows.length > 0 && tab === "quotes" && (
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="text-ink/60"><tr><th className="p-2">#</th><th>Customer</th><th>Job</th><th>Estimate</th><th>Status</th><th /></tr></thead>
            <tbody>{rows.map((q) => (
              <tr key={q.id} className="border-t border-snow-100 align-top">
                <td className="p-2">{q.id}</td>
                <td><b>{q.name}</b><br /><a className="text-snow-600 underline" href={`https://wa.me/${q.phone}`} target="_blank" rel="noreferrer">+{q.phone}</a></td>
                <td>{SERVICE[q.service]} · {q.property_size} · {q.rooms} rooms<br /><span className="text-ink/60">{q.address} · {q.frequency}{q.preferred_date ? ` · ${q.preferred_date}` : ""}</span></td>
                <td>{naira(q.est_low)}–{naira(q.est_high)}</td>
                <td><Select value={q.status} options={QUOTE_STATUSES} onChange={(v) => act(() => call(`/api/admin/quotes/${q.id}`, { method: "PATCH", body: JSON.stringify({ status: v }) }), "Quote updated.")} /></td>
                <td>{q.preferred_date && q.status !== "booked" && <button className="rounded-lg bg-snow-600 px-3 py-1 text-white" onClick={() => act(() => call(`/api/admin/quotes/${q.id}/book`, { method: "POST" }), "Booking created.")}>Make booking</button>}</td>
              </tr>))}</tbody>
          </table>
        )}
        {rows.length > 0 && (tab === "bookings" || tab === "reminders") && (
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="text-ink/60"><tr><th className="p-2">#</th><th>Date</th><th>Customer</th><th>Service</th><th>Plan</th><th>Reminder</th><th>Status</th></tr></thead>
            <tbody>{rows.map((b) => (
              <tr key={b.id} className="border-t border-snow-100 align-top">
                <td className="p-2">{b.id}</td>
                <td className="whitespace-nowrap font-medium">{b.scheduled_date}</td>
                <td>{b.name || "—"}<br /><a className="text-snow-600 underline" href={`https://wa.me/${b.phone}`} target="_blank" rel="noreferrer">+{b.phone}</a></td>
                <td>{SERVICE[b.service]}<br /><span className="text-ink/60">{b.address}</span></td>
                <td>{b.frequency}{b.source === "recurring" ? " (auto)" : ""}</td>
                <td>{b.reminder_sent_at ? "Sent " + when(b.reminder_sent_at) : "Not yet"}</td>
                <td><Select value={b.status} options={BOOKING_STATUSES} onChange={(v) => act(() => call(`/api/admin/bookings/${b.id}`, { method: "PATCH", body: JSON.stringify({ status: v }) }), "Booking updated.")} /></td>
              </tr>))}</tbody>
          </table>
        )}
        {rows.length > 0 && tab === "messages" && (
          <ul className="space-y-2">{rows.map((m) => (
            <li key={m.id} className={`max-w-2xl whitespace-pre-wrap rounded-xl px-3 py-2 text-sm ${m.direction === "in" ? "bg-snow-100" : "ml-auto bg-green-50"}`}>
              <span className="block text-xs text-ink/50">{m.direction === "in" ? "From" : "To"} +{m.phone} · {when(m.created_at)} · {m.mode}</span>{m.body}
            </li>))}</ul>
        )}
      </div>
    </div>
  );
}
