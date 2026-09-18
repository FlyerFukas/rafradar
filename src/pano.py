# -*- coding: utf-8 -*-
# RafRadar - https://github.com/FlyerFukas/rafradar
# Copyright (c) 2026 Furkan Akduman. Dual-licensed: free for noncommercial use
# under PolyForm Noncommercial 1.0.0 (LICENSE); commercial use requires a
# separate paid license (COMMERCIAL.md).
"""Skor JSON'undan tek sayfalik HTML pano uretir (Artifact formatinda)."""
import sys, os, json, glob, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
import ayarlar
from ayarlar import ad_goster, marka_adi, goz_hizasi

def oku(desen):
    d = sorted(glob.glob(desen))
    return json.load(open(d[-1], encoding="utf-8")) if d else None

skor = oku("cikti/skor_*.json")
mvk  = oku("cikti/marka_vs_kategori.json") or []
acik = {k: v for k, v in skor["kategoriler"].items() if v["tip"] == "izlenen"}
kapali = {k: v for k, v in skor["kategoriler"].items() if v["tip"] == "haric"}
ozet = skor["ozet"]
E = html.escape

def vir(deger, birim=""):
    """Turkce ondalik ayraci: 8.2 -> 8,2"""
    if deger is None: return "-"
    return f"{deger}".replace(".", ",") + birim

# ---------- SVG: kategori raf payi (yatay raf cubuklari) ----------
def raf_grafigi(veri):
    sirali = sorted(veri.items(), key=lambda x: x[1]["raf_payi"])
    satir_h, etiket_g, sag = 34, 148, 54
    gen, yuk = 720, len(sirali) * satir_h + 34
    olcek = gen - etiket_g - sag
    enb = 20  # eksen tavani %20
    p = [f'<svg viewBox="0 0 {gen} {yuk}" role="img" aria-label="Kategori bazlı organik dijital raf payı" style="width:100%;height:auto">']
    for t in range(0, enb + 1, 5):
        x = etiket_g + olcek * t / enb
        p.append(f'<line x1="{x:.1f}" y1="16" x2="{x:.1f}" y2="{len(sirali)*satir_h+16}" '
                 f'stroke="var(--cizgi)" stroke-width="1"/>')
        p.append(f'<text x="{x:.1f}" y="{yuk-4}" fill="var(--murekkep-3)" font-size="11" '
                 f'text-anchor="middle" font-family="var(--mono)">%{t}</text>')
    for i, (ad, s) in enumerate(sirali):
        y = 16 + i * satir_h
        pay = s["raf_payi"]
        w = max(olcek * pay / enb, 2.5)
        kritik = pay < 1
        renk = "var(--uyari)" if kritik else "var(--vurgu)"
        p.append(f'<text x="{etiket_g-10}" y="{y+16}" fill="var(--murekkep-2)" font-size="12.5" '
                 f'text-anchor="end">{E(ad_goster(ad))}</text>')
        p.append(f'<rect x="{etiket_g}" y="{y+5}" width="{olcek}" height="15" rx="2" fill="var(--raf-bos)"/>')
        p.append(f'<rect x="{etiket_g}" y="{y+5}" width="{w:.1f}" height="15" rx="2" fill="{renk}">'
                 f'<title>{E(ad_goster(ad))}: %{vir(pay)} organik raf payı: {s["izlenen"]}/{s["toplam"]} ürün</title></rect>')
        etk = "YOK" if kritik else f"%{vir(pay)}"
        p.append(f'<text x="{etiket_g+w+8:.1f}" y="{y+17}" fill="{renk}" font-size="12" '
                 f'font-weight="600" font-family="var(--mono)">{etk}</text>')
    p.append('</svg>')
    return "\n".join(p)

