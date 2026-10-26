@echo off
cd /d "%~dp0backend"
echo Starting Appilot FastAPI Backend Server...
.\.venv\Scripts\python.exe run.py
pause
