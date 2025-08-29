@echo off
setlocal enabledelayedexpansion

echo ========================================
echo    CVE Security Servers Launcher
echo ========================================
echo.

:: Set the base directory (current directory by default)
set "BASE_DIR=%~dp0"
echo Base directory: %BASE_DIR%
echo.

:: Define your specific servers with their configurations
echo Initializing CVE Security Servers...
echo.

:: Server 1: OpenCVE.io Server (Port 5000)
set "SERVER_1_NAME=OpenCVE.io Server"
set "SERVER_1_PATH=%BASE_DIR%opencve.io"
set "SERVER_1_FILE=simple_cve_server.py"
set "SERVER_1_PORT=5000"
set "SERVER_1_DESC=CVE scraper from opencve.io"

:: Server 2: CVEFind.com Server (Port 5001)
set "SERVER_2_NAME=CVEFind.com Server"
set "SERVER_2_PATH=%BASE_DIR%cvefind.com"
set "SERVER_2_FILE=cvefind_server.py"
set "SERVER_2_PORT=5001"
set "SERVER_2_DESC=CVE scraper from cvefind.com"

:: Server 3: DGSSI Bulletins Server (Port 5002)
set "SERVER_3_NAME=DGSSI Bulletins Server"
set "SERVER_3_PATH=%BASE_DIR%dgssi"
set "SERVER_3_FILE=dgssi_scraper.py"
set "SERVER_3_PORT=5002"
set "SERVER_3_DESC=Security bulletins from DGSSI Morocco"

set /a TOTAL_SERVERS=3

echo Checking server availability...
echo.

:: Check if all servers exist
set /a AVAILABLE_SERVERS=0

for /l %%i in (1,1,%TOTAL_SERVERS%) do (
    set "SERVER_PATH=!SERVER_%%i_PATH!"
    set "SERVER_FILE=!SERVER_%%i_FILE!"
    set "SERVER_NAME=!SERVER_%%i_NAME!"

    if exist "!SERVER_PATH!\!SERVER_FILE!" (
        echo [✓] !SERVER_NAME! - Ready
        set /a AVAILABLE_SERVERS+=1
    ) else (
        echo [✗] !SERVER_NAME! - NOT FOUND: !SERVER_PATH!\!SERVER_FILE!
    )
)

echo.
echo ========================================
echo Server Status: %AVAILABLE_SERVERS%/%TOTAL_SERVERS% servers available
echo ========================================

if %AVAILABLE_SERVERS%==0 (
    echo.
    echo ❌ No servers found! Please check your directory structure.
    echo Expected structure:
    echo   %BASE_DIR%opencve.io\simple_cve_server.py
    echo   %BASE_DIR%cvefind.com\cvefind_server.py
    echo   %BASE_DIR%dgssi\dgssi_scraper.py
    echo.
    pause
    exit /b 1
)

echo.
echo Server Details:
echo ---------------
for /l %%i in (1,1,%TOTAL_SERVERS%) do (
    set "SERVER_NAME=!SERVER_%%i_NAME!"
    set "SERVER_PORT=!SERVER_%%i_PORT!"
    set "SERVER_DESC=!SERVER_%%i_DESC!"
    echo %%i. !SERVER_NAME! ^(Port !SERVER_PORT!^)
    echo    └─ !SERVER_DESC!
)

echo.
set /p "CONFIRM=Start all available servers? (Y/N): "
if /i not "%CONFIRM%"=="Y" if /i not "%CONFIRM%"=="YES" (
    echo Operation cancelled.
    pause
    exit /b 0
)

echo.
echo Starting CVE Security Servers...
echo ================================

:: Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH!
    echo Please install Python 3.7+ and try again.
    pause
    exit /b 1
)

:: Start each server
for /l %%i in (1,1,%TOTAL_SERVERS%) do (
    set "SERVER_PATH=!SERVER_%%i_PATH!"
    set "SERVER_FILE=!SERVER_%%i_FILE!"
    set "SERVER_NAME=!SERVER_%%i_NAME!"
    set "SERVER_PORT=!SERVER_%%i_PORT!"

    if exist "!SERVER_PATH!\!SERVER_FILE!" (
        echo [%%i/%TOTAL_SERVERS%] Starting !SERVER_NAME! on port !SERVER_PORT!...

        :: Install requirements if requirements.txt exists
        if exist "!SERVER_PATH!\requirements.txt" (
            echo   └─ Installing dependencies...
            start /wait /min cmd /c "cd /d "!SERVER_PATH!" && pip install -r requirements.txt >nul 2>&1"
        )

        :: Start the server in a new window
        start "!SERVER_NAME! (Port !SERVER_PORT!)" cmd /k "cd /d "!SERVER_PATH!" && echo Starting !SERVER_NAME!... && echo Endpoint: http://localhost:!SERVER_PORT! && echo. && python !SERVER_FILE!"

        :: Small delay between starting servers
        timeout /t 3 /nobreak >nul
        echo   └─ ✓ Started successfully
    ) else (
        echo [%%i/%TOTAL_SERVERS%] ❌ Skipping !SERVER_NAME! - File not found
    )
    echo.
)

echo ========================================
echo 🚀 All available servers have been started!
echo ========================================
echo.
echo Server Endpoints:
echo ─────────────────
echo • OpenCVE.io Server:    http://localhost:5000/api/cves
echo • CVEFind.com Server:   http://localhost:5001/api/cves
echo • DGSSI Bulletins:      http://localhost:5002/api/bulletins
echo.
echo 📝 Each server is running in its own command window.
echo 🛑 Close individual windows to stop specific servers.
echo 🔄 All servers will auto-install dependencies on first run.
echo.
echo Press any key to open server status page...
pause >nul

:: Try to open a simple status page
echo ^<html^>^<head^>^<title^>CVE Servers Status^</title^>^</head^> > "%TEMP%\cve_servers.html"
echo ^<body^>^<h1^>CVE Security Servers^</h1^> >> "%TEMP%\cve_servers.html"
echo ^<ul^> >> "%TEMP%\cve_servers.html"
echo ^<li^>^<a href="http://localhost:5000/api/cves"^>OpenCVE.io Server^</a^> - Port 5000^</li^> >> "%TEMP%\cve_servers.html"
echo ^<li^>^<a href="http://localhost:5001/api/cves"^>CVEFind.com Server^</a^> - Port 5001^</li^> >> "%TEMP%\cve_servers.html"
echo ^<li^>^<a href="http://localhost:5002/api/bulletins"^>DGSSI Bulletins^</a^> - Port 5002^</li^> >> "%TEMP%\cve_servers.html"
echo ^</ul^>^</body^>^</html^> >> "%TEMP%\cve_servers.html"

start "" "%TEMP%\cve_servers.html"
