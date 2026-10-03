@echo off
setlocal

cd /d "%~dp0"

echo -= Activating virtual environment =-
call .venv\Scripts\activate.bat

echo -= Starting Flask app =-

echo Starting the application...
start http://127.0.0.1:5000
python app.py

endlocal
