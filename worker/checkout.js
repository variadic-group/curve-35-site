// The parts of checkout that can be tested without a network: reading a basket, building the request to Stripe,
// and sending it with a time limit and a bounded retry.  worker/checkout.test.mjs runs them.
export const SITE = "https://curve35.com";
export const REDIRECT_HOSTS = new Set(["www.curve35.com", "curve35.org", "www.curve35.org"]);
export const MAX_LINES = 30, MAX_EACH = 99;

export function checkoutOn(env) { return !!env && env.ENABLE_CHECKOUT === "1" && typeof env.STRIPE_SECRET_KEY === "string" && env.STRIPE_SECRET_KEY.length > 20; }

// body: { items: [{ id, q }] }.  Returns { lines: [{ id, name, cents, q }] } or { error }.
// Only products the shop puts in a basket, with a whole-dollar-and-cents price above zero, in whole quantities.
export function readBasket(body, catalog) {
  const items = body && Array.isArray(body.items) ? body.items : null;
  if (!items || !items.length) return { error: "empty" };
  if (items.length > MAX_LINES) return { error: "too_many_lines" };
  const seen = new Set(), lines = [];
  for (const it of items) {
    const id = it && typeof it.id === "string" ? it.id : "", q = it ? it.q : 0, p = Object.prototype.hasOwnProperty.call(catalog, id) ? catalog[id] : null;
    if (!p || p.basket !== true || typeof p.price_usd !== "number" || !(p.price_usd > 0)) return { error: "unknown_item" };
    if (!Number.isInteger(q) || q < 1 || q > MAX_EACH) return { error: "bad_quantity" };
    if (seen.has(id)) return { error: "repeated_item" };
    seen.add(id); lines.push({ id, name: String(p.name), cents: Math.round(p.price_usd * 100), q });      // money is whole cents from here on
  }
  return { lines };
}

// The form Stripe's "create a Checkout Session" call takes.
export function sessionForm(lines, env, site) {
  const f = new URLSearchParams();
  f.set("mode", "payment");
  f.set("success_url", site + "/?paid=1#thanks");
  f.set("cancel_url", site + "/#store");
  lines.forEach((l, i) => {
    f.set(`line_items[${i}][quantity]`, String(l.q));
    f.set(`line_items[${i}][price_data][currency]`, "usd");
    f.set(`line_items[${i}][price_data][unit_amount]`, String(l.cents));
    f.set(`line_items[${i}][price_data][product_data][name]`, l.name);
    f.set(`line_items[${i}][price_data][product_data][metadata][sku]`, l.id);
  });
  f.set("shipping_address_collection[allowed_countries][0]", "US");                 // United States only, for now
  f.set("phone_number_collection[enabled]", "true");
  f.set("metadata[order]", lines.map((l) => l.q + " x " + l.id).join(", ").slice(0, 480));      // what to pack, readable in the Stripe dashboard
  const ship = Number(env.SHIPPING_CENTS);
  if (Number.isInteger(ship) && ship >= 0 && env.SHIPPING_CENTS !== undefined && env.SHIPPING_CENTS !== "") {
    f.set("shipping_options[0][shipping_rate_data][type]", "fixed_amount");
    f.set("shipping_options[0][shipping_rate_data][display_name]", env.SHIPPING_NAME || "Standard shipping");
    f.set("shipping_options[0][shipping_rate_data][fixed_amount][amount]", String(ship));
    f.set("shipping_options[0][shipping_rate_data][fixed_amount][currency]", "usd");
  }
  if (env.STRIPE_TAX === "1") f.set("automatic_tax[enabled]", "true");
  if (env.CHECKOUT_NOTE) f.set("custom_text[submit][message]", String(env.CHECKOUT_NOTE).slice(0, 1000));
  return f;
}

// One call to Stripe: 8 seconds at most, and up to two more tries when the network fails or Stripe answers 429 or 5xx.
// The same Idempotency-Key goes with every try, so a retry can never make a second session.
export async function stripePost(key, form, idem, fetchFn = fetch, sleep = (ms) => new Promise((r) => setTimeout(r, ms))) {
  let last = { ok: false, status: 0, code: "network" };
  for (let attempt = 0; attempt < 3; attempt++) {
    if (attempt) await sleep(250 * 2 ** (attempt - 1) + Math.floor(Math.random() * 200));
    const ctl = new AbortController(), timer = setTimeout(() => ctl.abort(), 8000);
    try {
      const r = await fetchFn("https://api.stripe.com/v1/checkout/sessions", { method: "POST", signal: ctl.signal, body: form.toString(),
        headers: { authorization: "Bearer " + key, "content-type": "application/x-www-form-urlencoded", "idempotency-key": idem } });
      let data = null; try { data = await r.json(); } catch (e) { data = null; }
      if (r.ok && data && typeof data.url === "string") return { ok: true, status: r.status, url: data.url };
      last = { ok: false, status: r.status, code: data && data.error ? data.error.code || data.error.type || "error" : "error" };
      if (r.status !== 429 && r.status < 500) return last;                           // our mistake, not Stripe's: do not try again
    } catch (e) { last = { ok: false, status: 0, code: e && e.name === "AbortError" ? "timeout" : "network" }; }
    finally { clearTimeout(timer); }
  }
  return last;
}
