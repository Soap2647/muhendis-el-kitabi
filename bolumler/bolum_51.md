%% kisim_no: XII
%% kisim_ad: Matematik
%% bolum_no: 51
%% baslik: Bilgi Teorisi

## Giriş: Bir mesajın ne kadar bilgi taşıdığını ölçmek

Bir İHA saniyede yüzlerce sensör değeri üretir ve bunları yere göndermesi gerekir. Bu değerlerin çoğu bir önceki değere neredeyse eşittir. Bu veriyi bit olarak gönderirken iki soru ortaya çıkar: ne kadar az bitle gönderebilirim ve bağlantı bozulursa neyi kurtarabilirim? Bu iki soru, bilgi teorisinin iki temel sorusudur. Claude Shannon 1948'de yayımladığı "A Mathematical Theory of Communication" makalesiyle bu soruları nicel olarak cevapladı. Bir kaynağın ne kadar bilgi ürettiği **entropi** ile, bir kanalın ne kadar bilgi taşıyabildiği **kapasite** ile ölçülür.

Bu bilgi bugün her yerde karşına çıkar. Sıkıştırma (zip, PNG, JPEG), hata düzeltme (CD'deki çizik, QR koddaki bozulma, uydu bağlantısındaki gürültü) ve kriptografi (Bölüm 32'deki anahtar uzunlukları) bilgi teorisinin üç ayağıdır. Mülakatta "Huffman neden optimal?", "sıkıştırmanın alt sınırı nedir?" ya da "çapraz entropi kaybı neden MSE yerine kullanılır?" gibi sorular sık gelir. Son soru doğrudan bu bölümün konusudur.

