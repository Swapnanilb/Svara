@echo off
echo Killing existing processes...
taskkill /f /im node.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im electron.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo Starting Music Player...
echo Backend starting on port 5001...
echo Frontend starting on port 3000...
echo Electron starting...
echo.

cd frontend
start "Frontend" npm start

echo Waiting for frontend to start...
timeout /t 3 /nobreak >nul

cd ..\electron
start "Electron" npm run dev

echo Waiting for backend to start...
timeout /t 3 /nobreak >nul


cd ..\backend
start "Backend" cmd /k "..\test\Scripts\python.exe api_server.py"

echo.
echo Development environment started!
pause