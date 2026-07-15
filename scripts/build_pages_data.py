from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

from kakao_local import (
    DEFAULT_ADDRESS,
    DEFAULT_RADIUS,
    KakaoLocalError,
    fetch_nearby_restaurants,
    sample_restaurants,
)
from recommender import recommend_lunches
from weather import get_lunch_weather, sample_weather


OUTPUT_PATH = ROOT / "docs" / "data" / "site-data.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]
load_dotenv(ROOT / ".env")


def get_seoul_timezone():
    try:
        return ZoneInfo("Asia/Seoul")
    except Exception:
        return timezone(timedelta(hours=9))


SEOUL_TZ = get_seoul_timezone()
TODAY = datetime.now(SEOUL_TZ).date()


def load_service_account() -> Credentials | None:
    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw:
        return None

    info = json.loads(raw)
    if isinstance(info, str):
        info = json.loads(info)

    private_key = str(info.get("private_key", "")).strip()
    if private_key:
        private_key = private_key.replace("\\n", "\n").strip()
        if "BEGIN PRIVATE KEY" in private_key and "-----BEGIN PRIVATE KEY-----" not in private_key:
            private_key = private_key.replace("BEGIN PRIVATE KEY", "-----BEGIN PRIVATE KEY-----")
        if "END PRIVATE KEY" in private_key and "-----END PRIVATE KEY-----" not in private_key:
            private_key = private_key.replace("END PRIVATE KEY", "-----END PRIVATE KEY-----")
        info["private_key"] = private_key

    return Credentials.from_service_account_info(info, scopes=SCOPES)


def open_spreadsheet():
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_ID", "").strip()
    credentials = load_service_account()
    if not spreadsheet_id or credentials is None:
        return None
    client = gspread.authorize(credentials)
    return client.open_by_key(spreadsheet_id)


def get_or_create_worksheet(spreadsheet, title: str, rows: int = 200, cols: int = 20):
    try:
        return spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=title, rows=rows, cols=cols)


def ensure_headers(worksheet, headers: list[str]) -> None:
    current_headers = worksheet.row_values(1)
    if current_headers[: len(headers)] != headers:
        worksheet.clear()
        worksheet.update([headers])


def read_config(spreadsheet) -> dict[str, Any]:
    defaults = {
        "title": "점심 추천",
        "base_address": os.getenv("LUNCH_BASE_ADDRESS", DEFAULT_ADDRESS),
        "search_radius_meters": int(os.getenv("SEARCH_RADIUS_METERS", str(DEFAULT_RADIUS))),
        "party_size_default": 2,
        "selection_endpoint": "",
    }
    if spreadsheet is None:
        return defaults

    worksheet = get_or_create_worksheet(spreadsheet, "config", rows=20, cols=2)
    ensure_headers(worksheet, ["key", "value"])
    records = worksheet.get_all_records()
    values = {str(row.get("key", "")).strip(): row.get("value", "") for row in records}

    merged = {
        "title": values.get("title") or defaults["title"],
        "base_address": values.get("base_address") or defaults["base_address"],
        "search_radius_meters": int(values.get("search_radius_meters") or defaults["search_radius_meters"]),
        "party_size_default": int(values.get("party_size_default") or defaults["party_size_default"]),
        "selection_endpoint": values.get("selection_endpoint") or defaults["selection_endpoint"],
    }

    if not records:
        worksheet.update(
            [
                ["key", "value"],
                ["title", merged["title"]],
                ["base_address", merged["base_address"]],
                ["search_radius_meters", str(merged["search_radius_meters"])],
                ["party_size_default", str(merged["party_size_default"])],
                ["selection_endpoint", merged["selection_endpoint"]],
            ]
        )

    return merged


