@echo off
echo Starting StrelokAI...
cd /d "%~dp0"
python -m streamlit run app.py
pause
