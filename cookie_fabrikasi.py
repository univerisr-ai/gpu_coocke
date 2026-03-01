#!/usr/bin/env python3
"""
Sahibinden.com Cookie ve İlan Çekici
curl_cffi ile Chrome TLS parmak izi taklidi
"""

from curl_cffi import requests
from bs4 import BeautifulSoup
import json
import sys
from datetime import datetime, timezone

ANA_URL = "https://www.sahibinden.com"
HEDEF_URL = "https://www.sahibinden.com/ekran-karti-masaustu"


def log(mesaj):
    """Zaman damgalı log"""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {mesaj}", flush=True)


def main():
    log("🚀 Script başladı")

    tum_cookieler = {}

    # ═══════════════════════════════════════════════════════
    # 1️⃣ ANA SAYFA
    # ═══════════════════════════════════════════════════════
    log("① Ana sayfa isteği atılıyor...")

    try:
        r1 = requests.get(
            ANA_URL,
            impersonate="chrome",  # Otomatik en güncel Chrome taklidi
            timeout=30
        )
        log(f"   ✓ Status: {r1.status_code}")
        log(f"   ✓ HTML Boyutu: {len(r1.text):,} karakter")

        # Cookie'leri topluyoruz
        tum_cookieler.update(dict(r1.cookies))
        log(f"   ✓ Cookie: {len(tum_cookieler)} adet")

    except Exception as e:
        log(f"   ❌ Ana sayfa hatası: {e}")
        sys.exit(1)

    # ═══════════════════════════════════════════════════════
    # 2️⃣ HEDEF SAYFA (Ekran Kartları)
    # ═══════════════════════════════════════════════════════
    log("② Hedef sayfa isteği atılıyor...")

    try:
        r2 = requests.get(
            HEDEF_URL,
            impersonate="chrome",
            cookies=tum_cookieler,
            headers={"Referer": ANA_URL},
            timeout=30
        )
        log(f"   ✓ Status: {r2.status_code}")
        log(f"   ✓ HTML Boyutu: {len(r2.text):,} karakter")

        # Cookie'leri güncelle
        tum_cookieler.update(dict(r2.cookies))

    except Exception as e:
        log(f"   ❌ Hedef sayfa hatası: {e}")
        sys.exit(1)

    # ═══════════════════════════════════════════════════════
    # 3️⃣ DOSYALARI KAYDET
    # ═══════════════════════════════════════════════════════
    
    # HTML kaydet
    with open("sayfa.html", "w", encoding="utf-8") as f:
        f.write(r2.text)
    log("   ✓ sayfa.html kaydedildi")

    # Cookie kaydet
    with open("cookies.json", "w", encoding="utf-8") as f:
        json.dump({
            "cookies": tum_cookieler,
            "toplam": len(tum_cookieler),
            "isimler": sorted(tum_cookieler.keys()),
            "tarih": datetime.now(timezone.utc).isoformat()
        }, f, indent=2, ensure_ascii=False)
    log("   ✓ cookies.json kaydedildi")

    # ═══════════════════════════════════════════════════════
    # 4️⃣ İLANLARI PARSE ET
    # ═══════════════════════════════════════════════════════
    log("③ İlanlar parse ediliyor...")

    soup = BeautifulSoup(r2.text, "html.parser")
    ilanlar = []

    for item in soup.select("tr.searchResultsItem"):
        baslik_el = item.select_one("a.classifiedTitle")
        fiyat_el = item.select_one("td.searchResultsPriceValue span")
        konum_el = item.select_one("td.searchResultsLocationValue")
        
        if baslik_el:
            ilanlar.append({
                "baslik": baslik_el.get_text(strip=True),
                "url": "https://www.sahibinden.com" + baslik_el.get("href", ""),
                "fiyat": fiyat_el.get_text(strip=True) if fiyat_el else "",
                "konum": konum_el.get_text(" ", strip=True) if konum_el else ""
            })

    # İlanları kaydet
    with open("ilanlar.json", "w", encoding="utf-8") as f:
        json.dump({
            "toplam": len(ilanlar),
            "tarih": datetime.now(timezone.utc).isoformat(),
            "ilanlar": ilanlar[:50]  # İlk 50 ilan
        }, f, indent=2, ensure_ascii=False)

    log(f"   ✓ {len(ilanlar)} ilan bulundu")

    # ═══════════════════════════════════════════════════════
    # 5️⃣ ÖZET
    # ═══════════════════════════════════════════════════════
    log("\n" + "═" * 50)
    log("  ÖZET")
    log("═" * 50)
    log(f"  HTML Boyutu : {len(r2.text):,} karakter")
    log(f"  Cookie      : {len(tum_cookieler)} adet")
    log(f"  İlan        : {len(ilanlar)} adet")
    log(f"═" * 50)

    # Başarı kontrolü
    if len(r2.text) < 50000:
        log("\n⚠️  UYARI: HTML boyutu küçük, muhtemelen engellendin")
        log("   sayfa.html dosyasını kontrol et")
        sys.exit(1)

    if len(ilanlar) == 0:
        log("\n⚠️  UYARI: İlan bulunamadı")
        log("   HTML yapısı değişmiş olabilir")

    log("\n✅ TAMAMLANDI")


if __name__ == "__main__":
    main()
