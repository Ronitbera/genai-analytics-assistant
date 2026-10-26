"""Generate a reproducible synthetic retail transactions dataset."""
from pathlib import Path
import random
from datetime import date, timedelta
import csv

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "retail_sales.csv"
random.seed(42)
products = {
    "Electronics": [("Wireless Mouse", 18, 35), ("Headphones", 35, 110), ("Keyboard", 25, 80)],
    "Home": [("Desk Lamp", 15, 45), ("Storage Box", 8, 25), ("Water Bottle", 10, 30)],
    "Office": [("Notebook Set", 5, 18), ("Office Chair", 85, 220), ("Monitor Stand", 20, 65)],
    "Fitness": [("Yoga Mat", 15, 50), ("Resistance Bands", 8, 25), ("Dumbbell Set", 30, 100)],
}
regions = ["East", "West", "North", "South"]
channels = ["Online", "Store", "Marketplace"]
start = date(2025, 1, 1)
rows = []
for i in range(1, 801):
    dt = start + timedelta(days=random.randrange(365))
    category = random.choice(list(products))
    product, low, high = random.choice(products[category])
    price = round(random.uniform(low, high), 2)
    quantity = random.choices([1, 2, 3, 4, 5], weights=[45, 28, 15, 8, 4])[0]
    discount_pct = random.choices([0, 5, 10, 15, 20], weights=[45, 15, 22, 12, 6])[0]
    revenue = round(price * quantity * (1 - discount_pct / 100), 2)
    cost = round(price * quantity * random.uniform(0.48, 0.78), 2)
    rows.append({
        "order_id": f"ORD{i:05d}", "order_date": dt.isoformat(),
        "region": random.choice(regions), "sales_channel": random.choice(channels),
        "category": category, "product": product, "quantity": quantity,
        "unit_price": price, "discount_pct": discount_pct,
        "revenue": revenue, "cost": cost, "profit": round(revenue-cost, 2),
    })
OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader(); writer.writerows(rows)
print(f"Wrote {len(rows)} rows to {OUT}")
