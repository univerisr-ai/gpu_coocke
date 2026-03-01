#!/usr/bin/env python3
"""
Sahibinden.com Cookie Fabrikasi
undetected-chromedriver + Versiyon Sabitleme
"""

import undetected_chromedriver as uc
import json
import time
import random
import sys
import os
from datetime import datetime, timezone
from bs4 import BeautifulSoup

ANA_URL = "https://www.sahibinden.com"
HEDEF_URL = "https://www.sahibinden.com/ekran-karti-masaustu"
KRITIKLER = ["st", "vid", "_px3", "_pxvid", "_pxhd"]


def log(mesaj):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {mesaj}", flush=True)


def main():
    log("🚀 Basladi")

    # ═══════════════════════════════════════════════════════
    # TARAYICI AYARLARI
    # ═══════════════════════════════════════════════════════
    opts = uc.ChromeOptions()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--lang=tr-TR")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-infobars")

    driver = None
    
    try:
        log("Tarayici baslatiliyor...")
        
        # ═══════════════════════════════════════════════════
        # ÖNEMLI: version_main=145
        # Kurulu Chrome 145 oldugu icin driver da 145 olmali
        # ═══════════════════════════════════════════════════
        driver = uc.Chrome(
            options=opts,
            headless=False,
            use_subprocess=True,
            version_main=145,  # <-- KRITIK DÜZELTME
        )
        
        log("Tarayici acildi")

        # ═══════════════════════════════════════════════════════
        # 1️⃣ ANA SAYFA
        # ═══════════════════════════════════════════════════════
        log("① Ana sayfa...")
        driver.get(ANA_URL)
        time.sleep(random.uniform(6, 9))

        html1 = driver.page_source
        log(f"   HTML: {len(html1):,}")

        # Challenge bekle
        if len(html1) < 15000:
            log("   Challenge bekleniyor (25s)...")
            time.sleep(25)
            html1 = driver.page_source
            log(f"   Yeni HTML: {len(html1):,}")

        # Scroll
        driver.execute_script("window.scrollTo({top: 400, behavior: 'smooth'})")
        time.sleep(2)

        # ═══════════════════════════════════════════════════════
        # 2️⃣ HEDEF SAYFA
        # ═══════════════════════════════════════════════════════
        log("② Hedef sayfa...")
        driver.get(HEDEF_URL)
        time.sleep(random.uniform(8, 12))

        # Insan gibi scroll
        for y in [350, 750, 1200]:
            driver.execute_script(f"window.scrollTo({{top: {y}, behavior: 'smooth'}})")
            time.sleep(random.uniform(1.5, 3))

        html2 = driver.page_source
        baslik = driver.title
        log(f"   Baslik: {baslik}")
        log(f"   HTML: {len(html2):,}")

        # ═══════════════════════════════════════════════════════
        # 3️⃣ COOKIE TOPLA
        # ═══════════════════════════════════════════════════════
        cookieler = driver.get_cookies()
        cookie_dict = {c["name"]: c["value"] for c in cookieler}

        log(f"   Cookie: {len(cookieler)} adet")

        # Kritikleri kontrol et
        bulunan = [k for k in KRITIKLER if k in cookie_dict]
        log(f"   Kritik: {len(bulunan)}/{len(KRITIKLER)} → {bulunan}")

        # ═══════════════════════════════════════════════════════
        # 4️⃣ DOSYALARI KAYDET
        # ═══════════════════════════════════════════════════════
        
        # HTML
        with open("sayfa.html", "w", encoding="utf-8") as f:
            f.write(html2)

        # Cookies
        with open("cookies.json", "w", encoding="utf-8") as f:
            json.dump({
                "cookies": cookie_dict,
                "toplam": len(cookie_dict),
                "kritik_bulunan": bulunan,
                "tarih": datetime.now(timezone.utc).isoformat()
            }, f, indent=2, ensure_ascii=False)

        # Ilanlar
        soup = BeautifulSoup(html2, "html.parser")
        ilanlar = []
        for item in soup.select("tr.searchResultsItem"):
            b = item.select_one("a.classifiedTitle")
            f = item.select_one("td.searchResultsPriceValue span")
            if b:
                ilanlar.append({
                    "baslik": b.get_text(strip=True),
                    "url": "https://www.sahibinden.com" + b.get("href", ""),
                    "fiyat": f.get_text(strip=True) if f else ""
                })

        with open("ilanlar.json", "w", encoding="utf-8") as f:
            json.dump({"toplam": len(ilanlar), "ilanlar": ilanlar[:30]}, 
                      f, indent=2, ensure_ascii=False)

        # ═══════════════════════════════════════════════════════
        # ÖZET
        # ═══════════════════════════════════════════════════════
        log("\n" + "═" * 50)
        log("  ÖZET")
        log("═" * 50)
        log(f"  HTML   : {len(html2):,}")
        log(f"  Cookie : {len(cookie_dict)}")
        log(f"  Kritik : {bulunan}")
        log(f"  Ilan   : {len(ilanlar)}")
        log("═" * 50)

        if len(html2) < 50000:
            log("\n⚠️  ENGELLENDI")
            sys.exit(1)

        log("\n✅ BASARILI")

    except Exception as e:
        log(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        if driver:
            driver.quit()
            log("Tarayici kapandi")


if __name__ == "__main__":
    main()
