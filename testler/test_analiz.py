# -*- coding: utf-8 -*-
"""Skor kartı metriklerinin testleri.

Metrikler ticari karara girdiği için burada gerçek veri değil, sonucu elle
doğrulanabilen sentetik veri kullanılır.
"""
import json
import os
import sys
import tempfile
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "src"))

import ayarlar

AYAR = {
    "ad": "Alfa",
    "goz_hizasi": 10,
    "markalar": {"Alfa": ["alfa"]},
    "kategoriler": {"Krem": {"aramalar": ["krem"], "markalar": ["Alfa"]}},
}


def urun(sira, marka, fiyat, sponsorlu=False):
    return {"sira": sira, "organik_sira": None if sponsorlu else sira,
            "marka": marka, "ad": marka + " ürün", "fiyat": fiyat,
            "plus_fiyat": None, "sponsorlu": sponsorlu, "kanal": "n11"}


class MetrikTesti(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(AYAR, f, ensure_ascii=False)
        f.close()
        cls.dosya = f.name
        os.environ["RAFRADAR_AYAR"] = f.name
        ayarlar.yukle(yeniden=True)
        global analiz
        import analiz  # ayarlar yuklendikten sonra import edilmeli

    @classmethod
    def tearDownClass(cls):
        os.environ.pop("RAFRADAR_AYAR", None)
        ayarlar._onbellek = None
        try:
            os.unlink(cls.dosya)
        except OSError:
            pass

    def test_raf_payi(self):
        # 10 urunun 2'si Alfa -> %20
        urunler = [urun(i, "Alfa" if i <= 2 else "Beta", 100) for i in range(1, 11)]
        s = analiz.olc(urunler)
        self.assertEqual(s["toplam"], 10)
        self.assertEqual(s["izlenen"], 2)
        self.assertEqual(s["raf_payi"], 20.0)
        self.assertTrue(s["bulunurluk"])

    def test_sponsorlu_organikten_ayrilir(self):
        # 5 organik + 5 sponsorlu; sponsorlularin tamami Alfa.
        # Organik pay sponsorlulari saymamali.
        urunler = [urun(i, "Beta", 100) for i in range(1, 6)]
        urunler += [urun(i, "Alfa", 100, sponsorlu=True) for i in range(1, 6)]
        organik = analiz.olc(urunler, sadece_organik=True)
        hepsi = analiz.olc(urunler, sadece_organik=False)
        self.assertEqual(organik["izlenen"], 0)
        self.assertEqual(organik["raf_payi"], 0.0)
        self.assertEqual(hepsi["izlenen"], 5)

    def test_goz_hizasi_esigi(self):
        # 3. ve 12. siradaki Alfa: yalnizca biri ilk 10'da
        urunler = [urun(i, "Alfa" if i in (3, 12) else "Beta", 100) for i in range(1, 21)]
        s = analiz.olc(urunler)
        self.assertEqual(s["izlenen"], 2)
        self.assertEqual(s["goz_hizasinda"], 1)
        self.assertEqual(s["en_iyi_sira"], 3)

    def test_fiyat_endeksi_medyan_uzerinden(self):
        # Kategori medyani 100, Alfa medyani 200 -> endeks 2.0
        urunler = [urun(i, "Beta", 100) for i in range(1, 10)]
        urunler += [urun(10, "Alfa", 200), urun(11, "Alfa", 200)]
        s = analiz.olc(urunler)
        self.assertEqual(s["izlenen_medyan"], 200)
        self.assertEqual(s["fiyat_endeksi"], 2.0)

    def test_fiyatsiz_urunler_medyani_bozmaz(self):
        urunler = [urun(1, "Alfa", 100), urun(2, "Alfa", None), urun(3, "Beta", 100)]
        s = analiz.olc(urunler)
        self.assertEqual(s["izlenen_medyan"], 100)

    def test_bos_liste_none_doner(self):
        self.assertIsNone(analiz.olc([]))

    def test_hic_izlenen_yoksa_bulunurluk_yanlis(self):
        s = analiz.olc([urun(i, "Beta", 100) for i in range(1, 6)])
        self.assertEqual(s["izlenen"], 0)
        self.assertFalse(s["bulunurluk"])
        self.assertIsNone(s["en_iyi_sira"])

    def test_rakipler_sayilir(self):
        urunler = [urun(1, "Alfa", 100), urun(2, "Beta", 100), urun(3, "Beta", 100),
                   urun(4, "Gama", 100)]
        s = analiz.olc(urunler)
        self.assertEqual(dict(s["rakipler"])["Beta"], 2)
        self.assertNotIn("Alfa", dict(s["rakipler"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
