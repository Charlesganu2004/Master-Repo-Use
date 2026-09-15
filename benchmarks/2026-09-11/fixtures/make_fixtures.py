"""Generate the browser benchmark pages and their answer key.

Deterministic: the same seed writes the same two pages and the same answers,
so a run on another machine checks against the same key. The pages carry the
noise a real dashboard has (navigation, filters, promotions, footer links)
because a compressed snapshot only earns its keep against a page with noise.

    python benchmarks/2026-09-11/fixtures/make_fixtures.py

writes orders.html, checkout.html and answers.json beside this file.
"""
from __future__ import annotations

import html
import json
import pathlib
import random

HERE = pathlib.Path(__file__).resolve().parent
SEED = 20260911
ROWS = 240

FIRST = ["Ada", "Grace", "Linus", "Barbara", "Ken", "Margaret", "Dennis", "Radia",
         "Alan", "Frances", "Edsger", "Katherine", "Tim", "Hedy", "John", "Shafi"]
LAST = ["Lovelace", "Hopper", "Torvalds", "Liskov", "Thompson", "Hamilton", "Ritchie",
        "Perlman", "Turing", "Allen", "Dijkstra", "Johnson", "Berners-Lee", "Lamarr",
        "Backus", "Goldwasser"]
PRODUCTS = ["Standing desk", "Mechanical keyboard", "4K monitor", "USB-C dock",
            "Noise-cancelling headset", "Ergonomic chair", "Webcam", "Laptop stand",
            "Portable SSD", "Desk lamp"]
STATUSES = ["Pending", "Shipped", "Delivered", "Cancelled", "Refunded"]


def fnv1a(text: str) -> str:
    """The same 32-bit FNV-1a the checkout page computes in JavaScript."""
    value = 0x811C9DC5
    for byte in text.encode("utf-8"):
        value ^= byte
        value = (value * 0x01000193) & 0xFFFFFFFF
    return f"{value:08X}"


def orders() -> list[dict]:
    rng = random.Random(SEED)
    rows = []
    for index in range(ROWS):
        rows.append({
            "id": f"ORD-{10001 + index}",
            "customer": f"{rng.choice(FIRST)} {rng.choice(LAST)}",
            "product": rng.choice(PRODUCTS),
            "status": rng.choice(STATUSES),
            "total": round(rng.uniform(19, 1400), 2),
            "date": f"2026-{rng.randint(1, 8):02d}-{rng.randint(1, 28):02d}",
        })
    return rows


NAV = "".join(f'<li><a href="#{name.lower()}">{name}</a></li>' for name in
              ["Dashboard", "Orders", "Customers", "Products", "Inventory", "Returns",
               "Reports", "Marketing", "Settings", "Help"])
FOOTER = "".join(f'<li><a href="#f{i}">{name}</a></li>' for i, name in enumerate(
    ["About", "Careers", "Press", "Status", "Privacy", "Terms", "Cookies", "Accessibility",
     "Contact", "Partners", "Affiliates", "Developers", "API", "Changelog"]))


