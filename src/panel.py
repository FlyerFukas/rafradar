# -*- coding: utf-8 -*-
# RafRadar - https://github.com/FlyerFukas/rafradar
# Copyright (c) 2026 Furkan Akduman. Dual-licensed: free for noncommercial use
# under PolyForm Noncommercial 1.0.0 (LICENSE); commercial use requires a
# separate paid license (COMMERCIAL.md).
"""RafRadar - yerel kontrol paneli.

Komut satırı yerine tarayıcıdan çalıştırmak için. Ek kütüphane gerektirmez;
yalnızca Python standart kütüphanesi kullanılır.

    py src/panel.py

Tarayıcı otomatik açılır: http://localhost:8000
"""
import http.server
import re
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ayarlar

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(KOK, "src")
PORT = 8000
LOG_SINIRI = 300

durum = {
    "calisiyor": False,
    "adim": None,
    "log": [],
    "baslangic": None,
    "bitis": None,
    "hata": False,
}
kilit = threading.Lock()


def chrome_bul():
    adaylar = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for y in adaylar:
        if os.path.exists(y):
            return y
    return shutil.which("chrome") or shutil.which("msedge")


def rapor_dosyasi():
    """Rapor adi izlenen markadan turetilir: 'Solgar-dijital-raf.pdf' gibi."""
    ad = ayarlar.marka_adi()
    temiz = re.sub(r"[^0-9A-Za-zÇĞİÖŞÜçğıöşü]+", "-", ad).strip("-")
    kars = str.maketrans("ÇĞİÖŞÜçğıöşü", "CGIOSUcgiosu")
    return (temiz.translate(kars) or "rapor") + "-dijital-raf.pdf"


def rapor_komutu():
    tarayici = chrome_bul()
    if not tarayici:
        return None
    return [
        tarayici, "--headless", "--disable-gpu", "--no-sandbox",
        "--no-pdf-header-footer", "--virtual-time-budget=9000",
        "--print-to-pdf=" + os.path.join(KOK, "cikti", rapor_dosyasi()),
        "file:///" + os.path.join(KOK, "cikti", "pano.html").replace("\\", "/"),
    ]


def _arama_sayisi():
    a = ayarlar.yukle()
    return sum(len(v.get("aramalar", [])) for v in a["kategoriler"].values()) * len(a["kanallar"])


def tarama_aciklamasi():
    a = ayarlar.yukle()
    return (", ".join(k.title() for k in a["kanallar"]) + " üzerinde "
            + str(_arama_sayisi()) + " arama yürütür, ürünleri kaydeder")


def tarama_suresi():
    dk = max(1, round(_arama_sayisi() * 9 / 60))
    return "yaklaşık " + str(dk) + " dakika"


ADIMLAR = {
    "tarama": {
        "ad": "Tarama",
        "aciklama": tarama_aciklamasi(),
        "sure": tarama_suresi(),
        "komut": lambda: [sys.executable, os.path.join(SRC, "topla.py")],
        "cikti": "veri/tarama_coklu_TARIH.json",
    },
    "analiz": {
        "ad": "Analiz",
        "aciklama": "Hariç tutulanları ayırır, vitrini organikten ayrıştırır, metrikleri hesaplar",
        "sure": "birkaç saniye",
        "komut": lambda: [sys.executable, os.path.join(SRC, "analiz.py")],
        "cikti": "cikti/skor_TARIH.json",
    },
    "marka": {
        "ad": "Marka testi",
        "aciklama": "Marka araması ile kategori aramasını karşılaştırır",
        "sure": "yaklaşık 2 dakika",
        "komut": lambda: [sys.executable, os.path.join(SRC, "marka_vs_kategori.py")],
        "cikti": "cikti/marka_vs_kategori.json",
    },
    "pano": {
        "ad": "Pano",
        "aciklama": "Hesaplanan skorlardan HTML panoyu üretir",
        "sure": "birkaç saniye",
        "komut": lambda: [sys.executable, os.path.join(SRC, "pano.py")],
        "cikti": "cikti/pano.html",
    },
    "rapor": {
        "ad": "PDF rapor",
        "aciklama": "Panodan baskıya uygun PDF üretir",
        "sure": "birkaç saniye",
        "komut": rapor_komutu,
        "cikti": "cikti/" + rapor_dosyasi(),
    },
}

