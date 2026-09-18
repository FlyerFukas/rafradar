# -*- coding: utf-8 -*-
# RafRadar - https://github.com/FlyerFukas/rafradar
# Copyright (c) 2026 Furkan Akduman. Dual-licensed: free for noncommercial use
# under PolyForm Noncommercial 1.0.0 (LICENSE); commercial use requires a
# separate paid license (COMMERCIAL.md).
"""Cok kanalli dijital raf taramasi: N11 (dogrudan) + Trendyol (Firecrawl)."""
import sys, os, json, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
import kanal_n11, kanal_trendyol
import ayarlar
from ayarlar import izlenen_marka, kategori_tipi

def tara(kanallar=None, arama_basina=2, sadece_izlenen=True):
    tarih = datetime.date.today().isoformat()
    sonuc = {"tarih": tarih, "kayitlar": []}
    kanallar = kanallar or ayarlar.yukle()["kanallar"]
    for kat, bilgi in ayarlar.kategoriler().items():
        tip = kategori_tipi(kat)
        for kelime in bilgi["aramalar"][:arama_basina]:
            for kanal in kanallar:
                # Trendyol pahalidir (Firecrawl kredisi); haric tutulan kategorileri atla
                if kanal == "trendyol" and sadece_izlenen and tip != "izlenen":
                    continue
                mod = kanal_n11 if kanal == "n11" else kanal_trendyol
                r = mod.ara(kelime)
                r.update({"kategori": kat, "tip": tip, "izlenen_markalar": bilgi.get("markalar", [])})
                n = len(r.get("urunler", []))
                bn = sum(1 for u in r.get("urunler", []) if izlenen_marka(u["marka"], u["ad"]))
                print(f"  [{kanal:9s}] {kat:16s} | {kelime:24s} | "
                      f"{r.get('hata') or f'{n:3d} urun, {bn:2d} eslesme'}", flush=True)
                sonuc["kayitlar"].append(r)
    yol = f"veri/tarama_coklu_{tarih}.json"
    json.dump(sonuc, open(yol, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    top = sum(len(k.get("urunler", [])) for k in sonuc["kayitlar"])
    print(f"\n=> {len(sonuc['kayitlar'])} arama, {top} urun -> {yol}")
    return yol

if __name__ == "__main__":
    print("COK KANALLI DIJITAL RAF TARAMASI\n" + "-"*70, flush=True)
    tara()
