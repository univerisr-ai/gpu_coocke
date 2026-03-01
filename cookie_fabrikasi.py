#!/usr/bin/env python3
"""
Sahibinden.com Cookie Fabrikası
undetected-chromedriver + Xvfb
"""

import undetected_chromedriver as uc
import time
import json
import sys
import random
from datetime import datetime, timezone

# ── Ayarlar ───────────────────────────────────────────────
MAIN_URL    = "https://www.sahibinden.com"
TARGET_URL  = "https://www.sahibinden.com/ekran-karti-masaustu"
MAX_DENEME  = 3

KRITIK_COOKIELER = ["st", "vid", "_px3", "_pxvid", "_pxhd", "cdid"]


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def insan_bekle(az=2.0, cok=5.0):
    time.sleep(random.uniform(az, cok))


# ── Tarayıcı oluştur ─────────────────────────────────────
def tarayici_olustur():
    opts = uc.ChromeOptions()

    # CI ortamı için zorunlu
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")

    # Gerçekçi pencere
    opts.add_argument("--window-size=1920,1080")

    # Türkçe
    opts.add_argument("--lang=tr-TR,tr")
    opts.add_argument("--accept-lang=tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7")

    # Bildirim ve şifre popup kapatma
    opts.add_experimental_option("prefs", {
        "intl.accept_languages": "tr-TR,tr,en-US,en",
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.default_content_setting_values.notifications": 2,
    })

    driver = uc.Chrome(
        options=opts,
        headless=False,       # ZORUNLU — headless tespit edilir
        use_subprocess=True,  # CI'da daha stabil
    )

    # Viewport
    driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
        "width": 1920,
        "height": 1080,
        "deviceScaleFactor": 1,
        "mobile": False,
    })

    # Türkiye timezone
    driver.execute_cdp_cmd(
        "Emulation.setTimezoneOverride",
        {"timezoneId": "Europe/Istanbul"}
    )

    return driver


# ── Cookie topla ──────────────────────────────────────────
def cookie_topla(driver) -> tuple[dict, bool]:

    # ① Ana sayfa — PX sensörünün yüklenmesini bekle
    log("① Ana sayfa yükleniyor...")
    driver.get(MAIN_URL)
    insan_bekle(6, 10)

    html = driver.page_source
    log(f"   Ana sayfa HTML: {len(html):,} karakter")

    # Challenge/CAPTCHA varsa bekle
    if len(html) < 15_000:
        log("   ⏳ Challenge tespit edildi, 25s bekleniyor...")
        time.sleep(25)
        html = driver.page_source
        log(f"   Challenge sonrası HTML: {len(html):,} karakter")

    # İnsan gibi scroll
    driver.execute_script("window.scrollTo({top: 400, behavior: 'smooth'})")
    insan_bekle(2, 4)

    # ② Hedef sayfaya git
    log("② Hedef sayfa yükleniyor...")
    driver.get(TARGET_URL)
    insan_bekle(8, 13)

    # Sayfada gezin
    for y in [300, 700, 1100]:
        driver.execute_script(
            f"window.scrollTo({{top: {y}, behavior: 'smooth'}})"
        )
        insan_bekle(1, 2.5)

    # ③ Sonuçları topla
    baslik   = driver.title
    html     = driver.page_source
    html_boy = len(html)
    cookieler = driver.get_cookies()

    log(f"\n③ Sonuçlar:")
    log(f"   Sayfa başlığı : {baslik or '(boş)'}")
    log(f"   HTML boyutu   : {html_boy:,} karakter")
    log(f"   Cookie sayısı : {len(cookieler)}")

    # Cookie dict
    cookie_dict = {}
    log("\n   ── Cookie Listesi ──")
    for c in sorted(cookieler, key=lambda x: x["name"]):
        cookie_dict[c["name"]] = c["value"]
        yildiz = "★" if c["name"] in KRITIK_COOKIELER else " "
        deger = c["value"][:60] + "…" if len(c["value"]) > 60 else c["value"]
        log(f"   {yildiz} {c['name']}: {deger}")

    # Kritik cookie kontrolü
    bulunan = [c for c in KRITIK_COOKIELER if c in cookie_dict]
    eksik   = [c for c in KRITIK_COOKIELER if c not in cookie_dict]
    log(f"\n   Kritik: {len(bulunan)}/{len(KRITIK_COOKIELER)}")
    if bulunan:
        log(f"   ✅ Bulunan : {bulunan}")
    if eksik:
        log(f"   ❌ Eksik   : {eksik}")

    # İlan kontrolü
    ilan_sayisi = html.count("searchResultsItem")
    log(f"   İlan sayısı: ~{ilan_sayisi}")

    # Başarı kriteri
    basarili = html_boy > 50_000 and len(cookieler) >= 5
    return cookie_dict, basarili


# ── HTML'i de kaydet (debug için) ────────────────────────
def html_kaydet(driver):
    try:
        html = driver.page_source
        with open("sayfa.html", "w", encoding="utf-8") as f:
            f.write(html)
        log(f"sayfa.html kaydedildi ({len(html):,} karakter)")
    except Exception:
        pass


# ── Ana akış ──────────────────────────────────────────────
def main():
    son_cookieler = {}
    basarili = False

    for deneme in range(1, MAX_DENEME + 1):
        log(f"\n{'━' * 55}")
        log(f"  DENEME {deneme}/{MAX_DENEME}")
        log(f"{'━' * 55}")

        driver = None
        try:
            driver = tarayici_olustur()
            son_cookieler, basarili = cookie_topla(driver)
            html_kaydet(driver)

            if basarili:
                log("\n🎉 Cookie toplama BAŞARILI!")
                break

            log("⚠️  Yetersiz sonuç, tekrar denenecek...")

        except Exception as e:
            log(f"💥 Hata: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

        if deneme < MAX_DENEME:
            bekleme = deneme * 15
            log(f"⏳ {bekleme}s bekleniyor...")
            time.sleep(bekleme)

    # ── Her durumda dosyaya kaydet ────────────────────────
    sonuc = {
        "cookies":    son_cookieler,
        "toplam":     len(son_cookieler),
        "basarili":   basarili,
        "tarih":      datetime.now(timezone.utc).isoformat(),
        "kritik_bulunan": [
            c for c in KRITIK_COOKIELER if c in son_cookieler
        ],
        "kritik_eksik": [
            c for c in KRITIK_COOKIELER if c not in son_cookieler
        ],
    }

    with open("cookies.json", "w", encoding="utf-8") as f:
        json.dump(sonuc, f, indent=2, ensure_ascii=False)

    log(f"\ncookies.json kaydedildi ({len(son_cookieler)} cookie)")

    # ── Özet ──────────────────────────────────────────────
    log(f"\n{'═' * 55}")
    log(f"  ÖZET")
    log(f"{'═' * 55}")
    log(f"  Durum     : {'✅ BAŞARILI' if basarili else '❌ BAŞARISIZ'}")
    log(f"  Cookie    : {len(son_cookieler)}")
    log(f"  Kritik    : {len(sonuc['kritik_bulunan'])}/{len(KRITIK_COOKIELER)}")
    log(f"{'═' * 55}")

    if not basarili:
        sys.exit(1)


if __name__ == "__main__":
    main()
