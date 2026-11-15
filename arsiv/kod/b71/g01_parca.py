# -*- coding: utf-8 -*-
"""Bolum 71 - Parcalama stratejileri ve soru kumesi."""

import re
from ortak import bolumleri_oku

# (soru, kanit): kanit, cevabin bulundugu tam ifadedir. Her kanit
# korpusta aranir; bulunamayan soru calisma oncesi reddedilir.
SORULAR = [
    (
        "Attention skorunda neden olcekleme yapilir?",
        "Ölçekleme, skorun varyansını",
    ),
    (
        "Bahdanau ve arkadaşlarının dikkat makalesi neyi önerdi?",
        "Bahdanau, Cho ve Bengio'nun 2015'teki makalesi",
    ),
    (
        "Transformer mimarisini tanıtan makale hangi yılda çıktı?",
        "2017'de Vaswani ve arkadaşları",
    ),
    (
        "RNN encoder-decoder düzeninde darboğaz neydi?",
        "bütün bilgi tek bir vektörden geçer",
    ),
    (
        "Nedensel maske gelecek konumlara ne yapar?",
        "Nedensel maske gelecek konumları",
    ),
    (
        "Çok başlı attention'da parametre sayısı başlardan nasıl "
        "etkilenir?",
        "Parametre sayısı başlardan bağımsızdır",
    ),
    (
        "Attention neden konum bilgisine ihtiyaç duyar?",
        "permütasyon eşdeğişkendir",
    ),
    ("KV önbelleği neyi saklar?", "anahtar ve değer vektörlerini"),
    (
        "Pre-norm blok neden derin ağlarda daha kararlıdır?",
        "Pre-norm, artık yolu temiz tuttuğu için",
    ),
    (
        "Transformer neden RNN'den daha hızlı eğitilir?",
        "eğitim paralel yürür",
    ),
    (
        "Simetrik kuantizasyonda sıfır noktası nasıl seçilir?",
        "Simetrik eşlemede Z = 0 alınır",
    ),
    ("Simetrik eşlemede ölçek nasıl hesaplanır?", "S = max|r| / 127"),
    (
        "Kanal başına kuantizasyon nedir?",
        "Kanal başına (per-channel) kuantizasyonda",
    ),
    (
        "Model belleği parametre sayısı ve bit genişliğiyle nasıl "
        "hesaplanır?",
        "model belleği yaklaşık P · b / 8 bayttır",
    ),
    (
        "Tamsayı yeniden ölçeklemede birikim hangi çarpımla yapılır?",
        "64-bit çarpım acc · M0",
    ),
    (
        "İki model arasındaki farkın gerçekliği bootstrap ile nasıl "
        "sınanır?",
        "Test örneklerini yerine koyarak yeniden örnekleyip",
    ),
    (
        "Bootstrap ile güven aralığı nasıl elde edilir?",
        "yüzdelik %2,5 ve %97,5 güven aralığı verir",
    ),
    ("Little yasası nedir?", "L = lambda x W"),
    (
        "Yük dengeleyicinin L4 katmanı ne yapar?",
        "dengeleyici TCP bağlantılarını yönlendirir",
    ),
    (
        "Kullanım oranı 0,9 civarına geldiğinde gecikmeye ne olur?",
        "gecikme patlamaya başlıyordu",
    ),
    (
        "M/M/1 kuyruğunda ilk M neyi belirtir?",
        "varışlar Poisson sürecidir",
    ),
    (
        "k-means neden daireselmiş kümeler için siluet skorunu "
        "yüksek verir?",
        "kümeleri daireselmiş gibi ayırdığı için",
    ),
    (
        "Kriptografik olmayan hash'lerin sorunu nedir?",
        "bir saldırganın çakışma üretmesini engellemezler",
    ),
    (
        "Naif hash neden kötü dağılım üretti?",
        "naif hash kelimeleri dar bir sayı aralığına sıkıştırıyor",
    ),
    (
        "Singleton yerine önce hangi çözüm denenmelidir?",
        "singleton yerine önce bağımlılık enjeksiyonunu dene",
    ),
    (
        "Von Neumann mimarisinin devrimci fikri nedir?",
        "komutları ve verileri aynı bellekte tut",
    ),
    (
        "Adam optimizasyonu neyi birleştirir?",
        "momentumu ve RMSProp'un uyarlamasını birleştirir",
    ),
    (
        "Yığın taşmasına karşı hangi karşı önlemler anılır?",
        "stack canary, ASLR, NX bit",
    ),
    (
        "Yük faktörü neyi ölçer ve tablo dolunca ne olur?",
        "Yük faktörü α = n / M",
    ),
    (
        "Huffman algoritmasında her adımda hangi düğümler "
        "birleştirilir?",
        "her adımda en düşük frekanslı iki düğümü seç",
    ),
    ("Gradyan inişinde her adımda hangi yöne gidilir?", "−∇f"),
    (
        "Gradyan inişinin en büyük sorunu nedir?",
        "Gradyan inişinin en büyük sorunu zikzaktır",
    ),
    (
        "Dolgu maskesi attention'da ne yapar?",
        "Dolgu maskesi, dizi uzunlukları arasındaki farkı yok sayar",
    ),
    (
        "Attention çıktısı, ağırlıklarla değerlerin nasıl "
        "birleşmesiyle elde edilir?",
        "sonuç A·V",
    ),
]


