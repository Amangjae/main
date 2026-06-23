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
    
    # ============ SQLite 성능 최적화 ============
    conn.execute("PRAGMA synchronous = NORMAL")      # 속도 향상
    conn.execute("PRAGMA cache_size = -64000")       # 64MB 캐시
    conn.execute("PRAGMA journal_mode = WAL")        # Write-Ahead Logging
    conn.execute("PRAGMA temp_store = MEMORY")       # 임시 저장소를 메모리에
    conn.execute("PRAGMA query_only = False")        # 쓰기 가능
    
    return conn



def _ensure_column(conn: sqlite3.Connection, column_name: str, column_sql: str) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(restaurants)").fetchall()}
    if column_name not in columns:
        conn.execute(f"ALTER TABLE restaurants ADD COLUMN {column_sql}")



def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            PRAGMA foreign_keys = ON;

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
                price_level TEXT NOT NULL DEFAULT 'bo-tong',
                is_active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS visit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant_id INTEGER NOT NULL,
                visited_on TEXT NOT NULL,
                meal_type TEXT NOT NULL DEFAULT 'lunch',
                notes TEXT,
                FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE
            );
            
            -- ============ 인덱스 추가 (성능 최적화) ============
            CREATE INDEX IF NOT EXISTS idx_restaurants_is_active 
                ON restaurants(is_active);
            CREATE INDEX IF NOT EXISTS idx_restaurants_distance_m 
                ON restaurants(distance_m);
            CREATE INDEX IF NOT EXISTS idx_restaurants_category 
                ON restaurants(category);
            CREATE INDEX IF NOT EXISTS idx_visit_history_restaurant_id 
                ON visit_history(restaurant_id);
            CREATE INDEX IF NOT EXISTS idx_visit_history_visited_on 
                ON visit_history(visited_on DESC);
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



def upsert_restaurants(restaurants: Iterable[dict]) -> None:
    payload = []
    for restaurant in restaurants:
        payload.append(
            {
                "external_id": restaurant.get("external_id"),
                "kakao_place_id": restaurant.get("kakao_place_id"),
                "name": restaurant["name"],
                "category": restaurant["category"],
                "address": restaurant.get("address", ""),
                "road_address": restaurant.get("road_address", ""),
                "distance_m": restaurant["distance_m"],
                "phone": restaurant.get("phone", ""),
                "place_url": restaurant.get("place_url", ""),
                "x": restaurant.get("x", ""),
                "y": restaurant.get("y", ""),
                "source": restaurant.get("source", "sample"),
                "indoor_score": restaurant.get("indoor_score", 4),
                "spicy_score": restaurant.get("spicy_score", 2),
                "soup_score": restaurant.get("soup_score", 2),
                "noodle_score": restaurant.get("noodle_score", 2),
                "rice_score": restaurant.get("rice_score", 2),
                "price_level": restaurant.get("price_level", "\ubcf4\ud1b5"),
                "is_active": restaurant.get("is_active", 1),
            }
        )

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



def insert_restaurant(restaurant: dict) -> str:
    normalized_address = restaurant.get("road_address") or restaurant.get("address") or ""

    with get_connection() as conn:
        duplicate = conn.execute(
            """
            SELECT id
            FROM restaurants
            WHERE (kakao_place_id IS NOT NULL AND kakao_place_id = ?)
               OR (name = ? AND COALESCE(road_address, address, '') = ?)
            LIMIT 1
            """,
            (
                restaurant.get("kakao_place_id"),
                restaurant["name"],
                normalized_address,
            ),
        ).fetchone()

        if duplicate:
            return "duplicate"

        conn.execute(
            """
            INSERT INTO restaurants (
                external_id, kakao_place_id, name, category, address, road_address,
                distance_m, phone, place_url, x, y, source,
                indoor_score, spicy_score, soup_score, noodle_score,
                rice_score, price_level, is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                restaurant.get("external_id"),
                restaurant.get("kakao_place_id"),
                restaurant["name"],
                restaurant["category"],
                restaurant.get("address", ""),
                restaurant.get("road_address", ""),
                restaurant["distance_m"],
                restaurant.get("phone", ""),
                restaurant.get("place_url", ""),
                restaurant.get("x", ""),
                restaurant.get("y", ""),
                restaurant.get("source", "kakao"),
                restaurant.get("indoor_score", 4),
                restaurant.get("spicy_score", 2),
                restaurant.get("soup_score", 2),
                restaurant.get("noodle_score", 2),
                restaurant.get("rice_score", 2),
                restaurant.get("price_level", "\ubcf4\ud1b5"),
                restaurant.get("is_active", 1),
            ),
        )
    return "inserted"



def save_kakao_restaurants(restaurants: Iterable[dict]) -> dict:
    inserted = 0
    skipped = 0

    for restaurant in restaurants:
        result = insert_restaurant(restaurant)
        if result == "inserted":
            inserted += 1
        else:
            skipped += 1

    return {"inserted": inserted, "skipped": skipped}



def add_visit(restaurant_id: int, visited_on: str | None = None, meal_type: str = "\uc810\uc2ec", notes: str = "") -> None:
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
    """최근 방문 이력 조회 (최적화된 GROUP BY)"""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                vh.visited_on,
                vh.meal_type,
                r.name AS restaurant_name,
                COUNT(*) OVER (PARTITION BY vh.restaurant_id) AS visit_count
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