# ---------- SVG: marka aramasi vs kategori aramasi ----------
def mvk_grafigi(veri):
    if not veri: return ""
    gen, satir_h = 720, 68
    etiket_g, sag = 108, 60
    olcek = gen - etiket_g - sag
    enb = max(max(k["marka_bulunan"], sum(c["bulunan"] for c in k["kategoriler"])) for k in veri) or 1
    yuk = len(veri) * satir_h + 20
    p = [f'<svg viewBox="0 0 {gen} {yuk}" role="img" aria-label="Marka araması ve kategori araması karşılaştırması" style="width:100%;height:auto">']
    for i, k in enumerate(veri):
        y = 10 + i * satir_h
        kat = sum(c["bulunan"] for c in k["kategoriler"])
        kat_top = sum(c["toplam"] for c in k["kategoriler"])
        p.append(f'<text x="{etiket_g-12}" y="{y+30}" fill="var(--murekkep)" font-size="14" '
                 f'font-weight="600" text-anchor="end">{E(k["marka"])}</text>')
        for j, (deger, toplam, renk, etiket) in enumerate([
                (k["marka_bulunan"], k["marka_toplam"], "var(--vurgu)", "marka araması"),
                (kat, kat_top, "var(--uyari)", "kategori araması")]):
            yy = y + j * 24
            w = max(olcek * deger / enb, 1.5)
            p.append(f'<rect x="{etiket_g}" y="{yy+4}" width="{w:.1f}" height="15" rx="2" fill="{renk}">'
                     f'<title>{E(k["marka"])}, {etiket}: {deger} ürün / {toplam} organik sonuç</title></rect>')
            gosterim = f'{deger}' if deger else '0'
            p.append(f'<text x="{etiket_g+w+8:.1f}" y="{yy+16}" fill="{renk}" font-size="12" '
                     f'font-weight="600" font-family="var(--mono)">{gosterim}</text>')
            p.append(f'<text x="{etiket_g+w+34:.1f}" y="{yy+16}" fill="var(--murekkep-3)" '
                     f'font-size="10.5">{etiket}</text>')
    p.append('</svg>')
    return "\n".join(p)

# ---------- tablo satirlari ----------
def kategori_satirlari(veri):
    s = []
    for ad, k in sorted(veri.items(), key=lambda x: x[1]["raf_payi"]):
        kn = k["kanallar"]
        n11 = f'%{vir(kn["n11"]["raf_payi"])}' if "n11" in kn else "-"
        ty  = f'%{vir(kn["trendyol"]["raf_payi"])}' if "trendyol" in kn else "-"
        fe  = f'{vir(k["fiyat_endeksi"])}x' if k["fiyat_endeksi"] else "-"
        fe_sinif = "yuksek" if k["fiyat_endeksi"] and k["fiyat_endeksi"] > 1.4 else ""
        rl  = f'{k["rakipler"][0][0]} <span class="ufak">({k["rakipler"][0][1]})</span>' if k["rakipler"] else "-"
        gh  = f'{k["goz_hizasinda"]}/{k["izlenen"]}'
        gh_sinif = "kotu" if k["izlenen"] and k["goz_hizasinda"] == 0 else ""
        durum = ("kritik" if k["izlenen"] == 0 else "izle" if k["raf_payi"] < 8 else "iyi")
        rozet = {"kritik": "Bulunurluk yok", "izle": "İzlemede", "iyi": "Rafta"}[durum]
        s.append(f'''<tr>
 <th scope="row">{E(ad_goster(ad))}</th>
 <td class="sayi vurgulu">%{vir(k["raf_payi"])}</td>
 <td class="sayi">{n11}</td><td class="sayi">{ty}</td>
 <td class="sayi {gh_sinif}">{gh}</td>
 <td class="sayi {fe_sinif}">{fe}</td>
 <td>{rl}</td>
 <td><span class="rozet {durum}">{rozet}</span></td></tr>''')
    return "\n".join(s)

def vitrin_satirlari(veri):
    s = []
    for ad, k in sorted(veri.items(), key=lambda x: -x[1]["vitrin"]["adet"]):
        v = k["vitrin"]
        if not v["adet"]: continue
        mk = ", ".join(f'{m} <span class="ufak">({n})</span>' for m, n in v["markalar"][:3])
        sinif = "kotu" if v["izlenen_adet"] == 0 else ""
        s.append(f'<tr><th scope="row">{E(ad_goster(ad))}</th><td class="sayi">{v["adet"]}</td>'
                 f'<td class="sayi {sinif}">{v["izlenen_adet"]}</td><td>{mk}</td></tr>')
    return "\n".join(s)

def arama_tuzaklari(veri):
    s = []
    for ad, k in sorted(veri.items()):
        ar = sorted(k["aramalar"].items(), key=lambda x: x[1]["raf_payi"])
        if len(ar) < 2 or ar[-1][1]["raf_payi"] - ar[0][1]["raf_payi"] < 5: continue
        d, y = ar[0], ar[-1]
        s.append(f'''<div class="tuzak">
 <div class="tuzak-kat">{E(ad_goster(ad))}</div>
 <div class="tuzak-cift">
  <div class="tuzak-yan kotu-yan"><code>{E(d[0])}</code>
   <strong>%{vir(d[1]["raf_payi"])}</strong><span>{d[1]["izlenen"]}/{d[1]["toplam"]} ürün</span></div>
  <div class="tuzak-ok" aria-hidden="true">→</div>
  <div class="tuzak-yan iyi-yan"><code>{E(y[0])}</code>
   <strong>%{vir(y[1]["raf_payi"])}</strong><span>{y[1]["izlenen"]}/{y[1]["toplam"]} ürün</span></div>
 </div>
 <div class="tuzak-fark">Aynı kategori, {vir(round(y[1]["raf_payi"]-d[1]["raf_payi"],1))} puan fark</div></div>''')
    return "\n".join(s) or '<p class="bos">Bu taramada eşik üstü fark bulunmadı.</p>'



