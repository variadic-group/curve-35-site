// node --test worker/checkout.test.mjs
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { checkoutOn, readBasket, sessionForm, stripePost, SITE } from "./checkout.js";
import worker from "./index.js";

const data = JSON.parse(readFileSync(new URL("../public/data/products.json", import.meta.url)));
const catalog = Object.fromEntries(data.products.map((p) => [p.id, p]));
const KEY = "rk_test_" + "x".repeat(30);
const noSleep = () => Promise.resolve();

test("CHK-1 checkout is off unless the switch is on and a key is set", () => {
  assert.equal(checkoutOn({}), false);
  assert.equal(checkoutOn({ ENABLE_CHECKOUT: "1" }), false);
  assert.equal(checkoutOn({ STRIPE_SECRET_KEY: KEY }), false);
  assert.equal(checkoutOn({ ENABLE_CHECKOUT: "true", STRIPE_SECRET_KEY: KEY }), false);
  assert.equal(checkoutOn({ ENABLE_CHECKOUT: "1", STRIPE_SECRET_KEY: KEY }), true);
});

test("CHK-2 prices come from the catalogue, in whole cents, never from the basket", () => {
  const r = readBasket({ items: [{ id: "starter-kit", q: 2, price_usd: 1 }, { id: "film-roll", q: 1 }] }, catalog);
  assert.deepEqual(r.lines.map((l) => [l.id, l.cents, l.q]), [["starter-kit", catalog["starter-kit"].price_usd * 100, 2], ["film-roll", catalog["film-roll"].price_usd * 100, 1]]);
});

test("CHK-3 a basket that is not one is refused", () => {
  assert.equal(readBasket({}, catalog).error, "empty");
  assert.equal(readBasket({ items: [] }, catalog).error, "empty");
  assert.equal(readBasket({ items: [{ id: "no-such-thing", q: 1 }] }, catalog).error, "unknown_item");
  assert.equal(readBasket({ items: [{ id: "__proto__", q: 1 }] }, catalog).error, "unknown_item");
  assert.equal(readBasket({ items: [{ id: "the-files", q: 1 }] }, catalog).error, "unknown_item");            // free, and not a basket item
  assert.equal(readBasket({ items: [{ id: "single-part", q: 1 }] }, catalog).error, "unknown_item");          // priced by email
  for (const q of [0, -1, 1.5, 100, "2", null]) assert.equal(readBasket({ items: [{ id: "starter-kit", q }] }, catalog).error, "bad_quantity");
  assert.equal(readBasket({ items: [{ id: "starter-kit", q: 1 }, { id: "starter-kit", q: 1 }] }, catalog).error, "repeated_item");
  assert.equal(readBasket({ items: Array.from({ length: 31 }, () => ({ id: "starter-kit", q: 1 })) }, catalog).error, "too_many_lines");
});

test("CHK-4 the request to Stripe: United States, a phone number, what to pack; postage, tax and a note only when set", () => {
  const lines = readBasket({ items: [{ id: "starter-kit", q: 1 }, { id: "film-roll", q: 3 }] }, catalog).lines;
  const f = sessionForm(lines, {}, SITE);
  assert.equal(f.get("mode"), "payment");
  assert.equal(f.get("line_items[0][price_data][unit_amount]"), "4900");
  assert.equal(f.get("line_items[1][quantity]"), "3");
  assert.equal(f.get("shipping_address_collection[allowed_countries][0]"), "US");
  assert.equal(f.get("metadata[order]"), "1 x starter-kit, 3 x film-roll");
  assert.equal(f.get("success_url"), "https://curve35.com/?paid=1#thanks");
  assert.equal(f.has("shipping_options[0][shipping_rate_data][type]"), false);
  assert.equal(f.has("automatic_tax[enabled]"), false);
  assert.equal(f.has("custom_text[submit][message]"), false);
  const g = sessionForm(lines, { SHIPPING_CENTS: "600", STRIPE_TAX: "1", CHECKOUT_NOTE: "Ships in two weeks." }, SITE);
  assert.equal(g.get("shipping_options[0][shipping_rate_data][fixed_amount][amount]"), "600");
  assert.equal(g.get("automatic_tax[enabled]"), "true");
  assert.equal(g.get("custom_text[submit][message]"), "Ships in two weeks.");
  assert.equal(sessionForm(lines, { SHIPPING_CENTS: "six" }, SITE).has("shipping_options[0][shipping_rate_data][type]"), false);
});

