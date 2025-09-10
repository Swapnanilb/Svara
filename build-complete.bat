@echo off
echo Building SVARA Music Player...

:: Kill processes
taskkill /f /im api_server.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1

:: Clean
if exist "SVARA-Music-Player" rmdir /s /q "SVARA-Music-Player"

:: Build React
cd frontend
call npm run build
cd ..

:: Build Python backend
cd backend
call ..\myVenv\Scripts\pyinstaller --onefile --console api_server.py
cd ..

:: Create package structure
mkdir "SVARA-Music-Player"
mkdir "SVARA-Music-Player\resources"
mkdir "SVARA-Music-Player\resources\frontend"
mkdir "SVARA-Music-Player\resources\backend"

:: Copy files
copy "electron\main.js" "SVARA-Music-Player\"
copy "electron\preload.js" "SVARA-Music-Player\"
copy "electron\package.json" "SVARA-Music-Player\"
xcopy "frontend\build" "SVARA-Music-Player\resources\frontend\build" /E /I /Y
copy "backend\dist\api_server.exe" "SVARA-Music-Player\resources\backend\"

:: Package with electron
cd "SVARA-Music-Player"
call npm install electron electron-packager --save-dev
call npx electron-packager . "SVARA Music Player" --platform=win32 --arch=x64 --out=dist --overwrite
cd ..

echo.
echo Executable: SVARA-Music-Player\dist\SVARA Music Player-win32-x64\SVARA Music Player.exe
pause