#!/usr/bin/env python3
"""
Sahibinden.com İlan Çekici
curl_cffi ile Chrome TLS parmak izi taklidi
Tarayıcı açmaya gerek yok!
"""

import subprocess
import json
import sys
import os
import re
import time
import random
from datetime import datetime, timezone
from bs4 import BeautifulSoup

# ── Ayarlar ───────────────────────────────────────────────
DURUM_DOSYASI  = "durum.json"
COOKIE_DOSYASI = "cookies.json"
ILAN_DOSYASI   = "ilanlar.json"
HTML_DOSYASI   = "sayfa.html"
HATA_DOSYASI   = "hata.txt"
MAX_DENEME     = 3

HEDEF_URL = "https://www.sahibinden.com/ekran-karti-masaustu"
ANA_URL   = "https://www.sahibinden.com"


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def durum_kaydet(adim: str, detay: dict = None):
    veri = {
        "adim": adim,
        "zaman": datetime.now(timezone.utc).isoformat(),
        "detay": detay or {},
    }
    try:
        durumlar = []
        if os.path.exists(DURUM_DOSYASI):
            with open(DURUM_DOSYASI, "r") as f:
                eski = json.load(f)
                if isinstance(eski, list):
                    durumlar = eski
        durumlar.append(veri)
        with open(DURUM_DOSYASI, "w") as f:
            json.dump(durumlar, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
    log(f"📌 {adim}")


def hata_kaydet(msg: str):
    with open(HATA_DOSYASI, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}]\n{msg}\n{'='*60}\n")


