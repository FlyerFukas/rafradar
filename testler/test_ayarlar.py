# -*- coding: utf-8 -*-
# RafRadar - https://github.com/FlyerFukas/rafradar
# Copyright (c) 2026 Furkan Akduman. Dual-licensed: free for noncommercial use
# under PolyForm Noncommercial 1.0.0 (LICENSE); commercial use requires a
# separate paid license (COMMERCIAL.md).
"""Yapılandırma yükleyici ve marka eşleme testleri."""
import json
import os
import sys
import tempfile
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "src"))

import ayarlar


ORNEK = {
    "ad": "Test Markası",
    "pazar": "Türkiye",
    "markalar": {
        "Alfa": ["alfa"],
        "Alfa Baby": ["alfa baby"],
    },
    "haric_markalar": {
        "Reçeteli": {"anahtarlar": ["receteli"], "sebep": "mevzuat"},
    },
    "kategoriler": {
        "Krem": {"aramalar": ["krem", "bakım kremi"], "markalar": ["Alfa"]},
        "Reçeteli Ürün": {"aramalar": ["receteli krem"], "markalar": ["Reçeteli"]},
    },
}


def gecici_ayar(veri, yukle=True):
    """Gecici bir yapilandirma dosyasi yazar ve etkinlestirir.

    yukle=False: dosya hazirlanir ama okunmaz; gecersiz yapilandirmanin
    hatayi testin kendi assertRaises blogunda firlatmasi icin gerekir.
    """
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(veri, f, ensure_ascii=False)
    f.close()
    os.environ["RAFRADAR_AYAR"] = f.name
    if yukle:
        ayarlar.yukle(yeniden=True)
    return f.name


class YapilandirmaTesti(unittest.TestCase):
    def setUp(self):
        self.dosya = gecici_ayar(ORNEK)

    def tearDown(self):
        os.environ.pop("RAFRADAR_AYAR", None)
        try:
            os.unlink(self.dosya)
        except OSError:
            pass
        ayarlar._onbellek = None

    def test_varsayilanlar_doldurulur(self):
        a = ayarlar.yukle(yeniden=True)
        self.assertEqual(a["goz_hizasi"], 10)
        self.assertEqual(a["kanallar"], ["n11", "trendyol"])

    def test_zorunlu_alan_eksikse_hata(self):
        eksik = {k: v for k, v in ORNEK.items() if k != "markalar"}
        yol = gecici_ayar(eksik, yukle=False)
        try:
            with self.assertRaises(SystemExit):
                ayarlar.yukle(yeniden=True)
        finally:
            os.unlink(yol)

    def test_marka_urun_adindan_eslesir(self):
        # Sitelerin marka alani bos veya yanlis olabiliyor; urun adi da taranmali
        self.assertEqual(ayarlar.izlenen_marka("", "Alfa Nemlendirici 100 ml"), "Alfa")
        self.assertEqual(ayarlar.izlenen_marka("Alfa", ""), "Alfa")

    def test_uzun_anahtar_once_eslesir(self):
        # "alfa baby" hem "Alfa" hem "Alfa Baby" anahtarini icerir;
        # daha ozgul olan kazanmali
        self.assertEqual(ayarlar.izlenen_marka("", "Alfa Baby Pişik Kremi"), "Alfa Baby")

    def test_alakasiz_urun_eslesmez(self):
        self.assertIsNone(ayarlar.izlenen_marka("Beta", "Beta Krem"))

    def test_haric_marka_izlenen_sayilmaz(self):
        # Haric tutulan marka izlenen olarak donmemeli, ama haric olarak taninmali
        self.assertIsNone(ayarlar.izlenen_marka("", "Receteli Krem 50 g"))
        self.assertEqual(ayarlar.haric_marka("", "Receteli Krem 50 g"), "Reçeteli")

    def test_kategori_tipi(self):
        self.assertEqual(ayarlar.kategori_tipi("Krem"), "izlenen")
        self.assertEqual(ayarlar.kategori_tipi("Reçeteli Ürün"), "haric")

    def test_sadece_izlenen_kategoriler(self):
        izlenen = ayarlar.kategoriler(sadece_izlenen=True)
        self.assertIn("Krem", izlenen)
        self.assertNotIn("Reçeteli Ürün", izlenen)

    def test_haric_sebep_okunur(self):
        self.assertEqual(ayarlar.haric_sebep("Reçeteli Ürün"), "mevzuat")


if __name__ == "__main__":
    unittest.main(verbosity=2)
