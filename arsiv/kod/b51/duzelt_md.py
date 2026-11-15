import io

def uygula(dosya, reps):
    s = io.open(dosya, encoding="utf-8").read()
    for old, new in reps:
        n = s.count(old)
        print(dosya[-8:], n, old[:55].replace("\n", " "))
        if n == 1:
            s = s.replace(old, new)
    io.open(dosya, "w", encoding="utf-8").write(s)

A = [
 ("@@CIKTI python olcum_metin.py cikti_olcum_metin.txt@@",
  "@@CIKTI python olcum_metin.py bolumler engine\\veri cikti_olcum_metin.txt@@"),
]
B = [
 ("@@CIKTI python kodlama_olcum.py cikti_kodlama_olcum.txt@@",
  "@@CIKTI python kodlama_olcum.py bolumler engine\\veri cikti_kodlama_olcum.txt@@"),
 ('@@CIKTI python lz77_zlib.py "bolumler\\bolum_18.md" cikti_lz77_zlib.txt@@',
  "@@CIKTI python lz77_zlib.py bolumler\\bolum_18.md cikti_lz77_zlib.txt@@"),
]
C = []
D = [
 ('@@CIKTI python hamming_kanal.py "veri klasörü" cikti_hamming_kanal.txt@@',
  "@@CIKTI python hamming_kanal.py engine\\veri cikti_hamming_kanal.txt@@"),
 ("Sonuçları dikkatle okuman gerekir. Düşük `p`'de (0,001 ile 0,02 arası) tekrar kodu en düşük bit hatasını verir: `p = 0,01`de `0,00027`, Hamming'de `0,00083`.",
  "Sonuçları dikkatle okuman gerekir. `p = 0,005` ile `0,02` arasında tekrar kodu en düşük bit hatasını verir: `p = 0,01`de `0,00027`, Hamming'de `0,00083`. `p = 0,001`de iki kodun hatası sıfıra o kadar yakındır ki 160 000 bitlik simülasyonda sıralama gürültüye kalır."),
 ("Bu bir değiş tokuştur. Her iki kod da", "Bu bir değiş tokuştur. Her iki kod da"),
 ("Hamming(7,4)'ün `d = 3`tür, bu yüzden bir hatayı düzeltir ve iki hatayı tespit eder (ama düzeltemez).",
  "Hamming(7,4)'ün `d = 3`tür, bu yüzden bir hatayı düzeltir. İki hata teoride tespit edilebilir, ama bu kodun sendrom çözücüsü iki hatayı ayırt edemez: çift hatalı bir sözcük, yanlış bir tek hata gibi görünür ve yanlış bir konum düzeltilir."),
 ("Bu dizinin kodlanmış uzunluğu, sembol başına ortalama uzunluğun on katıdır.",
  "Bu dizinin kodlanmış uzunluğu `4·1 + 3·2 + 2·3 + 1·3 = 19` bittir; sembol başına `1,9` bit, yani ortalama `L` ile tam uyumludur."),
 ("**Adım 3 — Kaba çöz.** Entropi `H = −(0,4 log₂ 0,4 + 0,3 log₂ 0,3 + 0,2 log₂ 0,2 + 0,1 log₂ 0,1)` ile hesaplanır; bu `1,8464` bittir. Huffman için: `0,1 + 0,2 = 0,3`; sonra `0,3 + 0,3 = 0,6` (eski `0,3` ile birleşen yeni `0,3`); son olarak `0,4 + 0,6 = 1`. Derinlikler: `a` için 1, `b` için 2, `c` ve `d` için 3.",
  "**Adım 3 — Kaba çöz.** Entropi `H = −(0,4 log₂ 0,4 + 0,3 log₂ 0,3 + 0,2 log₂ 0,2 + 0,1 log₂ 0,1)` ile hesaplanır; bu `1,8464` bittir. Huffman birleştirmeleri şöyledir: önce `c` (0,2) ve `d` (0,1) birleşir, toplam `0,3`; sonra `b` (0,3) bu düğümle birleşir, toplam `0,6`; son olarak `a` (0,4) ile `0,6` birleşir ve kök `1` olur. Derinlikler: `a` için 1, `b` için 2, `c` ve `d` için 3."),
 ("Yorum: `p`nin ağırlıklı olduğu yönde (`KL(p‖q)`) `q` düzgün seçimi, gerçek veriyi daha az cezalandırır; `q`nun kütlesini `p`nin az olduğu yere koyduğu yönde ise ceza daha büyüktür.",
  "Yorum: bu örnekte `KL(p‖q)` daha küçüktür, çünkü `q` düzgün seçildiğinde `p`nin kütlesi `q`nun geniş kapsamında kalır. Ters yönde `q`nun `0,5` kütlesi `p`nin yalnızca `0,1` kütle taşıdığı tura bölgesine düşer ve ceza büyür."),
 ("8. (★★) Bir ikili sınıflandırıcı `p = 0,8` olasılıkla doğru etiket için `q = 0,8` vermiş olsun. Doğru etiket `1` ise çapraz entropi kaybını (nat) hesapla.",
  "8. (★★) Bir ikili sınıflandırıcı, doğru etiket için 0,8 olasılığını vermiş olsun. Çapraz entropi kaybını (nat) hesapla ve bu değerin neden 0,8'e değil `−ln 0,8`e eşit olduğunu açıkla."),
 ("10. (★★★) Tekrar kodu ile BSC üzerinde `p`'nin hangi değerinde kodsuz iletimle aynı bit hata oranını verir? (İpucu: `3p² − 2p³ = p` denklemini çöz.)",
  "10. (★★★) Tekrar kodunun bit hata oranı `3p² − 2p³`, kodsuz iletiminki `p`dir. `3p² − 2p³ = p` denkleminin `(0, 1)` aralığındaki çözümü nedir ve bu değerin ötesinde tekrar kodu neden kodsuzdan kötüdür?"),
 ("Fonksiyonun başlangıcı, pencere sınırını ve hash zincirini kurar. İlk kesit, değişkenlerin ve pencere sınırının tanımıdır (satır 1355–1361):",
  "Fonksiyonun başlangıcı, pencere sınırını ve hash zincirini kurar. İlk kesit, pencere sınırının ve hash zincirinin tanımıdır (satır 1355–1361):"),
 ("Satır 1348'de fonksiyonun imzası (`local uInt longest_match(deflate_state *s, IPos cur_match) {`) ve yerel değişkenler bulunur; 1349–1354 arasında `chain_length`, `scan`, `match`, `len`, `best_len` ve `nice_match` tanımlanır, bunlar bu kesitin dışında kaldı. Satır 1363 ile 1438 arasında `UNALIGNED_OK` makrosunun tanımlı olduğu dal yer alır; bu makro tanımlanmadığında derleyici `#else` dalını kullanır.",
  "Satır 1348'de fonksiyonun imzası (`local uInt longest_match(deflate_state *s, IPos cur_match) {`) ve yerel değişkenler yer alır; 1349–1354 satırları `chain_length`, `scan`, `match`, `len`, `best_len` ve `nice_match` gibi değişkenleri tanımlar ve bu kesitin dışında kalır. Satır 1363–1374 arasındaki `UNALIGNED_OK` denetimi, karşılaştırmanın iki baytlık mı bayt bayt mı yapılacağını seçer. Satır 1383'te `chain_length >>= 2` bulunur: önceki eşleşme yeterince iyiyse arama zinciri kısaltılır."),
 ("İkinci kesit, `#else` dalındaki karşılaştırma bloğudur (satır 1439–1444):",
  "İkinci kesit, döngünün `#else` dalındaki karşılaştırma bloğudur. Satır 1393'te başlayan `do` döngüsünün içinde, 1405–1438 arasındaki `UNALIGNED_OK` dalı atlanmış ve 1439'da `#else` dalına geçilmiştir (satır 1439–1444):"),
 ("Bu dalda önce dört karşılaştırma yapılır. Bunlar, eşleşmenin mevcut en iyi uzunluğundan (`best_len`) daha uzun olabileceğini hızlıca eler: `match[best_len]` ve `match[best_len − 1]` bayt denetimi, büyük bir eşleşmenin gerçekten ilerleyebileceğini sınar. Satır 1445–1448 bir açıklama yorumudur, atlanmıştır. Satır 1449–1467 arasında asıl karşılaştırma döngüsü (`do { } while` ile sekiz kere ilerleyen bir yapı) bulunur; bu kısmı da atlıyoruz.",
  "Bu dalda önce dört karşılaştırma yapılır. Bunlar, bir adayın mevcut en iyi eşleşmeden (`best_len`) daha uzun olup olamayacağını hızlıca eler: `match[best_len]` ve `match[best_len − 1]` denetimleri, aday eşleşmenin sondaki baytlarını önce kontrol eder. Satır 1445–1457 açıklama yorumu ve ilk karşılaştırma ilerletmelerini içerir; satır 1458–1463 ise `do { } while` ile sekiz karşılaştırmalık asıl eşleşme ölçümüdür. Bu iki parça atlanmıştır."),
 ("Üçüncü kesit, en iyi eşleşmenin güncellenmesi ve döngünün sonucu olan bölümdür (satır 1473–1486):",
  "Üçüncü kesit, en iyi eşleşmenin güncellenmesi ve döngünün sonucu olan bölümdür (satır 1473–1486). Arada kalan satırlar (1464–1472) ölçümün sonunu ve `UNALIGNED_OK` kapanışını içerir:"),
 ("Bu, bir bilgi ölçüsüdür de.", "Bu, bir bilgi ölçüsüdür de."),
 ("Bu bölümde her kayıp fonksiyonunun bir bilgi ölçüsü olduğunu, eğitimin ise veri ve model dağılımı arasındaki ıraksamayı küçülttüğünü gördün.",
  "Bu bölümde çapraz entropi ve KL gibi sınıflandırma ve üretici modellerdeki kayıpların bilgi teorisi kökenini gördün; eğitimin ise veri ve model dağılımı arasındaki ıraksamayı küçülttüğünü anladın. MSE gibi kayıpların olasılıksal yorumu ise Gauss varsayımından gelir."),
 ("Bölüm 46'daki kuantizasyonun ve Bölüm 72'deki değişimsel kodlayıcıların, bir anlamsal kodlayıcının gizli temsilini ve bu temsilin ne kadar bilgi taşıdığını ölçmek için kullanıldığını not et: gizli temsil ile girdi arasındaki karşılıklı bilgi ve KL terimi, bu tasarımın ölçüm araçlarıdır.",
  "Bölüm 46'daki kuantizasyon ve Bölüm 72'deki değişimsel kodlayıcılar, gizli temsilin ne kadar bilgi taşıdığını ölçmenin araçlarıdır. Bir anlamsal kodlayıcıda gizli temsil ile girdi arasındaki karşılıklı bilgi ve KL terimi, iletilecek temsilin boyutunu ve kalitesini belirler."),
]

uygula("A_placeholder_skip", []) if False else None
uygula("C:/Users/merty/AppData/Local/Temp/b51/md_a.md", A)
uygula("C:/Users/merty/AppData/Local/Temp/b51/md_b.md", B)
uygula("C:/Users/merty/AppData/Local/Temp/b51/md_d.md", D)
print("bitti")