def aksiyonlar(acik, mvk):
    """Aksiyon maddelerini taramanin kendisinden uretir.

    Elle yazilmis oneri yoktur; her madde bir olcumun esigi asmasiyla dogar ve
    kaniti da o olcumden gelir. Veri baska turlu cikarsa madde de degisir.
    """
    marka = marka_adi()
    gh = goz_hizasi()
    maddeler = []

    # 1) Hic gorunmedigi kategoriler: kategori buyutme kanali tamamen kapali
    sifir = [k for k, v in acik.items() if v["izlenen"] == 0]
    if sifir:
        maddeler.append({
            "baslik": ("Bulunurluğun sıfır olduğu kategorileri açın"
                       if len(sifir) > 1 else f"{sifir[0]} kategorisinde hiç görünmüyorsunuz"),
            "metin": (f"{', '.join(sifir)} kategorisinde tek bir {marka} ürünü organik "
                      "sonuçlara girmiyor. Markayı arayan bulur, kategoriyi arayan bulamaz; "
                      "yani yeni müşteri kazanma kanalı bu kategoride kapalı."),
            "kanit": " · ".join(f"{k}: {acik[k]['toplam']} organik sonuçta 0 ürün" for k in sifir),
        })

    # 2) Arama kelimesi tuzagi: ayni kategori, kelimeye gore ucurum
    en_fark, tuzak = 0, None
    for k, v in acik.items():
        ar = sorted(v["aramalar"].items(), key=lambda x: x[1]["raf_payi"])
        if len(ar) < 2:
            continue
        fark = ar[-1][1]["raf_payi"] - ar[0][1]["raf_payi"]
        if fark > en_fark:
            en_fark, tuzak = fark, (k, ar[0], ar[-1])
    if tuzak and en_fark >= 5:
        k, dusuk, yuksek = tuzak
        maddeler.append({
            "baslik": "Ürün başlıklarına kategori terimini ekleyin",
            "metin": (f"Aynı kategoride arama kelimesi değişince payınız {en_fark:.1f} puan "
                      "oynuyor. Bunun sebebi sıralama değil, başlık eşleşmesi: ürün adında o "
                      "kelime geçmiyorsa o aramada görünmüyorsunuz. Başlık içeriği sizin "
                      "kontrolünüzde olduğu için maliyetsiz ve en hızlı kazanç burada."),
            "kanit": (f"{k}: “{dusuk[0]}” aramasında %{dusuk[1]['raf_payi']} · "
                      f"“{yuksek[0]}” aramasında %{yuksek[1]['raf_payi']}"),
        })

    # 3) Rafta var ama goz hizasinda yok: bulunurluk degil siralama sorunu
    korler = [(k, v) for k, v in acik.items() if v["izlenen"] > 0 and v["goz_hizasinda"] == 0]
    if korler:
        k, v = max(korler, key=lambda x: x[1]["izlenen"])
        maddeler.append({
            "baslik": f"{k} kategorisinde sıralama sorununu çözün",
            "metin": (f"Ürünler listede var ama hiçbiri ilk {gh} organik sonuca giremiyor. "
                      "Bu bir bulunurluk değil sıralama problemi; yorum sayısı, satıcı puanı "
                      "ve başlık uyumu ile çalışılır."),
            "kanit": f"{k}: {v['izlenen']} ürün listede, ilk {gh} sonuçta 0",
        })

    # 4) Vitrin alanini rakip aliyor
    vitrinli = [(k, v) for k, v in acik.items()
                if v["vitrin"]["adet"] >= 10 and v["vitrin"]["izlenen_adet"] == 0]
    if vitrinli:
        k, v = max(vitrinli, key=lambda x: x[1]["vitrin"]["adet"])
        lider = v["vitrin"]["markalar"][0] if v["vitrin"]["markalar"] else ("-", 0)
        maddeler.append({
            "baslik": "Vitrin bütçesini kategori aramalarına kaydırın",
            "metin": ("Arama sayfalarındaki vitrin blokları satın alınan alandır ve bu "
                      "kategoride tamamını rakipler almış. Marka aramasında zaten "
                      "birincisiniz; vitrin, markasını henüz seçmemiş alışverişçinin "
                      "olduğu kategori aramalarında değerlidir."),
            "kanit": (f"{k}: {v['vitrin']['adet']} vitrin kartının 0'ı {marka} · "
                      f"en çok alan: {lider[0]} ({lider[1]})"),
        })

    # 5) Fiyat konumu kategori medyanindan belirgin sapiyor
    sapan = [(k, v) for k, v in acik.items()
             if v["fiyat_endeksi"] and (v["fiyat_endeksi"] >= 1.4 or v["fiyat_endeksi"] <= 0.7)]
    if sapan:
        k, v = max(sapan, key=lambda x: abs((x[1]["fiyat_endeksi"] or 1) - 1))
        e = v["fiyat_endeksi"]
        yon = "üstünde" if e > 1 else "altında"
        maddeler.append({
            "baslik": f"{k} kategorisinde fiyat konumunu gözden geçirin",
            "metin": (f"Medyan fiyatınız kategori medyanının belirgin {yon}. Bilinçli bir "
                      "konumlandırmaysa iletişimin bunu taşıması gerekir; değilse paket boyu "
                      "ve kanal fiyatı incelenmelidir."),
            "kanit": (f"{k}: fiyat endeksi {str(e).replace('.', ',')}x "
                      f"({v['izlenen_medyan']} TL / kategori medyanı {v['kategori_medyan']} TL)"),
        })

    if not maddeler:
        return ('<li><strong>Belirgin bir açık görünmüyor</strong>'
                '<p>Bu taramada eşik aşan bir bulgu çıkmadı. Kategori ve arama kelimesi '
                'listesini genişletmek ya da taramayı düzenli tekrarlayıp trendi izlemek '
                'daha anlamlı olacaktır.</p></li>')

    return "\n".join(
        f'<li><strong>{E(m["baslik"])}</strong><p>{E(m["metin"])}</p>'
        f'<div class="kanit">Kanıt: {E(m["kanit"])}</div></li>'
        for m in maddeler[:5]
    )


