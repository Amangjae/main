#!/usr/bin/env python3
"""Small local benchmark script."""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from db import get_recent_visits, get_restaurant_count, get_restaurants_with_history, init_db, list_restaurants
from recommender import recommend_lunches
from weather import get_lunch_weather


def measure(label: str, func):
    start = time.perf_counter()
    result = func()
    elapsed = (time.perf_counter() - start) * 1000
    print(f"{label:<30} {elapsed:8.2f} ms")
    return result


def main() -> int:
    print("=== Lunch Recommender Benchmark ===")
    measure("init_db", init_db)
    count = measure("get_restaurant_count", get_restaurant_count)
    restaurants = measure("list_restaurants", list_restaurants)
    with_history = measure("get_restaurants_with_history", get_restaurants_with_history)
    visits = measure("get_recent_visits", lambda: get_recent_visits(limit=10))
    weather = measure("get_lunch_weather", get_lunch_weather)
    recommendations = measure("recommend_lunches", recommend_lunches)

    print()
    print(f"restaurant count      : {count}")
    print(f"restaurants loaded    : {len(restaurants)}")
    print(f"history rows loaded   : {len(with_history)}")
    print(f"visits loaded         : {len(visits)}")
    print(f"weather category      : {weather['category']}")
    print(f"recommendations count : {len(recommendations)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
