#!/usr/bin/env python3
"""
Bot AntiGravity - Auto Add Account ke 9Router (WINDOWS EDITION: CHROME)

REVISI 4 (Windows): ganti Camoufox -> Chrome, selalu HEADED.
  Alasan: Camoufox di Windows sering error saat install (dependency) dan
  headless-nya bermasalah di Windows. Chrome lebih stabil:
    - Selalu dibuka dengan jendela (HEADed) — TIDAK ada mode headless
    - Tiap akun memakai PROFILE CHROME BARU (folder sementara)
    - Profile sementara DIHAPUS otomatis setelah akun selesai
      (tidak ada cache/cookie nyangkut antar akun)

Alur tetap API-driven (REVISI 3) — tidak butuh server callback:
  1. GET  /api/oauth/antigravity/authorize  -> authUrl + state + codeVerifier
  2. Chrome login Google; saat Google redirect ke
     http://localhost:8080/callback?code=..., KODE DIBACA DARI URL
     (halaman akan gagal load - itu NORMAL, kodenya sudah tertangkap)
  3. POST /api/oauth/antigravity/exchange   -> akun terdaftar di 9Router
  4. GET  /api/providers                    -> verifikasi akun masuk

Cara pakai:
  python bot_api.py                     # default (http://localhost:20128)
  python bot_api.py --fast              # delay minimal
  python bot_api.py --delay 10          # jeda antar akun
  python bot_api.py --file akun.txt

SYARAT: Google Chrome terinstall di Windows.
Format akun.txt: email|password (satu baris per akun)
"""

# ============================================================
# AUTO-INSTALLER
# ============================================================
import os
import sys
import json
import time
import random
import shutil
import tempfile
import argparse
import subprocess
import urllib.request
import urllib.parse
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _ensure_deps():
    """Pastikan DrissionPage terinstall (bikin venv kalau perlu)."""
    try:
        import DrissionPage  # noqa: F401
        return
    except ImportError:
        pass

    print("=" * 50)
    print(" DrissionPage belum terinstall! Menginstall otomatis...")
    print("=" * 50)
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "DrissionPage"],
        )
        print("\n DrissionPage berhasil diinstall!\n")
    except subprocess.CalledProcessError:
        print("\n [ERROR] Gagal install DrissionPage.")
        print("         Jalankan manual: pip install DrissionPage")
        sys.exit(1)


_ensure_deps()

from DrissionPage import ChromiumPage, ChromiumOptions  # noqa: E402

# ============================================================
# KONFIGURASI
# ============================================================
BASE_URL = "http://localhost:20128"
PROVIDER = "antigravity"
REDIRECT_PORT = 8080          # port callback loopback (default 9Router)
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"
AKUN_FILE = os.path.join(SCRIPT_DIR, "akun.txt")
DELAY_ANTAR_AKUN = 3

# Timeout total menunggu kode dari redirect Google (detik)
CODE_WAIT_TIMEOUT = 150

# ============================================================
# TIMING PROFILES (detik)
# ============================================================
TIMING = {
    "fast": {
        "google_initial":    1,
        "after_email_next":  2,
        "password_timeout":  10,
        "after_pw_next":     2,
        "step_loop_wait":    1,
        "no_btn_wait":       2,
        "after_success":     1,
    },
    "normal": {
        "google_initial":    3,
        "after_email_next":  4,
        "password_timeout":  20,
        "after_pw_next":     4,
        "step_loop_wait":    2,
        "no_btn_wait":       4,
        "after_success":     2,
    },
}


# ============================================================
# API 9ROUTER
# ============================================================
def api_get(path, params=None, base=None, timeout=30):
    base = base or BASE_URL
    url = base.rstrip("/") + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def api_post(path, payload, base=None, timeout=60):
    base = base or BASE_URL
    url = base.rstrip("/") + path
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json",
                 "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8"))
            return body, f"HTTP {e.code}: {body.get('error', body)}"
        except Exception:
            return {}, f"HTTP {e.code}"
    except Exception as e:
        return {}, str(e)


def start_oauth(base):
    """Minta 9Router bikin state+verifier & URL login Google."""
    data = api_get(f"/api/oauth/{PROVIDER}/authorize",
                   params={"redirect_uri": REDIRECT_URI}, base=base)
    for key in ("authUrl", "state", "codeVerifier"):
        if key not in data:
            raise Exception(f"Response /authorize tidak valid: {list(data.keys())}")
    return data


