@echo off
REM ============================================================
REM Setup Script - Bot AntiGravity API (Windows) — v3 (CHROME)
REM TIDAK lagi pakai Camoufox (sering error dependency di Windows).
REM Sekarang pakai Google Chrome yang sudah ada di komputer + DrissionPage.
REM Yang di-install cuma 1 package kecil: DrissionPage.
REM ============================================================

setlocal EnableExtensions
cd /d "%~dp0"
set VENV_DIR=%~dp0.venv

echo ==============================================
echo   Bot AntiGravity - Setup (Windows, Chrome)
echo ==============================================
echo.

REM ---------- [1/5] Cari Python ----------
set PYTHON=
py -3 --version >nul 2>&1 && set PYTHON=py -3
if not defined PYTHON (
    python --version >nul 2>&1 && set PYTHON=python
)
if not defined PYTHON (
    echo [ERROR] Python tidak ditemukan!
    echo.
    echo         Install Python 3.10 atau lebih baru dari https://python.org
    echo         PENTING: centang "Add Python to PATH" saat install.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('%PYTHON% -c "import sys;print(sys.version.split()[0])" 2^>nul') do set PYVER=%%v
echo [OK] Python ditemukan: %PYVER%
echo.

REM ---------- [2/5] Cek versi minimal 3.10 ----------
%PYTHON% -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
    echo [ERROR] Python yang terpasang: %PYVER%
    echo         Bot ini butuh Python 3.10 atau lebih baru.
    echo         Solusi: install Python 3.10 / 3.11 / 3.12 dari python.org,
    echo         lalu jalankan setup.bat lagi.
    pause
    exit /b 1
)

REM ---------- [3/5] Cek Google Chrome ----------
echo [INFO] Mencari Google Chrome...
set CHROME_FOUND=
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set CHROME_FOUND=1
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set CHROME_FOUND=1
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set CHROME_FOUND=1

if not defined CHROME_FOUND (
    echo [ERROR] Google Chrome tidak ditemukan di lokasi standar!
    echo.
    echo         Bot ini memakai Chrome untuk login Google.
    echo         Install Chrome dari: https://www.google.com/chrome/
    echo         Lalu jalankan setup.bat lagi.
    pause
    exit /b 1
)
echo [OK] Google Chrome ditemukan!
echo.

REM ---------- [4/5] Bikin virtual environment ----------
if exist "%VENV_DIR%\Scripts\python.exe" (
    echo [OK] Virtual environment sudah ada di .venv\
) else (
    echo [INFO] Membuat virtual environment di .venv\ ...
    %PYTHON% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Gagal membuat venv!
        echo         Solusi: install ulang Python dengan opsi lengkap.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment berhasil dibuat!
)
echo.

REM ---------- [5/5] Install DrissionPage (satu-satunya dependency) ----------
echo [INFO] Upgrade pip...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip >nul 2>&1
echo [INFO] Menginstall DrissionPage (package kecil, cepat)...
"%VENV_DIR%\Scripts\python.exe" -m pip install DrissionPage
if errorlevel 1 (
    echo [ERROR] Gagal install DrissionPage.
    echo         Solusi: cek koneksi internet, lalu jalankan ulang setup.bat
    pause
    exit /b 1
)

REM ---------- Verifikasi akhir ----------
echo.
echo [INFO] Verifikasi instalasi...
"%VENV_DIR%\Scripts\python.exe" -c "from DrissionPage import ChromiumPage; print('[OK] Bot siap dipakai!')"
if errorlevel 1 (
    echo [ERROR] DrissionPage terpasang tapi tidak bisa diimport.
    echo         Coba jalankan setup.bat sekali lagi.
    pause
    exit /b 1
)

REM ---------- Cek akun.txt ----------
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
echo   Setup selesai!
echo.
echo   Cara jalankan:
echo   1. Pastikan 9Router jalan (http://localhost:20128)
echo   2. Isi akun.txt dengan: email^|password
echo   3. Klik dua kali run.bat
echo ==============================================
pause