def orders_page(rows: list[dict]) -> str:
    body = "".join(
        f"<tr><td>{r['id']}</td><td>{html.escape(r['customer'])}</td><td>{r['product']}</td>"
        f"<td>{r['status']}</td><td>${r['total']:,.2f}</td><td>{r['date']}</td></tr>"
        for r in rows)
    filters = "".join(f'<label><input type="checkbox" name="status" value="{s}"> {s}</label>'
                      for s in STATUSES)
    promos = "".join(f'<article><h3>{p}</h3><p>Popular this week in your region.</p>'
                     f'<button type="button">View {p}</button></article>' for p in PRODUCTS[:6])
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Northwind Orders</title>
<style>body{{font:14px system-ui;margin:0}}nav ul,footer ul{{display:flex;gap:12px;list-style:none}}
table{{border-collapse:collapse}}td,th{{border:1px solid #ccc;padding:4px 8px}}</style></head>
<body>
<header><h1>Northwind Orders</h1><nav aria-label="Main"><ul>{NAV}</ul></nav>
<form role="search"><label>Search orders <input type="search" name="q"></label>
<button type="submit">Search</button></form></header>
<aside aria-label="Filters"><h2>Filters</h2>{filters}
<label>Sort by <select name="sort"><option>Newest</option><option>Oldest</option>
<option>Total, high to low</option><option>Total, low to high</option></select></label></aside>
<main><h2>All orders</h2><p>{ROWS} orders. Totals include tax.</p>
<table aria-label="Orders"><thead><tr><th>Order</th><th>Customer</th><th>Product</th>
<th>Status</th><th>Total</th><th>Date</th></tr></thead><tbody>{body}</tbody></table></main>
<section aria-label="Recommended"><h2>Recommended for your store</h2>{promos}</section>
<footer><ul>{FOOTER}</ul><p>Northwind Traders. Figures are fictional.</p></footer>
</body></html>
"""


CHECKOUT = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Northwind Checkout</title>
<style>body{font:14px system-ui;margin:0}form{display:grid;gap:8px;max-width:420px}
nav ul,footer ul{display:flex;gap:12px;list-style:none}.error{color:#b00}</style></head>
<body>
<header><h1>Northwind Checkout</h1><nav aria-label="Main"><ul>__NAV__</ul></nav></header>
<aside aria-label="Promotion"><p>Free returns for 60 days. Members save more.</p>
<button type="button">Join now</button><button type="button">Learn more</button></aside>
<main><h2>Your cart</h2>
<ul aria-label="Cart"><li>Standing desk, $649.00</li><li>Desk lamp, $49.00</li></ul>
<form id="checkout" novalidate>
<label>Full name <input name="name" autocomplete="name" required></label>
<label>Email <input name="email" type="email" autocomplete="email" required></label>
<label>Street address <input name="street" autocomplete="street-address" required></label>
<label>City <input name="city" autocomplete="address-level2" required></label>
<label>Postcode <input name="postcode" autocomplete="postal-code" required></label>
<label>Shipping method <select name="shipping">
<option>Standard</option><option>Express</option><option>Overnight</option></select></label>
<label>Coupon code <input name="coupon"></label>
<label><input type="checkbox" name="terms"> I accept the terms</label>
<button type="submit">Place order</button>
<p class="error" role="alert" id="error"></p>
</form>
<output id="confirmation" role="status"></output>
</main>
<footer><ul>__FOOTER__</ul></footer>
<script>
function fnv1a(s){let h=0x811c9dc5;for(const b of new TextEncoder().encode(s)){h^=b;h=Math.imul(h,0x01000193)>>>0;}
return h.toString(16).toUpperCase().padStart(8,'0');}
document.getElementById('checkout').addEventListener('submit',function(e){
  e.preventDefault();const f=e.target;const need=['name','email','street','city','postcode'];
  const missing=need.filter(n=>!f[n].value.trim());
  if(missing.length){document.getElementById('error').textContent='Missing: '+missing.join(', ');return;}
  if(!f.terms.checked){document.getElementById('error').textContent='Accept the terms to continue';return;}
  document.getElementById('error').textContent='';
  const code='CONF-'+fnv1a([f.name.value.trim(),f.email.value.trim(),f.shipping.value,f.coupon.value.trim()].join('|'));
  document.getElementById('confirmation').textContent='Order placed. Confirmation code: '+code;
});
</script>
</body></html>
"""

CHECKOUT_INPUT = {"name": "Ada Lovelace", "email": "ada@example.com",
                  "street": "12 Analytical Way", "city": "London", "postcode": "N1 9GU",
                  "shipping": "Express", "coupon": "SAVE10"}


def main() -> None:
    rows = orders()
    (HERE / "orders.html").write_text(orders_page(rows), encoding="utf-8")
    (HERE / "checkout.html").write_text(
        CHECKOUT.replace("__NAV__", NAV).replace("__FOOTER__", FOOTER), encoding="utf-8")
    target = rows[172]
    shipped_over_500 = sum(1 for r in rows if r["status"] == "Shipped" and r["total"] > 500)
    code = "CONF-" + fnv1a("|".join([CHECKOUT_INPUT["name"], CHECKOUT_INPUT["email"],
                                     CHECKOUT_INPUT["shipping"], CHECKOUT_INPUT["coupon"]]))
    answers = {
        "lookup": {"order": target["id"], "total": f"${target['total']:,.2f}"},
        "count": {"status": "Shipped", "over": 500, "count": shipped_over_500},
        "checkout": {"input": CHECKOUT_INPUT, "code": code},
    }
    (HERE / "answers.json").write_text(json.dumps(answers, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(answers, indent=2))


if __name__ == "__main__":
    main()
