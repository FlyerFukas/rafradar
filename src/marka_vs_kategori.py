# -*- coding: utf-8 -*-
"""Marka araması mı, kategori araması mı?

Bir markanın adıyla arandığında bulunup, kategori adıyla arandığında
bulunmaması ticari olarak kritik bir durumdur: markayı zaten bilen alışverişçi
ürünü bulur, bilmeyen hiç bulamaz. Yani marka mevcut müşterisini korur ama
kategoriden yeni müşteri kazanamaz.

Testler yapılandırmadan üretilir; her izlenen marka için marka araması ile
o markanın yarıştığı kategorilerin aramaları karşılaştırılır.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import ayarlar
import kanal_trendyol
from ayarlar import izlenen_marka

KATEGORI_BASINA = 2   # marka basina en fazla kac kategori aramasi denenir


def testleri_uret():
    a = ayarlar.yukle()
    testler = []
    for marka, anahtarlar in a["markalar"].items():
        if not anahtarlar:
            continue
        kelimeler = []
        for kat, bilgi in a["kategoriler"].items():
            if ayarlar.kategori_tipi(kat) != "izlenen":
                continue
            if marka not in bilgi.get("markalar", []):
                continue
            aramalar = bilgi.get("aramalar") or []
            if aramalar:
                kelimeler.append(aramalar[0])
        if kelimeler:
            testler.append({
                "marka": marka,
                "marka_arama": (a["kategoriler"].get(kelimeler[0], {}) or {}).get(
                    "marka_aramasi") or anahtarlar[0],
                "kategori_aramalari": kelimeler[:KATEGORI_BASINA],
            })
    return testler


def say(kayit, marka):
    """Sponsorlu vitrin kartlari haric, kac urun bu markaya ait?"""
    urunler = [u for u in kayit.get("urunler", []) if not u.get("sponsorlu")]
    return sum(1 for u in urunler if (izlenen_marka(u["marka"], u["ad"]) or "") == marka), len(urunler)


def calistir():
    testler = testleri_uret()
    if not testler:
        raise SystemExit("Yapılandırmada test üretilecek marka/kategori eşleşmesi yok.")

    sonuc = []
    for t in testler:
        marka = t["marka"]
        r = kanal_trendyol.ara(t["marka_arama"])
        mb, mt = say(r, marka)
        print(f"\n### {marka}")
        print(f"  MARKA ARAMASI  '{t['marka_arama']}': organik {mt} sonuç, {mb} tanesi {marka}")

        kayit = {"marka": marka, "marka_arama": t["marka_arama"],
                 "marka_bulunan": mb, "marka_toplam": mt, "kategoriler": []}
        for kk in t["kategori_aramalari"]:
            rk = kanal_trendyol.ara(kk)
            kb, kt = say(rk, marka)
            print(f"  KATEGORI ARAMA '{kk}': organik {kt} sonuç, {kb} tanesi {marka}")
            kayit["kategoriler"].append({"arama": kk, "bulunan": kb, "toplam": kt})
        sonuc.append(kayit)

    os.makedirs("cikti", exist_ok=True)
    with open("cikti/marka_vs_kategori.json", "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=1)

    print("\n" + "=" * 70)
    print("OZET: marka aramasinda gorunur, kategori aramasinda gorunmez mi?")
    print("=" * 70)
    for k in sonuc:
        kat_top = sum(c["bulunan"] for c in k["kategoriler"])
        tani = "GORUNMEZ" if kat_top == 0 and k["marka_bulunan"] > 0 else "gorunur"
        print(f"  {k['marka']:14s} | marka aramasi: {k['marka_bulunan']:3d} urun | "
              f"kategori aramasi: {kat_top:3d} urun | -> {tani}")
    print("\n-> cikti/marka_vs_kategori.json")
    return sonuc


if __name__ == "__main__":
    calistir()