ZINCIR = ["tarama", "analiz", "marka", "pano", "rapor"]

# Hangi adim hangi adimin ciktisina dayaniyor. Bir adimin ciktisi, dayandigi
# adimin ciktisindan ESKIYSE bayattir: veri tazelendigi halde o adim yeniden
# calistirilmamis demektir. Panoyu tarama sonrasi guncellemeyi unutmak en sik
# yapilan hata oldugu icin arayuzde uyari gosterilir.
BAGIMLILIK = {
    "analiz": ["tarama"],
    "pano": ["analiz", "marka"],
    "rapor": ["pano"],
}


def logla(satir):
    with kilit:
        durum["log"].append(satir)
        if len(durum["log"]) > LOG_SINIRI:
            del durum["log"][:-LOG_SINIRI]


def tek_adim(anahtar):
    bilgi = ADIMLAR[anahtar]
    komut = bilgi["komut"]()
    if not komut:
        logla("[hata] Chrome veya Edge bulunamadı, PDF üretilemiyor.")
        return False

    logla("")
    logla("=" * 60)
    logla(">>> " + bilgi["ad"] + " başlatıldı (" + bilgi["sure"] + ")")
    logla("=" * 60)

    try:
        surec = subprocess.Popen(
            komut, cwd=KOK, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
        )
    except Exception as e:
        logla("[hata] " + type(e).__name__ + ": " + str(e))
        return False

    for satir in surec.stdout:
        satir = satir.rstrip()
        if satir:
            logla(satir)
    surec.wait()

    if surec.returncode == 0:
        logla("[tamam] " + bilgi["ad"] + " bitti -> " + bilgi["cikti"])
        return True
    logla("[hata] " + bilgi["ad"] + " çıkış kodu " + str(surec.returncode))
    return False


def calistir(adimlar):
    with kilit:
        if durum["calisiyor"]:
            return
        durum.update({"calisiyor": True, "log": [], "hata": False,
                      "baslangic": time.time(), "bitis": None})

    basarili = True
    for anahtar in adimlar:
        with kilit:
            durum["adim"] = anahtar
        if not tek_adim(anahtar):
            basarili = False
            break

    logla("")
    logla("### " + ("Tüm adımlar tamamlandı." if basarili else "Akış hatayla durdu."))
    with kilit:
        durum.update({"calisiyor": False, "adim": None,
                      "bitis": time.time(), "hata": not basarili})


def dosya_bilgisi():
    import glob
    bilgi = {}
    esleme = {
        "tarama": "veri/tarama_coklu_*.json",
        "analiz": "cikti/skor_*.json",
        "marka": "cikti/marka_vs_kategori.json",
        "pano": "cikti/pano.html",
        "rapor": "cikti/*.pdf",
    }
    for anahtar, desen in esleme.items():
        bulunan = sorted(glob.glob(os.path.join(KOK, desen)))
        if bulunan:
            yol = bulunan[-1]
            st = os.stat(yol)
            bilgi[anahtar] = {
                "dosya": os.path.relpath(yol, KOK).replace("\\", "/"),
                "kb": round(st.st_size / 1024),
                "zaman": time.strftime("%d.%m.%Y %H:%M", time.localtime(st.st_mtime)),
                "mtime": st.st_mtime,
            }
        else:
            bilgi[anahtar] = None

    for anahtar, kaynaklar in BAGIMLILIK.items():
        hedef = bilgi.get(anahtar)
        if not hedef:
            continue
        eskiler = [k for k in kaynaklar
                   if bilgi.get(k) and bilgi[k]["mtime"] > hedef["mtime"]]
        hedef["bayat"] = bool(eskiler)
        hedef["bayat_kaynak"] = [ADIMLAR[k]["ad"] for k in eskiler]
    return bilgi


