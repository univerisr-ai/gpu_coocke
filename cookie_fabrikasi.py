#!/usr/bin/env python3
"""
Cookie Fabrikası v2 - Stealth Mod
PerimeterX bypass: stealth + mouse + bekleme
"""

import os
import sys
import json
import time
import random
import requests
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync


def insan_gibi_mouse(page):
    """Mouse'u rastgele gezdirerek insan gibi davran"""
    for _ in range(random.randint(3, 6)):
        x = random.randint(100, 1200)
        y = random.randint(100, 600)
        page.mouse.move(x, y)
        time.sleep(random.uniform(0.3, 0.8))

    # Scroll yap
    for _ in range(random.randint(2, 4)):
        page.mouse.wheel(0, random.randint(200, 500))
        time.sleep(random.uniform(0.5, 1.5))


def insan_gibi_bekle(min_s=3, max_s=7):
    """Rastgele süre bekle"""
    sure = random.uniform(min_s, max_s)
    time.sleep(sure)


def cookie_al():
    """Stealth mod ile cookie yakala"""
    print("🍪 Cookie alma başlıyor (STEALTH MOD)...")
    print(f"⏰ Zaman: {time.strftime('%H:%M:%S')}")

    cookies = {}

    with sync_playwright() as p:
        print("🌐 Stealth Chromium açılıyor...")

        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-infobars",
                "--window-size=1920,1080",
                "--start-maximized",
            ]
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="tr-TR",
            timezone_id="Europe/Istanbul",
            color_scheme="light",
            java_script_enabled=True,
            has_touch=False,
            is_mobile=False,
        )

        page = context.new_page()

        # STEALTH MODU AKTİF ET
        stealth_sync(page)
        print("🥷 Stealth modu aktif!")

        # Önce Google'a git (doğal görünsün)
        print("📡 Önce Google'a gidiliyor (doğal görünmek için)...")
        try:
            page.goto("https://www.google.com.tr", wait_until="domcontentloaded", timeout=20000)
            insan_gibi_bekle(2, 4)
            insan_gibi_mouse(page)
        except Exception:
            pass

        # Ana sayfaya git
        print("📡 sahibinden.com ana sayfaya gidiliyor...")
        try:
            page.goto(
                "https://www.sahibinden.com",
                wait_until="domcontentloaded",
                timeout=45000
            )
            print("   Ana sayfa yüklendi, bekleniyor...")
            insan_gibi_bekle(5, 8)
            insan_gibi_mouse(page)
        except Exception as e:
            print(f"   ⚠️ Ana sayfa hatası: {e}")

        # Ekran kartı sayfasına git
        print("📡 Ekran kartı sayfasına gidiliyor...")
        try:
            page.goto(
                "https://www.sahibinden.com/ekran-karti-masaustu",
                wait_until="domcontentloaded",
                timeout=45000
            )
            insan_gibi_bekle(4, 7)
            insan_gibi_mouse(page)
        except Exception as e:
            print(f"   ⚠️ Kategori hatası: {e}")

        # Sayfa yüklenmesini bekle (daha uzun)
        print("⏳ Sayfa yüklenmesi bekleniyor...")
        ilan_bulundu = False

        for i in range(12):
            content = page.content()

            if "searchResultsItem" in content:
                print(f"   ✅ İlanlar yüklendi! (deneme {i+1})")
                ilan_bulundu = True
                break
            elif "px-captcha" in content.lower():
                print(f"   🛡️ PerimeterX challenge... ({i+1}/12)")
                # Challenge sayfasında bekle ve mouse gezdirerek çözülmesini bekle
                insan_gibi_mouse(page)
                insan_gibi_bekle(5, 10)
            elif "cf-challenge" in content.lower():
                print(f"   🛡️ Cloudflare challenge... ({i+1}/12)")
                insan_gibi_bekle(5, 8)
            else:
                print(f"   ⏳ Bekleniyor... ({i+1}/12)")
                insan_gibi_mouse(page)
                insan_gibi_bekle(3, 5)

        # İlanlar bulunduysa sayfada biraz gez
        if ilan_bulundu:
            print("🖱️ Sayfada geziniliyor (doğal davranış)...")
            insan_gibi_mouse(page)
            insan_gibi_bekle(3, 5)

            # Scroll yap
            for _ in range(3):
                page.mouse.wheel(0, random.randint(300, 700))
                insan_gibi_bekle(1, 3)

        # 2. sayfaya geç
        print("📄 2. sayfaya geçiliyor...")
        try:
            page.goto(
                "https://www.sahibinden.com/ekran-karti-masaustu?pagingOffset=20",
                wait_until="domcontentloaded",
                timeout=30000
            )
            insan_gibi_bekle(4, 7)
            insan_gibi_mouse(page)
        except Exception as e:
            print(f"   ⚠️ 2. sayfa hatası: {e}")

        # Cookie'leri topla
        browser_cookies = context.cookies()

        for cookie in browser_cookies:
            domain = cookie.get("domain", "")
            if "sahibinden" in domain:
                cookies[cookie["name"]] = cookie["value"]

        print(f"\n🍪 {len(cookies)} cookie yakalandı!")

        # Önemli cookie kontrol
        onemli = ["st", "vid", "_px3", "_pxvid", "MS1"]
        bulunan_onemli = 0
        for key in onemli:
            if key in cookies:
                print(f"   ✅ {key}: mevcut")
                bulunan_onemli += 1
            else:
                print(f"   ❌ {key}: YOK")

        # Sayfa kontrolü
        content = page.content()
        if "searchResultsItem" in content:
            print("✅ Sayfada ilanlar görünüyor!")
        else:
            print("⚠️ Sayfada ilan görünmüyor")

            # Debug: Sayfanın başlığını göster
            title = page.title()
            print(f"   Sayfa başlığı: {title}")
            print(f"   HTML boyutu: {len(content)} karakter")

        browser.close()
        print("🔒 Chromium kapatıldı")

    return cookies


