@echo off
cd /d "G:\내 드라이브\VScode\lunck_recommender"

call ".venv\Scripts\activate.bat"

streamlit run app.py

pause