def read_restaurants(spreadsheet) -> list[dict[str, Any]]:
    if spreadsheet is None:
        return []

    worksheet = get_or_create_worksheet(spreadsheet, "restaurants", rows=500, cols=24)
    ensure_headers(
        worksheet,
        [
            "external_id",
            "kakao_place_id",
            "name",
            "category",
            "address",
            "road_address",
            "distance_m",
            "phone",
            "place_url",
            "x",
            "y",
            "source",
            "main_menu",
            "estimated_calories",
            "price_level",
            "party_size_min",
            "party_size_max",
            "indoor_score",
            "spicy_score",
            "soup_score",
            "noodle_score",
            "rice_score",
            "is_active",
            "updated_at",
        ],
    )
    records = worksheet.get_all_records()
    rows: list[dict[str, Any]] = []
    for row in records:
        if not row.get("name"):
            continue
        rows.append(
            {
                "external_id": str(row.get("external_id", "")).strip(),
                "kakao_place_id": str(row.get("kakao_place_id", "")).strip(),
                "name": str(row.get("name", "")).strip(),
                "category": str(row.get("category", "")).strip(),
                "address": str(row.get("address", "")).strip(),
                "road_address": str(row.get("road_address", "")).strip(),
                "distance_m": int(row.get("distance_m") or 0),
                "phone": str(row.get("phone", "")).strip(),
                "place_url": str(row.get("place_url", "")).strip(),
                "x": str(row.get("x", "")).strip(),
                "y": str(row.get("y", "")).strip(),
                "source": str(row.get("source", "")).strip(),
                "main_menu": str(row.get("main_menu", "")).strip(),
                "estimated_calories": int(row.get("estimated_calories") or 0),
                "price_level": str(row.get("price_level", "보통")).strip() or "보통",
                "party_size_min": int(row.get("party_size_min") or 1),
                "party_size_max": int(row.get("party_size_max") or 4),
                "indoor_score": int(row.get("indoor_score") or 4),
                "spicy_score": int(row.get("spicy_score") or 2),
                "soup_score": int(row.get("soup_score") or 2),
                "noodle_score": int(row.get("noodle_score") or 2),
                "rice_score": int(row.get("rice_score") or 2),
                "is_active": int(row.get("is_active") or 1),
            }
        )
    return rows


def read_visits(spreadsheet) -> list[dict[str, Any]]:
    if spreadsheet is None:
        return [
            {
                "date": "2026-07-05",
                "restaurant_id": "sample-1",
                "restaurant_name": "을지칼국수",
                "party_size": 2,
                "decision": "selected",
                "base_address": DEFAULT_ADDRESS,
                "dong_name": "을지로동",
                "weather_summary": "맑음",
                "selected_at": "2026-07-05T12:10:00+09:00",
            },
            {
                "date": "2026-07-08",
                "restaurant_id": "sample-6",
                "restaurant_name": "무교동국밥",
                "party_size": 3,
                "decision": "selected",
                "base_address": DEFAULT_ADDRESS,
                "dong_name": "을지로동",
                "weather_summary": "비",
                "selected_at": "2026-07-08T12:15:00+09:00",
            },
        ]

    try:
        worksheet = get_or_create_worksheet(spreadsheet, "visit_history", rows=500, cols=12)
    except Exception:
        worksheet = get_or_create_worksheet(spreadsheet, "visits", rows=500, cols=12)

    ensure_headers(
        worksheet,
        [
            "date",
            "restaurant_id",
            "restaurant_name",
            "party_size",
            "decision",
            "base_address",
            "dong_name",
            "weather_summary",
            "selected_at",
            "place_url",
            "main_menu",
            "estimated_calories",
        ],
    )
    records = worksheet.get_all_records()
    rows: list[dict[str, Any]] = []
    for row in records:
        decision = str(row.get("decision", "selected")).strip() or "selected"
        rows.append(
            {
                "date": str(row.get("date", "")).strip(),
                "restaurant_id": str(row.get("restaurant_id", "")).strip(),
                "restaurant_name": str(row.get("restaurant_name", "")).strip(),
                "party_size": int(row.get("party_size") or 0),
                "decision": decision,
                "base_address": str(row.get("base_address", "")).strip(),
                "dong_name": str(row.get("dong_name", "")).strip(),
                "weather_summary": str(row.get("weather_summary", "")).strip(),
                "selected_at": str(row.get("selected_at", "")).strip(),
                "place_url": str(row.get("place_url", "")).strip(),
                "main_menu": str(row.get("main_menu", "")).strip(),
                "estimated_calories": int(row.get("estimated_calories") or 0),
            }
        )
    return rows


