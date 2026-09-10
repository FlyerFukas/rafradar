# -*- coding: utf-8 -*-
"""Trendyol kanal adaptoru - Firecrawl (country=TR) + element bazli ayristirma.

Veri kalitesi notlari (HTML incelemesiyle dogrulandi):
  - Kart metninden regex ile fiyat cekmek YANLIS sonuc verir: ayni metinde
    satis fiyati, ustu cizili liste fiyati ve birim fiyat (TL/kg) birlikte gecer.
    Ornek: "649,90 TL ( 5.415,83 TL/kg ) 617,40 TL" -> regex 5.415,83'u secebilir.
  - Bu yuzden fiyat CSS class'larindan okunur; span.unit-price bilincli olarak elenir.
  - Arama sayfasindaki css-slider / slider-wrapper bloklari ORGANIK RAF DEGIL,
    marka vitrini/sponsorlu yerlesimdir. Raf payi metrigini sismesin diye isaretlenir.
"""
import re, subprocess, tempfile, os

KANAL = "trendyol"
ETIKETLER = ("Hızlı Bakış", "Hızlı Teslimat", "Sponsorlu", "Çok Satan", "Yeni",
             "Bugün Kargoda", "Trendyol Plus'a Özel", "Süper Fırsat Ürünü",
             "Yetkili Satıcı", "Çok Al Az Öde", "Sepette İndirim", "Kupon Fırsatı")
# Trendyol siralama rozetleri urun adinin basina yapisir:
# "En 5. Ürün", "En Çok Favorilenen 4. Ürün", "En Çok Ziyaret Edilen 2. Ürün"
ROZET = re.compile(r"^(?:En(?:\s+Çok\s+[\wçğıöşüÇĞİÖŞÜ]+(?:\s+[\wçğıöşüÇĞİÖŞÜ]+)?)?\s+\d+\.\s*Ürün\s*)+",
                   re.IGNORECASE)
SAYI = re.compile(r"([\d.]+,\d{2})")

def _sayi(metin):
    m = SAYI.search(metin or "")
    if not m: return None
    try: return float(m.group(1).replace(".", "").replace(",", "."))
    except ValueError: return None

def _temizle(metin):
    for e in ETIKETLER: metin = metin.replace(e, " ")
    metin = re.sub(r"[\d.]+,\d{2}\s*TL", " ", metin)
    metin = re.sub(r"\s+", " ", metin).strip()
    return ROZET.sub("", metin).strip()

def _slider_mi(dugum, derinlik=8):
    """Kart bir marka vitrini/carousel icinde mi? -> organik raf degil."""
    p = dugum.parent
    for _ in range(derinlik):
        if p is None: return False
        sinif = " ".join(p.get("class") or [])
        if "slider" in sinif or "carousel" in sinif: return True
        p = p.parent
    return False

def _fiyat_oku(kart):
    """Element bazli fiyat: unit-price ASLA kullanilmaz."""
    normal = plus = None
    for sec in ("div.price-section", "div.single-price", "div.sale-price"):
        el = kart.select_one(sec)
        if el and "unit-price" not in " ".join(el.get("class") or []):
            metin = "".join(t for t in el.find_all(string=True)
                            if "unit-price" not in " ".join((t.parent.get("class") or [])))
            normal = _sayi(metin)
            if normal: break
    el = kart.select_one("span.ty-plus-strip-view-price, span.seller-store-ty-plus-promotion-price-value")
    if el: plus = _sayi(el.get_text(" ", strip=True))
    return normal, plus

def _marka_coz(href, ad):
    yol = href.split("trendyol.com", 1)[1] if "trendyol.com" in href else (href or "")
    p = [x for x in yol.split("?")[0].split("/") if x]
    if p and "-p-" not in p[0] and len(p) > 1:
        return p[0].replace("-", " ").title()
    return (ad or "").split(" ")[0]

def ara(kelime):
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as t:
        gecici = t.name
    url = f"https://www.trendyol.com/sr?q={kelime.replace(' ', '%20')}"
    try:
        subprocess.run(["firecrawl", "scrape", url, "--country", "TR", "--wait-for", "6000",
                        "--format", "rawHtml", "-o", gecici],
                       capture_output=True, timeout=180, shell=True)
        html = open(gecici, encoding="utf-8", errors="replace").read()
    except Exception as e:
        return {"kanal": KANAL, "arama": kelime, "hata": type(e).__name__, "urunler": []}
    finally:
        try: os.unlink(gecici)
        except Exception: pass
    if len(html) < 5000:
        return {"kanal": KANAL, "arama": kelime, "hata": "bos yanit", "urunler": []}

    from bs4 import BeautifulSoup
    s = BeautifulSoup(html, "html.parser")
    urunler, gorulen = [], set()
    for a in s.select("a[href*='-p-']"):
        href = a.get("href") or ""
        anahtar = href.split("?")[0]
        if anahtar in gorulen: continue
        ham = a.get_text(" ", strip=True)
        ad = _temizle(ham)
        if len(ad) < 8: continue
        gorulen.add(anahtar)
        sponsorlu = _slider_mi(a)
        normal, plus = _fiyat_oku(a)
        urunler.append({
            "sira": len(urunler) + 1, "marka": _marka_coz(href, ad), "ad": ad[:120],
            "fiyat": normal, "plus_fiyat": plus, "para": "TRY",
            "sponsorlu": sponsorlu, "stok": "",
            "url": ("https://www.trendyol.com" + href) if href.startswith("/") else href,
            "gorsel": "", "aciklama": "",
        })
    # organik siralamayi yeniden numarala (vitrin bloklari raf sirasini bozmasin)
    n = 0
    for u in urunler:
        if not u["sponsorlu"]:
            n += 1; u["organik_sira"] = n
        else:
            u["organik_sira"] = None
    return {"kanal": KANAL, "arama": kelime, "sayfa": 1,
            "toplam_sonuc": len(urunler),
            "organik_sayi": sum(1 for u in urunler if not u["sponsorlu"]),
            "sponsorlu_sayi": sum(1 for u in urunler if u["sponsorlu"]),
            "urunler": urunler}

if __name__ == "__main__":
    import sys
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    r = ara("bepanthol")
    print(f"{len(r['urunler'])} urun | organik {r['organik_sayi']} | vitrin/sponsorlu {r['sponsorlu_sayi']}\n")
    for u in r["urunler"][:10]:
        tip = "VITRIN" if u["sponsorlu"] else f"org#{u['organik_sira']}"
        print(f"  {tip:8s} | {u['ad'][:50]:50s} | {u['fiyat']} TL"
              + (f" (Plus {u['plus_fiyat']})" if u["plus_fiyat"] else ""))