def duzlestir(metin):
    return re.sub(r"\s+", " ", metin).strip()


def bolum_metinleri():
    """Her bolum icin duz metin (paragraflar bosluk ile
    birlestirilir)."""
    sonuc = []
    for n, paragraflar in bolumleri_oku():
        sonuc.append((n, paragraflar))
    return sonuc


def sabit_parcalar(metin, uzunluk, ortusme, bolum):
    """Kelime sinirinda kesilen sabit uzunluklu parcalar."""
    parcalar, i = [], 0
    while i < len(metin):
        son = min(i + uzunluk, len(metin))
        if son < len(metin):
            k = metin.rfind(" ", i, son)
            if k > i:
                son = k
        parcalar.append(
            {"bolum": bolum, "metin": metin[i:son].strip()}
        )
        if son >= len(metin):
            break
        i = max(son - ortusme, i + 1)
    return parcalar


def baslik_parcalari(paragraflar, bolum, azami=600):
    """Cumleleri bolum basliklarina gore gruplar; baslik her parcanin
    basina eklenir."""
    parcalar = []
    grup, baslik, uzun = [], None, 0

    def kapat():
        if grup:
            metin = (baslik + ". " if baslik else "") + " ".join(grup)
            parcalar.append({"bolum": bolum, "metin": metin})

    for b, p in paragraflar:
        if b != baslik:
            kapat()
            grup, uzun = [], 0
            baslik = b
        for c in re.split(r"(?<=[.!?])\s+", p):
            if uzun + len(c) > azami and grup:
                kapat()
                grup, uzun = [], 0
            grup.append(c)
            uzun += len(c) + 1
    kapat()
    return parcalar


def parcalari_kur():
    """Uc strateji: sabit-400, sabit-400+80 ortusme, baslik-
    bilincli-600."""
    s_a, s_b, s_c = [], [], []
    for n, paragraflar in bolum_metinleri():
        duz = " ".join(p for _, p in paragraflar)
        s_a += sabit_parcalar(duz, 400, 0, n)
        s_b += sabit_parcalar(duz, 400, 80, n)
        s_c += baslik_parcalari(paragraflar, n, 600)
    return {"sabit400": s_a, "sabit400_80": s_b, "baslik600": s_c}


def kanit_kontrol(parcalar_listesi):
    """Her kanit en az bir bolumde gecmeli; degilse hata."""
    bolumler = {}
    for n, paragraflar in bolum_metinleri():
        bolumler[n] = " ".join(p for _, p in paragraflar)
    eksik = []
    for soru, kanit in SORULAR:
        if not any(kanit in m for m in bolumler.values()):
            eksik.append((soru, kanit))
    return eksik


if __name__ == "__main__":
    eksik = kanit_kontrol(None)
    print("kanit eksik:", len(eksik))
    for s, k in eksik:
        print("  -", k)
    parcalar = parcalari_kur()
    for ad, liste in parcalar.items():
        uzun = [len(p["metin"]) for p in liste]
        print(
            "%-12s parca=%5d ort=%5.0f maks=%4d"
            % (ad, len(liste), sum(uzun) / len(uzun), max(uzun))
        )
