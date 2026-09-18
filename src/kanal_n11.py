# -*- coding: utf-8 -*-
# RafRadar - https://github.com/FlyerFukas/rafradar
# Copyright (c) 2026 Furkan Akduman. Dual-licensed: free for noncommercial use
# under PolyForm Noncommercial 1.0.0 (LICENSE); commercial use requires a
# separate paid license (COMMERCIAL.md).
"""N11 kanal adaptoru - JSON-LD ItemList uzerinden urun cekimi."""
import json, time, requests
from bs4 import BeautifulSoup

BASLIK = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
          "Accept-Language": "tr-TR,tr;q=0.9"}
KANAL = "n11"

def ara(kelime, sayfa=1, bekle=1.2):
    """Bir arama kelimesi icin ilk sayfa urunlerini dondurur (shopper'in gordugu raf)."""
    url = f"https://www.n11.com/arama?q={requests.utils.quote(kelime)}&pg={sayfa}"
    try:
        r = requests.get(url, headers=BASLIK, timeout=25)
    except Exception as e:
        return {"kanal": KANAL, "arama": kelime, "hata": f"{type(e).__name__}", "urunler": []}
    if r.status_code != 200:
        return {"kanal": KANAL, "arama": kelime, "hata": f"HTTP {r.status_code}", "urunler": []}

    s = BeautifulSoup(r.text, "html.parser")
    for ld in s.find_all("script", type="application/ld+json"):
        try: d = json.loads(ld.string or "{}")
        except Exception: continue
        if d.get("@type") != "ItemList":
            continue
        urunler = []
        for sira, o in enumerate(d.get("itemListElement") or [], start=1):
            it = o.get("item", o)
            of = it.get("offers") or {}
            if isinstance(of, list): of = of[0] if of else {}
            br = it.get("brand")
            br = br.get("name") if isinstance(br, dict) else br
            try: fiyat = float(of.get("price")) if of.get("price") is not None else None
            except (TypeError, ValueError): fiyat = None
            urunler.append({
                "sira": sira, "marka": br or "", "ad": it.get("name") or "",
                "fiyat": fiyat, "para": of.get("priceCurrency") or "TRY",
                "stok": of.get("availability") or "", "url": it.get("url") or o.get("url") or "",
                "gorsel": it.get("image") or "", "aciklama": it.get("description") or "",
            })
        time.sleep(bekle)
        return {"kanal": KANAL, "arama": kelime, "sayfa": sayfa,
                "toplam_sonuc": d.get("numberOfItems"), "urunler": urunler}
    time.sleep(bekle)
    return {"kanal": KANAL, "arama": kelime, "hata": "ItemList bulunamadi", "urunler": []}
