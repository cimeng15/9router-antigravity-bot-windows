# Bot AntiGravity — Auto Add Account ke 9Router (Windows)

Bot otomatis untuk menambahkan akun Google (Antigravity) ke 9Router via API.
Berbasis **Python + DrissionPage + Google Chrome** (HEADED — selalu tampil
jendela browser) dan **API-driven** — tidak perlu klik UI dashboard dan
tidak butuh server callback.

> **REVISI 4:** browser diganti dari Camoufox → **Chrome**, karena Camoufox
> sering gagal install di Windows (dependency) dan headless-nya bermasalah.
> Sekarang bot **selalu headed** (jendela Chrome tampil), memakai **profile
> Chrome baru sementara** untuk tiap akun, dan **menghapusnya otomatis**
> setelah selesai — tidak ada cache/cookie nyangkut antar akun.

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
2. **Python 3.10+** (versi paling stabil: **3.10 / 3.11 / 3.12**)
   > ⚠️ Saat install, **centang "Add Python to PATH"** — ini WAJIB
3. **Google Chrome** terinstall (lokasi standar Windows)
4. **9Router** berjalan di komputer yang sama (`http://localhost:20128`)
   dengan opsi **login tidak diwajibkan** (require login disabled)
5. Koneksi internet (untuk login ke Google)

Tidak perlu install browser tambahan — bot memakai Chrome yang sudah ada.
Dependency Python hanya **satu**: DrissionPage (kecil, cepat terinstall).

---

## Setup

### Cara otomatis (direkomendasikan)

