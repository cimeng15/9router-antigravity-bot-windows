@echo off
REM ============================================================
REM Setup Script - Bot AntiGravity API (Windows)
REM Otomatis bikin virtual environment + install dependencies
REM ============================================================

setlocal
cd /d "%~dp0"
set VENV_DIR=%~dp0.venv

echo ==============================================
echo   Bot AntiGravity - Setup (Windows)
echo ==============================================
echo.

REM --- Cek Python ---
set PYTHON=
for %%P in (py python) do (
    if not defined PYTHON (
        %%P --version >nul 2>&1 && set PYTHON=%%P
    )
)
if not defined PYTHON (
    echo [ERROR] Python tidak ditemukan!
    echo         Install Python 3.9+ dari https://python.org
    echo         PENTING: centang "Add Python to PATH" saat install.
    pause
    exit /b 1
)

echo [OK] Python ditemukan:
%PYTHON% --version
echo.

REM --- Bikin virtual environment ---
if exist "%VENV_DIR%\Scripts\python.exe" (
    echo [OK] Virtual environment sudah ada di .venv\
) else (
    echo [INFO] Membuat virtual environment di .venv\ ...
    %PYTHON% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Gagal membuat venv!
        pause
        exit /b 1
    )
    echo [OK] Virtual environment berhasil dibuat!
)
echo.

REM --- Install dependencies ---
echo [INFO] Menginstall dependencies di venv...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
"%VENV_DIR%\Scripts\python.exe" -m pip install "camoufox[geoip]"
if errorlevel 1 (
    echo [ERROR] Gagal install dependencies!
    pause
    exit /b 1
)
echo.
echo [INFO] Mengunduh browser Camoufox ^(sekali saja^)...
"%VENV_DIR%\Scripts\python.exe" -m camoufox fetch
if errorlevel 1 (
    echo [ERROR] Gagal mengunduh browser Camoufox!
    pause
    exit /b 1
)
echo.
echo [OK] Setup selesai!

REM --- Cek akun.txt ---
echo.
if exist "%~dp0akun.txt" (
    echo [OK] File akun.txt ditemukan.
) else (
    echo [INFO] File akun.txt belum ada.
    echo        Buat file akun.txt di folder ini dengan format:
    echo        email@gmail.com^|password123
)

echo.
echo ==============================================
echo   Cara jalankan:
echo.
echo   1. Isi akun.txt dengan: email^|password
echo   2. Klik dua kali run.bat
echo      ATAU dari terminal:
echo      .venv\Scripts\python bot_api.py
echo ==============================================
pause
