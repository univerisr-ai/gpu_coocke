#!/usr/bin/env python3
"""
Sahibinden.com Cookie Fabrikası
Her adımda dosya yazarak artifact'ın boş kalmasını önler
"""

import time
import json
import sys
import os
import random
import subprocess
from datetime import datetime, timezone

# ── Durum dosyası — her adımda güncellenir ────────────────
DURUM_DOSYASI = "durum.json"
COOKIE_DOSYASI = "cookies.json"
HTML_DOSYASI = "sayfa.html"
HATA_DOSYASI = "hata.txt"

MAIN_URL = "https://www.sahibinden.com"
TARGET_URL = "https://www.sahibinden.com/ekran-karti-masaustu"
MAX_DENEME = 3
KRITIK_COOKIELER = ["st", "vid", "_px3", "_pxvid", "_pxhd", "cdid"]


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def durum_kaydet(adim: str, detay: dict = None):
    """Her adımda durum dosyası yaz — artifact hiç boş kalmaz"""
    veri = {
        "adim": adim,
        "zaman": datetime.now(timezone.utc).isoformat(),
        "detay": detay or {},
    }
    try:
        # Önceki durumları oku
        durumlar = []
        if os.path.exists(DURUM_DOSYASI):
            with open(DURUM_DOSYASI, "r") as f:
                eski = json.load(f)
                if isinstance(eski, list):
                    durumlar = eski
        durumlar.append(veri)
        with open(DURUM_DOSYASI, "w") as f:
            json.dump(durumlar, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Durum kaydetme hatası: {e}", flush=True)

    log(f"📌 {adim}")


def hata_kaydet(hata_mesaji: str):
    """Hata olursa dosyaya yaz"""
    with open(HATA_DOSYASI, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}]\n{hata_mesaji}\n{'='*60}\n")


def insan_bekle(az=2.0, cok=5.0):
    time.sleep(random.uniform(az, cok))


# ── Ortam kontrolleri ─────────────────────────────────────
def ortam_kontrol():
    durum_kaydet("ortam_kontrol_basladi")

    kontroller = {}

    # Chrome var mı?
    try:
        sonuc = subprocess.run(
            ["google-chrome", "--version"],
            capture_output=True, text=True, timeout=10
        )
        kontroller["chrome_versiyon"] = sonuc.stdout.strip()
        log(f"   Chrome: {sonuc.stdout.strip()}")
    except Exception as e:
        kontroller["chrome_hata"] = str(e)
        log(f"   ❌ Chrome bulunamadı: {e}")

    # chromedriver var mı kontrol etmeye gerek yok, uc kendisi halleder

    # Xvfb kontrolü
    try:
        sonuc = subprocess.run(
            ["xdpyinfo"],
            capture_output=True, text=True, timeout=5,
            env={**os.environ, "DISPLAY": os.environ.get("DISPLAY", ":99")}
        )
        kontroller["xvfb"] = "çalışıyor" if sonuc.returncode == 0 else "hata"
        log(f"   Xvfb: {kontroller['xvfb']}")
    except Exception as e:
        kontroller["xvfb"] = f"kontrol edilemedi: {e}"
        log(f"   Xvfb: {kontroller['xvfb']}")

    # DISPLAY
    kontroller["DISPLAY"] = os.environ.get("DISPLAY", "YOK")
    log(f"   DISPLAY: {kontroller['DISPLAY']}")

    # Python paketleri
    try:
        import undetected_chromedriver as uc_test
        kontroller["uc_versiyon"] = getattr(uc_test, "__version__", "?")
        log(f"   undetected-chromedriver: {kontroller['uc_versiyon']}")
    except ImportError as e:
        kontroller["uc_hata"] = str(e)
        log(f"   ❌ undetected-chromedriver import hatası: {e}")

    try:
        import selenium
        kontroller["selenium_versiyon"] = selenium.__version__
        log(f"   selenium: {kontroller['selenium_versiyon']}")
    except ImportError as e:
        kontroller["selenium_hata"] = str(e)

    durum_kaydet("ortam_kontrol_bitti", kontroller)
    return kontroller