def exchange_code(code, state, code_verifier, base):
    """Tukar kode OAuth jadi akun terdaftar di 9Router."""
    resp, err = api_post(f"/api/oauth/{PROVIDER}/exchange", {
        "code": code,
        "redirectUri": REDIRECT_URI,
        "codeVerifier": code_verifier,
        "state": state,
    }, base=base)
    if err:
        raise Exception(f"Exchange gagal: {err}")
    return resp


def get_antigravity_emails(base):
    """Ambil daftar email akun antigravity yang sudah terdaftar."""
    try:
        data = api_get("/api/providers", base=base)
        conns = data.get("connections", data if isinstance(data, list) else [])
        return {c.get("email", "").lower() for c in conns
                if c.get("provider", c.get("alias", "")) in (PROVIDER, "ag")
                and c.get("email")}
    except Exception as e:
        print(f" [WARN]   Gagal membaca /api/providers: {e}")
        return set()


# ============================================================
# AKUN
# ============================================================
def read_accounts(path):
    if not os.path.exists(path):
        print(f" [ERROR] File '{path}' tidak ditemukan!")
        return []
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    accounts = []
    for line in lines:
        if "|" not in line:
            continue
        email, password = [p.strip() for p in line.split("|", 1)]
        if email and password:
            accounts.append({"email": email, "password": password, "raw": line})
    return accounts


def remove_account(path, raw_line):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    remaining = [l for l in lines if l.strip() != raw_line]
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(remaining)


# ============================================================
# HELPER: OPERASI DI HALAMAN GOOGLE
# ============================================================
def find_and_click(page_or_tab, locators, timeout=5, desc="element"):
    """Cari elemen dari list locator DrissionPage, klik yang pertama ketemu."""
    for locator in locators:
        try:
            ele = page_or_tab.ele(locator, timeout=timeout)
            if ele:
                ele.click()
                return True
        except Exception:
            continue
    return False


def force_input(page_or_tab, locator, text, timeout=15, desc="field"):
    """Input teks ke field dengan beberapa strategi fallback."""
    ele = page_or_tab.ele(locator, timeout=timeout)
    if ele is None:
        raise Exception(f"Elemen {desc} tidak ditemukan: {locator}")

    # Strategi 1: .input() standar
    try:
        ele.clear()
        ele.input(text)
        time.sleep(0.5)
        if text in (ele.attr("value") or ele.attr("value") or ""):
            return ele
    except Exception:
        pass

    # Strategi 2: input via JS + event (React/form Google kadang butuh ini)
    try:
        ele.click()
        time.sleep(0.3)
        ele.run_js("""
            this.focus();
            this.value = arguments[0];
            this.dispatchEvent(new Event('input', {bubbles: true}));
            this.dispatchEvent(new Event('change', {bubbles: true}));
        """, text)
        time.sleep(0.5)
        if text in (ele.attr("value") or ""):
            return ele
    except Exception:
        pass

    # Strategi 3: ketik via actions (paling mirip manusia)
    try:
        ele.click()
        time.sleep(0.3)
        page_or_tab.actions.type(text)
        time.sleep(0.5)
        if text in (ele.attr("value") or ""):
            return ele
    except Exception:
        pass

    raise Exception(f"Gagal input teks ke {desc}")


# REVISI: Google bisa menampilkan halaman consent dalam bahasa Indonesia
# ATAU Inggris, tergantung lokasi IP. Contoh nyata (IP Indonesia):
#   "Pastikan Anda mendownload aplikasi ini dari Google" -> tombol "Login"
# Kata kunci diurutkan dari yang PALING AMAN — jangan pernah klik
# "Batal" / "Cancel" / "No" / "Sign out".
CONSENT_KEYWORDS = [
    "I Understand", "I understand", "Saya memahami",
    "Allow", "Izinkan",
    "Continue", "Lanjutkan",
    "Confirm", "Konfirmasi",
    "I agree", "Saya setuju",
    "Enter the password again",
    "Login", "Sign in", "Masuk",
    "Next", "Berikutnya",
]

_CONSENT_JS = """
([texts, exact]) => {
    const norm = s => (s || '').toLowerCase().replace(/\\s+/g, ' ').trim();
    const els = [...document.querySelectorAll('button, a, input[type="submit"]')];
    for (const t of texts) {
        const target = norm(t);
        const el = els.find(e => {
            const txt = norm(e.innerText || e.value);
            return exact ? txt === target : txt.includes(target);
        });
        if (el) { el.click(); return true; }
    }
    return false;
}
"""


def js_click_any(tab, texts, exact=False):
    """Klik elemen (button/a) yang teksnya cocok, via JS. Return True jika sukses."""
    try:
        return tab.run_js(_CONSENT_JS, texts, exact)
    except Exception:
        return False


