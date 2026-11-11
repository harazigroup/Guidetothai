// guidetothai — "gtt-checkout" Edge Function (Supabase). Turn OFF "Verify JWT" for this function.
// POST { action: "start", lang, pkg: "vip"|"standard", name, email, phone, date, flight, time, airport, pax, hotel, bags?, notes? }
//   → creates a Stripe Embedded Checkout session (THB, price set HERE on the server) → { clientSecret, ref }
// POST { action: "status", session_id } → { status, ref, name, date, flight, airport, pax, total }
// Secrets: GTT_STRIPE_SECRET_KEY (sk_live_… of the Stripe account that should receive the money)
//          GTT_SITE_URL (optional, default https://guidetothai.co)

const SK = Deno.env.get("GTT_STRIPE_SECRET_KEY") || "";
const SITE = (Deno.env.get("GTT_SITE_URL") || "https://guidetothai.co").replace(/\/$/, "");

// ---- the product (change prices here only) ----
const PACKAGES: Record<string, { thb: number; name: string; desc: string }> = {
  vip: { thb: 6000, name: P.name,
    desc: "Meet at the aircraft with name sign, fast track immigration, luggage help, escort to the car, private car to hotel" },
  standard: { thb: 1500, name: "Airport Arrival – Bangkok (per person)",
    desc: "Meet at the arrival hall exit with name sign, private car to hotel" },
};
const MAX_PAX = 10;
const AIRPORTS: Record<string, string> = {
  BKK: "Suvarnabhumi Airport (BKK)",
  DMK: "Don Mueang Airport (DMK)",
};

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (b: unknown, status = 200) =>
  new Response(JSON.stringify(b), { status, headers: { ...cors, "Content-Type": "application/json" } });

async function stripe(path: string, params?: Record<string, string>) {
  const r = await fetch("https://api.stripe.com/v1/" + path, {
    method: params ? "POST" : "GET",
    headers: { Authorization: `Bearer ${SK}`, "Content-Type": "application/x-www-form-urlencoded" },
    body: params ? new URLSearchParams(params) : undefined,
  });
  const b = await r.json();
  if (!r.ok) throw new Error(b?.error?.message || "Stripe error");
  return b;
}

const clean = (v: unknown, n = 200) => String(v ?? "").replace(/[\u0000-\u001f]/g, " ").trim().slice(0, n);

function newRef(pkg: string) {
  const d = new Date();
  const ymd = d.toISOString().slice(2, 10).replace(/-/g, "");
  const rnd = Math.random().toString(36).slice(2, 6).toUpperCase();
  return `GTT-${pkg === "vip" ? "VIP" : "STD"}-${ymd}-${rnd}`;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return json({ error: "method" }, 405);
  if (!SK) return json({ error: "payments not configured" }, 503);
  try {
    const b = await req.json();

    if (b.action === "status") {
      const id = clean(b.session_id, 120);
      if (!/^cs_[A-Za-z0-9_]+$/.test(id)) return json({ error: "bad session" }, 400);
      const cs = await stripe("checkout/sessions/" + encodeURIComponent(id));
      const m = cs.metadata || {};
      return json({
        status: cs.payment_status, ref: m.ref, pkg: m.package, name: m.name, date: m.date, flight: m.flight,
        time: m.time, airport: m.airport, pax: m.pax, total: (cs.amount_total || 0) / 100, currency: cs.currency,
      });
    }

    // ---- start: validate everything on the server ----
    const lang = ["ar", "th"].includes(b.lang) ? b.lang : "en";
    const pfx = lang === "en" ? "" : "/" + lang;
    const f = {
      name: clean(b.name, 80), email: clean(b.email, 120), phone: clean(b.phone, 40),
      date: clean(b.date, 10), flight: clean(b.flight, 20).toUpperCase(), time: clean(b.time, 5),
      pkg: clean(b.pkg, 10).toLowerCase(), airport: clean(b.airport, 3).toUpperCase(), hotel: clean(b.hotel, 300), bags: clean(b.bags, 3),
      notes: clean(b.notes, 400),
    };
    const pax = Math.floor(Number(b.pax));
    const errs: string[] = [];
    if (f.name.length < 2) errs.push("name");
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email)) errs.push("email");
    if (f.phone.replace(/\D/g, "").length < 7) errs.push("phone");
    if (!/^\d{4}-\d{2}-\d{2}$/.test(f.date) || isNaN(Date.parse(f.date))) errs.push("date");
    if (!/^[A-Z0-9]{2,3}\s?\d{1,4}[A-Z]?$/.test(f.flight)) errs.push("flight");
    if (!/^\d{2}:\d{2}$/.test(f.time)) errs.push("time");
    else if (!errs.includes("date") && Date.parse(`${f.date}T${f.time}:00+07:00`) < Date.now() + 24 * 3600 * 1000) errs.push("date");
    if (!PACKAGES[f.pkg]) errs.push("pkg");
    if (!AIRPORTS[f.airport]) errs.push("airport");
    if (!(pax >= 1 && pax <= MAX_PAX)) errs.push("pax");
    if (f.hotel.length < 3) errs.push("hotel");
    if (errs.length) return json({ error: "invalid", fields: errs }, 400);

    const P = PACKAGES[f.pkg];
    const ref = newRef(f.pkg);
    const cs = await stripe("checkout/sessions", {
      mode: "payment",
      ui_mode: "embedded",
      locale: lang === "ar" ? "auto" : lang,
      "line_items[0][quantity]": String(pax),
      "line_items[0][price_data][currency]": "thb",
      "line_items[0][price_data][unit_amount]": String(P.thb * 100),
      "line_items[0][price_data][product_data][name]": P.name,
      "line_items[0][price_data][product_data][description]":
        `${AIRPORTS[f.airport]} · ${f.date} ${f.time} · flight ${f.flight} · ${P.desc}`,
      customer_email: f.email,
      client_reference_id: ref,
      "metadata[ref]": ref,
      "metadata[package]": f.pkg,
      "metadata[name]": f.name,
      "metadata[phone]": f.phone,
      "metadata[date]": f.date,
      "metadata[time]": f.time,
      "metadata[flight]": f.flight,
      "metadata[airport]": f.airport,
      "metadata[pax]": String(pax),
      "metadata[hotel]": f.hotel,
      "metadata[bags]": f.bags,
      "metadata[notes]": f.notes,
      "metadata[lang]": lang,
      "payment_intent_data[description]": `guidetothai ${f.pkg} arrival ${ref} – ${f.name} – ${f.flight} ${f.date}`,
      "payment_intent_data[metadata][ref]": ref,
      return_url: `${SITE}${pfx}/vip-booking/?session_id={CHECKOUT_SESSION_ID}`,
    });
    return json({ clientSecret: cs.client_secret, ref });
  } catch (e) {
    return json({ error: String((e as Error).message || e) }, 500);
  }
});
