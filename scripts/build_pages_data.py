from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import gspread
from google.oauth2.service_account import Credentials

from kakao_local import DEFAULT_ADDRESS, DEFAULT_RADIUS, KakaoLocalError, fetch_nearby_restaurants, sample_restaurants
from recommender import recommend_lunches
from weather import get_lunch_weather, sample_weather


OUTPUT_PATH = ROOT / "docs" / "data" / "site-data.json"
SEOUL_TZ = ZoneInfo("Asia/Seoul")
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]


def load_service_account() -> Credentials | None:
    raw = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw:
        return None

    # Handle the common cases where the secret is stored as:
    # 1) raw JSON
    # 2) a JSON string wrapped in quotes
    # 3) JSON with escaped newline characters in private_key
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


def read_config(spreadsheet) -> dict:
    defaults = {
        "title": "점심 추천",
        "base_address": DEFAULT_ADDRESS,
        "search_radius_meters": DEFAULT_RADIUS,
    }
    if spreadsheet is None:
        return defaults

    worksheet = get_or_create_worksheet(spreadsheet, "config", rows=20, cols=2)
    records = worksheet.get_all_records()
    values = {str(row.get("key", "")).strip(): row.get("value", "") for row in records}
    merged = {
        "title": values.get("title") or defaults["title"],
        "base_address": values.get("base_address") or defaults["base_address"],
        "search_radius_meters": int(values.get("search_radius_meters") or defaults["search_radius_meters"]),
    }

    if not records:
        worksheet.update(
            "A1:B4",
            [
                ["key", "value"],
                ["title", merged["title"]],
                ["base_address", merged["base_address"]],
                ["search_radius_meters", str(merged["search_radius_meters"])],
            ],
        )
    return merged


def read_visits(spreadsheet) -> list[dict]:
    if spreadsheet is None:
        return [
            {"restaurant_key": "sample-1", "restaurant_name": "을지로국밥", "visited_on": "2026-06-20", "meal_type": "점심", "visit_count": 2},
            {"restaurant_key": "sample-6", "restaurant_name": "을지로중화반점", "visited_on": "2026-06-18", "meal_type": "점심", "visit_count": 1},
        ]

    worksheet = get_or_create_worksheet(spreadsheet, "visits", rows=500, cols=6)
    records = worksheet.get_all_records()
    return [
        {
            "restaurant_key": str(row.get("restaurant_key", "")).strip(),
            "restaurant_name": str(row.get("restaurant_name", "")).strip(),
            "visited_on": str(row.get("visited_on", "")).strip(),
            "meal_type": str(row.get("meal_type", "점심")).strip() or "점심",
            "visit_count": int(row.get("visit_count") or 1),
        }
        for row in records
        if row.get("restaurant_name")
    ]


def summarize_visits(visits: list[dict]) -> list[dict]:
    by_name = defaultdict(
        lambda: {
            "restaurant_name": "",
            "latest_date": "",
            "meal_type": "점심",
            "visit_count": 0,
            "total_visit_count": 0,
        }
    )
    for visit in visits:
        key = visit["restaurant_name"]
        item = by_name[key]
        item["restaurant_name"] = key
        item["meal_type"] = visit.get("meal_type", "점심")
        item["total_visit_count"] += int(visit.get("visit_count") or 1)
        if visit.get("visited_on", "") >= item["latest_date"]:
            item["latest_date"] = visit.get("visited_on", "")
            item["visit_count"] = int(visit.get("visit_count") or 1)

    ordered = sorted(by_name.values(), key=lambda x: (x["latest_date"], x["restaurant_name"]), reverse=True)
    return [
        {
            "restaurant_name": item["restaurant_name"],
            "visited_on": item["latest_date"],
            "meal_type": item["meal_type"],
            "visit_count": item["visit_count"],
            "total_visit_count": item["total_visit_count"],
        }
        for item in ordered
    ]


def sync_restaurants(spreadsheet, restaurants: list[dict]) -> None:
    if spreadsheet is None:
        return

    worksheet = get_or_create_worksheet(spreadsheet, "restaurants", rows=max(200, len(restaurants) + 20), cols=20)
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
    ]
    rows = [headers]
    for restaurant in restaurants:
        rows.append([restaurant.get(header, "") for header in headers])
    worksheet.clear()
    worksheet.update(rows)


def build_data() -> dict:
    spreadsheet = open_spreadsheet()
    config = read_config(spreadsheet)
    visits = read_visits(spreadsheet)
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_ID", "").strip()
    sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}" if spreadsheet_id else ""

    try:
        location, restaurants = fetch_nearby_restaurants(config["base_address"], int(config["search_radius_meters"]))
        weather = get_lunch_weather(float(location["y"]), float(location["x"]))
    except (KakaoLocalError, ValueError):
        location = {"dong_name": "을지로동", "x": "", "y": ""}
        restaurants = sample_restaurants()
        weather = sample_weather()

    sync_restaurants(spreadsheet, restaurants)
    recommendations = recommend_lunches(restaurants=restaurants, visits=visits, weather=weather, limit=4)

    return {
        "title": config["title"],
        "base_address": config["base_address"],
        "search_radius_meters": int(config["search_radius_meters"]),
        "dong_name": location.get("dong_name", ""),
        "weather": weather,
        "restaurants": restaurants,
        "recommendations": recommendations,
        "visits": summarize_visits(visits),
        "sheet_url": sheet_url,
        "generated_at": datetime.now(SEOUL_TZ).isoformat(),
    }


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(build_data(), ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
