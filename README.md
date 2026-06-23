# Lunch Recommender

Python + Streamlit + SQLite based office lunch recommender.

- Base address: Seoul, Jung-gu, Eulji-ro 16
- Search radius: 1.5km
- Recommendation count: 4
- Mix: 3 visited restaurants + 1 unvisited restaurant
- Factors: recent visit history + lunchtime weather
- UI language: Korean

## Files

```text
.
|- app.py
|- db.py
|- recommender.py
|- weather.py
|- kakao_local.py
|- seed.py
|- requirements.txt
|- .env.example
`- README.md
```

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes

- Local SQLite only. Internal data is kept inside the current workspace.
- If Kakao API keys are missing, the app uses sample restaurant data.
- `weather.py` currently returns sample weather data and is ready for later API integration.