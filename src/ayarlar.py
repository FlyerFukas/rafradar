# -*- coding: utf-8 -*-
"""Yapılandırma yükleyici.

Marka, kategori ve arama kelimeleri koda gömülü değildir; `yapilandirma/`
altındaki bir JSON dosyasından okunur. Böylece araç herhangi bir marka ve
sektör için çalıştırılabilir.

Hangi dosyanın kullanılacağı sırayla şöyle belirlenir:
  1. RAFRADAR_AYAR ortam değişkeni (dosya yolu)
  2. yapilandirma/aktif.json
  3. yapilandirma/ornek-*.json içinden ilki
"""
import glob
import json
import os

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AYAR_KLASORU = os.path.join(KOK, "yapilandirma")

_onbellek = None


def _dosya_bul():
    ortam = os.environ.get("RAFRADAR_AYAR")
    if ortam and os.path.exists(ortam):
        return ortam
    aktif = os.path.join(AYAR_KLASORU, "aktif.json")
    if os.path.exists(aktif):
        return aktif
    ornekler = sorted(glob.glob(os.path.join(AYAR_KLASORU, "ornek-*.json")))
    if ornekler:
        return ornekler[0]
    raise SystemExit(
        "Yapılandırma bulunamadı. yapilandirma/aktif.json oluşturun "
        "veya yapilandirma/ornek-*.json dosyalarından birini kopyalayın."
    )


def yukle(yeniden=False):
    """Yapılandırmayı okur ve doğrular."""
    global _onbellek
    if _onbellek is not None and not yeniden:
        return _onbellek

    yol = _dosya_bul()
    with open(yol, encoding="utf-8") as f:
        a = json.load(f)

    eksik = [k for k in ("ad", "markalar", "kategoriler") if k not in a]
    if eksik:
        raise SystemExit(
            os.path.basename(yol) + " içinde zorunlu alan eksik: " + ", ".join(eksik)
        )
    if not a["kategoriler"]:
        raise SystemExit("En az bir kategori tanımlanmalı.")

    a.setdefault("haric_markalar", {})
    a.setdefault("kanallar", ["n11", "trendyol"])
    a.setdefault("goz_hizasi", 10)
    a.setdefault("pazar", "Türkiye")
    a.setdefault("hazirlayan", "")
    a["_dosya"] = os.path.relpath(yol, KOK).replace("\\", "/")

    # Anahtar kelime -> marka eşlemesi. Uzun anahtarlar önce denenir ki
    # "bepanthol baby" gibi bir ifade "bepanthol"dan önce eşleşebilsin.
    esleme = []
    for marka, anahtarlar in a["markalar"].items():
        for k in anahtarlar:
            esleme.append((k.lower(), marka, False))
    for marka, bilgi in a["haric_markalar"].items():
        for k in bilgi.get("anahtarlar", []):
            esleme.append((k.lower(), marka, True))
    a["_esleme"] = sorted(esleme, key=lambda x: -len(x[0]))

    _onbellek = a
    return a


def izlenen_marka(marka_alani, urun_adi=""):
    """Ürün, izlenen markalardan birine ait mi? Ait değilse None.

    Sitelerin marka alanı güvenilmez olabildiği için ürün adında da aranır.
    Hariç tutulan markalar (ör. mevzuat gereği satılamayanlar) None döner;
    onlar `haric_marka` ile ayrıca sorgulanır.
    """
    a = yukle()
    metin = ((marka_alani or "") + " " + (urun_adi or "")).lower()
    for anahtar, marka, haric in a["_esleme"]:
        if anahtar in metin:
            return None if haric else marka
    return None


def haric_marka(marka_alani, urun_adi=""):
    """Ürün, bilinçli olarak analiz dışı bırakılan bir markaya mı ait?"""
    a = yukle()
    metin = ((marka_alani or "") + " " + (urun_adi or "")).lower()
    for anahtar, marka, haric in a["_esleme"]:
        if anahtar in metin:
            return marka if haric else None
    return None


def kategori_tipi(kategori):
    """'izlenen'  : kategoride izlenen bir marka yarışıyor
    'haric'   : kategorideki markalar bilinçli olarak analiz dışı
    """
    a = yukle()
    bilgi = a["kategoriler"].get(kategori, {})
    markalar = bilgi.get("markalar", [])
    if not markalar:
        return "izlenen"
    if all(m in a["haric_markalar"] for m in markalar):
        return "haric"
    return "izlenen"


def haric_sebep(kategori):
    a = yukle()
    markalar = a["kategoriler"].get(kategori, {}).get("markalar", [])
    for m in markalar:
        bilgi = a["haric_markalar"].get(m)
        if bilgi and bilgi.get("sebep"):
            return bilgi["sebep"]
    return ""


def ad_goster(kategori):
    """Kategori anahtarı zaten görünen addır; ileride ayrışırsa buradan yönetilir."""
    return kategori


def kategoriler(sadece_izlenen=False):
    a = yukle()
    if not sadece_izlenen:
        return a["kategoriler"]
    return {k: v for k, v in a["kategoriler"].items() if kategori_tipi(k) == "izlenen"}


def goz_hizasi():
    return yukle()["goz_hizasi"]


def marka_adi():
    return yukle()["ad"]


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    a = yukle()
    print("Yapılandırma :", a["_dosya"])
    print("İzlenen taraf:", a["ad"], "| pazar:", a["pazar"])
    print("Markalar     :", ", ".join(a["markalar"]))
    if a["haric_markalar"]:
        print("Hariç        :", ", ".join(a["haric_markalar"]))
    print("Kanallar     :", ", ".join(a["kanallar"]))
    print("Göz hizası   : ilk", a["goz_hizasi"], "organik sonuç")
    print()
    for k in a["kategoriler"]:
        tip = kategori_tipi(k)
        aramalar = a["kategoriler"][k].get("aramalar", [])
        print(f"  {k:22s} [{tip:7s}] {len(aramalar)} arama: " + ", ".join(aramalar[:3]))
