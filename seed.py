from db import add_visit, clear_all, get_restaurants_with_history, init_db, upsert_restaurants
from kakao_local import search_nearby_restaurants



def seed_data(reset: bool = False) -> None:
    init_db()
    if reset:
        clear_all()

    restaurants = search_nearby_restaurants()
    upsert_restaurants(restaurants)

    existing_rows = get_restaurants_with_history()
    if any(row["total_visits"] for row in existing_rows):
        return

    existing = {row["external_id"]: row["id"] for row in existing_rows}
    seed_visits = [
        ("sample-1", "2026-06-02", "\uc810\uc2ec"),
        ("sample-2", "2026-06-09", "\uc810\uc2ec"),
        ("sample-4", "2026-06-16", "\uc810\uc2ec"),
        ("sample-6", "2026-06-18", "\uc810\uc2ec"),
        ("sample-1", "2026-06-20", "\uc810\uc2ec"),
    ]

    if not any(external_id.startswith("sample-") for external_id in existing):
        ordered_ids = [row["external_id"] for row in existing_rows[:4]]
        if len(ordered_ids) >= 4:
            seed_visits = [
                (ordered_ids[0], "2026-06-02", "\uc810\uc2ec"),
                (ordered_ids[1], "2026-06-09", "\uc810\uc2ec"),
                (ordered_ids[2], "2026-06-16", "\uc810\uc2ec"),
                (ordered_ids[0], "2026-06-20", "\uc810\uc2ec"),
            ]

    for external_id, visited_on, meal_type in seed_visits:
        restaurant_id = existing.get(external_id)
        if restaurant_id:
            add_visit(restaurant_id, visited_on=visited_on, meal_type=meal_type)


if __name__ == "__main__":
    seed_data(reset=True)