def js_click_consent(tab):
    """Klik tombol consent di halaman Google — exact-match dulu (aman
    untuk tombol pendek seperti 'Login'), baru partial-match frasa panjang.
    Terakhir: exact-match Login/Masuk/Sign in (khusus halaman nativeapp)."""
    if js_click_any(tab, CONSENT_KEYWORDS, exact=True):
        return True
    long_phrases = [
        "I Understand", "I understand", "Saya memahami",
        "Lanjutkan", "Continue", "Izinkan", "Allow",
        "Konfirmasi", "Confirm", "Saya setuju", "I agree",
        "Enter the password again", "Berikutnya", "Next",
    ]
    if js_click_any(tab, long_phrases, exact=False):
        return True
    return js_click_any(tab, ["Login", "Masuk", "Sign in"], exact=True)


_LOGIN_ERR_JS = """
() => {
    const t = document.body.innerText.toLowerCase();
    if (t.includes('wrong password') || t.includes('sandi salah')
        || t.includes('kata sandi salah'))
        return 'Password salah (Google: Wrong password)';
    if (t.includes("couldn't find your google account")
        || t.includes('tidak menemukan akun google')
        || t.includes('tidak dapat menemukan akun google'))
        return 'Email tidak ditemukan (Google: Account not found)';
    return null;
}
"""


def detect_login_error(tab):
    """Deteksi halaman error login (EN + ID). Return pesan atau None."""
    try:
        return tab.run_js(_LOGIN_ERR_JS)
    except Exception:
        return None


def parse_callback_code(url):
    """Ambil kode OAuth dari URL callback. Return (code, state) atau None."""
    if f"localhost:{REDIRECT_PORT}/callback" not in url:
        return None
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    if "code" in q:
        return q["code"][0], (q.get("state") or [""])[0]
    if "error" in q:
        return "__error__", (q.get("error_description") or q["error"])[0]
    return None


# ============================================================
# CHROME: PROFILE SEMENTARA
# ============================================================
def launch_chrome():
    """Buka Chrome HEADED dengan profile sementara baru.
    Return (page, profile_dir)."""
    profile_dir = tempfile.mkdtemp(prefix="ag_chrome_")

    co = ChromiumOptions()
    # PENTING: JANGAN pakai auto_port() — di beberapa versi DrissionPage
    # menghasilkan address tanpa port dan crash saat connect.
    co.set_local_port(random.randint(19200, 29200))
    co.set_user_data_path(profile_dir)  # profile baru, terisolasi
    co.set_argument("--start-maximized")
    co.set_argument("--disable-blink-features=AutomationControlled")
    co.set_argument("--no-first-run")
    co.set_argument("--no-default-browser-check")
    co.set_argument("--disable-dev-shm-usage")
    # HEADED SELALU — tidak ada headless di versi Windows ini

    page = ChromiumPage(co)
    return page, profile_dir


def close_chrome(page, profile_dir):
    """Tutup Chrome dan hapus profile sementaranya."""
    try:
        page.quit()
    except Exception:
        pass
    # Windows kadang masih mengunci folder beberapa saat setelah quit —
    # coba hapus beberapa kali, diamkan kalau gagal.
    for _ in range(5):
        try:
            if os.path.exists(profile_dir):
                shutil.rmtree(profile_dir, ignore_errors=True)
            if not os.path.exists(profile_dir):
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        print(" [INFO]   Profil sementara belum bisa dihapus (akan terhapus"
              " saat Windows restart folder temp)")


