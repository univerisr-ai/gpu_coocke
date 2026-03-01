#!/usr/bin/env python3

from curl_cffi import requests
from bs4 import BeautifulSoup
import json
import sys
from datetime import datetime, timezone

ANA_URL = "https://www.sahibinden.com"
HEDEF_URL = "https://www.sahibinden.com/ekran-karti-masaustu"

def log(x):
    print(x, flush=True)

def main():
    log("Başladı")

    tum_cookieler = {}

    # 1️⃣ Ana sayfa
    log("Ana sayfa isteği atılıyor...")
    r1 = requests.get(
        ANA_URL,
        impersonate="chrome131",
        timeout=30
    )

    log(f"Ana sayfa status: {r1.status_code}")
    tum_cookieler.update(dict(r1.cookies))

    # 2️⃣ Hedef sayfa
    log("Hedef sayfa isteği atılıyor...")
    r2 = requests.get(
        HEDEF_URL,
        impersonate="chrome131",
        cookies=tum_cookieler,
        headers={"referer": ANA_URL},
        timeout=30
    )

    log(f"Hedef status: {r2.status_code}")
    log(f"HTML boyut: {len(r2.text)}")

    # HTML kaydet
    with open("sayfa.html", "w", encoding="utf-8") as f:
        f.write(r2.text)

    # Cookie kaydet
    tum_cookieler.update(dict(r2.cookies))

    with open("cookies.json", "w") as f:
        json.dump({
            "cookies": tum_cookieler,
            "toplam": len(tum_cookieler),
            "tarih": datetime.now(timezone.utc).isoformat()
        }, f, indent=2)

    # İlan parse
    soup = BeautifulSoup(r2.text, "html.parser")
    ilanlar = []

    for item in soup.select("tr.searchResultsItem"):
        baslik = item.select_one("a.classifiedTitle")
        if baslik:
            ilanlar.append({
                "baslik": baslik.get_text(strip=True),
                "url": "https://www.sahibinden.com" + baslik["href"]
            })

    with open("ilanlar.json", "w") as f:
        json.dump({
            "toplam": len(ilanlar),
            "ilanlar": ilanlar[:20]
        }, f, indent=2)

    log(f"İlan sayısı: {len(ilanlar)}")

    if len(r2.text) < 50000:
        log("Muhtemelen PX block")
        sys.exit(1)

    log("Bitti ✅")

if __name__ == "__main__":
    main()
