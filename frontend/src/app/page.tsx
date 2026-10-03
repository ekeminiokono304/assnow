import FloatingWhatsApp from "@/components/FloatingWhatsApp";
import { Icon, WhatsAppIcon } from "@/components/Icons";
import QuoteForm from "@/components/QuoteForm";
import { AREAS, BOOK_MESSAGE, GOOGLE_REVIEWS_URL, PHONE_DISPLAY, RATING, SERVICES, TESTIMONIALS, WA_NUMBER, waLink } from "@/lib/site";

const Stars = () => (
  <span className="inline-flex text-amber-400" aria-label="5 out of 5 stars">
    {[0, 1, 2, 3, 4].map((i) => (<Icon key={i} name="star" className="h-5 w-5" />))}
  </span>
);

export default function Home() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "HomeAndConstructionBusiness",
    name: "As Snow Cleaning & Pest Control",
    telephone: `+${WA_NUMBER}`,
    areaServed: "Lagos, Nigeria",
    address: { "@type": "PostalAddress", addressLocality: "Gbagada, Lagos", addressCountry: "NG" },
    aggregateRating: { "@type": "AggregateRating", ratingValue: RATING.score, reviewCount: RATING.count },
  };
  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />

      <header className="sticky top-0 z-40 border-b border-snow-100 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <a href="#top" className="flex items-center gap-2 font-extrabold text-snow-700">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-snow-600 text-white">❄</span>
            <span>As Snow</span>
          </a>
          <nav className="flex items-center gap-4 text-sm font-medium">
            <a href="#services" className="hidden sm:inline hover:text-snow-600">Services</a>
            <a href="#areas" className="hidden sm:inline hover:text-snow-600">Areas</a>
            <a href="#quote" className="rounded-full bg-snow-600 px-4 py-2 text-white hover:bg-snow-700">Get a quote</a>
          </nav>
        </div>
      </header>

      <main id="top">
        {/* HERO */}
        <section className="bg-gradient-to-b from-snow-100 to-white">
          <div className="mx-auto max-w-5xl px-4 pb-14 pt-12 sm:pt-20">
            <p className="inline-flex items-center gap-2 rounded-full bg-white px-3 py-1 text-sm shadow-sm">
              <Stars /> <b>{RATING.score}</b> <span className="text-ink/60">· {RATING.count} Google reviews</span>
            </p>
            <h1 className="mt-5 max-w-2xl text-4xl font-extrabold leading-tight sm:text-6xl">
              A cleaner, pest-free space in Lagos.
            </h1>
            <p className="mt-4 max-w-xl text-lg text-ink/75">
              Home and office cleaning, pest control and fumigation. Get an instant price, book on WhatsApp, and we remind you before every visit.
            </p>
            <div className="mt-7 flex flex-col gap-3 sm:flex-row">
              <a href="#quote" className="btn bg-snow-600 text-white hover:bg-snow-700">Get an instant quote</a>
              <a href={waLink(BOOK_MESSAGE)} target="_blank" rel="noopener noreferrer" className="btn bg-wa text-white hover:bg-wa-dark">
                <WhatsAppIcon /> Book on WhatsApp
              </a>
            </div>
            <p className="mt-4 text-sm text-ink/60">Prefer to call? <a className="underline" href={`tel:+${WA_NUMBER}`}>{PHONE_DISPLAY}</a></p>
          </div>
        </section>

        {/* SERVICES */}
        <section id="services" className="mx-auto max-w-5xl px-4 py-14">
          <h2 className="text-3xl font-extrabold">What we do</h2>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            {SERVICES.map((s) => (
              <article key={s.key} className="rounded-2xl border border-snow-200 p-5">
                <div className="mb-3 inline-flex rounded-xl bg-snow-100 p-2.5 text-snow-600"><Icon name={s.icon} /></div>
                <h3 className="text-xl font-bold">{s.title}</h3>
                <p className="mt-1 text-ink/70">{s.blurb}</p>
              </article>
            ))}
          </div>
        </section>

        {/* HOW IT WORKS + RECURRING */}
        <section className="bg-snow-50">
          <div className="mx-auto grid max-w-5xl gap-6 px-4 py-14 sm:grid-cols-3">
            {[
              { i: "form", t: "1. Get your price", d: "Fill the short form and see an instant estimate. No waiting for a callback." },
              { i: "chat", t: "2. Book on WhatsApp", d: "Pick a service, date and address in a quick chat. No app to install." },
              { i: "repeat", t: "3. Relax, we remind you", d: "On weekly, 2-weekly or monthly plans we remind you the day before and handle the next visit automatically." },
            ].map((x) => (
              <div key={x.t}>
                <div className="mb-2 inline-flex rounded-xl bg-white p-2.5 text-snow-600 shadow-sm"><Icon name={x.i} /></div>
                <h3 className="text-lg font-bold">{x.t}</h3>
                <p className="mt-1 text-ink/70">{x.d}</p>
              </div>
            ))}
          </div>
          <p className="mx-auto max-w-5xl px-4 pb-10 text-center text-sm font-medium text-wa-dark">
            Recurring plans save up to 15% per visit.
          </p>
        </section>

        {/* REVIEWS */}
        <section id="reviews" className="mx-auto max-w-5xl px-4 py-14">
          <div className="rounded-3xl border border-snow-200 p-6 text-center sm:p-10">
            <Stars />
            <p className="mt-2 text-5xl font-extrabold">{RATING.score}</p>
            <p className="text-ink/70">Rated 5 stars by {RATING.count} customers on Google</p>
            <a href={GOOGLE_REVIEWS_URL} target="_blank" rel="noopener noreferrer" className="btn mt-5 border border-snow-200 hover:bg-snow-50">
              Read our reviews on Google
            </a>
          </div>
          {TESTIMONIALS.length > 0 && (
            <div className="mt-6 grid gap-4 sm:grid-cols-3">
              {TESTIMONIALS.map((t) => (
                <blockquote key={t.name} className="rounded-2xl bg-snow-50 p-5">
                  <Stars />
                  <p className="mt-2">&ldquo;{t.quote}&rdquo;</p>
                  <footer className="mt-2 text-sm text-ink/60">{t.name}{t.area ? `, ${t.area}` : ""}</footer>
                </blockquote>
              ))}
            </div>
          )}
        </section>

        {/* AREAS */}
        <section id="areas" className="bg-snow-50">
          <div className="mx-auto max-w-5xl px-4 py-14">
            <h2 className="text-3xl font-extrabold">Areas we serve in Lagos</h2>
            <ul className="mt-5 flex flex-wrap gap-2">
              {AREAS.map((a) => (<li key={a} className="rounded-full border border-snow-200 bg-white px-4 py-1.5 text-sm">{a}</li>))}
            </ul>
            <p className="mt-4 text-ink/70">Not on the list? Message us on WhatsApp. We may still be able to reach you.</p>
          </div>
        </section>

        {/* QUOTE */}
        <section id="quote" className="mx-auto max-w-2xl px-4 py-14">
          <h2 className="text-center text-3xl font-extrabold">Get your instant quote</h2>
          <p className="mb-6 mt-2 text-center text-ink/70">Takes about 30 seconds.</p>
          <QuoteForm />
        </section>
      </main>

      <footer className="border-t border-snow-100 px-4 pb-24 pt-8 text-center text-sm text-ink/60">
        <p className="font-semibold text-ink">As Snow Cleaning &amp; Pest Control</p>
        <p>Gbagada, Lagos, Nigeria · <a href={`tel:+${WA_NUMBER}`} className="underline">{PHONE_DISPLAY}</a></p>
        <p className="mt-1"><a href="/admin" className="text-ink/30 hover:text-ink/60">Staff login</a></p>
      </footer>

      <FloatingWhatsApp />
    </>
  );
}