# ── curl-impersonate ile istek at ─────────────────────────
def curl_isle(url: str, cookie_str: str = "", referer: str = "") -> dict:
    """
    curl-impersonate kullanarak Chrome gibi TLS handshake yapar.
    Normal curl veya requests ile yapılan istekler TLS parmak izinden
    yakalanır. curl-impersonate bunu çözer.
    """

    cmd = [
        "curl-impersonate-chrome",
        "--max-time", "30",
        "--location",              # Redirect takip et
        "--compressed",            # gzip/br kabul et
        "-s",                      # Sessiz mod
        "-D", "/dev/stderr",       # Header'ları stderr'e yaz
        "-H", "accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "-H", "accept-language: tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "-H", "cache-control: max-age=0",
        "-H", "sec-ch-ua: \"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
        "-H", "sec-ch-ua-mobile: ?0",
        "-H", 'sec-ch-ua-platform: "Windows"',
        "-H", "sec-fetch-dest: document",
        "-H", "sec-fetch-mode: navigate",
        "-H", "sec-fetch-site: same-origin",
        "-H", "sec-fetch-user: ?1",
        "-H", "upgrade-insecure-requests: 1",
        "-H", "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    ]

    if referer:
        cmd += ["-H", f"referer: {referer}"]
    else:
        cmd += ["-H", "sec-fetch-site: none"]

    if cookie_str:
        cmd += ["-H", f"cookie: {cookie_str}"]

    # Cookie jar — otomatik cookie yönetimi
    cmd += [
        "-c", "cookiejar.txt",    # Cookie'leri dosyaya kaydet
        "-b", "cookiejar.txt",    # Cookie'leri dosyadan oku
    ]

    cmd.append(url)

    log(f"   curl → {url}")

    sonuc = subprocess.run(
        cmd,
        capture_output=True,
        timeout=45,
    )

    body = sonuc.stdout.decode("utf-8", errors="replace")
    headers_raw = sonuc.stderr.decode("utf-8", errors="replace")

    # Response header'lardan cookie'leri çıkar
    cookieler = {}
    for satir in headers_raw.split("\n"):
        if satir.lower().startswith("set-cookie:"):
            parcalar = satir.split(":", 1)[1].strip().split(";")[0]
            if "=" in parcalar:
                isim, deger = parcalar.split("=", 1)
                cookieler[isim.strip()] = deger.strip()

    # HTTP durum kodu
    status = 0
    for satir in headers_raw.split("\n"):
        m = re.match(r"HTTP/\S+\s+(\d+)", satir)
        if m:
            status = int(m.group(1))

    return {
        "status": status,
        "body": body,
        "headers_raw": headers_raw,
        "cookies": cookieler,
        "body_len": len(body),
    }


# ── Fallback: normal curl (curl-impersonate yoksa) ───────
def curl_normal(url: str, cookie_str: str = "", referer: str = "") -> dict:
    """curl-impersonate bulunamazsa normal curl kullan"""

    cmd = [
        "curl",
        "--max-time", "30",
        "--location",
        "--compressed",
        "-s",
        "-D", "/dev/stderr",
        "--ciphers", "TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256",
        "--tls-max", "1.3",
        "--http2",
        "-H", "accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "-H", "accept-language: tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "-H", "cache-control: max-age=0",
        "-H", "sec-ch-ua: \"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
        "-H", "sec-ch-ua-mobile: ?0",
        "-H", 'sec-ch-ua-platform: "Windows"',
        "-H", "sec-fetch-dest: document",
        "-H", "sec-fetch-mode: navigate",
        "-H", "sec-fetch-site: none",
        "-H", "sec-fetch-user: ?1",
        "-H", "upgrade-insecure-requests: 1",
        "-H", "user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    ]

    if referer:
        cmd += ["-H", f"referer: {referer}"]

    if cookie_str:
        cmd += ["-H", f"cookie: {cookie_str}"]

    cmd += ["-c", "cookiejar.txt", "-b", "cookiejar.txt"]
    cmd.append(url)

    log(f"   curl (normal) → {url}")

    sonuc = subprocess.run(cmd, capture_output=True, timeout=45)

    body = sonuc.stdout.decode("utf-8", errors="replace")
    headers_raw = sonuc.stderr.decode("utf-8", errors="replace")

    cookieler = {}
    for satir in headers_raw.split("\n"):
        if satir.lower().startswith("set-cookie:"):
            parcalar = satir.split(":", 1)[1].strip().split(";")[0]
            if "=" in parcalar:
                isim, deger = parcalar.split("=", 1)
                cookieler[isim.strip()] = deger.strip()

    status = 0
    for satir in headers_raw.split("\n"):
        m = re.match(r"HTTP/\S+\s+(\d+)", satir)
        if m:
            status = int(m.group(1))

    return {
        "status": status,
        "body": body,
        "headers_raw": headers_raw,
        "cookies": cookieler,
        "body_len": len(body),
    }


# ── curl_cffi yöntemi (Python kütüphanesi) ───────────────
def curl_cffi_isle(url: str, mevcut_cookieler: dict = None,
                   referer: str = "") -> dict:
    """
    curl_cffi — Python'dan Chrome TLS parmak izi taklidi
    curl-impersonate'ın Python wrapper'ı
    """
    from curl_cffi import requests as cffi_requests

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "max-age=0",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
    }

    if referer:
        headers["referer"] = referer
        headers["sec-fetch-site"] = "same-origin"

    log(f"   curl_cffi → {url}")

    resp = cffi_requests.get(
        url,
        headers=headers,
        cookies=mevcut_cookieler or {},
        impersonate="chrome131",   # Chrome 131 TLS parmak izi
        timeout=30,
        allow_redirects=True,
    )

    # Cookie dict
    cookieler = dict(resp.cookies)

    return {
        "status": resp.status_code,
        "body": resp.text,
        "cookies": cookieler,
        "body_len": len(resp.text),
        "headers_raw": str(dict(resp.headers)),
    }


# ── Hangi curl yöntemi kullanılacak? ─────────────────────
def curl_yontemi_sec():
    """En iyi mevcut yöntemi seç"""

    # Öncelik 1: curl_cffi (Python paketi)
    try:
        from curl_cffi import requests as test_req
        log("✅ curl_cffi bulundu — Python TLS impersonation")
        return "curl_cffi"
    except ImportError:
        log("   curl_cffi yok")

    # Öncelik 2: curl-impersonate (binary)
    try:
        r = subprocess.run(
            ["curl-impersonate-chrome", "--version"],
            capture_output=True, timeout=5
        )
        if r.returncode == 0:
            log("✅ curl-impersonate-chrome bulundu")
            return "curl_impersonate"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        log("   curl-impersonate-chrome yok")

    # Öncelik 3: normal curl
    try:
        r = subprocess.run(["curl", "--version"], capture_output=True, timeout=5)
        if r.returncode == 0:
            log("⚠️  Sadece normal curl var — TLS parmak izi farklı olacak")
            return "curl_normal"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    log("❌ Hiçbir curl bulunamadı!")
    return None


def istek_at(url: str, cookieler: dict = None, referer: str = "",
             yontem: str = "curl_cffi") -> dict:
    """Seçilen yöntemle istek at"""

    if yontem == "curl_cffi":
        return curl_cffi_isle(url, cookieler, referer)
    elif yontem == "curl_impersonate":
        cookie_str = "; ".join(f"{k}={v}" for k, v in (cookieler or {}).items())
        return curl_isle(url, cookie_str, referer)
    else:
        cookie_str = "; ".join(f"{k}={v}" for k, v in (cookieler or {}).items())
        return curl_normal(url, cookie_str, referer)


# ── İlanları parse et ─────────────────────────────────────
def ilanlari_ayikla(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    ilanlar = []

    for item in soup.select("tr.searchResultsItem"):
        baslik_el = item.select_one("a.classifiedTitle")
        fiyat_el  = item.select_one("td.searchResultsPriceValue span")
        konum_el  = item.select_one("td.searchResultsLocationValue")
        tarih_el  = item.select_one("td.searchResultsDateValue span")

        if baslik_el:
            ilan = {
                "baslik": baslik_el.get_text(strip=True),
                "url":    "https://www.sahibinden.com" + baslik_el.get("href", ""),
                "fiyat":  fiyat_el.get_text(strip=True) if fiyat_el else "",
                "konum":  konum_el.get_text(" ", strip=True) if konum_el else "",
                "tarih":  tarih_el.get_text(strip=True) if tarih_el else "",
            }
            ilanlar.append(ilan)

    return ilanlar


# ── Ana akış ──────────────────────────────────────────────
def main():
    # Boş dosyaları oluştur
    for dosya in [COOKIE_DOSYASI, DURUM_DOSYASI, HATA_DOSYASI]:
        if not os.path.exists(dosya):
            with open(dosya, "w") as f:
                if dosya.endswith(".json"):
                    json.dump({"durum": "baslamadi"}, f)
                else:
                    f.write("")

    durum_kaydet("script_basladi", {
        "python": sys.version,
        "cwd": os.getcwd(),
    })

    # Yöntem seç
    yontem = curl_yontemi_sec()
    if not yontem:
        hata_kaydet("Hiçbir curl yöntemi bulunamadı")
        durum_kaydet("curl_bulunamadi")
        sys.exit(1)

    durum_kaydet("yontem_secildi", {"yontem": yontem})

    tum_cookieler = {}
    basarili = False
    ilanlar = []

    for deneme in range(1, MAX_DENEME + 1):
        log(f"\n{'━' * 55}")
        log(f"  DENEME {deneme}/{MAX_DENEME}  (yöntem: {yontem})")
        log(f"{'━' * 55}")

        durum_kaydet(f"deneme_{deneme}_basladi")

        try:
            # ① Ana sayfa — cookie toplamak için
            log("\n① Ana sayfa...")
            r1 = istek_at(ANA_URL, yontem=yontem)
            log(f"   HTTP {r1['status']} | {r1['body_len']:,} karakter | {len(r1['cookies'])} cookie")

            tum_cookieler.update(r1["cookies"])
            durum_kaydet("ana_sayfa_tamam", {
                "status": r1["status"],
                "body_len": r1["body_len"],
                "cookie_sayisi": len(r1["cookies"]),
                "cookie_isimleri": list(r1["cookies"].keys()),
            })

            time.sleep(random.uniform(3, 6))

            # ② Hedef sayfa
            log("\n② Hedef sayfa...")
            r2 = istek_at(
                HEDEF_URL,
                cookieler=tum_cookieler,
                referer=ANA_URL,
                yontem=yontem,
            )
            log(f"   HTTP {r2['status']} | {r2['body_len']:,} karakter | {len(r2['cookies'])} cookie")

            tum_cookieler.update(r2["cookies"])

            # HTML kaydet
            with open(HTML_DOSYASI, "w", encoding="utf-8") as f:
                f.write(r2["body"])

            # Başlık bul
            baslik = ""
            m = re.search(r"<title>(.*?)</title>", r2["body"], re.IGNORECASE)
            if m:
                baslik = m.group(1).strip()

            log(f"   Başlık: {baslik or '(boş)'}")

            # İlanları parse et
            ilanlar = ilanlari_ayikla(r2["body"])
            log(f"   İlan sayısı: {len(ilanlar)}")

            durum_kaydet("hedef_sayfa_tamam", {
                "status": r2["status"],
                "body_len": r2["body_len"],
                "baslik": baslik,
                "ilan_sayisi": len(ilanlar),
                "toplam_cookie": len(tum_cookieler),
                "cookie_isimleri": list(tum_cookieler.keys()),
            })

            # İlk 3 ilanı göster
            if ilanlar:
                log("\n   ── İlk 3 İlan ──")
                for i, ilan in enumerate(ilanlar[:3], 1):
                    log(f"   {i}. {ilan['baslik']}")
                    log(f"      {ilan['fiyat']} | {ilan['konum']}")

            # Başarı kontrolü
            basarili = r2["body_len"] > 50_000 and len(ilanlar) > 0

            if basarili:
                log("\n🎉 BAŞARILI!")
                durum_kaydet(f"deneme_{deneme}_basarili", {
                    "ilan_sayisi": len(ilanlar),
                })
                break

            # 50KB üstü ama ilan yoksa da kısmi başarı
            if r2["body_len"] > 50_000:
                log("⚠️  Sayfa geldi ama ilan bulunamadı (HTML yapısı farklı olabilir)")
                basarili = True  # HTML'yi incelemek için başarılı say
                break

            log("⚠️  Yetersiz sonuç")
            durum_kaydet(f"deneme_{deneme}_yetersiz")

        except Exception as e:
            import traceback
            hata_detay = traceback.format_exc()
            log(f"💥 {type(e).__name__}: {e}")
            hata_kaydet(f"Deneme {deneme}:\n{hata_detay}")
            durum_kaydet(f"deneme_{deneme}_hata", {
                "tip": type(e).__name__,
                "mesaj": str(e),
            })

        if deneme < MAX_DENEME:
            bekleme = deneme * 10
            log(f"⏳ {bekleme}s bekleniyor...")
            time.sleep(bekleme)

    # ── Sonuçları kaydet ──────────────────────────────────
    with open(COOKIE_DOSYASI, "w", encoding="utf-8") as f:
        json.dump({
            "cookies": tum_cookieler,
            "toplam": len(tum_cookieler),
            "basarili": basarili,
            "tarih": datetime.now(timezone.utc).isoformat(),
            "yontem": yontem,
            "cookie_isimleri": sorted(tum_cookieler.keys()),
        }, f, indent=2, ensure_ascii=False)

    if ilanlar:
        with open(ILAN_DOSYASI, "w", encoding="utf-8") as f:
            json.dump({
                "toplam": len(ilanlar),
                "tarih": datetime.now(timezone.utc).isoformat(),
                "ilanlar": ilanlar,
            }, f, indent=2, ensure_ascii=False)

    # ── Özet ──────────────────────────────────────────────
    log(f"\n{'═' * 55}")
    log(f"  ÖZET")
    log(f"{'═' * 55}")
    log(f"  Durum   : {'✅ BAŞARILI' if basarili else '❌ BAŞARISIZ'}")
    log(f"  Yöntem  : {yontem}")
    log(f"  Cookie  : {len(tum_cookieler)}")
    log(f"  İlan    : {len(ilanlar)}")
    log(f"  Cookieler: {sorted(tum_cookieler.keys())}")
    log(f"{'═' * 55}")

    durum_kaydet("script_bitti", {
        "basarili": basarili,
        "cookie_sayisi": len(tum_cookieler),
        "ilan_sayisi": len(ilanlar),
    })

    if not basarili:
        sys.exit(1)


if __name__ == "__main__":
    main()
