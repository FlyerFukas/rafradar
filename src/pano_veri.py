# -*- coding: utf-8 -*-
"""Panoya gomulecek kompakt kesif verisi uretir.

Ham tarama 1,1 MB; panoya oldugu gibi gomulmez. Burada her urun
dizi olarak sikistirilir: [sira, marka, ad, fiyat, izlenenMarka, sponsorlu, kanal]
"""
import sys, os, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
from collections import defaultdict
import re
from ayarlar import izlenen_marka, kategori_tipi, ad_goster, marka_adi, goz_hizasi, goz_hizasi, marka_adi

# Trendyol siralama rozetleri ve promosyon etiketleri urun adina yapisir;
# mevcut ham veri icin gosterim katmaninda temizlenir.
ROZET = re.compile(r"^(?:En(?:\s+Çok\s+[\wçğıöşüÇĞİÖŞÜ]+(?:\s+[\wçğıöşüÇĞİÖŞÜ]+)?)?\s+\d+\.\s*Ürün\s*)+",
                   re.IGNORECASE)
EK_ETIKET = ("Süper Fırsat Ürünü", "Başarılı Satıcı", "Yetkili Satıcı", "Çok Al Az Öde",
             "Sepette İndirim", "Kupon Fırsatı")


# Trendyol urun adinin SONUNA satis rozeti ekliyor:
#   "... 30 Tablet 🚀 3 günde 1,7B kişi ekledi! 4.6 ( 3976 )"
# Bunlar urun adinin parcasi degil; emojiden itibaren kesilir, ayrica
# emoji kullanilmayan varyantlari da desenle temizlenir.
EMOJI = re.compile("[🌀-🫿☀-➿⬀-⯿️]")
KUYRUK = re.compile(
    r"\s*(?:"
    r"Son\s+\d+\s+g[üu]n\w*.*"
    r"|\d+\s*g[üu]nde\s+.*"
    r"|[\d.,]+\s*B?\s*ki[şs]i\s+.*"
    r"|\d[.,]\d\s*\(\s*\d+\s*\).*"
    r")$", re.IGNORECASE)


def rozet_kuyrugu_at(ad):
    """Urun adinin sonundaki satis/populerlik rozetlerini atar."""
    m = EMOJI.search(ad)
    if m:
        ad = ad[:m.start()]
    onceki = None
    while onceki != ad:            # birden fazla rozet ust uste gelebiliyor
        onceki = ad
        ad = KUYRUK.sub("", ad).strip(" -|·,")
    return ad.strip()


def ad_temizle(ad):
    for e in EK_ETIKET:
        ad = ad.replace(e, " ")
    ad = re.sub(r"\s+", " ", ad).strip()
    return rozet_kuyrugu_at(ROZET.sub("", ad).strip())

def uret():
    d = sorted(glob.glob("veri/tarama_coklu_*.json"))
    if not d: raise SystemExit("Tarama dosyasi yok.")
    veri = json.load(open(d[-1], encoding="utf-8"))

    kat = defaultdict(lambda: defaultdict(list))   # kategori -> arama -> kayitlar
    for k in veri["kayitlar"]:
        if not k.get("urunler"): continue
        if kategori_tipi(k["kategori"]) != "izlenen": continue
        for u in k["urunler"]:
            marka = izlenen_marka(u["marka"], u["ad"])
            kat[k["kategori"]][k["arama"]].append([
                u.get("organik_sira") or u["sira"],
                (u.get("marka") or "")[:28],
                ad_temizle(u.get("ad") or "")[:95],
                u.get("fiyat") or u.get("plus_fiyat"),
                marka,
                1 if u.get("sponsorlu") else 0,
                k["kanal"][0],           # 'n' veya 't'
            ])

    cikti = {"tarih": veri["tarih"], "marka": marka_adi(),
             "goz_hizasi": goz_hizasi(), "kategoriler": {}}
    for k, aramalar in kat.items():
        cikti["kategoriler"][ad_goster(k)] = {
            # kanala gore grupla (Trendyol once), sonra vitrin/organik, sonra sira:
            # iki kanal birlikte gosterilirken sira numaralari tekrar etmesin
            a: sorted(kayitlar, key=lambda x: (x[6] != "t", x[5], x[0]))
            for a, kayitlar in aramalar.items()
        }
    yol = "cikti/kesif_verisi.json"
    json.dump(cikti, open(yol, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    boyut = os.path.getsize(yol)
    toplam = sum(len(v) for a in cikti["kategoriler"].values() for v in a.values())
    print(f"-> {yol} ({boyut/1024:.0f} KB) | {len(cikti['kategoriler'])} kategori, "
          f"{sum(len(a) for a in cikti['kategoriler'].values())} arama, {toplam} urun")
    return yol

if __name__ == "__main__":
    uret()