class Sunucu(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass  # konsolu kirletme

    def _gonder(self, kod, tur, govde, indir=None):
        self.send_response(kod)
        self.send_header("Content-Type", tur)
        self.send_header("Content-Length", str(len(govde)))
        self.send_header("Cache-Control", "no-store, must-revalidate")
        if indir:
            self.send_header("Content-Disposition", 'attachment; filename="' + indir + '"')
        self.end_headers()
        self.wfile.write(govde)

    def _dosya(self, gorece, tur, indir=None):
        yol = os.path.join(KOK, gorece)
        if not os.path.exists(yol):
            self._gonder(404, "text/plain; charset=utf-8",
                         "Dosya henüz üretilmedi.".encode("utf-8"))
            return
        with open(yol, "rb") as f:
            self._gonder(200, tur, f.read(), indir)

    def do_GET(self):
        yol = urlparse(self.path).path
        if yol in ("/", "/index.html"):
            with open(os.path.join(SRC, "panel.html"), encoding="utf-8") as f:
                self._gonder(200, "text/html; charset=utf-8", f.read().encode("utf-8"))
        elif yol == "/api/durum":
            with kilit:
                veri = {
                    "calisiyor": durum["calisiyor"],
                    "adim": durum["adim"],
                    "log": durum["log"][-LOG_SINIRI:],
                    "hata": durum["hata"],
                    "gecen": round(time.time() - durum["baslangic"]) if durum["baslangic"] and durum["calisiyor"] else None,
                }
            veri["dosyalar"] = dosya_bilgisi()
            veri["adimlar"] = [
                {"anahtar": a, "ad": ADIMLAR[a]["ad"],
                 "aciklama": ADIMLAR[a]["aciklama"], "sure": ADIMLAR[a]["sure"]}
                for a in ZINCIR
            ]
            self._gonder(200, "application/json; charset=utf-8",
                         json.dumps(veri, ensure_ascii=False).encode("utf-8"))
        elif yol == "/pano":
            self._dosya("cikti/pano.html", "text/html; charset=utf-8")
        elif yol == "/rapor":
            self._dosya("cikti/" + rapor_dosyasi(), "application/pdf",
                        indir=rapor_dosyasi())
        else:
            self._gonder(404, "text/plain; charset=utf-8", b"yok")

    def do_POST(self):
        yol = urlparse(self.path)
        if yol.path != "/api/calistir":
            self._gonder(404, "text/plain; charset=utf-8", b"yok")
            return
        sorgu = parse_qs(yol.query)
        adim = (sorgu.get("adim") or ["hepsi"])[0]

        with kilit:
            mesgul = durum["calisiyor"]
        if mesgul:
            self._gonder(409, "application/json; charset=utf-8",
                         json.dumps({"hata": "Zaten bir işlem çalışıyor."},
                                    ensure_ascii=False).encode("utf-8"))
            return

        adimlar = ZINCIR if adim == "hepsi" else [adim] if adim in ADIMLAR else None
        if not adimlar:
            self._gonder(400, "application/json; charset=utf-8",
                         json.dumps({"hata": "Bilinmeyen adım."},
                                    ensure_ascii=False).encode("utf-8"))
            return

        threading.Thread(target=calistir, args=(adimlar,), daemon=True).start()
        self._gonder(200, "application/json; charset=utf-8",
                     json.dumps({"baslatildi": adimlar}, ensure_ascii=False).encode("utf-8"))


def main():
    os.chdir(KOK)

    # Port mesgulse (panel zaten acikysa veya baska bir uygulama kullaniyorsa)
    # sirayla bir sonrakini dene; kullanici hata mesajiyla ugrasmasin.
    sunucu = None
    for port in range(PORT, PORT + 12):
        try:
            sunucu = http.server.ThreadingHTTPServer(("127.0.0.1", port), Sunucu)
            break
        except OSError:
            continue
    if sunucu is None:
        print("Uygun port bulunamadi (" + str(PORT) + "-" + str(PORT + 11) + " arasi dolu).")
        print("Acik panelleri kapatip tekrar deneyin.")
        input("Kapatmak icin Enter...")
        return

    adres = "http://localhost:" + str(sunucu.server_address[1])
    print("RafRadar kontrol paneli çalışıyor - izlenen marka: " + ayarlar.marka_adi())
    print("   " + adres)
    print("   Durdurmak için: Ctrl+C")
    try:
        webbrowser.open(adres)
    except Exception:
        pass
    try:
        sunucu.serve_forever()
    except KeyboardInterrupt:
        print("\nPanel kapatıldı.")
        sunucu.shutdown()


if __name__ == "__main__":
    main()