test("CHK-5 Stripe is tried again on 500 and 429 with the same idempotency key, and not on 400", async () => {
  const seen = []; let n = 0;
  const flaky = async (url, init) => { seen.push(init.headers["idempotency-key"]); n++; return n < 3 ? new Response("{}", { status: n === 1 ? 500 : 429 }) : new Response(JSON.stringify({ url: "https://checkout.stripe.com/c/pay/x" }), { status: 200 }); };
  const r = await stripePost(KEY, new URLSearchParams("a=1"), "idem-1", flaky, noSleep);
  assert.deepEqual([r.ok, r.url, n], [true, "https://checkout.stripe.com/c/pay/x", 3]);
  assert.deepEqual(seen, ["idem-1", "idem-1", "idem-1"]);
  let m = 0; const bad = async () => { m++; return new Response(JSON.stringify({ error: { code: "parameter_invalid_integer" } }), { status: 400 }); };
  const b = await stripePost(KEY, new URLSearchParams("a=1"), "idem-2", bad, noSleep);
  assert.deepEqual([b.ok, b.status, b.code, m], [false, 400, "parameter_invalid_integer", 1]);
  let k = 0; const down = async () => { k++; throw new TypeError("network"); };
  const d = await stripePost(KEY, new URLSearchParams("a=1"), "idem-3", down, noSleep);
  assert.deepEqual([d.ok, d.code, k], [false, "network", 3]);
});

// the Worker itself, with the site's files and Stripe stood in for
function env(extra = {}) { return { ASSETS: { fetch: async (req) => new URL(req.url).pathname === "/data/products.json" ? new Response(JSON.stringify(data), { status: 200 }) : new Response("page", { status: 200 }) }, ...extra }; }
const post = (body, headers = {}) => new Request("https://curve35.com/api/checkout", { method: "POST", body: typeof body === "string" ? body : JSON.stringify(body), headers: { "content-type": "application/json", origin: "https://curve35.com", ...headers } });

test("CHK-6 while it is off the Worker says so and never calls Stripe", async () => {
  const real = globalThis.fetch; let called = 0; globalThis.fetch = async () => { called++; return new Response("{}"); };
  try {
    const g = await worker.fetch(new Request("https://curve35.com/api/checkout"), env()); assert.deepEqual(await g.json(), { on: false });
    const r = await worker.fetch(post({ items: [{ id: "starter-kit", q: 1 }] }), env({ STRIPE_SECRET_KEY: KEY })); assert.equal(r.status, 503); assert.equal((await r.json()).error, "checkout_off");
    assert.equal(called, 0);
  } finally { globalThis.fetch = real; }
});

test("CHK-7 switched on: a basket becomes a Stripe page; another site's page, bad JSON and a bad basket do not", async () => {
  const real = globalThis.fetch; const sent = [];
  globalThis.fetch = async (url, init) => { sent.push([String(url), init.headers.authorization, init.body]); return new Response(JSON.stringify({ url: "https://checkout.stripe.com/c/pay/abc" }), { status: 200 }); };
  const on = env({ STRIPE_SECRET_KEY: KEY, ENABLE_CHECKOUT: "1", SHIPPING_CENTS: "600" });
  try {
    const g = await worker.fetch(new Request("https://curve35.com/api/checkout"), on); assert.deepEqual(await g.json(), { on: true });
    const r = await worker.fetch(post({ items: [{ id: "starter-kit", q: 1 }] }), on); assert.equal(r.status, 200); assert.deepEqual(await r.json(), { url: "https://checkout.stripe.com/c/pay/abc" });
    assert.equal(sent.length, 1); assert.equal(sent[0][0], "https://api.stripe.com/v1/checkout/sessions"); assert.equal(sent[0][1], "Bearer " + KEY);
    assert.match(sent[0][2], /unit_amount%5D=4900/); assert.match(sent[0][2], /fixed_amount%5D%5Bamount%5D=600/);
    assert.equal((await worker.fetch(post({ items: [{ id: "starter-kit", q: 1 }] }, { origin: "https://evil.example" }), on)).status, 403);
    assert.equal((await worker.fetch(post("{not json"), on)).status, 400);
    assert.equal((await worker.fetch(post({ items: [{ id: "starter-kit", q: 1000 }] }), on)).status, 400);
    assert.equal((await worker.fetch(post("x".repeat(5000)), on)).status, 413);
    assert.equal(sent.length, 1);                                                    // none of the refused ones reached Stripe
  } finally { globalThis.fetch = real; }
});

test("CHK-8 everything else is still the site, and the other hosts still redirect", async () => {
  const r = await worker.fetch(new Request("https://curve35.com/index.html"), env()); assert.equal(await r.text(), "page");
  const w = await worker.fetch(new Request("https://www.curve35.com/start?x=1"), env()); assert.equal(w.status, 301); assert.equal(w.headers.get("location"), "https://curve35.com/start?x=1");
});
