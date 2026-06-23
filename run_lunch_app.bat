@echo off
cd /d "G:\내 드라이브\VScode\lunck_recommender"

call ".venv\Scripts\activate.bat"

echo.
echo ==============================================================
echo FastAPI Lunch Recommender Server
echo ==============================================================
echo.
echo Server URL: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.

python app.py

pause