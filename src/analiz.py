# -*- coding: utf-8 -*-
# RafRadar - https://github.com/FlyerFukas/rafradar
# Copyright (c) 2026 Furkan Akduman. Dual-licensed: free for noncommercial use
# under PolyForm Noncommercial 1.0.0 (LICENSE); commercial use requires a
# separate paid license (COMMERCIAL.md).
"""Dijital Raf Skor Karti v3 - organik / sponsorlu ayrimli.

Perfect Store metodolojisinin dijital karsiligi. Dort temel metrik:
  BULUNURLUK   : İzlenen marka urunu organik sonuclarda var mi?
  GORUNURLUK   : Ilk 10 organik sonucta mi? (dijital goz hizasi)
  ORGANIK RAF PAYI : İzlenen marka urun sayisi / organik urun sayisi
  FIYAT ENDEKSI    : İzlenen marka medyan fiyat / kategori medyan fiyat

Ek metrik:
  REKLAM BASKISI : Vitrin/sponsorlu yerlesimlerin kim tarafindan alindigi.
"""
import sys, os, json, glob, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
from collections import Counter, defaultdict
from ayarlar import izlenen_marka, kategori_tipi, goz_hizasi, marka_adi

GOZ_HIZASI = goz_hizasi()

def yukle():
    d = sorted(glob.glob("veri/tarama_coklu_*.json"))
    if not d: raise SystemExit("Tarama yok. Once: py src/topla_coklu.py")
    return json.load(open(d[-1], encoding="utf-8"))

def _fiyat(u):
    return u.get("fiyat") or u.get("plus_fiyat")

def olc(urunler, sadece_organik=True):
    """sadece_organik=True ise vitrin/sponsorlu kartlar disarida birakilir."""
    havuz = [u for u in urunler if not (sadece_organik and u.get("sponsorlu"))]
    if not havuz: return None
    esli = [(u, izlenen_marka(u["marka"], u["ad"])) for u in havuz]
    izlenen = [(u, m) for u, m in esli if m]
    fiy = [f for u in havuz if (f := _fiyat(u))]
    bf  = [f for u, _ in izlenen if (f := _fiyat(u))]
    sira = [u.get("organik_sira") or u["sira"] for u, _ in izlenen]
    rakip = Counter(u["marka"] for u, m in esli
                    if not m and u["marka"] and u["marka"].lower() not in ("diğer", "diger", ""))
    return {
        "toplam": len(havuz), "izlenen": len(izlenen),
        "raf_payi": round(100 * len(izlenen) / len(havuz), 1),
        "bulunurluk": len(izlenen) > 0,
        "goz_hizasinda": sum(1 for s in sira if s and s <= GOZ_HIZASI),
        "en_iyi_sira": min(sira) if sira else None,
        "izlenen_medyan": round(statistics.median(bf), 2) if bf else None,
        "kategori_medyan": round(statistics.median(fiy), 2) if fiy else None,
        "fiyat_endeksi": round(statistics.median(bf) / statistics.median(fiy), 2) if bf and fiy else None,
        "rakipler": rakip.most_common(6),
        "izlenen_markalar": Counter(m for _, m in izlenen).most_common(),
    }