def oracle_gonder(cookies):
    """Cookie'leri Oracle'a gönder"""
    oracle_ip = os.environ.get("ORACLE_IP", "")
    oracle_port = os.environ.get("ORACLE_PORT", "5000")
    api_key = os.environ.get("ORACLE_API_KEY", "")

    if not oracle_ip:
        print("⏭️ ORACLE_IP yok, gönderme atlanıyor (henüz kurulmamış)")
        return True  # Hata değil, sadece henüz kurulmamış

    url = f"http://{oracle_ip}:{oracle_port}/api/cookie-guncelle"
    print(f"📤 Oracle'a gönderiliyor: {oracle_ip}")

    try:
        resp = requests.post(url, json={
            "api_key": api_key,
            "cookies": cookies,
            "zaman": time.strftime("%Y-%m-%d %H:%M:%S"),
            "kaynak": "github-actions-stealth"
        }, timeout=15)

        if resp.status_code == 200:
            print(f"✅ Oracle'a gönderildi!")
            return True
        else:
            print(f"❌ Oracle hatası: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Oracle bağlantı hatası: {e}")
        return False


def telegram_bildir(mesaj):
    """Telegram'dan bildir"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        print("⏭️ Telegram bilgileri yok, bildirim atlanıyor")
        return

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={
            "chat_id": chat_id,
            "text": f"🏭 Cookie Fabrikası\n{mesaj}"
        }, timeout=10)
        print("📱 Telegram bildirimi gönderildi")
    except Exception:
        pass


def main():
    print("=" * 50)
    print("🏭 GPU HUNTER - COOKİE FABRİKASI v2")
    print("🥷 STEALTH MOD AKTİF")
    print("=" * 50)

    # Cookie al
    cookies = cookie_al()

    if not cookies or len(cookies) < 3:
        print(f"\n❌ Yetersiz cookie ({len(cookies) if cookies else 0} adet)")
        telegram_bildir(f"❌ Cookie alınamadı! Sadece {len(cookies) if cookies else 0} cookie.")
        sys.exit(1)

    # Önemli cookie var mı kontrol
    onemli_var = any(k in cookies for k in ["st", "vid", "_px3"])
    if not onemli_var:
        print("\n⚠️ Önemli cookie'ler eksik!")
        telegram_bildir("⚠️ Cookie alındı ama önemli olanlar eksik.")

    # Oracle'a gönder
    oracle_gonder(cookies)

    # Telegram bildir
    telegram_bildir(f"✅ {len(cookies)} cookie alındı!")

    print("\n🎉 İşlem tamamlandı!")


if __name__ == "__main__":
    main()
