#!/usr/bin/env python3
"""
Cookie Fabrikası
GitHub Actions'da çalışır
Playwright ile Sahibinden'e girip cookie alır
Oracle Cloud'a gönderir
"""

import os
import sys
import json
import time
import requests
from playwright.sync_api import sync_playwright


def cookie_al():
    """Playwright ile Sahibinden'e girip cookie yakala"""
    
    print("🍪 Cookie alma başlıyor...")
    print(f"⏰ Zaman: {time.strftime('%H:%M:%S')}")
    
    cookies = {}
    
    with sync_playwright() as p:
        
        # Chromium aç
        print("🌐 Chromium açılıyor...")
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ]
        )
        
        # Gerçek kullanıcı gibi context
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="tr-TR",
            timezone_id="Europe/Istanbul",
        )
        
        page = context.new_page()
        
        # Ana sayfaya git
        print("📡 sahibinden.com'a gidiliyor...")
        try:
            page.goto(
                "https://www.sahibinden.com",
                wait_until="domcontentloaded",
                timeout=45000
            )
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ Ana sayfa hatası: {e}")
        
        # Ekran kartı sayfasına git
        print("📡 Ekran kartı sayfasına gidiliyor...")
        try:
            page.goto(
                "https://www.sahibinden.com/ekran-karti-masaustu",
                wait_until="domcontentloaded",
                timeout=45000
            )
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ Kategori sayfası hatası: {e}")
        
        # Sayfanın yüklenmesini bekle
        print("⏳ Sayfa yüklenmesi bekleniyor...")
        for i in range(8):
            content = page.content()
            
            if "searchResultsItem" in content:
                print("✅ İlanlar yüklendi!")
                break
            elif "px-captcha" in content.lower():
                print(f"⏳ PerimeterX challenge... ({i+1}/8)")
                time.sleep(5)
            else:
                print(f"⏳ Bekleniyor... ({i+1}/8)")
                time.sleep(4)
        
        # İkinci sayfaya geç (senin yaptığın gibi)
        print("📄 2. sayfaya geçiliyor...")
        try:
            page.goto(
                "https://www.sahibinden.com/ekran-karti-masaustu?pagingOffset=20",
                wait_until="domcontentloaded",
                timeout=30000
            )
            time.sleep(4)
        except Exception as e:
            print(f"⚠️ 2. sayfa hatası: {e}")
        
        # Cookie'leri yakala
        browser_cookies = context.cookies()
        
        for cookie in browser_cookies:
            domain = cookie.get("domain", "")
            if "sahibinden" in domain:
                cookies[cookie["name"]] = cookie["value"]
        
        print(f"🍪 {len(cookies)} cookie yakalandı!")
        
        # Önemli cookie'leri kontrol et
        onemli_cookieler = ["st", "vid", "_px3", "_pxvid", "MS1"]
        for key in onemli_cookieler:
            if key in cookies:
                print(f"   ✅ {key}: mevcut")
            else:
                print(f"   ❌ {key}: YOK")
        
        # Sayfada ilan var mı kontrol et
        content = page.content()
        if "searchResultsItem" in content:
            print("✅ Sayfada ilanlar görünüyor, cookie'ler geçerli!")
        else:
            print("⚠️ Sayfada ilan görünmüyor, cookie'ler çalışmayabilir")
        
        browser.close()
        print("🔒 Chromium kapatıldı")
    
    return cookies


def oracle_gonder(cookies):
    """Cookie'leri Oracle Cloud'a gönder"""
    
    oracle_ip = os.environ.get("ORACLE_IP", "")
    oracle_port = os.environ.get("ORACLE_PORT", "5000")
    api_key = os.environ.get("ORACLE_API_KEY", "")
    
    if not oracle_ip:
        print("❌ ORACLE_IP ayarlanmamış!")
        return False
    
    if not api_key:
        print("❌ ORACLE_API_KEY ayarlanmamış!")
        return False
    
    url = f"http://{oracle_ip}:{oracle_port}/api/cookie-guncelle"
    
    print(f"📤 Oracle'a gönderiliyor: {oracle_ip}:{oracle_port}")
    
    payload = {
        "api_key": api_key,
        "cookies": cookies,
        "zaman": time.strftime("%Y-%m-%d %H:%M:%S"),
        "kaynak": "github-actions"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        
        if response.status_code == 200:
            print(f"✅ Oracle'a gönderildi! Yanıt: {response.json()}")
            return True
        else:
            print(f"❌ Oracle hatası: {response.status_code}")
            print(f"   {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Oracle'a bağlanılamadı! IP: {oracle_ip}")
        return False
    except Exception as e:
        print(f"❌ Gönderme hatası: {e}")
        return False


def telegram_bildir(mesaj):
    """Hata durumunda Telegram'dan bildir"""
    
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    
    if not bot_token or not chat_id:
        return
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        requests.post(url, json={
            "chat_id": chat_id,
            "text": f"🏭 Cookie Fabrikası\n{mesaj}"
        }, timeout=10)
    except Exception:
        pass


def main():
    """Ana fonksiyon"""
    
    print("=" * 50)
    print("🏭 GPU HUNTER - COOKİE FABRİKASI")
    print("=" * 50)
    
    # 1. Cookie al
    cookies = cookie_al()
    
    if not cookies:
        print("\n❌ Cookie alınamadı!")
        telegram_bildir("❌ Cookie alınamadı! PerimeterX engelliyor olabilir.")
        sys.exit(1)
    
    if len(cookies) < 3:
        print(f"\n⚠️ Çok az cookie ({len(cookies)}), yetersiz olabilir")
        telegram_bildir(f"⚠️ Sadece {len(cookies)} cookie alındı, yetersiz olabilir.")
    
    # 2. Oracle'a gönder
    basarili = oracle_gonder(cookies)
    
    if basarili:
        print("\n🎉 Başarılı! Cookie alındı ve Oracle'a gönderildi.")
        telegram_bildir(f"✅ Cookie alındı ({len(cookies)} adet) ve Oracle'a gönderildi!")
    else:
        print("\n⚠️ Cookie alındı ama Oracle'a gönderilemedi!")
        telegram_bildir("⚠️ Cookie alındı ama Oracle'a gönderilemedi!")
        sys.exit(1)


if __name__ == "__main__":
    main()