def calistir(yaz=True):
    veri = yukle()
    kat = defaultdict(list); kanal = defaultdict(lambda: defaultdict(list))
    arama = defaultdict(lambda: defaultdict(list)); sponsor = defaultdict(list)
    for k in veri["kayitlar"]:
        u = k.get("urunler") or []
        if not u: continue
        kat[k["kategori"]] += u
        kanal[k["kategori"]][k["kanal"]] += u
        arama[k["kategori"]][k["arama"]] += u
        sponsor[k["kategori"]] += [x for x in u if x.get("sponsorlu")]

    rapor = {"tarih": veri["tarih"], "kategoriler": {}, "ozet": {}}
    for k, urunler in kat.items():
        s = olc(urunler)
        if not s: continue
        s["tip"] = kategori_tipi(k)
        s["tum_dahil"] = olc(urunler, sadece_organik=False)
        s["kanallar"] = {kn: olc(uu) for kn, uu in kanal[k].items() if olc(uu)}
        s["aramalar"] = {a: olc(uu) for a, uu in arama[k].items() if olc(uu)}
        vit = sponsor[k]
        s["vitrin"] = {"adet": len(vit),
                       "markalar": Counter(u["marka"] for u in vit).most_common(5),
                       "izlenen_adet": sum(1 for u in vit if izlenen_marka(u["marka"], u["ad"]))}
        rapor["kategoriler"][k] = s

    acik = {k: v for k, v in rapor["kategoriler"].items() if v["tip"] == "izlenen"}
    if acik:
        rapor["ozet"] = {
            "kategori_sayisi": len(acik),
            "toplam_urun": sum(v["toplam"] for v in rapor["kategoriler"].values()),
            "ortalama_raf_payi": round(statistics.mean(v["raf_payi"] for v in acik.values()), 1),
            "sifir_kategoriler": [k for k, v in acik.items() if v["izlenen"] == 0],
            "goz_hizasi_yok": [k for k, v in acik.items() if v["izlenen"] > 0 and v["goz_hizasinda"] == 0],
        }
    if yaz:
        os.makedirs("cikti", exist_ok=True)
        yol = f"cikti/skor_{veri['tarih']}.json"
        json.dump(rapor, open(yol, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"-> {yol}\n")
    return rapor

def yazdir(rapor):
    acik = {k: v for k, v in rapor["kategoriler"].items() if v["tip"] == "izlenen"}
    o = rapor["ozet"]
    print("=" * 92)
    print(f"DIJITAL RAF SKOR KARTI  |  {rapor['tarih']}  |  {o.get('toplam_urun',0):,} urun  |  n11 + trendyol")
    print("=" * 92)
    print(f"\n{'Kategori':<17}{'Organik':>9}{'Tüm':>8}{'n11':>7}{'trendyol':>10}"
          f"{'Göz hiz.':>10}{'Fiyat':>8}   Rafı alan rakip")
    print("-" * 92)
    for k, s in sorted(acik.items(), key=lambda x: x[1]["raf_payi"]):
        kn = s["kanallar"]
        n11 = f"{kn['n11']['raf_payi']}%" if "n11" in kn else "-"
        ty = f"{kn['trendyol']['raf_payi']}%" if "trendyol" in kn else "-"
        rl = f"{s['rakipler'][0][0][:19]} ({s['rakipler'][0][1]})" if s["rakipler"] else "-"
        fe = f"{s['fiyat_endeksi']}x" if s["fiyat_endeksi"] else "-"
        td = f"{s['tum_dahil']['raf_payi']}%" if s["tum_dahil"] else "-"
        print(f"{k:<17}{s['raf_payi']:>8.1f}%{td:>8}{n11:>7}{ty:>10}"
              f"{str(s['goz_hizasinda'])+'/'+str(s['izlenen']):>10}{fe:>8}   {rl}")
    print(f"\nOrtalama organik raf payı: %{o.get('ortalama_raf_payi','-')}")
    if o.get("sifir_kategoriler"):
        print(f"SIFIR bulunurluk: {', '.join(o['sifir_kategoriler'])}")
    if o.get("goz_hizasi_yok"):
        print(f"Rafta var ama göz hizasında YOK: {', '.join(o['goz_hizasi_yok'])}")

    print("\n\n### ARAMA KELIMESI TUZAGI\n")
    for k, s in sorted(acik.items()):
        ar = sorted(s["aramalar"].items(), key=lambda x: x[1]["raf_payi"])
        if len(ar) < 2 or ar[-1][1]["raf_payi"] - ar[0][1]["raf_payi"] < 5: continue
        d, y = ar[0], ar[-1]
        print(f"{k}: '{d[0]}' %{d[1]['raf_payi']} ({d[1]['izlenen']}/{d[1]['toplam']})"
              f"  ->  '{y[0]}' %{y[1]['raf_payi']} ({y[1]['izlenen']}/{y[1]['toplam']})"
              f"  | fark {y[1]['raf_payi']-d[1]['raf_payi']:.1f} puan")

    print("\n\n### VITRIN / SPONSORLU YERLESIM (reklam baskisi)\n")
    for k, s in sorted(acik.items(), key=lambda x: -x[1]["vitrin"]["adet"]):
        v = s["vitrin"]
        if not v["adet"]: continue
        mk = ", ".join(f"{m}({n})" for m, n in v["markalar"][:3])
        print(f"{k:<17} {v['adet']:3d} vitrin kartı | İzlenen marka {v['izlenen_adet']} | alan: {mk}")

if __name__ == "__main__":
    yazdir(calistir())