1. Copy folder ini ke komputer Windows (misal: `D:\9router-antigravity-windows\`)
2. **Klik dua kali `setup.bat`**

`setup.bat` akan otomatis:
- Mendeteksi Python (`py` atau `python`) + validasi versi 3.10+
- **Mencari Google Chrome** di lokasi standar Windows
- Membuat virtual environment di `.venv\`
- Menginstall **DrissionPage** (satu-satunya dependency, ukuran kecil)
- Verifikasi instalasi di akhir
- Mengecek apakah `akun.txt` sudah ada

Jika berhasil, di akhir muncul:

```
[OK] Bot siap dipakai!
```

> Catatan: tidak ada lagi download browser ±150 MB seperti versi Camoufox —
> setup sekarang cuma beberapa detik.

### Cara manual (jika setup.bat gagal)

Buka **Command Prompt** / **PowerShell** di folder ini, lalu jalankan satu per satu:

```bat
py -m venv .venv
.venv\Scripts\pip install --upgrade pip
.venv\Scripts\pip install DrissionPage
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

> Saat bot jalan, **jendela Chrome akan terbuka sendiri** — itu normal
> (bot selalu headed). Jangan ditutup; bot yang menutupnya otomatis.

Atau dari terminal (Command Prompt / PowerShell) di folder ini:

```bat
:: mode normal (default, direkomendasikan)
.venv\Scripts\python bot_api.py

:: mode cepat (internet bagus)
.venv\Scripts\python bot_api.py --fast

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
 [2/6] Membuka Chrome (headed, profile baru)...
 [3/6] Membuka halaman login Google...
 [4/6] Login Google: email@gmail.com
 [5/6] Menunggu konfirmasi Google & kode OAuth...
        >> Kode OAuth tertangkap dari URL!
 [6/6] Mendaftarkan akun ke 9Router (exchange)...
 [INFO] Menutup Chrome & menghapus profile sementara...

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

> **Penting:** saat Google selesai consent, tab akan menampilkan error
> *"This site can't be reached"* / *"Situs ini tidak dapat dijangkau"*
> untuk alamat `localhost:8080`. **Itu NORMAL dan memang disengaja** —
> bot hanya butuh membaca kode dari URL-nya, halamannya tidak perlu termuat.

---

## Opsi Command Line

| Opsi | Default | Keterangan |
|------|---------|------------|
| `--base` | `http://localhost:20128` | Base URL 9Router |
| `--file` | `akun.txt` | Path file akun |
| `--fast` | normal | Delay minimal (untuk internet cepat) |
| `--delay` | `3` | Jeda antar akun (detik) |
| `--port` | `8080` | Port callback loopback OAuth |

> Tidak ada opsi `--headed`/`--headless` — bot selalu headed.

Contoh kombinasi:

```bat
.venv\Scripts\python bot_api.py --fast --delay 10 --file daftar2.txt
```

Atau lewat `run.bat` (argumen diteruskan otomatis):

```bat
run.bat --fast --delay 5
```

---

## Cara Kerja Bot

1. `GET /api/oauth/antigravity/authorize` → minta URL login Google + state + codeVerifier ke 9Router
2. Chrome dibuka **headed** dengan **profile sementara baru** (folder kosong di `%TEMP%`)
3. Login Google: email → Next → password → Next
4. Halaman konfirmasi Google (bahasa Inggris/Indonesia) diklik otomatis —
   termasuk tombol "Login" di halaman "Pastikan Anda mendownload aplikasi ini dari Google"
5. Saat Google redirect ke `localhost:8080/callback?code=...`, halaman memang
   gagal dimuat — **kode dibaca langsung dari URL-nya**
6. `POST /api/oauth/antigravity/exchange` → akun terdaftar di 9Router
7. Chrome ditutup + **profile sementara dihapus** (tidak ada jejak akun)
8. Verifikasi via `GET /api/providers` → sukses = akun dihapus dari `akun.txt`

---

## Troubleshooting

### "Python tidak ditemukan"
Install Python dari [python.org](https://www.python.org/downloads/) dan
**centang "Add Python to PATH"** saat install, lalu jalankan ulang `setup.bat`.
Cek dengan: `py --version` di CMD.

### "Google Chrome tidak ditemukan"
Install Chrome dari [google.com/chrome](https://www.google.com/chrome/),
lalu jalankan ulang `setup.bat`. Chrome harus ada di lokasi standar Windows
(`Program Files\Google\Chrome`).

### "9Router tidak bisa dihubungi"
- Pastikan 9Router berjalan: buka `http://localhost:20128` di browser
- Kalau port-nya beda, tambahkan `--base http://localhost:PORT`
- Tes API: buka `http://localhost:20128/api/providers` di browser — harus muncul JSON

### "Password salah (Wrong password)"
- Cek `akun.txt` — format harus `email|password`, tanpa spasi di sekitar `|`
- Coba login manual di google.com untuk memastikan akun tidak diblokir

### "Field password tidak muncul" / bot berhenti di Google
- Akun dengan **verifikasi 2 langkah (2FA)** tidak bisa diproses otomatis
- Google bisa meminta CAPTCHA — naikkan delay (`--delay 10`) dan jangan
  proses terlalu banyak akun sekaligus. Karena bot sekarang selalu headed,
  Anda bisa langsung melihat kalau CAPTCHA muncul

### "Kode OAuth tidak tertangkap"
- Lihat jendela Chrome yang terbuka — di halaman mana bot berhenti
- Halaman Google bisa berubah — pesan error dari bot membantu debugging

### Chrome jalan lambat / jendela putih
- Chrome butuh resource saat headed. Tutup aplikasi lain yang berat
- Kalau Chrome macet total: tutup semua Chrome, hapus folder `.venv`,
  lalu jalankan ulang `run.bat` (profil nyangkut dibersihkan otomatis saat start)

### Gagal install DrissionPage
- Jarang terjadi (package kecil, pure-Python). Cek koneksi internet,
  lalu jalankan ulang `setup.bat`
- Kalau antivirus memblokir pip: tambahkan folder ini + folder Python
  ke exclusion antivirus

---

## Keamanan

- **JANGAN** bagikan `akun.txt` kepada siapa pun (sudah di-ignore git)
- Password hanya dipakai untuk login Google, tidak dikirim ke server lain
- **Profile Chrome sementara dihapus otomatis** setelah tiap akun —
  sesi login Google tidak tertinggal di komputer
- `akun.txt` otomatis kosong seiring akun sukses diproses
- Gunakan hanya pada 9Router milik sendiri