# ── Tarayıcı oluştur ─────────────────────────────────────
def tarayici_olustur():
    durum_kaydet("tarayici_olusturuluyor")

    import undetected_chromedriver as uc

    opts = uc.ChromeOptions()

    # CI zorunlu
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    opts.add_argument("--disable-extensions")

    # Gerçekçi pencere
    opts.add_argument("--window-size=1920,1080")

    # Türkçe
    opts.add_argument("--lang=tr-TR,tr")

    opts.add_experimental_option("prefs", {
        "intl.accept_languages": "tr-TR,tr,en-US,en",
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.default_content_setting_values.notifications": 2,
    })

    durum_kaydet("chrome_baslatiliyor")

    driver = uc.Chrome(
        options=opts,
        headless=False,
        use_subprocess=True,
        version_main=None,  # Otomatik algıla
    )

    durum_kaydet("chrome_baslatildi")

    # Viewport
    try:
        driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
            "width": 1920,
            "height": 1080,
            "deviceScaleFactor": 1,
            "mobile": False,
        })
    except Exception:
        pass

    # Timezone
    try:
        driver.execute_cdp_cmd(
            "Emulation.setTimezoneOverride",
            {"timezoneId": "Europe/Istanbul"}
        )
    except Exception:
        pass

    durum_kaydet("tarayici_hazir")
    return driver


# ── Cookie topla ──────────────────────────────────────────
def cookie_topla(driver) -> tuple[dict, bool]:

    # ① Ana sayfa
    durum_kaydet("ana_sayfa_yukleniyor")
    driver.get(MAIN_URL)
    insan_bekle(6, 10)

    html = driver.page_source
    durum_kaydet("ana_sayfa_yuklendi", {
        "html_boyut": len(html),
        "baslik": driver.title,
        "url": driver.current_url,
    })

    # HTML kaydet (debug)
    with open("ana_sayfa.html", "w", encoding="utf-8") as f:
        f.write(html)

    # Challenge kontrolü
    if len(html) < 15_000:
        durum_kaydet("challenge_tespit_edildi", {"html_boyut": len(html)})
        log("   ⏳ Challenge tespit edildi, 25s bekleniyor...")
        time.sleep(25)
        html = driver.page_source
        durum_kaydet("challenge_sonrasi", {"html_boyut": len(html)})

    # Scroll
    driver.execute_script("window.scrollTo({top: 400, behavior: 'smooth'})")
    insan_bekle(2, 4)

    # ② Hedef sayfa
    durum_kaydet("hedef_sayfa_yukleniyor")
    driver.get(TARGET_URL)
    insan_bekle(8, 13)

    # Scroll
    for y in [300, 700, 1100]:
        driver.execute_script(
            f"window.scrollTo({{top: {y}, behavior: 'smooth'}})"
        )
        insan_bekle(1, 2.5)

    # ③ Sonuçları topla
    baslik = driver.title
    html = driver.page_source
    html_boy = len(html)
    cookieler = driver.get_cookies()

    # Hedef sayfa HTML kaydet
    with open(HTML_DOSYASI, "w", encoding="utf-8") as f:
        f.write(html)

    durum_kaydet("hedef_sayfa_yuklendi", {
        "baslik": baslik,
        "html_boyut": html_boy,
        "cookie_sayisi": len(cookieler),
        "url": driver.current_url,
    })

    log(f"\n③ Sonuçlar:")
    log(f"   Başlık    : {baslik or '(boş)'}")
    log(f"   HTML      : {html_boy:,} karakter")
    log(f"   Cookie    : {len(cookieler)}")

    # Cookie dict
    cookie_dict = {}
    log("\n   ── Cookie Listesi ──")
    for c in sorted(cookieler, key=lambda x: x["name"]):
        cookie_dict[c["name"]] = c["value"]
        yildiz = "★" if c["name"] in KRITIK_COOKIELER else " "
        deger = c["value"][:60] + "…" if len(c["value"]) > 60 else c["value"]
        log(f"   {yildiz} {c['name']}: {deger}")

    # Kritik kontrol
    bulunan = [c for c in KRITIK_COOKIELER if c in cookie_dict]
    eksik = [c for c in KRITIK_COOKIELER if c not in cookie_dict]
    log(f"\n   Kritik: {len(bulunan)}/{len(KRITIK_COOKIELER)}")
    if bulunan:
        log(f"   ✅ {bulunan}")
    if eksik:
        log(f"   ❌ {eksik}")

    ilan_sayisi = html.count("searchResultsItem")
    log(f"   İlan: ~{ilan_sayisi}")

    durum_kaydet("cookie_toplandi", {
        "toplam_cookie": len(cookie_dict),
        "kritik_bulunan": bulunan,
        "kritik_eksik": eksik,
        "ilan_sayisi": ilan_sayisi,
        "html_boyut": html_boy,
    })

    basarili = html_boy > 50_000 and len(cookieler) >= 5
    return cookie_dict, basarili


