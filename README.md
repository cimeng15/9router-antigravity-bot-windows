# Bot AntiGravity — Auto Add Account ke 9Router (Windows)

Bot otomatis untuk menambahkan akun Google (Antigravity) ke 9Router via API.
Berbasis **Python + Camoufox** (anti-detect Firefox) dan **API-driven** —
tidak perlu klik UI dashboard dan tidak butuh server callback.

> **Versi Windows ini untuk 9Router yang berjalan lokal** di
> `http://localhost:20128` — jalankan 9Router dulu di komputer yang sama.

---

## Daftar Isi

- [Requirements](#requirements)
- [Setup](#setup)
- [Penggunaan](#penggunaan)
- [Opsi Command Line](#opsi-command-line)
- [Cara Kerja Bot](#cara-kerja-bot)
- [Troubleshooting](#troubleshooting)
- [Keamanan](#keamanan)

---

## Requirements

1. **Windows 10 / 11**
2. **Python 3.9+** — download dari [python.org](https://www.python.org/downloads/)
   > ⚠️ Saat install, **centang "Add Python to PATH"** — ini WAJIB
3. **9Router** berjalan di komputer yang sama (`http://localhost:20128`)
   dengan opsi **login tidak diwajibkan** (require login disabled)
4. Koneksi internet (untuk login ke Google)

Tidak perlu install Chrome/Chromium — Camoufox mengunduh browser-nya sendiri.

---

## Setup

### Cara otomatis (direkomendasikan)

1. Copy folder ini ke komputer Windows (misal: `D:\9router-antigravity-windows\`)
2. **Klik dua kali `setup.bat`**

`setup.bat` akan otomatis:
- Mendeteksi Python (`py` atau `python`)
- Membuat virtual environment di `.venv\`
- Menginstall `camoufox[geoip]` + dependencies
- Mengunduh browser Camoufox (±150 MB, **sekali saja**)
- Mengecek apakah `akun.txt` sudah ada

Jika berhasil, di akhir muncul:

```
[OK] Setup selesai!
```

### Cara manual (jika setup.bat gagal)

Buka **Command Prompt** / **PowerShell** di folder ini, lalu jalankan satu per satu:

```bat
py -m venv .venv
.venv\Scripts\pip install --upgrade pip
.venv\Scripts\pip install camoufox[geoip]
.venv\Scripts\python -m camoufox fetch
```

---

## Penggunaan

### Langkah 1 — Isi akun

Buka file **`akun.txt`** (di folder yang sama dengan `bot_api.py`) dengan Notepad:

```
email@gmail.com|password123
akun2@gmail.com|password456
```

> Format: `email|password` dipisah tanda `|`, **satu baris per akun**.
> Akun yang **sukses akan otomatis dihapus** dari file ini —
> kalau bot dijalankan ulang, hanya akun yang belum sukses yang diproses.

### Langkah 2 — Pastikan 9Router jalan

Buka `http://localhost:20128` di browser. Dashboard harus tampil.
Jika tidak, nyalakan dulu 9Router-nya.

> Tes cepat API: buka `http://localhost:20128/api/providers` —
> harus muncul JSON berisi daftar koneksi.

### Langkah 3 — Jalankan bot

**Cara termudah:** klik dua kali **`run.bat`**

Atau dari terminal (Command Prompt / PowerShell) di folder ini:

```bat
:: mode normal (default, direkomendasikan)
.venv\Scripts\python bot_api.py

:: mode cepat (internet bagus)
.venv\Scripts\python bot_api.py --fast

:: lihat jendela browser saat proses berjalan (bagus untuk debugging)
.venv\Scripts\python bot_api.py --headed

:: delay 10 detik antar akun
.venv\Scripts\python bot_api.py --delay 10

:: file akun lain
.venv\Scripts\python bot_api.py --file akun_lain.txt
```

### Langkah 4 — Cek hasil

Saat berjalan, bot menampilkan progres per akun:

```
=======================================================
 Akun 1/2: email@gmail.com
=======================================================
 [1/6] Membuat sesi OAuth via API 9Router...
 [2/6] Membuka Camoufox (anti-detect Firefox)...
 [3/6] Membuka halaman login Google...
 [4/6] Login Google: email@gmail.com
 [5/6] Menunggu konfirmasi Google & kode OAuth...
        >> Kode OAuth tertangkap dari redirect!
 [6/6] Mendaftarkan akun ke 9Router (exchange)...

 [SUKSES] Akun 1/2: email@gmail.com
 [INFO]   Akun terverifikasi ada di /api/providers
 [INFO]   Akun dihapus dari akun.txt
```

Ringkasan di akhir:

```
 SELESAI!
 Total  : 2 akun
 Sukses : 2 akun
 Gagal  : 0 akun
```

Verifikasi manual: buka `http://localhost:20128/api/providers` di browser —
akun baru harus muncul di daftar dengan `provider: antigravity`.

---

## Opsi Command Line

| Opsi | Default | Keterangan |
|------|---------|------------|
| `--base` | `http://localhost:20128` | Base URL 9Router |
| `--file` | `akun.txt` | Path file akun |
| `--headed` | headless (tanpa jendela) | Tampilkan jendela browser |
| `--fast` | normal | Delay minimal (untuk internet cepat) |
| `--delay` | `3` | Jeda antar akun (detik) |
| `--port` | `8080` | Port callback loopback OAuth |

Contoh kombinasi:

```bat
.venv\Scripts\python bot_api.py --headed --delay 10 --file daftar2.txt
```

Atau lewat `run.bat` (argumen diteruskan otomatis):

```bat
run.bat --headed
run.bat --fast --delay 5
```

---

## Cara Kerja Bot

1. `GET /api/oauth/antigravity/authorize` → minta URL login Google + state + codeVerifier ke 9Router
2. Browser Camoufox membuka halaman login Google (email → Next → password → Next)
3. Halaman konfirmasi Google (bahasa Inggris/Indonesia) diklik otomatis —
   termasuk tombol "Login" di halaman "Pastikan Anda mendownload aplikasi ini dari Google"
4. Kode OAuth dari redirect `localhost:8080/callback` **ditangkap langsung** dari
   browser (route interception) — tidak butuh port terbuka / server callback
5. `POST /api/oauth/antigravity/exchange` → akun terdaftar di 9Router
6. Verifikasi via `GET /api/providers` → sukses = akun dihapus dari `akun.txt`

---

## Troubleshooting

### "Python tidak ditemukan"
Install Python dari [python.org](https://www.python.org/downloads/) dan
**centang "Add Python to PATH"** saat install, lalu jalankan ulang `setup.bat`.
Cek dengan: `py --version` di CMD.

### "9Router tidak bisa dihubungi"
- Pastikan 9Router berjalan: buka `http://localhost:20128` di browser
- Kalau port-nya beda, tambahkan `--base http://localhost:PORT`
- Tes API: buka `http://localhost:20128/api/providers` di browser — harus muncul JSON

### "Password salah (Wrong password)"
- Cek `akun.txt` — format harus `email|password`, tanpa spasi di sekitar `|`
- Coba login manual di google.com untuk memastikan akun tidak diblokir

### "Field password tidak muncul" / bot berhenti di Google
- Akun dengan **verifikasi 2 langkah (2FA)** tidak bisa diproses otomatis
- Google bisa meminta CAPTCHA — jalankan dengan `--headed`, naikkan delay
  (`--delay 10`), dan jangan proses terlalu banyak akun sekaligus

### "Kode OAuth tidak tertangkap"
- Jalankan dengan `--headed` untuk melihat di halaman mana bot berhenti
- Halaman Google bisa berubah — pesan error dari bot membantu debugging

### Gagal install / download Camoufox
- Cek koneksi internet
- Jalankan ulang `setup.bat`
- Atau manual: `.venv\Scripts\python -m camoufox fetch`

### Antivirus / Windows Defender memblokir
- Tambahkan folder ini ke exclusion Defender
  (bot menjalankan Firefox khusus yang terkadang terdeteksi salah)

---

## Keamanan

- **JANGAN** bagikan `akun.txt` kepada siapa pun (sudah di-ignore git)
- Password hanya dipakai untuk login Google, tidak dikirim ke server lain
- `akun.txt` otomatis kosong seiring akun sukses diproses
- Gunakan hanya pada 9Router milik sendiri
