// The Worker in front of the static site in ./public.
//   1. Sends www.curve35.com and curve35.org (and its www) to https://curve35.com.
//   2. /api/checkout: turns a basket into a Stripe Checkout page.  OFF unless ENABLE_CHECKOUT is "1" and a key is set;
//      while it is off the site keeps its "Order by email" button.
//
// Checkout settings (Cloudflare: Workers > curve-35-site > Settings > Variables and Secrets):
//   STRIPE_SECRET_KEY  secret   a restricted Stripe key that may write Checkout Sessions, nothing else
//   ENABLE_CHECKOUT    "1"      the switch.  Anything else, or missing: off
//   SHIPPING_CENTS     "600"    flat postage for an order, in cents.  Missing: no postage line
//   SHIPPING_NAME      text     what the postage line is called (default "Standard shipping")
//   STRIPE_TAX         "1"      let Stripe Tax work out sales tax (it must be set up in Stripe first)
//   CHECKOUT_NOTE      text     a line shown beside the pay button, such as when the order will ship
//
// Prices never come from the browser.  The basket sends ids and quantities; names and prices are read here from the
// site's own /data/products.json, which is written from the canon.
import { REDIRECT_HOSTS, SITE, checkoutOn, readBasket, sessionForm, stripePost } from "./checkout.js";

const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });

let catalog = null;                                              // id -> product, read once per isolate
async function loadCatalog(request, env) {
  if (catalog) return catalog;
  const r = await env.ASSETS.fetch(new Request(new URL("/data/products.json", request.url)));
  if (!r.ok) throw new Error("products.json: " + r.status);
  const data = await r.json(); const c = {};
  for (const p of data.products || []) c[p.id] = p;
  catalog = c; return c;
}

async function checkout(request, env) {
  if (request.method === "GET") return json({ on: checkoutOn(env) });
  if (request.method !== "POST") return json({ error: "method" }, 405);
  if (!checkoutOn(env)) return json({ error: "checkout_off" }, 503);
  const origin = request.headers.get("origin");
  if (origin && origin !== new URL(request.url).origin) return json({ error: "origin" }, 403);      // the site's own pages only
  const text = await request.text();
  if (text.length > 4000) return json({ error: "too_long" }, 413);
  let body; try { body = JSON.parse(text); } catch (e) { return json({ error: "not_json" }, 400); }
  let cat; try { cat = await loadCatalog(request, env); } catch (e) { console.error("checkout: catalogue not read: " + e.message); return json({ error: "catalogue" }, 500); }
  const basket = readBasket(body, cat);
  if (basket.error) return json({ error: basket.error }, 400);
  const res = await stripePost(env.STRIPE_SECRET_KEY, sessionForm(basket.lines, env, SITE), crypto.randomUUID());
  if (!res.ok) { console.error("checkout: Stripe said " + res.status + " " + res.code); return json({ error: "stripe", code: res.code || null }, 502); }
  return json({ url: res.url });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (REDIRECT_HOSTS.has(url.hostname)) return Response.redirect(SITE + url.pathname + url.search, 301);
    if (url.pathname === "/api/checkout") return checkout(request, env);
    return env.ASSETS.fetch(request);
  },
};