# ============================================================
# FUNGSI UTAMA: PROSES SATU AKUN
# ============================================================
def process_account(account, index, total, t, base):
    email = account["email"]
    password = account["password"]

    print(f"\n{'=' * 55}")
    print(f" Akun {index + 1}/{total}: {email}")
    print(f"{'=' * 55}")

    # --- [1/6] Minta sesi OAuth ke 9Router ---
    print(" [1/6] Membuat sesi OAuth via API 9Router...")
    oauth = start_oauth(base)
    state, verifier = oauth["state"], oauth["codeVerifier"]
    print(f"        redirect_uri : {oauth.get('redirectUri', REDIRECT_URI)}")

    # --- [2/6] Buka Chrome dengan profile sementara baru ---
    print(" [2/6] Membuka Chrome (headed, profile baru)...")
    page = None
    profile_dir = None
    try:
        page, profile_dir = launch_chrome()

        # --- [3/6] Buka halaman login Google ---
        print(" [3/6] Membuka halaman login Google...")
        page.get(oauth["authUrl"])
        time.sleep(t["google_initial"])

        # --- [4/6] Login Google ---
        print(f" [4/6] Login Google: {email}")
        force_input(page, "#identifierId", email,
                    timeout=t["password_timeout"], desc="email field")
        time.sleep(0.5)
        if not find_and_click(page, [
            "#identifierNext",
            "tag:button@@text():Next",
            "tag:button@@text():Berikutnya",
        ], timeout=5, desc="Next (email)"):
            raise Exception("Tombol Next (email) tidak ditemukan")
        time.sleep(t["after_email_next"])

        pw_done = False
        for loc in ("@type=password", "tag:input@@type=password", "@name=Passwd"):
            try:
                force_input(page, loc, password,
                            timeout=t["password_timeout"], desc="password field")
                pw_done = True
                break
            except Exception:
                continue
        if not pw_done:
            err = detect_login_error(page)
            if err:
                raise Exception(err)
            raise Exception(
                f"Field password tidak muncul (mungkin email salah / 2FA. "
                f"URL: {(page.url or '')[:80]})")
        time.sleep(0.5)
        if not find_and_click(page, [
            "#passwordNext",
            "tag:button@@text():Next",
            "tag:button@@text():Berikutnya",
        ], timeout=5, desc="Next (password)"):
            raise Exception("Tombol Next (password) tidak ditemukan")
        time.sleep(t["after_pw_next"])

        # --- [5/6] Handle konfirmasi Google sampai kode tertangkap ---
        # Saat Google redirect ke localhost:8080/callback, halaman GAGAL
        # dimuat — itu NORMAL. Kode cukup dibaca dari URL-nya.
        print(" [5/6] Menunggu konfirmasi Google & kode OAuth...")
        print("        (halaman error 'site can't be reached' setelah ini"
              " = NORMAL, bukan gagal)")
        deadline = time.time() + CODE_WAIT_TIMEOUT
        step = 0
        code = err_msg = cb_state = None

        while time.time() < deadline:
            step += 1
            time.sleep(t["step_loop_wait"])

            try:
                current_url = page.url or ""
            except Exception:
                break  # tab ditutup

            # Kode tertangkap dari URL callback?
            parsed = parse_callback_code(current_url)
            if parsed:
                if parsed[0] == "__error__":
                    err_msg = parsed[1]
                    print(f"        >> Google mengembalikan error: {err_msg}")
                else:
                    code, cb_state = parsed
                    print("        >> Kode OAuth tertangkap dari URL!")
                break

            err = detect_login_error(page)
            if err:
                raise Exception(err)

            if step % 5 == 1:
                print(f"        [Step {step}] URL: {current_url[:80]}")

            # Halaman Workspace TOS: "Welcome to your new account"
            if ("workspacetermsofservice" in current_url
                    or "speedbump" in current_url):
                print("        >> Halaman 'Welcome to your new account' terdeteksi")
                if js_click_consent(page):
                    print("        >> 'I understand' diklik!")
                    time.sleep(t["after_pw_next"])
                continue

            # Consent / nativeapp / Allow / Continue / Login (ID+EN)
            if js_click_consent(page):
                print("        >> Tombol consent diklik!")
                time.sleep(t["step_loop_wait"])
                continue

            # Centang checkbox consent yang belum dicentang (kalau ada)
            try:
                page.run_js("""
                    document.querySelectorAll('input[type="checkbox"]:not(:checked)')
                        .forEach(cb => cb.click());
                """)
            except Exception:
                pass

            time.sleep(t["no_btn_wait"])

        if err_msg:
            raise Exception(f"Google menolak consent: {err_msg}")
        if not code:
            raise Exception(
                f"Kode OAuth tidak tertangkap dalam {CODE_WAIT_TIMEOUT} detik "
                f"(kemungkinan stuck di halaman: {(page.url or '')[:80]})")

        if cb_state and cb_state != state:
            raise Exception("State OAuth tidak cocok — kemungkinan sesi kedaluwarsa")

        # --- [6/6] Exchange kode -> akun terdaftar di 9Router ---
        print(" [6/6] Mendaftarkan akun ke 9Router (exchange)...")
        exchange_code(code, state, verifier, base)

    finally:
        # Selalu tutup Chrome + hapus profile sementara, sukses maupun gagal
        if page is not None:
            print(" [INFO] Menutup Chrome & menghapus profile sementara...")
            close_chrome(page, profile_dir)

    # --- Verifikasi akun benar-benar masuk ---
    time.sleep(t["after_success"])
    emails = get_antigravity_emails(base)
    if email.lower() in emails:
        print(f"\n [SUKSES] Akun {index + 1}/{total}: {email}")
        print(" [INFO]   Akun terverifikasi ada di /api/providers")
        remove_account(AKUN_FILE, account["raw"])
        print(" [INFO]   Akun dihapus dari akun.txt")
    else:
        print(f"\n [SUKSES?] Akun {index + 1}/{total}: {email}")
        print(" [WARN]   Exchange sukses tapi email belum terlihat di "
              "/api/providers (cek manual di dashboard)")


