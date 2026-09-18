# -*- coding: utf-8 -*-
# RafRadar - https://github.com/FlyerFukas/rafradar
# Copyright (c) 2026 Furkan Akduman. Dual-licensed: free for noncommercial use
# under PolyForm Noncommercial 1.0.0 (LICENSE); commercial use requires a
# separate paid license (COMMERCIAL.md).
"""Kanal ayrıştırma testleri.

Buradaki her test, gerçek sayfalarda karşılaşılmış bir ayrıştırma hatasını
temsil eder; regresyon olmasın diye sabitlenmiştir.
"""
import os
import sys
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "src"))

from bs4 import BeautifulSoup

import kanal_trendyol as ty


class BaslikTemizligiTesti(unittest.TestCase):
    def test_siralama_rozeti_atilir(self):
        # Trendyol urun adinin basina siralama rozeti yapistiriyor
        self.assertEqual(ty._temizle("En 5. Ürün Alfa C Vitamini"), "Alfa C Vitamini")
        self.assertEqual(ty._temizle("En Çok Favorilenen 4. Ürün Alfa Krem"), "Alfa Krem")
        self.assertEqual(ty._temizle("En Çok Ziyaret Edilen 2. Ürün Alfa"), "Alfa")

    def test_promosyon_etiketleri_atilir(self):
        self.assertEqual(ty._temizle("Yetkili Satıcı Alfa Krem"), "Alfa Krem")
        self.assertEqual(ty._temizle("Süper Fırsat Ürünü Alfa Krem"), "Alfa Krem")
        self.assertEqual(ty._temizle("Hızlı Teslimat Alfa Krem"), "Alfa Krem")

    def test_fiyat_metinden_temizlenir(self):
        self.assertEqual(ty._temizle("Alfa Krem 359,50 TL"), "Alfa Krem")

    def test_birden_fazla_etiket_birlikte(self):
        ham = "En 3. Ürün Yetkili Satıcı Hızlı Teslimat Alfa Krem 100 ml 249,90 TL"
        self.assertEqual(ty._temizle(ham), "Alfa Krem 100 ml")


    def test_emoji_sonrasi_satis_rozeti_atilir(self):
        # "... 30 Tablet 🚀 3 günde 1,3B kişi ekledi! 4.6 ( 3976 )"
        ham = "Ocean Orzax Vitamin C 1000 mg 30 Tablet 🚀 3 günde 1,3B kişi ekledi! 4.6 ( 3976 )"
        self.assertEqual(ty._temizle(ham), "Ocean Orzax Vitamin C 1000 mg 30 Tablet")

    def test_favori_rozeti_atilir(self):
        ham = "Aromel C Vitamini 100 Şase Askorbik Asit ❤️ 7,6B kişi favoriledi!"
        self.assertEqual(ty._temizle(ham), "Aromel C Vitamini 100 Şase Askorbik Asit")

    def test_basarili_satici_oneki_adi_silmez(self):
        # "Başarılı Satıcı" adin BASINDA gecer; kuyruk deseni sanilirsa
        # tum urun adi silinir. Regresyon testi.
        self.assertEqual(ty._temizle("Başarılı Satıcı One Up C Vitamini 60 Tablet"),
                         "One Up C Vitamini 60 Tablet")

    def test_onek_ve_kuyruk_birlikte(self):
        ham = "Yetkili Satıcı Nutraxin C Vitamin 1000 Mg 3 günde 1,7B kişi ekledi"
        self.assertEqual(ty._temizle(ham), "Nutraxin C Vitamin 1000 Mg")

    def test_normal_baslik_bozulmaz(self):
        self.assertEqual(ty._temizle("Alfa Yoğun Nemlendirici 400 ML"),
                         "Alfa Yoğun Nemlendirici 400 ML")


class FiyatOkumaTesti(unittest.TestCase):
    """Kart metninde satis fiyati, birim fiyat ve uye fiyati birlikte gecer.
    Regex ile okumak birim fiyati (TL/kg) secebiliyordu; element bazli okunur."""

    def _kart(self, html):
        return BeautifulSoup(html, "html.parser")

    def test_birim_fiyat_secilmez(self):
        kart = self._kart(
            '<a><div class="price-section">649,90 TL</div>'
            '<span class="unit-price">( 5.415,83 TL/kg )</span></a>')
        normal, plus = ty._fiyat_oku(kart)
        self.assertEqual(normal, 649.90)

    def test_uye_fiyati_ayri_alanda_doner(self):
        kart = self._kart(
            '<a><div class="price-section">649,90 TL</div>'
            '<span class="ty-plus-strip-view-price">617,40 TL</span></a>')
        normal, plus = ty._fiyat_oku(kart)
        self.assertEqual(normal, 649.90)
        self.assertEqual(plus, 617.40)

    def test_binlik_ayraci_dogru_cozulur(self):
        kart = self._kart('<a><div class="price-section">1.299,50 TL</div></a>')
        normal, _ = ty._fiyat_oku(kart)
        self.assertEqual(normal, 1299.50)

    def test_fiyat_yoksa_none(self):
        kart = self._kart('<a><div>fiyat yok</div></a>')
        normal, plus = ty._fiyat_oku(kart)
        self.assertIsNone(normal)
        self.assertIsNone(plus)


class VitrinTespitiTesti(unittest.TestCase):
    """css-slider icindeki kartlar marka vitrinidir, organik raf degildir."""

    def test_slider_icindeki_kart_vitrin_sayilir(self):
        s = BeautifulSoup(
            '<div class="css-slider"><div class="css-slide">'
            '<a href="/marka/urun-p-1">Alfa</a></div></div>', "html.parser")
        self.assertTrue(ty._slider_mi(s.select_one("a")))

    def test_slider_disindaki_kart_organiktir(self):
        s = BeautifulSoup(
            '<div class="prdct-cntnr"><a href="/marka/urun-p-1">Alfa</a></div>',
            "html.parser")
        self.assertFalse(ty._slider_mi(s.select_one("a")))


class MarkaCozmeTesti(unittest.TestCase):
    def test_yol_ilk_segmenti_markadir(self):
        self.assertEqual(ty._marka_coz("/alfa-kozmetik/urun-adi-p-123", "Alfa Krem"),
                         "Alfa Kozmetik")

    def test_mutlak_url_de_calisir(self):
        self.assertEqual(
            ty._marka_coz("https://www.trendyol.com/alfa/urun-p-9", "Alfa Krem"), "Alfa")

    def test_yol_cozulemezse_urun_adina_duser(self):
        self.assertEqual(ty._marka_coz("", "Alfa Krem"), "Alfa")


if __name__ == "__main__":
    unittest.main(verbosity=2)