ML tarafında bu bölüm, kayıp fonksiyonlarının kökenini açıklar. Sınıflandırmada kullanılan çapraz entropi kaybı, aslında negatif olabilirlik (Bölüm 49'da göreceğin en çok olabilirlik ilkesi) ile aynı şeydir. Bölüm 57'de değerlendirme metriklerinde, Bölüm 63'te geri yayılımda, Bölüm 70'te dil modellerinde perplexity'de ve Bölüm 72'de değişimsel otomatik kodlayıcıda (VAE) **Kullback-Leibler ıraksaması** (KL) yine karşına çıkacak. Bu bölümde bu terimleri sıfırdan tanımlayıp hesaplayacağız.

Savunma sanayiinde aynı sorular somut hâle gelir. Bir hedef takip hattında sensör okuması ile hedefin gerçek durumu arasında ne kadar bilgi vardır? Bir telemetri bağında saniyede kaç bit taşınabilir ve gürültü arttığında hangi kodla ne kadar veri kurtarılır? Bu soruların hepsi tek bir hesapla cevaplanabilir.

Yaklaşımımız aynıdır: her kavram için bir tanım, bir sezgi, Python ile bir hesap ve bir simülasyon. Simülasyonlarda sabit tohum (`random.Random(51)`) kullanıyoruz; böylece aynı sayıları sen de elde edebilirsin. Bölüm 18'de Huffman kodunun gerçek bir metinde entropiye ne kadar yaklaştığını ölçmüştük. Bu bölüm, o ölçümün neden o değerleri verdiğini açıklıyor.

::: not
Bu bölümdeki her sayı bir programın çıktısıdır. Ölçümler `bolumler/` klasöründeki 1–46 numaralı bölümlerin düz metni üzerinde yapıldı. Bölüm 47 ve sonrası yazılırken değişebileceği için kapsam bilerek 46 ile sınırlandı. Corpus özeti (SHA-256'nın ilk 16 karakteri) çıktıda yer alıyor; aynı özeti veren bir metin kümesiyle sonuçları birebir tekrar üretebilirsin.
:::

## 51.1 Bilgi nedir? Şaşırma olarak öz bilgi

Günlük dilde "bilgi" kelimesini belirsizliğin azalması anlamında kullanırız. "Yarın güneş doğacak" cümlesi neredeyse hiçbir şey söylemez; herkes bunu zaten bilir. "Yarın Ankara'da kar yağacak" cümlesi ise bir şey öğretir, çünkü beklenmedik bir olayı haber verir. Bilgi teorisi bu sezgiyi tam olarak şöyle ölçer: bir olay, olasılığı küçükken gerçekleştiğinde daha çok şaşırtır ve daha çok bilgi taşır.

Bir `x` olayının **öz bilgisi** (self-information), olasılığı `p(x)` iken şöyle tanımlanır:

I(x) = −log₂ p(x)   (bit)

Neden logaritma? İki bağımsız olay düşünelim: `P(A ve B) = P(A) · P(B)`. İki olayın birlikte verdiği bilginin, tek tek verdiklerinin toplamı olmasını istiyoruz. Çarpımı toplama çeviren tek ailesel dönüşüm logaritmadır; bu, log'un tercih edilmesinin temel nedenidir (fonksiyonel denklem sonucu, genel bilgi). Eksi işareti ise olasılık küçüldükçe öz bilginin büyümesini sağlar, çünkü `0 < p ≤ 1` için `−log₂ p ≥ 0` olur.

Birim olarak `log₂` kullanıldığında sonuç **bit** çıkar. Bir bit, bir evet-hayır sorusunun cevabıdır. Olasılığı yarıya indiren her soru bir bit kazandırır: 8 eşit olasılıklı seçenekten birini bulmak için 3 soru yeter, çünkü `−log₂(1/8) = 3`. Doğal logaritma kullanılırsa birim **nat** olur (`1 nat = 1/ln 2 ≈ 1,4427 bit`). Makine öğrenmesi literatüründe çoğu zaman nat tercih edilir; bunu Bölüm 51.10'da göreceksin.

Birkaç değerle sezgiyi pekiştirelim:

| Olay | Olasılık p | Öz bilgi −log₂ p (bit) |
|---|---|---|
| Adil madeni paranın tura gelmesi | 0,5 | 1,000 |
| Zarın 6 gelmesi | 1/6 | 2,585 |
| Yağmurun yağmaması (çok olası) | 0,9 | 0,152 |
| Nadir bir arıza olayı | 0,01 | 6,644 |

Son satırı dikkatle oku. Nadir arıza, sıradan gündelik olaydan yaklaşık kırk kat daha fazla bilgi taşır. Bir telemetri sisteminde bu fark, "normal" değerleri ucuza, anomalileri pahalıya kodlamanın mantığıdır. Bölüm 51.5'te bunun kodlamaya nasıl yansıdığını göreceğiz.

## 51.2 Entropi: beklenen şaşırma

Bir kaynağın öz bilgisi her sembol için farklıdır. Kaynağın **entropisi** (entropy), bu öz bilgilerin olasılığa göre ağırlıklı ortalamasıdır:

H(X) = ∑ p(x) · (−log₂ p(x))   (bit)

Entropi, bir kaynaktan ortalama olarak bir sembol başına gelen belirsizliğin bit cinsinden ölçüsüdür. Üç temel özelliği hemen aklında tutmalısın:

- H(X) ≥ 0 ve H(X) = 0 olması için kaynak kesin olmalıdır (tek bir sembol olasılığı 1 ise).
- Bir kaynağın alfabesi `n` sembol içeriyorsa, en büyük entropi düzgün dağılımda elde edilir: H(X) ≤ log₂ n. Eşitlik yalnızca düzgün dağılımda geçerlidir. Bu sınırın ispatı Bölüm 51.9'daki Gibbs eşitsizliğinden çıkar.
- Entropi, sembollerin *değerlerine* değil yalnızca *olasılıklarına* bağlıdır. "a" ile "z" adlarını değiştirmek entropiyi değiştirmez.

Yazı-tura ile zar arasındaki farkı düşün. Adil madeni parada iki sonuç da eşit olasılıklıdır ve entropi tam 1 bittir. Çarpık bir parada (tura olasılığı 0,9) sonuç daha az şaşırtır ve entropi 0,469 bite düşer. Zarda altı eşit sonuç vardır, entropi `log₂ 6 ≈ 2,585` bittir. Şekil 51.1 ikili bir kaynağın entropisinin olasılıkla nasıl değiştiğini gösterir: en yüksek nokta `p = 0,5`'tedir ve orada kaynak en belirsizdir.

![Şekil 51.1: İkili entropi H(p). En büyük değer p = 0,5'te 1 bit; olasılık uçlara yaklaştıkça entropi sıfıra iner.](gorseller/b51_ikili_entropi.png)

Aşağıdaki program entropi hesabının yanında ortak entropi, koşullu entropi ve karşılıklı bilgi için gerekli tüm fonksiyonları içerir. Önce tek boyutlu entropiye bakalım; geri kalanı Bölüm 51.4'te açıklanıyor. Program üç parçaya bölünmüştür; tam hâli sırayla okunabilir.

```python
# entropi_temel.py: öz bilgi, entropi, ortak ve koşullu entropi,
# karşılıklı bilgi. Tüm hesaplar bit (log2) cinsinden yapılır.
import math
import random

def ozbilgi(p):
    # p olasılıklı bir olay gerçekleşince kazanılan şaşırma: -log2 p.
    return -math.log2(p)

def entropi(dagilim):
    # H = sum p * (-log2 p). p = 0 olan terim 0 katkı verir.
    return sum(p * ozbilgi(p) for p in dagilim if p > 0)

# Ortak tablo P(X=x, Y=y). Satır: X (sensör okuması),
# sütun: Y (gerçek durum: boş, küçük hedef, büyük hedef).
ORTAK = [
    [0.4400, 0.0300, 0.0050],   # x = boş diyor
    [0.2400, 0.0900, 0.0150],   # x = belirsiz
    [0.0300, 0.0700, 0.0800],   # x = hedef diyor
]

def marjinal(ortak):
    px = [sum(satir) for satir in ortak]
    py = [sum(ortak[i][j] for i in range(len(ortak)))
          for j in range(len(ortak[0]))]
    return px, py

def ortak_entropi(ortak):
    # H(X,Y): tüm hücrelerin entropisi.
    return entropi([v for satir in ortak for v in satir])

def kosullu_entropi(ortak):
    # H(Y|X) = H(X,Y) - H(X)  (zincir kuralı)
    px, _ = marjinal(ortak)
    return ortak_entropi(ortak) - entropi(px)

def karsilikli_bilgi(ortak):
    # I(X;Y) = H(X) + H(Y) - H(X,Y)
    px, py = marjinal(ortak)
    return entropi(px) + entropi(py) - ortak_entropi(ortak)
```

Bu ilk parçada iki temel fonksiyon var. `ozbilgi` tek bir olayın şaşırmasını verir. `entropi` ise tüm dağılımın ağırlıklı ortalamasını alır. `p > 0` koşulu önemlidir: `p = 0` olan bir sembol hiç gelmediği için katkı vermez ve `0 · log 0` tanımsız görünse de sınırda 0'a gider. Python'da `log2(0)` hata verir, bu yüzden koşulu ihmal etmemek gerekir.

Aşağıdaki parça, sensör örneğinin ortak tablosunu tanımlar ve marjinal dağılımları hesaplar. Bu tablo Bölüm 51.4'te ayrıntısıyla ele alınacak.

```python
def denetle():
    toplam = sum(v for satir in ORTAK for v in satir)
    assert abs(toplam - 1.0) < 1e-12, toplam

def main():
    denetle()
    print("Zar (6 yüz):  H = %.4f bit" % entropi([1/6]*6))
    print("Adil yazı-tura: H = %.4f bit" % entropi([0.5, 0.5]))
    print("Çarpık yazı-tura (0.9): H = %.4f bit"
          % entropi([0.9, 0.1]))
    print("Öz bilgi, p=1/8: %.1f bit" % ozbilgi(1/8))
    px, py = marjinal(ORTAK)
    print("P(X) =", [round(v, 4) for v in px])
    print("P(Y) =", [round(v, 4) for v in py])
    hx, hy = entropi(px), entropi(py)
    hxy = ortak_entropi(ORTAK)
    hyx = kosullu_entropi(ORTAK)
    i = karsilikli_bilgi(ORTAK)
    print("H(X)   = %.4f" % hx)
    print("H(Y)   = %.4f" % hy)
    print("H(X,Y) = %.4f" % hxy)
    print("H(Y|X) = %.4f" % hyx)
    print("I(X;Y) = %.4f" % i)
    print("zincir kurali hatasi: %.1e" % abs(hxy - (hx + hyx)))
    # Tekdüze dağılım en büyük entropiyi verir: H <= log2 n
    rnd = random.Random(51)
```

Son parça ana programdır. Denetim ve rastgele testler ilk kez burada yapılır.

```python
    ihlal = 0
    for _ in range(1000):
        w = [rnd.random() for _ in range(6)]
        s = sum(w)
        if entropi([v / s for v in w]) > math.log2(6) + 1e-12:
            ihlal += 1
    print("1000 rastgele 6'lı dağılım, H > log2 6 olan: %d" % ihlal)
    # Bağımsız X,Y için I(X;Y) = 0 olmalı.
    bagimsiz = [[a * b for b in py] for a in px]
    print("Bağımsız tablo için I(X;Y) = %.1e"
          % karsilikli_bilgi(bagimsiz))
    # Rastgele tablolarda I(X;Y) negatif olabilir mi? Olamaz.
    negatif = 0
    for _ in range(1000):
        w = [[rnd.random() for _ in range(3)] for _ in range(3)]
        s = sum(v for satir in w for v in satir)
        t = [[v / s for v in satir] for satir in w]
        if karsilikli_bilgi(t) < -1e-12:
            negatif += 1
    print("1000 rastgele ortak tablo, I < 0 olan: %d" % negatif)

if __name__ == "__main__":
    main()
```

Programı çalıştırdığında şu çıktıyı alırsın:

```term
$ python entropi_temel.py
Zar (6 yüz):  H = 2.5850 bit
Adil yazı-tura: H = 1.0000 bit
Çarpık yazı-tura (0.9): H = 0.4690 bit
Öz bilgi, p=1/8: 3.0 bit
P(X) = [0.475, 0.345, 0.18]
P(Y) = [0.71, 0.19, 0.1]
H(X)   = 1.4851
H(Y)   = 1.1382
H(X,Y) = 2.3206
H(Y|X) = 0.8355
I(X;Y) = 0.3027
zincir kurali hatasi: 0.0e+00
1000 rastgele 6'lı dağılım, H > log2 6 olan: 0
Bağımsız tablo için I(X;Y) = 4.4e-16
1000 rastgele ortak tablo, I < 0 olan: 0
```

İlk üç satır, zar ve madeni para örneklerinin değerlerini doğrular: `log₂ 6 = 2,5850`, adil para `1,0000` bit ve çarpık para `0,4690` bit. Beşinci satırdan itibaren sensör tablosunun sonuçları vardır. Son iki satır, sezgiyi sınayan simülasyonlardır: rastgele seçilen 1000 altı-sınıflı dağılımın hiçbiri `log₂ 6`yı aşmadı ve rastgele 1000 ortak tablonun hiçbirinde karşılıklı bilgi negatif çıkmadı. Bu iki gözlem bir kanıt değildir, ama yanlış bir formül yazdığında genellikle ilk önce burada yakalanır.

## 51.3 Kitabın kendi metninde entropi: sıfırıncı ve birinci derece

Bir dili modellemenin en basit yolu, her harfi bağımsız ve kendi sıklığıyla seçmektir. Buna **sıfırıncı derece** (0. derece) model denir. Oysa Türkçede harfler bağımsız değildir: `q` harfinden sonra neredeyse her zaman `u` gelir, `ğ` hiçbir zaman kelime başında yer almaz. Bağlamı bilmek belirsizliği azaltır. Bu, **koşullu entropi** kavramının dilde somut karşılığıdır.

Birinci derece (1. derece) koşullu entropi, bir harfin bir önceki harf bilindiğinde ne kadar belirsiz olduğunu ölçer:

H(X₂ | X₁) = H(X₁, X₂) − H(X₁)

Burada `H(X₁, X₂)` iki harfli dizilerin (bigram) entropisi, `H(X₁)` ise ilk harfin entropisidir. Aynı mantıkla `H(X₃ | X₁, X₂) = H(üçlü) − H(ikili)` ikinci derece koşullu entropiyi verir. Bağlam uzadıkça entropi düşer, ama örneklem (metin) sınırlı olduğu için düşüş sonsuza kadar devam etmez. Bu tuzağa Bölüm 51.3'ün sonunda tekrar döneceğiz.

Aşağıdaki program, kitabın 1–46 numaralı bölümlerinin düz metninden harf ve bayt entropilerini hesaplar. Kod blokları, tablolar ve şekil satırları ölçüme katılmaz; yalnızca okunan Türkçe metin sayılır. Türkçede büyük `I` harfinin küçüğü `ı`dır, `İ`nin küçüğü `i`dir; Python'un varsayılan dönüşümü bu yüzden yanlış olur ve program bunu düzeltir.

```python
# olcum_metin.py: kitabın bölüm metinlerinde harf ve bayt entropisi;
# 0., 1., 2. dereceden (koşullu) entropi karşılaştırması.
# Kullanım: python olcum_metin.py <bolumler klasörü> <veri klasörü>
import csv
import glob
import hashlib
import math
import os
import re
import sys
from collections import Counter

ALFA = "abcçdefgğhıijklmnoöprsştuüvyz"   # 29 Türkçe harf
SON_BOLUM = 46                           # ölçüm 1..46 üzerinde

def tr_kucuk(s):
    # Türkçe büyük/küçük harf: I -> ı, İ -> i
    # (Python'un varsayılanı yanlış)
    return s.replace("I", "ı").replace("İ", "i").lower()

def duz_metin(md):
    # Kod bloklarını, tabloları, şekil satırlarını, kutu işaretlerini
    # at.
    cikti, kodda = [], False
    for satir in md.splitlines():
        if satir.startswith("```"):
            kodda = not kodda
            continue
        if kodda or satir.startswith(("|", "![", "%%", ":::")):
            continue
        cikti.append(satir)
    return "\n".join(cikti)
```

Bu parçada metni temizleyen `duz_metin` ve Türkçe küçültme fonksiyonu var. Bu temizlik sonucu değiştirir: kod örnekleri entropiyi düşürür, çünkü tekrar eden `def`, `print` gibi kelimeler yapay bir düzen taşır. Ölçümü yalnızca doğal dil üzerinde yapmak istiyoruz.

```python
def entropi_sayim(sayac):
    # Ölçülen (plug-in) entropi: H = -sum (c/n) log2 (c/n)
    n = sum(sayac.values())
    return -sum(c / n * math.log2(c / n) for c in sayac.values())

def kosullu(dizi, k):
    # H(X_k | X_1..X_{k-1}) = H(k-gram) - H((k-1)-gram)
    if k == 1:
        return entropi_sayim(Counter(dizi))
    n = len(dizi) - k + 1
    kgram = Counter(tuple(dizi[i:i + k]) for i in range(n))
    onceki = Counter(tuple(dizi[i:i + k - 1])
                     for i in range(len(dizi) - k + 1))
    return entropi_sayim(kgram) - entropi_sayim(onceki)
```

`entropi_sayim` sayımlardan plug-in entropi hesaplar: her sayının oranını alıp `−∑ (c/n) log₂ (c/n)` toplamını verir. `kosullu` fonksiyonu, `k`-gram sayımlarından `H(k-gram) − H((k−1)-gram)` farkını alır. Bu fark, son harfin öncekilere koşullu entropisidir.

```python

def main(kok, veri):
    dosyalar = []
    for yol in sorted(glob.glob(os.path.join(kok, "bolum_*.md"))):
        no = int(re.search(r"bolum_(\d+)\.md", yol).group(1))
        if no <= SON_BOLUM:
            dosyalar.append(yol)
    ham = b""
    for yol in dosyalar:
        with open(yol, "rb") as f:
            ham += f.read()
    print("dosya sayisi:", len(dosyalar))
    ozet = hashlib.sha256(ham).hexdigest()[:16]
    print("corpus sha256:", ozet, "...")
    metin = duz_metin("\n".join(open(y, encoding="utf-8").read()
                                for y in dosyalar))
    harf = [c for c in tr_kucuk(metin) if c in ALFA]
    print("harf sayisi:", len(harf), " farkli harf:", len(set(harf)))
    print("ust sinir log2(29) = %.4f" % math.log2(29))
    olc = [("harf", "H0 (bagimsiz)", kosullu(harf, 1)),
           ("harf", "H(X2|X1)", kosullu(harf, 2)),
           ("harf", "H(X3|X1X2)", kosullu(harf, 3))]
    bayt = list(metin.encode("utf-8"))
    olc += [("bayt", "H0 (bagimsiz)", kosullu(bayt, 1)),
            ("bayt", "H(X2|X1)", kosullu(bayt, 2))]
    print("%-6s %-14s %s" % ("alfabe", "model", "bit/simge"))
```

Ana fonksiyon, corpus özetini hesaplar, ölçümleri yazdırır ve iki CSV dosyası üretir. Bu CSV'ler Şekil 51.2 ve 51.3'ü çizer. Son satırlar bloğun çıktı biçimini belirler.

```python
    for a, m, h in olc:
        print("%-6s %-14s %.4f" % (a, m, h))
    print("duz metin bayt: %d, bayt/harf: %.3f"
          % (len(bayt), len(bayt) / len(harf)))
    # CSV 1: harf sıklıkları (şekil 51.x için)
    n = len(harf)
    sayac = Counter(harf)
    yol = os.path.join(veri, "b51_harf.csv")
    with open(yol, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["harf", "sayi", "olasilik", "ozbilgi_bit"])
        for h in ALFA:
            c = sayac.get(h, 0)
            w.writerow([h, c, "%.6f" % (c / n),
                        "%.4f" % (-math.log2(c / n))])
    # CSV 2: entropi düzeyleri
    with open(os.path.join(veri, "b51_metin_entropi.csv"), "w",
              encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["alfabe", "model", "bit_per_simge"])
        for a, m, h in olc:
            w.writerow([a, m, "%.4f" % h])

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
```

Programı çalıştırdığında şu sonuçları alırsın:

```term
$ python olcum_metin.py bolumler engine\veri
dosya sayisi: 46
corpus sha256: 22730ee5a7c18739 ...
harf sayisi: 1996285  farkli harf: 29
ust sinir log2(29) = 4.8580
alfabe model          bit/simge
harf   H0 (bagimsiz)  4.4102
harf   H(X2|X1)       3.7807
harf   H(X3|X1X2)     3.1128
bayt   H0 (bagimsiz)  5.1051
bayt   H(X2|X1)       3.5316
duz metin bayt: 2859071, bayt/harf: 1.432
```

Sonuçları okuyalım. Metinde 1 996 285 harf vardır ve bunların 29'u Türkçe alfabe harfidir (noktalama ve sayılar sayılmadı). Sıfırıncı derece harf entropisi `H0 = 4,4102` bit/harftir. Üst sınır `log₂ 29 = 4,8580`dir; gerçek dağılım düzgün değildir, bu yüzden entropi üst sınırın altında kalır. Şekil 51.2 bu eşitsizliğin nedenini gösterir: `a`, `e`, `i`, `r`, `n` harfleri toplam metnin büyük bölümünü oluşturur, `j` ve `f` gibi harfler nadirdir.

Bağlam bilgisi büyük fark yaratır. İki harfli bağlamla koşullu entropi `3,7807` bite, üç harfli bağlamla `3,1128` bite iner. Yani bir harfi tahmin etmek için önceki iki harfi bilmek, ortalama olarak yaklaşık bir bit kazandırır. Bu, bir sıkıştırıcının dil modeli gibi davranarak neden daha az bit harcadığını açıklar.

![Şekil 51.2: Kitabın 1–46 numaralı bölümlerindeki Türkçe harf olasılıkları, azalan sıraya göre. H0 = 4,410 bit/harf; üst sınır log₂ 29 = 4,858.](gorseller/b51_harf_frekans.png)

Bayt düzeyinde ölçüm de aynı dört değeri verir: sıfırıncı derece `5,1051` bit/bayt ve bir önceki baytla koşullu `3,5316` bit/bayt. Türkçe harflerin çoğu UTF-8'de iki bayt tutar (ç, ğ, ı, ö, ş, ü), bu yüzden bayt entropisi harf entropisinden büyüktür. Harf başına düşen bayt sayısı `1,432`dir; yani metindeki her harf ortalama 1,43 bayt yer tutar. Bu ayrım Bölüm 18'de yaptığımız Huffman ölçümünün neden bayt üzerinde yapıldığını da açıklar.

![Şekil 51.3: Harf ve bayt için 0. ve koşullu entropi düzeyleri (bit/simge). Kesikli çizgi harf alfabesinin üst sınırıdır.](gorseller/b51_entropi_duzeyleri.png)

Şimdi tuzağa dönelim. `H(X₃ | X₁X₂) = 3,1128` değeri, üçlü bağlamın tahmin gücünü gösterir. Ancak üçlü sayısı `29³ = 24 389` hücreye çıkar ve metinde yaklaşık iki milyon harf vardır. Hücre başına düşen örnek sayısı yeterince büyük olsa da, plug-in tahminci küçük olasılıklı hücrelerde entropiyi hafifçe **aşağı** çeker. Metinde 841 olası harf çiftinden 805'i, 24 389 olası üçlüden ise yalnızca 13 826'sı görülmüştür. Seyrek hücrelerin yarattığı sapmayı Miller-Madow tarzı bir düzeltmeyle kabaca tahmin edersek yaklaşık `0,005` bit çıkar; bu bir tahmindir, kesin bir değer değildir. Bunun önemi şudur: bağlam uzadıkça entropi ölçümü güvenilirliğini kaybeder. Dil modellerinin (Bölüm 70) bu sorunu aşmak için neden parametrik modeller kullandığını böylece anlarsın.

Bölüm 18'deki ölçümle bağlayalım. Orada Huffman kodunun düz metinde yalnızca yaklaşık `%64,6`ya indiğini, gzip'in ise `%33,8`e indiğini gördük. Bu fark tesadüf değildir. Bir Huffman kodu yalnızca sembol olasılıklarını kullanır; yani yukarıdaki `H0` değerine (bayt için 5,1 bit) en fazla yaklaşabilir. Gzip ise sembol olasılıklarından fazlasını, yani tekrarları, kullanır. Bölüm 51.7'de bu ikinci mekanizmayı (LZ77) ayrıca göreceğiz.

## 51.4 Ortak ve koşullu entropi, zincir kuralı, karşılıklı bilgi

Tek bir kaynak yerine iki rastgele değişkeni birlikte düşünelim: `X` bir sensörün okuduğu değer, `Y` ise hedefin gerçek durumu olsun. İkisinin **ortak entropisi** (joint entropy) `H(X, Y) = −∑ p(x,y) log₂ p(x,y)` toplamıdır. Bu iki değişkenin birlikte ne kadar belirsiz olduğunu gösterir.

**Koşullu entropi** `H(Y | X)`, `X` bilindikten sonra `Y`nin ne kadar belirsiz kaldığını ölçer. Tanımı şöyledir: `H(Y | X) = ∑ p(x) H(Y | X = x)`. Bu tanımın kullanışlı biçimi **zincir kuralıdır**:

H(X, Y) = H(X) + H(Y | X)

Zincir kuralı sezgisel olarak açıktır: iki şeyi öğrenmek için önce birini, sonra diğerini öğrenmenin toplam maliyeti aynıdır. Programda bu eşitliği her çalıştırmada sayısal olarak kontrol ediyoruz; çıktıdaki `zincir kurali hatasi` satırı sıfır olmalıdır.

**Karşılıklı bilgi** (mutual information) iki değişken arasında paylaşılan bilgiyi ölçer:

I(X; Y) = H(X) + H(Y) − H(X, Y) = H(Y) − H(Y | X)

Karşılıklı bilgi simetriktir, yani `I(X;Y) = I(Y;X)`. Negatif olmaz (bunun kanıtı Gibbs eşitsizliğine dayanır, Bölüm 51.9). `X` ile `Y` bağımsızsa sıfırdır. Bu, bağımsızlık testine bilgi teorisinden bakmanın bir yoludur: korelasyon yalnızca doğrusal bağımlılığı yakalar, karşılıklı bilgi ise her türlü bağımlılığı yakalar.

Sensör örneğimizin ortak tablosu şöyledir. Satırlar sensör okumasıdır (`boş`, `belirsiz`, `hedef` diyor), sütunlar gerçek durumdur:

| Sensör \ Gerçek | boş | küçük hedef | büyük hedef | P(X) |
|---|---|---|---|---|
| boş diyor | 0,4400 | 0,0300 | 0,0050 | 0,4750 |
| belirsiz | 0,2400 | 0,0900 | 0,0150 | 0,3450 |
| hedef diyor | 0,0300 | 0,0700 | 0,0800 | 0,1800 |
| P(Y) | 0,7100 | 0,1900 | 0,1000 | 1,0000 |

Bu tablodan entropi değerlerini hesaplarsak `H(X) = 1,4851`, `H(Y) = 1,1382`, `H(X,Y) = 2,3206` bit çıkar. Buradan `H(Y|X) = 2,3206 − 1,4851 = 0,8355` ve `I(X;Y) = 1,4851 + 1,1382 − 2,3206 = 0,3027` bit bulunur. Yani sensör okuması, gerçek durum hakkında ortalama 0,30 bit bilgi taşıyor. Hedef ne kadar belirsizse (`H(Y) = 1,14`), sensörün bu belirsizliği ne kadar azalttığı `I(X;Y)` ile ölçülür: yaklaşık `%27` (0,3027 / 1,1382).

![Şekil 51.4: H(X), H(Y), I(X;Y) ve H(X,Y) ilişkisi. Ortak bölge karşılıklı bilgidir; dış çerçeve ortak entropidir.](gorseller/b51_venn_iliski.png)

Bu sayılar bir öznitelik seçimine nasıl bağlanır? Bir özniteliğin hedef etiketiyle karşılıklı bilgisi büyükse, o öznitelik etiket hakkında çok şey söyler. Ağaç tabanlı yöntemler (Bölüm 59) bölünmeyi seçerken bu büyüklüğe yakın bir ölçüt olan **bilgi kazancını** kullanır. Öznitelik mühendisliğini Bölüm 56'da göreceksin; orada karşılıklı bilginin ne zaman yanıltıcı olabileceğini (örneğin çok değerli kategorik öznitelikler) tartışacağız.

Bir kritik sonuç daha vardır. Bir veri işleme adımı (örneğin bir filtre ya da bir sınıflandırıcı) `X → Y → Z` zincirini oluşturuyorsa, `I(X;Z) ≤ I(X;Y)` olur. Bu **veri işleme eşitsizliğidir** ve hiçbir işlemin yeni bilgi üretemeyeceğini söyler. Bölüm 51.11'de bunu bir kanal zincirinde sayısal olarak göstereceğiz.

## 51.5 Kaynak kodlama: Shannon'ın sınırı ve Kraft eşitsizliği

Bir kaynağı sıkıştırmak, her sembole ikili bir kod sözcüğü atamak demektir. İki koşul vardır. Birincisi, kod çözülebilir olmalı: iki farklı mesaj aynı bit dizisine düşmemeli. İkincisi, kod **öneksiz** (prefix) olmalı: hiçbir kod sözcüğü başka bir kod sözcüğünün başı olmamalı. Öneksiz kodda bit akışını soldan sağa okuyunca kelime sınırını anında tanırsın; bunu Bu, sıradan bir ayrıştırıcının kelimeleri ayırmasıyla aynı sezgidir.

Öneksiz bir kodun kelime uzunlukları `l₁, l₂, ..., lₙ` rastgele seçilemez. Bunları sınırlayan eşitsizlik **Kraft eşitsizliğidir**:

∑ 2^(−lᵢ) ≤ 1

Bu eşitsizliği şöyle sezebilirsin. İkili bir ağaçta her düzeyde düğüm sayısı ikiye katlanır. Kökten `lᵢ` derinliğindeki bir yaprağa giden yol, o derinlikteki toplam yolların `2^(−lᵢ)` oranını "tüketir". Öneksizlik, tüketilen oranların toplamının en fazla 1 olmasını zorunlu kılar. McMillan'ın genellemesi, yalnızca öneksiz değil, her çözülebilir kodun aynı eşitsizliği sağladığını gösterir (genel bilgi).

Şimdi kaynak kodlamanın alt sınırına gelelim. Bir kaynağın ortalama kod uzunluğu `L = ∑ pᵢ lᵢ` olsun. **Shannon'ın kaynak kodlama teoremi** şunu söyler: her çözülebilir kod için `L ≥ H(X)`'tir ve bu sınıra istenildiği kadar yaklaşan kodlar vardır. Tek sembol kodlamasında bu sınıra en çok bir bit yaklaşılabilir: `H ≤ L < H + 1`. Bölüm 18'de bu eşitsizliği gerçek metinde görmüştük. Burada nedenini kanıtlayacak ve Huffman kodunun optimal olduğunu sınayacağız.

Aşağıdaki program dört sembollü bir kaynak için Huffman kod uzunluklarını bulur, Kraft toplamını hesaplar ve rastgele kaynaklarda `L − H` farkını ölçer. Huffman'ın optimalliği, tüm tamsayı uzunluk vektörlerini deneyen bir kaba kuvvet aramasıyla sınanır. Program dört bloğa bölünmüştür.

```python
# kraft_huffman.py: Kraft eşitsizliği, Huffman kod uzunlukları,
# entropiye uzaklık (H <= L < H + 1) ve Huffman'ın optimalliğinin
# kaba kuvvet denetimi.
import heapq
import itertools
import math
import random

def entropi(p):
    return -sum(x * math.log2(x) for x in p if x > 0)

def kraft_toplam(uzunluk):
    # Öneksiz (prefix) kod için sum 2^(-l_i) <= 1 olmalıdır.
    return sum(2.0 ** -l for l in uzunluk)

def huffman_uzunluk(p):
    # Her yaprak için kod uzunluğu: birleştirilen her düğümde
    # o düğümdeki yaprakların derinliği 1 artar.
    uz = [0] * len(p)
    kuyruk = [(x, [i]) for i, x in enumerate(p)]
    heapq.heapify(kuyruk)
    while len(kuyruk) > 1:
        a, ga = heapq.heappop(kuyruk)
        b, gb = heapq.heappop(kuyruk)
        for i in ga + gb:
            uz[i] += 1
        heapq.heappush(kuyruk, (a + b, ga + gb))
    return uz

def ortalama(p, uz):
    return sum(x * l for x, l in zip(p, uz))

def kaba_kuvvet(p, enbuyuk=4):
    # Tüm tamsayı uzunluk vektörlerini dene; Kraft <= 1 olanlar
    # arasında
    # en küçük ortalama uzunluğu bul.
    en = math.inf
    for uz in itertools.product(range(1, enbuyuk + 1), repeat=len(p)):
        if kraft_toplam(uz) <= 1.0 + 1e-12:
            en = min(en, ortalama(p, uz))
    return en
```

`huffman_uzunluk` fonksiyonu Huffman ağacını kurmanın bir yolunu kullanır: en küçük iki olasılığı birleştirir ve birleşen düğümdeki her yaprağın derinliğini bir artırır. Ağaç kurmadan yalnızca uzunlukları izlemek yeterlidir, çünkü kod sözcüklerinin kendisi uzunluklar belirlendikten sonra kolayca atanabilir. `kaba_kuvvet` fonksiyonu, `enbuyuk=4` sınırına kadar tüm uzunluk vektörlerini tarar ve Kraft eşitsizliğini sağlayanlar arasından en küçük ortalamayı seçer. Dört sembol için derinlik sınırı `n − 1 = 3`'tür, bu yüzden dört sınır yeterlidir.

```python

def main():
    p = [0.4, 0.3, 0.2, 0.1]
    h = entropi(p)
    uz = huffman_uzunluk(p)
    print("p      =", p)
    print("H(p)   = %.4f bit" % h)
    print("uzunluk =", uz, " Kraft toplam =", kraft_toplam(uz))
    print("L      = %.4f bit" % ortalama(p, uz))
    print("L - H  = %.4f bit" % (ortalama(p, uz) - h))
    rnd = random.Random(51)
    en_buyuk_fark, sayi = 0.0, 0
    for _ in range(1000):
        n = rnd.randint(2, 8)
        w = [rnd.random() ** 3 + 1e-6 for _ in range(n)]
        s = sum(w)
        q = [v / s for v in w]
        u = huffman_uzunluk(q)
        L, H = ortalama(q, u), entropi(q)
        assert H - 1e-12 <= L < H + 1.0 + 1e-12
        en_buyuk_fark = max(en_buyuk_fark, L - H)
```

Ana fonksiyon, örnek kaynağın sonuçlarını yazdırır ve iki rastgele denetim yapar. Rastgele kaynakların olasılıkları sabit tohumlu bir üreteçten gelir.

```python
        sayi += 1
    print("%d rastgele kaynak: en buyuk L - H = %.4f (sinir 1)" % (
        sayi, en_buyuk_fark))
    # Optimallik: 300 rastgele 4'lü dağılımda kaba kuvvet = Huffman
    eslesen = 0
    for _ in range(300):
        w = [rnd.random() + 0.01 for _ in range(4)]
        s = sum(w)
        q = [v / s for v in w]
        opt = ortalama(q, huffman_uzunluk(q))
        if abs(kaba_kuvvet(q) - opt) < 1e-9:
            eslesen += 1
    print("300 rastgele 4'lu kaynakta Huffman = kaba kuvvet: %d"
          % eslesen)

if __name__ == "__main__":
    main()
```

```term
$ python kraft_huffman.py
p      = [0.4, 0.3, 0.2, 0.1]
H(p)   = 1.8464 bit
uzunluk = [1, 2, 3, 3]  Kraft toplam = 1.0
L      = 1.9000 bit
L - H  = 0.0536 bit
1000 rastgele kaynak: en buyuk L - H = 0.9999 (sinir 1)
300 rastgele 4'lu kaynakta Huffman = kaba kuvvet: 300
```

İlk örnekte `p = [0,4; 0,3; 0,2; 0,1]` için `H(p) = 1,8464` bit. Huffman uzunlukları `[1, 2, 3, 3]`tür ve Kraft toplamı tam `1,0`dır: kodun ağacı tamamen doludur, boşluk kalmamıştır. Ortalama uzunluk `L = 1,9` bittir. Bu, entropinin `0,0536` bit üstünde demektir; `H ≤ L < H + 1` sınırı burada rahatça sağlanır.

Rastgele 1000 kaynağın en büyük `L − H` farkı `0,9999` çıktı. Bu, farkın bir bite ne kadar yaklaşabildiğini gösterir: bazı çarpık dağılımlarda Huffman neredeyse tam bir bit kaybeder. Ortalama davranış iyidir, en kötü durum iyi değildir. Bu kötü durumu Bölüm 51.6'da aritmetik kodlamanın nasıl önlediğini göreceğiz.

Optimallik sınaması ise tam eşleşme verdi: 300 rastgele dört sembollü kaynağın tamamında Huffman'ın ortalama uzunluğu, kaba kuvvetle bulunan en iyi öneksiz kodun uzunluğuna eşit çıktı. Bu bir kanıt değildir, ama Huffman'ın optimalliğinin (1952'de Huffman'ın verdiği ispatın) doğruluğunu sayısal olarak doğrular. İspatın özü şudur: en az olasılıklı iki sembol en derin iki yaprağa konulabilir; bu, herhangi bir optimal ağacın yapısını değiştirmeden yapılabilir.

## 51.6 Aritmetik kodlama: bir sayı ile tüm mesaj

Huffman'ın bir sınırı var: her sembol tam sayı bit ile kodlanır. `p = 0,9` olasılıklı bir sembol gerçekte `−log₂ 0,9 = 0,152` bit taşır, ama Huffman ona en az bir bit verir. Çarpık kaynaklarda bu fark büyüktür. Üç sembollü `p = [0,9; 0,05; 0,05]` kaynağında Huffman ortalama `1,1` bit harcar; oysa entropi `0,569` bittir. Huffman'ın kaybı, ortalama uzunluk ile entropi arasındaki yarım bitten fazladır.

**Aritmetik kodlama** bu kısıtı ortadan kaldırır. Fikir, tüm mesajı `[0, 1)` aralığında bir alt aralığa eşlemektir. Her sembol, aralığı kendi olasılığı oranında daraltır. Mesaj bittiğinde, son aralığın içinden bir sayı seçmek yeterlidir. Bu sayının bit gösterimi, mesajın olasılığının `−log₂` değeri kadar uzunluğa yaklaşır: `−log₂ P(mesaj) + 2` bit. Mesaj uzadıkça sembol başına maliyet `H`ye yaklaşır, çünkü kesirli bitler birikir ve tam sayı zorunluluğu yok olur.

Gerçek bir uygulamada kesirli sayıları sonsuz hassasiyetle tutamayız. Witten, Neal ve Cleary'nin 1987 tarihli tamsayı gerçeklemesi bu sorunu 32 bitlik aralıklarla çözer. Aralık her adımda daraltılır; üst ve alt yarılar aynı tarafa düşerse ortak en büyük bit yazılır ve aralık genişletilir. Aralık orta noktanın iki yanına aynı anda düşerse (ki bu underflow durumudur) ters bitler bir sayaçta bekletilir ve uygun anda yazılır. Aşağıdaki program bu mekanizmayı, kodlayıcı ve çözücüyü birlikte içerir. Frekanslar tamsayı olarak verilir ve toplamları `2³⁰`u geçmemelidir.

```python
# aritmetik.py: tamsayı aritmetik kodlayıcı
# (Witten, Neal, Cleary 1987).
# Olasılıklar tamsayı frekanslarla verilir. Toplam 2^30'u geçmemeli.
import random

BITS = 32
TOP = (1 << BITS) - 1
CEYREK = 1 << (BITS - 2)        # First
YARIM = 2 * CEYREK              # Half
UCTE = 3 * CEYREK               # Third

def kumulatif(frek):
    kum = [0]
    for f in frek:
        kum.append(kum[-1] + f)
    return kum
```

Sabitler 32 bitlik aralığın dörtte birlik kesitlerini tanımlar. `kumulatif` fonksiyonu frekansları birikimli toplama çevirir; bir sembolün aralığı `[kum[s], kum[s+1])` olur.

```python
class Kodlayici:
    def __init__(self, frek):
        self.kum = kumulatif(frek)
        self.toplam = self.kum[-1]
        self.bits = []
        self.bekleyen = 0           # ters bit beklentisi (underflow)

    def _yaz(self, b):
        self.bits.append(b)
        self.bits.extend([1 - b] * self.bekleyen)
        self.bekleyen = 0

    def kodla(self, mesaj):
        low, high = 0, TOP
        for s in mesaj:
            aralik = high - low + 1
            high = low + aralik * self.kum[s + 1] // self.toplam - 1
            low = low + aralik * self.kum[s] // self.toplam
            while True:
                if high < YARIM:
                    self._yaz(0)
                elif low >= YARIM:
                    self._yaz(1)
                    low -= YARIM
                    high -= YARIM
                elif low >= CEYREK and high < UCTE:
                    self.bekleyen += 1
                    low -= CEYREK
                    high -= CEYREK
                else:
                    break
                low = 2 * low
                high = 2 * high + 1
        self.bekleyen += 1
        self._yaz(0 if low < CEYREK else 1)
        return self.bits
```

`Kodlayici.kodla` döngüsü, her sembol için aralığı daraltır ve üç durumdan birini uygular: aralık alt yarıdaysa `0`, üst yarıdaysa `1` yazar; orta noktayı kesen ama dörtlüklerin ortasında kalan durumda ise bekleyen bit sayacını artırır. Her renormalizasyonda aralık iki katına çıkarılır. Sonda kodlayıcı, kalan belirsizliği kapatmak için bir bit daha yazar.

```python
class Dekodlayici:
    def __init__(self, frek, bits):
        self.kum = kumulatif(frek)
        self.toplam = self.kum[-1]
        self.bits = bits
        self.konum = 0
        self.deger = 0
        for _ in range(BITS):
            self.deger = 2 * self.deger + self._oku()

    def _oku(self):
        # Bit dizisi bittiğinde 0 okunur (kodlayıcı sonunu kapatır).
        var = self.konum < len(self.bits)
        b = self.bits[self.konum] if var else 0
        self.konum += 1
        return b

    def coz(self, n):
        low, high = 0, TOP
        cikti = []
        for _ in range(n):
            aralik = high - low + 1
            c = ((self.deger - low + 1) * self.toplam - 1) // aralik
            s = 0
            while self.kum[s + 1] <= c:
                s += 1
```

Çözücü aynı aralık hesabını yapar, ama bit akışını bir pencere olarak tutar. `coz` her adımda pencerenin hangi sembol aralığına düştüğünü bulur ve kodlayıcıyla birebir aynı daraltmayı uygular. Bit dizisi bittiğinde sıfır okunur; bu, kodlayıcının sonunda yazdığı bitlerle uyumludur.

```python
            cikti.append(s)
            high = low + aralik * self.kum[s + 1] // self.toplam - 1
            low = low + aralik * self.kum[s] // self.toplam
            while True:
                if high < YARIM:
                    pass
                elif low >= YARIM:
                    self.deger -= YARIM
                    low -= YARIM
                    high -= YARIM
                elif low >= CEYREK and high < UCTE:
                    self.deger -= CEYREK
                    low -= CEYREK
                    high -= CEYREK
                else:
                    break
                low = 2 * low
                high = 2 * high + 1
                self.deger = 2 * self.deger + self._oku()
        return cikti
```

```python
def sına():
    rnd = random.Random(51)
    tamam = 0
    for frek in ([90, 5, 5], [1, 1, 1, 1], [7, 3, 1, 9, 2]):
        for n in (0, 1, 2, 50, 2000):
            mesaj = [rnd.choices(range(len(frek)), weights=frek)[0]
                     for _ in range(n)]
            bits = Kodlayici(frek).kodla(mesaj)
            geri = Dekodlayici(frek, bits).coz(n)
            assert geri == mesaj, (frek, n)
            tamam += 1
    # Tek simge tekrarı (ortalama uzunluk 0'a yakın olmalı)
    mesaj = [0] * 5000
    bits = Kodlayici([999, 1]).kodla(mesaj)
    assert Dekodlayici([999, 1], bits).coz(5000) == mesaj
    print("gidis-donus denemesi: %d/%d tamam" % (tamam, tamam))
    print("5000 'a' simgesi: %d bit" % len(bits))

def main():
    sına()
    # Çarpık kaynak: entropi 0.569 bit, Huffman en az 1 bit
    frek = [900, 50, 50]
    rnd = random.Random(51)
    mesaj = [rnd.choices([0, 1, 2], weights=frek)[0]
             for _ in range(20000)]
    bits = Kodlayici(frek).kodla(mesaj)
    print("bit/simge: %.4f" % (len(bits) / len(mesaj)))

if __name__ == "__main__":
    main()
```

Sınama fonksiyonu, üç farklı frekans tablosu ve beş farklı uzunlukta (boş mesaj dahil) mesajla gidiş-dönüş testi yapar. Son kısım, çarpık kaynağın bit/simge oranını ölçer.

```term
$ python aritmetik.py
gidis-donus denemesi: 15/15 tamam
5000 'a' simgesi: 9 bit
bit/simge: 0.5719
```

Bütün gidiş-dönüş denemeleri doğru çıktı: 15 kombinasyonun hepsinde çözülen mesaj özgün mesajla birebir aynıdır. Tek simgeli bir dizi (`5000` tane `a`) yalnızca `9` bit tutar, çünkü olasılığı `0,999`a yakın olan bir simge neredeyse bedava kodlanır. Çarpık üç sembollü kaynakta ölçülen değer `0,5719` bit/simgedir; entropi `0,569`, Huffman ise `1,1`. Aradaki `0,003` bitlik fark, 20 000 örneğin ürettiği istatistiksel sapmadan ve sınırlı hassasiyetten gelir.

Aritmetik kodlayıcıyı gerçek bir metinde de sınayalım. Aşağıdaki program üç kaynağı karşılaştırır: çarpık bir üç sembollü kaynak, dört sembollü bir kaynak ve Türkçe harf akışı. Türkçe harfler için tamsayı frekansları toplamı yaklaşık `2¹⁶` olacak şekilde ölçeklenir. Bu, çok daha büyük tablolara gerek kalmadan olasılıkların hassasiyetini korur.

```python
# kodlama_olcum.py: entropi, Huffman ve aritmetik kodlamanın bit/simge
# karşılaştırması. Üç kaynak: çarpık ikili-üç simge, dört simge,
# kitabın Türkçe harf akışı (bolum_01..46 düz metni).
# Kullanım: python kodlama_olcum.py <bolumler> <veri klasörü>
import csv
import glob
import os
import random
import re
import sys

from aritmetik import Dekodlayici, Kodlayici
from kraft_huffman import entropi, huffman_uzunluk, ortalama
from olcum_metin import ALFA, SON_BOLUM, duz_metin, tr_kucuk

def harf_akisi(kok):
    parcalar = []
    for yol in sorted(glob.glob(os.path.join(kok, "bolum_*.md"))):
        no = int(re.search(r"bolum_(\d+)\.md", yol).group(1))
        if no <= SON_BOLUM:
            with open(yol, encoding="utf-8") as f:
                parcalar.append(f.read())
    metin = duz_metin("\n".join(parcalar))
    return [c for c in tr_kucuk(metin) if c in ALFA]
```

Program, yukarıdaki `aritmetik` ve `kraft_huffman` modüllerini kullanır ve metin okuma işini Bölüm 51.3'teki `olcum_metin` ile paylaşır. Böylece tüm ölçümler aynı corpus üzerinde yapılır.

```python
def olc(ad, frek, mesaj, p):
    # frek: aritmetik kodlayıcının tamsayı frekansları;
    # p: gerçek olasılıklar (Huffman ve entropi için).
    n = len(mesaj)
    bits = Kodlayici(frek).kodla(mesaj)
    geri = Dekodlayici(frek, bits).coz(n)
    assert geri == mesaj, ad
    h = entropi(p)
    hf = ortalama(p, huffman_uzunluk(p))
    ar = len(bits) / n
    print("%-12s n=%-8d H=%.4f Huff=%.4f arit=%.4f" % (
        ad, n, h, hf, ar))
    return [ad, n, "%.4f" % h, "%.4f" % hf, "%.4f" % ar]
```

`olc` fonksiyonu her kaynak için üç rakamı yan yana basar: entropi `H`, Huffman ortalaması ve aritmetik kodun gerçek bit/simge oranı. Kod ayrıca kodu çözer ve sonucun özgün mesajla aynı olduğunu `assert` ile doğrular.

```python
def main(kok, veri):
    satirlar = []
    rnd = random.Random(51)
    # 1) Çarpık kaynak: p = [0.9, 0.05, 0.05]
    p = [0.9, 0.05, 0.05]
    frek = [900, 50, 50]
    m = [rnd.choices(range(3), weights=frek)[0] for _ in range(20000)]
    satirlar.append(olc("carpik3", frek, m, p))
    # 2) Dört simge: p = [0.4, 0.3, 0.2, 0.1]
    p = [0.4, 0.3, 0.2, 0.1]
    frek = [40, 30, 20, 10]
    m = [rnd.choices(range(4), weights=frek)[0] for _ in range(20000)]
    satirlar.append(olc("dort simge", frek, m, p))
    # 3) Türkçe harf akışı: frekanslar tamsayıya ölçeklenir
    #    (toplam yaklaşık 2^16)
    harfler = harf_akisi(kok)
    sira = {h: i for i, h in enumerate(ALFA)}
    m = [sira[h] for h in harfler]
    sayi = [0] * len(ALFA)
    for s in m:
        sayi[s] += 1
    n = len(m)
    frek = [max(1, round(c * 65536 / n)) for c in sayi]
    p = [c / n for c in sayi]
    satirlar.append(olc("Turkce harf", frek, m, p))
    with open(os.path.join(veri, "b51_kodlama.csv"), "w",
              encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kaynak", "n", "entropi_bit", "huffman_bit",
                    "aritmetik_bit"])
        w.writerows(satirlar)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
```

```term
$ python kodlama_olcum.py bolumler engine\veri
carpik3      n=20000    H=0.5690 Huff=1.1000 arit=0.5719
dort simge   n=20000    H=1.8464 Huff=1.9000 arit=1.8485
Turkce harf  n=1996285  H=4.4102 Huff=4.4477 arit=4.4102
```

Sonuçlar üç şeyi açıkça gösterir. Çarpık kaynakta Huffman `1,1` bit harcarken aritmetik kod `0,5719` bitle entropiye (`0,5690`) çok yakın kalır. Dört sembollü kaynakta fark azalır, çünkü Huffman'ın kaybı olasılıkların tam ikinin kuvvetlerine ne kadar yakın olduğuna bağlıdır: `0,4; 0,3; 0,2; 0,1` dağılımı bu ikili yapıdan uzaktır, bu yüzden Huffman `1,9` bit ile `1,8464` entropisinden `0,054` bit uzaklaşır; aritmetik kod ise `1,8485` bit ile sınıra çok daha yakındır.

Türkçe harf akışında ilginç bir şey olur. Aritmetik kod `4,4102` bit/harf harcar ve bu, aynı tablo için hesaplanan entropiyle dört ondalıkta aynıdır. Huffman ise `4,4477` bit harcar, yani `0,0375` bit fazla. Türkçe harf entropisi bölüm 51.3'ten bildiğimiz `H0` değeridir; Huffman'ın fazlalığı, sembol olasılıklarının ikinin kuvvetlerine uzaklığından gelir. Ölçümde çözücünün bildiği frekans tablosunun maliyeti sayılmadı. Büyük metinlerde bu maliyet ihmal edilebilir, küçük dosyalarda ise belirleyicidir.

![Şekil 51.5: Üç kaynak için entropi, Huffman ortalama uzunluğu ve aritmetik kod (bit/simge). Huffman, çarpık kaynakta sınırdan en çok uzaklaşandır.](gorseller/b51_kodlama_karsilastirma.png)

Bu sonuçlar, JPEG 2000 ve H.264/H.265 gibi standartların neden aritmetik ya da bağlama duyarlı aritmetik kodlama kullandığını açıklar: yüksek olasılıklı simgelerde Huffman'ın bir bitlik tabanı pahalıya gelir. Bu tür standartların kodlama ayrıntıları bu kitabın kapsamı dışındadır; ilkeyi burada kurduk.

## 51.7 Sözlük kodlama: LZ77 ve DEFLATE

Aritmetik ve Huffman kodlar yalnızca **tek tek sembollerin** olasılığını kullanır. Ama gerçek metinlerde kelimeler ve kelime parçaları tekrar eder: "kod" kelimesi bu bölümde yüzlerce kez geçiyor. Bu tekrarı kullanmak için sembol olasılıklarının ötesine geçmek gerekir. Bu, **sözlük kodlamanın** fikridir ve Abraham Lempel ile Jacob Ziv'in 1977 tarihli LZ77 yöntemiyle başlar.

LZ77'nin fikri basittir: kodlayıcı, metnin önceki bir kısmında (pencere) mevcut konumdan başlayan en uzun eşleşmeyi arar. Eşleşme bulursa, bunu `(ofset, uzunluk)` çifti ile yazar; bulamazsa tek bir sembol yazar. Üçlü biçimde her çıktı `(ofset, uzunluk, sonraki bayt)` olur: eşleşme yoksa `(0, 0, bayt)`, varsa eşleşme ve ardından gelen bayt. Aşağıdaki programda basit bir LZ77 kodlayıcı ve çözücü, kitabın 16. bölümünden alınmış bir kesit ve zlib ile karşılaştırma yer alıyor.

```python
# lz77_zlib.py: LZ77 sözlük kodlamasının sezgisi, DEFLATE = LZ77 +
# Huffman ve sıkıştırılamaz veri (rastgele ve "şifreli benzeri")
# ölçümü.
# Kullanım: python lz77_zlib.py <bolum_18.md yolu>
import hashlib
import random
import sys
import zlib

def lz77_kodla(s, pencere=32, azami=15):
    # Üçlü çıktı: (ofset, uzunluk, sonraki bayt). Kaba kuvvet arama.
    i, cikti = 0, []
    while i < len(s):
        en_uz, en_of = 0, 0
        for j in range(max(0, i - pencere), i):
            k = 0
            # son baytı sonraki için bırak: i+k < len(s)-1
            while (k < azami and i + k < len(s) - 1
                   and s[j + k] == s[i + k]):
                k += 1
            if k > en_uz:
                en_uz, en_of = k, i - j
        cikti.append((en_of, en_uz, s[i + en_uz]))
        i += en_uz + 1
    return cikti

def lz77_coz(uclu):
    # Örtüşen kopyalar bayt bayt yazılır (ofset < uzunluk olabilir).
    cikti = bytearray()
    for of, ul, son in uclu:
        for _ in range(ul):
            cikti.append(cikti[-of])
        cikti.append(son)
    return bytes(cikti)
```

`lz77_kodla` her konumda pencereyi tarar ve en uzun eşleşmeyi seçer. Önemli bir ayrıntı: eşleşme, pencerenin dışına çıkmadan kendi üzerine de katlanabilir (ofset uzunluktan küçükse). Bu yüzden `lz77_coz` baytları tek tek ekler; `abracadabra` gibi tekrarlı dizilerde bu gereklidir. Çözücü, kendi çıktısının son baytlarını kopyalar ve bu yüzden kodlayıcıyla aynı bilgiyi kullanır.

```python

def sifreli_benzeri(metin, anahtar=b"muhendis-51"):
    # Sayaçlı SHA-256 akışı ile XOR: çıktı rastgeleye yakın görünür.
    # (Gerçek bir şifre DEĞİL; yalnızca sıkıştırılamazlık gösterimi.)
    cikti = bytearray()
    for blok in range(0, len(metin), 32):
        sayac = blok.to_bytes(8, "big")
        ks = hashlib.sha256(anahtar + sayac).digest()
        parca = metin[blok:blok + 32]
        cikti.extend(a ^ b for a, b in zip(parca, ks))
    return bytes(cikti)

def boyut_orani(veri, seviye=9, strateji=zlib.Z_DEFAULT_STRATEGY):
    c = zlib.compressobj(seviye, zlib.DEFLATED, 15, 9, strateji)
    out = c.compress(veri) + c.flush()
    return len(out), len(out) / len(veri)
```

Bu parçadaki `sifreli_benzeri` fonksiyonu, Bölüm 51.8'de sıkıştırılamazlığı sınamak için bir veri üretir. Bir SHA-256 sayaç akışıyla XOR alır; sonuç rastgeleye benzer ama **gerçek bir şifre değildir**. Kriptografik güvenlik için Bölüm 32'deki `secrets` ve gerçek şifreleme kütüphaneleri kullanılmalıdır.

```python
def main(yol):
    with open(yol, "rb") as f:
        metin = f.read()
    print("abracadabra LZ77 üçlüleri:")
    for u in lz77_kodla(b"abracadabra"):
        print("  ", u)
    ornek = metin[:4000]
    uclu = lz77_kodla(ornek)
    assert lz77_coz(uclu) == ornek
    eslesen = sum(1 for u in uclu if u[1] > 0)
    print("4000 baytlık kesit: %d üçlü, %d tanesi eşleşme içeriyor"
          % (len(uclu), eslesen))
    print("---")
    print("kaynak              bayt   zlib-9  orani  huff-only orani")
    rnd = random.Random(51)
    kaynaklar = [
        ("bolum_18 (metin)", metin),
        ("rastgele 100000", rnd.randbytes(100000)),
        ("sifreli benzeri", sifreli_benzeri(metin)),
    ]
    for ad, veri in kaynaklar:
        b9, o9 = boyut_orani(veri, 9)
        bh, oh = boyut_orani(veri, 9, zlib.Z_HUFFMAN_ONLY)
        print("%-18s %7d %7d  %.4f  %8d   %.4f" % (
            ad, len(veri), b9, o9, bh, oh))
    # Düzey 0: LZ77 ve Huffman yok, yalnızca başlık+saklama
    b0, o0 = boyut_orani(metin, 0)
    print("bolum_18 zlib duzey 0: %d bayt (oran %.4f)" % (b0, o0))

if __name__ == "__main__":
    main(sys.argv[1])
```

```term
$ python lz77_zlib.py bolumler\bolum_18.md
abracadabra LZ77 üçlüleri:
   (0, 0, 97)
   (0, 0, 98)
   (0, 0, 114)
   (3, 1, 99)
   (5, 1, 100)
   (7, 3, 97)
4000 baytlık kesit: 2162 üçlü, 1428 tanesi eşleşme içeriyor
---
kaynak              bayt   zlib-9  orani  huff-only orani
bolum_18 (metin)    103991   34956  0.3361     67254   0.6467
rastgele 100000     100000  100026  1.0003    100026   1.0003
sifreli benzeri     103991  104017  1.0003    104017   1.0003
bolum_18 zlib duzey 0: 104012 bayt (oran 1.0002)
```

İlk satırlar `abracadabra` üzerinde LZ77 üçlülerini gösterir. İlk üç üçlü `(0, 0, a)`, `(0, 0, b)`, `(0, 0, r)` yani henüz eşleşme yok. Dördüncü üçlü `(3, 1, c)`: ofset 3, yani üç bayt geriye git, bir bayt kopyala (`a`), sonra `c` yaz. Son üçlü `(7, 3, a)` ise `abr` dizisini yedi bayt geriden kopyalar. Altı üçlü ile on bir baytlık metin ifade edildi; bu küçük örnekte sıkıştırma kazancı yoktur, ama mekanizma görülebilir.

Asıl ölçüm, Bölüm 18'in metni olan dosya üzerindedir. Burada iki sıkıştırma ayarını karşılaştırdık. Varsayılan DEFLATE (LZ77 + Huffman) `103 991` bayttan `34 956` bayta, yani `%33,6`ya indi. Yalnızca Huffman kullanan `Z_HUFFMAN_ONLY` kipi ise `67 254` bayt, yani `%64,7` verdi. Bu iki sayı Bölüm 18'deki ölçümle tutarlıdır: orada Huffman `%64,6`, gzip `%33,8` çıkmıştı. Aradaki farkın tamamı LZ77 aşamasının katkısıdır. Bu, Bölüm 51.3'teki sonucun uygulamadaki karşılığıdır: sembol olasılıklarının (0. derece) sınırı `5,1` bit/bayt, yani yaklaşık `%64`tür; bunun altına inmek için tekrar yapısını kullanmak gerekir.

DEFLATE, RFC 1951'de tanımlanan bu iki aşamalı yapıdır: önce LZ77 ile tekrarlar geri gösterimlere çevrilir, sonra çıkan semboller (literal ve uzunluk/ofset kodları) dinamik Huffman ile kodlanır. zlib (RFC 1950) bu akışa bir başlık ve Adler-32, gzip (RFC 1952) ise bir başlık ve CRC-32 ekler (genel bilgi). Bu sağlama toplamları yalnızca hata tespiti yapar, düzeltmez; bu farkı Bölüm 51.14'te ele alacağız.

## 51.8 Sıkıştırılamaz veri: rastgele ve şifreli bayt dizileri

Her veri sıkıştırılamaz değildir. Üç baytlık bir dizide her şey olası değildir, ama rastgele bir dizi neden sıkışmaz? Cevap bir sayma argümanıdır. `n` bitlik `2ⁿ` farklı dizi vardır. Bunların her birini daha kısa bir çıktıya eşleyen kayıpsız bir sıkıştırıcı olsaydı, `n` bitten kısa çıktı sayısı `2ⁿ − 1` olurdu ve iki farklı girdi aynı çıktıya düşmek zorunda kalırdı. Bu bir **güvercin deliği ilkesidir**: hiçbir kayıpsız yöntem her girdiyi kısaltamaz; bazı girdiler kısalırken bazıları uzamak zorundadır.

Pratikte bu, rastgele veriyi sıkıştırmanın neden anlamsız olduğunu açıklar. Programda `random.Random(51).randbytes` ile 100 000 rastgele bayt üretip zlib'e verdik. Çıktı `100 026` bayt oldu, yani `%0,03` büyüdü. Bu büyüme, DEFLATE'in saklanan (stored) blokların başlığından gelir: bir sıkıştırıcı girdinin sıkıştırılamadığını anlarsa, veriyi olduğu gibi saklar ve küçük bir başlık ekler. Düzey 0 (hiç sıkıştırma yok) da aynı davranışı gösterir: Bölüm 18'in metni için oran `1,0002`dir; yani bu büyüme her girdide görülen sabit bir başlık maliyetidir.

Şifreli veri de bu kategoriye girer. İyi bir şifre çıktısı, düzgün bir bit dağılımına sahip olmalıdır; aksi halde saldırgan istatistik kullanabilirdi. Bu yüzden **önce sıkıştır, sonra şifrele** sırası zorunludur: şifrelenmiş veriyi sıkıştırmaya çalışmak boşunadır, ayrıca ortaya çıkan uzunluk farkları yan kanal sızıntısı bile oluşturabilir (CRIME ve BREACH saldırıları bu tür sızıntıya dayanır, genel bilgi). Programdaki "şifreli benzeri" veri `%0,03` büyüdü, tıpkı rastgele veri gibi.

Teorik olarak daha derin bir soru da vardır. **Kolmogorov karmaşıklığı** `K(x)`, `x` dizisini çıktı olarak üretecek en kısa programın uzunluğudur. Bu tanım, sıkıştırma kavramını makine bağımsız biçimde verir: `x` ne kadar düzenliyse `K(x)` o kadar küçüktür. Ancak `K(x)` hesaplanamaz bir fonksiyondur (genel bilgi, Kolmogorov 1965 ve Chaitin): hiçbir program, her dizinin en kısa tanımını bulamaz. Bu yüzden pratik sıkıştırıcılar bir alt sınıfa, yani kalıplara ve istatistiğe dayanır. Bölüm 51.2'deki entropi, bu sınıfa dahil olan kaynakların ortalama sınırıdır; Kolmogorov karmaşıklığı ise tek bir dizinin sınırıdır.

Burada bir uyarı önemli: `random.Random` sabit tohumla tekrarlanabilir sonuç verir, ama güvenlik için **tahmin edilemez** değildir. Tohum bilinirse üretilen tüm diziler yeniden üretilebilir. Anahtar, token ve nonce üretimi için Bölüm 32.2'de gösterilen `secrets` modülünü kullan. Bu bölümdeki sabit tohum yalnızca ölçümün tekrarlanabilirliği içindir.

## 51.9 Çapraz entropi ve KL ıraksaması

Şimdiye kadar tek bir dağılımla çalıştık. Gerçek sorularda ise iki dağılım vardır: gerçek dağılım `p` ve bizim varsaydığımız dağılım `q`. Kodu `q`ya göre tasarladık ama semboller `p`ye göre geliyor. Bu uyumsuzluğun bedeli nedir?

Cevap **çapraz entropidir** (cross-entropy):

H(p, q) = −∑ p(x) log₂ q(x)

Bu, `p`'den gelen sembolleri `q`ya göre tasarlanmış bir kodla kodlamanın ortalama bit maliyetidir. Bir kod sözcüğü uzunluğu `−log₂ q(x)` olarak seçildiğinde (Bölüm 51.5'teki gibi), `p(x)` olasılıkla gelen `x`in bedeli bu kadardır.

Çapraz entropi, gerçek kaynağın kendi entropisinin üstüne bir ek bindirir. Bu ek, **Kullback-Leibler ıraksamasıdır** (KL divergence):

D_KL(p ‖ q) = ∑ p(x) log₂ (p(x) / q(x))

Ve aralarındaki ilişki zincir kuralı gibi basittir:

H(p, q) = H(p) + D_KL(p ‖ q)

Üç özelliği bilmek gerekir. Birincisi, `D_KL(p ‖ q) ≥ 0` ve eşitlik yalnızca `p = q` iken geçerlidir. Bu, **Gibbs eşitsizliğidir**. İspatı Jensen eşitsizliğine dayanır: `log` konkavdır, bu yüzden `−D = ∑ p log (q/p) ≤ log ∑_{p>0} q ≤ log 1 = 0`. Bu ispat, Bölüm 51.2'deki `H ≤ log₂ n` sınırının da kaynağıdır: düzgün `q` ile `p` arasındaki KL'yi yazıp sıfırdan büyük olduğunu görmek yeterlidir.

İkincisi, KL **simetrik değildir**: genel olarak `D_KL(p ‖ q) ≠ D_KL(q ‖ p)`. Üçüncüsü, `q(x) = 0` iken `p(x) > 0` ise KL sonsuz olur. Nedeni açıktır: `q` bu sembole hiç kod sözcüğü vermemiştir, ama sembol gelebilir.

Somut bir örnek bu asimetriyi gösterir. `p = [0,9; 0,1]` gerçek dağılım, `q = [0,5; 0,5]` varsayılan dağılım olsun:

- `D_KL(p ‖ q) = 0,9 log₂(0,9/0,5) + 0,1 log₂(0,1/0,5) = 0,531` bit
- `D_KL(q ‖ p) = 0,5 log₂(0,5/0,9) + 0,5 log₂(0,5/0,1) = 0,737` bit

Şekil 51.6 bu iki yönü yan yana gösterir. Önemli nokta şudur: ıraksama bir mesafe değildir, çünkü simetrik değildir ve üçgen eşitsizliğini sağlamaz. Yine de "bu iki dağılım ne kadar farklı" sorusuna yön bilgisiyle cevap verir: `p`den `q`ya ne kadar pahalıdır.

![Şekil 51.6: Solda iki dağılım, sağda aynı çiftin iki yönlü KL ıraksamaları. Asimetri açıktır: KL(p‖q) = 0,531 bit, KL(q‖p) = 0,737 bit.](gorseller/b51_kl_asimetri.png)

Asimetrinin en çarpıcı biçimi sıfır kütleyle ortaya çıkar. Aşağıdaki programda `p` iki sınıfta eşit olasılıklı, diğer iki sınıfta sıfırdır. `q_tek` yalnızca bir sınıfa yapışır, `q_kapsa` ise `p`nin desteğinde yayılır ama sıfır olan üçüncü sınıfa da kütle verir. Program, dört yönü de hesaplar. Ayrıca rastgele çiftlerde KL'nin hiçbir zaman negatif çıkmadığını ve iki Gauss arasındaki KL'nin kapalı biçimini sayısal integralle doğrular.

```python
# kl_ce.py: çapraz entropi, KL ıraksaması, asimetri, perplexity
# ve iki Gauss arasındaki KL'nin kapalı biçimi (VAE'deki terim).
import math
import random

def entropi(p):
    return -sum(x * math.log2(x) for x in p if x > 0)

def capraz(p, q):
    # H(p, q) = -sum p log2 q. q = 0 ve p > 0 ise sonsuz.
    t = 0.0
    for x, y in zip(p, q):
        if x > 0:
            if y == 0:
                return math.inf
            t -= x * math.log2(y)
    return t

def kl(p, q):
    # D_KL(p || q) = sum p log2(p/q) = H(p,q) - H(p)
    t = 0.0
    for x, y in zip(p, q):
        if x > 0:
            if y == 0:
                return math.inf
            t += x * math.log2(x / y)
    return t
```

`entropi`, `capraz` ve `kl` fonksiyonları tanımları doğrudan yansıtır. `capraz` ve `kl` içindeki `y == 0` denetimi önemlidir: sıfır paydaya bölmek yerine `inf` döndürürler. Bu, Python'da hata vermemesi için değil, matematiksel olarak doğru olduğu için yapılır: `q = 0` olan yerde KL gerçekten sonsuzdur.

```python
def gauss_kl_nat(mu, sigma):
    # KL(N(mu, s^2) || N(0,1)) = 0.5 (s^2 + mu^2 - 1 - ln s^2), nat
    s2 = sigma * sigma
    return 0.5 * (s2 + mu * mu - 1.0 - math.log(s2))

def gauss_kl_sayisal(mu, sigma, aralik=12.0, n=200000):
    # Aynı integrali dikdörtgen kuralıyla sayısal olarak hesapla.
    def pdf(x, m, s):
        ust = math.exp(-0.5 * ((x - m) / s) ** 2)
        return ust / (s * math.sqrt(2 * math.pi))
    h = 2 * aralik / n
    t = 0.0
    for i in range(n):
        x = -aralik + (i + 0.5) * h
        p = pdf(x, mu, sigma)
        q = pdf(x, 0.0, 1.0)
        if p > 0:
            t += p * math.log(p / q) * h
    return t
```

`gauss_kl_nat` iki Gauss arasındaki KL'nin kapalı biçimini verir (Bölüm 51.10'da VAE için kullanacağız). `gauss_kl_sayisal` aynı değeri dikdörtgen kuralıyla hesaplar. İkisinin karşılaştırılması, kapalı biçimin doğru türetildiğini sayısal olarak kontrol eder.

```python
def main():
    p = [0.9, 0.1]
    q = [0.5, 0.5]
    print("KL(p||q) = %.4f bit" % kl(p, q))
    print("KL(q||p) = %.4f bit" % kl(q, p))
    # Sıfır olasılık: q'da olmayan olay p'de varsa KL sonsuz olur.
    print("KL([0.5,0.5] || [1,0]) = %s" % kl([0.5, 0.5], [1.0, 0.0]))
    print("KL([1,0] || [0.5,0.5]) = %.4f"
          % kl([1.0, 0.0], [0.5, 0.5]))
    # Çapraz entropi = H(p) + KL(p||q)
    print("H(p)=%.4f  H(p,q)=%.4f  H(p)+KL=%.4f" % (
        entropi(p), capraz(p, q), entropi(p) + kl(p, q)))
    # Sıfır kütleli destek: forward ve reverse KL asimetrisi
    p2 = [0.5, 0.5, 0.0, 0.0]          # destek: 1. ve 2. sınıf
    q_tek = [1.0, 0.0, 0.0, 0.0]       # yalnızca 1. sınıfta
    q_kapsa = [0.5, 0.4, 0.1, 0.0]     # destekte yayılır
    print("KL(p||tek)   = %s" % kl(p2, q_tek))
    print("KL(tek||p)   = %.4f" % kl(q_tek, p2))
    print("KL(p||kapsa) = %.4f" % kl(p2, q_kapsa))
    print("KL(kapsa||p) = %s" % kl(q_kapsa, p2))
    # Gibbs eşitsizliği: 2000 rastgele çift için KL < 0 olmamalı.
    rnd = random.Random(51)
    en_kucuk = math.inf
    for _ in range(2000):
```

```python
        a = [rnd.random() + 1e-9 for _ in range(4)]
        b = [rnd.random() + 1e-9 for _ in range(4)]
        sa, sb = sum(a), sum(b)
        a = [v / sa for v in a]
        b = [v / sb for v in b]
        en_kucuk = min(en_kucuk, kl(a, b))
    print("2000 rastgele cift, en kucuk KL = %.2e" % en_kucuk)
    # Gauss KL: kapalı biçim ile sayısal integral karşılaştırması
    for mu, s in [(0.0, 1.0), (1.5, 0.7), (-0.8, 2.0)]:
        kap = gauss_kl_nat(mu, s)
        say = gauss_kl_sayisal(mu, s)
        print("N(%.1f, %.1f^2): kapali=%.6f sayisal=%.6f nat" % (
            mu, s, kap, say))
    # Perplexity: 2^H; 50 000 kelimelik düzgün model
    print("perplexity (duzgun, 50000): %.0f" % 2 ** math.log2(50000))
    print("perplexity (3.0 bit/simge):  %.1f" % 2 ** 3.0)

if __name__ == "__main__":
    main()
```

```term
$ python kl_ce.py
KL(p||q) = 0.5310 bit
KL(q||p) = 0.7370 bit
KL([0.5,0.5] || [1,0]) = inf
KL([1,0] || [0.5,0.5]) = 1.0000
H(p)=0.4690  H(p,q)=1.0000  H(p)+KL=1.0000
KL(p||tek)   = inf
KL(tek||p)   = 1.0000
KL(p||kapsa) = 0.1610
KL(kapsa||p) = inf
2000 rastgele cift, en kucuk KL = 2.37e-03
N(0.0, 1.0^2): kapali=0.000000 sayisal=0.000000 nat
N(1.5, 0.7^2): kapali=1.226675 sayisal=1.226675 nat
N(-0.8, 2.0^2): kapali=1.126853 sayisal=1.126852 nat
perplexity (duzgun, 50000): 50000
perplexity (3.0 bit/simge):  8.0
```

İlk iki satır, Şekil 51.6'nın değerlerini doğrular. `KL([0,5, 0,5] ‖ [1, 0])` satırı sonsuzdur, çünkü `q` ikinci sınıfa hiç kütle vermez. Ters yön, `KL([1, 0] ‖ [0,5, 0,5]) = 1` bit ile sonludur. Üçüncü satır çapraz entropi kimliğini sayısal olarak sağlar: `H(p) + KL = 1,0000 = H(p,q)`.

Sıfır kütleli örnek (`p2`, `q_tek`, `q_kapsa`) asimetrinin en açık biçimidir. `KL(p ‖ tek)` sonsuz çıkar: gerçek dağılım ikinci sınıfta kütle taşırken `q` bu sınıfa sıfır vermiştir. Buna karşılık `KL(tek ‖ p) = 1` bit sonludur, çünkü `q` yalnızca `p`nin kütle taşıdığı sınıfta yoğunlaşmıştır. `q_kapsa` ise ters yönde sonsuz olur: `p`nin sıfır olduğu üçüncü sınıfa kütle koyduğu için. Yani iki yön de farklı bir hata türünü cezalandırır: `KL(p ‖ q)` destekte bir boşluk bulunmasını (`q`nun yetersiz kapsamasını) cezalandırır, `KL(q ‖ p)` ise `p`nin desteği dışına taşmayı cezalandırır.

Bu asimetri makine öğrenmesinde önemlidir. Bir modeli gerçek veriye uydururken genellikle `KL(veri ‖ model)` yönünü kullanırız, çünkü bu yön modelin veriyi kapsamasını ister (Bölüm 51.10). Değişimsel çıkarımda (Bölüm 72) ise tersi, `KL(model ‖ gerçek)` çoğu zaman kullanılır ve modelin gerçek dağılımın tek bir kipine yerleşmesine yol açabilir; bu, ters ıraksamanın "mod arayan" davranışıdır (genel bilgi).

Son iki sayı perplexity'yi tanıtır. Bir dağılımın perplexity'si `2^H` olarak tanımlanır ve "eşit olasılıklı kaç seçenek varmış gibi" sorusunun cevabıdır. Düzgün 50 000 kelimelik bir dağılımın perplexity'si 50 000'dir. Bir dil modeli, token başına 3 bit çapraz entropi veriyorsa, perplexity'si `2³ = 8` olur; yani model her adımda ortalama 8 seçenek arasında tereddüt ediyor gibidir. Bölüm 70'te dil modellerini değerlendirirken bu ölçüyü sık kullanacağız.

## 51.10 Makine öğrenmesi bağlantısı: çapraz entropi kaybı, softmax ve sayısal kararlılık

Bir sınıflandırıcı, bir örnek için sınıflar üzerinde bir olasılık dağılımı `q` üretir. Gerçek etiket ise tek bir sınıftır: one-hot vektör `y`, yalnızca doğru sınıfta 1, diğerlerinde 0 içerir. Bu durumda çapraz entropi kaybı şuna iner:

H(y, q) = −∑ yᵢ log qᵢ = −log q_doğru

Bu, Bölüm 49'da ayrıntısıyla göreceğin **en çok olabilirlik** (MLE) ilkesinin negatif log-olabilirliğidir. Eğitim verisi üzerinde ortalama çapraz entropiyi küçültmek, verinin olasılığını en büyütmekle aynı şeydir. Daha genel olarak, `p` veri dağılımı ve `qθ` parametreli modelse:

D_KL(p ‖ qθ) = H(p, qθ) − H(p)

Sağdaki `H(p)` parametre `θ`ya bağlı değildir. Bu yüzden `θ`yı en iyi seçmek, `KL(p ‖ qθ)`yı en küçük yapmakla aynıdır. Yani eğitim, veri dağılımı ile model dağılımı arasındaki ıraksamayı küçültür. Çapraz entropi kaybı, bu ıraksamanın bilinen ve hesaplanabilir kısmıdır.

**Birim hakkında bir not.** Bu bölümde bit (log₂) ile yazdığımız ifadeler ML'de genellikle nat (ln) ile yazılır. Türev alırken doğal logaritma daha sade sonuç verir ve bit ile nat arasındaki fark yalnızca `1/ln 2` çarpanıdır. Aşağıdaki programda kayıp nat cinsinden hesaplanır.

Softmax'ı hatırlayalım. Bir sınıflandırıcı ham skorları (logit) `z = (z₁, ..., z_K)` üretir ve olasılıkları `pᵢ = e^{zᵢ} / ∑ⱼ e^{zⱼ}` ile hesaplar. Çapraz entropi kaybı ile softmax birleştiğinde gradyan çok sadeleşir. Doğru sınıf `k` için kayıp `L = −z_k + ln ∑ⱼ e^{zⱼ}` olur. İkinci terimin `zᵢ`ye göre türevi `pᵢ`dir, birinci terimin türevi ise `−[i = k]`dır. Dolayısıyla:

∂L / ∂zᵢ = pᵢ − yᵢ

Bu sonuç, Bölüm 63'te sinir ağlarında geri yayılımın ilk adımı olacak: çıkış katmanındaki hata, tahmin olasılığı eksi gerçek etikettir. Aşağıdaki program bu gradyanı sayısal olarak doğrular. Sayısal gradyan, Bölüm 50'de anlatılan merkezi fark yöntemidir ve türetilmiş formülün doğruluğunu sınamanın standart yoludur.

Softmax'ın bir tuzağı vardır. `e^{z}` büyük `z` değerlerinde taşar. Python'da `math.exp(1000)` bir `OverflowError` üretir ve büyük ağlarda bu, eğitimin ortasında sessiz `inf` ve `nan` değerlerine yol açabilir. Çözüm **log-sum-exp** hilesidir: en büyük logit `m` çıkarılır, çünkü `softmax(z) = softmax(z − m)` eşitliği her zaman geçerlidir:

ln ∑ e^{zⱼ} = m + ln ∑ e^{zⱼ − m}

Böylece üsler en fazla 0 olur ve taşma olmaz. Aşağıdaki program üç parçaya bölünmüştür: softmax fonksiyonları, gradyan ve sayısal denetim, ana program.

```python
# softmax_gradyan.py: softmax + çapraz entropi kaybı, sayısal
# kararlılık (log-sum-exp) ve gradyanın sayısal denetimi.
# Birim: nat (ln).
import math
import random

def softmax_naif(z):
    e = [math.exp(v) for v in z]          # büyük z'de taşar
    s = sum(e)
    return [v / s for v in e]

def lse(z):
    # log-sum-exp: ln sum exp(z_i), en büyük değer çıkarılarak
    m = max(z)
    return m + math.log(sum(math.exp(v - m) for v in z))

def softmax(z):
    m = max(z)
    e = [math.exp(v - m) for v in z]
    s = sum(e)
    return [v / s for v in e]

def kayip(z, y):
    # Tek örnek, tek sıcak etiket y (sınıf indeksi):
    # L = -ln p_y = lse(z) - z_y
    return lse(z) - z[y]

def gradyan(z, y):
    # dL/dz_i = p_i - [i == y]  (softmax + çapraz entropinin sadeliği)
    p = softmax(z)
    return [p[i] - (1.0 if i == y else 0.0) for i in range(len(z))]

def gradyan_sayisal(z, y, h=1e-5):
    # Merkezi fark: (L(z+h e_i) - L(z-h e_i)) / 2h
    g = []
    for i in range(len(z)):
        zp = list(z); zm = list(z)
        zp[i] += h; zm[i] -= h
        g.append((kayip(zp, y) - kayip(zm, y)) / (2 * h))
    return g
```

`softmax_naif` ile `softmax` farkına dikkat et. Birincisi doğrudan üstel alır; ikincisi en büyük logiti çıkarır. `lse` (log-sum-exp) fonksiyonu kaybın kararlı hesabını verir. `gradyan` fonksiyonu `pᵢ − yᵢ` formülünü doğrudan uygular, `gradyan_sayisal` ise her bileşen için merkezi farkla yaklaşık türev alır.

```python
def main():
    # 1) Taşma: büyük logitler
    z_buyuk = [1000.0, 999.0, 998.0]
    try:
        softmax_naif(z_buyuk)
        print("naif softmax: taşma yok")
    except OverflowError as e:
        print("naif softmax hata verdi:", e)
    print("kararlı softmax:", [round(v, 6) for v in softmax(z_buyuk)])
    print("kararlı kayıp (y=0): %.6f" % kayip(z_buyuk, 0))
    # 2) Düşük olasılık: ln 0 hatası; kararlı log-softmax çalışır
    z_fark = [0.0, -800.0]
    e = [math.exp(v) for v in z_fark]
    p_naif = [v / sum(e) for v in e]
    print("naif p:", p_naif)
    try:
        print("naif ln p_1 =", math.log(p_naif[1]))
    except ValueError as err:
        print("naif ln p_1 hata:", err)
    print("kararlı ln p_1 = %.1f" % (z_fark[1] - lse(z_fark)))
    # 3) Çalışılmış örnek: 3 sınıf, y = 0
    z = [2.0, 0.5, -1.0]
    p = softmax(z)
```

```python
    print("logit:", z, " p:", [round(v, 4) for v in p])
    print("kayip = %.4f nat" % kayip(z, 0))
    print("gradyan (p - y):", [round(v, 4) for v in gradyan(z, 0)])
    # 4) Gradyan denetimi (sabit tohum): 500 rastgele z, 3 sınıf
    rnd = random.Random(51)
    en_buyuk = 0.0
    for _ in range(500):
        zz = [rnd.uniform(-3, 3) for _ in range(3)]
        y = rnd.randrange(3)
        a = gradyan(zz, y)
        s = gradyan_sayisal(zz, y)
        fark = max(abs(u - v) for u, v in zip(a, s))
        en_buyuk = max(en_buyuk, fark)
    print("500 rastgele z icin max |analitik - sayisal| = %.2e"
          % en_buyuk)
    # 5) Etiket yumuşatma: hedef dağılımı yumuşat
    eps, k = 0.1, 3
    yum = [(1 - eps) * (i == 0) + eps / k for i in range(k)]
    print("yumusatilmis hedef:", [round(v, 4) for v in yum])

if __name__ == "__main__":
    main()
```

```term
$ python softmax_gradyan.py
naif softmax hata verdi: math range error
kararlı softmax: [0.665241, 0.244728, 0.090031]
kararlı kayıp (y=0): 0.407606
naif p: [1.0, 0.0]
naif ln p_1 hata: math domain error
kararlı ln p_1 = -800.0
logit: [2.0, 0.5, -1.0]  p: [0.7856, 0.1753, 0.0391]
kayip = 0.2413 nat
gradyan (p - y): [-0.2144, 0.1753, 0.0391]
500 rastgele z icin max |analitik - sayisal| = 7.30e-11
yumusatilmis hedef: [0.9333, 0.0333, 0.0333]
```

İlk iki satır taşmayı gösterir. `[1000, 999, 998]` logitleriyle naif softmax `math range error` verir. Kararlı sürüm ise `[0,6652; 0,2447; 0,0900]` olasılıklarını üretir ve kaybı `0,4076` nat verir. Sonraki satırda `[0, −800]` için naif `p₁` değeri tamamen sıfırdır (`e^{−800}` alt taşıp sıfıra düşer), bu yüzden `ln p₁` bir `math domain error` verir. Kararlı `ln p₁` ise doğrudan `−800,0` olarak hesaplanır, çünkü log-softmax `z₁ − lse(z)` olarak yazılabilir.

Çalışılmış örnek üç sınıfta `z = [2,0; 0,5; −1,0]` ve `y = 0` için kaybı verir: `p = [0,7856; 0,1753; 0,0391]`, `L = 0,2413` nat. Gradyan `p − y = [−0,2144; 0,1753; 0,0391]`dir; doğru sınıfın gradyanı negatiftir, çünkü onun olasılığını artırmak kaybı azaltır. Diğer sınıfların gradyanları pozitiftir, yani olasılıklarını azaltmak gerekir. Bu dört sayının toplamı sıfırdır, çünkü olasılıkların toplamı 1'dir.

Sayısal denetim 500 rastgele logit vektöründe analitik ve sayısal gradyan arasındaki en büyük farkın `7,3 × 10⁻¹¹` olduğunu gösterir. Bu, türetilmiş formülün doğru olduğuna dair güçlü bir kanıttır. Bir sinir ağı yazarken aynı kontrolü her yeni kayıp fonksiyonunda yapmak, Bölüm 64'teki "eğitim hatası ayıklama" alışkanlığının temelidir.

Son satır **etiket yumuşatmasını** (label smoothing) gösterir. One-hot hedef `[1, 0, 0]` yerine `[0,9333; 0,0333; 0,0333]` kullanılır. Bu, modelin en yüksek olasılığı sonsuza kadar büyütmesini engeller ve aşırı güvenli tahminleri azaltır. Bu sezgiyi basit tutuyoruz; yumuşatmanın etkisi ve seçimi için genel bilgi yeterlidir.

Kaybın kendisi ile sınıflandırma doğruluğu arasındaki ilişkiyi de bilmek gerekir. Kayıp, yanlış tahminlerin "ne kadar yanlış" olduğunu ölçer; doğruluk ise yalnızca en büyük olasılığın doğru olup olmadığına bakar. Bu yüzden iki model aynı doğrulukta olabilir ama farklı kayıp verebilir. Değerlendirme metriklerini Bölüm 57'de ayrıntılı işleyeceğiz.

Şekil 51.7 iki sınıflı bir durumda kaybın ve gradyanın davranışını gösterir. Doğru sınıfın logiti arttıkça kayıp sıfıra yaklaşır, gradyanın büyüklüğü de sıfıra iner. Bu, eğitim sırasında iyi tahmin edilen örneklerin modeli fazla değiştirmediğini söyler.

![Şekil 51.7: Doğru sınıfın logiti z0 arttıkça çapraz entropi kaybı (solda) ve gradyan dL/dz0 = p0 − 1 (sağda) sıfıra iner. Kesikli çizgi diğer sınıfın gradyanıdır.](gorseller/b51_softmax_kayip.png)

Bu bölümün son ML bağlantıları üç kavramdır, hepsi bu bölümde tanımlandı. Birincisi **değişimsel otomatik kodlayıcının** (VAE, Bölüm 72) kaybındaki KL terimidir. Gauss önseli `N(0,1)` ve kodlayıcı `N(μ, σ²)` olduğunda KL'nin kapalı biçimi `½(σ² + μ² − 1 − ln σ²)` nat'tır. Programda `N(1,5; 0,7²)` için bu değer `1,226675` nat çıkar ve sayısal integral aynı değeri verir. İkincisi **bilgi darboğazıdır** (information bottleneck, Tishby ve arkadaşları 1999): bir temsilin girdiyi ne kadar sıkıştırdığı ile hedefi ne kadar koruduğu arasında bir değiş tokuş vardır (genel bilgi). Üçüncüsü, perplexity'nin dil modelleri (Bölüm 70) için anlamıdır: ortalama çapraz entropi bit cinsinden 1 azaldığında perplexity tam olarak yarıya iner, çünkü `2^(H−1) = 2^H / 2`dir.

## 51.11 Kanal kapasitesi: ikili simetrik kanal ve veri işleme eşitsizliği

Şimdiye kadar kaynağı sıkıştırdık. Şimdi bitleri gürültülü bir kanaldan geçirelim. En basit gürültü modeli **ikili simetrik kanaldır** (binary symmetric channel, BSC): her bit olasılıkla `p` çevrilir, `1 − p` ile doğru iletilir. Bir İHA'nın bağlantısındaki bir bitin, gürültü nedeniyle ters çevrilmesi bu modelle yaklaşık olarak temsil edilir.

BSC'nin **kapasitesi**, girdi dağılımı üzerinden en büyük karşılıklı bilgidir: `C = max_{p(x)} I(X; Y)`. Simetrik bir kanalda en iyi girdi düzgün dağılımdır (genel bilgi). Düzgün girdi için çıktı da düzgündür, yani `H(Y) = 1` bit. Koşullu entropi ise `H(Y | X) = H(p)`dir, çünkü her girdi için belirsizlik yalnızca çevrilme olasılığından gelir. Böylece:

C = 1 − H(p)

Bu formül, Bölüm 51.4'teki karşılıklı bilgi tanımının doğrudan uygulamasıdır: `I(X;Y) = H(Y) − H(Y|X)`. Programın ilk bölümü bu formülü bir ortak tablodan hesaplayıp karşılaştırır.

```python
# kanal_kapasite.py: BSC kapasitesi C = 1 - H(p), veri işleme
# eşitsizliği (iki BSC'nin zinciri) ve Shannon-Hartley
# C = B log2(1 + S/N).
import math
import random

def h2(p):
    # İkili entropi (bit)
    if p in (0.0, 1.0):
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)

def bsc_karsilikli(p):
    # Düzgün girdi, BSC(p): I(X;Y) = H(Y) - H(Y|X) = 1 - H(p)
    # Ortak tablodan hesaplayıp formülle karşılaştır.
    ortak = {(0, 0): 0.5 * (1 - p), (0, 1): 0.5 * p,
             (1, 0): 0.5 * p, (1, 1): 0.5 * (1 - p)}
    py = {y: sum(v for (x, yy), v in ortak.items() if yy == y)
          for y in (0, 1)}
    hy = -sum(v * math.log2(v) for v in py.values() if v > 0)
    hyx = -sum(v * math.log2(v / 0.5)
               for v in ortak.values() if v > 0)
    return hy - hyx

def zincir(p1, p2):
    # X -> Y (BSC p1) -> Z (BSC p2): Z'nin çapraz olma olasılığı
    return p1 * (1 - p2) + (1 - p1) * p2
```

`bsc_karsilikli` fonksiyonu, düzgün girdi için ortak tabloyu kurar ve karşılıklı bilgiyi tablodan hesaplar. Formülle sonucun aynı çıkması, hem tanımın hem de formülün doğruluğunu birlikte sınar.

Veri işleme eşitsizliğini göstermek için bir kanal zinciri kurarız: `X`, `p₁`lik bir BSC'den geçip `Y` olur; `Y`, `p₂`lik ikinci bir BSC'den geçip `Z` olur. Bir kanaldan geçen bilgi bir sonrakine geçtikçe azalmak zorundadır. Bu, `I(X;Z) ≤ I(X;Y)` demektir. Zincirin toplam çapraz olma olasılığı `p₁(1 − p₂) + (1 − p₁)p₂` olur; bu bir BSC'nin çapraz olma olasılığıdır ve `I(X;Z) = 1 − H(zincir)` verir.

```python
def simule_zincir(p1, p2, n=200000, tohum=51):
    # Örnek tabanlı I(X;Z) tahmini (plug-in)
    rnd = random.Random(tohum)
    sayim = {}
    for _ in range(n):
        x = rnd.randrange(2)
        y = x ^ (rnd.random() < p1)
        z = y ^ (rnd.random() < p2)
        sayim[(x, z)] = sayim.get((x, z), 0) + 1
    px = {0: 0.0, 1: 0.0}
    pz = {0: 0.0, 1: 0.0}
    for (x, z), c in sayim.items():
        px[x] += c / n
        pz[z] += c / n
    i = 0.0
    for (x, z), c in sayim.items():
        pxz = c / n
        i += pxz * math.log2(pxz / (px[x] * pz[z]))
    return i
```

`simule_zincir` fonksiyonu aynı zinciri 200 000 bit üzerinden çalıştırır ve karşılıklı bilgiyi örneklerin sayımından (plug-in) tahmin eder. Sabit tohum `51` sonuçların tekrarlanabilir olmasını sağlar.

```python
def main():
    print("BSC kapasitesi C(p) = 1 - H(p)")
    for p in [0.0, 0.01, 0.05, 0.11, 0.5]:
        print("p=%.2f  C=%.4f  I(formul)=%.4f" % (
            p, 1 - h2(p), bsc_karsilikli(p)))
    print("--- veri isleme esitsizligi: I(X;Z) <= I(X;Y) ---")
    p1 = 0.05
    for p2 in [0.0, 0.05, 0.2]:
        iy = 1 - h2(p1)
        iz = 1 - h2(zincir(p1, p2))
        sim = simule_zincir(p1, p2)
        print("p2=%.2f  I(X;Y)=%.4f  I(X;Z)=%.4f  simulasyon=%.4f" % (
            p2, iy, iz, sim))
    print("--- Shannon-Hartley: C = B log2(1 + S/N) ---")
    for b_mhz, snr_db in [(1, 0), (1, 10), (10, 10), (10, 20)]:
        snr = 10 ** (snr_db / 10)
        c = b_mhz * 1e6 * math.log2(1 + snr)
        print("B=%2d MHz, SNR=%2d dB -> C = %.2f Mbit/s" % (
            b_mhz, snr_db, c / 1e6))
    # Ters soru: 5 Mbit/s için gereken bant genişliği (SNR = 10 dB)
    snr = 10 ** (10 / 10)
    b = 5e6 / math.log2(1 + snr)
    print("5 Mbit/s icin gereken B = %.3f MHz (SNR 10 dB)"
          % (b / 1e6))

if __name__ == "__main__":
    main()
```

```term
$ python kanal_kapasite.py
BSC kapasitesi C(p) = 1 - H(p)
p=0.00  C=1.0000  I(formul)=1.0000
p=0.01  C=0.9192  I(formul)=0.9192
p=0.05  C=0.7136  I(formul)=0.7136
p=0.11  C=0.5001  I(formul)=0.5001
p=0.50  C=0.0000  I(formul)=0.0000
--- veri isleme esitsizligi: I(X;Z) <= I(X;Y) ---
p2=0.00  I(X;Y)=0.7136  I(X;Z)=0.7136  simulasyon=0.7102
p2=0.05  I(X;Y)=0.7136  I(X;Z)=0.5471  simulasyon=0.5447
p2=0.20  I(X;Y)=0.7136  I(X;Z)=0.2220  simulasyon=0.2214
--- Shannon-Hartley: C = B log2(1 + S/N) ---
B= 1 MHz, SNR= 0 dB -> C = 1.00 Mbit/s
B= 1 MHz, SNR=10 dB -> C = 3.46 Mbit/s
B=10 MHz, SNR=10 dB -> C = 34.59 Mbit/s
B=10 MHz, SNR=20 dB -> C = 66.58 Mbit/s
5 Mbit/s icin gereken B = 1.445 MHz (SNR 10 dB)
```

İlk beş satır, `p` arttıkça kapasitenin düştüğünü gösterir. `p = 0,11` civarında kapasite `0,5` bite iner ve `p = 0,5`te sıfıra düşer: bu noktada çıktı girdiden tamamen bağımsızdır, çünkü bit çevrilme olasılığı yarıdır ve hiçbir bilgi kalmaz. `p = 0,01` gibi küçük gürültüde kapasite `0,9192`dir, yani bit başına yaklaşık `%8` kayıp vardır.

Veri işleme eşitsizliği, üç satırda açıkça görülür. `p₁ = 0,05` ve `p₂ = 0` iken zincir kesintisizdir ve `I(X;Z) = I(X;Y) = 0,7136` bit olur. `p₂ = 0,05` iken `I(X;Z) = 0,5471` bit çıkar, yani ikinci kanal bilgiyi düşürür. `p₂ = 0,2`de ise `0,2220` bit kalır. Simülasyon her üç satırda da teorinin hemen altındadır (örneğin `0,5447` ve `0,5471`), fark en fazla `0,0034` bittir. Bu fark, 200 000 örneklik tahmin gürültüsüdür, bir hata değildir. Bu eşitsizlik, bir sinir ağındaki her katmanın bilgiyi azaltabileceğini (ya da en fazla koruyabileceğini) söyler; Bölüm 51.4'teki öznitelik çıkarımı ile bağlanır.

![Şekil 51.8: Solda BSC kapasitesi C(p) = 1 − H(p). Sağda Shannon–Hartley kapasitesinin SNR'ye göre değişimi (1 MHz ve 10 MHz bant genişliği için).](gorseller/b51_bsc_shannon.png)

## 51.12 Shannon–Hartley: bant genişliği, sinyal gücü ve bir İHA veri bağı

BSC, bitleri zaten ayrık olarak alan bir kanaldır. Gerçek bir radyo bağında ise sinyal sürekli bir değerdir ve gürültü de Gauss dağılımlıdır (AWGN, toplamsal beyaz Gauss gürültüsü). Bu durumda kanal kapasitesi **Shannon–Hartley** formülüyle verilir:

C = B · log₂ (1 + S/N)   (bit/s)

Burada `B` bant genişliği (Hz), `S` sinyal gücü ve `N = N₀B` gürültü gücüdür. `S/N` oranı, doğrusal ölçekte signal-to-noise ratio'dur (SNR); desibel cinsinden `10 log₁₀(S/N)`dir.

Formülün iki sezgisi vardır. İlki, bant genişliği ne kadar büyükse, saniyede o kadar çok bağımsız sembol gönderebileceğindir (Nyquist: `B` Hz'lik bantta saniyede en fazla `2B` bağımsız reel sembol). İkincisi, her sembolün taşıyabileceği bilgi `log₂(1 + S/N)`dir: gürültü arttıkça bu ifade sıfıra yaklaşır, sinyal arttıkça logaritmik olarak büyür. Bant genişliği kapasiteyi doğrusal olarak artırır: `B`yi iki katına çıkarmak kapasiteyi de iki katına çıkarır. Güç ise logaritmik etki yapar: yüksek SNR'de gücü iki katına çıkarmak bant başına yaklaşık 1 bit/s/Hz kazandırır, düşük SNR'de bu kazanç çok daha küçüktür. Bu logaritmik davranış, bant genişliği ile güç arasındaki tasarım takaslarının temelidir.

Kanal kodlama teoremi bu kapasitenin anlamını tamamlar: `C`nin altındaki her hız için, hatayı istenildiği kadar küçülten kodlar vardır; `C`nin üstündeki hızlarda ise hata olasılığı sıfırdan uzakta kalır (Shannon 1948, genel bilgi). Teorem bir varlık ispatıdır: kapasiteye yaklaşan kodu nasıl kuracağını söylemez, yalnızca sınırı verir. Bölüm 51.13 ve 51.14'te pratik kodların bu sınıra ne kadar yaklaştığını göreceğiz.

Yukarıdaki programın son bölümü (satır 49–76) Shannon–Hartley hesabını ve ters sorusunu yapar: bir hedef hız için gereken bant genişliği nedir? Çıktının son altı satırı bu hesabın sonuçlarıdır.

Bu sayılar bir İHA veri bağı için somut bir karar sağlar. Varsayalım 10 MHz'lik bir kanal ve 20 dB SNR var. Teorik üst sınır `66,58 Mbit/s`dir. Buna karşılık bir telemetri akışı yalnızca `5 Mbit/s` gerektiriyorsa, 10 dB SNR'de bile yeterli bant genişliği `1,445 MHz`tir. Bu fark, bant genişliğinin ne zaman bir maliyet, ne zaman bir gereksinim olduğunu gösterir: kanal dar olduğunda hızı artırmanın yolu SNR'yi yükseltmek ya da daha verimli bir modülasyon ve kodlama seçmektir.

Teorik üst sınır ile sahada ulaşılan hız arasında her zaman bir fark olduğunu unutma. Modülasyon, kodlama, senkronizasyon, zamanlama ve kanal bozulmaları bu farkı büyütür. Bu bölüm kapasitenin **sınır** olduğunu söyler; sahada ne kadar yaklaşabildiğin ayrı bir mühendislik sorusudur.

## 51.13 Hata düzeltme: tekrar kodu, eşlik ve Hamming(7,4)

Kanal bitleri çevirdiğinde iki şey yapabilirsin: hatayı yalnızca fark etmek (tespit) ya da düzeltmek. Tespit ucuzdur, ama alıcı yeniden gönderim isteyebilir; düzeltme ise alıcının kendisi kararı verebilmesini sağlar. Bir İHA'dan gelen komutlarda bu fark, yeniden gönderimin zaman kaybına tahammül edilip edilemeyeceğine bağlıdır.

En basit düzeltme **tekrar kodudur**: her bit üç kez gönderilir, alıcı çoğunluk oyu ile karar verir. Üç kopyada bir bit çevrilirse çoğunluk doğru kalır; iki kopya çevrilirse yanlış karar verilir. Bu yüzden tekrar kodunun bit hata oranı (BER) `3p² − 2p³` olur. Bedeli ağırdır: hız `1/3`tür, yani her veri bitine üç kanal biti harcanır.

Daha verimli bir yol **eşlik** (parity) bitleridir. Bir eşlik biti, bir bit grubundaki 1'lerin sayısını çift yapacak şekilde seçilir. Tek bir eşlik biti tek hatayı **tespit** eder ama yerini söylemez. Bunu düzeltmek için birden fazla eşlik bitinin farklı bit kümelerini denetlemesi gerekir. Hamming(7,4) kodu tam bu fikri, 4 veri biti ve 3 eşlik biti ile en az bir hatayı düzeltecek biçimde kurar.

Düzeltme kapasitesini anlamak için **Hamming mesafesini** kullanırız: iki kod sözcüğü arasında farklı olan bit sayısı. Bir kodun en küçük çifter mesafesi `d` ise, `d − 1` hatayı tespit eder ve `⌊(d − 1)/2⌋` hatayı düzeltir. Hamming(7,4)'ün `d = 3`tür, bu yüzden bir hatayı düzeltir. İki hata teoride tespit edilebilir, ama bu kodun sendrom çözücüsü iki hatayı ayırt edemez: çift hatalı bir sözcük, yanlış bir tek hata gibi görünür ve yanlış bir konum düzeltilir.

Hamming(7,4)'te konumlar 1'den 7'ye numaralanır. Konum 1, 2 ve 4 eşlik bitleridir (2'nin kuvvetleri), kalan konumlar 3, 5, 6 ve 7 veri bitleridir. Her eşlik biti, konum numarasının belirli bir ikili basamağı 1 olan konumları denetler. Alıcı üç denetimi yapar ve sonuç bir **sendrom** verir. Sendrom, hatalı konumun ikili gösterimidir; sıfırsa hata yoktur. Aşağıdaki program kodlayıcıyı, sendrom çözücüyü ve BSC simülasyonunu birlikte içerir.

```python
# hamming_kanal.py: Hamming(7,4) kodlayıcı ve sendrom çözücü;
# ikili simetrik kanal (BSC) üzerinde kodsuz, tekrar(3) ve
# Hamming(7,4) bit hata oranı.
# Kullanım: python hamming_kanal.py <veri klasörü>
import csv
import itertools
import os
import random
import sys

def kodla(d):
    # d = [d1, d2, d3, d4]; çıktı konumları 1..7 sırasıyla:
    # p1 p2 d1 p3 d2 d3 d4
    d1, d2, d3, d4 = d
    p1 = d1 ^ d2 ^ d4
    p2 = d1 ^ d3 ^ d4
    p3 = d2 ^ d3 ^ d4
    return [p1, p2, d1, p3, d2, d3, d4]

def sendrom(c):
    # s = H c. Bitler: s1 s2 s3 (s1 en düşük değerlikli).
    s1 = c[0] ^ c[2] ^ c[4] ^ c[6]
    s2 = c[1] ^ c[2] ^ c[5] ^ c[6]
    s3 = c[3] ^ c[4] ^ c[5] ^ c[6]
    return s1 + 2 * s2 + 4 * s3      # 0: hata yok, 1..7: hatalı konum

def coz(c):
    s = sendrom(c)
    c = list(c)
    if s:
        c[s - 1] ^= 1                # tek bit hatasını düzelt
    return [c[2], c[4], c[5], c[6]], s
```

`kodla` dört veri bitinden yedi bitlik kod sözcüğü üretir. `sendrom` üç denetim yapar: `s1` konumların ikili basamağı 1 olanlarını (1, 3, 5, 7), `s2` ikinci basamağı 1 olanları (2, 3, 6, 7), `s3` üçüncüsünü (4, 5, 6, 7) denetler. `coz` sendromun gösterdiği konumdaki biti çevirir ve veri bitlerini geri alır.

```python
def bsc(bitler, p, rnd):
    # Her bit, bağımsız olarak p olasılıkla çevrilir.
    return [b ^ (1 if rnd.random() < p else 0) for b in bitler]

def tekrar_kodla(bitler):
    return [b for b in bitler for _ in range(3)]

def tekrar_coz(bitler):
    return [1 if sum(bitler[i:i + 3]) >= 2 else 0
            for i in range(0, len(bitler), 3)]
```

Kanal modeli BSC'dir: her bit bağımsız olarak `p` olasılıkla çevrilir. Tekrar kodu da bu bölümde kodlanır ve çözülür.

```python
def dogrula():
    # 16 mesaj: kodla, sıfır veya tek bit hatası, çöz
    kod = {}
    for d in itertools.product([0, 1], repeat=4):
        c = kodla(list(d))
        kod[d] = c
        assert coz(c)[0] == list(d)
        for k in range(7):
            e = list(c)
            e[k] ^= 1
            assert coz(e)[0] == list(d), (d, k)
    minimum = min(sum(a != b for a, b in zip(kod[x], kod[y]))
                  for x, y in itertools.combinations(kod, 2))
    print("16 mesaj x (hatasiz + 7 tek bit hatasi): hepsi dogru")
    print("kod sozcuklerinin en kucuk Hamming mesafesi: %d" % minimum)
    return kod
```

`dogrula` fonksiyonu, 16 veri mesajının her birini hatasız ve her konumda tek bit hatasıyla sınar. Hepsi doğru çözülmelidir. Ayrıca kod sözcükleri arasındaki en küçük Hamming mesafesini hesaplar; sonuç `3` çıkmalıdır, çünkü bu `d = 3` demektir.

```python
def main(veri):
    kod = dogrula()
    c = "".join(map(str, kodla([1, 0, 1, 1])))
    print("ornek: 1011 -> %s" % c)
    rnd = random.Random(51)
    n_mesaj = 40000
    veri_bitler = [rnd.randrange(2) for _ in range(4 * n_mesaj)]
    satirlar = []
    print("%-7s %-10s %-10s %s" % ("p", "kodsuz", "tekrar3",
                                  "hamming74"))
    for p in [0.001, 0.005, 0.01, 0.02, 0.05, 0.10, 0.15]:
        # kodsuz
        al = bsc(veri_bitler, p, rnd)
        ber0 = sum(a != b for a, b in zip(al, veri_bitler)) / len(
            veri_bitler)
        # tekrar kodu
        al = tekrar_coz(bsc(tekrar_kodla(veri_bitler), p, rnd))
        ber3 = sum(a != b for a, b in zip(al, veri_bitler)) / len(
            veri_bitler)
        # Hamming(7,4)
        cozulen = []
        for i in range(n_mesaj):
            c = kodla(veri_bitler[4 * i:4 * i + 4])
            cozulen.extend(coz(bsc(c, p, rnd))[0])
        hata = sum(a != b for a, b in zip(cozulen, veri_bitler))
        berh = hata / len(veri_bitler)
        print("%-7.3f %-10.5f %-10.5f %.5f" % (p, ber0, ber3, berh))
        formul = 3 * p * p - 2 * p ** 3
        satirlar.append([p, "%.6f" % ber0, "%.6f" % ber3,
                         "%.6f" % berh, "%.6f" % formul])
    yol = os.path.join(veri, "b51_ber.csv")
    with open(yol, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["p", "kodsuz", "tekrar3", "hamming74",
                    "tekrar3_formul"])
        w.writerows(satirlar)

if __name__ == "__main__":
    main(sys.argv[1])
```

```term
$ python hamming_kanal.py engine\veri
16 mesaj x (hatasiz + 7 tek bit hatasi): hepsi dogru
kod sozcuklerinin en kucuk Hamming mesafesi: 3
ornek: 1011 -> 0110011
p       kodsuz     tekrar3    hamming74
0.001   0.00108    0.00001    0.00000
0.005   0.00516    0.00011    0.00020
0.010   0.00992    0.00027    0.00083
0.020   0.02021    0.00114    0.00333
0.050   0.04939    0.00725    0.01983
0.100   0.09902    0.02811    0.06676
0.150   0.15052    0.06124    0.12891
```

Çıktının ilk satırı, 16 mesajın ve 7 konumun hepsinde tek hatanın düzeltildiğini doğrular. Kod sözcükleri arasındaki en küçük mesafe `3`tür, bu da teorinin tam olarak öngördüğü değerdir. Örnek satırı `1011` mesajının kodunu `0110011` olarak verir. Bu, Örnek 4'te elle izleyeceğimiz sonuçtur.

Simülasyon her `p` için 160 000 veri biti üzerinde yapılır. Tablo üç sütunda bit hata oranlarını verir ve Şekil 51.10 aynı sonucu log-log ölçekte gösterir.

Sonuçları dikkatle okuman gerekir. `p = 0,005` ile `0,02` arasında tekrar kodu en düşük bit hatasını verir: `p = 0,01`de `0,00027`, Hamming'de `0,00083`. `p = 0,001`de iki kodun hatası sıfıra o kadar yakındır ki 160 000 bitlik simülasyonda sıralama gürültüye kalır. Ama tekrar kodu her veri bitine üç kanal biti harcar; Hamming ise `7/4 = 1,75` kanal biti harcar. Yani aynı kanal kullanım sayısı için Hamming'in veri hızı daha yüksektir, ama bit hatası daha fazladır. Bu bir değiş tokuştur. Her iki kod da kanal kötüleştikçe kazancını kaybeder: `p = 0,15`te tekrar kodu `0,061`, Hamming `0,129` verir, kodsuz hata `0,151`dir. Yani bu kodlar yalnızca belli bir gürültü seviyesinin altında anlamlıdır; üstünde kanal zaten fazla bozuktur.

Bu sonuçların mesajı şudur: "daha iyi kod" tek bir ölçüte göre tanımlanamaz. Hız, bit hatası, gecikme ve enerji birlikte değerlendirilmelidir. Bölüm 51.11'deki kapasite, bu değiş tokuşun üst sınırını verir: `C = 1 − H(p)`. `p = 0,01` için `C ≈ 0,919` bit/kanal kullanımıdır. Hamming'in hızı `0,571`, tekrar kodunun hızı `0,333`tür; her ikisi de bu sınırın epey altındadır. Sınıra daha yakın kodlar, Bölüm 51.14'te anlatılan LDPC ve polar kodlardır.

![Şekil 51.9: Hamming(7,4) için küme gösterimi. Üç çember üç eşlik bitinin kapsamını gösterir; kesişim bölgelerindeki veri bitleri birden fazla denetimde yer alır.](gorseller/b51_hamming_venn.png)

Şekil 51.9 sendromun mantığını gösterir. Her veri biti en az iki çemberin kesişiminde olduğundan, o bitteki bir hata birden fazla denetimi bozar ve sendrom bu bitin konumunu verir. Eşlik bitleri (konum 1, 2, 4) yalnızca bir çemberde yer alır; bu yüzden bu konumdaki hata da yalnızca o eşlik bitini bozar.

![Şekil 51.10: Kodsuz, tekrar(3) ve Hamming(7,4) için bit hata oranı, kanal hata olasılığına göre (log-log). Sıfır değerler log ölçekte çizilemediği için atlanmıştır.](gorseller/b51_kodsuz_kodlu_ber.png)

## 51.14 CRC, Reed–Solomon, LDPC, turbo ve polar kodlar

Bölüm 31.5'te gördüğün `zlib.crc32` ile Bölüm 45'te gösterdiğin CRC-16/CCITT-FALSE aynı ailenin üyeleridir: **döngüsel artıklık denetimi**. Bir çerçeveye bir artık (CRC) eklenir; alıcı aynı işlemi yapar ve artık sıfır değilse çerçeve bozulmuştur. Bu yöntem tespit eder, düzeltmez. Bölüm 45'te CRC-16 için standart test değeri `"123456789"` metninden `0x29B1` olarak verilmişti. Bir `n` bitlik CRC, uzunluğu `n` bitten küçük ya da eşit olan her **patlamayı** (ardışık bozuk bit dizisi) tespit eder (genel bilgi). Hamming(7,4) ise tek bit hatasını düzeltir ama çok bitlik patlamalar için yetersizdir; bu yüzden ikisi birlikte kullanılır: CRC tespit eder, ayrı bir kod düzeltme yapar ya da yeniden gönderim tetikler.

Modern kodlar bu iki işi birleştirir ve Shannon sınırına çok daha yakındır (genel bilgi, sayısal değerler kod ailesine ve blok uzunluğuna göre değişir):

- **Reed–Solomon** kodları, sembol (birden fazla bit) düzeyinde çalışan doğrusal kodlardır. `n − k` eşlik sembolüyle `(n − k)/2` sembol hatasını düzeltir. CD'lerdeki çizik ve QR koddaki bozulma bu kodla kurtarılır.
- **LDPC** (düşük yoğunluklu eşlik denetimi) kodları, seyrek bir denetim matrisiyle tanımlanır ve kod çözme yinelemeli mesaj geçişiyle yapılır. 5G NR veri kanalında LDPC kullanılır.
- **Turbo** kodlar, iki kodlayıcının bir arada ve bir karıştırıcı (interleaver) ile çalışmasına dayanır; 1993'te tanıtıldıklarında Shannon sınırına çok yakın oldukları görüldü.
- **Polar** kodlar, Arıkan'ın 2009'da tanıttığı, kanal kutuplaşması olgusuna dayanan kodlardır. 5G NR'nin kontrol kanalında kullanılır.

Bu kodların hepsi Bölüm 51.11'deki kapasite sınırına, pratik blok uzunluklarında yaklaşır. Ama kapasite bir varlık sınırıdır; bu kodların nasıl kurulduğu ve kod çözme karmaşıklığı ayrı bir konudur, bu kitabın kapsamı dışındadır. Kodların ayrıntıları için standartlara ve ders kitaplarına bak. Bu bölümde amacımız, her kodun neyi düzelttiğini ve neye yaklaştığını bilmek.

## 51.15 Semantik iletişim: bitleri değil anlamı iletmek

Shannon'ın teorisi, bitlerin doğru iletilmesiyle ilgilenir. Warren Weaver 1949'da bunu üç düzeye ayırdı: **teknik düzey** (semboller doğru iletiliyor mu), **anlamsal düzey** (gönderilen anlamı doğru taşıyor mu) ve **etkililik düzeyi** (alıcının davranışını değiştiriyor mu). Shannon'ın kanal kodlama teoremi birinci düzeyi çözer. Anlamsal ve etkililik düzeyleri ise ayrı bir problemdir.

**Semantik iletişim** bu ikinci düzeye yönelik bir yaklaşımdır: gönderici tüm bitleri değil, alıcının görevi için gerekli olan özellikleri iletir. Buradaki ölçü, yine karşılıklı bilgidir ama farklı bir değişkenle: görev değişkeni `T` için `I(Z; T)` (`Z` iletilen özellikler). Bu, Bölüm 51.4'te öznitelik seçiminde gördüğümüz mantığın iletişime taşınmasıdır: iletilmesi gereken bit sayısı, görevle ilgili bilginin miktarına bağlıdır, bitlerin tam sayısına değil.

Bu yaklaşımın bedeli vardır. Gönderici ve alıcı, anlamı ortak bir modelde (bir kodlayıcı ve bir çözücü) paylaşmalıdır. Model uyumsuz olursa iletim bit hatasından farklı biçimde bozulur: bitler doğru gelse bile anlam kayabilir. Bu, klasik kanal modelinde olmayan bir hata türüdür. Ayrıca anlamsal kazanç görevle bağlıdır: bir sınıflandırma görevi için iyi olan özellikler, bir yeniden yapılandırma görevi için yetersiz olabilir.

Mert'in ÖZCE projesi, bu çerçevenin kavramsal bir uygulaması olarak bu bölümde anılır. Bu bölümde yalnızca kavramsal atıf yapılmıştır; proje klasörünün içeriği bu kitaba kopyalanmamıştır. Bölüm 46'daki kuantizasyon ve Bölüm 72'deki değişimsel kodlayıcılar, gizli temsilin ne kadar bilgi taşıdığını ölçmenin araçlarıdır. Bir anlamsal kodlayıcıda gizli temsil ile girdi arasındaki karşılıklı bilgi ve KL terimi, iletilecek temsilin boyutunu ve kalitesini belirler.

## 51.16 Entropi ve güvenlik: parola ve anahtar uzunluğu

Entropi bir güvenlik ölçüsüdür de. Düzgün ve bağımsız rastgele seçilmiş bir parolanın entropisi `L · log₂ N`dir; burada `L` uzunluk, `N` alfabe büyüklüğüdür. Bu, saldırganın tüm olasılıkları denemek için gereken bit sayısıdır. Aşağıdaki program birkaç parola türü için bu değeri ve varsayımsal bir tarama süresini hesaplar.

```python
# parola.py: parola entropisi H = L log2(N) (düzgün, bağımsız seçim)
# ve varsayımsal bir saldırganın tüm uzayı tarama süresi.
import math

HIZ = 1e10   # varsayımsal tahmin hızı: saniyede 10^10 deneme

def entropi_bit(uzunluk, alfabe):
    return uzunluk * math.log2(alfabe)

def ortalama_sure_yil(bit):
    # Ortalama: uzayın yarısını tarama (2^bit / 2 deneme)
    saniye = 2 ** bit / 2 / HIZ
    return saniye / (365.25 * 24 * 3600)

def main():
    ornekler = [
        ("8 küçük harf (a-z)", 8, 26),
        ("8 harf+rakam (a-zA-Z0-9)", 8, 62),
        ("12 yazdırılabilir ASCII", 12, 95),
        ("6 kelime, 7776'lık liste", 6, 7776),
    ]
    print("%-28s %8s %10s" % ("parola", "bit", "yil"))
    for ad, n, a in ornekler:
        b = entropi_bit(n, a)
        print("%-28s %8.1f %10.3g" % (ad, b, ortalama_sure_yil(b)))

if __name__ == "__main__":
    main()
```

`entropi_bit` formülü doğrudan uygular. `ortalama_sure_yil` ise uzayın yarısını taradığını varsayar (ortalama durum), saniyede `10^10` deneme hızında. Bu hız bir örnek değer, bir ölçüm değil; gerçek saldırı hızları donanıma, algoritmaya ve tuzlamaya (salting) bağlıdır.

```term
$ python parola.py
parola                            bit        yil
8 küçük harf (a-z)               37.6   3.31e-07
8 harf+rakam (a-zA-Z0-9)         47.6   0.000346
12 yazdırılabilir ASCII          78.8   8.56e+05
6 kelime, 7776'lık liste         77.5    3.5e+05
```

Tablo açık bir mesaj verir: sekiz küçük harf 37,6 bit eder ve varsayımsal hızda saniyeler içinde kırılır (yıl sütunu `3,31 × 10⁻⁷`). Aynı uzunlukta harf ve rakam kullanmak 47,6 bit eder, ama hâlâ kolay bir hedeftir. On iki karakterlik yazdırılabilir ASCII parola 78,8 bit eder ve pratikte aranmaz. Altı kelimelik bir parola (7776 kelimelik listeden seçilmiş, zar ile üretilmiş) 77,5 bit verir ve uzunluk ile hatırlanabilirlik arasında iyi bir denge sunar.

Burada bir uyarı önemlidir. Bu formül yalnızca **gerçekten düzgün ve bağımsız** seçimde geçerlidir. İnsanların seçtiği parolalar düzgün değildir: "Sifre123" gibi tahmin edilebilir kalıplar, sözlük kelimeleri ve kişisel bilgiler efektif entropiyi düşürür. Bu yüzden bir parolanın gücü, uzunluğuna ve rastgelelik kaynağına birlikte bakılarak değerlendirilir. Rastgelelik kaynağı tahmin edilebilir olduğunda entropi formülü hiçbir işe yaramaz. Bölüm 32.2'de anlatılan `secrets` modülü, işletim sisteminin kriptografik rastgele kaynağını kullanır; `random` modülü ise tahmin edilebilirdir (Mersenne Twister), bu yüzden güvenlik için kullanılmaz.

Anahtar uzunluğu da aynı mantıkla değerlendirilir. 128 bitlik bir simetrik anahtarın olası değer sayısı `2¹²⁸`dir; bu, her saniye `10^10` deneme yapan bir saldırganın bile tüm uzayı taramasını astronomik sürelere uzatır. Bu, anahtarın uzunluğunun güvenliğin üst sınırını belirlediğini ve tek başına yeterli olmadığını gösterir: anahtarın rastgele üretilmesi ve saklanması aynı derecede önemlidir.

## Çözümlü Örnekler

Bu bölümdeki dört örnek, zorluk sırasıyla ★, ★★, ★★ ve ★★★ olarak dizilmiştir. Her örnek Bölüm 5'teki altı adımı izler: anla, örnekle, kaba çöz, örüntüyü bul, iyileştir ve doğrula. Doğrulama adımında elle iz sürme tablosu bulunur. Her örneğin sonunda, hiçbir yapay zekâ aracı kullanmadan çözebilmen için bir varyasyon sorusu vardır.

### Örnek 1 (★): Dört sembollü kaynağın Huffman kodu ve ortalama uzunluğu

Bir kaynak `a, b, c, d` sembollerini `0,4; 0,3; 0,2; 0,1` olasılıklarıyla üretiyor. Kaynağın entropisi nedir, Huffman kodunun ortalama uzunluğu kaça çıkar ve aradaki fark ne kadardır?

**Adım 1 — Anla.** İstenen üç sayı var: `H(p)`, `L = ∑ pᵢ lᵢ` ve `L − H`. Huffman uzunlukları, en küçük iki olasılığı sırayla birleştirerek bulunur.

**Adım 2 — Örnekle.** Kaynaktan on sembollük bir örnek düşünelim: `a a b c a d b a c b`. Bu dizide `a` dört, `b` üç, `c` iki, `d` bir kez geçer; yani frekanslar olasılıklara yakındır. Bu dizinin kodlanmış uzunluğu `4·1 + 3·2 + 2·3 + 1·3 = 19` bittir; sembol başına `1,9` bit, yani ortalama `L` ile tam uyumludur.

**Adım 3 — Kaba çöz.** Entropi `H = −(0,4 log₂ 0,4 + 0,3 log₂ 0,3 + 0,2 log₂ 0,2 + 0,1 log₂ 0,1)` ile hesaplanır; bu `1,8464` bittir. Huffman birleştirmeleri şöyledir: önce `c` (0,2) ve `d` (0,1) birleşir, toplam `0,3`; sonra `b` (0,3) bu düğümle birleşir, toplam `0,6`; son olarak `a` (0,4) ile `0,6` birleşir ve kök `1` olur. Derinlikler: `a` için 1, `b` için 2, `c` ve `d` için 3.

**Adım 4 — Örüntü.** Huffman her adımda en küçük iki düğümü birleştirdiği için, en az olasılıklı iki sembol en derin yaprakta kalır. Sonuçta olasılığı büyük olan sembol en kısa kodu alır. Ortalama uzunluk: `L = 0,4 · 1 + 0,3 · 2 + 0,2 · 3 + 0,1 · 3 = 1,9` bit.

**Adım 5 — İyileştir.** Tek sembol kodunda `L − H = 0,054` bit fark var. İki sembolü birlikte kodlarsak (16 çift, olasılıkları çarpımdır), ortalama sembol başına `1,8650` bit olur. Üç sembolü birlikte kodlarsak `1,8590` bit olur. Her iki durumda da fark küçülür; bu, blok kodlamanın Huffman'ın bir bitlik tabanını aşmasının yoludur. Aritmetik kodlama (Bölüm 51.6) bunu tek tek blok yapmadan başarır.

**Adım 6 — Doğrula.** Elle iz tablosu:

| Sembol | p | kod uzunluğu l | p · l |
|---|---|---|---|
| a | 0,4 | 1 | 0,4 |
| b | 0,3 | 2 | 0,6 |
| c | 0,2 | 3 | 0,6 |
| d | 0,1 | 3 | 0,3 |
| Toplam | 1,0 | | L = 1,9 |

Kraft toplamı `2⁻¹ + 2⁻² + 2⁻³ + 2⁻³ = 1` olduğundan kod tam bir ağaçtır. `H = 1,8464 ≤ L = 1,9 < H + 1 = 2,8464` sınırı sağlanır. Programın çıktısı (`L = 1,9000`, `L − H = 0,0536`) ile tablo birebir tutar.

**Bunu AI'sız yazabilir misin?** Olasılıkları `0,5; 0,25; 0,125; 0,125` olan bir kaynak için entropiyi, Huffman uzunluklarını ve `L − H` farkını hesapla. Bu dağılım ikinin kuvvetleridir; bu yüzden farkın sıfır çıkıp çıkmadığını önceden tahmin et ve sonra doğrula.

### Örnek 2 (★★): İki dağılım için KL(p‖q) ve KL(q‖p)

Gerçek dağılım `p = [0,9; 0,1]`, varsayılan dağılım `q = [0,5; 0,5]`. İki yönlü KL'yi hesapla ve asimetrinin yorumunu yap.

**Adım 1 — Anla.** İki ayrı büyüklük isteniyor: `D_KL(p ‖ q)` ve `D_KL(q ‖ p)`. Her biri ayrı bir toplamdır ve birbirine eşit olmak zorunda değildir.

**Adım 2 — Örnekle.** Yazı ve tura sonuçlarından bir örnek: `p`ye göre 10 atıştan 9'u yazı, 1'i tura gelmiştir. Bu veriyi `q` (düzgün para) modeliyle kodlamanın bedeli nedir?

**Adım 3 — Kaba çöz.** `D_KL(p‖q) = ∑ p log₂ (p/q)` ve `D_KL(q‖p) = ∑ q log₂ (q/p)` formüllerini doğrudan uygula.

**Adım 4 — Örüntü.** Her iki yönde de terimler `p` ile `q`nun oranına bağlıdır. `p` büyük olduğu yerde `p/q` büyük çıkarsa ilk yönde terim büyür. İkinci yönde `q` büyükken `q/p` oranı, `p`nin küçük olduğu yerde büyür. Asimetri bu iki ağırlıklandırmanın farklı olmasından gelir.

**Adım 5 — İyileştir.** Bu hesaplar için iki cebirsel kısayol vardır: `D_KL(p‖q) = H(p,q) − H(p)`, yani çapraz entropi ile entropi arasındaki fark. Bu yolla `H(p,q)` ve `H(p)` ayrı ayrı hesaplanır ve farkı alınır. Bu, sonucu kontrol etmek için de iyi bir yoldur.

**Adım 6 — Doğrula.** İz tablosu:

| Yön | x | p(x) | q(x) | p/q | p log₂(p/q) |
|---|---|---|---|---|---|
| KL(p‖q) | yazı | 0,9 | 0,5 | 1,8 | 0,7632 |
| KL(p‖q) | tura | 0,1 | 0,5 | 0,2 | −0,2322 |
| Toplam | | | | | 0,5310 |

Ters yön için aynı tablonun `q` ve `p` rollerini değiştirmesi gerekir: `q log₂(q/p)` terimleri `−0,4240` ve `1,1610` olur, toplam `0,7370`tir. Programın çıktısı (`0,5310` ve `0,7370`) ile eşleşir. Yorum: bu örnekte `KL(p‖q)` daha küçüktür, çünkü `q` düzgün seçildiğinde `p`nin kütlesi `q`nun geniş kapsamında kalır. Ters yönde `q`nun `0,5` kütlesi `p`nin yalnızca `0,1` kütle taşıdığı tura bölgesine düşer ve ceza büyür.

**Bunu AI'sız yazabilir misin?** `p = [0,8; 0,2]` ve `q = [0,6; 0,4]` için iki yönlü KL'yi hesapla. Hangi yönün daha büyük çıkmasını bekliyorsun ve neden? Önce tahmin et, sonra hesapla.

### Örnek 3 (★★): Üç sınıflı softmax, çapraz entropi kaybı ve gradyan

Bir sınıflandırıcı üç sınıf için logitler `z = [2,0; 0,5; −1,0]` üretiyor. Doğru sınıf `y = 0`. Olasılıkları, kaybı (nat) ve gradyanı bul.

**Adım 1 — Anla.** Üç şey isteniyor: `p = softmax(z)`, `L = −ln p₀` ve `∂L/∂zᵢ`. Gradyan formülü `pᵢ − yᵢ`dir, ama bunu türetmeden kullanmamak gerekir.

**Adım 2 — Örnekle.** Tek bir sınıf etiketi için düşün: doğru sınıfın olasılığı `0,5`'ten küçükse kayıp `ln 2 ≈ 0,69`dan büyüktür; `0,9`'a yakınsa kayıp `0,1`e yakındır. Bu sezgi kaybın formunu kontrol etmemizi sağlar.

**Adım 3 — Kaba çöz.** Her logiti üsse al, topla, böl. `e² = 7,3891`, `e^0,5 = 1,6487`, `e^(−1) = 0,3679`. Toplam `9,4057`.

**Adım 4 — Örüntü.** Kayıp `L = −z₀ + ln ∑ e^{zⱼ}` yazılabilir. Bu biçimde türev alınca `∂L/∂zᵢ = pᵢ − yᵢ` çıkar. Doğru sınıfın gradyanı negatiftir, diğerleri pozitiftir ve toplamları sıfırdır.

**Adım 5 — İyileştir.** Büyük logitlerde taşma olmaması için log-sum-exp kullan: en büyük logiti (`2,0`) çıkar; `z − 2 = [0; −1,5; −3]`. Böylece üsler en fazla sıfır olur ve sonuç değişmez.

**Adım 6 — Doğrula.** İz tablosu:

| Sınıf | logit z | e^z | p = e^z / 9,4057 | gradyan p − y |
|---|---|---|---|---|
| 0 (doğru) | 2,0 | 7,3891 | 0,7856 | −0,2144 |
| 1 | 0,5 | 1,6487 | 0,1753 | 0,1753 |
| 2 | −1,0 | 0,3679 | 0,0391 | 0,0391 |
| Toplam | | 9,4057 | 1,0000 | 0,0000 |

Kayıp `L = −ln 0,7856 = 0,2413` nat. Programın çıktısı (`p = [0,7856; 0,1753; 0,0391]`, `L = 0,2413`, gradyan `[−0,2144; 0,1753; 0,0391]`) tabloyla birebir tutar. Gradyanların toplamı sıfır olduğu için tablonun son satırı bu kontrolü verir.

**Bunu AI'sız yazabilir misin?** Logitler `[0; 0; 0]` ve doğru sınıf `1` ise `p`yi, kaybı (nat) ve gradyanı bul. Simetrik durumda gradyanların ne olmasını beklediğini önce söyle ve sonra doğrula.

### Örnek 4 (★★★): Hamming(7,4) ile 1011 mesajını kodlamak, bir hatayı bulup düzeltmek

Mesaj `1011` olsun. Kodla, kanalda konum 5'te bir bit çevrilsin, alıcı sendromu hesaplayıp hatayı düzeltsin.

**Adım 1 — Anla.** Üç iş var: kodlamak, hatayı bulmak (sendrom ile), düzeltip veriyi geri almak. Konum numaraları 1'den 7'ye gider; 1, 2 ve 4 eşlik bitleridir.

**Adım 2 — Örnekle.** Mesajın dört bitini `d₁ d₂ d₃ d₄ = 1 0 1 1` olarak alalım. Konumlar: `c₁ = p₁`, `c₂ = p₂`, `c₃ = d₁`, `c₄ = p₃`, `c₅ = d₂`, `c₆ = d₃`, `c₇ = d₄`.

**Adım 3 — Kaba çöz.** Eşlik bitleri: `p₁ = d₁ ⊕ d₂ ⊕ d₄`, `p₂ = d₁ ⊕ d₃ ⊕ d₄`, `p₃ = d₂ ⊕ d₃ ⊕ d₄`. Bunları hesapla. `d₁ = 1, d₂ = 0, d₃ = 1, d₄ = 1` için: `p₁ = 1 ⊕ 0 ⊕ 1 = 0`, `p₂ = 1 ⊕ 1 ⊕ 1 = 1`, `p₃ = 0 ⊕ 1 ⊕ 1 = 0`.

**Adım 4 — Örüntü.** Kod sözcüğü `[p₁ p₂ d₁ p₃ d₂ d₃ d₄] = 0 1 1 0 0 1 1`dir. Hatalı konum, sendromun ikili değeridir: `s = s₁ + 2 s₂ + 4 s₃`. Bu, konumun ikili basamaklarının kendisidir; bu yüzden tek bit hatasının konumunu doğrudan verir.

**Adım 5 — İyileştir.** Alıcı kanal çıktısını alır: konum 5 çevrilmiş olsun, `r = 0 1 1 0 1 1 1`. Sendromu üç denetimle hesaplar: `s₁ = r₁ ⊕ r₃ ⊕ r₅ ⊕ r₇`, `s₂ = r₂ ⊕ r₃ ⊕ r₆ ⊕ r₇`, `s₃ = r₄ ⊕ r₅ ⊕ r₆ ⊕ r₇`. Sonucu `s = s₁ + 2 s₂ + 4 s₃` ile birleştir. Sonra konum 5'i çevir ve veri bitlerini al.

**Adım 6 — Doğrula.** İz tablosu (bit vektörleri):

| Adım | Vektör | Hesap | Sonuç |
|---|---|---|---|
| Kod sözcüğü | 0110011 | kodla(1011) | — |
| Alınan | 0110111 | konum 5 çevrildi | — |
| s₁ | | r₁⊕r₃⊕r₅⊕r₇ = 0⊕1⊕1⊕1 | 1 |
| s₂ | | r₂⊕r₃⊕r₆⊕r₇ = 1⊕1⊕1⊕1 | 0 |
| s₃ | | r₄⊕r₅⊕r₆⊕r₇ = 0⊕1⊕1⊕1 | 1 |
| Sendrom | 101 | 1 + 0 + 4 | 5 |
| Düzeltilmiş | 0110011 | konum 5 çevrildi | — |
| Veri | 1011 | c₃ c₅ c₆ c₇ | 1011 |

Sendrom `5` çıktı, yani hata konum 5'te. Düzeltilmiş kod sözcüğü orijinal sözcükle aynıdır ve veri `1011` olarak geri gelir. Programın `coz` fonksiyonu aynı sonucu verir: `([1, 0, 1, 1], 5)`.

**Bunu AI'sız yazabilir misin?** Aynı kod sözcüğü `0110011` için konum 3'te bir hata olsun. Alınan vektörü yaz, üç sendromu hesapla ve düzeltilmiş veriyi bul. Son olarak konum 1 ile 2 birlikte çevrilseydi ne olurdu diye düşün: Hamming(7,4) bu durumu düzeltebilir mi?

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ aracı kullanma. Kodu, testleri ve ölçümleri kendin yaz. Amaç, aşağıdaki kavramları bir mülakatta ya da boş bir IDE'de yeniden kurabilmektir. Bir hata bulursan, önce hatayı kendin çöz; bu, bu bölümün en değerli kısmıdır.
:::

### Proje 1 (★★): Sıkıştırma laboratuvarı

**Amaç.** Huffman, aritmetik kodlama ve basit bir LZ77 kodlayıcıyı sıfırdan yaz; üçünü de kitabın kendi metinleri ve ikili bir telemetri benzeri veri üzerinde karşılaştır.

**Yapılacak / Beklenen davranış.** Üç ayrı program olsun: `huff.py`, `arit.py` ve `lz.py`. Her biri bir dosya okuyup sıkıştırılmış bit sayısını yazdırsın, sonra çözüp özgün dosyayla bayt bayt aynı olduğunu doğrulasın. Üç kaynak kullan: (a) bu kitabın bir bölümünün düz metni, (b) bir sensör telemetri simülasyonu (sabit tohumlu, normal değerler ve ara sıra anomaliler), (c) rastgele bayt dizisi. Her biri için entropiyi, zlib (düzey 9) sonucunu ve kendi kodlayıcılarının sonucunu tabloya koy.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Huffman için bu bölümdeki `huffman_uzunluk` fikrini kullan ama bu sefer kod sözcüklerini gerçekten ata ve çöz. Aritmetik kodlama için bu bölümdeki WNC gerçeklemesini referans al ama kendi ifadelerinle yaz: önce kodlayıcıyı, sonra çözücüyü ve son olarak bekleyen-bit mekanizmasını. LZ77 için pencere boyutunu 4096 ve eşleşme uzunluğunu 258 ile sınırla; kaba kuvvetten daha hızlı bir bulma istersen bir karma tablo (hash) düşün, ama önce doğru çalıştığından emin ol.

**Başarı kriterleri.** (1) Üç kodlayıcı üç kaynakta da gidiş-dönüşte özgün veriyi birebir geri verir. (2) Çarpık kaynakta aritmetik kodunuz Huffman'dan en az `0,4` bit/simge daha iyi çıkar (bu bölümdeki `0,5719` ve `1,1` değerlerine benzer). (3) Rastgele veride çıktı boyutu girdi boyutunun `%0,5`ten fazla büyümez. (4) Tabloda her değer ya ölçülmüş ya da hesaplanmış olarak etiketlenmiştir.

### Proje 2 (★★★): Gürültülü İHA telemetri kanalı simülatörü

**Amaç.** Bir İHA'dan yere gönderilen telemetri karesini gürültülü bir kanaldan geçiren bir simülatör yaz. Hata düzeltme, hata tespiti ve yeniden gönderimi birlikte değerlendir.

**Yapılacak / Beklenen davranış.** Simülatör şunları yapsın: (a) sabit uzunlukta bir telemetri karesi üretsin (sıra numarası, sensör değerleri, bir CRC-16/CCITT-FALSE sağlaması; test değeri Bölüm 45'te `"123456789"` için `0x29B1`), (b) kareyi BSC (ve isteğe bağlı olarak bozulmanın patlamalı olduğu bir Gilbert-Elliott modeli) üzerinden geçirsin, (c) alıcı tarafında üç strateji uygulasın: yalnızca tespit ve yeniden gönderim, Hamming(7,4), tekrar kodu. Her strateji için kare kaybı oranını, gerekli ortalama kanal bit sayısını ve etkili veri hızını ölç.

**Önerilen yaklaşım (ipucu).** Kareyi önce CRC ile sağla, sonra kodla. Yeniden gönderim sayısını bir döngüyle modelle; her yeniden gönderimde yeni bir gürültü tohumu kullan. Hız–güvenilirlik grafiğinde yatay eksene kanal hata olasılığını, dikey eksene etkili veri hızını koy. CRC'nin tespit edemediği bir durumu kasıtlı olarak üret ve neden olduğunu açıkla.

**Başarı kriterleri.** (1) Simülatör sabit tohumla birebir tekrarlanabilir sonuç verir. (2) Her strateji için en az beş farklı `p` değeri ölçülmüş ve grafiğe konmuştur. (3) CRC-16'nın tespit ettiği hatalar ile kaçırdığı hataların oranı hesaplanmıştır ve kaçırma ihtimalinin neden çok küçük olduğu açıklanmıştır. (4) Hız–güvenilirlik grafiği üzerinde Bölüm 51.11'deki `C = 1 − H(p)` sınırı çizilmiş ve stratejilerin bu sınırın altında kaldığı gösterilmiştir.

### Ek Alıştırmalar

Aşağıdaki problemler cevapsızdır. Her birini önce kendin çöz, sonra kontrol etmek için bu bölümdeki programları kullan.

1. (★) Bir zar atışının entropisini hesapla. Ardından, zarın yalnızca çift ve tek yüzlerini ayırt eden bir ölçümün karşılıklı bilgisini düşün: `I(zar; paritesi)` nedir?
2. (★) İki bağımsız madeni paranın birlikte entropisi kaçtır? Zincir kuralıyla doğrula.
3. (★) Kanal BSC(0,1) ise, düzgün girdi için karşılıklı bilgi nedir? Bu değeri `1 − H(0,1)` formülüyle hesapla.
4. (★★) Bir kaynağın 8 sembolü vardır ve dağılım `[1/2, 1/4, 1/8, 1/16, 1/64, 1/64, 1/64, 1/64]`tür. Huffman uzunluklarını bul ve `L = H` olduğunu göster.
5. (★★) Düzgün 5 sembollük bir kaynak için Huffman'ın ortalama uzunluğunu ve entropisini hesapla. Fark neden `0`dan büyüktür?
6. (★★) `D_KL(p ‖ q)` ile `D_KL(q ‖ p)` aynı olabilir mi? Bir örnek ver ve neden genel olarak eşit olmadığını açıkla.
7. (★★) Softmax çıktısının tüm logitlere aynı sabit `c` eklenmesiyle değişmediğini kanıtla. Bu özellik log-sum-exp hilesinin temelidir.
8. (★★) Bir ikili sınıflandırıcı, doğru etiket için 0,8 olasılığını vermiş olsun. Çapraz entropi kaybını (nat) hesapla ve bu değerin neden 0,8'e değil `−ln 0,8`e eşit olduğunu açıkla.
9. (★★) Hamming(7,4) kodunda `d = 3` olduğunu elle göster: iki farklı veri sözcüğünün kod sözcükleri arasındaki en küçük mesafeyi bul.
10. (★★★) Tekrar kodunun bit hata oranı `3p² − 2p³`, kodsuz iletiminki `p`dir. `3p² − 2p³ = p` denkleminin `(0, 1)` aralığındaki çözümü nedir ve bu değerin ötesinde tekrar kodu neden kodsuzdan kötüdür?
11. (★★★) Bir kanalın bant genişliği 2 MHz ve SNR 15 dB'dir. Shannon–Hartley kapasitesini hesapla ve bu kanalda 10 Mbit/s hızı ulaşılabilir mi, neden?
12. (★★★) Aritmetik kodlamada bekleyen bit mekanizması neden gereklidir? Aralık orta noktanın iki yanına düşer ama alt ve üst yarılara girmezse, kodlayıcı bu durumda hangi bitleri yazabilir ve neden hemen yazamaz?

### Kod Okuma Egzersizi

Bu bölümde `longest_match` fonksiyonuna bakacağız. Bu fonksiyon, zlib'in DEFLATE sıkıştırıcısının LZ77 aşamasında bir konum için pencerede en uzun eşleşmeyi arar. Kaynak olarak zlib 1.3.1 sürümünün `deflate.c` dosyasını kullandık (`https://raw.githubusercontent.com/madler/zlib/v1.3.1/deflate.c`, 2139 satır). Aşağıdaki kesitler birebir kopyadır; aralarında kalan satırlar atlanmıştır ve her atlamanın yeri belirtilmiştir.

Fonksiyonun başlangıcı, pencere sınırını ve hash zincirini kurar. İlk kesit, pencere sınırının ve hash zincirinin tanımıdır (satır 1355–1361):

```c
    IPos limit = s->strstart > (IPos)MAX_DIST(s) ?
        s->strstart - (IPos)MAX_DIST(s) : NIL;
    /* Stop when cur_match becomes <= limit. To simplify the code,
     * we prevent matches with the string of window index 0.
     */
    Posf *prev = s->prev;
    uInt wmask = s->w_mask;
```

Satır 1348'de fonksiyonun imzası (`local uInt longest_match(deflate_state *s, IPos cur_match) {`) ve yerel değişkenler yer alır; 1349–1354 satırları `chain_length`, `scan`, `match`, `len`, `best_len` ve `nice_match` gibi değişkenleri tanımlar ve bu kesitin dışında kalır. Satır 1363–1374 arasındaki `UNALIGNED_OK` denetimi, karşılaştırmanın iki baytlık mı bayt bayt mı yapılacağını seçer. Satır 1383'te `chain_length >>= 2` bulunur: önceki eşleşme yeterince iyiyse arama zinciri kısaltılır.

İkinci kesit, döngünün `#else` dalındaki karşılaştırma bloğudur. Satır 1393'te başlayan `do` döngüsünün içinde, 1405–1438 arasındaki `UNALIGNED_OK` dalı atlanmış ve 1439'da `#else` dalına geçilmiştir (satır 1439–1444):

```c
#else /* UNALIGNED_OK */

        if (match[best_len]     != scan_end  ||
            match[best_len - 1] != scan_end1 ||
            *match              != *scan     ||
            *++match            != scan[1])      continue;
```

Bu dalda önce dört karşılaştırma yapılır. Bunlar, bir adayın mevcut en iyi eşleşmeden (`best_len`) daha uzun olup olamayacağını hızlıca eler: `match[best_len]` ve `match[best_len − 1]` denetimleri, aday eşleşmenin sondaki baytlarını önce kontrol eder. Satır 1445–1457 açıklama yorumu ve ilk karşılaştırma ilerletmelerini içerir; satır 1458–1463 ise `do { } while` ile sekiz karşılaştırmalık asıl eşleşme ölçümüdür. Bu iki parça atlanmıştır.

Üçüncü kesit, en iyi eşleşmenin güncellenmesi ve döngünün sonucu olan bölümdür (satır 1473–1486). Arada kalan satırlar (1464–1472) ölçümün sonunu ve `UNALIGNED_OK` kapanışını içerir:

```c
        if (len > best_len) {
            s->match_start = cur_match;
            best_len = len;
            if (len >= nice_match) break;
#ifdef UNALIGNED_OK
            scan_end = *(ushf*)(scan + best_len - 1);
#else
            scan_end1  = scan[best_len - 1];
            scan_end   = scan[best_len];
#endif
        }
    } while ((cur_match = prev[cur_match & wmask]) > limit
             && --chain_length != 0);
```

`if (len > best_len)` bloğu yeni eşleşmeyi kaydeder. `nice_match` kontrolü, yeterince uzun bir eşleşme bulunduğunda aramayı erken keser. Döngünün koşulu hem zincirdeki bir sonraki adayın pencere sınırının içinde kalmasını hem de `chain_length` sayacının bitmemiş olmasını denetler.

**Sorular — cevaplamadan geçme:**

1. `longest_match` hangi kısımdır: LZ77 kodlayıcının mı, çözücünün mü? Bu fonksiyon neden çözücüde gerekli değildir?
2. `nice_match` ile erken çıkış, sıkıştırma oranını ve hızı nasıl etkiler? Bu, Bölüm 51.7'de gördüğümüz "en uzun eşleşme" tanımından nasıl sapar?
3. Kesit 1'deki `limit` hesabı, pencereden çok uzakta kalan eşleşmeleri neden dışlar? Bu, `MAX_DIST` sınırıyla nasıl ilişkilidir?
4. Kesit 2'deki dört karşılaştırma, tam eşleşme uzunluğunu hesaplamadan önce neyi eliyor? Bu bir "hızlı reddetme" (fast reject) heuristiğidir; neden doğru sonuçları değiştirmez?
5. `chain_length >>= 2` (satır 1378 civarı, kesitte yok) yapılması neden önceki eşleşme iyiyse arama süresini azaltır? Bu tercih, kompresyon oranı ile hız arasındaki hangi değiş tokuşu yansıtır?
6. Bu fonksiyonun ürettiği eşleşmeler, Bölüm 51.7'deki LZ77 üçlülerine ve Bölüm 51.3'teki entropi sınırına nasıl bağlanır? Eşleşme bulunamayan baytlar sonuçta hangi aşamaya girer?

## Bölüm Özeti

- **Öz bilgi** `I(x) = −log₂ p(x)` bir olayın şaşırmasıdır; birimi bit (ln kullanılırsa nat). Logaritma, bağımsız olayların bilgisinin toplanmasını sağlar.
- **Entropi** `H(X) = ∑ p log₂ (1/p)` bir kaynağın sembol başına ortalama belirsizliğidir; en büyük değeri düzgün dağılımda `log₂ n` alır.
- **Ortak, koşullu entropi ve zincir kuralı** iki değişkenin birlikte belirsizliğini ayrıştırır. **Karşılıklı bilgi** `I(X;Y)` paylaşılan bilgidir, negatif olmaz ve öznitelik seçiminin ölçüsü olarak kullanılır.
- **Kaynak kodlama** teoremi `L ≥ H` sınırını verir; Kraft eşitsizliği öneksiz kodların varlığını sınırlar. Huffman optimal bir öneksiz koddur ama sembol başına en az bir bit kaybeder. **Aritmetik kodlama** bu bir bitlik tabanı kaldırır ve sınıra yaklaşır.
- **LZ77** tekrarları geri gösterimlerle kodlar; **DEFLATE** bunu Huffman ile birleştirir. Rastgele ve şifreli veriler sıkışmaz; bu, güvercin deliği ilkesinin sonucudur.
- **Çapraz entropi** `H(p,q) = H(p) + D_KL(p‖q)` bir yanlış modelin maliyetidir; KL ≥ 0 ve asimetriktir. Sınıflandırmadaki çapraz entropi kaybı, negatif log-olabilirliktir ve softmax ile gradyanı `p − y`dir.
- **Sayısal kararlılık** için log-sum-exp kullanılır; gradyan sayısal olarak denetlenir.
- **Kanal kapasitesi** BSC için `C = 1 − H(p)`, Gauss kanalı için `C = B log₂(1 + S/N)`dir. Veri işleme eşitsizliği bilginin bir kanalda artamayacağını söyler.
- **Hata düzeltme**: tekrar kodu basit ama düşük hızlıdır; Hamming(7,4) `d = 3` ile tek hatayı düzeltir. CRC yalnızca tespit eder; LDPC, turbo, polar ve Reed–Solomon kodları sınıra yaklaşır.
- **Semantik iletişim** bitler yerine görev için gerekli bilgiyi iletmeyi hedefler; ölçü yine karşılıklı bilgidir ama değişken görevdir.

**Kısım XII'nin kapanışı.** Bu bölümle Kısım XII, Matematik, tamamlandı. Bölüm 47'de ayrık matematiği, Bölüm 48'de lineer cebiri, Bölüm 49'da olasılık ve istatistiği, Bölüm 50'de optimizasyonu ve bu bölümde bilgi teorisini gördün. Bu beş bölüm, ML'in dilini oluşturur: vektörler ve matrisler (48), olasılık dağılımları ve en çok olabilirlik (49), gradyan inişi (50) ve kayıp fonksiyonlarının bilgi teorisi kökeni (51). Bu bölümde çapraz entropi ve KL gibi sınıflandırma ve üretici modellerdeki kayıpların bilgi teorisi kökenini gördün; eğitimin ise veri ve model dağılımı arasındaki ıraksamayı küçülttüğünü anladın. MSE gibi kayıpların olasılıksal yorumu ise Gauss varsayımından gelir.

**Sonraki bölümde:** Bölüm 52, DSP Temelleri ile Kısım XIII'e (Sinyal ve Paralel) başlıyor. Bu bölümde kanal üzerinden gelen analog sinyali örnekleyip dijitale çevirmeyi, Nyquist sınırını ve filtrelemeyi göreceksin. Bu bölümdeki Shannon–Hartley'deki `B` ve `S/N` kavramları, DSP'de örnekleme hızı ve kuantizasyon gürültüsü olarak yeniden karşına çıkacak.

::: mulakat
1. Huffman kodu neden optimaldir ve neden bir sembol başına en az bir bit harcar? Aritmetik kodlama bu kısıtı nasıl aşar?
2. Çapraz entropi kaybı neden sınıflandırmada MSE yerine kullanılır? Bu seçimi olabilirlik ilkesi ile açıklar mısın?
3. KL ıraksamasının simetrik olmamasının pratik sonuçları nelerdir? Forward ve reverse KL'nin model davranışını nasıl değiştirdiğini anlat.
4. Softmax ve çapraz entropi birlikte kullanıldığında gradyan neden `p − y` olur? Bu sadeliğin sinir ağı eğitimi için önemi nedir?
5. Bir sıkıştırıcı hem rastgele veriyi hem de şifreli veriyi küçültebilir mi? Güvercin deliği ilkesiyle neden hayır, açıkla.
6. Shannon–Hartley formülünde bant genişliği ile sinyal gücünü artırmanın kapasiteye etkisi neden farklıdır? Bir İHA veri bağı tasarlarken bu farkı nasıl kullanırsın?
7. Karşılıklı bilgi bir öznitelik seçiminde korelasyondan neden daha genel bir ölçüttür? Hangi durumda ikisi de yanıltabilir?
8. Hamming(7,4) neden tek hatayı düzeltebilir ama iki hatayı düzeltemez? Mesafe kavramıyla açıkla.
