%% kisim_no: XII
%% kisim_ad: Matematik
%% bolum_no: 49
%% baslik: Olasılık & İstatistik

## Giriş: Belirsizlik bir hata değil, bir veri türüdür

Bir İHA'nın kamerası karşıdaki aracı gördüğünü söylüyor. Ama bu gerçekten bir tanker mi, yoksa yağmurda bir kaya mı? Sensör ölçümü her zaman gürültülüdür; GPS konumu birkaç metre oynar, bir ADC okuması birkaç birim titrer, bir ağ isteği bazen 12 milisaniye, bazen 900 milisaniye sürer. Mühendislik bu belirsizlikle başlar. Soru "belirsizlik var mı?" değil, "bu belirsizlikle ne kadar emin olabilirim?" sorusudur.

Olasılık, belirsizliği hesaplanabilir bir dille anlatır. İstatistik ise tersini yapar: elindeki sınırlı veriden, arkasındaki bilinmeyen düzeni geri kazanmaya çalışır. Bu iki alan olmadan makine öğrenmesi yoktur. Bir sınıflandırıcının çıktısı, aslında "bu görüntünün tank olma olasılığı 0,93" gibi bir olasılık dağılımıdır. Bir kayıp fonksiyonunun çoğu, bir olasılık modelinin negatif log-olabilirliğidir (Bölüm 51 ve 57'de bu bağlantıyı açacağız). Eğitimde gördüğün "ortalama kayıp" da bir örnek ortalamasıdır ve kendi belirsizliği vardır.

Mühendislik tarafında da aynı sorular çıkar. Bölüm 41'de p99 gecikmesini ölçtük; bir yük dengeleme politikasının p99'u diğerinden küçük çıkarsa, bu fark gerçek mi yoksa tek bir koşunun şansı mı? Bölüm 39'daki kararsız testler de aynı sorudur: bir test %2 olasılıkla kalıyorsa, bunu kaç koşuda ayırt edebilirsin? Bölüm 35'teki Bloom filtresinin "muhtemelen var" cevabı ve quorum okumasındaki bayat veri olasılığı da bu dilin uygulamalarıdır. Savunma sanayiinde ise taban oranı yanılgısı hayati bir tuzaktır: çok seyrek bir hedefi tespit eden bir alarmın yüzde 95 doğru olması, alarmın gerçek bir tehdit olduğu anlamına gelmez.

Bu bölümde sıfırdan başlayacağız. Önce olasılığın temel kuralları, sonra Bayes teoremi ve rastgele değişkenler, ardından büyük sayılar ve merkezi limit teoremi. Kestirim (MLE, MAP), güven aralığı, bootstrap ve hipotez testi bu temelin üzerine kurulur. Her kavramı üç biçimde göstereceğiz: sezgi, formül ve simülasyon. Simülasyon, formülün doğru olup olmadığını sınamanın en dürüst yoludur; sabit tohumla yazdığımız her betik aynı sonucu verir ve sen de kendi makinende aynı sayıları görebilirsin.

::: not
Olasılık bize "ne olabilir?" sorusunu, istatistik "veri bize ne söylüyor?" sorusunu sorar. İkisini karıştırmak, bu bölümdeki en yaygın hatanın kaynağıdır: bir p-değerini "hipotezin doğruluk olasılığı" sanmak ya da bir örnek ortalamasını "gerçek ortalama" sanmak.
:::

## 49.1 Örnek uzayı, olaylar ve olasılık aksiyomları

Bir deneyin olası bütün sonuçlarının kümesine **örnek uzayı** (sample space) denir ve Ω ile gösterilir. Bir zar atışında Ω = {1, 2, 3, 4, 5, 6}'dır. Örnek uzayın bir alt kümesine **olay** (event) denir: "çift gelmesi" olayı A = {2, 4, 6}'dır. Olayları küme işlemleriyle birleştirebiliriz: A ∪ B (en az biri olur), A ∩ B (ikisi de olur), A′ (A olmaz, tümleyen).

Bir olaya bir sayı atayan fonksiyona **olasılık** (probability) denir ve P ile gösterilir. Modern olasılık, Kolmogorov'un 1933'te yazdığı üç aksiyomla kurulur:

- P(A) ≥ 0 her olay için.
- P(Ω) = 1.
- A ve B ayrık olaylarsa (A ∩ B = boş küme), P(A ∪ B) = P(A) + P(B).

Bu üç kuraldan geri kalan her şey çıkar. Örneğin P(A′) = 1 − P(A) olduğunu görmek için, A ile A′ ayrıktır ve birleşimleri Ω'dır; bu yüzden P(A) + P(A′) = 1'dir. Aynı şekilde P(boş küme) = 0 ve her olay için 0 ≤ P(A) ≤ 1 yazılabilir.

Sayma yaparak olasılık hesaplarken her sonucun eşit olasılıklı olduğu durumda P(A) = |A| / |Ω| kullanılır. İki zar atışında toplamın 7 olma olasılığı, 36 eşit olası sonuçtan 6 tanesinin toplamı 7 yapmasıyla 6/36 = 1/6 olur. Bu sayımın nasıl yapıldığı Bölüm 47'de (ayrık matematik) anlatılıyor; burada bunu kullanacağız.

Olasılığın bir ikinci yorumu da **sıklık** (frequentist) yorumudur: bir olayın olasılığı, deney çok kez tekrarlandığında o olayın göreli sıklığının yaklaştığı değerdir. Bu yorum büyük sayılar yasasıyla (49.6) doğrulanır. Mühendislikte iki yorumu da kullanırız: bir zarın adil olduğunu sıklıkla sınarız, bir İHA'nın bu görevde başarısız olma olasılığını ise çoğu zaman bir inanç olarak tahmin ederiz. Bayesçi yorum bu inancı veriyle güncellemeye izin verir (49.8).

| Kavram | Matematik | Mühendislik örneği |
|---|---|---|
| Örnek uzayı | Ω | Bir paketin olası iletim sonuçları: alındı, kayıp, bozuk |
| Olay | A ⊆ Ω | "Paket 3 saniyeden geç geldi" |
| Tümleyen | A′ | "Paket zamanında geldi" |
| Ayrık olaylar | A ∩ B = boş küme | "Aynı anda hem ARM hem x86 hedefi" (iki ayrı durum) |
| Olasılık | P(A) ∈ [0, 1] | Yıllık arıza olasılığı 0,002 |

## 49.2 Koşullu olasılık, bağımsızlık ve Bayes teoremi

Bazen bir olayın olasılığını, başka bir şeyi bildikten sonra yeniden hesaplamak isteriz. Bir paketin kayıp olma olasılığı genelde %3 olabilir; ama paketin bir yönlendiricide zaten 2 kez tekrarlandığını bilirsek, bu olasılık değişir. Bu yeni olasılığa **koşullu olasılık** denir:

P(A | B) = P(A ∩ B) / P(B), P(B) > 0.

Okunuşu "B olduğu bilindiğinde A'nın olasılığı"dır. Formülün sezgisi basittir: B'nin gerçekleştiği dünyaya bakıyoruz, o dünyada A ile birlikte olanların oranını alıyoruz. Bu bir **pay ve payda** işlemidir: payda, yeni evrenin büyüklüğüdür; pay, o evrenin içinde A'nın da olduğu kısımdır.

Buradan **bağımsızlık** tanımı çıkar. A ve B bağımsızsa, B'yi bilmek A'nın olasılığını değiştirmez: P(A | B) = P(A), dolayısıyla P(A ∩ B) = P(A) · P(B). İki zarın birinci zarının çift olması (A) ile toplamın 7 olması (B) bağımsız olaylardır: P(A) = 1/2, P(B) = 1/6 ve P(A ∩ B) = 3/36 = 1/12 = (1/2) · (1/6). Bu sayımı aşağıdaki programla tam olarak doğruladık.

**Toplam olasılık.** B olayını, birbirini dışlayan ve tüm Ω'yı dolduran A ve A′ durumlarına ayırabiliriz. O zaman P(B) = P(B | A) · P(A) + P(B | A′) · P(A′) olur. Bu, bir olayın olasılığını koşullu parçalarına ayırarak hesaplama tekniğidir. Bayes teoremi bu toplamı payda olarak kullanır.

**Bayes teoremi.** Koşullu tanımdan iki yönü yazarsak P(A ∩ B) = P(B | A) P(A) = P(A | B) P(B) elde ederiz. İkisini eşitleyip P(B)'ye bölersek:

P(A | B) = P(B | A) · P(A) / P(B).

Bu formülün gücü, koşulları ters çevirmesidir. Mühendis genelde "gerçek tehdit varken alarm verme olasılığı nedir?" sorusunu sorabilir; yani P(alarm | tehdit) bilinir. Ama asıl merak ettiği, "alarm verildiğinde gerçek tehdit olma olasılığı" yani P(tehdit | alarm) değeridir. Bayes teoremi bu iki yönü birbirine bağlar. Payda ise toplam olasılıkla hesaplanır: P(alarm) = P(alarm | tehdit) P(tehdit) + P(alarm | yok) P(yok).

### Taban oranı yanılgısı

Taban oranı (base rate), bir olayın genel sıklığıdır: nadir bir hastalığın nüfustaki oranı, nadir bir hedefin uçuş alanındaki oranı. İnsanlar bu oranı çoğu zaman görmezden gelir ve yalnızca testin doğruluğuna bakar. Bu hataya **taban oranı yanılgısı** denir ve test sonuçlarını yorumlarken en pahalı hatalardan biridir.

Bir örnek alalım. Bir hastalığın nüfustaki oranı 1/1000 olsun. Testin duyarlılığı (hastayı yakalama olasılığı) 0,99, özgüllüğü (sağlıklıyı doğru eleme olasılığı) 0,95 olsun. Bir kişinin testi pozitif çıktığında hasta olma olasılığı nedir? Bölüm 5'teki yaklaşımla önce sayıları kağıda döküp bakalım: 1000 kişiden biri hasta; onun testi %99 ihtimalle pozitif. Geri kalan 999 sağlıklıdan %5'i yanlış pozitif verir, yani yaklaşık 50 kişi. Pozitif çıkanlar yaklaşık 1 + 50 = 51 kişi; bunların içinde gerçekten hasta olan 1 kişi. Yani pozitif bir sonucun hasta olma olasılığı yaklaşık 1/51 ≈ %2'dir. Formül aynı sonucu verir:

P(H | +) = (0,99 · 0,001) / (0,99 · 0,001 + 0,05 · 0,999) = 0,00099 / 0,05094 ≈ 0,0194.

Bu sonucu programla hem formülle hem de bir milyon kişilik rastgele bir simülasyonla doğruladık, aşağıdaki programın ilk kısmında.

### Savunma örneği: İHA hedef tanıma alarmı

Bir İHA'nın görüntü işleme modülü, gözlenen her olay için "tehdit" ya da "değil" kararı verir. Diyelim ki 10 000 olayın 200'ü gerçek bir tehdit (%2) ve alarm mekanizması şöyle çalışıyor: gerçek tehditlerin %95'inde alarm verilir; tehdit olmayanların ise %3'ünde yanlış alarm verilir. Bir alarm verildiğinde, bunun gerçek bir tehdit olma olasılığı nedir?

Bayes teoremiyle hesap, ama önce sayılarla bakalım (Şekil 49.1). Gerçek tehditlerin 190'ı yakalanır. Tehdit olmayan 9 800 olayın %3'ü, yani 294 tanesi yanlış alarm verir. Toplam alarm sayısı 190 + 294 = 484'tür ve bunların yalnızca 190'ı gerçektir:

P(tehdit | alarm) = 190 / 484 ≈ 0,39.

Yani "alarmın %95 doğru olduğu" bir sistemde, alarmın gerçek tehdit olma olasılığı yalnızca %39'dur. Geri kalan %61 yanlış alarmdır. Bu sayıyı yalnızca tehdit oranı %2 olduğu için alabiliyoruz; tehdit oranı %0,1 olsaydı, aynı sistem için alarmın gerçek olma olasılığı çok daha düşük çıkardı. Bu yüzden savunma sistemlerinde alarm eşiği ve taban oranı birlikte tasarlanır.

Aşağıdaki program dört şeyi yapar: hastalık örneğini formülle ve simülasyonla hesaplar, İHA alarmını hesaplar, Monty Hall'u simüle eder ve zar bağımsızlığını tam sayımla doğrular. Önce hastalık örneğinin fonksiyonlarını okuyalım. Simülasyon her kişi için bir rastgele sayı üretip hastalık ve test durumunu belirliyor; pozitif çıkanların içinde hasta olanların oranını sayıyor. Sayılar birbirine yakındır; küçük farkın nedeni rastgeleliktir ve kişi sayısı arttıkça kapanır.

```python
def bayes_pozitif(pH, duyarlilik, ozgulluk):
    """P(H | +) ve P(+) hesabi; toplam olasilik kullanilir."""
    p_pozitif = duyarlilik * pH + (1 - ozgulluk) * (1 - pH)
    return duyarlilik * pH / p_pozitif, p_pozitif
```

Birinci fonksiyon, toplam olasılıkla P(+)'ı hesaplar ve Bayes formülünü uygular. İkinci fonksiyon aynı mantığı bir simülasyonla yapar: her kişi için bağımsız iki rastgele sayı üretilir; hasta olup olmadığı ve testin ne çıktığı bu sayılardan belirlenir.

```python
def hastalik_frekans(n=1_000_000, seed=49):
    """n kisi uret; pozitifleri ve gercek hastalari say."""
    rnd = random.Random(seed)
    poz = hasta_poz = 0
    for _ in range(n):
        hasta = rnd.random() < 0.001
        if hasta:
            test_poz = rnd.random() < 0.99
        else:
            test_poz = rnd.random() < 0.05
        if test_poz:
            poz += 1
            if hasta:
                hasta_poz += 1
    return hasta_poz / poz
```

### Monty Hall: sezgiye aykırı bir koşullu olasılık

Bir yarışmada üç kapıdan birinin arkasında araba, diğer ikisinin arkasında keçi vardır. Sen bir kapı seçersin. Yarışma sunucusu, seçmediğin ve arkasında araba olmayan bir kapıyı açar ve sana şunu sorar: "Seçimini değiştirmek ister misin?" Değiştirmek mi, yoksa kalmak mı daha iyi?

Sezgi "fark etmez, ikisi de yarı yarıya" der. Ama sayılar farklıdır. İlk seçimin doğru olma olasılığı 1/3'tür; yani seçtiğin kapının arabayı tutma olasılığı 1/3, diğer ikisinin toplamı ise 2/3'tür. Sunucu, arabanın olmadığı kapılardan birini açarak o 2/3 kütleyi değiştirmeden yalnızca diğer kapıya aktarır. Değiştirmek, kazanma olasılığını 2/3'e çıkarır.

Bu hesabı simülasyonla kontrol etmek kolaydır: her denemede arabayı ve seçimi rastgele yerleştir, sunucunun açtığı kapıyı belirle ve iki stratejinin kazanma oranlarını say. Bu programın ikinci fonksiyonu tam bunu yapar.

```python
def monty_hall(n=100_000, seed=49):
    """Kapi degistir / degistirme stratejilerinin kazanma oranlari."""
    rnd = random.Random(seed)
    degistir = koru = 0
    for _ in range(n):
        odul = rnd.randrange(3)
        secim = rnd.randrange(3)
        # Sunucu, ne secilen ne de odul olan bir kapiyi acar.
        acilan = next(k for k in range(3) if k != secim and k != odul)
        yeni = next(k for k in range(3) if k != secim and k != acilan)
        degistir += yeni == odul
        koru += secim == odul
    return koru / n, degistir / n
```

Bağımsızlık kontrolü, zar örneğini tam sayımla yapar. Kesirler Python'un Fraction türünde tutulduğu için sonuç yuvarlama hatası içermez; P(A ∩ B) ile P(A) · P(B) tam olarak eşit çıkar.

```python
def bagimsizlik_kontrol():
    """Iki zar: A = ilk zar cift, B = toplam 7. Tam sayim."""
    uzay = list(product(range(1, 7), repeat=2))
    a = [w for w in uzay if w[0] % 2 == 0]
    b = [w for w in uzay if w[0] + w[1] == 7]
    ab = [w for w in a if w in b]
    p = lambda k: Fraction(len(k), len(uzay))
    return p(a), p(b), p(ab), p(a) * p(b)
```

Ana fonksiyon, üç bölümü çalıştırır ve sonuçları yazdırır:

```python
def main():
    pH = 0.001
    p, pp = bayes_pozitif(pH, 0.99, 0.95)
    print("Hastalik: P(H|+) = %.4f  P(+) = %.5f" % (p, pp))
    print("Simulasyon (1 000 000 kisi): %.4f" % hastalik_frekans())

    # Iha hedef tanima: 10 000 olay, 200 gercek tehdit.
    p, pp = bayes_pozitif(0.02, 0.95, 0.97)
    print(
        "IHA alarm: P(tehdit|alarm) = %.4f  P(alarm) = %.4f" % (p, pp)
    )

    k, d = monty_hall()
    print(
        "Monty Hall (100 000 deneme): koru=%.4f degistir=%.4f"
        % (k, d)
    )

    pa, pb, pab, prod = bagimsizlik_kontrol()
    print("P(A)=%s P(B)=%s P(A n B)=%s" % (pa, pb, pab))
    print("P(A) P(B) = %s -> bagimsiz: %s" % (prod, pab == prod))


if __name__ == "__main__":
    main()
```

Bu betiğin çıktısı şöyledir: Bayes hesabı, bir milyon kişilik simülasyon, İHA alarmı, Monty Hall ve zar bağımsızlığı.

```term
$ python b49_a_olasilik.py
Hastalik: P(H|+) = 0.0194  P(+) = 0.05094
Simulasyon (1 000 000 kisi): 0.0198
IHA alarm: P(tehdit|alarm) = 0.3926  P(alarm) = 0.0484
Monty Hall (100 000 deneme): koru=0.3328 degistir=0.6672
P(A)=1/2 P(B)=1/6 P(A n B)=1/12
P(A) P(B) = 1/12 -> bagimsiz: True
```

![Şekil 49.1: Frekans ağacı. 10 000 olaydan 200 gerçek tehdit var; alarmların 190'ı gerçek, 294'ü yanlıştır. P(tehdit | alarm) = 190 / 484.](gorseller/b49_bayes_agac.png)

Şekil 49.1, İHA örneğini frekans ağacı olarak gösterir. Bu yöntem Bayes teoremini formül yazmadan kavramanın en sağlam yoludur: her dalın sayısı bir olay sayısıdır ve koşullu olasılık, bir alt dalın üst dala oranıdır. Mülakatta ve projede Bayes sorusu çıktığında, önce bu ağacı çizmeni öneririm.

Bu bölümde gördüğün her Bayes hesabı aynı kalıbı izler. Önce tabloyu ya da ağacı çiz, sonra payda olan toplam olasılığı yaz, en son oranı al. Bu kalıp Bölüm 62'de Naive Bayes sınıflandırıcısına, Bayes ağlarına ve gizli Markov modellerine olduğu gibi taşınacak.

## 49.3 Rastgele değişkenler: kesikli dağılımlar

Bir deneyin sonucunu bir sayıya çevirdiğimizde **rastgele değişken** (random variable) elde ederiz. X, bir paketin kaç kez tekrarlandığını ya da bir saatte kaç arıza olduğunu tutan bir fonksiyondur. Değerleri sayılabilir bir kümedeyse X **kesiklidir**. Her k değeri için P(X = k) olasılığına **kütle fonksiyonu** (probability mass function, PMF) denir. PMF'in iki kuralı vardır: her değer için P(X = k) ≥ 0 ve tüm değerler üzerinden toplamı 1'dir.

Mühendislikte dört kesikli dağılım yeterlidir ve hepsi bir "deney" modelinden doğar:

- **Bernoulli(p):** tek bir deneme, başarı olasılığı p. Bir paketin ya kayıp ya da kayıp olmadığı en basit durumdur. E[X] = p, Var(X) = p(1 − p).
- **Binom(n, p):** n bağımsız Bernoulli denemesinde kaç başarı olduğu. Formülü P(X = k) = C(n, k) p^k (1 − p)^(n−k)'dır; C(n, k), Bölüm 47'de anlatılan kombinasyon sayısıdır. E[X] = np, Var(X) = np(1 − p).
- **Geometrik(p):** ilk başarıya kadar kaç deneme yapıldığı. P(X = k) = (1 − p)^(k−1) p. E[X] = 1/p. Bir sinyal paketinin yeniden iletim sayısını modellemek için kullanılır.
- **Poisson(λ):** sabit bir zaman ya da alan içinde kaç olay olduğu, olayların birbirinden bağımsız ve ortalama oranının λ olduğu durumda. P(X = k) = e^(−λ) λ^k / k! ve E[X] = Var(X) = λ. Bir saatte gelen paket kaybı, bir sensör hattında biten bit sayısı gibi olaylar Poisson ile modellenir. Binom(n, p) için n büyük, p küçük ve np = λ ise Poisson'a yaklaşır (genel bilgi).

Şekil 49.2 üç dağılımın PMF'ini gösterir. Binom(20; 0,05) sol üstte: 20 paketin çoğu sağlam, kayıp sayısı genelde 0 ya da 1. Poisson(3) sağ üstte: saatte ortalama 3 kayıp, en olası değerler 2 ve 3. Geometrik sol altta: ilk başarı genelde erken gelir ama uzun kuyruğu vardır. Binom(20; 0,5) sağ altta simetrik ve tepesi 10'dadır; karşılaştırma için konuldu.

![Şekil 49.2: Kesikli dağılımlar. Binom(20; 0,05) paket kaybı, Poisson(3) saatlik kayıp, Geometrik(0,1) ilk başarıya kadar deneme, Binom(20; 0,5) simetrik karşılaştırma.](gorseller/b49_kesikli.png)

Paket kaybı örneğiyle bu dağılımları sayılarla görelim. 20 paketlik bir mesajda her paketin %5 olasılıkla kaybolduğunu varsayalım. Kaç paket kaybolmasını bekleriz? Binom(20; 0,05) için E[X] = 20 · 0,05 = 1'dir. Hiç kayıp olmama olasılığı 0,95^20 ≈ 0,3585'tir; en az iki kayıp olma olasılığı ise yaklaşık 0,264'tür. Aynı hatlar saatte ortalama 3 kayıp veriyorsa, Poisson(3) ile bir saatte en az 5 kayıp olma olasılığı yaklaşık 0,185'tir. Bu iki hesabı ve geometrik dağılımın beklenen değerini aşağıdaki betiğin ilk kısmı yapar. Sonuçları scipy kütüphanesinin kendi fonksiyonlarıyla da karşılaştırdık; kendi yazdığımız formül ile kütüphane aynı sayıyı veriyorsa formülü doğru yazmışız demektir.

```python
import math
import random

from scipy import stats


def binom_pmf(n, p, k):
    return math.comb(n, k) * p**k * (1 - p) ** (n - k)
```

```python
def poisson_pmf(lam, k):
    return math.exp(-lam) * lam**k / math.factorial(k)


def paket_kaybi():
    # 20 paket, her biri %5 olasilikla kayboluyor (binom).
    p0 = binom_pmf(20, 0.05, 0)
    p1 = binom_pmf(20, 0.05, 1)
    print(
        "Binom(20, 0.05): P(0)=%.4f P(1)=%.4f P(>=2)=%.4f"
        % (p0, p1, 1 - p0 - p1)
    )
    print(
        "  scipy: P(0)=%.4f P(>=2)=%.4f"
        % (stats.binom.pmf(0, 20, 0.05), stats.binom.sf(1, 20, 0.05))
    )
    # Saatte ortalama 3 kayip (Poisson).
    lam = 3.0
    p_ge5 = 1 - sum(poisson_pmf(lam, k) for k in range(5))
    print(
        "Poisson(3): P(0)=%.4f P(>=5)=%.4f"
        % (poisson_pmf(lam, 0), p_ge5)
    )
    print("  scipy: P(>=5)=%.4f" % stats.poisson.sf(4, lam))
```

```python
def geometrik():
    # Basari olasiligi p=0.1; ilk basariya kadar deneme sayisi.
    p = 0.1
    print(
        "Geometrik(0.1): P(X=1)=%.3f P(X=10)=%.5f E[X]=%.1f"
        % (p, (1 - p) ** 9 * p, 1 / p)
    )
    print("  scipy E=%.1f" % stats.geom.mean(p))
```

Bu betikte `math.comb` binom katsayısını, `math.factorial` Poisson'daki k! değerini verir. Kesir hesabı tamsayı ve kayan nokta karışımıdır; 0,95^20 gibi küçük olasılıklarda kayan nokta hatası ihmal edilebilir düzeydedir.

## 49.4 Sürekli rastgele değişkenler: PDF, CDF ve belleksizlik

Bir arızanın kaç saat sonra olacağı ya da bir sensörün ölçtüğü gerilim kesikli değildir; sürekli bir değer alır. Sürekli bir X için tek bir değerin olasılığı sıfırdır: P(X = 2,000...) = 0. Bu yüzden olasılığı bir aralıkta tanımlarız ve **olasılık yoğunluk fonksiyonu** (probability density function, PDF) f(x) ile çalışırız. P(a ≤ X ≤ b) değeri, f'nin a'dan b'ye kadar integralidir:

P(a ≤ X ≤ b) = ∫ f(x) dx (a'dan b'ye).

f'nin tüm R üzerindeki integrali 1 olmalı ve f negatif olmamalıdır. **Birikimli dağılım fonksiyonu** (cumulative distribution function, CDF) F(x) = P(X ≤ x), kesikli durumdaki toplamın sürekli karşılığıdır. F, sıfırdan bire monoton olarak artar ve f = F′ ilişkisiyle f'den türetilir.

Üç sürekli dağılım mühendislikte çok sık görünür:

- **Düzgün U(a, b):** aralık içinde her değer eşit olası. f(x) = 1/(b − a), E[X] = (a + b)/2. Bir kuantizasyon hatasının dağılımı yaklaşık düzgündür (Bölüm 52'de sayısal işlemede göreceksin).
- **Üstel(λ):** iki arıza arasındaki süre gibi "bekleme süreleri". f(x) = λ e^(−λx), F(x) = 1 − e^(−λx), E[X] = 1/λ ve Var(X) = 1/λ². Üstel dağılım, Poisson sürecinin bekleme süresidir: olaylar Poisson(λ) ile gelirse, iki olay arasındaki süre Üstel(λ)'dır.
- **Normal N(μ, σ²):** çok sayıda küçük ve bağımsız etkinin toplamı. f(x) = (1 / (σ√(2π))) e^(−(x − μ)² / (2σ²)). E[X] = μ, Var(X) = σ². Bu dağılımın neden her yerde ortaya çıktığını 49.6'da merkezi limit teoremi ile göreceğiz.

**Belleksizlik.** Üstel dağılımın en önemli özelliği belleksizliktir: P(T > s + t | T > s) = P(T > t). Bunun anlamı, bir sensörün 3 saattir çalışıyor olması, onun önümüzdeki 2 saat içinde arızalanma olasılığını değiştirmez. Formülle görelim. P(T > s + t | T > s) = P(T > s + t) / P(T > s) = e^(−λ(s+t)) / e^(−λs) = e^(−λt) = P(T > t). Yani "eskimiyor". Bu varsayım, arıza modelleri için her zaman gerçekçi değildir (aşınma söz konusuysa eskir); ama bir ölçüm aracı, rastgele bir gecikme ya da bir gelen istek akışı için doğru bir ilk model olabilir.

Şekil 49.3, üstel ve normal dağılımların PDF ve CDF eğrilerini gösterir. Üstel için f(0) = λ ile başlayıp hızla düşer; F, 1'e doğru yaklaşırken eğrisi yatıklaşır. Normal için f simetriktir ve F ortada 0,5'ten geçer.

![Şekil 49.3: Sürekli dağılımlar. Üstel(0,5) yoğunluk ve birikimli fonksiyonu (üst), Normal(0,1) yoğunluk ve birikimli fonksiyonu (alt).](gorseller/b49_surekli.png)

Aşağıdaki betiğin ikinci bölümü, belleksizliği bir milyon örnekle simüle eder. Bir sürecin 3 saat sonra hâlâ ayakta olduğu koşulda, 5 saatten sonra da ayakta kalma olasılığı, 2 saatlik bir yaşam olasılığına eşit çıkmalıdır. Normal kuralını da simülasyonla doğruluyoruz: ortalamadan 1, 2 ve 3 standart sapma uzaklıktaki olasılık (simülasyonda 0,6828, 0,9546 ve 0,9973) kesin değerler olan 0,6827, 0,9545 ve 0,9973'e yakındır.

```python
def ustel_belleksizlik(n=1_000_000, seed=49):
    """Arizalar arasi sure ~ Ustel(lambda=0.5 / saat)."""
    lam = 0.5
    rnd = random.Random(seed)
    sure = [rnd.expovariate(lam) for _ in range(n)]
    kosul = [t for t in sure if t > 3.0]
    ust = sum(1 for t in kosul if t > 5.0) / len(kosul)
    print(
        "Ustel(0.5): P(T>2)=%.4f (teorik %.4f)"
        % (sum(t > 2 for t in sure) / n, math.exp(-lam * 2))
    )
    print(
        "P(T>5 | T>3) = %.4f  (P(T>2) = %.4f): belleksiz"
        % (ust, math.exp(-lam * 2))
    )
```

```python
def normal_kurali(n=1_000_000, seed=49):
    rnd = random.Random(seed)
    x = [rnd.gauss(0.0, 1.0) for _ in range(n)]
    for k in (1, 2, 3):
        oran = sum(abs(t) <= k for t in x) / n
        print(
            "P(|Z| <= %d) = %.4f  scipy: %.4f"
            % (k, oran, stats.norm.cdf(k) - stats.norm.cdf(-k))
        )
```

Sapka problemi, beklenen değer bölümünde (49.5) kullanacağımız bir örnektir; burada yalnızca sayısal bir kontrol olarak yer alır. Betiğin ana fonksiyonu ve son çıktı şöyledir:

```python
def sabit_nokta(n=10, deneme=200_000, seed=49):
    """Sapka problemi: beklenen dogru eslesme sayisi (sabit nokta)."""
    rnd = random.Random(seed)
    toplam = 0
    sifir = 0
    for _ in range(deneme):
        p = list(range(n))
        rnd.shuffle(p)
        s = sum(1 for i, v in enumerate(p) if i == v)
        toplam += s
        sifir += s == 0
    return toplam / deneme, sifir / deneme
```

```python
def main():
    paket_kaybi()
    geometrik()
    ustel_belleksizlik()
    normal_kurali()
    ort, d = sabit_nokta()
    print(
        "Sapka (n=10): ortalama eslesme=%.4f  hic eslesmeme=%.4f"
        % (ort, d)
    )
    print("  1/e = %.4f" % (1 / math.e))


if __name__ == "__main__":
    main()
```

```term
$ python b49_b_dagilim.py
Binom(20, 0.05): P(0)=0.3585 P(1)=0.3774 P(>=2)=0.2642
  scipy: P(0)=0.3585 P(>=2)=0.2642
Poisson(3): P(0)=0.0498 P(>=5)=0.1847
  scipy: P(>=5)=0.1847
Geometrik(0.1): P(X=1)=0.100 P(X=10)=0.03874 E[X]=10.0
  scipy E=10.0
Ustel(0.5): P(T>2)=0.3673 (teorik 0.3679)
P(T>5 | T>3) = 0.3679  (P(T>2) = 0.3679): belleksiz
P(|Z| <= 1) = 0.6828  scipy: 0.6827
P(|Z| <= 2) = 0.9546  scipy: 0.9545
P(|Z| <= 3) = 0.9973  scipy: 0.9973
Sapka (n=10): ortalama eslesme=1.0002  hic eslesmeme=0.3680
  1/e = 0.3679
```

Çıktıdaki sayılar iki yönlü okunmalıdır. Simüle edilen olasılık ile teorik değer yan yana geldiğinde farklar, örnek sayısının kareköküyle ters orantılı olarak küçülür (49.6'da bu hata ölçülecek). Belleksizlik satırında simüle edilen P(T > 5 | T > 3) ile P(T > 2) değerleri aynıdır; bu, teorideki eşitliğin bir ölçümüdür. Sapka satırındaki 1,0002 ile 1/e ≈ 0,3679 karşılaştırması ise 49.5'te beklenen değer ve sabit nokta düşüncesine bağlanacaktır.

## 49.5 Beklenen değer, varyans, kovaryans ve korelasyon

Bir rastgele değişkenin "ortalama değeri" beklenen değerdir (expected value):

E[X] = ∑ x · P(X = x) (kesikli), E[X] = ∫ x f(x) dx (sürekli).

Beklenen değer, olasılık ağırlıklı bir ortalamadır. Bir zarın beklenen değeri (1 + 2 + ... + 6) / 6 = 3,5'tir; bu, zarın 3,5 gelmesi demek değildir, uzun vadeli ortalamanın bu sayıya yaklaşmasıdır (49.6'da bunu büyük sayılar yasasıyla göreceğiz).

Beklenen değerin en güçlü özelliği **doğrusallıktır**: E[aX + bY] = aE[X] + bE[Y]. Bu kural X ile Y'nin bağımsız olup olmadığına bakmaz. Bu yüzden karmaşık bir sayımı, her biri basit bir **gösterge değişkeni** (indicator variable) olan parçaların toplamına bölebiliriz. I_i, i. olay gerçekleşirse 1, gerçekleşmezse 0 değerini alan bir değişkense, E[I_i] = P(olay i) olur ve toplamın beklenen değeri parçaların beklenenlerinin toplamıdır.

Bu tekniğin en klasik örneği **şapka problemidir**. n kişi şapkalarını bir torbaya atar ve her biri rastgele bir şapka çeker. Kaç kişi kendi şapkasını bulur? S = ∑ I_i yazalım; her i için P(I_i = 1) = 1/n olduğundan E[S] = n · (1/n) = 1 çıkar. Bu sonuç n'den bağımsızdır ve I_i'ler birbirine bağımlı olsa da geçerlidir. Bu arada hiç kimsenin kendi şapkasını bulmama olasılığı (düzensizlik, derangement) n büyüdükçe 1/e ≈ 0,3679'a yaklaşır (genel bilgi).

**Varyans** ve standart sapma, değişkenin ortalamadan ne kadar saçıldığını ölçer:

Var(X) = E[(X − μ)²] = E[X²] − μ², σ = √Var(X), μ = E[X].

Varyans, karelerle çalıştığı için birimi karedir; standart sapma ise aynı birimdedir. Bir İHA'nın GPS hatasının standart sapması 2 metre ise, hatanın 4 metreden büyük olma olasılığı için bunu normal dağılımla bağlayabiliriz (49.4).

**Kovaryans** iki değişkenin birlikte nasıl hareket ettiğini ölçer:

Cov(X, Y) = E[(X − μx)(Y − μy)] = E[XY] − μx μy.

Pozitif kovaryans, X büyüdükçe Y'nin de büyümeye eğilimli olduğunu; negatif kovaryans ters yönü gösterir. Bu değerin birimi X ve Y'nin birimlerinin çarpımıdır, bu yüzden karşılaştırmak zordur. **Korelasyon** bunu birimsiz bir ölçeğe çevirir:

ρ = Cov(X, Y) / (σx σy), −1 ≤ ρ ≤ 1.

ρ = ±1 değerleri, X ile Y arasında mükemmel doğrusal bir ilişki olduğunu gösterir. ρ = 0 ise yalnızca doğrusal bir ilişki olmadığını söyler; aralarında karesel ya da başka bir ilişki olabilir. Bu ayrım önemlidir ve Anscombe örneğiyle gösterilir.

**Korelasyon nedensellik değildir.** Bir yaz günü dondurma satışı ile boğulma vakaları birlikte artar; ama dondurma boğulmaya neden olmaz. Ortak bir üçüncü değişken, sıcaklık, iki olayı birlikte hareket ettirir. Mühendislik verisinde bu tuzak sıktır: bir sensörün sıcaklığı ile arıza oranı korelasyonlu olabilir, ama bu, sıcaklığın arızayı yarattığı anlamına gelmez; tasarımı ancak deneyle (A/B, kontrollü değişim) doğrulayabilirsin (49.10).

### Anscombe dörtlüsü: aynı sayılar, farklı şekiller

Anscombe (1973) dört küçük veri kümesi tanıttı. Dördünün ortalamaları, varyansları, korelasyonları ve en küçük kareler doğrusu neredeyse aynıdır; yine de ikincisinin grafiği belirgin biçimde eğridir, üçüncüsü ise tek bir aykırı değerle bozulmuş bir doğrudur. Sayılar özetlere bakarak yetmez, grafiğe bakmak gerekir.

Aşağıdaki betik bu dört kümenin özetlerini ve kovaryans formülünü uygular. Ayrıca şapka problemi için dogrusallık sayımını yapar.

```python
import math
import random

import numpy as np

# Anscombe ceyreklisi (Anscombe 1973). Dort veri kumesi ayni ozet
# istatistiklere sahiptir ama tamamen farkli sekillerdedir.
X1 = [10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5]
Y1 = [8.04, 6.95, 7.58, 8.81, 8.33, 9.96, 7.24, 4.26,
      10.84, 4.82, 5.68]
Y2 = [9.14, 8.14, 8.74, 8.77, 9.26, 8.10, 6.13, 3.10,
      9.13, 7.26, 4.74]
Y3 = [7.46, 6.77, 12.74, 7.11, 7.81, 8.84, 6.08, 5.39,
      8.15, 6.42, 5.73]
X4 = [8, 8, 8, 8, 8, 8, 8, 19, 8, 8, 8]
Y4 = [6.58, 5.76, 7.71, 8.84, 8.47, 7.04, 5.25, 12.50,
      5.56, 7.91, 6.89]
```

```python
def ortalama(v):
    return sum(v) / len(v)


def kovaryans(x, y):
    """Cov(X,Y) = E[(X - mu_x)(Y - mu_y)] (n bolu n-1 ile)."""
    n = len(x)
    mx, my = ortalama(x), ortalama(y)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (n - 1)


def korelasyon(x, y):
    sx = math.sqrt(kovaryans(x, x))
    sy = math.sqrt(kovaryans(y, y))
    return kovaryans(x, y) / (sx * sy)
```

```python
def anscombe():
    seriler = [
        ("I", X1, Y1),
        ("II", X1, Y2),
        ("III", X1, Y3),
        ("IV", X4, Y4),
    ]
    for ad, x, y in seriler:
        print(
            "%-3s ort_y=%.2f  var_y=%.3f  r=%.3f"
            % (ad, ortalama(y), kovaryans(y, y), korelasyon(x, y))
        )
    print("numpy r (I): %.3f" % np.corrcoef(X1, Y1)[0, 1])
```

```python
def sapka_dogrusallik(n=10, deneme=100_000, seed=49):
    """Dogrusallik: S = sum I_i, E[S] = n * (1/n) = 1."""
    rnd = random.Random(seed)
    top = 0.0
    kare = 0.0
    for _ in range(deneme):
        p = list(range(n))
        rnd.shuffle(p)
        s = sum(1 for i, v in enumerate(p) if i == v)
        top += s
        kare += s * s
    ort = top / deneme
    var = kare / deneme - ort * ort
    return ort, var
```

```python
def main():
    anscombe()
    ort, var = sapka_dogrusallik()
    print(
        "Sapka n=10: E[S] ~ %.4f, Var(S) ~ %.4f (teorik 1)"
        % (ort, var)
    )


if __name__ == "__main__":
    main()
```

Aşağıdaki çıktı, dört kümenin ortalamasının 7,50, varyansının yaklaşık 4,12 ve korelasyonunun 0,816 ile 0,817 arasında olduğunu gösteriyor. Şapka simülasyonunda E[S] ve Var(S) değerleri teorik 1 değerlerine yakındır.

```term
$ python b49_c_beklenen.py
I   ort_y=7.50  var_y=4.127  r=0.816
II  ort_y=7.50  var_y=4.128  r=0.816
III ort_y=7.50  var_y=4.123  r=0.816
IV  ort_y=7.50  var_y=4.123  r=0.817
numpy r (I): 0.816
Sapka n=10: E[S] ~ 0.9972, Var(S) ~ 0.9966 (teorik 1)
```

Betiğin I. kümesi için hesapladığımız korelasyon, numpy'nin `np.corrcoef` fonksiyonuyla üç ondalık basamakta aynı çıkar; bu, kendi formülümüzün doğru olduğunun bir kontrolüdür. Varyans ve kovaryans kavramları Bölüm 48'de çok değişkenli bir yapıya taşınır: n boyutlu bir veri kümesinin **kovaryans matrisi** Σ, köşegeninde her değişkenin varyansını, dışında ikili kovaryansları tutar. Bu matrisin özdeğer ve özvektörleri, ana bileşen analizinin (Bölüm 61) ve SVD'nin (Bölüm 48) özüdür.

## 49.6 Büyük sayılar yasası, merkezi limit teoremi ve Monte Carlo

Şimdiye kadar tek bir değişkenin dağılımına baktık. Mühendislik ise hep **örnek ortalaması** ile çalışır: 1000 gecikme ölçümünün ortalaması, bir sensörün 50 okumasının ortalaması, bir eğitim kümesinde kaybın ortalaması. İki temel teorem, bu ortalamaların ne zaman ve nasıl güvenilir olduğunu söyler.

**Büyük sayılar yasası** (law of large numbers) der ki: X₁, X₂, ... bağımsız ve aynı dağılımlı (i.i.d.) ve beklenen değeri μ ise, örnek ortalaması X̄ₙ = (X₁ + ... + Xₙ) / n, n büyüdükçe μ'ye yaklaşır. Daha kesin olarak, her ε > 0 için P(|X̄ₙ − μ| > ε) olasılığı n arttıkça 0'a gider (zayıf yasa). Bu, sıklık yorumunun matematiksel temelidir: bir paranın yazı gelme sıklığı uzun vadede 1/2'ye yaklaşır.

Şimdi bunu görelim. Ortalaması 1 olan üstel bir dağılımdan (Üstel(1)) bir milyon örnek çekip kümülatif ortalamayı izleyelim. Kümülatif ortalama n = 10'da 1,456'dır, n = 100'de 0,832, n = 1000'de 0,949 ve n = 10 000'de 0,995'tir. Dalgalanma azalır, ama yavaş azalır: hata yaklaşık 1/√n ile ölçeklenir. Bu, bir sonraki bölümün ana fikridir.

**Merkezi limit teoremi** (central limit theorem, CLT) bu hatanın şeklini söyler. İ.i.d. X₁, ..., Xₙ için ortalama μ ve varyans σ² varsa, standartlaştırılmış örnek ortalaması

Z = (X̄ₙ − μ) / (σ / √n)

n büyüdükçe, X'in dağılımı ne olursa olsun, standart normal N(0, 1) dağılımına yaklaşır. Bu, mühendislikte normal dağılımın neden her yerde karşımıza çıktığını açıklar: her ölçüm birçok küçük ve bağımsız etkinin toplamı gibi davrandığında, ortalama normal olur.

Şekil 49.4 bunu gösteriyor. Üstel(1) dağılımı keskin biçimde çarpıktır; n = 1 için histogram sağa doğru uzun bir kuyruğa sahiptir ve sol sınırı −1'dedir (çünkü X ≥ 0 iken Z = X − 1 ≥ −1). n = 2 ve n = 5 için şekil yavaşça simetrikleşir. n = 30'da histogram, kırmızı çizgiyle gösterilen N(0, 1) eğrisine neredeyse oturur. Betik, her n için ortalama ve varyansın 0 ve 1'e yaklaştığını, ayrıca |Z| > 2 olasılığının (normalde 0,0455) yaklaştığını ölçer.

![Şekil 49.4: Merkezi limit teoremi. Üstel(1) örneklerinin standartlaştırılmış ortalaması: n = 1, 2, 5, 30. Kırmızı çizgi N(0,1) yoğunluğu.](gorseller/b49_mlt.png)

Aşağıdaki betik büyük sayılar, merkezi limit ve Monte Carlo deneylerini birlikte yapar. Monte Carlo kısmı, birim karenin içine rastgele nokta atıp çeyrek daireye düşen oranla π'yi tahmin eder: nokta (x, y) için x² + y² ≤ 1 ise daire içindedir ve 4 · (daire içi oran) ≈ π'dir.

```python
import csv
import math
import os

import numpy as np

VERI = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "..",
    "engine",
    "veri",
)
```

```python
def buyuk_sayilar(seed=49):
    """Ustel(1) orneklerinin kosan ortalamasi: E[X] = 1."""
    rng = np.random.default_rng(seed)
    x = rng.exponential(1.0, 1_000_000)
    kosan = np.cumsum(x) / np.arange(1, len(x) + 1)
    for n in (10, 100, 1_000, 10_000, 1_000_000):
        print("n=%8d  ort=%.4f" % (n, kosan[n - 1]))
```

```python
def mlt(seed=49, m=200_000):
    """Ustel(1) icin Z = (Xbar - 1) * sqrt(n) standartlastirmasi.

    Bins: [-4, 4] icinde 40 kutu. Yogunluk, kutu genisligine bolunmus
    oranla verilir; normal yogunluk ile birlikte karsilastirilir.
    """
    rng = np.random.default_rng(seed)
    kenar = np.linspace(-4, 4, 41)
    satirlar = [["n", "merkez", "yogunluk"]]
    for n in (1, 2, 5, 30):
        x = rng.exponential(1.0, (m, n))
        z = (x.mean(axis=1) - 1.0) * math.sqrt(n)
        h, _ = np.histogram(z, bins=kenar)
        yog = h / (m * (kenar[1] - kenar[0]))
        merk = (kenar[:-1] + kenar[1:]) / 2
        for c, y in zip(merk, yog):
            satirlar.append([n, "%.2f" % c, "%.5f" % y])
        # Ozet: ortalama 0 ve varyans 1 hedeflenir.
        print(
            "n=%2d  E[Z]=%.4f  Var(Z)=%.4f  P(|Z|>2)=%.4f"
            % (n, z.mean(), z.var(), np.mean(np.abs(z) > 2))
        )
    return satirlar
```

```python
def monte_carlo_pi(seed=49, tekrar=20):
    """Birim kare icine rastgele nokta; pi ~ 4 * (iceride / n).

    Her n icin tekrar kosusu yapilir; hata RMS olarak raporlanir.
    """
    rng = np.random.default_rng(seed)
    satirlar = [["n", "rms_hata", "ort_mutlak_hata"]]
    for n in np.logspace(2, 7, 11).astype(int):
        hatalar = []
        for _ in range(tekrar):
            x = rng.random(n)
            y = rng.random(n)
            pi_hat = 4.0 * np.mean(x * x + y * y <= 1.0)
            hatalar.append(pi_hat - math.pi)
        h = np.array(hatalar)
        rms = math.sqrt(np.mean(h * h))
        mab = np.mean(np.abs(h))
        satirlar.append([int(n), "%.6f" % rms, "%.6f" % mab])
    return satirlar
```

```python
def egim(satirlar):
    """log(rms) - log(n) dogrusunun egimi (en kucuk kareler)."""
    ns = np.array([float(r[0]) for r in satirlar[1:]])
    rms = np.array([float(r[1]) for r in satirlar[1:]])
    a, _ = np.polyfit(np.log(ns), np.log(rms), 1)
    return a
```

```python
def yaz(ad, satirlar):
    yol = os.path.join(VERI, ad)
    with open(yol, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(satirlar)
    print("yazildi:", ad)
```

```python
def main():
    buyuk_sayilar()
    yaz("b49_mlt.csv", mlt())
    pi_satir = monte_carlo_pi()
    yaz("b49_mc_pi.csv", pi_satir)
    for r in pi_satir:
        print(r)
    print("egim (log-log) = %.3f  (beklenen -0.5)" % egim(pi_satir))


if __name__ == "__main__":
    main()
```

Betik, şekil üretimi için iki CSV dosyası yazar (`engine/veri/` klasörüne). Çıktıda bu dosyaların adı görünür; Monte Carlo tablosunda her satır, n nokta, 20 bağımsız tekrarın hata karesi ortalamasının karekökünü (RMS hata) verir.

```term
$ python b49_d_limit.py
n=      10  ort=1.4560
n=     100  ort=0.8323
n=    1000  ort=0.9488
n=   10000  ort=0.9954
n= 1000000  ort=0.9986
n= 1  E[Z]=-0.0032  Var(Z)=0.9909  P(|Z|>2)=0.0493
n= 2  E[Z]=-0.0024  Var(Z)=0.9960  P(|Z|>2)=0.0465
n= 5  E[Z]=-0.0005  Var(Z)=1.0031  P(|Z|>2)=0.0412
n=30  E[Z]=-0.0008  Var(Z)=0.9992  P(|Z|>2)=0.0436
yazildi: b49_mlt.csv
yazildi: b49_mc_pi.csv
['n', 'rms_hata', 'ort_mutlak_hata']
[100, '0.160059', '0.133522']
[316, '0.087202', '0.062731']
[1000, '0.068444', '0.054841']
[3162, '0.027434', '0.023114']
[10000, '0.015316', '0.013141']
[31622, '0.010595', '0.008294']
[100000, '0.006104', '0.004949']
[316227, '0.002928', '0.002498']
[1000000, '0.001343', '0.001198']
[3162277, '0.000918', '0.000807']
[10000000, '0.000407', '0.000312']
egim (log-log) = -0.515  (beklenen -0.5)
```

Monte Carlo hatasının teorik biçimi basittir. Her nokta, daire içinde olma olasılığı p = π/4 olan bir Bernoulli denemesidir. 4 · (daire içi oran) tahmincisinin varyansı 16 · p(1 − p) / n'dir; standart hata 4√(p(1 − p)/n) ≈ 1,64 / √n olur. Yani hata n ile 1/√n oranında azalır: hatayı yarıya indirmek için dört kat, bir basamak küçültmek için yüz kat örnek gerekir. Şekil 49.5'te bu eğim log-log ölçeğinde doğru bir çizgi olarak görünür; ölçülen eğim −0,515'tir, teorik −1/2'ye çok yakın. Bu sonuç, Monte Carlo yönteminin hatasını bir deneyle ve bir formülle aynı anda kontrol edebildiğimizi gösterir.

![Şekil 49.5: Monte Carlo ile π tahmininin hatası, log-log ölçekte. Ölçülen RMS hata (kırmızı) ile eğim −1/2 referansı (kesikli).](gorseller/b49_mc_hata.png)

Bu sonuç mühendislikte önemlidir: bir simülasyonun doğruluğunu artırmak, çalışma süresini aynı oranda artırır. Bir savunma simülasyonunda hata payını yarıya indirmek için dört kat daha fazla koşu gerekir. Bu yüzden Monte Carlo'nun kendi hatasını raporlamak (standart hata ya da güven aralığı, 49.9) zorunludur. Ayrıca bu bölümün ilerleyen kısımlarında kullanacağımız her örnek ortalaması, bu hata kurallarına uyar.

## 49.7 Rastgele sayı üretimi: ters CDF, Box–Muller ve reddetme

Monte Carlo ve simülasyonun her adımı bir rastgele sayıya dayanır. Ama bilgisayarlar gerçekten rastgele sayı üretemez; ürettikleri sayılar bir **sözde rastgele** (pseudo-random) üreteçten gelir. Bir tohum (seed) verildiğinde, üreteç her zaman aynı diziyi verir. Bu bir kusur gibi görünebilir, ama simülasyonu tekrarlanabilir kılan tam da budur: Bölüm 39.11'deki kararsız testlerin nedenlerinden biri, tohumsuz üretilen rastgeleliktir; tohumu sabitlemek bu kaynağı ortadan kaldırır.

Python'da iki modül vardır ve bunları karıştırmamak gerekir. `random` modülü (Mersenne Twister algoritması) simülasyon içindir: hızlıdır, tekrarlanabilirdir, ama kriptografik olarak güvenli değildir; çıktısından iç durumu geri çıkarmak mümkündür. `secrets` modülü ise işletim sisteminin entropi kaynağını kullanır; parola, oturum anahtarı ve jeton gibi tahmin edilmemesi gereken değerler içindir. Bölüm 32'de gördüğün `random.Random(42)` ile `secrets.token_bytes` arasındaki fark tam budur: birincisi her seferinde aynıdır, ikincisi her seferinde farklıdır ve tekrarlanamaz.

Bir rastgele sayı üretecini düzgün bir dağılımdan (U(0, 1)) başlatıp başka dağılımlar üretmek için üç temel yöntem vardır.

**Ters CDF yöntemi.** F, X'in birikimli dağılım fonksiyonuysa ve F⁻¹ tersi hesaplanabiliyorsa, U ~ U(0, 1) için X = F⁻¹(U) bir X üretir. Bunun nedeni şudur: P(F⁻¹(U) ≤ x) = P(U ≤ F(x)) = F(x). Üstel(λ) için F(x) = 1 − e^(−λx), dolayısıyla F⁻¹(u) = −ln(1 − u) / λ'dır. Ters CDF yöntemi, F'nin tersi kolay olan her dağılım için çalışır; normal için tersi yoktur, bu yüzden başka bir yöntem gerekir.

**Box–Muller yöntemi.** İki bağımsız U(0, 1) değerinden iki bağımsız N(0, 1) değeri üretir. R = √(−2 ln U₁) ve Θ = 2πU₂ alınır; Z₁ = R cos Θ ve Z₂ = R sin Θ iki bağımsız standart normal değerdir. Bu, iki boyutlu normal dağılımın kutupsal koordinatlara çevrilmesinden gelir: (Z₁, Z₂) noktasının açısı düzgün, yarıçapının karesi üstel dağılımlıdır. Yöntem, ters CDF gibi normalin tersini gerektirmez.

**Reddetme örneklemesi.** Hedef yoğunluk f(x) biliniyor ama ters CDF'i yoksa şöyle çalışır: basit bir g(x) önerici dağılımından x çek, bir v ~ U(0, 1) çek ve f(x) ≥ M · g(x) · v ise x'i kabul et; değilse reddet. Burada M, f(x)/g(x) oranının üst sınırıdır. Kabul olasılığı 1/M'dir: yüksek M, verimsiz bir yöntem demektir. Hedef 6x(1 − x) (Beta(2, 2)) ve öneri U(0, 1) olsun. f(x) en çok x = 1/2'de, değeri 1,5'tir; yani M = 1,5 ve kabul oranı 2/3'tür.

Aşağıdaki betik her üç yöntemle 200 000 örnek üretir ve ortalama ile varyansı teorik değerlerle karşılaştırır. Ayrıca tohumun tekrarlanabilirliğini ve `secrets` çıktısının uzunluğunu gösterir.

```python
import math
import random
import secrets


def ters_cdf_ustel(lam, rnd):
    """F(x) = 1 - e^(-lam x) -> F^-1(u) = -ln(1 - u) / lam."""
    u = rnd.random()
    return -math.log(1.0 - u) / lam
```

```python
def box_muller(rnd):
    """Iki bagimsiz U(0,1) -> iki bagimsiz N(0,1)."""
    u1 = 1.0 - rnd.random()  # log(0) olmasin diye (0,1]
    u2 = rnd.random()
    r = math.sqrt(-2.0 * math.log(u1))
    return r * math.cos(2 * math.pi * u2), r * math.sin(
        2 * math.pi * u2
    )
```

```python
def reddetme(rnd):
    """Hedef f(x) = 6x(1-x) (Beta(2,2)), oneri g(x) = 1 (U(0,1)).

    M = max f = 1.5 (x = 1/2). Kabul olasiligi f(x) / (M g(x)).
    Her denemede: x ~ U(0,1), v ~ U(0,1); v <= f(x)/M ise kabul.
    Beklenen kabul orani 1/M = 2/3.
    """
    M = 1.5
    deneme = 0
    while True:
        deneme += 1
        x = rnd.random()
        v = rnd.random()
        if v <= 6 * x * (1 - x) / M:
            return x, deneme
```

```python
def ozet(ad, veri, teorik_ort, teorik_var):
    n = len(veri)
    ort = sum(veri) / n
    var = sum((t - ort) ** 2 for t in veri) / (n - 1)
    print(
        "%-22s ort=%.4f (%.4f)  var=%.4f (%.4f)"
        % (ad, ort, teorik_ort, var, teorik_var)
    )
```

```python
def main():
    rnd = random.Random(49)
    n = 200_000

    ustel = [ters_cdf_ustel(2.0, rnd) for _ in range(n)]
    ozet("Ters CDF Ustel(2)", ustel, 0.5, 0.25)

    z = []
    while len(z) < n:
        a, b = box_muller(rnd)
        z.extend((a, b))
    ozet("Box-Muller N(0,1)", z[:n], 0.0, 1.0)

    kabul = []
    toplam_deneme = 0
    for _ in range(n // 2):
        x, d = reddetme(rnd)
        kabul.append(x)
        toplam_deneme += d
    ozet("Reddetme Beta(2,2)", kabul, 0.5, 0.05)
    print(
        "Kabul orani = %.4f (beklenen 0.6667)"
        % (len(kabul) / toplam_deneme)
    )

    # Tohum: ayni tohum ayni dizi, secrets ise her seferinde farkli.
    a = random.Random(42)
    b = random.Random(42)
    print("Tohum 42 iki kez: %s" % (a.random() == b.random()))
    print(
        "secrets uzunluk: %d bit" % (len(secrets.token_bytes(16)) * 8)
    )


if __name__ == "__main__":
    main()
```

```term
$ python b49_e_ornekleme.py
Ters CDF Ustel(2)      ort=0.4986 (0.5000)  var=0.2472 (0.2500)
Box-Muller N(0,1)      ort=-0.0004 (0.0000)  var=0.9991 (1.0000)
Reddetme Beta(2,2)     ort=0.5002 (0.5000)  var=0.0498 (0.0500)
Kabul orani = 0.6656 (beklenen 0.6667)
Tohum 42 iki kez: True
secrets uzunluk: 128 bit
```

Çıktıdaki ortalama ve varyans değerleri teorik değerlere birkaç binde birlik farkla yaklaşır; örnek sayısı 200 000'dir ve beklenen fark küçüktür. Kabul oranının 0,6656 çıkması, teorik 2/3 ≈ 0,6667'ye yakındır. Tohum satırı, aynı sayının iki kez üretildiğini gösterir; `secrets` satırı ise her çalıştırmada farklı olan sayıların bitlerini değil yalnızca uzunluğunu yazdırır, çünkü tekrarlanabilir bir çıktı beklemek burada yanlış olurdu.

Reddetme yöntemi küçük boyutlarda basittir, ama boyut arttıkça kabul oranı üstel olarak düşer. Bu, **boyutsallık laneti** (curse of dimensionality) olarak bilinir (genel bilgi). Yüksek boyutlu ML modellerinin posterior örneklemesinde (Bölüm 62 ve 74) bu yüzden MCMC gibi yöntemler kullanılır. Ama temel fikir aynıdır: bir dağılımdan örnek almak, onu kapsayan kolay bir dağılımdan örnek almak ve bir kabul kuralı uygulamaktır.

## 49.8 Kestirim: momentler, en büyük olabilirlik ve MAP

Elinde bir veri kümesi var, ama dağılımın parametresini bilmiyorsun. Bir sensörün arıza oranı λ'yı, bir iletim kanalının bit hata olasılığını p'yi, bir ölçümün gürültü düzeyini σ'yı bilmek istiyorsun. **Kestirim** (estimation) bu parametreyi veriden hesaplayan bir kuraldır: θ̂ = g(X₁, ..., Xₙ). Şapka (ˆ) işareti, bu değerin gerçek θ'nın bir tahmini olduğunu gösterir.

İyi bir kestiricinin üç özelliği vardır. **Yanlılık** (bias), E[θ̂] − θ farkıdır; sıfır olması istenir ama her zaman mümkün değildir. **Varyans**, Var(θ̂), tahminin örnekten örneğe ne kadar oynadığını söyler. **Tutarlılık**, n büyüdükçe θ̂'nin θ'ya olasılıkla yaklaşmasıdır. Bu üç özellik çoğu zaman birbiriyle çatışır: yanlılığı sıfırlamak varyansı artırabilir. Bu takası aşağıda somut olarak göreceğiz.

**Momentler yöntemi.** Dağılımın momentlerini (E[X], E[X²], ...) parametrelerle yazıp, örnek momentleriyle eşitlersin. U(0, θ) düzgün dağılımında E[X] = θ/2'dir; bu yüzden θ̂ = 2X̄. Yöntem sezgiseldir ve çoğu zaman tutarlı bir kestirim verir, ama her zaman en iyi olmaz.

**En büyük olabilirlik (maximum likelihood, MLE).** Verinin olabilirliği, gözlenen veriyi üreten parametrenin ne kadar "inandırıcı" olduğudur. Bağımsız X₁, ..., Xₙ için olabilirlik L(θ) = ∏ f(xᵢ; θ)'dır. Çarpımlar toplamaya dönmesi için log-olabilirlik l(θ) = ∑ ln f(xᵢ; θ) kullanılır; logaritma artan bir fonksiyon olduğu için maksimumu aynı yerdedir. MLE, l'yi maksimize eden θ̂'dır.

Üç klasik örneği kendi kâğıdında türetebilirsin. Adımları atlamadan yaz; yapay zekâ kullanmadan yapabildiğin an, MLE sende yerleşmiş demektir.

**Bernoulli(p).** n denemede k başarı varsa l(p) = k ln p + (n − k) ln(1 − p). Türevi alıp sıfıra eşitle: k/p − (n − k)/(1 − p) = 0. Buradan p̂ = k/n çıkar: başarı oranı. Simülasyonda n = 100, gerçek p = 0,3 için k = 27 gözlendi ve p̂ = 0,27 bulundu.

**Üstel(λ).** Bağımsız süreler x₁, ..., xₙ için l(λ) = n ln λ − λ ∑ xᵢ. Türev n/λ − ∑ xᵢ = 0; yani λ̂ = n / ∑ xᵢ = 1 / x̄. Ortalama süre ne kadar uzunsa, arıza oranı o kadar küçük çıkar. Aşağıdaki betik bunu sayısal olarak da doğrular: altın oran aramasıyla log-olabilirliğin maksimumunu bulur ve kapalı formülle aynı değeri verdiğini gösterir (Şekil 49.6).

**Normal(μ, σ²).** Log-olabilirliği μ ve σ² üzerinden maksimize ederek μ̂ = x̄ ve σ̂² = (1/n) ∑ (xᵢ − x̄)² elde edilir. Dikkat et: payda n'dir, n − 1 değil. Bu fark önemlidir. σ̂² yanlıdır: E[σ̂²] = ((n − 1)/n) σ². Yanlılığı düzeltmek için n − 1 ile bölünür; bu değer s² (örnek varyansı) olur ve yansızdır. Payda n − 1 olmasının sebebi, x̄'nin veriden hesaplanması ve bir serbestlik derecesi harcamasıdır (Bessel düzeltmesi). Simülasyonda n = 5 için E[σ̂²] = 0,7998, (n − 1)/n = 0,8 ile örtüşüyor; E[s²] = 0,9997 ise σ² = 1'e yakın.

Şekil 49.6, Üstel(0,5) ile üretilen 50 gözlemin log-olabilirlik eğrisini gösterir. Eğri, gerçek değerden (0,5) biraz sağda, λ̂ = 0,5926'da tepe yapar. Sapmanın nedeni tek bir örneğin rastgeleliğidir; örnek büyüdükçe tepe gerçek değere yaklaşır.

![Şekil 49.6: Üstel(0,5) için log-olabilirlik eğrisi (n = 50). Tepe, MLE = n / ∑x = 0,5926; kesikli çizgi gerçek değer 0,5.](gorseller/b49_mle.png)

### Yanlılık ve varyans takası: düzgün dağılım örneği

Düzgün U(0, θ) dağılımında iki kestirici var: momentler yöntemiyle θ̂ = 2X̄ ve MLE ile θ̂ = max(X). MLE, maksimumdur çünkü olabilirlik θ'nın en büyük gözlemden küçük olmasını yasaklar. Bu iki kestiricinin yanlılık ve varyansını simüle ettik (θ = 1, n = 10). Momentler yöntemi yansızdır: ortalaması 0,9998 çıktı. MLE ise yanlıdır: E[max] = nθ/(n + 1) = 0,909 beklenir ve simülasyon 0,9090 verdi. Ama varyansı yaklaşık beş kat küçüktür: 0,00692'ye karşılık 0,03330. Yani yanlı bir kestirici, yansız olandan çok daha kararlı olabilir. Ortalama hatası (MSE = yanlılık² + varyans) açısından MLE bu örnekte çok daha iyidir.

### Önseller, MAP ve sıfır gözlem sorunu

Bayesçi bakışta parametre θ de bir rastgele değişkendir ve önceden bildiğimiz bir **önsel** dağılım π(θ) ile tanımlanır. Veriyi gördükten sonra **sonsal** (posterior) dağılım, Bayes teoremiyle p(θ | veri) ∝ f(veri | θ) π(θ) olur. Sonsalın tepesi **MAP** (maximum a posteriori) kestiricisidir. MAP, MLE'ye bir önsel ceza terimi eklenmiş halidir: log π(θ) terimi, önseli inandığın değerlere yakın tutar.

Beta–Bernoulli modeli bunun en temiz örneğidir. p, başarı olasılığı ve önsel Beta(α, β) olsun. n denemede k başarı görülürse sonsal yine bir Beta'dır: Beta(α + k, β + n − k). Bu özelliğe **eşlenik önsel** (conjugate prior) denir; hesap kapalı biçimdedir. Sonsal ortalama (k + α) / (n + α + β) ve MAP değeri (k + α − 1) / (n + α + β − 2) olur.

Burada ciddi bir tuzak var: n = 10 denemede hiç başarı görmediysen, MLE p̂ = 0 çıkar. Bu, bir daha asla başarı olmayacağı anlamına gelir; sıfır olasılığa güvenmek hem yanlış hem tehlikelidir. Bu sorun, "sıfır gözlem" (zero-count) problemi olarak bilinir ve seyrek olayların her modelde karşımıza çıkan ortak bir tuzağıdır. Çözüm **Laplace düzeltmesidir**: başarı ve başarısızlığa birer sanal gözlem ekleyip (k + 1) / (n + 2) kullanmak. Bu, Beta(1, 1) (düzgün) önseli altında sonsal ortalamaya karşılık gelir.

Aşağıdaki betik, bu değerleri n = 10 ve k = 0 için hesaplar ve kendi formüllerimizi karşılaştırır. Beta(2, 2) önseli için MAP formülü (k + 1) / (n + 2) verir; bu, Laplace düzeltmesinin sonucuyla aynıdır. Sonsal ortalama ise (k + 2) / (n + 4) = 0,1429'dur.

```python
import csv
import os
import math
import random

VERI = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "..",
    "engine",
    "veri",
)


def log_olabilirlik_ustel(lam, veri):
    """l(lam) = n ln(lam) - lam * sum(x)."""
    return len(veri) * math.log(lam) - lam * sum(veri)


def altin_oran_maks(f, a, b, tol=1e-10):
    """Tek tepeli f icin altin oran aramasi: maksimum noktasi."""
    g = (math.sqrt(5) - 1) / 2
    c, d = b - g * (b - a), a + g * (b - a)
    while abs(b - a) > tol:
        if f(c) > f(d):
            b = d
        else:
            a = c
        c, d = b - g * (b - a), a + g * (b - a)
    return (a + b) / 2
```

```python
def ustel_mle(seed=49, n=50, lam_gercek=0.5):
    rnd = random.Random(seed)
    veri = [rnd.expovariate(lam_gercek) for _ in range(n)]
    kapali = n / sum(veri)
    sayisal = altin_oran_maks(
        lambda l: log_olabilirlik_ustel(l, veri), 0.01, 5.0
    )
    print(
        "Ustel MLE: kapali=%.6f  sayisal=%.6f  gercek=%.2f"
        % (kapali, sayisal, lam_gercek)
    )
    # Log-olabilirlik egrisi (Sekil 49.6 icin).
    satirlar = [["lambda", "log_olabilirlik", "kapali_mle"]]
    for i in range(0, 201):
        l = 0.05 + i * (1.2 - 0.05) / 200
        satirlar.append(
            [
                "%.4f" % l,
                "%.4f" % log_olabilirlik_ustel(l, veri),
                "%.6f" % kapali,
            ]
        )
    with open(
        VERI + "/b49_mle.csv", "w", encoding="utf-8", newline=""
    ) as f:
        csv.writer(f).writerows(satirlar)
    print("  b49_mle.csv yazildi (%d satir)" % (len(satirlar) - 1))
```

```python
def bernoulli_mle(seed=49):
    rnd = random.Random(seed)
    n, p = 100, 0.3
    veri = [1 if rnd.random() < p else 0 for _ in range(n)]
    k = sum(veri)
    print("Bernoulli: k=%d n=%d  MLE p = k/n = %.4f" % (k, n, k / n))


def normal_yanlilik(seed=49, n=5, tekrar=200_000):
    """E[sigma^2_MLE] = (n-1)/n sigma^2 ; E[s^2] = sigma^2."""
    rnd = random.Random(seed)
    s_mle = s_ust = 0.0
    for _ in range(tekrar):
        x = [rnd.gauss(0.0, 1.0) for _ in range(n)]
        m = sum(x) / n
        kare = sum((t - m) ** 2 for t in x)
        s_mle += kare / n
        s_ust += kare / (n - 1)
    print(
        "Normal n=%d (sigma^2=1): E[MLE]=%.4f (%.2f)  E[s^2]=%.4f"
        % (n, s_mle / tekrar, (n - 1) / n, s_ust / tekrar)
    )
```

```python
def uniform_momentler_mle(seed=49, n=10, teta=1.0, tekrar=200_000):
    rnd = random.Random(seed)
    mm = []
    ml = []
    for _ in range(tekrar):
        x = [rnd.uniform(0.0, teta) for _ in range(n)]
        mm.append(2 * sum(x) / n)
        ml.append(max(x))
    o1 = sum(mm) / tekrar
    v1 = sum((t - o1) ** 2 for t in mm) / tekrar
    o2 = sum(ml) / tekrar
    v2 = sum((t - o2) ** 2 for t in ml) / tekrar
    print(
        "Momentler: ort=%.4f var=%.5f (teorik %.5f)"
        % (o1, v1, teta * teta / (3 * n))
    )
    print(
        "MLE max:   ort=%.4f var=%.5f (teorik %.5f)"
        % (o2, v2, n * teta * teta / ((n + 1) ** 2 * (n + 2)))
    )


def beta_bernoulli():
    n, k = 10, 0
    mle = k / n
    laplace = (k + 1) / (n + 2)
    map22 = (k + 1) / (n + 2)  # Beta(2,2) icin (k+a-1)/(n+a+b-2)
    ort22 = (k + 2) / (n + 4)  # Beta(2,2) sonsal ortalama
    print("n=%d k=%d: MLE=%.4f Laplace=%.4f" % (n, k, mle, laplace))
    print(
        "  Beta(2,2): MAP=%.4f  sonsal ortalama=%.4f" % (map22, ort22)
    )
```

```python
def main():
    ustel_mle()
    bernoulli_mle()
    normal_yanlilik()
    uniform_momentler_mle()
    beta_bernoulli()


if __name__ == "__main__":
    main()
```

```term
$ python b49_f_kestirim.py
Ustel MLE: kapali=0.592570  sayisal=0.592570  gercek=0.50
  b49_mle.csv yazildi (201 satir)
Bernoulli: k=27 n=100  MLE p = k/n = 0.2700
Normal n=5 (sigma^2=1): E[MLE]=0.7998 (0.80)  E[s^2]=0.9997
Momentler: ort=0.9998 var=0.03330 (teorik 0.03333)
MLE max:   ort=0.9090 var=0.00692 (teorik 0.00689)
n=10 k=0: MLE=0.0000 Laplace=0.0833
  Beta(2,2): MAP=0.0833  sonsal ortalama=0.1429
```

Çıktıdaki ilk satır iki yöntemi karşılaştırır: kapalı formül n / ∑x ile altın oran araması aynı değeri (0,592570) veriyor. Bu, türevden elde ettiğimiz formülün doğru olduğunu gösterir. Beta(2, 2) önseline gelince, Şekil 49.7 önselden sonsala geçişi gösterir: bir başarı sonrası eğri sağa kayar; on denemenin üçü başarıysa sonsal Beta(5, 9) olur ve tepesi 1/3 civarındadır. Önselin etkisi, veri azken büyüktür; veri çoğaldıkça sonsal verinin şekline yaklaşır.

![Şekil 49.7: Beta(2, 2) önselinden sonsala. Kesikli eğri önsel; mavi, bir başarı sonrası Beta(3, 2); bordo, 10 denemede 3 başarı sonrası Beta(5, 9).](gorseller/b49_beta.png)

### Bayesçi mi, sıklıkçı mı?

İki okulun da savunulabilir gerekçeleri vardır ve mühendis ikisini bilmek zorundadır. Sıklıkçı yaklaşımda θ sabit ama bilinmeyen bir sayıdır; veri rastgeledir; güven aralığı ve p-değeri gibi kavramlar tekrarlanabilir deneyler üzerinden tanımlanır (49.9 ve 49.10). Bayesçi yaklaşımda θ kendisi bir rastgele değişkendir; belirsizliği olasılıkla anlatırsın ve önsel bilgini açıkça katarsın. Pratikte ML mühendisleri çoğu zaman MAP kullanır, çünkü regülarizasyon (L2 cezası bir Gauss önseline, L1 cezası bir Laplace önseline karşılık gelir; Bölüm 58) ile MAP birebir aynı şeydir. Bu bağlantıyı Bölüm 62'de Bayesçi modellerde tekrar göreceksin.

## 49.9 Güven aralıkları: normal, t ve bootstrap

Nokta tahmini tek bir sayıdır ve neredeyse kesinlikle yanlıştır. "Gecikme ortalaması 42,8 çevrim" dediğinde, bu sayının ne kadar güvenilir olduğunu söylemiyorsun. **Güven aralığı** (confidence interval, GA) bu belirsizliği bir aralıkla anlatır: θ̂'nin etrafında, belirli bir güven düzeyinde gerçek değeri içermesi beklenen bir [L, U] aralığı.

Burada en sık yapılan yoruma dikkat et. "%95 güven aralığı" demek, "gerçek değerin bu aralıkta olma olasılığı %95'tir" demek **değildir**. Gerçek θ sabittir; aralık ise veriye bağlı rastgele bir nesnedir. Doğru yorum şöyledir: aynı yöntemle çok sayıda bağımsız örnek alıp her biri için aralık hesaplarsan, bu aralıkların yaklaşık %95'i gerçek θ'yı içerir. Bu yorum, aşağıdaki kapsama simülasyonuyla doğrudan sınanır.

### Normal yaklaşım ve t dağılımı

Örnek ortalaması X̄ için Merkezi Limit Teoremi'nden (49.6) X̄ ≈ N(μ, σ²/n). σ biliniyorsa %95 GA: X̄ ± 1,96 · σ/√n. 1,96 değeri, standart normalin %97,5 yüzdeliğidir; iki kuyruktaki toplam %5'i bırakır. σ bilinmez; onun yerine örnek standart sapması s kullanılırsa standart hata s/√n olur. Ama küçük örneklerde s, σ'yı düşük tahmin eder ve aralık çok dar çıkar. Bu yüzden t dağılımı kullanılır: X̄ ± t(0,975; n − 1) · s/√n. t dağılımının kuyrukları normalden daha kalındır; serbestlik derecesi n − 1 büyüdükçe normale yaklaşır (n = 10 için t = 2,262; n = 283 için 1,968; normal için 1,960).

Gecikme verisinde bunu deneyelim. Bölüm 44'teki cevrim düzeyi benzetiminde, kesme kaynağı TIM için 283 gecikme ölçümü var (ortalama 42,81; standart sapma 65,65). Normal yaklaşım [35,16; 50,46], t aralığı [35,13; 50,49] verir; n büyük olduğu için fark küçüktür. Ama yalnızca ilk on gözlemi alırsak tablo değişir: t aralığı [5,32; 66,88] olur ve z-aralığı [9,43; 62,77] hâlâ dardır. Küçük örnekte z-aralığı gereğinden kısadır; t bu eksik belirsizliği hesaba katar.

Bu sayılar, aşağıdaki programın ilk bölümünde üretilir. Program scipy'nin `t.interval` fonksiyonuyla da karşılaştırılır.

```python
import csv
import os
import math
import random

import numpy as np
from scipy import stats

VERI = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "..",
    "engine",
    "veri",
)


def gecikme(tur, kaynak):
    with open(VERI + "/b44_gecikme.csv", encoding="utf-8") as f:
        return [
            float(r["gecikme_cevrim"])
            for r in csv.DictReader(f)
            if r["tur"] == tur and r["kaynak"] == kaynak
        ]


def ort_s(v):
    n = len(v)
    m = sum(v) / n
    s = math.sqrt(sum((t - m) ** 2 for t in v) / (n - 1))
    return m, s
```

```python
def normal_ve_t_ga(v, guven=0.95):
    n = len(v)
    m, s = ort_s(v)
    z = stats.norm.ppf(0.5 + guven / 2)
    t = stats.t.ppf(0.5 + guven / 2, n - 1)
    h_z = z * s / math.sqrt(n)
    h_t = t * s / math.sqrt(n)
    print("n=%d ort=%.3f s=%.3f" % (n, m, s))
    print("  z-GA: [%.3f, %.3f]  (z=%.4f)" % (m - h_z, m + h_z, z))
    print(
        "  t-GA: [%.3f, %.3f]  (t=%.4f, sd=%d)"
        % (m - h_t, m + h_t, t, n - 1)
    )
    lo, hi = stats.t.interval(
        guven, n - 1, loc=m, scale=s / math.sqrt(n)
    )
    print("  scipy t-GA: [%.3f, %.3f]" % (lo, hi))
```

### Bootstrap: dağılımı varsaymadan belirsizlik

Normal ve t aralıkları, örnek ortalaması için ve bir dağılım varsayımı altında çalışır. Peki ortalama yerine medyan ya da p99 gibi bir istatistik için güven aralığı istersek ne yapmalıyız? Bu istatistiğin örnekleme dağılımını teorik olarak türetmek çoğu zaman mümkün değildir.

**Bootstrap** (Efron, 1979) bu sorunu şöyle çözer: elindeki n gözlemi bir "sanal anakitle" gibi düşün. Bu anakitleden yerine koyarak n gözlemlik bir yeniden örnek çek, istatistiği hesapla. Bunu B kez (genelde 10 000) tekrarla. Elde edilen B değerin dağılımı, gerçek örnekleme dağılımının bir tahminidir. %95 yüzdelik bootstrap GA, bu dağılımın %2,5 ve %97,5 yüzdelikleridir.

Bootstrap'in mantığı şudur: gerçek anakitleyi bilmediğin için, onun yerine örneğinin kendisini kullanırsın. Bu, örneğin anakitleyi "iyi temsil ettiğini" varsayar; küçük örneklerde ya da çok kuyruklu dağılımlarda bu varsayım zayıf kalır. Yine de medyan, yüzdelik ve oran gibi istatistikler için en pratik yöntemdir ve Bölüm 49.11'de bunu ölçüm verisinde kullanacağız.

Yukarıdaki TIM verisinin ortalaması için bootstrap (B = 10 000) [35,56; 50,88] verdi; t aralığına çok yakın. Bu beklenen bir sonuçtur: ortalama için normal ve bootstrap aralıkları büyük n'de örtüşür. Şekil 49.8 bootstrap dağılımını ve iki yüzdeliği gösterir. Dağılım simetrik ve yaklaşık normaldir; bu yüzden yüzdelik aralığı ile t aralığı birbirine yakındır.

```python
def bootstrap_ga(v, B=10_000, seed=49):
    """Yuzdelik bootstrap: her yeniden orneklemde ortalama."""
    rnd = random.Random(seed)
    n = len(v)
    dagilim = []
    for _ in range(B):
        ornek = [v[rnd.randrange(n)] for _ in range(n)]
        dagilim.append(sum(ornek) / n)
    dagilim.sort()
    lo = dagilim[int(0.025 * B)]
    hi = dagilim[int(0.975 * B) - 1]
    return lo, hi, dagilim
```

![Şekil 49.8: Bootstrap ortalama dağılımı (B = 10 000, TIM gecikme verisi). Kesikli çizgiler %2,5 ve %97,5 yüzdelikleri, yani 35,56 ve 50,88.](gorseller/b49_bootstrap.png)

### Kapsama simülasyonu: %95 gerçekten %95 mi?

Güven aralığının kendi iddiasını sınamanın yolu, gerçek değeri bildiğimiz bir anakitleden çok kez örnek çekmektir. Aralığın gerçek değeri içerme oranına **kapsama oranı** (coverage) denir. %95 aralık için bu oran 0,95 olmalıdır. Normal anakitle ve üstel anakitle (sağa çarpık) için, n = 5, 10 ve 30 ile 100 000 tekrar yaptık.

| Anakitle | n | z-GA kapsama | t-GA kapsama |
|---|---|---|---|
| Normal | 5 | 0,878 | 0,949 |
| Normal | 10 | 0,917 | 0,949 |
| Normal | 30 | 0,940 | 0,950 |
| Üstel (çarpık) | 5 | 0,811 | 0,884 |
| Üstel (çarpık) | 10 | 0,869 | 0,900 |
| Üstel (çarpık) | 30 | 0,917 | 0,926 |

Tablo iki şey söyler. Birincisi, normal anakitlede t aralığı, n = 5'ten itibaren %95'e çok yakındır; z aralığı ise %88'de kalır, yani %12 yanlış güven vermiş olur. İkincisi, üstel (çarpık) anakitlede bile t aralığı, z'den iyi olsa da n = 30'a kadar %95'in altındadır. Çarpıklık, ortalamanın normale yaklaşmasını yavaşlatır (49.6'daki merkezi limit yavaşlığı). Bu durumda güven aralığının iddiasına değil, dağılımın şekline ve örnek büyüklüğüne bakmak gerekir.

![Şekil 49.9: Güven aralıklarının gerçek değeri içerme oranı. Sol: normal anakitle; sağ: üstel anakitle. Kesikli çizgi %95.](gorseller/b49_kapsama.png)

Bu sonuç mühendislik için bir uyarıdır: gecikme, arıza süresi ve ağ süreleri neredeyse hep sağa çarpıktır. Bu tür verilerde "%95 güven aralığı" diye sunulan bir aralık, gerçekte %90 ya da daha düşük bir kapsamaya sahip olabilir. Ya daha büyük örnek toplarsın, ya da bootstrap ile ölçülen yüzdelikler için kendi kapsamını simülasyonla doğrularsın.

## 49.10 Hipotez testi: p-değeri, hata türleri, güç ve A/B tasarımı

Bir mühendis sık sık "yeni sürüm daha hızlı mı?" diye sorar. Hipotez testi bu soruyu bir karar kuralına çevirir. Önce **sıfır hipotezi** H₀ tanımlanır: genellikle "fark yok" ya da "değişiklik etkisiz" iddiasıdır. Karşıt olan **alternatif hipotez** H₁ ise araştırdığımız iddiadır. Sonra bir **test istatistiği** T seçilir (ortalamalar farkı gibi) ve verinin H₀ altında ne kadar beklenmedik olduğu ölçülür.

Bu ölçünün adı **p-değeridir**: H₀ doğruyken, gözlediğimiz kadar ya da daha aşırı bir test istatistiği görme olasılığı. Formülle, t_gözlenen gözlemlenen değerse, p = P(|T| ≥ |t_gözlenen| | H₀). p-değeri küçükse, veri H₀ ile zor uyuşuyor demektir; karar genelde p < α olduğunda H₀'ı reddetmektir. α, önceden seçilen anlamlılık düzeyidir (genelde 0,05).

### p-değerini nasıl yanlış okuruz?

p-değeri, mühendislikte en çok yanlış yorumlanan sayıdır. Üç yaygın hatayı bilmek, onları yapmaktan kurtarır:

- **p-değeri, H₀'ın doğru olma olasılığı değildir.** p = 0,03 demek, "H₀ %3 ihtimalle doğrudur" değildir. H₀ ya doğrudur ya değildir; p-değeri veriye verilen bir tepkidir, hipotezin olasılığı değil.
- **p büyükse, H₀ doğrudur denemez.** p = 0,40 "fark yok" anlamına gelmez; yalnızca mevcut veriyle fark gösterilemedi demektir. Yani "reddedilemedi" ile "kabul edildi" aynı şey değildir.
- **Anlamlılık, önemlilik değildir.** Çok büyük bir örnekte, pratikte bir değeri olmayan minicik bir fark bile p < 0,05 verir. Bu yüzden etki büyüklüğünü de raporlamak gerekir; bir ölçüsü Cohen'in d'sidir: d = (μ₁ − μ₂) / σ_ortak.

### Hata türleri ve güç

Test her zaman hata yapabilir. **I. tip hata**, H₀ doğruyken onu reddetmektir; olasılığı α'dır. **II. tip hata**, H₁ doğruyken H₀'ı reddedememektir; olasılığı β'dır. **Güç** (power) 1 − β'dır: gerçek bir etkiyi yakalama olasılığı. Mühendislikte genelde güç %80 hedeflenir.

Şekil 49.10, bu üç kavramı tek bir resimde toplar. Mavi eğri H₀ altında z istatistiğinin dağılımıdır; bordo eğri ise gerçek bir etki (δ = 2,8) varken dağılımdır. Kritik değer 1,96'nın sağındaki kırmızı alan α'dır (I. tip hata). Bordo eğrinin kritik değerin solunda kalan kısmı β'dır (II. tip hata). Noktalı çizgi, bir deneyde gözlenen z = 2,3'tür; mavi eğrinin bu değerin sağında kalan kuyruğu, p-değerinin yarısıdır (iki yönlü test için tüm kuyruklar toplanır).

![Şekil 49.10: p-değeri ve hata türleri. Mavi: H₀ altında z dağılımı; bordo: H₁ altında (δ = 2,8). α = 0,05 (I. tip), β (II. tip) ve gözlenen z = 2,3.](gorseller/b49_p_hata.png)

Şekil, iki önemli sonucu gösterir. Birincisi, α'yı küçültmek (kritik değeri sağa itmek) β'yı büyütür; iki hata birbirine karşı bir takas içindedir. İkincisi, β'yı küçültmenin tek sağlıklı yolu örneklem büyüklüğünü artırmak ya da etki büyüklüğünü artıran bir tasarım yapmaktır.

### t testi ve permütasyon testi

Normal varsayımı altında iki örnek ortalamasını karşılaştırmanın standart yolu **Welch t-testidir**. t = (x̄₁ − x̄₂) / √(s₁²/n₁ + s₂²/n₂) ve serbestlik derecesi Welch–Satterthwaite formülüyle hesaplanır. Varyansların eşit olduğunu varsaymaz; bu yüzden eşit olmayan örneklerde daha güvenlidir. Aşağıdaki programda iki küçük normal örnek (n = 12 her biri, ortalamaları 10 ve 12, standart sapma 2) üretiyor ve Welch testini kendi yazdığımız kodla scipy'nin `ttest_ind` fonksiyonuyla karşılaştırıyoruz.

Normal varsayımı şüpheli olduğunda **permütasyon testi** kullanılır. Fikir şudur: H₀ doğruysa iki gruptaki etiketler anlamsızdır; yani tüm veriyi karıştırıp yeniden iki gruba bölsek, elde ettiğimiz fark dağılımı gözlenen farkı içermelidir. Veriyi B = 10 000 kez karıştırıp her seferinde farkı hesaplarsak, p-değeri gözlenen farkın mutlak değerden büyük ya da eşit çıkma oranıdır. Hiçbir dağılım varsayımı gerekmez; bu yüzden 49.11'de ölçüm verisine de uygulayacağız.

Aşağıdaki betik, bu iki testi ve diğer üç konuyu (çoklu karşılaştırma, A/B tasarımı ve gücün simülasyonu) içerir.

```python
import math
import random

from scipy import stats


def welch_t(a, b):
    """Welch t-istatistigi ve serbestlik derecesi (Satterthwaite)."""
    na, nb = len(a), len(b)
    ma, mb = sum(a) / na, sum(b) / nb
    va = sum((x - ma) ** 2 for x in a) / (na - 1)
    vb = sum((x - mb) ** 2 for x in b) / (nb - 1)
    se2 = va / na + vb / nb
    t = (ma - mb) / math.sqrt(se2)
    df = se2**2 / (
        (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)
    )
    p = 2 * stats.t.sf(abs(t), df)  # iki yonlu p-degeri
    return t, df, p
```

```python
def permutasyon(a, b, B=10_000, seed=49):
    """Iki orneklik permutasyon testi (ortalama farki)."""
    rnd = random.Random(seed)
    gozlenen = abs(sum(a) / len(a) - sum(b) / len(b))
    havuz = a + b
    na = len(a)
    say = 0
    for _ in range(B):
        rnd.shuffle(havuz)
        fark = abs(
            sum(havuz[:na]) / na - sum(havuz[na:]) / (len(havuz) - na)
        )
        if fark >= gozlenen:
            say += 1
    return gozlenen, (say + 1) / (B + 1)
```

```python
def cokluk_karsilastirma(deney=20_000, k=20, seed=49):
    """k test, H0 dogru: en az birinin p<0.05 olma orani."""
    rnd = random.Random(seed)
    en_az_bir = 0
    bonf = 0
    for _ in range(deney):
        pv = []
        for _ in range(k):
            x = [rnd.gauss(0, 1) for _ in range(30)]
            m = sum(x) / 30
            s = math.sqrt(sum((t - m) ** 2 for t in x) / 29)
            t = m / (s / math.sqrt(30))
            pv.append(2 * stats.t.sf(abs(t), 29))
        if min(pv) < 0.05:
            en_az_bir += 1
        if min(pv) < 0.05 / k:
            bonf += 1
    return en_az_bir / deney, bonf / deney
```

```python
def ab_orneklem(p1, p2, alfa=0.05, guc=0.80):
    """Iki oran icin orneklem buyuklugu (grup basina)."""
    za = stats.norm.ppf(1 - alfa / 2)
    zb = stats.norm.ppf(guc)
    pb = (p1 + p2) / 2
    pay = za * math.sqrt(2 * pb * (1 - pb)) + zb * math.sqrt(
        p1 * (1 - p1) + p2 * (1 - p2)
    )
    return math.ceil((pay / (p2 - p1)) ** 2)


def guc_simulasyonu(n, delta, deney=10_000, seed=49):
    """Iki kosullu normal: sapma delta. Guc = P(p < 0.05 | H1)."""
    rnd = random.Random(seed)
    hit = 0
    for _ in range(deney):
        a = [rnd.gauss(0, 1) for _ in range(n)]
        b = [rnd.gauss(delta, 1) for _ in range(n)]
        _, _, p = welch_t(a, b)
        hit += p < 0.05
    return hit / deney
```

```python
def main():
    # Ornek: iki kucuk olcum serisi (rastgele, tohum 49).
    rnd = random.Random(49)
    a = [rnd.gauss(10.0, 2.0) for _ in range(12)]
    b = [rnd.gauss(12.0, 2.0) for _ in range(12)]
    t, df, p = welch_t(a, b)
    print("Welch: t=%.4f df=%.3f p=%.5f" % (t, df, p))
    tt = stats.ttest_ind(a, b, equal_var=False)
    print("scipy: t=%.4f p=%.5f" % (tt.statistic, tt.pvalue))
    g, pp = permutasyon(a, b)
    print("Permutasyon: gozlenen fark=%.4f p=%.4f" % (g, pp))

    en, bonf = cokluk_karsilastirma()
    print(
        "20 test, H0 dogru: p<0.05 orani = %.4f (teorik %.4f)"
        % (en, 1 - 0.95**20)
    )
    print("Bonferroni (0.05/20): en az bir hata = %.4f" % bonf)

    n = ab_orneklem(0.10, 0.12)
    print("A/B: p1=0.10 p2=0.12 -> grup basina n = %d" % n)
    print(
        "Guc simulasyonu (n=%d, delta fark=0.8 sigma): %.3f"
        % (25, guc_simulasyonu(25, 0.8))
    )


if __name__ == "__main__":
    main()
```

```term
$ python b49_h_hipotez.py
Welch: t=-0.7726 df=21.630 p=0.44814
scipy: t=-0.7726 p=0.44814
Permutasyon: gozlenen fark=0.5656 p=0.4459
20 test, H0 dogru: p<0.05 orani = 0.6429 (teorik 0.6415)
Bonferroni (0.05/20): en az bir hata = 0.0491
A/B: p1=0.10 p2=0.12 -> grup basina n = 3841
Guc simulasyonu (n=25, delta fark=0.8 sigma): 0.793
```

Çıktının ilk iki satırı Welch testini iki kez verir: kendi formülümüz ile scipy aynı t (−0,7726) ve aynı p (0,44814) değerini bulur. Üçüncü satır aynı veriye permütasyon testi uygular; p = 0,4459, t-testiyle yakın sonuç verir. Bu örnekte gerçek fark 2 birimdir ama 12'lik örneklerle bunu güvenle gösteremeyiz; bu, düşük gücün tipik bir sonucudur.

### Çoklu karşılaştırma: 20 testte bir "anlamlı" bulgu

Bir deneyde 20 farklı metrik ölçüp her birine ayrı bir test uygularsan ne olur? Her test için H₀ doğru olsa bile, en az birinin p < 0,05 çıkma olasılığı 1 − 0,95²⁰ = 0,6415'tir. Yani hiçbir etki olmasa bile, dörtte üçe yakın bir ihtimalle "anlamlı" bir bulgu bulursun. Betiğin simülasyonu bunu 20 000 deneyle doğruladı: oran 0,6429. Bu, **çoklu karşılaştırma** (multiple comparisons) problemidir ve dikkatsiz bir ölçüm kültürünün en yaygın yanılgısıdır.

Çözümlerden biri **Bonferroni düzeltmesidir**: her testi α/k düzeyinde yap (burada 0,05 / 20 = 0,0025). Bu, en az bir yanlış alarm olasılığını α'da tutar; simülasyonumuzda bu olasılık 0,0491 çıktı. Bonferroni tutucu bir yöntemdir; test sayısı çoksa güç ciddi biçimde düşer. Daha ince yöntemler (Holm, Benjamini–Hochberg) genel bilgi olarak bilinir ve yanlış keşif oranını kontrol ederler.

Buna bağlı bir tuzak da **p-hacking** (p-avcılığı)'dir: veriye bakıp anlamlı çıkana kadar ek veri toplamak ya da testi değiştirmek. Her bakışta %5'lik bir şans eklenir. Bu tuzağın büyüklüğünü 49.12'deki bakıp-durdurma simülasyonunda ölçeceğiz: on kez bakıp ilk anlamlı sonuçta durmak, H₀ doğruyken yanlış alarm oranını yaklaşık 0,2'ye çıkarıyor.

### A/B testi: örneklem büyüklüğünü önceden hesapla

A/B testi, iki sürümü (kontrol ve deney) rastgele iki gruba ayırıp bir metriği karşılaştırmaktır. Kullanıcı dönüşüm oranı gibi bir **oran** için, iki oranın farkını anlamlı yakalamak istiyorsan örneklem büyüklüğünü önceden hesaplamalısın. Formül, iki yönlü testte α ve gücü hedefleyen bir standart formüldür:

n = ((z(α/2) √(2p̄(1 − p̄)) + z(β) √(p₁(1 − p₁) + p₂(1 − p₂))) / (p₂ − p₁))², p̄ = (p₁ + p₂) / 2.

Burada z(α/2) = 1,96 (α = 0,05), z(β) = 0,8416 (güç %80). Dönüşüm oranı p₁ = 0,10'dan p₂ = 0,12'ye çıkan bir değişikliği yakalamak için grup başına n = 3841 kullanıcı gerekir. Bu sayı küçük bir fark için büyüktür; bu yüzden tasarıma başlamadan önce hesap yapılır, veriye bakıp "yeterli" demek yerine.

Son satır, t-testi için gücün bir simülasyonudur: grup başına 25 örnek ve gerçek fark 0,8σ (Cohen'in d = 0,8'i, "büyük etki") ile gücü 0,793 buluyoruz; yani %80'e yakın. Bu, büyük etkiyi yakalamak için grup başına yaklaşık 25 örneğin yettiğini gösterir. Küçük etkiyi (d = 0,2) yakalamak için ise yüzlerce örnek gerekir; güç ile etki büyüklüğü arasındaki ilişki, örneklem büyüklüğü hesabının kalbidir.

**Mühendislik notu.** Bir yazılım sürümünün hız farkını ölçerken, A/B yerine "önce ve sonra" karşılaştırması yaparsan, zaman etkisini ve ortam değişikliğini ayıramazsın. Rastgele atama, nedensel bir sonuç için gerekli koşuldur. Bölüm 57'de deney tasarımını bu temel üzerine kuracağız.

## 49.11 Mühendislik ölçümü: ortalama, medyan ve kuyruk

Mühendislikte bir performans sayısı nadiren tek başına anlamlıdır. Bir servisin "ortalama yanıt süresi 20 ms" olması, bazı isteklerin 2 saniye sürmediği anlamına gelmez. Gecikme, arıza süresi, ağ paketi boyutu gibi büyüklükler genelde **sağa çarpıktır**: çoğu değer küçük, az sayıda değer çok büyüktür. Bu tür verilerde ortalama, yaşanan deneyimi yanıltır; medyan (p50) tipik durumu, p90 ve p99 ise kuyruğu anlatır. Bölüm 41'de SLO'ları p99 üzerinden tanımlamıştık; burada aynı düşünceyi istatistiksel olarak sağlamlaştıracağız.

Bu bölümde Bölüm 44'teki kesme gecikmesi benzetiminin çıktısını kullanıyoruz. Veri, `b44_gecikme.csv` dosyasındaki kesme kaynakları için **çevrim** cinsinden gecikmeler içerir. Önemli bir not: bu bir donanım ölçümü değil, Bölüm 44'teki cevrim düzeyi benzetiminin çıktısıdır; yöntemi göstermek için kullanıyoruz, bir donanımın gerçek ölçümü olarak değil. İki kaynağı karşılaştıracağız: zamanlayıcı kesmesi (TIM, n = 283) ve ADC kesmesi (n = 723).

İlk bakışta şu tabloyu görürsün:

| Kaynak | n | ortalama | p50 | p90 | p99 | en büyük |
|---|---|---|---|---|---|---|
| TIM | 283 | 42,81 | 12,0 | 110,8 | 284,6 | 538 |
| ADC | 723 | 14,01 | 12,0 | 20,0 | 47,0 | 65 |

İki kaynağın **medyanı aynı** (12 çevrim)! Buna rağmen ortalamaları 3 kat farklı, p99 değerleri 6 kat farklı. Hangisi "daha hızlı"? Cevap ölçüye bağlıdır: tipik durumda iki kaynak aynıdır; kuyrukta TIM belirgin biçimde daha kötüdür. Gerçek bir sistemde, bu fark bir kesmenin diğerini ne sıklıkla geciktirdiğini belirler. Bu yüzden bir ölçüm raporunda tek bir sayı yetmez: n, p50, p90, p99 ve en büyük değer birlikte verilmelidir.

Yüzdelik hesabı için iki kural gerekir. Sıralı bir listede p yüzdeliği, (n − 1)p konumundaki değerdir; tam bir konumda değilse komşu iki değer arasında doğrusal enterpolasyon yapılır. Bu, numpy'nin varsayılanıyla aynıdır. Aşağıdaki programın `yuzdelik` fonksiyonu bunu uygular.

```python
import csv
import os
import math
import random

VERI = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "..",
    "engine",
    "veri",
)


def oku(tur, kaynak):
    with open(VERI + "/b44_gecikme.csv", encoding="utf-8") as f:
        return [
            float(r["gecikme_cevrim"])
            for r in csv.DictReader(f)
            if r["tur"] == tur and r["kaynak"] == kaynak
        ]
```

```python
def yuzdelik(v, p):
    """Dogrusal enterpolasyonlu yuzdelik (numpy varsayilani)."""
    s = sorted(v)
    h = (len(s) - 1) * p
    lo = math.floor(h)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (h - lo) * (s[hi] - s[lo])


def medyan(v):
    return yuzdelik(v, 0.5)


def ortalama(v):
    return sum(v) / len(v)


def ozet(ad, v):
    print(
        "%-12s n=%4d ort=%6.2f med=%5.1f "
        "p90=%6.1f p99=%6.1f max=%5.0f"
        % (
            ad,
            len(v),
            ortalama(v),
            medyan(v),
            yuzdelik(v, 0.9),
            yuzdelik(v, 0.99),
            max(v),
        )
    )
```

### Farkı anlamlı mı yapmak: üç ölçü, üç cevap

Fark bir sayı olarak ölçüldüğünde, o sayının ne olduğunu seçmek zorundasın. Bu bölümde üç istatistiği karşılaştırıyoruz: ortalama farkı, medyan farkı ve p99 farkı. Her biri için aynı iki araçla belirsizliği ölçeriz: permütasyon testi (p-değeri) ve bootstrap güven aralığı (farkın yüzde 95'i). Ayrıca iki etki büyüklüğü hesaplıyoruz: **Cohen'in d**'si (ortalama farkının ortak standart sapmaya oranı) ve **Cliff'in δ**'sı (bir ölçümün diğerinden büyük olma olasılığı farkı). Cliff'in δ'sı dağılım şekline bakmaz, bu yüzden çarpık verilerde d'den daha güvenilirdir.

```python
def cohen_d(a, b):
    va = sum((x - ortalama(a)) ** 2 for x in a) / (len(a) - 1)
    vb = sum((x - ortalama(b)) ** 2 for x in b) / (len(b) - 1)
    sp = math.sqrt(
        ((len(a) - 1) * va + (len(b) - 1) * vb)
        / (len(a) + len(b) - 2)
    )
    return (ortalama(a) - ortalama(b)) / sp


def cliff_delta(a, b):
    """P(A > B) - P(A < B), sayarak hesaplanir. Olcek-bagimsiz."""
    gt = lt = 0
    for x in a:
        for y in b:
            if x > y:
                gt += 1
            elif x < y:
                lt += 1
    return (gt - lt) / (len(a) * len(b))
```

```python
def permutasyon(a, b, istat, B=10_000, seed=49):
    rnd = random.Random(seed)
    gozlenen = abs(istat(a) - istat(b))
    havuz = a + b
    na = len(a)
    say = 0
    for _ in range(B):
        rnd.shuffle(havuz)
        if abs(istat(havuz[:na]) - istat(havuz[na:])) >= gozlenen:
            say += 1
    return gozlenen, (say + 1) / (B + 1)


def bootstrap_fark(a, b, istat, B=10_000, seed=49):
    rnd = random.Random(seed)
    fark = []
    for _ in range(B):
        ra = [a[rnd.randrange(len(a))] for _ in range(len(a))]
        rb = [b[rnd.randrange(len(b))] for _ in range(len(b))]
        fark.append(istat(ra) - istat(rb))
    fark.sort()
    return fark[int(0.025 * B)], fark[int(0.975 * B) - 1]
```

```python
def main():
    tim = oku("kesme", "TIM")
    adc = oku("kesme", "ADC")
    print("== Ozet (cevrim) ==")
    ozet("kesme TIM", tim)
    ozet("kesme ADC", adc)

    print("== Ortalama farki (TIM - ADC) ==")
    print("Fark ort: %.3f" % (ortalama(tim) - ortalama(adc)))
    g, p = permutasyon(tim, adc, ortalama)
    print("Permutasyon (ortalama): gozlenen=%.3f  p=%.5f" % (g, p))
    lo, hi = bootstrap_fark(tim, adc, ortalama)
    print("Bootstrap GA (ortalama farki): [%.2f, %.2f]" % (lo, hi))
    print("Cohen d = %.3f" % cohen_d(tim, adc))
    print("Cliff delta = %.3f" % cliff_delta(tim, adc))

    print("== Medyan farki ==")
    g, p = permutasyon(tim, adc, medyan)
    print("Permutasyon (medyan): gozlenen=%.3f  p=%.5f" % (g, p))
    lo, hi = bootstrap_fark(tim, adc, medyan)
    print("Bootstrap GA (medyan farki): [%.2f, %.2f]" % (lo, hi))

    print("== p99 farki ==")
    g, p = permutasyon(tim, adc, lambda v: yuzdelik(v, 0.99))
    print("Permutasyon (p99): gozlenen=%.3f  p=%.5f" % (g, p))


if __name__ == "__main__":
    main()
```

```term
$ python b49_i_olcum.py
== Ozet (cevrim) ==
kesme TIM    n= 283 ort= 42.81 med= 12.0 p90= 110.8 p99= 284.6 max=  538
kesme ADC    n= 723 ort= 14.01 med= 12.0 p90=  20.0 p99=  47.0 max=   65
== Ortalama farki (TIM - ADC) ==
Fark ort: 28.801
Permutasyon (ortalama): gozlenen=28.801  p=0.00010
Bootstrap GA (ortalama farki): [21.48, 36.86]
Cohen d = 0.815
Cliff delta = 0.318
== Medyan farki ==
Permutasyon (medyan): gozlenen=0.000  p=1.00000
Bootstrap GA (medyan farki): [0.00, 0.00]
== p99 farki ==
Permutasyon (p99): gozlenen=237.600  p=0.00010
```

Çıktı şunları söylüyor. Ortalama farkı 28,80 çevrimdir ve permütasyon testinin p-değeri 0,00010'dur. Bu değer, B = 10 000 permütasyonla elde edilebilecek en küçük p-değeridir (1 / (B + 1)); gerçek p-değeri bundan daha küçük olabilir ama bu yöntemle daha fazla hassasiyet alamayız. Ortalama farkı için bootstrap güven aralığı [21,48; 36,86] olduğundan, fark sıfırın çok uzağındadır. Cohen'in d = 0,815 büyük bir etki, Cliff'in δ = 0,318 ise "TIM'den gelen bir gecikmenin ADC'den büyük olma olasılığı, tersi olasılığından yaklaşık 0,32 fazla" demektir.

Medyan farkı ise tam tersini söylüyor: permütasyon p-değeri 1,0 ve bootstrap aralığı [0,00; 0,00]. Sebebi, verinin **ayrık ve yinelenen** olmasıdır. Medyan çoğu durumda tam olarak 12 çevrimdir ve yeniden örneklemelerde neredeyse her zaman 12 çıkar; bu yüzden medyan farkının dağılımı tek bir noktaya çöker. Burada bootstrap yüzdelik aralığı, teorik olarak "sıfır genişlikte" bir aralık verir ve bu bir hata değil, verinin bir özelliğidir. Bu tuzağın sonucu şudur: ayrık veride medyan için güven aralığı hesaplamak, sanılandan çok daha dikkatli bir iş olmalıdır.

p99 farkı ise permütasyonla 237,6 olarak ölçüldü ve p-değeri 0,00010'dur. Kuyruk farkı burada en büyük ve en açıklayıcıdır: ADC'nin p99'u, TIM'in kuyruk davranışını yaşamaz. Sistem tasarımında (Bölüm 41), hedefin p99 olması bu yüzden TIM'i sakinleştirmeyi zorunlu kılar; ortalama bu kararı tek başına verdirmez.

### Bu raporu nasıl yazarsın?

Bir performans farkı raporlarken yalnızca "A daha hızlı" yazmak yetmez. Üç şey gerekir: örnek büyüklükleri (n), dağılımın özeti (p50, p90, p99, en büyük) ve farkın belirsizliği (güven aralığı ve permütasyon p-değeri). Üstelik ortalamayı mı, medyanı mı, yoksa p99'u mu kullandığını açıkça belirtmelisin; çünkü seçtiğin istatistik sonucu değiştirebilir. Bölüm 41'deki yük dengeleme karşılaştırmasında da aynı kural geçerlidir: tek bir koşudan elde edilen bir p99 farkı, bootstrap ve permütasyonla doğrulanmadan karar için kullanılmamalıdır.

Ayrıca ölçümün kendisi kararsız olabilir: aynı deneyi iki kez yaparsan p99 değerleri birbirinden farklı çıkabilir. Bölüm 39'da kararsız testleri anlatırken bunun ölçüm dünyasındaki karşılığını görmüştük; burada onu sayılarla ölçüyoruz.

## 49.12 Makine öğrenmesi köprüsü: füzyon, güncelleme, çapraz entropi

Bu bölümün istatistiği, makine öğrenmesinin dilidir. Bir sınıflandırıcı bize bir etiket değil, bir olasılık verebilir: p(y = 1 | x) = 0,93. Bu sayının iki özelliği önemlidir: doğru olmalı (kalibrasyon) ve bu olasılığa dayanan kayıp fonksiyonu eğitimi yönlendirmeli. Burada dört köprü kuruyoruz: sensör füzyonunun 1B Bayesçi hali, Beta güncellemesinin bir veri akışındaki davranışı, çapraz entropinin log-olabilirlik olarak yorumu ve bakıp durdurma tuzağının sayısal ölçümü. Hepsi tek bir betikte, `b49_j_kopru.py` içinde.

### Sensör füzyonu: 1B Bayesçi güncelleme

Bir İHA'nın yüksekliği sabit ama bilinmeyen bir h değeridir. Önceden bilgimiz h ~ N(5, 4) (ortalama 5 m, varyans 4 m²). Sonra iki bağımsız sensör ölçüm yapıyor: z₁ = 6,2 (varyans 4), z₂ = 4,9 (varyans 1). Her iki ölçüm de normal gürültülü olduğunda sonsal dağılım da normal olur ve formül kapalıdır.

Kesinlik (precision, varyansın tersi) kavramını kullanırsak işler sadeleşir: sonsal kesinlik, önsel ve ölçümlerin kesinliklerinin toplamıdır; sonsal ortalama ise her birinin kesinliğiyle ağırlıklandırılmış ortalamadır:

1/σ²_son = 1/σ²_önsel + ∑ 1/σ²ᵢ,   μ_son = σ²_son · (μ_önsel/σ²_önsel + ∑ zᵢ/σ²ᵢ).

Sayılarla: kesinlikler 0,25 (önsel), 0,25 (z₁) ve 1 (z₂) toplamı 1,5 eder; sonsal varyans 1/1,5 = 0,6667, sonsal standart sapma 0,8165'tir. Sonsal ortalama (5 · 0,25 + 6,2 · 0,25 + 4,9 · 1) / 1,5 = 5,1333'tür. Daha kesin sensöre (z₂) daha çok ağırlık verildi, ama zayıf sensör (z₁) da katkı yaptı; sonsal belirsizlik her iki ölçümden de küçüldü.

Aşağıdaki betik, bu formülü `fuzyon` fonksiyonunda uygular. Ardından, önselsiz iki ölçümün ağırlıklı birleşiminin varyansını simülasyonla kontrol eder: 1/(1/4 + 1) = 0,8 olmalıdır.

```python
import math
import random

import numpy as np
from scipy import stats


def fuzyon():
    """Iki sensor, onsel N(5,4): z1=6.2 (s1=2), z2=4.9 (s2=1)."""
    m0, v0 = 5.0, 4.0
    z = [(6.2, 4.0), (4.9, 1.0)]
    prec = 1 / v0
    mu = m0 * prec
    for zi, vi in z:
        prec += 1 / vi
        mu += zi / vi
    print(
        "Fuzyon: sonsal ortalama = %.4f, sonsal sigma = %.4f"
        % (mu / prec, math.sqrt(1 / prec))
    )
    rnd = np.random.default_rng(49)
    x = rnd.normal(5.0, 1.0, 100_000)
    # Gercek x ~ N(5, 1); sensor hatalari sigma1=2, sigma2=1
    y1 = x + rnd.normal(0, 2, x.size)
    y2 = x + rnd.normal(0, 1, x.size)
    p = 1 / 4.0 + 1 / 1.0
    birlesik = (y1 / 4.0 + y2 / 1.0) / p
    print(
        "  Simulasyon: var(birlesik-x) = %.4f "
        "(teorik 1/(1/4+1) = %.4f)" % (np.var(birlesik - x), 1 / p)
    )
```

Betikteki simülasyon, bu formülün ikinci kısmını test eder. Çıktıda 0,8001 gözlenmesi, teorik 0,8 ile uyumludur. Bu, 1B Kalman filtresinin (Bölüm 62) ölçüm güncellemesinin özüdür; zamanla değişen durumda aynı formül bir tahmin adımıyla birleşir.

### Beta güncellemesi: veriyle önseli eritmek

49.8'de anlattığımız Beta–Bernoulli güncellemesini bir dizi üzerinden izleyelim: önsel Beta(2, 2) ve on gözlem (1, 0, 0, 1, 0, 0, 0, 1, 0, 0). Her adımda sonsal parametreleri, sonsal ortalamayı ve MAP değerini yazdırıyoruz. Aşağıdaki fonksiyon bu döngüyü yapar.

Çıktıda görülen şey, sonsal ortalamanın veriye doğru hareket etmesi ve önselin etkisinin veri çoğaldıkça azalmasıdır. Bu kayma, öğrenmenin istatistiksel tanımıdır: yeni veri geldikçe belirsizlik azalır ve tahmin veriye yaklaşır.

```python
def beta_guncelleme():
    a, b = 2, 2
    yazi = [1, 0, 0, 1, 0, 0, 0, 1, 0, 0]
    print("Beta(2,2) on dagilimi, sirayla gozlemler:")
    print(" n  k   a  b   sonsal_ort   MAP")
    k = 0
    for n, x in enumerate(yazi, 1):
        k += x
        a2, b2 = 2 + k, 2 + (n - k)
        ort = a2 / (a2 + b2)
        mp = (a2 - 1) / (a2 + b2 - 2)
        print(
            "%2d %2d %3d %2d   %.4f     %.4f"
            % (n, k, a2, b2, ort, mp)
        )
```

### Çapraz entropi ve kalibrasyon

İkili bir etiketi y ∈ {0, 1} ve modelin tahminini p ∈ (0, 1) ile gösterelim. Bernoulli modelinde bir gözlemin olabilirliği p^y (1 − p)^(1 − y)'dir. Negatif log-olabilirlik bunun eksi logaritmasıdır:

−ln[p^y (1 − p)^(1 − y)] = −[y ln p + (1 − y) ln(1 − p)].

Bu, ikili çapraz entropi kaybıdır. n örnek için ortalamasını alırsak, **çapraz entropi = negatif ortalama log-olabilirlik** olur. Bu özdeşlik, sınıflandırıcı eğitiminin bir olasılık modelinin en büyük olabilirlik kestirimi olduğunu söyler (Bölüm 51'de bilgi teorisi tarafından bu kaybın kökenini derinleştireceğiz). Aşağıdaki fonksiyon bu özdeşliği 2000 rastgele örnekte sayısal olarak doğrular ve aynı zamanda kalibrasyonu da sınar.

```python
def capraz_entropi():
    """Bernoulli: CE = -(1/n) sum [y log p + (1-y) log(1-p)]."""
    rnd = random.Random(49)
    n = 2000
    p = [rnd.random() for _ in range(n)]
    y = [1 if rnd.random() < q else 0 for q in p]
    ce = (
        -sum(
            t * math.log(q) + (1 - t) * math.log(1 - q)
            for t, q in zip(y, p)
        )
        / n
    )
    ll = sum(
        math.log(q) if t else math.log(1 - q) for t, q in zip(y, p)
    )
    print("Capraz entropi = %.6f  -ll/n = %.6f" % (ce, -ll / n))
    # Kalibrasyon: ayni p'yi karesi ile bozarak asiri ozguvenli model.
    bozuk = [q**0.3 for q in p]
    ce2 = (
        -sum(
            t * math.log(q) + (1 - t) * math.log(1 - q)
            for t, q in zip(y, bozuk)
        )
        / n
    )
    print("Kalibre model CE=%.4f  Bozuk (p^0.3) CE=%.4f" % (ce, ce2))
    print(
        "  Ortalama: kalibre tahmin=%.4f  gozlenen=%.4f"
        % (sum(p) / n, sum(y) / n)
    )
```

**Kalibrasyon** şudur: bir model "bu grubun her birinde p = 0,7" diyorsa, o grubun yaklaşık %70'inin gerçekten pozitif olması beklenir. Kalibrasyon, sıralama yeteneğinden (AUC gibi) ayrı bir özelliktir: bir model sınıfları doğru sıralayıp her olasılığı iki katına çıkarabilir. Betikte iki model karşılaştırılıyor: gerçek olasılıkları olan "kalibre" model ve aynı sıralamayı koruyan ama olasılıkları p^0,3 ile bozulmuş model. Kalibre modelin çapraz entropisi 0,4887 iken bozuk modelin 0,7261'dir; sıralama aynı kalmasına rağmen. Ortalama tahmin (0,4871) ile gözlenen pozitif oranı (0,4845) birbirine yakındır. Kalibrasyonun ayrıntıları Bölüm 57'de ele alınacak.

### Bakıp durdurma tuzağı

49.10'da p-hacking'i anlattık. Burada onun sayısını ölçüyoruz. H₀ doğru (aynı normal dağılım) ve her 10 gözlemde bir tek-örnek t-testi yapılıyor; ilk anlamlı sonuçta durulursa (en fazla 100 gözlem). Sabit n = 100'de tek bir bakışla testin yanlış alarm oranı 0,05'tir. Ama on kez bakıp ilk anlamlı sonuçta durduğunda oran 0,2052'ye çıkıyor, yani dört katına yakın. Bu, "veriye bakıp yeterince anlamlı görünceye kadar devam etmek" yönteminin, yanlış sonuç üretme olasılığını ne kadar artırdığını gösterir.

```python
def bakip_durdurma(deney=20_000, seed=49):
    """H0 dogru; her 10 gozlemde bir t-testi; ilk anlamlida dur."""
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 1, (deney, 100))
    mask = np.zeros(deney, dtype=bool)
    for k in range(10, 101, 10):
        sub = x[:, :k]
        m = sub.mean(axis=1)
        s = sub.std(axis=1, ddof=1)
        t = m / (s / math.sqrt(k))
        p = 2 * stats.t.sf(np.abs(t), k - 1)
        mask = mask | (p < 0.05)
    print(
        "Bakip durdurma: en az bir bakista p<0.05: %.4f "
        "(sabit n=100: 0.05)" % np.mean(mask)
    )
```

```python
def main():
    fuzyon()
    beta_guncelleme()
    capraz_entropi()
    bakip_durdurma()


if __name__ == "__main__":
    main()
```

Betiğin tam çıktısı şöyledir: füzyon sonuçları, Beta dizisi, çapraz entropi ve kalibrasyon, bakıp durdurma.

```term
$ python b49_j_kopru.py
Fuzyon: sonsal ortalama = 5.1333, sonsal sigma = 0.8165
  Simulasyon: var(birlesik-x) = 0.8001 (teorik 1/(1/4+1) = 0.8000)
Beta(2,2) on dagilimi, sirayla gozlemler:
 n  k   a  b   sonsal_ort   MAP
 1  1   3  2   0.6000     0.6667
 2  1   3  3   0.5000     0.5000
 3  1   3  4   0.4286     0.4000
 4  2   4  4   0.5000     0.5000
 5  2   4  5   0.4444     0.4286
 6  2   4  6   0.4000     0.3750
 7  2   4  7   0.3636     0.3333
 8  3   5  7   0.4167     0.4000
 9  3   5  8   0.3846     0.3636
10  3   5  9   0.3571     0.3333
Capraz entropi = 0.488742  -ll/n = 0.488742
Kalibre model CE=0.4887  Bozuk (p^0.3) CE=0.7261
  Ortalama: kalibre tahmin=0.4871  gozlenen=0.4845
Bakip durdurma: en az bir bakista p<0.05: 0.2052 (sabit n=100: 0.05)
```

Bu bölümde gördüğün dört fikir, makine öğrenmesinin her bölümünde yeniden karşına çıkacak: olasılık çıktısı (Bölüm 57), log-olabilirlik kaybı (Bölüm 51 ve 58), eşlenik güncellemeler ve füzyon (Bölüm 62), ve deney disiplini (Bölüm 57 ve 79). Bakıp durdurma tuzağı ise ML yarışmalarında ve makale sonuçlarında en sık görülen istatistiksel hatalardan biridir.

## Çözümlü Örnekler

Her örnek Bölüm 5'teki altı adımı izler: anla, örnekle, kaba çöz, örüntü, iyileştir, doğrula. Doğrulama adımında elle izlenebilir bir tablo vardır. Her örneğin sonundaki soruyu kâğıtta çöz; yapay zekâ kullanmadan cevaplayabildiğin an, konu sende yerleşmiş demektir.

### Örnek 1 (★): Alarmın gerçek tehdit olma olasılığı

**Adım 1 — Anla.** Bir İHA'nın hedef tanıma alarmı, 10 000 olaydan 200'ünde gerçek bir tehdide karşılık geliyor. Gerçek tehditlerin %95'inde alarm veriliyor; tehdit olmayan olayların %3'ünde de yanlış alarm veriliyor. Soru: bir alarm verildiğinde, gerçek tehdit olma olasılığı nedir? Ve ikinci, bağımsız bir sensör de alarm verirse bu olasılık nasıl değişir?

**Adım 2 — Örnekle.** Önce küçük bir kontrol: 10 000 olay yerine 1000 olay düşünelim. Yaklaşık 20 tehdit olur; bunların 19'u alarm verir. Tehdit olmayan 980 olayın %3'ü, yani yaklaşık 29'u, yanlış alarm verir. Alarm sayısı 48'dir; bunların 19'u gerçek. Oran 19/48 ≈ 0,40, yani 10 000'lik hesabın sonucuna yakın.

**Adım 3 — Kaba çöz.** Doğrudan Bayes: P(tehdit | alarm) = P(alarm | tehdit) P(tehdit) / P(alarm). Pay: 0,95 · 0,02 = 0,019. Payda, toplam olasılıkla: 0,95 · 0,02 + 0,03 · 0,98 = 0,019 + 0,0294 = 0,0484. Sonuç: 0,019 / 0,0484 ≈ 0,3926.

**Adım 4 — Örüntü.** Pay ve paydadaki ilk terimin aynı olduğunu fark et: 0,019 "gerçek alarm" kütlesidir. Paydanın ikinci terimi, yanlış alarm kütlesidir (0,0294). Yanlış alarmın kütlesi, tehdit olmayan olayların çokluğu (%98) nedeniyle büyüktür; oranı %3 gibi küçük bir sayı bile, büyük bir çoğunlukla çarpılınca gerçek alarmı geride bırakır. Bu, taban oranı yanılgısının mekanizmasıdır.

**Adım 5 — İyileştir.** İkinci bir sensör bağımsız olarak aynı hedefi tarasın ve iki sensörün de alarm vermesini şart koşalım. Gerçek tehditte iki alarm olasılığı 0,95² = 0,9025; tehdit olmayanda 0,03² = 0,0009. Pay: 0,9025 · 0,02 = 0,01805. Payda: 0,01805 + 0,0009 · 0,98 = 0,01805 + 0,000882 = 0,018932. Sonuç: 0,01805 / 0,018932 ≈ 0,953. İki bağımsız sensör, alarmın güvenilirliğini %39'dan %95'e çıkarır. Ama bu hesap, iki sensörün hatalarının bağımsız olduğunu varsayar; gerçekte aynı yanılsamaya (yağmur, parlama) iki sensör birden kapılabilir ve kazanç düşer.

**Adım 6 — Doğrula.** Aşağıdaki frekans tablosu aynı sonucu sayarak verir:

| Durum | Tehdit var (200) | Tehdit yok (9 800) | Toplam |
|---|---|---|---|
| Alarm | 190 | 294 | 484 |
| Alarm yok | 10 | 9 506 | 9 516 |
| İki sensör alarm | 180,5 | 8,8 | 189,3 |

İlk satır: P(tehdit | alarm) = 190 / 484 = 0,3926 (formülle aynı). Üçüncü satır: iki sensörün birlikte alarm verdiği olaylar arasında gerçek tehdit oranı 180,5 / 189,3 ≈ 0,953. Bu iki sayı, Bayes formülünün ve sayımın aynı sonucu verdiğini gösterir.

**Bunu AI'sız yazabilir misin?** Tehdit oranı %0,5, duyarlılık %90 ve yanlış alarm oranı %2 olsun. Tek sensör alarmında gerçek tehdit olma olasılığını hesapla. Sonra aynı sistemde 10 000 olayı tabloya dök ve iki yöntemin sonucunu karşılaştır.

### Örnek 2 (★★): Saatte k paket kaybı: Poisson ve simülasyon

**Adım 1 — Anla.** Bir veri hattında paket kayıpları birbirinden bağımsız ve saatte ortalama 3 kayıp oluşturuyor. Soru: bir saat içinde hiç kayıp olmama olasılığı, tam 5 kayıp olma olasılığı ve en az 5 kayıp olma olasılığı nedir? Bu sonuçları bir simülasyonla da doğrulayabilir misin?

**Adım 2 — Örnekle.** Önce bir saatlik küçük bir örneği kağıtta izleyelim. Bir saatte kayıplar 0, 1, 2, 3, 4, 5, ... gibi değerler alabilir. 3 saat boyunca gözlenen kayıp sayıları 2, 4, 3 olsaydı, bu üç saatin ortalaması 3 olurdu. Ama tek üç saatlik veriden olasılık çıkmaz; bu yüzden formüle geçiyoruz.

**Adım 3 — Kaba çöz.** Poisson formülü P(k) = e^(−λ) λ^k / k! ve λ = 3 için: P(0) = e^(−3) ≈ 0,0498. P(1) = 3 · 0,0498 = 0,1494. P(2) = (9 / 2) · 0,0498 = 0,2240. P(3) = (27 / 6) · 0,0498 = 0,2240. P(4) = (81 / 24) · 0,0498 = 0,1680. P(5) = (243 / 120) · 0,0498 = 0,1008. En az 5 için tümleyen: 1 − (0,0498 + 0,1494 + 0,2240 + 0,2240 + 0,1680) = 1 − 0,8153 = 0,1847.

**Adım 4 — Örüntü.** Her P(k+1) / P(k) = λ / (k + 1) oranı bir önceki terimi verir. Bu oran k < λ − 1 iken 1'den büyüktür, dolayısıyla dizi artar; k = 2 ve k = 3 için oran 1'dir, yani iki tepe noktası vardır. Bu, λ tam sayıysa Poisson'un iki eşit tepeye sahip olabileceğini gösterir.

**Adım 5 — İyileştir.** Formülü doğrudan kullanmak yerine, süreci simüle edelim: olaylar arasındaki süreler Üstel(3) ile üretilir (Bölüm 49.4'teki Poisson–üstel bağlantısı) ve her saat içinde kaç olay oluştuğu sayılır. 100 000 saatlik bir simülasyon bu sayıları üretir. Bu, formülden bağımsız bir doğrulamadır. Betiğin ilk bölümü şöyledir:

```python
import math
import random

from scipy import stats


def ornek2_poisson(saat=100_000, lam=3.0, seed=49):
    """Poisson sureci: ardisik olaylar arasi Ustel(lam) bekleme.
    Her birim saat icinde kac olay oldugunu say."""
    rnd = random.Random(seed)
    sayilar = []
    for _ in range(saat):
        t = 0.0
        k = 0
        while True:
            t += rnd.expovariate(lam)
            if t > 1.0:
                break
            k += 1
        sayilar.append(k)
    n = len(sayilar)
    print("Simulasyon: %d saat, lam=%.1f" % (n, lam))
    for k in range(0, 6):
        emp = sayilar.count(k) / n
        teo = math.exp(-lam) * lam**k / math.factorial(k)
        print("  k=%d  simule=%.4f  teorik=%.4f" % (k, emp, teo))
    ge5 = sum(1 for s in sayilar if s >= 5) / n
    print(
        "  P(k>=5) simule=%.4f  teorik=%.4f"
        % (ge5, stats.poisson.sf(4, lam))
    )
    print("  ortalama=%.4f (lam=%.1f)" % (sum(sayilar) / n, lam))
```



**Adım 6 — Doğrula.** Aşağıdaki tablo, simülasyonun (100 000 saat) ve formülün değerlerini karşılaştırır. Simülasyon satırları, Örnek 3'ün sonundaki çıktının ilk bölümünden alınmıştır.

| k | simüle P(k) | teorik P(k) |
|---|---|---|
| 0 | 0,0493 | 0,0498 |
| 1 | 0,1478 | 0,1494 |
| 2 | 0,2239 | 0,2240 |
| 3 | 0,2266 | 0,2240 |
| 4 | 0,1666 | 0,1680 |
| 5 | 0,1014 | 0,1008 |
| ≥ 5 | 0,1857 | 0,1847 |

Tablo, her satırda simülasyonun teorik değere birkaç binde birlik farkla yaklaştığını gösterir. Simüle ortalama 3,0068 çıktı; teorik değer 3,0'dır. Poisson'un E[X] = Var(X) = λ özelliği, burada da gözlenen sayıların ortalamasıyla uyumludur.

**Bunu AI'sız yazabilir misin?** λ = 1,5 için P(0), P(1), P(2) ve P(≥3) değerlerini kağıtta hesapla. Sonra bu değerlerin toplamının 1 olduğunu doğrula. Son olarak, aynı hattın 10 saatlik toplam kaybının dağılımını tahmin et: bu bir Poisson mi, yoksa başka bir dağılım mı?

### Örnek 3 (★★): Arıza sürelerinden λ kestirimi ve bootstrap güven aralığı

**Adım 1 — Anla.** Bir sensörün on arızası arasındaki süreler (saat olarak) şunlar: 1,8; 0,4; 3,1; 2,2; 0,9; 5,6; 1,2; 0,7; 2,9; 1,5. Arızaların süreçinin üstel olduğunu varsayarak arıza oranı λ'yı kestir ve bu kestirimin 95% güven aralığını bootstrap ile hesapla.

**Adım 2 — Örnekle.** Toplam süre ∑x = 20,3 saattir. Bir kestirimin mantıklı olup olmadığını görmek için iki aday düşün: λ = 0,3 ve λ = 0,8. Ortalama süre 2,03 saat olduğuna göre, arıza oranı kabaca 1/2,03 ≈ 0,49 olmalıdır. λ = 0,8 çok hızlı bir arıza oranı olur ve veriye pek uymaz gibi görünür.

**Adım 3 — Kaba çöz.** Log-olabilirlik l(λ) = n ln λ − λ ∑x. Türev sıfıra eşitlenirse λ̂ = n / ∑x = 10 / 20,3 = 0,4926 bulunur. Ortalama süre 2,03 saat ise λ̂ = 1 / ortalama süre'dir; bu iki ifade aynıdır.

**Adım 4 — Örüntü.** λ̂, verinin tek bir özetine (toplam süre) bağlıdır. Yeni bir arıza süresi eklediğinde toplam değişir ve λ̂ kayar. n küçük olduğunda bu kayma büyüktür; bu da güven aralığının geniş olacağı anlamına gelir. Bunu bootstrap ile göreceğiz.

**Adım 5 — İyileştir.** Bootstrap'te on arıza süresinden yerine koyarak 10 gözlemlik yeniden örnekler çekiyoruz; her seferinde λ = n / ∑x ve ortalama süreyi hesaplıyoruz. 10 000 yeniden örnekte %2,5 ve %97,5 yüzdelikleri, λ için [0,3322; 0,8197] ve ortalama süre için [1,22; 3,01] saat olarak çıktı. Aralık geniş; bu, 10 gözlemin hâlâ çok az olduğunun işaretidir.

**Adım 6 — Doğrula.** Log-olabilirlik tablosu, λ̂ çevresinde l'nin en büyük olduğunu gösterir:

| λ | l(λ) = 10 ln λ − 20,3 λ |
|---|---|
| 0,3 | −18,1297 |
| 0,4926 | −17,0804 |
| 0,6 | −17,2883 |
| 0,8 | −18,4714 |

En büyük değer 0,4926'da (−17,0804) görülür. Türevin işaretini de kontrol et: λ = 0,3'te l′ = 10 / 0,3 − 20,3 ≈ 13,0 > 0 (artıyor); λ = 0,8'de l′ = 12,5 − 20,3 = −7,8 < 0 (azalıyor). Tepe bu iki değer arasındadır, beklendiği gibi.

Örnek 2 ile 3'ün betiğinin çıktısı aşağıdadır. Simülasyon tablosu, bu çıktının ilk sekiz satırından alınmıştır.

Betiğin ikinci bölümü, arıza süreleri üzerinden kestirim ve bootstrap yapar:

```python
def ornek3_mle_bootstrap(seed=49, B=10_000):
    sureler = [1.8, 0.4, 3.1, 2.2, 0.9, 5.6, 1.2, 0.7, 2.9, 1.5]
    n = len(sureler)
    s = sum(sureler)
    lam = n / s
    print(
        "n=%d  toplam=%.1f  MLE lambda=%.4f  ort=%.4f saat"
        % (n, s, lam, s / n)
    )
    for l in (0.3, 0.4926, 0.6, 0.8):
        ll = n * math.log(l) - l * s
        print("  l(%.4f) = %.4f" % (l, ll))
    rnd = random.Random(seed)
    lam_dag = []
    ort_dag = []
    for _ in range(B):
        ornek = [sureler[rnd.randrange(n)] for _ in range(n)]
        t = sum(ornek)
        lam_dag.append(n / t)
        ort_dag.append(t / n)
    lam_dag.sort()
    ort_dag.sort()
    print(
        "Bootstrap GA (lambda): [%.4f, %.4f]"
        % (lam_dag[int(0.025 * B)], lam_dag[int(0.975 * B) - 1])
    )
    print(
        "Bootstrap GA (ortalama sure): [%.4f, %.4f]"
        % (ort_dag[int(0.025 * B)], ort_dag[int(0.975 * B) - 1])
    )
```

```python
def main():
    ornek2_poisson()
    ornek3_mle_bootstrap()


if __name__ == "__main__":
    main()
```

```term
$ python b49_k_ornek2_3.py
Simulasyon: 100000 saat, lam=3.0
  k=0  simule=0.0493  teorik=0.0498
  k=1  simule=0.1478  teorik=0.1494
  k=2  simule=0.2239  teorik=0.2240
  k=3  simule=0.2266  teorik=0.2240
  k=4  simule=0.1666  teorik=0.1680
  k=5  simule=0.1014  teorik=0.1008
  P(k>=5) simule=0.1857  teorik=0.1847
  ortalama=3.0068 (lam=3.0)
n=10  toplam=20.3  MLE lambda=0.4926  ort=2.0300 saat
  l(0.3000) = -18.1297
  l(0.4926) = -17.0804
  l(0.6000) = -17.2883
  l(0.8000) = -18.4714
Bootstrap GA (lambda): [0.3322, 0.8197]
Bootstrap GA (ortalama sure): [1.2200, 3.0100]
```

**Bunu AI'sız yazabilir misin?** Arıza süreleri 0,5; 1,0; 2,0 ve 0,5 saat olsun. λ̂'yı kağıtta hesapla. Sonra "ortalama süre" için bir bootstrap aralığı tahmin et: dört değerden on bin kez yerine koyarak örnek çekmek mümkün olsaydı, aralığın genişliği bu sonuçla nasıl karşılaştırılırdı?

### Örnek 4 (★★★): İki pivot stratejisinin farkı anlamlı mı?

**Adım 1 — Anla.** Quicksort'un iki sürümü var: pivotu rastgele seçen ve pivotu üç elemanın medyanından seçen (medyan-üç). Her ikisinin çalışma süresi, yapılan karşılaştırma sayısıyla ölçülebilir; zaman ölçümü donanıma bağlı olduğundan burada karşılaştırma sayısını vekil olarak kullanıyoruz. Soru: rastgele pivot sürümü medyan-üç sürümünden daha çok karşılaştırma mı yapıyor, ve bu fark küçük örnekte güvenilir mi?

**Adım 2 — Örnekle.** Beş rastgele permütasyon (n = 50) için iki sürümün karşılaştırma sayıları: rastgele pivot için 233, 267, 230, 242, 231 (ortalama 240,6); medyan-üç için 214, 249, 241, 212, 214 (ortalama 226,0). Gözlenen fark 14,60 karşılaştırmadır. Bu fark gerçek bir üstünlük mü, yoksa birkaç karşılaştırmalık bir şans farkı mı?

**Adım 3 — Kaba çöz.** Permütasyon testi: iki grubun 10 değeri (beş rastgele, beş medyan-üç) tek bir havuzda toplanır ve bu 10 değerin 5'erli bölünmesinin kaç farklı biçimi olduğu sayılır: C(10, 5) = 252 (Bölüm 47). Her bölme için ortalamalar farkını hesaplayıp gözlenen farkın mutlak değerine eşit ya da büyük olanları sayarız. 252 bölmenin 48'inde bu koşul sağlanır. Yani p = 48 / 252 = 0,1905.

**Adım 4 — Örüntü.** Permütasyon dağılımının yapısını eşiklerle görelim: |fark| ≥ 0 için 252 bölme (hepsi); ≥ 5 için 170; ≥ 10 için 106; ≥ 15 için 40; ≥ 20 için 18. Gözlenen 14,60 değeri 10 ile 15 arasındadır; yani rastgele bir bölmenin farkı çoğu zaman 10'dan küçüktür, bu yüzden 14,60 "sıra dışı" sayılmaz. Örüntü: 5 + 5 küçük örnekte, karşılaştırma sayılarının kendi değişkenliği (örneğin 212 ile 267 arası) bu farkı gölgede bırakır.

**Adım 5 — İyileştir.** Örneği büyütelim: 25 + 25 dizi, n = 300. Bu durumda rastgele pivot ortalama 2533,9, medyan-üç ortalama 2186,8 karşılaştırma yapıyor; fark 347,08. Permütasyon testi (10 000 yeniden karıştırma) p = 0,0001 verir, yani fark istatistiksel olarak anlamlıdır. Medyan-üçün daha az karşılaştırma yapması, genel bilgi olarak bilinen bir sonuçtur. Dolayısıyla küçük örnekte bulamadığımız fark, büyük örnekte açıkça ortaya çıkıyor.

**Adım 6 — Doğrula.** Aşağıdaki sayılar, 5 + 5 örneğin tam permütasyon testinden gelir:

| Eşik | Mutlak fark ≥ eşik olan bölme sayısı |
|---|---|
| 0 | 252 |
| 5 | 170 |
| 10 | 106 |
| 15 | 40 |
| 20 | 18 |

Gözlenen fark 14,60 olduğunda, eşik 15 ile 10 arasında kalır ve 48 bölme (≥ 14,60) bu bölgeden gelir. Bu tablo, p-değerinin sayımla elde edildiğini gösterir; sonuç 48 / 252 = 0,1905'tir. Betiğin çıktısı aşağıda verilmiştir.

**Bunu AI'sız yazabilir misin?** Beşer elemanlı iki grubun değerleri A = {10, 12, 14, 16, 18} ve B = {9, 11, 13, 15, 17} olsun. Gözlenen fark ne kadardır? Sonra 252 bölmeyi tek tek saymak yerine, gözlenen farkın |fark| ≥ gözlenen olan bölme sayısını stratejik olarak nasıl bulabilirsin? Bu soruyu kâğıtta çözmeye çalış; sonra kontrol et.

```python
import random
from itertools import combinations


def quicksort_karsilastirma(a, pivot):
    """Lomuto bolmeli yinelemeli quicksort: karsilastirma sayisi."""
    sayac = 0
    yigin = [(0, len(a) - 1)]
    while yigin:
        lo, hi = yigin.pop()
        if lo >= hi:
            continue
        if pivot == "rastgele":
            p = random.randint(lo, hi)
        else:  # medyan-uc
            m = (lo + hi) // 2
            uc = sorted([(a[lo], lo), (a[m], m), (a[hi], hi)])
            p = uc[1][1]
        a[p], a[hi] = a[hi], a[p]
        x = a[hi]
        i = lo
        for j in range(lo, hi):
            sayac += 1
            if a[j] < x:
                a[i], a[j] = a[j], a[i]
                i += 1
        a[i], a[hi] = a[hi], a[i]
        yigin.append((lo, i - 1))
        yigin.append((i + 1, hi))
    return sayac
```

```python
def tam_permutasyon(a, b):
    """5+5 ornek: |fark| >= gozlenen olan bolmeler."""
    havuz = a + b
    na, nb = len(a), len(b)
    gozlenen = sum(a) / na - sum(b) / nb
    toplam = say = 0
    for idx in combinations(range(len(havuz)), na):
        secili = set(idx)
        x = [havuz[i] for i in idx]
        y = [havuz[i] for i in range(len(havuz)) if i not in secili]
        f = sum(x) / na - sum(y) / nb
        toplam += 1
        if abs(f) >= abs(gozlenen) - 1e-12:
            say += 1
    return gozlenen, say, toplam
```

```python
def buyuk_ornek(seed=49, B=10_000):
    """25+25 ornek, n=300: yaklasik permutasyon testi (B=10000)."""
    random.seed(seed)
    rnd = random.Random(seed)
    a, b = [], []
    for _ in range(25):
        dizi = list(range(300))
        rnd.shuffle(dizi)
        a.append(quicksort_karsilastirma(list(dizi), "rastgele"))
        b.append(quicksort_karsilastirma(list(dizi), "medyan3"))
    g = sum(a) / 25 - sum(b) / 25
    havuz = a + b
    say = 0
    for _ in range(B):
        rnd.shuffle(havuz)
        f = sum(havuz[:25]) / 25 - sum(havuz[25:]) / 25
        if abs(f) >= abs(g):
            say += 1
    print(
        "25+25: ort A=%.1f B=%.1f fark=%.2f"
        % (sum(a) / 25, sum(b) / 25, g)
    )
    print(
        "25+25: permutasyon p = %.4f (B=10000)"
        % ((say + 1) / (B + 1))
    )
```

```python
def main(seed=49, n=50):
    random.seed(seed)  # quicksort pivotu global RNG kullanir
    rnd = random.Random(seed)
    rastgele, medyan3 = [], []
    for _ in range(5):
        dizi = list(range(n))
        rnd.shuffle(dizi)
        rastgele.append(
            quicksort_karsilastirma(list(dizi), "rastgele")
        )
        medyan3.append(quicksort_karsilastirma(list(dizi), "medyan3"))
    print("A (rastgele):", rastgele, "ort=%.1f" % (sum(rastgele) / 5))
    print("B (medyan3): ", medyan3, "ort=%.1f" % (sum(medyan3) / 5))
    g, say, top = tam_permutasyon(rastgele, medyan3)
    print("gozlenen fark (A-B) = %.2f" % g)
    print("bolme sayisi = %d" % top)
    print("|fark| >= gozlenen olan bolme = %d" % say)
    print("exact p = %d/%d = %.4f" % (say, top, say / top))
    havuz = rastgele + medyan3
    for esik in (0, 5, 10, 15, 20):
        c = 0
        for idx in combinations(range(10), 5):
            secili = set(idx)
            x = [havuz[i] for i in idx]
            y = [havuz[i] for i in range(10) if i not in secili]
            if abs(sum(x) / 5 - sum(y) / 5) >= esik - 1e-12:
                c += 1
        print("  |fark| >= %2d : %3d bolme" % (esik, c))


if __name__ == "__main__":
    main()
    buyuk_ornek()
```

```term
$ python b49_l_ornek4.py
A (rastgele): [233, 267, 230, 242, 231] ort=240.6
B (medyan3):  [214, 249, 241, 212, 214] ort=226.0
gozlenen fark (A-B) = 14.60
bolme sayisi = 252
|fark| >= gozlenen olan bolme = 48
exact p = 48/252 = 0.1905
  |fark| >=  0 : 252 bolme
  |fark| >=  5 : 170 bolme
  |fark| >= 10 : 106 bolme
  |fark| >= 15 :  40 bolme
  |fark| >= 20 :  18 bolme
25+25: ort A=2533.9 B=2186.8 fark=347.08
25+25: permutasyon p = 0.0001 (B=10000)
```

Örnek 2 ile 3'ün betiği `b49_k_ornek2_3.py`, Örnek 4'ün betiği `b49_l_ornek4.py` dosyasındadır. Hepsi `arsiv/kod/b49/` klasöründe ve sabit tohumlarla yeniden üretilebilir.

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ araçları **yasak**. Amaç, bir ölçüm raporunu ya da bir sensör izleyicisini kendi kafanla kurup sınayabilmen. Önce kâğıda çiz, küçük testler yaz, sonra kodla. Ürettiğin sayılar, bu bölümdeki sonuçlarla uyuşmalı; uyuşmuyorsa nedenini bul. Çözümü dışarıdan alma.
:::

### Proje 1 (★★): Ölçüm istatistiği aracı

**Amaç:** Bir CSV dosyasından iki ölçüm grubunu okuyup, her grup için dağılım özetini çıkaran, iki grup arasındaki farkı üç istatistikle (ortalama, medyan, p99) değerlendiren ve belirsizliğini bootstrap ile permütasyon testiyle raporlayan bir komut satırı aracı yaz.

**Yapılacak / Beklenen davranış:** Araç `python olcum.py veri.csv --grup kaynak --deger gecikme_cevrim` gibi çağrılabilmeli. Çıktı, her grup için n, ortalama, p50, p90, p99 ve en büyük değeri içermeli. İki grup varsa; ortalama, medyan ve p99 farkları için permütasyon p-değeri (B = 10 000), bootstrap %95 güven aralığı (B = 10 000), Cohen'in d'si ve Cliff'in δ'sı yazılmalı. Veri ayrık ve yinelenen değerler içeriyorsa (medyan farkı için aralık sıfır genişlikli çıkıyorsa), araç bunu bir uyarıyla belirtmeli. Aynı tohumla iki kez çalışan araç, birebir aynı çıktıyı vermelidir.

Test verisi olarak `engine/veri/b44_gecikme.csv` dosyasında `kesme,TIM` ile `kesme,ADC` gruplarını kullan. Beklenen sonuçlar Bölüm 49.11'de verildi: ortalama farkı 28,80 (p = 0,00010), medyan farkı p = 1,0 ve güven aralığı sıfır genişlikli.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Yüzdelik fonksiyonunu 49.11'deki gibi enterpolasyonla yaz. Permütasyon testinde iki grubun değerlerini tek bir listede birleştir, karıştır, ilk n₁ değerin ortalamasıyla kalan değerlerin ortalamasını karşılaştır; bu işlemi istatistik fonksiyonuna parametre olarak geçirirsen, aynı kodu medyan ve p99 için de kullanabilirsin. Bootstrap'te her yeniden örnek için iki grubu ayrı ayrı yeniden örnekle. Cliff'in δ'sı için iki döngü yeter; O(n·m) bu boyutta sorun değildir.

**Başarı kriterleri:**
- Aynı tohumla iki çalıştırma birebir aynı çıktıyı verir.
- TIM/ADC karşılaştırmasında ortalama farkı 28,80 ± 0,01, p-değeri 0,00010 ve Cohen'in d'si 0,815 ± 0,01 çıkar.
- Aynı dağılımdan üretilmiş iki grupta (fark yok) 200 bağımsız veri setinde permütasyon testinin p < 0,05 çıktığı oran 0,03 ile 0,07 arasındadır.
- Ayrık veride medyan için sıfır genişlikli aralık geldiğinde araç uyarı verir.

### Proje 2 (★★★): Gürültülü sabit bir değeri izleyen 1B Bayesçi tahmin

**Amaç:** Bir İHA'nın sabit yüksekliğini, her adımda gelen gürültülü bir sensör ölçümüyle zamanla güncelleyen bir tahminleyici yaz. Her ölçümden sonra sonsal ortalama ve sonsal standart sapma tutulmalı. Bu, Bölüm 49.12'deki tek seferlik füzyonun zamanla genişletilmiş hâlidir ve Bölüm 62'deki Kalman filtresinin 1B öncülüdür.

**Yapılacak / Beklenen davranış:** Gerçek yükseklik h = 5 m olsun. Her adımda ölçüm z = h + gürültü, gürültünün standart sapması σ = 2 m. 200 ölçüm yap ve her 20 ölçümde bir sonsal ortalama ile sonsal standart sapmayı yazdır. Önsel N(0, 100) olarak başlasın (çok belirsiz). Program son olarak gerçek değerin sonsal ±2σ aralığında kalıp kalmadığını raporlamalı. 1000 bağımsız koşuda bu oran ölçülmeli.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Kesinliği tut: her ölçümde kesinlik artar (1/σ²'nin toplamı), ortalama ise kesinlik ağırlıklı bir ortalamadır. Sonsal ortalamayı tekrar hesaplamak yerine, önceki kesinlik ve önceki ortalamadan güncelleyebilirsin. Gürültüyü numpy ile üret ve tohumu sabitle.

**Başarı kriterleri:**
- 200 ölçüm sonunda sonsal standart sapma 1/√(200/4) = 0,1414'e çok yakın çıkar (kesinlik toplamı 200 · 1/4 = 50).
- Önsel çok belirsiz olduğunda ilk birkaç adımda sonsal ortalama ölçümlere yakındır; önsel etkisi azalır.
- 1000 koşuda gerçek değerin sonsal ±2σ_son aralığında kalma oranı %93 ile %97 arasındadır.
- Her ölçüm için güncelleme yalnızca iki toplama ve iki bölme içerir; döngü içinde gereksiz bellek tahsisi yoktur.

### Ek Alıştırmalar

Aşağıdaki problemlerin çözümü bu kitapta yok. Önce kâğıda, sonra editöre geç; yapay zekâ yasak. Zorluk etiketine göre sırala. Mülakat etiketli olanları sesli düşünerek ve süreyi sınırlayarak çöz.

1. **★ — Koşullu olasılık.** P(A) = 0,3, P(B | A) = 0,5 ve P(B | A′) = 0,2 veriliyor. P(A | B) nedir?
2. **★ — Bağımsızlık.** İki zar atılıyor. A: ilk zar 6 gelsin; B: toplam 10 olsun. A ve B bağımsız mıdır? Sayarak göster.
3. **★ — Binom ve Poisson.** Bir sürümde 50 modülün her biri %2 olasılıkla hata içeriyor. En az üç hatalı modül olma olasılığını önce Poisson ile yaklaşık hesapla, sonra binom ile karşılaştır.
4. **★ — Beklenen en büyük değer.** Bir zar iki kez atılıyor ve daha büyük değer alınıyor. Bu değerin beklenen değeri nedir? (İpucu: P(max ≤ k) = (k/6)² yaz.)
5. **★ — Merkezi limit.** 100 bağımsız gözlemin ortalaması 10, standart sapması 4. Ortalamanın yaklaşık %95 aralığı nedir?
6. **★★ — Mülakat: taban oranı.** Bir yazılım testi %90 oranında gerçek hatayı yakalıyor ve doğru olmayan kodun %5'inde yanlış alarm veriyor. Hataların genel oranı %1 ise, test pozitif çıktığında gerçek hata olasılığı nedir? Sonucu sezgiyle yorumla.
7. **★★ — Mülakat: Poisson kestirimi.** Bir sunucu beş saatte 12, 7, 9, 11 ve 6 hata kaydetti. Saatlik hata oranı λ için en büyük olabilirlik kestirimi nedir? Bu kestirimin yaklaşık %95 aralığını bulmak için hangi yöntemi seçersin?
8. **★★ — Bootstrap medyanı.** Bir ölçüm dizisinde medyan için bootstrap güven aralığı hesaplıyorsun ve aralık tek bir değere çöküyor. Bu neden olur? Ayrık veri ile sürekli veri arasında bu davranışı nasıl ayırt edersin?
9. **★★★ — Mülakat: çoklu test.** Bir ekip 30 farklı metrik ölçüyor ve birinde p = 0,03 çıkınca "yeni özellik işe yarıyor" diyor. Bu iddiayı nasıl sınarsın? Hangi düzeltmeyi uygularsın ve düzeltilmiş eşik ne olur?
10. **★★★ — Mülakat: n − 1.** Örnek varyansını n − 1 ile bölmenin nedenini bir cümleyle açıkla. n = 1 olduğunda ne olur ve bu neden bir sorun değildir?
11. **★★★ — Mülakat: güven aralığı yorumu.** Bir mühendis "bu %95 aralığında gerçek değerin olma olasılığı %95'tir" dedi. Bu cümleyi düzelt ve yanlışın kaynağını yaz.
12. **★★★ — Mülakat: olasılıksal çıktı.** Bir sınıflandırıcı her örnek için olasılık veriyor ama bu olasılıklar gerçek oranları yansıtmıyor (aşırı özgüven). Kalibrasyonu hangi veri ile ve hangi yöntemle düzeltirsin? Düzeltme sonrası sıralamanın değişip değişmediğini nasıl anlarsın?

## Kod Okuma Egzersizi

Bu bölümde sayısal kararlılığı gösteren gerçek bir kaynak kodu okuyacaksın. Kaynak: CPython **3.12.10**, `Lib/statistics.py`. Dosya, yerel Python 3.12.10 kurulumundan (`C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\statistics.py`) alındı. Sayfa genişliği için iki küçük değişiklik yaptık, ikisi de metinde işaretli: (1) `variance` ve `_ss` fonksiyonlarının docstring'leri çıkarıldı; (2) bir `raise` satırı 70 sütuna sığsın diye iki satıra bölündü. Kod mantığında hiçbir değişiklik yoktur.

Önce `variance`: n − 1 ile bölme, örnek varyansının (yansız) tanımıdır. Asıl iş `_ss`'e devredilir.

```python
def variance(data, xbar=None):
    T, ss, c, n = _ss(data, xbar)
    if n < 2:
        raise StatisticsError(
            'variance requires at least two data points')
    return _convert(ss / (n - 1), T)
```

`_ss`, dört değer döndürür: tip (T), kare sapmaların toplamı (ssd), ortalama (c) ve örnek sayısı (count). Dikkat et, bu fonksiyon ortalamayı önce hesaplamıyor; tek bir geçişte kesirlerle (Fraction) toplamları tutuyor. Yardımcı fonksiyonlar Bölüm 49 metninde açıklandı: `_exact_ratio(x)`, bir kayan nokta sayısını tam bir (pay, payda) çiftine çevirir; `sx_partials` ve `sxx_partials` bu çiftleri paydaya göre gruplayıp kısmi toplamları tutar; `_coerce` ve `_convert` ise sonucu, girdinin tipine (float, Decimal, Fraction) geri çevirir. Sonuç Σ(x − x̄)²'yi ((n · Σx² − (Σx)²) / n) biçiminde verir. Bu ifade cebirsel olarak doğrudur, ama kayan nokta ile hesaplanırsa yuvarlama hatası büyütür; burada tam kesirlerle çalıştığı için hata yoktur.

```python
def _ss(data, c=None):
    if c is not None:
        T, ssd, count = _sum((d := x - c) * d for x in data)
        return (T, ssd, c, count)
    count = 0
    types = set()
    types_add = types.add
    sx_partials = defaultdict(int)
    sxx_partials = defaultdict(int)
    for typ, values in groupby(data, type):
        types_add(typ)
        for n, d in map(_exact_ratio, values):
            count += 1
            sx_partials[d] += n
            sxx_partials[d] += n * n
    if not count:
        ssd = c = Fraction(0)
    elif None in sx_partials:
        # The sum will be a NAN or INF. We can ignore all the finite
        # partials, and just look at this special one.
        ssd = c = sx_partials[None]
        assert not _isfinite(ssd)
    else:
        sx = sum(Fraction(n, d) for d, n in sx_partials.items())
        sxx = sum(Fraction(n, d*d) for d, n in sxx_partials.items())
        # This formula has poor numeric properties for floats,
        # but with fractions it is exact.
        ssd = (count * sxx - sx * sx) / count
        c = sx / count
    T = reduce(_coerce, types, int)  # or raise TypeError
    return (T, ssd, c, count)
```

Şimdi bu tasarımın neden gerekli olduğunu görelim. Aşağıdaki betik, 1 milyar civarındaki dört değerin varyansını üç yöntemle hesaplar: `statistics.variance`, naif tek geçişli formül ve iki geçişli kayan nokta hesabı.

```python
import statistics as st
```

```python
def naif_varyans(veri):
    """Tek gecisli formul: (sum x^2 - (sum x)^2 / n) / (n - 1)."""
    n = len(veri)
    sx = sum(veri)
    sxx = sum(x * x for x in veri)
    return (sxx - sx * sx / n) / (n - 1)
```

```python
def iki_gecis(veri):
    m = sum(veri) / len(veri)
    return sum((x - m) ** 2 for x in veri) / (len(veri) - 1)
```

```python
if __name__ == "__main__":
    veri = [1e9 + 4, 1e9 + 7, 1e9 + 13, 1e9 + 16]
    print("statistics.variance = %r" % st.variance(veri))
    print("naif tek gecis      = %r" % naif_varyans(veri))
    print("iki gecis (float)   = %r" % iki_gecis(veri))
```

```term
$ python b49_m_kod_okuma.py
statistics.variance = 30.0
naif tek gecis      = 0.0
iki gecis (float)   = 30.0
```

Sonuç çarpıcıdır. Naif formül 0,0 verir: Σx² ≈ 4 · 10¹⁸ büyüklüğündedir; bu aralıkta bir float64'ün iki komşu değeri arasındaki adım 512'dir. Gerçek fark olan 90 bu gürültüde kaybolur. İki geçişli kayan nokta hesabı, önce ortalamayı çıkardığı için doğru sonucu (30,0) verir. `statistics.variance` ise tam kesirlerle çalıştığı için bu sonucu da doğrudan verir.

**Sorular — cevaplamadan geçme:**

1. `_ss` iki yolu izliyor: `c` verildiğinde ve verilmediğinde. `c` verildiğinde ortalama hesaplanmaz; bu, kullanıcının yanlış bir `xbar` girmesi durumunda neden çöp sonuç üretebilir?
2. Naif formül neden 0,0 verdi? Σx², (Σx)² ve bölmenin her birinin hangi büyüklükte olduğunu hesaplayarak yuvarlama hatasını göster.
3. `sx_partials` sözlüğü neden değerleri değil, paydaları anahtar yapıyor? Bir kayan nokta sayısının (pay, payda) çiftine dönüşümü neden tam ve kayıpsızdır?
4. `(count * sxx - sx * sx) / count` ifadesinin Σ(x − x̄)²'ye eşit olduğunu cebirsel olarak göster.
5. `variance` neden `n < 2` durumunda hata veriyor? n = 1 olsaydı payda ne olurdu ve bu ne anlama gelirdi?
6. `numpy.var` varsayılan olarak n ile böler (`ddof=0`). Bu fark hangi durumda (küçük n, bir popülasyon ya da bir örnek) önemli hâle gelir?

## Bölüm Özeti

- Olasılık, Kolmogorov'un üç aksiyomundan çıkar; koşullu olasılık ve bağımsızlık, bir olayın başka bir olay bilindiğinde nasıl değiştiğini ölçer.
- Bayes teoremi, P(A | B)'yi P(B | A)'dan çevirir; taban oranı yanılgısı, düşük oranlı olaylarda yanlış alarmın gerçek alarmı geride bırakmasıdır (İHA örneğinde %39).
- Kesikli dağılımlar (Bernoulli, binom, geometrik, Poisson) sayma ve bekleme modellerini; sürekli dağılımlar (düzgün, üstel, normal) ölçüm ve zaman modellerini verir. Üstel dağılımın belleksizliği ilk arıza modeli için kullanılır.
- Beklenen değer doğrusaldır ve bağımsızlık gerektirmez; gösterge değişkenleriyle karmaşık sayımlar kolaylaşır (şapka problemi: beklenen eşleşme sayısı 1). Kovaryans ve korelasyon ilişkiyi ölçer, nedenselliği değil.
- Büyük sayılar yasası örnek ortalamasını μ'ye yaklaştırır; merkezi limit teoremi bu ortalamanın hatasının normale yaklaştığını ve hatanın 1/√n ile küçüldüğünü söyler. Monte Carlo hatası da aynı kuralı izler.
- Ters CDF, Box–Muller ve reddetme örneklemesi, rastgele sayılardan başka dağılımlar üretmenin üç temel yoludur; tohumu sabitlemek tekrarlanabilirlik için zorunludur.
- MLE, verinin olabilirliğini maksimize eder; üstel ve Bernoulli için kapalı formülleri türevden çıkar. Örnek varyansındaki n − 1, yanlılığı düzeltir. MAP, önseli ekleyen MLE'dir; sıfır gözlem sorununu Laplace düzeltmesi çözer.
- Güven aralığı, yöntemin tekrarlandığında gerçek değeri içerme oranıdır; küçük ve çarpık örneklerde normal aralık %95'in altında kalır. Bootstrap, dağılım varsaymadan belirsizlik ölçer.
- Hipotez testinde p-değeri H₀ altında veriyi görme olasılığıdır, H₀'ın olasılığı değildir. Çoklu karşılaştırma ve p-hacking yanlış alarm oranını hızla artırır; A/B testinin örneklem büyüklüğü önceden hesaplanmalıdır.
- Mühendislik ölçümünde ortalama, medyan ve kuyruk (p99) farklı şeyleri anlatır; farkın anlamlılığını permütasyon ve bootstrap ile, etki büyüklüğünü Cohen'in d'si ve Cliff'in δ'sı ile raporlarsın.

**Sonraki bölümde:** Bölüm 50 — Optimizasyon. Bu bölümde MLE'yi bir kayıp fonksiyonunu en küçükleyen (ya da log-olabilirliği en büyükleyen) θ olarak tanımladık ve λ̂ = n / ∑xᵢ türevle bulduk. Bölüm 50'de bu adımı genel hâle getireceğiz: türevin sıfır olmadığı durumlarda gradyan inişi, konveks fonksiyonlar, Lagrange çarpanları ve kısıtlı optimizasyon. Bölüm 51'de ise çapraz entropinin neden bu kadar doğal bir kayıp olduğunu bilgi teorisinden çıkaracağız.

::: mulakat
Aşağıdaki sorular cevapsızdır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. Bir sınıflandırıcı %99 doğrulukla çalışıyor ama nadir bir sınıfta hiç doğru tahmin yapmıyor. Bu neden olur, hangi metrik bunu gösterir ve nasıl düzeltirsin?
2. Bir ölçümün ortalaması 20 ms, medyanı 12 ms. Bu dağılımın şekli hakkında ne söylersin ve bu bilgiyle hangi istatistiği raporlarsın?
3. Bir A/B testi 3 hafta sonra "anlamlı" çıktı, ama bu süreçte sürekli veriye bakılmıştı. Sonucu güvenilir kılmak için hangi değişikliği yapmalısın?
4. Örnek ortalamasının standart hatası 0,5. Örnek sayısını 4 katına çıkarırsan standart hata ne olur ve bunu neden yalnızca iki katına çıkarmak yeterli olmaz?
5. MLE ile MAP arasındaki fark tam olarak nedir? Veri çok büyüdüğünde iki kestirici neden birbirine yaklaşır?
6. Bir İHA'nın sensör füzyonunda iki sensörden biri çok gürültülü. Yine de ona hiç ağırlık vermemek neden genellikle en iyi karar değildir?
7. Bir yazılım ekibi "p99 gecikmesi 200 ms'in altında" hedefini tutturduğunu raporluyor. Bu iddiayı doğrulamak için hangi örneklem, hangi güven aralığı ve hangi sınırlamaları bilmen gerekir?
:::