def baslik_bulgu(bm):
    """Marka aramasi ile kategori aramasi arasindaki farki tek blokta anlatir.

    Metin sabit degil: kategori aramasinda hic urun yoksa "tek bir X yok",
    varsa "sadece N tanesi X" denir. Yanlis iddia uretmemesi icin sayilar
    dogrudan olcumden gelir.
    """
    if not bm:
        return ""
    marka = bm.get("marka", "")
    kategoriler = bm.get("kategoriler") or [{}]
    # En dusuk gorunurluge sahip kategori aramasi secilir: kontrast en nettir.
    kat = min(kategoriler, key=lambda c: (c.get("bulunan", 0), -c.get("toplam", 0)))
    kb, kt = kat.get("bulunan", 0), kat.get("toplam", 0)
    ma, mb = bm.get("marka_arama", ""), bm.get("marka_bulunan", 0)

    if kb == 0:
        cumle = (f"<em>&ldquo;{E(kat.get('arama',''))}&rdquo;</em> yazarsanız {kt} sonu&ccedil;ta "
                 f"tek bir {E(marka)} yok.")
        alt = f"{kt} organik sonu&ccedil;ta hi&ccedil; yok"
        sinif = " sifir"
    else:
        cumle = (f"<em>&ldquo;{E(kat.get('arama',''))}&rdquo;</em> yazarsanız {kt} sonucun "
                 f"yalnızca {kb} tanesi {E(marka)}.")
        alt = f"{kt} organik sonu&ccedil;tan {kb} tanesi"
        sinif = " sifir" if kb <= 2 else ""

    ikinci = ("Markayı zaten bilen buluyor; bilmeyen bulamıyor."
              if kb == 0 else
              "Markayı arayan buluyor; kategoriyi arayan neredeyse hi&ccedil; g&ouml;rm&uuml;yor.")

    return f'''<section class="bulgu">
  <div class="etiket">Başlık bulgu</div>
  <p>Aramada <em>&ldquo;{E(ma)}&rdquo;</em> yazarsanız {mb} &uuml;r&uuml;n &ccedil;ıkıyor.
     {cumle}<br>{ikinci}</p>
  <div class="kiyas">
    <div class="kiyas-kutu"><code>arama: &ldquo;{E(ma)}&rdquo;</code>
      <div class="rakam">{mb}</div><small>{E(marka)} &uuml;r&uuml;n&uuml; listeleniyor</small></div>
    <div class="kiyas-kutu{sinif}"><code>arama: &ldquo;{E(kat.get("arama",""))}&rdquo;</code>
      <div class="rakam">{kb}</div><small>{alt}</small></div>
  </div>
</section>'''

