@echo off
cd /d "C:\Users\Noodl\Projects\BDA"
call bda_lstm_env\Scripts\activate.bat
python forecast_lstm.py
pause
