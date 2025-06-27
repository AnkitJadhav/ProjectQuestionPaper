@echo off
echo Starting Question Paper Generator...
echo ====================================

REM Activate virtual environment
call .\venv\Scripts\activate.bat

REM Load environment variables
if exist .env (
    for /f "tokens=*" %%a in (.env) do (
        set %%a
    )
)

REM Start the application
python start_app.py

pause 