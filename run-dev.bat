@echo off
echo Starting Music Player in Development Mode
echo.

call kill-processes.bat

echo Starting Backend Server...
start "Backend" cmd /k "cd backend && python api_server.py"

echo Waiting for backend to start...
timeout /t 5 /nobreak > nul

echo Starting React Dev Server...
start "Frontend" cmd /k "cd frontend && npm start"

echo Waiting for React to start...
timeout /t 10 /nobreak > nul

echo Starting Electron...
cd electron
npm run dev

pause