# ============================================================
# MAIN
# ============================================================
def main():
    global BASE_URL, REDIRECT_PORT, REDIRECT_URI, AKUN_FILE

    parser = argparse.ArgumentParser(
        description="Bot AntiGravity - Auto Add Account ke 9Router "
                    "(Windows / Chrome / headed)"
    )
    parser.add_argument("--fast", action="store_true",
                        help="Mode cepat (internet bagus, delay minimal)")
    parser.add_argument("--delay", type=int, default=DELAY_ANTAR_AKUN,
                        help=f"Delay antar akun (default: {DELAY_ANTAR_AKUN}s)")
    parser.add_argument("--file", type=str, default=None,
                        help="Path file akun (default: akun.txt)")
    parser.add_argument("--base", type=str, default=None,
                        help=f"Base URL 9Router (default: {BASE_URL})")
    parser.add_argument("--port", type=int, default=None,
                        help=f"Port callback loopback (default: {REDIRECT_PORT})")
    args = parser.parse_args()

    if args.base:
        BASE_URL = args.base.rstrip("/")
    if args.port:
        REDIRECT_PORT = args.port
        REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"
    if args.file:
        AKUN_FILE = args.file

    speed_mode = "fast" if args.fast else "normal"
    t = TIMING[speed_mode]

    print_banner()

    # Bersihkan profil sementara sisa run sebelumnya (kalau ada)
    tmp = tempfile.gettempdir()
    for old in os.listdir(tmp):
        if old.startswith("ag_chrome_"):
            shutil.rmtree(os.path.join(tmp, old), ignore_errors=True)

    # Sanity check: 9Router harus bisa dihubungi
    try:
        api_get("/api/providers", base=BASE_URL, timeout=15)
    except Exception as e:
        print(f" [ERROR] 9Router tidak bisa dihubungi di {BASE_URL}: {e}")
        print("         Pastikan 9Router berjalan (buka "
              "http://localhost:20128 di browser)")
        sys.exit(1)

    accounts = read_accounts(AKUN_FILE)
    if not accounts:
        print("\n [INFO] Tidak ada akun yang bisa diproses.")
        print("        Format akun.txt: email|password (satu baris per akun)")
        sys.exit(1)

    before = get_antigravity_emails(BASE_URL)
    print(f" Target      : {BASE_URL}")
    print(f" Browser     : Chrome (HEADED — selalu tampil jendela)")
    print(f" Speed mode  : {speed_mode.upper()}")
    print(f" Delay antar : {args.delay} detik")
    print(f" File akun   : {AKUN_FILE}")
    print(f" Akun terdaftar sudah: {len(before)}")
    print(f" Total akun baru   : {len(accounts)}\n")

    sukses, gagal = 0, 0
    for i, account in enumerate(accounts):
        try:
            process_account(account, i, len(accounts), t=t, base=BASE_URL)
            remaining = read_accounts(AKUN_FILE)
            if account["raw"] not in [a["raw"] for a in remaining]:
                sukses += 1
            else:
                gagal += 1
        except Exception as e:
            print(f"\n [GAGAL] Akun {i + 1}/{len(accounts)}: {account['email']}")
            print(f"          Error: {e}")
            gagal += 1

        if i < len(accounts) - 1:
            print(f"\n [DELAY] Menunggu {args.delay} detik...")
            time.sleep(args.delay)

    print(f"\n{'=' * 55}")
    print(" SELESAI!")
    print(f" Total  : {len(accounts)} akun")
    print(f" Sukses : {sukses} akun")
    print(f" Gagal  : {gagal} akun")
    print(f"{'=' * 55}")


def print_banner():
    banner = r"""
     _   __                __
    / | / /__  _______  __/ /_____  _________ ____
   /  |/ / _ \/ ___/ / / / __/ __ \/ ___/ __ `/ _ \
  / /|  /  __/ /  / /_/ / /_/ /_/ / /  / /_/ /  __/
 /_/ |_/\___/_/   \__,_/\__/\____/_/   \__,_/\___/
    Bot Auto Add Account - Chrome HEADED (Windows)
    """
    print(banner)
    print("=" * 55)


if __name__ == "__main__":
    main()
