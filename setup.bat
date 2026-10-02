@echo off
REM ============================================================
REM Setup Script - Bot AntiGravity API (Windows) — v2 (lebih tahan error)
REM Perbaikan dibanding v1:
REM   1. Cek versi Python (Camoufox butuh 3.10+, bukan sekadar 3.9)
REM   2. Upgrade pip/setuptools/wheel dulu (pip lama = sumber error utama)
REM   3. Install bertahap dengan fallback:
REM      camoufox[geoip] -> camoufox (tanpa geoip) kalau gagal
REM   4. "camoufox fetch" di-retry (download browser kadang gagal/timeout)
REM ============================================================

setlocal EnableExtensions
cd /d "%~dp0"
set VENV_DIR=%~dp0.venv

echo ==============================================
echo   Bot AntiGravity - Setup (Windows)
echo ==============================================
echo.

REM ---------- [1/6] Cari Python ----------
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
    echo         Python 3.10 / 3.11 / 3.12 paling aman.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('%PYTHON% -c "import sys;print(sys.version.split()[0])" 2^>nul') do set PYVER=%%v
echo [OK] Python ditemukan: %PYVER%
echo.

REM ---------- [2/6] Cek versi minimal 3.10 ----------
%PYTHON% -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
    echo [ERROR] Python yang terpasang: %PYVER%
    echo         Camoufox butuh Python 3.10+ (lihat pypi.org/pypi/camoufox).
    echo         Solusi: install Python 3.10 / 3.11 / 3.12 dari python.org,
    echo         lalu jalankan setup.bat lagi.
    pause
    exit /b 1
)

REM ---------- [3/6] Bikin virtual environment ----------
if exist "%VENV_DIR%\Scripts\python.exe" (
    echo [OK] Virtual environment sudah ada di .venv\
) else (
    echo [INFO] Membuat virtual environment di .venv\ ...
    %PYTHON% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Gagal membuat venv!
        echo         Kemungkinan: instalasi Python tidak lengkap.
        echo         Solusi: install ulang Python dan pilih instalasi lengkap.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment berhasil dibuat!
)
echo.

REM ---------- [4/6] Upgrade pip, setuptools, wheel ----------
echo [INFO] Upgrade pip / setuptools / wheel (mencegah error dependency)...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo [WARN] Upgrade pip gagal, lanjut dengan pip bawaan...
)
echo.

REM ---------- [5/6] Install camoufox (dengan fallback) ----------
echo [INFO] Menginstall Camoufox + GeoIP...
"%VENV_DIR%\Scripts\python.exe" -m pip install "camoufox[geoip]>=0.5.6"
if errorlevel 1 (
    echo.
    echo [WARN] camoufox[geoip] gagal terpasang. Mencoba TANPA geoip...
    echo        (fitur geoip hanya membuat lokasi IP konsisten, bot tetap
    echo         jalan tanpa itu)
    "%VENV_DIR%\Scripts\python.exe" -m pip install "camoufox>=0.5.6"
    if errorlevel 1 (
        echo.
        echo [ERROR] Gagal menginstall Camoufox!
        echo         Penyebab yang paling sering:
        echo         1. Versi Python terlalu baru (baru rilis, belum ada
        echo            wheel-nya) -^> pakai Python 3.10 / 3.11 / 3.12
        echo         2. Antivirus memblokir pip -^> tambahkan folder ini dan
        echo            folder Python ke exclusion antivirus
        echo         3. Koneksi internet/proxy -^> coba jaringan lain
        echo.
        pause
        exit /b 1
    )
)
echo.

REM ---------- [6/6] Unduh browser Camoufox (dengan retry) ----------
echo [INFO] Mengunduh browser Camoufox (sekitar 150 MB, sekali saja)...
"%VENV_DIR%\Scripts\python.exe" -m camoufox fetch
if errorlevel 1 (
    echo [WARN] Percobaan pertama gagal, mencoba lagi dalam 5 detik...
    timeout /t 5 /nobreak >nul
    "%VENV_DIR%\Scripts\python.exe" -m camoufox fetch
    if errorlevel 1 (
        echo [ERROR] Gagal mengunduh browser Camoufox setelah 2x percobaan.
        echo         Biasanya karena koneksi ke GitHub terputus.
        echo         Solusi: jalankan ulang setup.bat (unduhan dilanjutkan),
        echo         atau pakai VPN/jaringan lain bila GitHub diblokir.
        pause
        exit /b 1
    )
)

REM ---------- Verifikasi akhir ----------
echo.
echo [INFO] Verifikasi instalasi...
"%VENV_DIR%\Scripts\python.exe" -c "from camoufox.sync_api import Camoufox; print('[OK] Camoufox siap dipakai!')"
if errorlevel 1 (
    echo [ERROR] Camoufox terpasang tapi tidak bisa diimport.
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
echo   1. Isi akun.txt dengan: email^|password
echo   2. Klik dua kali run.bat
echo ==============================================
pause