# basligi tasiyan bulgu
# Kategori aramasinda hic gorunmeyen markalar arasindan, marka aramasindaki
# urun sayisi EN YUKSEK olani sec: kontrast ne kadar buyukse bulgu o kadar carpici.
_adaylar = [k for k in mvk
            if sum(c["bulunan"] for c in k["kategoriler"]) == 0 and k["marka_bulunan"] > 0]
kritik_marka = max(_adaylar, key=lambda k: k["marka_bulunan"]) if _adaylar else None

# ---------- sablonu doldur ----------
ham = oku("veri/tarama_coklu_*.json")
arama_sayisi = len(ham["kayitlar"]) if ham else 0

bm = kritik_marka or (mvk[0] if mvk else {})
bm_kat = (bm.get("kategoriler") or [{}])[0]
toplam_urun = sum(v["toplam"] for v in skor["kategoriler"].values())

degerler = {
    "__TARIH__": skor["tarih"],
    "__ARAMA__": str(arama_sayisi),
    "__TOPLAM_URUN__": f"{toplam_urun:,}".replace(",", "."),
    "__ORT_PAY__": str(ozet.get("ortalama_raf_payi", "-")).replace(".", ","),
    "__KAT_SAYI__": str(len(acik)),
    "__SIFIR_SAYI__": str(len(ozet.get("sifir_kategoriler", []))),
    "__BM_AD__": bm.get("marka", ""),
    "__BMS__": str(bm.get("marka_bulunan", 0)),
    "__BM__": bm.get("marka_arama", ""),
    "__BKA__": bm_kat.get("arama", ""),
    "__BKT__": str(bm_kat.get("toplam", 0)),
    "__RAF_GRAFIK__": raf_grafigi(acik),
    "__MVK_GRAFIK__": mvk_grafigi(mvk),
    "__KATEGORI_SATIRLARI__": kategori_satirlari(acik),
    "__VITRIN_SATIRLARI__": vitrin_satirlari(acik),
    "__TUZAKLAR__": arama_tuzaklari(acik),
    "__AKSIYONLAR__": aksiyonlar(acik, mvk),
    "__BASLIK_BULGU__": baslik_bulgu(bm),
    "__MARKA__": marka_adi(),
    "__PAZAR__": ayarlar.yukle()["pazar"],
    "__GOZ__": str(goz_hizasi()),
    "__HAZIRLAYAN__": (("Hazırlayan: " + ayarlar.yukle()["hazirlayan"] + " · ")
                       if ayarlar.yukle().get("hazirlayan") else ""),
    "__META_HAZIRLAYAN__": ("<span>Hazırlayan: <b>" + E(ayarlar.yukle()["hazirlayan"])
                            + "</b></span>") if ayarlar.yukle().get("hazirlayan") else "",
}

# Gezilebilir katmanin verisi: yoksa uretilir, sonra sablona gomulur
import pano_veri
if not os.path.exists("cikti/kesif_verisi.json"):
    pano_veri.uret()
degerler["__KESIF_VERISI__"] = open("cikti/kesif_verisi.json", encoding="utf-8").read()

kok = os.path.dirname(os.path.abspath(__file__))
sayfa = open(os.path.join(kok, "sablon.html"), encoding="utf-8").read()
for anahtar, deger in degerler.items():
    sayfa = sayfa.replace(anahtar, deger)

kalan = [a for a in degerler if a in sayfa]
if kalan:
    print("UYARI - doldurulmamis yer tutucu:", kalan)

os.makedirs("cikti", exist_ok=True)
open("cikti/pano.html", "w", encoding="utf-8").write(sayfa)
print(f"-> cikti/pano.html ({len(sayfa):,} karakter)")
_k = min((bm.get("kategoriler") or [{}]),
         key=lambda c: (c.get("bulunan", 0), -c.get("toplam", 0)))
print(f"   baslik bulgu: {bm.get('marka')} | marka aramasi {bm.get('marka_bulunan')} urun"
      f" vs '{_k.get('arama')}' aramasi {_k.get('bulunan')}/{_k.get('toplam')}")
print(f"   kategori: {len(acik)} | ortalama organik pay: %{ozet.get('ortalama_raf_payi')}"
      f" | toplam urun: {toplam_urun}")
