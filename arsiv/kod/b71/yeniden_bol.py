# -*- coding: utf-8 -*-
"""Kod yer tutucularini 40-50 satirlik parcalara boler; devam parcalarina
kisa aciklama paragrafi ekler."""
import glob

def K(f, a, b):
    return "{{KOD:%s|%d|%d}}" % (f, a, b)

def devam(metin, f, a, b):
    return metin + "\n\n" + K(f, a, b)

harita = {}
harita["{{KOD:ortak.py|1|end}}"] = "\n\n".join([
    K("ortak.py", 1, 49),
    "Dosyanın devamında, bölüm metnini paragraflara ayıran `bolumleri_oku` "
    "işlevi tamamlanır. Ardından Türkçe'ye uygun küçük harf dönüşümü "
    "(`dk_notu`) ve belirteçleme (`belirtecler`, isteğe bağlı kök kesme) "
    "gelir.",
    K("ortak.py", 50, 95),
    "Son kısımda BM25'in terslenmiş indeksini kuran `bm25_indeks` ve "
    "skorları hesaplayan `bm25_skor` yer alır.",
    K("ortak.py", 96, 148)])

harita["{{KOD:g01_parca.py|1|60}}"] = K("g01_parca.py", 1, 49)
harita["{{KOD:g01_parca.py|61|end}}"] = "\n\n".join([
    "Soru listesi devam ediyor; her soru bir kanıt ifadesiyle eşleştirilmiştir.",
    K("g01_parca.py", 50, 98),
    "Liste ardından bölüm metinlerini toplayan `bolum_metinleri` ve sabit "
    "uzunluklu parçalayıcı `sabit_parcalar` ile sürer.",
    K("g01_parca.py", 99, 146),
    "Başlık-bilinçli parçalayıcı `baslik_parcalari`, cümleleri bölüm "
    "başlıklarına göre gruplar ve her parçanın başına başlığı ekler.",
    K("g01_parca.py", 147, 184),
    "Son kısımda üç stratejiyi birleştiren `parcalari_kur`, kanıt denetimini "
    "yapan `kanit_kontrol` ve ana program yer alır.",
    K("g01_parca.py", 185, 235)])

harita["{{KOD:g02_geri_getirme.py|1|60}}"] = K("g02_geri_getirme.py", 1, 42)
harita["{{KOD:g02_geri_getirme.py|61|end}}"] = "\n\n".join([
    "Dosyanın devamında, her sorgu için kanıtın bulunduğu parçaları "
    "hesaplayan `alaka_kumeleri` ile sıra ölçütlerini üreten `rr_ve_geri` "
    "yer alır.",
    K("g02_geri_getirme.py", 43, 84),
    "Sonraki kısım, ölçütleri toplayan `ozet`, LSA gömmesini üreten "
    "`lsa_gomme` ve RRF'i uygulayan `rrf` işlevlerini içerir.",
    K("g02_geri_getirme.py", 85, 133),
    "Ana değerlendirme işlevi `degerlendir`, her sorgu için dört yöntemin "
    "skorunu hesaplar ve sıralamaları ölçütlere dönüştürür.",
    K("g02_geri_getirme.py", 134, 182),
    "Son kısım tabloyu yazdırır; ana blok parça boyutu taramasını çalıştırıp "
    "sonuçları CSV'ye kaydeder.",
    K("g02_geri_getirme.py", 183, 203)])

harita["{{KOD:g03_bootstrap.py|1|end}}"] = K("g03_bootstrap.py", 1, 55)

harita["{{KOD:g04_ivf.py|1|50}}"] = K("g04_ivf.py", 1, 48)
harita["{{KOD:g04_ivf.py|51|end}}"] = "\n\n".join([
    "Dosyanın devamında, her kümenin üyelerini ters liste olarak tutan "
    "`ivf_kur` ve bir sorguyu yalnızca en yakın `nprobe` kümede arayan "
    "`ara_ivf` gelir.",
    K("g04_ivf.py", 49, 97),
    "Ana program veriyi üretir, kaba kuvveti sorgu başına ölçer, ardından "
    "`nprobe` taramasını yapıp CSV'yi yazar.",
    K("g04_ivf.py", 98, 133)])

harita["{{KOD:lm71.py|1|50}}"] = K("lm71.py", 1, 34)
harita["{{KOD:lm71.py|51|end}}"] = "\n\n".join([
    "Model, bir bloğun yığılmasından oluşur; bloğun ileri geçişi, KV "
    "önbelleğini kullanan dikkati ve MLP'yi içerir.",
    K("lm71.py", 35, 87)])

harita["{{KOD:g05_egitim.py|1|end}}"] = K("g05_egitim.py", 1, 57)

