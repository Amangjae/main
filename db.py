import os
import sqlite3
from datetime import date
from pathlib import Path
from typing import Iterable


DB_PATH = Path(os.getenv("DB_PATH", "data/lunch_recommender.db"))


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA cache_size = -16000")
    return conn


def _ensure_column(conn: sqlite3.Connection, column_name: str, column_sql: str) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(restaurants)").fetchall()}
    if column_name not in columns:
        conn.execute(f"ALTER TABLE restaurants ADD COLUMN {column_sql}")


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS restaurants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_id TEXT UNIQUE,
                kakao_place_id TEXT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                address TEXT,
                road_address TEXT,
                distance_m INTEGER NOT NULL,
                phone TEXT,
                place_url TEXT,
                x TEXT,
                y TEXT,
                source TEXT NOT NULL DEFAULT 'sample',
                indoor_score INTEGER NOT NULL DEFAULT 3,
                spicy_score INTEGER NOT NULL DEFAULT 2,
                soup_score INTEGER NOT NULL DEFAULT 2,
                noodle_score INTEGER NOT NULL DEFAULT 2,
                rice_score INTEGER NOT NULL DEFAULT 2,
                price_level TEXT NOT NULL DEFAULT '보통',
                is_active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS visit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant_id INTEGER NOT NULL,
                visited_on TEXT NOT NULL,
                meal_type TEXT NOT NULL DEFAULT '점심',
                notes TEXT,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_restaurants_active_distance
            ON restaurants (is_active, distance_m, name);

            CREATE INDEX IF NOT EXISTS idx_restaurants_kakao_place_id
            ON restaurants (kakao_place_id);

            CREATE INDEX IF NOT EXISTS idx_restaurants_name_address
            ON restaurants (name, road_address, address);

            CREATE INDEX IF NOT EXISTS idx_visit_history_restaurant_date
            ON visit_history (restaurant_id, visited_on DESC);

            CREATE INDEX IF NOT EXISTS idx_visit_history_visited_on
            ON visit_history (visited_on DESC);
            """
        )
        _ensure_column(conn, "kakao_place_id", "kakao_place_id TEXT")
        _ensure_column(conn, "road_address", "road_address TEXT")
        _ensure_column(conn, "place_url", "place_url TEXT")
        _ensure_column(conn, "x", "x TEXT")
        _ensure_column(conn, "y", "y TEXT")
        _ensure_column(conn, "source", "source TEXT NOT NULL DEFAULT 'sample'")


def clear_all() -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM visit_history")
        conn.execute("DELETE FROM restaurants")


def _normalize_restaurant(restaurant: dict, default_source: str = "sample") -> dict:
    return {
        "external_id": restaurant.get("external_id"),
        "kakao_place_id": restaurant.get("kakao_place_id"),
        "name": restaurant["name"],
        "category": restaurant["category"],
        "address": restaurant.get("address", ""),
        "road_address": restaurant.get("road_address", ""),
        "distance_m": int(restaurant.get("distance_m", 0)),
        "phone": restaurant.get("phone", ""),
        "place_url": restaurant.get("place_url", ""),
        "x": restaurant.get("x", ""),
        "y": restaurant.get("y", ""),
        "source": restaurant.get("source", default_source),
        "indoor_score": int(restaurant.get("indoor_score", 4)),
        "spicy_score": int(restaurant.get("spicy_score", 2)),
        "soup_score": int(restaurant.get("soup_score", 2)),
        "noodle_score": int(restaurant.get("noodle_score", 2)),
        "rice_score": int(restaurant.get("rice_score", 2)),
        "price_level": restaurant.get("price_level", "보통"),
        "is_active": int(restaurant.get("is_active", 1)),
    }


def upsert_restaurants(restaurants: Iterable[dict]) -> None:
    payload = [_normalize_restaurant(restaurant) for restaurant in restaurants]
    if not payload:
        return

    with get_connection() as conn:
        conn.executemany(
            """
            INSERT INTO restaurants (
                external_id, kakao_place_id, name, category, address, road_address,
                distance_m, phone, place_url, x, y, source,
                indoor_score, spicy_score, soup_score, noodle_score,
                rice_score, price_level, is_active
            )
            VALUES (
                :external_id, :kakao_place_id, :name, :category, :address, :road_address,
                :distance_m, :phone, :place_url, :x, :y, :source,
                :indoor_score, :spicy_score, :soup_score, :noodle_score,
                :rice_score, :price_level, :is_active
            )
            ON CONFLICT(external_id) DO UPDATE SET
                kakao_place_id=excluded.kakao_place_id,
                name=excluded.name,
                category=excluded.category,
                address=excluded.address,
                road_address=excluded.road_address,
                distance_m=excluded.distance_m,
                phone=excluded.phone,
                place_url=excluded.place_url,
                x=excluded.x,
                y=excluded.y,
                source=excluded.source,
                indoor_score=excluded.indoor_score,
                spicy_score=excluded.spicy_score,
                soup_score=excluded.soup_score,
                noodle_score=excluded.noodle_score,
                rice_score=excluded.rice_score,
                price_level=excluded.price_level,
                is_active=excluded.is_active
            """,
            payload,
        )


def save_kakao_restaurants(restaurants: Iterable[dict]) -> dict[str, int]:
    payload = [_normalize_restaurant(restaurant, default_source="kakao") for restaurant in restaurants]
    if not payload:
        return {"inserted": 0, "skipped": 0}

    with get_connection() as conn:
        existing_rows = conn.execute(
            """
            SELECT kakao_place_id, name, COALESCE(NULLIF(road_address, ''), address, '') AS normalized_address
            FROM restaurants
            """
        ).fetchall()

        existing_place_ids = {row["kakao_place_id"] for row in existing_rows if row["kakao_place_id"]}
        existing_name_address = {
            (row["name"], row["normalized_address"])
            for row in existing_rows
            if row["name"] and row["normalized_address"]
        }

        to_insert = []
        skipped = 0
        for restaurant in payload:
            normalized_address = restaurant["road_address"] or restaurant["address"] or ""
            duplicate = False

            if restaurant["kakao_place_id"] and restaurant["kakao_place_id"] in existing_place_ids:
                duplicate = True
            elif normalized_address and (restaurant["name"], normalized_address) in existing_name_address:
                duplicate = True

            if duplicate:
                skipped += 1
                continue

            to_insert.append(restaurant)
            if restaurant["kakao_place_id"]:
                existing_place_ids.add(restaurant["kakao_place_id"])
            if normalized_address:
                existing_name_address.add((restaurant["name"], normalized_address))

        if to_insert:
            conn.executemany(
                """
                INSERT INTO restaurants (
                    external_id, kakao_place_id, name, category, address, road_address,
                    distance_m, phone, place_url, x, y, source,
                    indoor_score, spicy_score, soup_score, noodle_score,
                    rice_score, price_level, is_active
                )
                VALUES (
                    :external_id, :kakao_place_id, :name, :category, :address, :road_address,
                    :distance_m, :phone, :place_url, :x, :y, :source,
                    :indoor_score, :spicy_score, :soup_score, :noodle_score,
                    :rice_score, :price_level, :is_active
                )
                """,
                to_insert,
            )

    return {"inserted": len(to_insert), "skipped": skipped}


def add_visit(restaurant_id: int, visited_on: str | None = None, meal_type: str = "점심", notes: str = "") -> None:
    visited_on = visited_on or date.today().isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO visit_history (restaurant_id, visited_on, meal_type, notes)
            VALUES (?, ?, ?, ?)
            """,
            (restaurant_id, visited_on, meal_type, notes),
        )


def list_restaurants() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM restaurants
            WHERE is_active = 1
            ORDER BY distance_m ASC, name ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_restaurant_count() -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS count FROM restaurants").fetchone()
    return int(row["count"])


def get_recent_visits(limit: int = 10) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                vh.visited_on,
                vh.meal_type,
                r.name AS restaurant_name,
                (
                    SELECT COUNT(*)
                    FROM visit_history vh2
                    WHERE vh2.restaurant_id = vh.restaurant_id
                ) AS visit_count
            FROM visit_history vh
            JOIN restaurants r ON r.id = vh.restaurant_id
            ORDER BY vh.visited_on DESC, vh.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_restaurants_with_history() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                r.*,
                COUNT(vh.id) AS total_visits,
                MAX(vh.visited_on) AS last_visited_on
            FROM restaurants r
            LEFT JOIN visit_history vh ON vh.restaurant_id = r.id
            WHERE r.is_active = 1
            GROUP BY r.id
            ORDER BY r.distance_m ASC, r.name ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]