# ── Screenshot al ─────────────────────────────────────────
def ekran_goruntusu(driver, dosya_adi="screenshot.png"):
    try:
        driver.save_screenshot(dosya_adi)
        log(f"   📸 {dosya_adi} kaydedildi")
    except Exception as e:
        log(f"   📸 Screenshot hatası: {e}")


# ── Ana akış ──────────────────────────────────────────────
def main():
    # İlk iş: boş dosyaları oluştur — artifact asla boş kalmaz
    for dosya in [COOKIE_DOSYASI, DURUM_DOSYASI, HATA_DOSYASI]:
        if not os.path.exists(dosya):
            with open(dosya, "w") as f:
                if dosya.endswith(".json"):
                    json.dump({"durum": "baslamadi"}, f)
                else:
                    f.write("Henüz hata yok\n")

    durum_kaydet("script_basladi", {
        "python": sys.version,
        "cwd": os.getcwd(),
        "dosyalar": os.listdir("."),
    })

    # Ortam kontrolü
    try:
        ortam = ortam_kontrol()
    except Exception as e:
        hata_kaydet(f"Ortam kontrol hatası:\n{e}")
        durum_kaydet("ortam_kontrol_hatasi", {"hata": str(e)})

    son_cookieler = {}
    basarili = False

    for deneme in range(1, MAX_DENEME + 1):
        log(f"\n{'━' * 55}")
        log(f"  DENEME {deneme}/{MAX_DENEME}")
        log(f"{'━' * 55}")

        durum_kaydet(f"deneme_{deneme}_basladi")
        driver = None

        try:
            driver = tarayici_olustur()
            son_cookieler, basarili = cookie_topla(driver)
            ekran_goruntusu(driver, f"screenshot_{deneme}.png")

            if basarili:
                log("\n🎉 Cookie toplama BAŞARILI!")
                durum_kaydet(f"deneme_{deneme}_basarili")
                break

            log("⚠️  Yetersiz sonuç")
            durum_kaydet(f"deneme_{deneme}_yetersiz")

        except Exception as e:
            import traceback
            hata_detay = traceback.format_exc()
            log(f"💥 Hata: {type(e).__name__}: {e}")
            log(hata_detay)
            hata_kaydet(f"Deneme {deneme}:\n{hata_detay}")
            durum_kaydet(f"deneme_{deneme}_hata", {
                "tip": type(e).__name__,
                "mesaj": str(e),
            })

            # Crash olsa bile screenshot dene
            if driver:
                ekran_goruntusu(driver, f"screenshot_hata_{deneme}.png")

        finally:
            if driver:
                try:
                    driver.quit()
                    log("   Tarayıcı kapatıldı")
                except Exception:
                    pass

        if deneme < MAX_DENEME:
            bekleme = deneme * 15
            log(f"⏳ {bekleme}s bekleniyor...")
            time.sleep(bekleme)

    # ── Sonuç dosyası ─────────────────────────────────────
    sonuc = {
        "cookies": son_cookieler,
        "toplam": len(son_cookieler),
        "basarili": basarili,
        "tarih": datetime.now(timezone.utc).isoformat(),
        "kritik_bulunan": [
            c for c in KRITIK_COOKIELER if c in son_cookieler
        ],
        "kritik_eksik": [
            c for c in KRITIK_COOKIELER if c not in son_cookieler
        ],
    }

    with open(COOKIE_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(sonuc, f, indent=2, ensure_ascii=False)

    log(f"\n{COOKIE_DOSYASI} kaydedildi ({len(son_cookieler)} cookie)")

    # ── Özet ──────────────────────────────────────────────
    log(f"\n{'═' * 55}")
    log(f"  ÖZET")
    log(f"{'═' * 55}")
    log(f"  Durum  : {'✅ BAŞARILI' if basarili else '❌ BAŞARISIZ'}")
    log(f"  Cookie : {len(son_cookieler)}")
    log(f"  Kritik : {len(sonuc['kritik_bulunan'])}/{len(KRITIK_COOKIELER)}")
    log(f"{'═' * 55}")

    durum_kaydet("script_bitti", {
        "basarili": basarili,
        "cookie_sayisi": len(son_cookieler),
    })

    # Başarısız olsa bile exit(0) — artifact'lar kaybolmasın
    # Gerçek başarısızlığı cookies.json içindeki "basarili" alanından anla
    if not basarili:
        log("\n⚠️  Script başarısız ama dosyalar kaydedildi")
        log("    Artifact'ları indirip durum.json ve hata.txt'yi kontrol et")
        sys.exit(1)


if __name__ == "__main__":
    main()