def summarize_visits(visits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary = defaultdict(
        lambda: {
            "restaurant_name": "",
            "restaurant_id": "",
            "visited_on": "",
            "visit_count": 0,
            "party_size": 0,
        }
    )

    for visit in visits:
        if visit.get("decision") != "selected":
            continue
        key = str(visit.get("restaurant_id") or visit.get("restaurant_name") or "").strip()
        if not key:
            continue
        row = summary[key]
        row["restaurant_name"] = visit.get("restaurant_name", "")
        row["restaurant_id"] = visit.get("restaurant_id", "")
        row["visit_count"] += 1
        if str(visit.get("date", "")) >= row["visited_on"]:
            row["visited_on"] = visit.get("date", "")
            row["party_size"] = int(visit.get("party_size") or 0)

    ordered = sorted(
        summary.values(),
        key=lambda item: (item["visited_on"], item["restaurant_name"]),
        reverse=True,
    )
    return ordered[:5]


def sync_restaurants(spreadsheet, restaurants: list[dict[str, Any]]) -> None:
    if spreadsheet is None:
        return

    worksheet = get_or_create_worksheet(
        spreadsheet,
        "restaurants",
        rows=max(500, len(restaurants) + 20),
        cols=24,
    )
    headers = [
        "external_id",
        "kakao_place_id",
        "name",
        "category",
        "address",
        "road_address",
        "distance_m",
        "phone",
        "place_url",
        "x",
        "y",
        "source",
        "main_menu",
        "estimated_calories",
        "price_level",
        "party_size_min",
        "party_size_max",
        "indoor_score",
        "spicy_score",
        "soup_score",
        "noodle_score",
        "rice_score",
        "is_active",
        "updated_at",
    ]
    rows = [headers]
    updated_at = datetime.now(SEOUL_TZ).isoformat()
    for restaurant in restaurants:
        rows.append(
            [
                restaurant.get("external_id", ""),
                restaurant.get("kakao_place_id", ""),
                restaurant.get("name", ""),
                restaurant.get("category", ""),
                restaurant.get("address", ""),
                restaurant.get("road_address", ""),
                restaurant.get("distance_m", 0),
                restaurant.get("phone", ""),
                restaurant.get("place_url", ""),
                restaurant.get("x", ""),
                restaurant.get("y", ""),
                restaurant.get("source", ""),
                restaurant.get("main_menu", ""),
                restaurant.get("estimated_calories", 0),
                restaurant.get("price_level", "보통"),
                restaurant.get("party_size_min", 1),
                restaurant.get("party_size_max", 4),
                restaurant.get("indoor_score", 4),
                restaurant.get("spicy_score", 2),
                restaurant.get("soup_score", 2),
                restaurant.get("noodle_score", 2),
                restaurant.get("rice_score", 2),
                restaurant.get("is_active", 1),
                updated_at,
            ]
        )
    worksheet.clear()
    worksheet.update(rows)


def build_data() -> dict[str, Any]:
    spreadsheet = open_spreadsheet()
    config = read_config(spreadsheet)
    cached_restaurants = read_restaurants(spreadsheet)
    visits = read_visits(spreadsheet)
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_ID", "").strip()
    sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}" if spreadsheet_id else ""

    warning = ""
    try:
        location, restaurants = fetch_nearby_restaurants(
            config["base_address"],
            int(config["search_radius_meters"]),
        )
        weather = get_lunch_weather(float(location["y"]), float(location["x"]))
    except (KakaoLocalError, ValueError) as exc:
        warning = str(exc)
        restaurants = cached_restaurants or sample_restaurants()
        if cached_restaurants:
            location = {
                "dong_name": config["base_address"].split()[2] if len(config["base_address"].split()) >= 3 else "",
                "x": str(cached_restaurants[0].get("x", "")),
                "y": str(cached_restaurants[0].get("y", "")),
            }
        else:
            location = {"dong_name": "을지로동", "x": "", "y": ""}
        weather = sample_weather()

    sync_restaurants(spreadsheet, restaurants)
    recommendations = recommend_lunches(
        restaurants=restaurants,
        visits=visits,
        weather=weather,
        limit=4,
        party_size=int(config["party_size_default"]),
    )

    return {
        "title": config["title"],
        "base_address": config["base_address"],
        "search_radius_meters": int(config["search_radius_meters"]),
        "party_size_default": int(config["party_size_default"]),
        "selection_endpoint": config["selection_endpoint"],
        "dong_name": location.get("dong_name", ""),
        "weather": weather,
        "restaurants": restaurants,
        "recommendations": recommendations,
        "visits": summarize_visits(visits),
        "visit_history": visits,
        "sheet_url": sheet_url,
        "warning": warning,
        "generated_at": datetime.now(SEOUL_TZ).isoformat(),
        "updated_for_date": TODAY.isoformat(),
    }


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(build_data(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