harita["{{KOD:g06_kuantizasyon.py|1|60}}"] = K("g06_kuantizasyon.py", 1, 48)
harita["{{KOD:g06_kuantizasyon.py|61|end}}"] = "\n\n".join([
    "Kuantizasyonun devamında, kuantize edilmiş ağırlıkları modele yükleyen "
    "`model_yukle` ve test kümesinde bit/karakter ile perplexity'yi "
    "hesaplayan `bpc` yer alır.",
    K("g06_kuantizasyon.py", 49, 90),
    "Ana program altı yöntemi sırayla çalıştırır, sonuçları yazdırır ve "
    "CSV'ye kaydeder.",
    K("g06_kuantizasyon.py", 91, 144)])

harita["{{KOD:g07_kv.py|1|60}}"] = K("g07_kv.py", 1, 49)
harita["{{KOD:g07_kv.py|61|end}}"] = "\n\n".join([
    "Önbelleksiz üretim, aynı işi her adımda tüm diziyi yeniden işleyerek "
    "yapar; iki fonksiyonun sonucu aşağıda karşılaştırılacak.",
    K("g07_kv.py", 50, 98),
    "Son kısım prefill ve decode sürelerini ölçer ve KV bellek formülünü "
    "hem küçük model hem 7B sınıfı için yazdırır.",
    K("g07_kv.py", 99, 133)])

harita["{{KOD:g08_spekulatif.py|1|60}}"] = K("g08_spekulatif.py", 1, 46)
harita["{{KOD:g08_spekulatif.py|61|end}}"] = "\n\n".join([
    "Hedef modelin greedy tahmini ve spekülatif döngü burada: taslak `γ` "
    "belirteç önerir, hedef model tek geçişte hepsini kontrol eder.",
    K("g08_spekulatif.py", 47, 87),
    "Ana program 20 istem için referans çıktıları üretir ve farklı `γ` "
    "değerleri için ölçütleri yazar.",
    K("g08_spekulatif.py", 88, 136)])

harita["{{KOD:g09_kisit.py|1|60}}"] = K("g09_kisit.py", 1, 49)
harita["{{KOD:g09_kisit.py|61|end}}"] = "\n\n".join([
    "Üretim işlevi `dagit`, her adımda `izinli` maskesini logit'lere ekler "
    "ve örnekleme yapar; `dogrula` çıktıyı şemaya göre denetler.",
    K("g09_kisit.py", 50, 97),
    "Ana program iki üretimi (kısıtsız ve kısıtlı) 200'er örnek için "
    "çalıştırır ve geçerlilik oranlarını yazdırır.",
    K("g09_kisit.py", 98, 124)])

harita["{{KOD:g10_ajan.py|1|50}}"] = K("g10_ajan.py", 1, 49)
harita["{{KOD:g10_ajan.py|51|end}}"] = "\n\n".join([
    "Ajan işlevi, getirilen veriyi savunmasız ya da savunmalı bir politika "
    "ile işler; zehirli belge ve ana program son kısımdadır.",
    K("g10_ajan.py", 50, 97)])

harita["{{KOD:g11_pii.py|1|end}}"] = "\n\n".join([
    K("g11_pii.py", 1, 47),
    "Son kısım, TC kimlik numarası denetimini ve maskelemeyi sınayan sekiz "
    "örnekten oluşan test kümesini içerir.",
    K("g11_pii.py", 48, 96)])

harita["{{KOD:g12_servis.py|1|60}}"] = K("g12_servis.py", 1, 37)
harita["{{KOD:g12_servis.py|61|end}}"] = "\n\n".join([
    "Sürekli toplu işleme simülasyonu, aktif istek kümesini her adımda "
    "güncelleyen döngüdür; ardından ölçütleri hesaplayan `ozet` gelir.",
    K("g12_servis.py", 38, 86),
    "Ana program her yöntem ve `B` değeri için yük taramasını çalıştırır "
    "ve sonuçları CSV'ye yazar.",
    K("g12_servis.py", 87, 108)])

harita["{{KOD:g13_gecikme.py|1|end}}"] = "\n\n".join([
    K("g13_gecikme.py", 1, 41),
    "Ana program 60 istek üretir, TTFT ve belirteç başına süreleri toplar ve "
    "yüzdelikleri yazdırır.",
    K("g13_gecikme.py", 42, 72)])

harita["{{KOD:g14_eval.py|1|end}}"] = "\n\n".join([
    K("g14_eval.py", 1, 33),
    "Ana program her soru için tahmini ve ölçütleri hesaplar; F1 için "
    "bootstrap güven aralığı üretir.",
    K("g14_eval.py", 34, 62)])

harita["{{KOD:qparams_sarili.py|1|end}}"] = "\n\n".join([
    K("qparams_sarili.py", 1, 49),
    "Fonksiyonun son kısmı, ölçek ve sıfır noktasını tensör biçimine getirip "
    "döndüren adımlardır.",
    K("qparams_sarili.py", 50, 64)])

sayac = 0
for yol in sorted(glob.glob("md/p0*.md")):
    s = open(yol, encoding="utf-8").read()
    for eski, yeni in harita.items():
        if eski in s:
            s = s.replace(eski, yeni)
            sayac += 1
    open(yol, "w", encoding="utf-8").write(s)
print("degistirilen yer tutucu:", sayac)
