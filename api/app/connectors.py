"""Synthetic sources with bounded retries and independent failure handling."""

import asyncio
from datetime import date

DATA = {
    "bank": [
        {"name": "Everyday cash", "category": "Cash", "value": 18450.0},
        {"name": "Term deposit", "category": "Cash", "value": 25000.0},
    ],
    "shares": [
        {"name": "Australian equities", "category": "Shares", "value": 64200.0},
        {"name": "Global index fund", "category": "Shares", "value": 52700.0},
    ],
    "super": [{"name": "Superannuation", "category": "Super", "value": 83650.0}],
}


async def fetch_source(name):
    await asyncio.sleep(0.02)
    return [dict(item, source=name) for item in DATA[name]]


async def aggregate(fetch=fetch_source, timeout=0.6):
    async def one(name):
        for attempt in range(2):
            try:
                return name, await asyncio.wait_for(fetch(name), timeout), "connected"
            except (TimeoutError, ConnectionError, OSError):
                if attempt == 0:
                    await asyncio.sleep(0.03)
        return name, [], "unavailable"

    results = await asyncio.gather(*(one(name) for name in DATA))
    holdings = [item for _, items, _ in results for item in items]
    return {
        "holdings": holdings,
        "total": round(sum(item["value"] for item in holdings), 2),
        "sources": {name: status for name, _, status in results},
        "as_of": date.today().isoformat(),
        "mock": True,
    }
