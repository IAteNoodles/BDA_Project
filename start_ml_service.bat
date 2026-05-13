@echo off
cd /d "C:\Users\Noodl\Projects\BDA"

echo.
echo ================================================================================
echo Starting ML Service (Port 5000)
echo ================================================================================
echo.

call bda_lstm_env\Scripts\activate.bat
start "ML Service" python ml_service.py

timeout /t 3 /nobreak

echo.
echo ML Service started. Check http://localhost:5000/ml/health
echo.
echo Run your Java backend and frontend to see forecasts!
echo.
pause
