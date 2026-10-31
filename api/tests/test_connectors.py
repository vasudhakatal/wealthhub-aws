"""Aggregation resilience: independent sources, bounded retries, partial results."""

import asyncio
import time

import pytest
from app.connectors import DATA, aggregate, fetch_source


def test_all_sources_connected_by_default():
    result = asyncio.run(aggregate())
    assert result["sources"] == {"bank": "connected", "shares": "connected", "super": "connected"}
    assert result["total"] == 244000
    assert result["mock"] is True


def test_every_holding_is_tagged_with_its_source():
    result = asyncio.run(aggregate())
    assert len(result["holdings"]) == sum(len(items) for items in DATA.values())
    assert {h["source"] for h in result["holdings"]} == set(DATA)


@pytest.mark.parametrize(
    ("failing_source", "expected_total"),
    [("bank", 200550), ("shares", 127100), ("super", 160350)],
)
def test_one_failing_source_returns_the_others(failing_source, expected_total):
    async def fetch(name):
        if name == failing_source:
            raise ConnectionError("source down")
        return await fetch_source(name)

    result = asyncio.run(aggregate(fetch))
    assert result["sources"][failing_source] == "unavailable"
    assert [s for s, st in result["sources"].items() if st == "connected"] != []
    assert result["total"] == expected_total


def test_transient_failure_is_recovered_by_one_retry():
    seen = set()

    async def flaky(name):
        if name not in seen:
            seen.add(name)
            raise TimeoutError("first call fails")
        return await fetch_source(name)

    result = asyncio.run(aggregate(flaky))
    assert set(result["sources"].values()) == {"connected"}
    assert result["total"] == 244000


def test_sources_are_fetched_concurrently():
    async def slow(name):
        await asyncio.sleep(0.2)
        return await fetch_source(name)

    started = time.perf_counter()
    result = asyncio.run(aggregate(slow, timeout=1))
    elapsed = time.perf_counter() - started
    assert result["total"] == 244000
    # Three sequential 0.2s calls would take 0.6s; concurrent calls take about 0.2s.
    assert elapsed < 0.5


def test_unexpected_errors_are_not_swallowed():
    async def broken(name):
        raise ValueError("programming error, not a network failure")

    with pytest.raises(ValueError):
        asyncio.run(aggregate(broken))
