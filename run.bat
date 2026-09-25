@echo off
REM ============================================================
REM Launcher Bot AntiGravity API (Windows)
REM Klik dua kali file ini untuk menjalankan bot
REM ============================================================
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Belum di-setup. Menjalankan setup dulu...
    call setup.bat
)

if not exist "akun.txt" (
    echo [ERROR] File akun.txt tidak ditemukan!
    echo         Buat file akun.txt di folder ini dengan format:
    echo         email@gmail.com^|password123
    pause
    exit /b 1
)

".venv\Scripts\python.exe" bot_api.py %*
pause
