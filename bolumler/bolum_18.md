%% kisim_no: IV
%% kisim_ad: Algoritmalar
%% bolum_no: 18
%% baslik: Greedy

## Giriş: Her adımda en iyisini seç, geri dönme

Bölüm 16'da bir problemi çözmenin güvenli yolunu gördük: her olası seçimi dene, alt problemlerin sonuçlarını tabloda sakla, en iyisini al. Bu yöntem doğrudur, ama her adımda birçok dalı hesaplamayı gerektirir. Bu bölümde tersini deneyeceğiz. Her adımda yalnızca **şu an en iyi görünen** seçimi yapacağız ve bir daha geri dönmeyeceğiz. Bu yaklaşıma açgözlü algoritma (greedy algorithm) denir.

Açgözlü yaklaşımın cazibesi hızıdır. Çoğu açgözlü algoritma, bir sıralama ve tek bir geçişten oluşur; çalışma süresi genellikle `O(n log n)`, bazen `O(n)`dir. Tehlikesi de aynı hızdır: yerelde doğru görünen bir seçim, küresel olarak yanlış olabilir. Bu yüzden greedy'de kod yazmadan önce bir soru sormak zorunludur: "Bu seçim, optimal bir çözümün parçası olmak zorunda mı?" Cevabı kanıtlayamıyorsan, kuralın yanlış olduğunu da henüz bilmiyorsun demektir; o durumda küçük girdilerde kaba kuvvetle sınamak en hızlı yoldur.

Bu bölümde üç kanıt tekniği göreceğiz: değiş-tokuş argümanı (exchange argument), "greedy önde kalır" (greedy stays ahead) ve kesme özelliği (cut property). Bunları etkinlik seçimi, aralık bölümleme, sırt çantası, zaman çizelgeleme, Huffman kodlama ve minimum yayan ağaç üzerinde uygulayacağız. Bölüm 16'daki sırt çantası ve LCS gibi problemlerde greedy'nin neden yetmediğini, bu bölümdeki karşı örneklerle birlikte göreceksin.

Bu bölüm birkaç kez önceki bölümlere dayanır. Huffman ağacını heap ile kurduğumuz için Bölüm 10'daki öncelik kuyruğu gerekir. Etkinlikleri sıralamak Bölüm 13'teki sıralama algoritmalarını kullanır. Minimum yayan ağaç için Bölüm 17'deki Kruskal ve Prim'i yeniden gerçeklemek yerine oradaki kodu temel alacağız. Dijkstra'nın ayrıntılı anlatımı da Bölüm 17'dedir; burada yalnızca onun neden bir greedy algoritması olduğunu ve negatif kenarda neden çöktüğünü greedy çerçevesinde inceleyeceğiz. Huffman kodunun entropiyle ilişkisi Bölüm 51'in bilgi teorisine köprü kurar; zamanlayıcılar Bölüm 26'da, önbellek değiştirme ise Bölüm 25'te yeniden karşımıza çıkacak.

::: not
Bu bölümdeki her program Python 3.12.10 ile çalıştırıldı; sabit tohum olarak `random.Random(42)` kullanıldı, bu yüzden çıktılar sizde de aynı olmalı. C programları WSL içinde gcc 13.3 ile `-std=c11 -Wall -Wextra` uyarılarıyla derlendi; bellek ve tanımsız davranış denetimi için `-fsanitize=address,undefined` de WSL2 içinde çalıştırıldı. Python'un `zlib` modülü bu bölümde zlib 1.3.1 ile çalıştı. Windows'ta `long` 4 bayt olduğu için C kodunda boyutları `int` ve `size_t` ile açıkça seçtik.
:::

## 18.1 Açgözlü seçim: tanım, iki koşul ve karşı örnek avı

Bir problemi açgözlü yöntemle çözmek üç şeyi gerektirir: bir **sıralama ya da öncelik kuralı**, her adımda bu kurala göre **tek bir seçim** ve seçimden sonra kalan alt problemi aynı türden küçük bir problem olarak görebilme. Geri dönüş yoktur: bir kez seçilen eleman bir daha değerlendirilmez.

Doğruluk için iki koşulun birlikte sağlanması gerekir. Birincisi **açgözlü seçim özelliği** (greedy choice property): her adımdaki yerel seçim, bir optimal çözümün parçası olarak genişletilebilir. İkincisi **optimal alt yapı** (optimal substructure), Bölüm 16.1'de gördüğümüz koşulun aynısıdır: seçimden sonra kalan alt problemin optimal çözümü, bütün problemin optimal çözümünü tamamlar. Bölüm 16 ile arasındaki fark şudur: DP her seçimi dener ve en iyisini alır; greedy seçimi bir kez yapar ve bunun doğru olduğunu **kanıtlamak zorundadır**.

Bu kanıt zorunluluğu, açgözlü algoritmaların en sık yanlış kullanıldığı yerdir. Pratikte önerilen kural genellikle makul görünür. Bu yüzden şu dört adımı sırayla uygula:

1. Açgözlü kuralı tek cümleyle yaz (ör. "en erken biten etkinliği seç").
2. Küçük, rastgele girdiler üretip kaba kuvvet çözümle karşılaştır.
3. Eşleşmeyen bir girdi (karşı örnek) bulursan kural yanlıştır; küçük olanı sakla.
4. Karşı örnek bulamazsan, değiş-tokuş ya da "önde kalma" argümanıyla kanıtla.

Dördüncü adım bir kanıt olur, ama ikinci ve üçüncü adım bir **iddiayı reddetmenin** en güvenilir yoludur. Aşağıdaki program bu üç adımı otomatikleştirir: bir açgözlü fonksiyonu, bir kaba kuvvet fonksiyonunu ve bir girdi üreticisini alır, rastgele girdilerde karşılaştırır ve bulduğu en küçük karşı örneği yazdırır. Programda iki sınama var: para bozma (madeni para sayısı) ve sırt çantası (kapasiteye göre değer). İkisinde de açgözlü kural, her zaman optimum vermez.

Programın ilk kısmı yardımcı fonksiyonları tanımlar. `para_acgozlu` en büyük parayı önce kullanır; `para_dp` Bölüm 16.6'daki tabloyla optimumu verir. `kanonik_mi` ise bir para sisteminde açgözlünün her tutar için doğru olup olmadığını kontrol eder. Bu kontrol için bilinen bir sonucu kullanıyoruz (Kozen ve Zaks, 1994): bir para sistemi kanonik değilse, en küçük karşı örnek en büyük iki paranın toplamından küçüktür. Dolayısıyla o sınıra kadar denemek bir kanıt olur.

```python
# karsi_ornek_avcisi.py: acgozlu bir kuralin kaba kuvvete karsi
# en kucuk karsi ornegini rastgele arama ile bulur (tohum 42).
import random


def para_acgozlu(paralar, tutar):
    # en buyuk parayi once al, kalan tutari kucuk paralarla dene
    sayi = 0
    for p in sorted(paralar, reverse=True):
        sayi += tutar // p
        tutar %= p
    return sayi


def para_dp(paralar, tutar):
    inf = float("inf")
    dp = [0] + [inf] * tutar
    for t in range(1, tutar + 1):
        dp[t] = min((dp[t - p] + 1 for p in paralar if p <= t),
                    default=inf)
    return dp[tutar]


def kanonik_mi(paralar):
    # Kozen-Zaks (1994): en kucuk karsi ornek c_n + c_(n-1)'den kucuk
    # oldugu icin bu sinira kadar kontrol yeterlidir (bilinen sonuc).
    c = sorted(paralar)
    sinir = c[-1] + c[-2]
    return all(para_acgozlu(c, t) == para_dp(c, t)
               for t in range(1, sinir + 1))
```

Programın ikinci kısmı sırt çantası için açgözlü kuralı, optimum DP'yi ve karşı örnek avı işlevini içerir. `en_kucuk_karsi` rastgele girdilerde açgözlü ile optimumu karşılaştırır ve boyutu en küçük olan karşı örneği tutar. Boyut ölçüsü, para sisteminde `(madeni para sayısı, tutar)`, sırt çantasında `(eşya sayısı, kapasite)` olarak seçildi; küçük örnekler okunması en kolay olanlardır.

```python
def sirt_acgozlu(esyalar, W):
    toplam, kalan = 0, W
    sirali = sorted(esyalar, key=lambda x: x[1] / x[0],
                    reverse=True)
    for w, v in sirali:
        if w <= kalan:
            toplam += v
            kalan -= w
    return toplam


def sirt_dp(esyalar, W):
    dp = [0] * (W + 1)
    for w, v in esyalar:
        for c in range(W, w - 1, -1):
            dp[c] = max(dp[c], dp[c - w] + v)
    return dp[W]


def en_kucuk_karsi(uret, acgozlu, kaba, boyut, deneme, rnd):
    en_iyi = None
    for _ in range(deneme):
        g = uret(rnd)
        if acgozlu(*g) != kaba(*g):
            if en_iyi is None or boyut(g) < boyut(en_iyi):
                en_iyi = g
    return en_iyi
```

Son kısım girdi üreticilerini ve ana programı içerir. Ana program iki sınamayı çalıştırır ve sonuçları yazdırır. Her sınama için tohum `42` ile yeniden başlatılır; böylece her sınama kendi içinde tekrarlanabilir.

```python
def uret_para(rnd):
    adaylar = rnd.sample(range(2, 13), rnd.randint(2, 4))
    return sorted(set([1] + adaylar)), rnd.randint(1, 30)


def uret_sirt(rnd):
    n = rnd.randint(2, 5)
    esyalar = [(rnd.randint(1, 8), rnd.randint(1, 12))
               for _ in range(n)]
    return esyalar, rnd.randint(3, 12)


def main():
    for sistem in ([1, 5, 10, 25], [1, 2, 5, 10, 20, 50, 100, 200],
                   [1, 3, 4]):
        print("kanonik mi %-32s %s" % (sistem, kanonik_mi(sistem)))
    rnd = random.Random(42)
    g = en_kucuk_karsi(uret_para, para_acgozlu, para_dp,
                       lambda g: (len(g[0]), g[1]), 3000, rnd)
    paralar, tutar = g
    print("para: en kucuk karsi ornek:", paralar, "tutar", tutar)
    print("   acgozlu:", para_acgozlu(paralar, tutar),
          "optimum:", para_dp(paralar, tutar))
    rnd = random.Random(42)
    g = en_kucuk_karsi(uret_sirt, sirt_acgozlu, sirt_dp,
                       lambda g: (len(g[0]), g[1]), 3000, rnd)
    esyalar, W = g
    print("sirt: en kucuk karsi ornek:", esyalar, "W", W)
    print("   acgozlu:", sirt_acgozlu(esyalar, W),
          "optimum:", sirt_dp(esyalar, W))


if __name__ == "__main__":
    main()
```

Aşağıdaki çıktı bu programı çalıştırmanın sonucudur:

```term
$ python karsi_ornek_avcisi.py
kanonik mi [1, 5, 10, 25]                   True
kanonik mi [1, 2, 5, 10, 20, 50, 100, 200]  True
kanonik mi [1, 3, 4]                        False
para: en kucuk karsi ornek: [1, 4, 6] tutar 9
   acgozlu: 4 optimum: 3
sirt: en kucuk karsi ornek: [(3, 6), (1, 3)] W 3
   acgozlu: 3 optimum: 6
```

Çıktıdaki ilk üç satır kanonikliği ölçer. `[1, 5, 10, 25]` (ABD madeni para sistemi) ve `[1, 2, 5, 10, 20, 50, 100, 200]` sistemleri açgözlüyle her tutarda optimum verir; `[1, 3, 4]` vermez. Dördüncü ve beşinci satırdaki karşı örnekler okunabilir: `[1, 4, 6]` sisteminde 9 TL için açgözlü `6 + 1 + 1 + 1` (4 madeni para) seçer, oysa `4 + 4 + 1` (3 madeni para) optimumdur. Sırt çantasında `W = 3` kapasiteli çantaya, değer/ağırlık oranı en büyük olan `(1, 3)` eşyası önce girer ve kalan 2 birim yetmediği için `(3, 6)` alınamaz; sonuç 3 olur, oysa yalnızca `(3, 6)` alınarak 6 elde edilir.

Bu iki karşı örnek, açgözlü kuralların neden tehlikeli olduğunu gösterir: kural her adımda doğru görünür, ama bir adımdaki seçim sonraki adımların olanaklarını yok eder. Bölüm 16.5'teki 0/1 sırt çantası tablosunu hatırla: orada her eşya için "al" ya da "alma" kararını iki yolla değerlendirdik. Greedy bu iki yoldan birini kör biçimde seçer.

## 18.2 Değiş-tokuş argümanı: etkinlik seçimi

Etkinlik seçimi (activity selection) klasik açgözlü problemdir. Her etkinlik bir `[s, e)` zaman aralığıdır; yarı açık aralık kullanıyoruz, yani `e` anında biten etkinlik, aynı anda başlayan etkinliğe yer açar. Amaç, birbiriyle çakışmayan en çok etkinliği seçmektir. Her aralığın başlangıcı bitişinden küçüktür (`s < e`).

Açgözlü kural şudur: **bitiş zamanı en erken olan etkinliği seç, sonra ondan sonra başlayan ve bitişi en erken olanı seç**. Bu kuralın neden doğru olduğunu değiş-tokuş argümanıyla gösterelim. Varsayalım `O = o_1, o_2, ..., o_m` optimal bir çözüm, bitiş sırasına göre. Açgözlü ilk seçim `g_1`, bitişi en erken etkinliktir, yani `e(g_1) ≤ e(o_1)`. Şimdi `O'` kümesini `O`'dan `o_1`'i `g_1` ile değiştirerek kuralım.

`O'` geçerli midir? `o_2`, `o_1` ile çakışmıyordu, yani `s(o_2) ≥ e(o_1) ≥ e(g_1)`. Demek ki `g_1` ile `o_2` çakışmaz. Diğer etkinlikler `O`'da zaten birbiriyle uyumluydu ve değişmedi. `|O'| = |O|` olduğu için `O'` de optimaldir. Bu, açgözlü ilk seçimin bir optimal çözümde bulunabileceğini gösterir: açgözlü seçim özelliği sağlanmıştır.

Optimal alt yapı için, `g_1` seçildikten sonra kalan problem `g_1`'den sonra başlayan etkinliklerin problemidir ve onun optimal çözümü `O'`'nün kalanıdır. Tümevarımla açgözlünün her adımda bir optimal çözümle uyumlu kaldığı sonucuna varırız.

Şekil 18.1, değiş-tokuş adımını gösterir. Optimal çözümdeki ilk eleman, açgözlünün ilk seçimiyle yer değiştirir; geri kalan eleman dizisi aynı kalır.

![Şekil 18.1: Değiş-tokuş argümanı. Optimum O'nun ilk elemanı o_1, açgözlünün ilk seçimi g_1 ile değiştirilir. e(g_1) ≤ e(o_1) olduğu için O' hâlâ çakışmasız ve aynı büyüklüktedir.](gorseller/b18_degis_tokus.png)

Şekil 18.2, sekiz etkinlikli bir örnekte aynı kuralın seçimlerini gösterir. Her satır bir etkinliktir ve bitiş sırasına göre dizilmiştir. Bordo kutular açgözlünün seçtiği etkinliklerdir; kesikli çizgiler, her seçimden sonra "son" bitiş zamanını gösterir. Sıradaki bir etkinliğin başlangıcı son bitişten önce ise çakışır ve atlanır.

![Şekil 18.2: Sekiz etkinlik, bitişe göre sıralı. Açgözlü (1,4), (5,7) ve (8,11)'i seçer: üç etkinlik. Diğerleri son bitişten önce başladığı için atlanır.](gorseller/b18_aktivite.png)

Kuralın sınama programı dört farklı açgözlü kuralı karşılaştırır: bitişe göre (doğru), başlangıca göre, en kısa süreye göre ve en az çakışmaya göre. Programın ilk kısmı dört açgözlü kuralı tanımlar; ana programın başı ise bu kuralları iki elle örnekte gösterir ve ardından rastgele girdilerde karşılaştırır. Kaba kuvvet, `2^n` altkümeyi dener ve en büyük uyumlu olanı bulur; `n ≤ 8` için bu hızlıdır.

```python
# etkinlik_kurallar.py: etkinlik secimi icin dort acgozlu kural,
# kaba kuvvet referansi ve karsi ornekler. Aralik [s, e) yari acik.
import random


def uygun(s, son):
    return s >= son


def bitis_sirali(a):
    secilen, son = [], float("-inf")
    for s, e in sorted(a, key=lambda x: x[1]):
        if uygun(s, son):
            secilen.append((s, e))
            son = e
    return secilen


def baslangic_sirali(a):
    secilen, son = [], float("-inf")
    for s, e in sorted(a, key=lambda x: x[0]):
        if uygun(s, son):
            secilen.append((s, e))
            son = e
    return secilen


def cakisir(x, y):
    return x[0] < y[1] and y[0] < x[1]


def en_kisa_once(a):
    secilen = []
    for x in sorted(a, key=lambda x: x[1] - x[0]):
        if not any(cakisir(x, y) for y in secilen):
            secilen.append(x)
    return sorted(secilen)
```

İkinci kısım, en az çakışma kuralını, kaba kuvveti ve girdi üreticisini içerir. Kaba kuvvet her altkümeyi sıralayıp komşu çiftlerin uyumlu olup olmadığını kontrol eder; sıralı bir dizide yalnızca komşu çiftlere bakmak yeterlidir, çünkü her etkinlik bir öncekinden sonra başlamalıdır ve bu zincir boyunca geçerlidir.

```python
def en_az_cakisma(a):
    kalan, secilen = list(a), []
    while kalan:
        def cakisma_sayisi(x):
            return sum(1 for y in kalan
                       if y is not x and cakisir(x, y))
        x = min(kalan, key=cakisma_sayisi)
        secilen.append(x)
        kalan = [y for y in kalan if not cakisir(x, y)]
    return sorted(secilen)


def kaba(a):
    n, en_iyi = len(a), 0
    for maske in range(1 << n):
        sec = sorted(a[i] for i in range(n) if maske >> i & 1)
        if all(uygun(sec[i + 1][0], sec[i][1])
               for i in range(len(sec) - 1)):
            en_iyi = max(en_iyi, len(sec))
    return en_iyi


def rastgele(rnd):
    n = rnd.randint(1, 8)
    a = []
    for _ in range(n):
        s = rnd.randint(0, 14)
        a.append((s, s + rnd.randint(1, 5)))
    return a
```

Üçüncü parça, `yazdir` ve `kucult` yardımcılarını içerir. `kucult` bir karşı örneği, karşı örnek özelliğini koruyarak küçültür: her elemanı tek tek çıkarır ve hâlâ karşı örnekse kalıcı olarak atar. Bu, en küçük karşı örnek olduğunu garanti etmez; ama okunabilir bir örnek üretir.

```python
def yazdir(liste):
    for i in range(0, len(liste), 4):
        print("   ", liste[i:i + 4])


def kucult(a, hatali):
    changed = True
    while changed:
        changed = False
        for i in range(len(a)):
            b = a[:i] + a[i + 1:]
            if hatali(b):
                a, changed = b, True
                break
    return a
```

Son parça sınamayı çalıştırır. Önce iki elle örnek yazdırılır; sonra 500 rastgele örnekte her kuralın optimumdan kaç kez saptığı sayılır. Üçüncü adım olarak "en az çakışma" kuralı için tohum `11` ile daha geniş bir arama yapılır ve bulunan karşı örnek küçültülür.

```python
def main():
    kurallar = [("bitis", bitis_sirali),
                ("baslangic", baslangic_sirali),
                ("en kisa", en_kisa_once),
                ("az cakisma", en_az_cakisma)]
    for el in ([(0, 10), (1, 2), (3, 4)], [(0, 3), (2, 4), (3, 5)]):
        print("elle ornek:", el, "optimum", kaba(el))
        for ad, f in kurallar:
            print("   %-11s -> %s" % (ad, f(el)))
    rnd = random.Random(42)
    testler = [rastgele(rnd) for _ in range(500)]
    for ad, f in kurallar:
        hata, ilk = 0, None
        for a in testler:
            if len(f(a)) != kaba(a):
                hata += 1
                if ilk is None:
                    ilk = a
        print("%-11s hata: %3d / 500" % (ad, hata))
        if ilk is not None:
            print("   ilk karsi ornek (n=%d):" % len(ilk))
            yazdir(ilk)
            print("   secilen", len(f(ilk)), "optimum", kaba(ilk))
```

```python
    # az cakisma icin: 500 ornekte hata yok; genis arama (tohum 11)
    rnd = random.Random(11)
    for _ in range(200000):
        n = rnd.randint(3, 12)
        a = []
        for _ in range(n):
            s = rnd.randint(0, 25)
            a.append((s, s + rnd.randint(1, 9)))
        if len(en_az_cakisma(a)) != len(bitis_sirali(a)):
            break
    print("az cakisma, genis arama ilk karsi ornek (n=%d):" % len(a))
    k = kucult(a, lambda x: len(en_az_cakisma(x)) != kaba(x))
    print("   kucultulmus (n=%d):" % len(k))
    yazdir(sorted(k))
    print("   secilen", len(en_az_cakisma(k)), "optimum", kaba(k))


if __name__ == "__main__":
    main()
```

Programın çıktısı şöyledir:

```term
$ python etkinlik_kurallar.py
elle ornek: [(0, 10), (1, 2), (3, 4)] optimum 2
   bitis       -> [(1, 2), (3, 4)]
   baslangic   -> [(0, 10)]
   en kisa     -> [(1, 2), (3, 4)]
   az cakisma  -> [(1, 2), (3, 4)]
elle ornek: [(0, 3), (2, 4), (3, 5)] optimum 2
   bitis       -> [(0, 3), (3, 5)]
   baslangic   -> [(0, 3), (3, 5)]
   en kisa     -> [(2, 4)]
   az cakisma  -> [(0, 3), (3, 5)]
bitis       hata:   0 / 500
baslangic   hata:  49 / 500
   ilk karsi ornek (n=7):
    [(9, 10), (6, 10), (9, 13), (8, 11)]
    [(8, 9), (10, 11), (10, 15)]
   secilen 2 optimum 3
en kisa     hata:   7 / 500
   ilk karsi ornek (n=7):
    [(1, 6), (3, 5), (14, 17), (13, 15)]
    [(1, 2), (2, 5), (9, 14)]
   secilen 3 optimum 4
az cakisma  hata:   0 / 500
az cakisma, genis arama ilk karsi ornek (n=12):
   kucultulmus (n=9):
    [(2, 8), (3, 10), (6, 11), (8, 13)]
    [(11, 15), (14, 20), (18, 27), (20, 24)]
    [(22, 27)]
   secilen 3 optimum 4
```

Çıktı dört şey gösterir. Birincisi, bitişe göre sıralama 500 örnekte hiç hata yapmaz. İkincisi, başlangıca göre sıralama 49 hata yapar: `(0, 10)` uzun bir etkinliktir, onu seçmek iki kısa etkinliği öldürür. Üçüncüsü, en kısa süreye göre sıralama 7 hata yapar: `(2, 4)` en kısa olmasına rağmen iki komşuyu öldürür. Dördüncüsü, en az çakışma kuralı 500 örnekte hiç hata yapmadı; ama 200 bin denemelik genişletilmiş aramada 12 aralıklı bir karşı örnek buldu ve bunu 9 aralığa küçülttü. Bu, küçük örneklerde doğru görünen bir kuralın genel olarak doğru olmayabileceğinin somut bir kanıtıdır. Bu yüzden "küçük testte geçti" bir kanıt değildir; yalnızca bir karşı örnek bulunamadığını söyler.

Şekil 18.3, üç yanlış kuralın karşı örneklerini üst üste gösterir. Her blokta açgözlünün seçtiği etkinlikler ile optimum kümesi karşılaştırılır.

![Şekil 18.3: Yanlış kuralların karşı örnekleri. (a) başlangıca göre: uzun (0,10) seçilir ve iki kısa etkinlik kaybedilir. (b) en kısa önce: (2,4) seçilir ve iki komşu etkinlik kaybedilir. (c) en az çakışma: 9 aralıkta açgözlü 3, optimum 4 seçer.](gorseller/b18_karsi_ornek.png)

Bu örnekler, açgözlü kural ile "doğru" kuralın farkını netleştirir. Bitiş zamanı, bir etkinliğin kapattığı zaman dilimini en az tutan ölçüdür: erken biten bir etkinlik, sonrasındaki seçenekleri en az kısıtlar. Bu, değiş-tokuş argümanının sezgisel karşılığıdır. Sonraki bölümde aynı düşünceyi aralık bölümleme ve önde kalma argümanıyla kullanacağız.

## 18.3 Greedy önde kalır: aralık bölümleme ve sweep line

Değiş-tokuş argümanı tek bir optimal çözümü değiştirerek ilerler. Bazen daha doğrudan bir yol vardır: açgözlü çözümün her adımda diğer herhangi bir geçerli çözümden **önde** olduğunu göstermek. Bu, "greedy önde kalır" (greedy stays ahead) argümanıdır.

Etkinlik seçimi için iddia şöyledir. `G = g_1, g_2, ...` açgözlü çözüm, `F = f_1, f_2, ...` herhangi bir geçerli çözüm, ikisi de bitiş sırasına göre olsun. Her `i` için `e(g_i) ≤ e(f_i)` olduğunu göstermek istiyoruz; yani açgözlü k-inci etkinliğini, herhangi bir çözümün k-incisinden önce bitirir. Tümevarımla: `i = 1` için `g_1`, bitişi en erken olan etkinlik olduğundan `e(g_1) ≤ e(f_1)`. Varsayalım `e(g_i) ≤ e(f_i)`. `f_{i+1}`, `f_i`'den sonra başlar; `f_i` de `e(g_i)`'den sonra bittiği için `s(f_{i+1}) ≥ e(f_i) ≥ e(g_i)`. Yani `f_{i+1}` açgözlünün `i+1`. adımında aday olarak duruyordu. Açgözlü o adımda aday arasından en erken bitene bakar; bu yüzden `e(g_{i+1}) ≤ e(f_{i+1})`. Bu, açgözlünün her zaman en az o kadar etkinlik seçtiğini de söyler: `F` ne kadar uzunsa `G` de o kadar uzundur.

Aynı fikir daha zor bir problemde de işe yarar: **aralık bölümleme** (interval partitioning). Elimizde `n` ders (zaman aralığı) ve sınırsız sayıda oda var; çakışan iki ders aynı odada olamaz. Amaç, en az kaç odanın gerektiğini bulmaktır.

Açgözlü kural şudur: dersleri başlangıç zamanına göre sırala; her ders için boş bir oda varsa (odanın son dersi o dersin başlangıcından önce bitmişse) onu kullan, yoksa yeni bir oda aç. Odaların bitiş zamanlarını bir **min-yığında** tutarsak, en erken boşalan odayı her seferinde `O(log k)` içinde bulabiliriz (Bölüm 10'daki öncelik kuyruğu).

Bu kuralın optimal olduğunu iki adımda gösterebiliriz. Birincisi bir alt sınır: herhangi bir noktada `d` aralık birden ortuşuyorsa (aynı anda hepsi aktifse), bu `d` aralık farklı odalarda olmak zorundadır; yani en az `d` oda gerekir. `d`'ye **derinlik** diyelim ve en büyük derinliği ölçelim. İkincisi, açgözlünün hiçbir zaman derinlikten fazla oda açmadığını göstermek. Açgözlü yeni bir oda açtığı anda, `s` başlangıç noktasında bütün mevcut odalar doluydu: her odanın son dersi `s`'den önce başladı (sıralama nedeniyle) ve `s`'den sonra bitiyor (oda dolu). Yani o odaların son dersleri ve yeni ders, `s` noktasında birlikte aktiftir. Böylece derinlik, o anda açılmış odaların sayısına kadar çıkar; açılan oda sayısı derinliği aşamaz. Alt sınır ile üst sınır eşleştiği için açgözlü optimaldir: oda sayısı = en büyük derinlik.

Şekil 18.4 bu sezgiyi gösterir. Üstte üç oda şeridi vardır: her oda, kendisine atanan dersleri taşır. Altta sweep line (süpürme çizgisi) ilerlerken aktif ders sayısını gösteren basamak fonksiyonu vardır. Fonksiyonun en yüksek değeri, açgözlünün açtığı oda sayısına eşittir.

![Şekil 18.4: Aralık bölümleme. Üstte yedi ders üç odaya atanmıştır; altta süpürme çizgisi boyunca aktif ders sayısı. En yüksek değer 3'tür (zaman [3,4) ve [7,8) aralıklarında) ve açgözlünün açtığı oda sayısıyla eşittir.](gorseller/b18_sweep_oda.png)

Derinlik hesabı `O(n log n)` (sıralama ile) ya da bir süpürme çizgisi ile yapılır: başlangıçları ve bitişleri sıralayıp soldan sağa ilerlersin, aktif sayacı artırıp azaltırsın. Açgözlü algoritmanın kendisi de bu sıralamayla başlar ve toplam `O(n log n)` çalışır. Bu algoritmayı C'de ve bir kaba kuvvet denetimiyle Çözümlü Örnek 2'de yazacağız.

## 18.4 Sırt çantası: kesirli (doğru), 0/1 (yanlış); kanonik para sistemleri

Bölüm 16.7'de sınırsız sırt çantasını ve 0/1 sırt çantasını gördük. Burada aynı problemin iki farklı versiyonunu açgözlü yöntemle karşılaştırıyoruz. Bunun farkı büyük: **eşyayı bölebilir miyiz?**

**Kesirli sırt çantası** (fractional knapsack): her eşyanın bir kısmını alabilirsin. Açgözlü kural: değer/ağırlık oranına göre azalan sırada eşyaları al; bir eşya sığmazsa kalan kapasite kadarını al ve dur.

Doğruluk için değiş-tokuş argümanı yeterlidir. Bir optimal çözümde oranı daha yüksek bir eşyadan tam miktarda alınmamışsa ve oranı daha düşük bir eşyadan pozitif miktar alınmışsa, düşük oranlı eşyadan `δ` ağırlık çıkarıp yüksek oranlı eşyaya ekleyebiliriz. Kapasite korunur; değer, `δ` ağırlık başına oran farkı kadar artar ya da aynı kalır. Bu takas, optimal çözümü tekrar tekrar açgözlü çözüme yaklaştırır.

**0/1 sırt çantası**: her eşya ya tamamen alınır ya da hiç alınmaz. Aynı açgözlü kural burada başarısız olur. Üç eşyalı klasik örnekte `(ağırlık, değer)` ikilileri `(10, 60)`, `(20, 100)`, `(30, 120)` ve kapasite `W = 50`'dir. Oranlar sırasıyla `6`, `5`, `4`'tür. Açgözlü önce ilk iki eşyayı alır (ağırlık 30, değer 160), üçüncü eşya (ağırlık 30) kalan 20 birime sığmaz; sonuç 160. Oysa ikinci ve üçüncü eşyayı alırsak ağırlık tam 50 olur ve değer 220'dir. Açgözlü, "ilk eşyanın oranı yüksek" diye ilk eşyayı alırken, kapasiteyi tam doldurma fırsatını kaçırmıştır.

Aşağıdaki program üç şeyi hesaplar: kesirli açgözlü ile kesirli optimum (kaba kuvvetle, tam kesirlerle, LP'nin köşe noktalarını tarayarak) ve 0/1 açgözlü ile 0/1 optimum. Kesirli optimumu kaba kuvvetle hesaplamak için şunu kullanıyoruz: doğrusal programın köşe noktalarında en fazla bir eşya kesirli olabilir. Dolayısıyla her eşyanın alt kümesini ve kalan kapasiteyi bu bir kesirli eşyayla doldurup en iyisini alırsak, bütün köşeleri tararız.

```python
# fraksiyonel_sirt.py: kesirli sirt cantasi (acgozlu) ve 0/1 sirt
# cantasi karsilastirmasi. Kaba kuvvet dogrulamasi tam kesirlerle
# (Fraction) yapilir; LP'nin koseleri en fazla bir kesirli degisken
# icerir, bu yuzden o noktalari tarayarak optimum bulunur.
from fractions import Fraction
import random


def kesirli_acgozlu(esyalar, W):
    kalan, toplam = Fraction(W), Fraction(0)
    sirali = sorted(esyalar, key=lambda x: Fraction(x[1], x[0]),
                    reverse=True)
    for w, v in sirali:
        if kalan == 0:
            break
        al = min(Fraction(w), kalan)
        toplam += Fraction(v, w) * al
        kalan -= al
    return toplam


def kesirli_kaba(esyalar, W):
    n, en_iyi = len(esyalar), Fraction(0)
    for maske in range(1 << n):
        s_w = sum(esyalar[i][0] for i in range(n) if maske >> i & 1)
        s_v = sum(esyalar[i][1] for i in range(n) if maske >> i & 1)
        if s_w > W:
            continue
        en_iyi = max(en_iyi, Fraction(s_v))
        for j in range(n):
            if not (maske >> j & 1):
                w, v = esyalar[j]
                f = min(Fraction(W - s_w, w), Fraction(1))
                en_iyi = max(en_iyi, s_v + v * f)
    return en_iyi
```

Programın ikinci kısmında 0/1 açgözlü kuralı ve 0/1 sırt çantasının kesin çözümü yer alır. Kesin çözüm, Bölüm 16.4'teki tek boyutlu tablonun aynısıdır; kapasiteleri büyükten küçüğe tararız.

```python
def sirt_01_acgozlu(esyalar, W):
    kalan, toplam = W, 0
    sirali = sorted(esyalar, key=lambda x: Fraction(x[1], x[0]),
                    reverse=True)
    for w, v in sirali:
        if w <= kalan:
            toplam += v
            kalan -= w
    return toplam


def sirt_01(esyalar, W):
    dp = [0] * (W + 1)
    for w, v in esyalar:
        for c in range(W, w - 1, -1):
            dp[c] = max(dp[c], dp[c - w] + v)
    return dp[W]
```

Son kısım ana programdır: klasik üç eşyalı örneği çözer ve 300 rastgele küçük örnekte kesirli açgözlünün kaba kuvvetle eşleştiğini doğrular.

```python
def main():
    ornek = [(10, 60), (20, 100), (30, 120)]
    W = 50
    print("ornek (agirlik, deger):", ornek, "W =", W)
    print("kesirli acgozlu:", kesirli_acgozlu(ornek, W))
    print("kesirli kaba   :", kesirli_kaba(ornek, W))
    print("0/1 acgozlu   :", sirt_01_acgozlu(ornek, W))
    print("0/1 optimum    :", sirt_01(ornek, W))
    rnd = random.Random(42)
    hata = 0
    for _ in range(300):
        n = rnd.randint(1, 6)
        es = [(rnd.randint(1, 9), rnd.randint(1, 20))
              for _ in range(n)]
        W = rnd.randint(1, 25)
        if kesirli_acgozlu(es, W) != kesirli_kaba(es, W):
            hata += 1
    print("300 rastgele ornek, kesirli hata:", hata)


if __name__ == "__main__":
    main()
```

```term
$ python fraksiyonel_sirt.py
ornek (agirlik, deger): [(10, 60), (20, 100), (30, 120)] W = 50
kesirli acgozlu: 240
kesirli kaba   : 240
0/1 acgozlu   : 160
0/1 optimum    : 220
300 rastgele ornek, kesirli hata: 0
```

Çıktı, kesirli açgözlünün 240 bulduğunu ve kaba kuvvetle eşleştiğini; 0/1 açgözlünün 160, 0/1 optimumun 220 olduğunu gösterir. 300 rastgele örnekte kesirli hata sayısı sıfırdır. Şekil 18.5 aynı iki çözümü yan yana gösterir.

![Şekil 18.5: Aynı üç eşya, W = 50. Üstte kesirli açgözlü: E1 ve E2 tam, E3 yalnızca 20/30 kadar alınır; toplam 240. Altta 0/1 optimum: E2 ve E3 tam alınır; toplam 220. Kesirli çözüm, 0/1 probleminin üst sınırıdır.](gorseller/b18_fraksiyon.png)

**Kanonik para sistemleri.** Para bozma problemi (Bölüm 16.6) 0/1 sırt çantasına benzemez, ama açgözlü kuralı burada da cazip. Her adımda en büyük parayı alıp kalan tutara devam ediyoruz. Bu kural, para sistemi **kanonik** (canonical) ise yani her tutar için optimum madeni para sayısını açgözlü veriyorsa, doğrudur. Bölüm 18.1'deki program üç sistemi denetledi: `[1, 5, 10, 25]` ve `[1, 2, 5, 10, 20, 50, 100, 200]` kanoniktir; `[1, 3, 4]` değildir. Kanonikliği tek tek tutarları kontrol ederek sınamak, Kozen ve Zaks'ın sınırı sayesinde bir **kanıt** olur: en büyük iki paranın toplamına kadar bakmak yeter (bilinen sonuç). Bu sonuç, açgözlüyü her para sistemi için değil, bu sistemler için kesin olarak garanti eder.

## 18.5 Gecikme ve ağırlıklı tamamlama: EDF ve Smith kuralı

Tek bir makinede `n` iş olsun. Her işin işlem süresi `p_j`, son teslim tarihi `d_j` ve ağırlığı `w_j` olsun. İş `j`'nin tamamlanma zamanı `C_j` ile gecikmesi `L_j = C_j - d_j`'dir. İki farklı amaç iki farklı açgözlü kural doğurur.

**En büyük gecikmeyi (`L_max`) enküçültmek:** son teslim tarihi en erken olan işi önce yap. Bu, EDF (earliest due date first) kuralıdır. Doğruluğu değiş-tokuş argümanıyla gösterebiliriz. Yan yana iki iş `i, j` düşünelim; `i` önce, `j` sonra çalışıyor ve `d_i > d_j`. `t` başlangıç zamanı olsun. Sıra değişip `j` önce çalışırsa, `j` `t + p_j`'de biter; eski durumda `j`'nin gecikmesi `t + p_i + p_j - d_j`'ydi, yeni durumda `t + p_j - d_j` olur ve bu daha küçüktür. `i`'nin yeni gecikmesi `t + p_i + p_j - d_i`'dir; `d_i > d_j` olduğu için bu değer eski `L_j`'den küçüktür. Dolayısıyla takastan sonra her iki gecikme de eski `L_max`'tan küçük ya da eşit kalır. Bu, EDF'nin optimal olduğunu gösterir (Jackson'ın bilinen sonucu, 1955).

**Ağırlıklı tamamlama süresini (`Σ w_j C_j`) enküçültmek:** `p_j / w_j` oranına göre artan sırada yap. Bu, Smith kuralıdır. Kanıt için iki ardışık iş `i, j`'yi ele alalım; ikisi de `t` anında başlasın. `i` önce ise katkıları `w_i(t + p_i) + w_j(t + p_i + p_j)`; `j` önce ise `w_j(t + p_j) + w_i(t + p_j + p_i)`dir. İkisi arasındaki fark, cebirsel olarak:

`(w_i(t+p_i) + w_j(t+p_i+p_j)) - (w_j(t+p_j) + w_i(t+p_i+p_j))` ifadesi sadeleşip `w_j p_i - w_i p_j` olur.

Yani `i` önce yapmak, `w_j p_i ≤ w_i p_j` ise, yani `p_i / w_i ≤ p_j / w_j` ise en az o kadar iyidir. Ardışık iki işi bu kurala göre sıralamak, her ardışık çiftte değişim yapmanın toplamı artırmadığını gösterir; bu da optimal sıralamayı verir.

Aşağıdaki program üç şey yapar: iki kuralın optimal olduğunu tüm permütasyonlarla (`n ≤ 5`) doğrular, ayrıca yanlış bir kuralı (yalnızca işlem süresine göre sıralama) sınar ve bu kuralın ağırlık göz ardı edildiğinde nasıl başarısız olduğunu gösterir.

```python
# zaman_cizelgesi.py: tek makinede is siralama. Her is (p, w, d):
# p islem suresi, w agirlik, d son teslim. Smith kurali (p/w artan)
# toplam agirlikli tamamlama suresini; EDF (d artan) en buyuk
# gecikmeyi minimize eder. Kaba kuvvet: tum siralamalar (n <= 5).
import itertools
import random


def smith(isler):
    return sorted(isler, key=lambda j: j[0] / j[1])


def edf(isler):
    return sorted(isler, key=lambda j: j[2])


def sirali_maliyet(sira):
    t, agirlikli, gecikme = 0, 0, float("-inf")
    for p, w, d in sira:
        t += p
        agirlikli += w * t
        gecikme = max(gecikme, t - d)
    return agirlikli, gecikme


def kaba(isler):
    sonuclar = [sirali_maliyet(s)
                for s in itertools.permutations(isler)]
    return min(s[0] for s in sonuclar), min(s[1] for s in sonuclar)
```

```python
def main():
    isler = [(3, 1, 4), (2, 5, 6), (4, 2, 12)]
    print("isler (p, w, d):", isler)
    print("smith sirasi:", smith(isler))
    print("  agirlikli:", sirali_maliyet(smith(isler))[0],
          "kaba:", kaba(isler)[0])
    print("edf sirasi  :", edf(isler))
    print("  en buyuk gecikme:", sirali_maliyet(edf(isler))[1],
          "kaba:", kaba(isler)[1])
    rnd = random.Random(42)
    hata_s = hata_e = hata_p = 0
    for _ in range(300):
        n = rnd.randint(1, 5)
        isler = [(rnd.randint(1, 9), rnd.randint(1, 9),
                  rnd.randint(1, 30)) for _ in range(n)]
        w_opt, g_opt = kaba(isler)
        if sirali_maliyet(smith(isler))[0] != w_opt:
            hata_s += 1
        if sirali_maliyet(edf(isler))[1] != g_opt:
            hata_e += 1
        # karsilastirma: yalnizca islem suresine gore (w yok sayilir)
        spt = sorted(isler, key=lambda j: j[0])
        if sirali_maliyet(spt)[0] != w_opt:
            hata_p += 1
    print("300 ornek, smith hatasi:", hata_s)
    print("300 ornek, edf hatasi:", hata_e)
    print("300 ornek, p'ye gore (yanlis) hatasi:", hata_p)


if __name__ == "__main__":
    main()
```

```term
$ python zaman_cizelgesi.py
isler (p, w, d): [(3, 1, 4), (2, 5, 6), (4, 2, 12)]
smith sirasi: [(2, 5, 6), (4, 2, 12), (3, 1, 4)]
  agirlikli: 31 kaba: 31
edf sirasi  : [(3, 1, 4), (2, 5, 6), (4, 2, 12)]
  en buyuk gecikme: -1 kaba: -1
300 ornek, smith hatasi: 0
300 ornek, edf hatasi: 0
300 ornek, p'ye gore (yanlis) hatasi: 143
```

Çıktıdaki ilk örnekte üç iş `(p, w, d) = (3, 1, 4), (2, 5, 6), (4, 2, 12)` olarak verilmiştir. Smith sıralaması `(2, 5, 6), (4, 2, 12), (3, 1, 4)` olur ve toplam `5·2 + 2·6 + 1·9 = 31` eder; kaba kuvvet de 31 bulur. EDF sıralaması `(3, 1, 4), (2, 5, 6), (4, 2, 12)` olur ve en büyük gecikme `-1`dir; kaba kuvvet de `-1` bulur. Rastgele 300 örnekte iki kural da hiç hata yapmaz. Ağırlığı yok sayan kural ise 300 örnekte 143 kez yanlış sonuç verir: ağırlığın, Smith kuralında oranın bir parçası olduğunu görmek için bu sayı yeterli bir kanıttır.

## 18.6 Huffman kodlama

Bir metni bitlerle saklamak istediğimizi düşünelim. En basit yol her simgeye aynı uzunlukta bir kod vermektir: `n` simge için ceil(log2 n) bit. Ama metinde bazı harfler çok sık, bazıları nadir geçer. Sık harflere kısa, nadir harflere uzun kod vermek ortalama uzunluğu düşürür. Bunun çalışması için kodlar **öneksiz** (prefix-free) olmalıdır: hiçbir kod, başka bir kodun baş kısmı olmamalıdır. Öneksiz bir kodda bit akışı soldan okunduğunda her kod kesin olarak tek bir simgeye karşılık gelir; ayırıcı bit gerekmez.

Öneksiz kodlar bir ikili ağaçla temsil edilir: yaprak simgelerdir, sol kenar `0`, sağ kenar `1` dir, bir simgenin kodu kökten yaprağa giden yoldur. Her yaprağın kökten uzaklığı, o simgenin kod uzunluğudur. Kraft eşitsizliğinin bilinen sonucu (Kraft–McMillan): `n` simgeye karşılık gelen uzunluklar `l_1, ..., l_n` ancak `toplam 2^(-l_i) <= 1` ise bir öneksiz kod vardır. Bu eşitsizlik, aşağıda optimalliği denetlerken kullanacağımız tek teorik araçtır.

Frekansları `f_i` olan simgeler için amaç, `Σ f_i l_i` toplamını enküçültmektir. Huffman'ın açgözlü algoritması (1952) şöyledir: her adımda en düşük frekanslı iki düğümü seç, bunları yeni bir düğümün çocukları yap ve yeni düğümün frekansını iki frekansın toplamı olarak ver; tek bir düğüm kalana kadar tekrarla. Bu bir öncelik kuyruğu ile yapılır (Bölüm 10); `n` simge için `O(n log n)`.

Algoritmanın doğruluğu iki adımlık bir değiş-tokuş argümanıdır. Birincisi: en düşük frekanslı iki simge `x` ve `y`, optimal bir ağaçta en derin seviyedeki kardeşler olarak alınabilir. Gerçekten, eğer `x` daha derinde değilse, onu en derindeki yaprakla yer değiştirmek toplamı artırmaz. İkincisi: `x` ve `y`'yi tek bir simgeye (frekansı `f_x + f_y`) birleştirirsek, kalan problemin maliyeti, eksik kalan toplamı tam olarak `f_x + f_y` kadar değiştirir. Tümevarımla: birleştirilmiş problemin optimal ağacını al, yapraklarını `x` ve `y`'ye aç; maliyet, birleştirilmiş problemin maliyetine `f_x + f_y` eklenmiş olur. Huffman, her adımda bu iki kardeşi seçtiği için optimaldir.

Şekil 18.6, `abracadabra` kelimesinin frekanslarıyla algoritmanın dört adımını gösterir. Her sütun, o anda ormandaki (köklerin kümesi) düğümleri gösterir; bordo kutu, o adımda oluşan yeni düğümdür.

![Şekil 18.6: "abracadabra" için Huffman adımları. Frekanslar: a 5, b 2, r 2, c 1, d 1. Her adımda en küçük iki kök birleşir; son kök 11'dir.](gorseller/b18_huffman_adim.png)

Aşağıdaki program Huffman ağacını bir `heapq` yığınıyla kurar, kodları üretir, ortalama kod uzunluğunu hesaplar ve geri çözmeyi dener. Yığın elemanına `sayac` eklenmesi, frekansları eşit olan düğümler karşılaştırılırken iç düğümlerin (demetlerin) karşılaştırılmasını önler.

```python
# huffman.py: Huffman agacini heap ile kur, kodlari uret, dogrula.
# Her adimda en kucuk iki dugum birlestirilir (acgozlu secim).
import heapq
import math
from collections import Counter


def huffman_agaci(frekans):
    # kuyruk elemani: (frekans, sayac, dugum); sayac esitlikte
    # dugumlerin karsilastirilmasini onler
    kuyruk = []
    for sayac, (sembol, f) in enumerate(sorted(frekans.items())):
        heapq.heappush(kuyruk, (f, sayac, sembol))
    sayac = len(kuyruk)
    adimlar = []
    while len(kuyruk) > 1:
        f1, _, d1 = heapq.heappop(kuyruk)
        f2, _, d2 = heapq.heappop(kuyruk)
        adimlar.append((d1, f1, d2, f2))
        heapq.heappush(kuyruk, (f1 + f2, sayac, (d1, d2)))
        sayac += 1
    return kuyruk[0][2], adimlar


def kodlar(agac, onek=""):
    if isinstance(agac, str):
        return {agac: onek or "0"}
    tablo = kodlar(agac[0], onek + "0")
    tablo.update(kodlar(agac[1], onek + "1"))
    return tablo


def ort_uzunluk(frekans, tablo):
    toplam = sum(frekans.values())
    return sum(f * len(tablo[s]) for s, f in frekans.items()) / toplam
```

Programın ikinci kısmı ağacı kodlara çevirir, entropiyi hesaplar ve ana programı içerir. Ana program, `abracadabra` üzerinde algoritmanın adımlarını yazdırır ve sonucu geri çözerek doğrular.

```python
def entropi(frekans):
    toplam = sum(frekans.values())
    return -sum((f / toplam) * math.log2(f / toplam)
                for f in frekans.values())


def ada(d):
    if isinstance(d, str):
        return d
    return "(" + "".join(map(ada, d)) + ")"


def main():
    metin = "abracadabra"
    frekans = Counter(metin)
    print("frekanslar:", dict(sorted(frekans.items())))
    agac, adimlar = huffman_agaci(frekans)
    for i, (d1, f1, d2, f2) in enumerate(adimlar, 1):
        print("adim %d: %s(%d) + %s(%d)"
              % (i, ada(d1), f1, ada(d2), f2))
    tablo = kodlar(agac)
    for s in sorted(tablo, key=lambda s: (len(tablo[s]), s)):
        print("  %s -> %s" % (s, tablo[s]))
    kodlanmis = "".join(tablo[c] for c in metin)
    print("bit sayisi:", len(kodlanmis), "(sabit uzunluk: 3*11 = 33)")
    print("ortalama:", round(ort_uzunluk(frekans, tablo), 4),
          "entropi:", round(entropi(frekans), 4))
    ters = {v: k for k, v in tablo.items()}
    cozulmus, akim = [], ""
    for bit in kodlanmis:
        akim += bit
        if akim in ters:
            cozulmus.append(ters[akim])
            akim = ""
    print("geri cozum dogru:", "".join(cozulmus) == metin)


if __name__ == "__main__":
    main()
```

```term
$ python huffman.py
frekanslar: {'a': 5, 'b': 2, 'c': 1, 'd': 1, 'r': 2}
adim 1: c(1) + d(1)
adim 2: b(2) + r(2)
adim 3: (cd)(2) + (br)(4)
adim 4: a(5) + ((cd)(br))(6)
  a -> 0
  b -> 110
  c -> 100
  d -> 101
  r -> 111
bit sayisi: 23 (sabit uzunluk: 3*11 = 33)
ortalama: 2.0909 entropi: 2.0404
geri cozum dogru: True
```

Çıktıdan görülebilecekleri bir tabloda toplayalım. `a` simgesi 5 kez geçtiği için tek bit (`0`) alır; `b`, `c`, `d`, `r` dört bitle kodlanır. Toplam bit sayısı `5·1 + 2·3 + 2·3 + 1·3 + 1·3 = 23`tür; sabit uzunluklu kod 3 bit × 11 karakter = 33 bit olurdu. Ortalama uzunluk `23 / 11 ≈ 2.09` bit/simge; kaynağın entropisi `2.04` bittir. Bilinen bir sonuç olarak Huffman'ın ortalama uzunluğu `H ≤ L < H + 1` aralığındadır; burada `2.04 ≤ 2.09 < 3.04`. Entropi `H`, Bölüm 51'de ayrıntısıyla göreceğimiz bilgi miktarıdır: bir simgenin ortalama "sürpriz"i.

**Optimalliği kaba kuvvetle denetlemek.** Huffman'ın optimal olduğunu bir sınama ile de görebiliriz. Öneksiz kodların uzunlukları Kraft eşitsizliğini sağlamalıdır ve tersine, Kraft'ı sağlayan her uzunluk vektörü bir öneksiz kod verir. Bu yüzden `n ≤ 5` simgeli küçük örneklerde, bütün uzunluk vektörlerini (her uzunluk `1..n-1` aralığında) tarayabilir, Kraft'ı sağlayanlar arasındaki en küçük `Σ f_i l_i` değerini bulabiliriz. En büyük derinlik `n - 1` olduğu için bu aralık yeterlidir. Aşağıdaki program bu kaba kuvveti 300 rastgele frekans vektöründe Huffman ile karşılaştırır.

```python
# huffman_dogrula.py: Huffman'in maliyeti, tum gecerli uzunluk
# vektorleri arasindaki en kucuk maliyete esit mi? Kraft-McMillan
# esitsizligine gore bir uzunluk vektorunun prefix kodu olmasi icin
# gerek ve yeter kosul sum 2^-l <= 1'dir. Kaba kuvvet, uzunluk
# vektorlerini tarar ve bu kosulu denetler.
import itertools
import random
from huffman import huffman_agaci, kodlar


def kraft_kaba(f):
    n = len(f)
    L = n - 1 if n > 1 else 1      # optimal derinlik en fazla n-1
    en_iyi = None
    for l in itertools.product(range(1, L + 1), repeat=n):
        # Kraft toplamini tam sayi olarak: sum 2^(L-l) <= 2^L
        if sum(1 << (L - x) for x in l) > (1 << L):
            continue
        maliyet = sum(fi * li for fi, li in zip(f, l))
        if en_iyi is None or maliyet < en_iyi:
            en_iyi = maliyet
    return en_iyi


def huffman_maliyeti(f):
    sembol = {i: fi for i, fi in enumerate(f)}
    agac, _ = huffman_agaci({str(i): fi for i, fi in sembol.items()})
    tablo = kodlar(agac)
    return sum(fi * len(tablo[str(i)]) for i, fi in sembol.items())
```

```python
def main():
    rnd = random.Random(42)
    hata = 0
    for _ in range(300):
        n = rnd.randint(2, 5)
        f = [rnd.randint(1, 50) for _ in range(n)]
        if huffman_maliyeti(f) != kraft_kaba(f):
            hata += 1
    print("300 rastgele frekans vektoru, uyusmayan:", hata)
    for f in ([5, 2, 2, 1, 1], [1, 1, 2, 4, 8]):
        print("f =", f, "huffman:", huffman_maliyeti(f),
              "kaba:", kraft_kaba(f))


if __name__ == "__main__":
    main()
```

```term
$ python huffman_dogrula.py
300 rastgele frekans vektoru, uyusmayan: 0
f = [5, 2, 2, 1, 1] huffman: 23 kaba: 23
f = [1, 1, 2, 4, 8] huffman: 30 kaba: 30
```

Çıktı, 300 rastgele vektörün tamamında Huffman'ın maliyetinin kaba kuvvetle eşleştiğini gösterir. `[5, 2, 2, 1, 1]` için sonuç 23'tür; bu, `abracadabra`'nın toplam bit sayısıyla aynıdır (`23`), çünkü bu frekanslar o metinden gelir.

**Gerçek bir metinde.** Son sınama, Huffman'ı kitabın 16. bölümünün kaynak metni üzerinde uygular. Bu metin Türkçe ve UTF-8 kodlu olduğu için program **bayt** düzeyinde çalışır: Türkçe harfler iki baytlık diziler olarak sayılır. Ayrıca Huffman tablosunun kendisinin maliyeti (başlık) sayılmaz; yalnızca veri bitleri hesaplanır. Program ayrıca `zlib` (DEFLATE) ve gzip ile sıkıştırmayı karşılaştırır.

```python
# huffman_metin.py: gercek bir metinde bayt bazli Huffman, entropi ve
# gzip karsilastirmasi. Dosya: bolum_16.md (kitabin bolum 16 metni,
# SHA-256 ozetini cikti basar). Huffman basligi (tablo) maliyeti dahil
# DEGIL; yalnizca veri bitleri sayilir.
import gzip
import hashlib
import math
import sys
import zlib
from collections import Counter
from huffman import huffman_agaci, kodlar

DOSYA = sys.argv[1] if len(sys.argv) > 1 else "bolum_16.md"
```

```python
def main():
    with open(DOSYA, "rb") as f:
        veri = f.read()
    print("dosya:", DOSYA, "boyut:", len(veri), "bayt")
    print("sha256:", hashlib.sha256(veri).hexdigest()[:16], "...")
    print("zlib surumu:", zlib.ZLIB_RUNTIME_VERSION)
    frekans = Counter(veri)
    toplam = len(veri)
    h = -sum((f / toplam) * math.log2(f / toplam)
             for f in frekans.values())
    agac, _ = huffman_agaci({bytes([b]).hex(): f
                             for b, f in frekans.items()})
    tablo = kodlar(agac)
    bit = sum(f * len(tablo[bytes([b]).hex()])
              for b, f in frekans.items())
    gz = len(gzip.compress(veri, compresslevel=9, mtime=0))
    print("farkli bayt sayisi:", len(frekans))
    print("entropi        : %.4f bit/bayt" % h)
    print("huffman (veri) : %.4f bit/bayt" % (bit / toplam))
    print("gzip -9 (tum)  : %.4f bit/bayt" % (gz * 8 / toplam))
    print("sikistirma: huffman %.1f%%, gzip %.1f%%" % (
        100 * bit / 8 / toplam, 100 * gz / toplam))


if __name__ == "__main__":
    main()
```

```term
$ python huffman_metin.py
dosya: bolum_16.md boyut: 99098 bayt
sha256: 3aca772785323232 ...
zlib surumu: 1.3.1
farkli bayt sayisi: 119
entropi        : 5.1203 bit/bayt
huffman (veri) : 5.1659 bit/bayt
gzip -9 (tum)  : 2.7050 bit/bayt
sikistirma: huffman 64.6%, gzip 33.8%
```

Sonuçlar üç şey anlatır. Birincisi, Huffman'ın ortalama uzunluğu (`5.1659`) entropinin (`5.1203`) hemen üstündedir; `H ≤ L < H + 1` sınırı burada da geçerlidir. İkincisi, Huffman tek başına metni `%64.6`'ya sıkıştırır; gzip ise `%33.8`'e iner. Bu büyük fark, gzip'in iki aşamalı olmasından gelir: önce LZ77 tekrarlı dizgileri (ör. "kod" kelimesinin tekrarlarını) geri gösterimlerle değiştirir, sonra ortaya çıkan simge dizisini Huffman ile kodlar. Yani Huffman yalnızca simge frekansını kullanır; gzip ise frekansın yanında tekrarı da kullanır. Üçüncüsü, sıkıştırma sınırının entropi olduğu bilinen bir sonuçtur (Shannon); simge frekansından daha fazlasını kullanan yöntemler bu sınırın altına inebilir, çünkü entropi yalnızca tek simgelerin istatistiğini ölçer.

Şekil 18.7, en sık 12 baytın Huffman kod uzunluğunu ideal `-log2 p` uzunluğuyla karşılaştırır. Bu on iki simgenin hiçbirinde Huffman uzunluğu ideal uzunluktan bir bitin altında ayrılır; bu, `H ≤ L < H + 1`'in simge bazındaki bir görünümüdür, ama genel bir kanıt değildir.

![Şekil 18.7: bolum_16.md metninde en sık 12 bayt için ideal kod uzunluğu (-log2 p, gri) ve Huffman kod uzunluğu (bordo). Her simgede fark bir bitin altındadır; tam sayı bit zorunluluğu, ideal değerle Huffman uzunluğu arasındaki farkın kaynağıdır.](gorseller/b18_entropi_uzunluk.png)

## 18.7 Minimum yayan ağaç, kesme özelliği ve Dijkstra

Bir bağlantılı ağırlıklı çizgede **minimum yayan ağaç** (minimum spanning tree, MST), bütün düğümleri birbirine bağlayan, toplam ağırlığı en küçük olan ağaçtır. Bu problemin iki klasik açgözlü çözümü vardır: Kruskal ve Prim. Bunları Bölüm 17'de Union-Find ve öncelik kuyruğuyla gerçekledik; burada yeniden yazmayacağız. Bu bölümün işi, neden doğru olduklarını tek bir ilkeye bağlamaktır.

Bu ilke **kesme özelliğidir** (cut property). Çizgenin düğümlerini iki boş olmayan kümeye, `S` ve `V - S`'ye, bölen bir kesim düşünelim. Bu kesimi geçen kenarlar arasında ağırlığı en küçük olan `e` bir MST'de bulunur. Kanıt, değiş-tokuş argümanıdır. Bir MST `T` alalım ama `e`'yi içermesin. `T`'ye `e`'yi eklersek bir döngü oluşur. Bu döngü kesimi en az iki kez geçer, yani döngüde `e`'den başka kesimi geçen bir `f` kenarı vardır. `f`, `e` ile birlikte kesimden geçtiği için `w(f) ≥ w(e)`dir (`e` en hafif kesim kenarıdır). `T' = T - f + e` kümesi de bir yayan ağaçtır ve `w(T') = w(T) - w(f) + w(e) ≤ w(T)` olur. `T` minimum olduğu için eşitlik olmalı ve `T'` de bir MST'dir; `e` onun içindedir.

Şekil 18.8 bu argümanı gösterir: `S` ve `V - S` iki bölge, `e` kesikli bordo çizgi (en hafif kesim kenarı), `f` ise `T`'nin kesimden geçen kenarıdır.

![Şekil 18.8: Kesme özelliği. e kesimi geçen en hafif kenardır. T içinde e olmayan bir MST'dir; T + e bir döngü oluşturur ve döngüdeki kesim kenarı f çıkarılarak yeni bir ağaç elde edilir, ağırlığı artmaz.](gorseller/b18_kesme.png)

Bu ilkeden iki algoritma doğar. **Kruskal** her adımda kalan kenarlar arasında en hafif olanı alır ve iki farklı bileşeni birleştiriyorsa ekler; eklenen her kenar, bir bileşenin kesiminde en hafif kenardır. **Prim** ise ağacın içindeki düğümler kümesini `S` olarak tutar ve `S`'den dışarıya giden en hafif kenarı ekler; bu da doğrudan kesme özelliğidir. Her iki algoritmanın ayrıntılı gerçeklemesi Bölüm 17'dedir.

Aşağıdaki program kesme özelliğini küçük rastgele çizgelerde sınar. Her çizge için minimum yayan ağaçların hepsini (`n ≤ 5`) kaba kuvvetle listeler, her kesim `(S, V - S)` için kesimi geçen en hafif kenarların en az birinin bir MST'de olduğunu denetler.

```python
# mst_kesme.py: kesme ozelligini kucuk rastgele cizgelerde dogrular.
# Her kesim (S, V - S) icin, kesimi gecen en hafif kenar e, bazi
# minimum yayan agacta yer alir mi? Tum yayan agaclar kaba kuvvetle
# listelenir (n <= 5, bu yuzden denemek ucuzdur).
import itertools
import random


def bagli(n, kenarlar):
    komsu = {i: [] for i in range(n)}
    for u, v, _ in kenarlar:
        komsu[u].append(v)
        komsu[v].append(u)
    gorulen, yigin = {0}, [0]
    while yigin:
        x = yigin.pop()
        for y in komsu[x]:
            if y not in gorulen:
                gorulen.add(y)
                yigin.append(y)
    return len(gorulen) == n


def minimum_yayan_agaclar(n, kenarlar):
    en_az, agaclar = None, []
    for sec in itertools.combinations(kenarlar, n - 1):
        if bagli(n, sec):
            w = sum(k[2] for k in sec)
            if en_az is None or w < en_az:
                en_az, agaclar = w, [sec]
            elif w == en_az:
                agaclar.append(sec)
    return agaclar
```

```python
def main():
    rnd = random.Random(42)
    kesim_testi = ihlal = minimum_olmayan = 0
    for _ in range(300):
        n = rnd.randint(3, 5)
        tum = list(itertools.combinations(range(n), 2))
        m = rnd.randint(n, len(tum))
        secilen = rnd.sample(tum, m)
        kenarlar = [(u, v, rnd.randint(1, 6)) for u, v in secilen]
        if not bagli(n, kenarlar):
            continue
        msts = minimum_yayan_agaclar(n, kenarlar)
        for maske in range(1, (1 << n) - 1):
            S = {i for i in range(n) if maske >> i & 1}
            C = [k for k in kenarlar if (k[0] in S) != (k[1] in S)]
            en_hafif = min(k[2] for k in C)
            for k in C:
                bulundu = any(k in t for t in msts)
                if k[2] == en_hafif:
                    kesim_testi += 1
                    if not bulundu:
                        ihlal += 1
                elif not bulundu:
                    minimum_olmayan += 1
    print("kesim testi (en hafif kenar):", kesim_testi)
    print("ihlal (hicbir MST'de yok):", ihlal)
    print("minimum olmayan kenar, MST'de yok:", minimum_olmayan)


if __name__ == "__main__":
    main()
```

```term
$ python mst_kesme.py
kesim testi (en hafif kenar): 6060
ihlal (hicbir MST'de yok): 0
minimum olmayan kenar, MST'de yok: 6080
```

Çıktı, 300 rastgele çizgede toplam 6060 kesim-en-hafif-kenar testinde hiçbir ihlal olmadığını gösterir. Ayrıca en hafif olmayan kesim kenarlarının 6080 durumda hiçbir MST'de yer almadığı görülür; bu, kesme özelliğinin "en hafif" koşulunun neden gerekli olduğunu gösterir: hafif olmayan kenarlar genellikle MST dışında kalır, ama bu, onların hiçbir zaman dahil edilemeyeceği anlamına gelmez, sadece kuralın onları garanti etmediğini söyler.

**Dijkstra da bir açgözlü algoritmadır.** Kaynak düğümden başlayıp her adımda en küçük tentatif uzaklığa sahip, henüz kesinleşmemiş düğümü kesinleştirir. Bu seçimin doğruluğu, negatif kenar olmadığı sürece, şöyle görülür: `u` kesinleşmemiş düğümler içinde en küçük tentatif uzaklığa sahipse, kaynaktan `u`'ya giden her yol kesinleşmiş kümeden dışarı bir kenarla çıkmak zorundadır. Bu çıkış düğümü `y` olsun. Pozitif (ya da sıfır) ağırlıklarla `y`'nin gerçek uzaklığı, yolun `u`'ya kadar olan kısmından küçük değildir; `y`'nin tentatif uzaklığı en az `u`'nunki kadardır ve bu nedenle `u`'nun uzaklığı gerçek değerindedir. Negatif kenar bu adımı kırar: kesinleşmiş kümeden dışarı çıkan yol, sonradan daha da kısalabilir ve kesinleşmiş bir değeri geri çevirmek gerekir. Ama Dijkstra kesinleşmiş düğümleri değiştirmez.

Şekil 18.9 ve aşağıdaki küçük çizge bu durumu gösterir. Kaynak `S`'den `X`'e `5`, `S`'den `Y`'ye `6`, `Y`'den `X`'e `-3` ağırlıklı kenarlar vardır. Dijkstra önce `X`'i `5` ile kesinleştirir; oysa `S-Y-X` yolu `6 - 3 = 3` eder.

![Şekil 18.9: Negatif kenarda açgözlü seçim başarısızlığı. Solda Dijkstra X'i 5 ile kesinleştirir. Sağda gerçek en kısa yol S-Y-X, uzunluk 3'tür.](gorseller/b18_dijkstra_negatif.png)

Aşağıdaki program Dijkstra'yı bir `heapq` yığınıyla yazar ve Bellman-Ford ile karşılaştırır. Negatif kenarlı rastgele yönlü çizgeler için döngü oluşmasın diye yalnızca küçük düğüm numaralı düğümden büyük olana kenar koyduk (DAG, yönlü çevrimsiz çizge); böylece Bellman-Ford doğrudur.

```python
# dijkstra_negatif.py: Dijkstra'nin acgozlu secimi negatif kenarda
# neden bozulur? Kucuk bir cizgede Dijkstra ve Bellman-Ford sonucunu
# karsilastirir; rastgele DAG'lerde (dongu yok) istatistik verir.
import heapq
import random

INF = float("inf")


def dijkstra(n, kenarlar, s):
    komsu = [[] for _ in range(n)]
    for u, v, w in kenarlar:
        komsu[u].append((v, w))
    dist = [INF] * n
    dist[s] = 0
    kesin = [False] * n
    yigin = [(0, s)]
    while yigin:
        d, u = heapq.heappop(yigin)
        if kesin[u]:
            continue
        kesin[u] = True           # bir kez kesinlesen dugum degismez
        for v, w in komsu[u]:
            if not kesin[v] and d + w < dist[v]:
                dist[v] = d + w
                heapq.heappush(yigin, (dist[v], v))
    return dist


def bellman_ford(n, kenarlar, s):
    dist = [INF] * n
    dist[s] = 0
    for _ in range(n - 1):
        for u, v, w in kenarlar:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    return dist
```

```python
def main():
    # 0 = S, 1 = X, 2 = Y
    cizge = [(0, 1, 5), (0, 2, 6), (2, 1, -3)]
    print("Dijkstra     :", dijkstra(3, cizge, 0))
    print("Bellman-Ford :", bellman_ford(3, cizge, 0))
    rnd = random.Random(42)
    hata_pozitif = hata_negatif = 0
    for _ in range(300):
        n = rnd.randint(3, 7)
        kenar = []
        for u in range(n):
            for v in range(u + 1, n):
                if rnd.random() < 0.5:
                    kenar.append((u, v, rnd.randint(1, 9)))
        if dijkstra(n, kenar, 0) != bellman_ford(n, kenar, 0):
            hata_pozitif += 1
        neg = [(u, v, rnd.randint(-3, 6)) for u, v, _ in kenar]
        if dijkstra(n, neg, 0) != bellman_ford(n, neg, 0):
            hata_negatif += 1
    print("300 DAG, pozitif kenar, hata:", hata_pozitif)
    print("300 DAG, negatif kenar, hata:", hata_negatif)


if __name__ == "__main__":
    main()
```

```term
$ python dijkstra_negatif.py
Dijkstra     : [0, 5, 6]
Bellman-Ford : [0, 3, 6]
300 DAG, pozitif kenar, hata: 0
300 DAG, negatif kenar, hata: 8
```

Çıktı, küçük çizgede Dijkstra'nın `X = 5` (yanlış), Bellman-Ford'un `X = 3` (doğru) bulduğunu gösterir. 300 rastgele DAG'de yalnızca pozitif kenarlarla hata sayısı sıfırdır; negatif kenarlarla 8 hata vardır. Yani Dijkstra'nın açgözlü seçimi, pozitif ağırlıklarda kanıtlanabilir biçimde doğrudur ve negatif kenar varlığında doğruluğunu kaybeder. Bu nedenle negatif kenarlı çizgeler için Bellman-Ford (Bölüm 17) kullanılır.

## 18.8 Matroidler, yaklaşım algoritmaları ve tek geçişli greedy

Bu bölümde gördüğümüz açgözlü algoritmaların ortak yanı, bir **bağımsızlık** kavramı üzerinde çalışmalarıdır: etkinlikler birlikte uyumluysa, kenarlar ormansa, eşyalar kapasiteyi aşmıyorsa birlikte "bağımsız"dırlar. Bu soyutlamanın adı **matroiddir**. Bir matroid `(E, I)` ikilisidir; `E` sonlu bir küme, `I` bağımsız alt kümelerin ailesidir ve iki kuralı sağlar: bağımsız bir kümenin her alt kümesi de bağımsızdır (kalıtımsallık) ve iki bağımsız küme `A`, `B` için `|A| < |B|` ise `B`'den `A`'ya eklenebilecek bir eleman vardır (değiş-tokuş aksiyomu).

Matroidin açgözlü bağlantısı bilinen bir sonuçtur (Rado 1957, Edmonds 1971): ağırlıklı bir matroidde, elemanları ağırlığa göre sırayla alıp bağımsız kaldığı sürece ekleyen açgözlü algoritma, **her** ağırlık fonksiyonu için optimal bir bağımsız küme verir. Üstelik bu özellik matroidi tanımlar: açgözlü her ağırlık için çalışıyorsa, küme bir matroiddir. Bunun örnekleri şunlardır: **grafik matroidi** (kenarlar, döngü oluşturmayan kümeler; Kruskal'ın açgözlüsünü açıklar) ve **bölümlü matroid** (her renkten en fazla belli sayıda eleman). Bu bölümde yalnızca tanımı ve sezgiyi veriyoruz; tam kanıt için bir kombinatorik kitabına bakılmalıdır.

**Yaklaşım olarak greedy.** Her problemde açgözlü optimum vermez; ama çoğu zaman makul bir çözüm verir ve bunun ne kadar iyi olduğu bir **yaklaşım oranı** ile ölçülür. Küme örtme probleminde (set cover) açgözlü, en çok yeni elemanı örten kümeyi seçer. Bilinen bir sonuç, bu açgözlünün optimumun `H_n ≤ ln n + 1` katından kötü olmadığını söyler (Johnson 1974, Lovász 1975, Chvátal 1979). Bu sonucu burada kanıtlamıyor ve bir program ile denemiyoruz; yalnızca bir yaklaşım garantisinin nasıl göründüğünü bilmen için anıyoruz.

**Tek geçişli açgözlü.** Bazı problemlerde seçim, dizinin tek bir geçişinde yapılır. Çözümlü Örnek 3'teki Jump Game II buna girer: her konumdan erişilebilen en uzak noktayı izleyerek sıçrama sayısını tek geçişte bulur. Klasik "benzin istasyonu" problemi de benzerdir: toplam yakıt toplam tüketime eşit ya da fazlaysa, bir başlangıç istasyonu vardır ve açgözlü bir taramayla bulunur (bilinen sonuç).

Aşağıdaki tablo bu bölümdeki kararları özetler. Son sütun, her biri için kullandığımız kanıt tekniğini gösterir.

| Problem | Açgözlü kural | Doğru mu? | Kanıt / sınama |
|---|---|---|---|
| Etkinlik seçimi | Bitişi en erken olan | Evet | Değiş-tokuş, önde kalma |
| Etkinlik seçimi | Başlangıcı en erken olan | Hayır | Karşı örnek (Şekil 18.3) |
| Aralık bölümleme | Başlangıca göre, boş odayı kullan | Evet | Derinlik alt sınırı |
| Kesirli sırt çantası | Değer/ağırlık oranı | Evet | Değiş-tokuş |
| 0/1 sırt çantası | Değer/ağırlık oranı | Hayır | Karşı örnek (160 / 220) |
| Para bozma | En büyük parayı al | Kanonikse evet | Kozen–Zaks sınırı |
| Gecikme (`L_max`) | Son teslimi en erken | Evet | Değiş-tokuş |
| Ağırlıklı tamamlama | `p/w` oranı artan | Evet | Adjacent-swap |
| Huffman | En küçük iki kökü birleştir | Evet | Değiş-tokuş, tümevarım |
| MST | Kesim/döngü kuralı | Evet | Kesme özelliği |
| En kısa yol | En yakın kesinleşmemiş düğüm | Yalnızca pozitif kenar | Karşı örnek (Şekil 18.9) |

## 18.9 Gerçek dünya: DEFLATE, zamanlayıcılar ve önbellek

**DEFLATE ve gzip.** DEFLATE biçimi (RFC 1951), gzip ve zlib'in ortak sıkıştırma biçimidir. İçinde iki Huffman kodu kullanılır: biri harf ve uzunluk simgeleri, diğeri mesafe simgeleri için. Bu kodlarda her kod uzunluğu en fazla 15 bit olabilir; bu sınır, kodların kodlayıcıda ve çözücüde temsil edilmesini kolaylaştırır. zlib 1.3.1 kaynağında bu değer `deflate.h` dosyasında `#define MAX_BITS 15` olarak yer alır (satır 52; kaynağı indirip denetledik). Kod Okuma bölümünde, bu sınırın Huffman ağacını kuran kodda nasıl uygulandığını göreceksin.

**Zamanlayıcılar.** İşletim sistemi zamanlayıcıları Bölüm 26'da ayrıntılı işlenecek. Burada iki açgözlü fikir görünür: gerçek zamanlı sistemlerde son teslimi en erken olan işi önce çalıştırmak (EDF) ve ağırlıklı ortalama bekleme süresini azaltmak için Smith kuralı. Bu bölümdeki Smith ve EDF sınamaları, bu kuralların küçük iş kümelerinde neden doğru olduğunu gösterir; gerçek zamanlayıcılar ise kesilebilir (preemptive) işlerle çalışır ve bu, analizi değiştirir.

**Önbellek değiştirme (Bélády).** Sanal bellek ve işlemci önbelleği, sınırlı sayıda sayfayı tutar. Yeni bir sayfa gelip yer yoksa, hangi sayfa çıkarılmalıdır? En iyi açgözlü karar, **en uzak gelecekte kullanılacak** sayfayı çıkarmaktır; bu, Bélády'nin (1966) optimal algoritmasıdır. Ama bu, geleceği bilmeyi gerektirir; bu yüzden gerçek sistemler **LRU** (en uzun süredir kullanılmayan) gibi bir yaklaşım kullanır. LRU, geçmişe bakarak geleceği tahmin eden bir açgözlüdür ve optimum değildir.

Aşağıdaki program üç algoritmayı karşılaştırır: FIFO, LRU ve Bélády. Bélády'nin optimalliğini, her kurban seçimini deneyen bir tam aramayla küçük dizilerde doğrular. Ayrıca FIFO'da ünlü Bélády anomalisini gösterir: çerçeve sayısını artırmak hata sayısını artırabilir.

```python
# belady.py: onbellek degistirme. FIFO, LRU ve Belady (en uzak
# gelecek). Belady'nin en az hatayi verdigi, tum kurban secimlerini
# deneyen bir kaba kuvvet ile dogrulanir (kucuk dizilerde).
import random
from functools import lru_cache


def hata_say(seq, k, kurban):
    onb, hata = [], 0
    for i, p in enumerate(seq):
        if p in onb:
            continue
        hata += 1
        if len(onb) == k:
            onb.remove(kurban(onb, i, seq))
        onb.append(p)
    return hata


def fifo_kurban(onb, i, seq):
    return onb[0]


def lru_kurban(onb, i, seq):
    def son_kullanim(p):
        for j in range(i - 1, -1, -1):
            if seq[j] == p:
                return j
        return -1
    return min(onb, key=son_kullanim)


def belady_kurban(onb, i, seq):
    def sonraki(p):
        for j in range(i + 1, len(seq)):
            if seq[j] == p:
                return j
        return float("inf")
    return max(onb, key=sonraki)
```

```python
def en_az_hata(seq, k):
    @lru_cache(maxsize=None)
    def f(i, onb):
        if i == len(seq):
            return 0
        p = seq[i]
        if p in onb:
            return f(i + 1, onb)
        if len(onb) < k:
            return 1 + f(i + 1, onb | {p})
        return 1 + min(f(i + 1, (onb - {q}) | {p}) for q in onb)
    return f(0, frozenset())


def main():
    seq = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
    for k in (3, 4):
        print("k=%d FIFO:%d LRU:%d Belady:%d" % (
            k, hata_say(seq, k, fifo_kurban),
            hata_say(seq, k, lru_kurban),
            hata_say(seq, k, belady_kurban)))
    rnd = random.Random(42)
    hata_b = hata_l = 0
    for _ in range(300):
        s = [rnd.randint(1, 6) for _ in range(rnd.randint(4, 12))]
        k = rnd.randint(2, 3)
        opt = en_az_hata(tuple(s), k)
        if hata_say(s, k, belady_kurban) != opt:
            hata_b += 1
        if hata_say(s, k, lru_kurban) != opt:
            hata_l += 1
    print("300 dizi: Belady optimumdan farkli:", hata_b)
    print("300 dizi: LRU optimumdan farkli   :", hata_l)


if __name__ == "__main__":
    main()
```

```term
$ python belady.py
k=3 FIFO:9 LRU:10 Belady:7
k=4 FIFO:10 LRU:8 Belady:6
300 dizi: Belady optimumdan farkli: 0
300 dizi: LRU optimumdan farkli   : 155
```

Çıktı, bu bölümün en öğretici sonuçlarından birini verir: `k=3` çerçevede FIFO 9, LRU 10 hata yapar; `k=4`'te FIFO 10 hata yapar, yani çerçeve artınca hata da arttı. Bélády algoritması her iki durumda da en az hatayı yapar. 300 rastgele dizide Bélády her zaman tam aramanın optimumuna eşittir (0 fark); LRU ise 155 dizide optimumdan farklıdır. LRU'nun yaklaşım olduğu, ama optimum olmadığı böylece sayısal olarak görülür.

## Çözümlü Örnekler

Bu bölümdeki dört örnek ★ zorluğundan ★★★'e doğru ilerler. Her birinde Bölüm 5'teki altı adımı izleyeceğiz. Adım 6'da elle iz sürme tablosu olacak; tablodaki değerler, örnekte verilen programın çıktısıyla aynıdır. Önce kendi kâğıdında ilk üç adımı dene.

### Örnek 1 (★): En fazla toplantı

**Problem:** `n` toplantının her biri `[s, e)` zaman aralığında yapılır. Birbiriyle çakışmayan en çok toplantıyı seç. Bu, etkinlik seçimi problemidir; Bölüm 18.2'de bitiş sıralı açgözlünün doğruluğunu kanıtladık.

**Adım 1 — Anla.** Girdi bir aralık listesidir; çıktı seçilen aralıkların sayısı (ve isterse kümesi). Kenar durumlar: boş liste (cevap 0), tek aralık (cevap 1), hepsi aynı anda başlayan aralıklar (cevap 1).

**Adım 2 — Örnekle.** Sekiz toplantı: `(1,4), (3,5), (0,6), (5,7), (3,9), (5,9), (6,10), (8,11)`. Bunlardan en az üç tanesi çakışmadan seçilebilir: `(1,4), (5,7), (8,11)`.

**Adım 3 — Kaba çöz.** Her alt kümeyi dene (`2^8 = 256` alt küme) ve çakışmayanların en büyüğünü al. Doğru, ama `n` büyüdükçe üstel.

**Adım 4 — Örüntü.** Bitişi en erken olan toplantıyı seç; ondan sonra başlayan ve bitişi en erken olanı seç; tekrarla. Bu, Bölüm 18.2'deki değiş-tokuş ve Bölüm 18.3'teki önde kalma argümanıyla doğrudur. Sıralama `O(n log n)`, geri kalan tek geçiş `O(n)`dir.

**Adım 5 — İyileştir.** Sıralamadan sonra tek bir döngü yeter ve yalnızca son seçilen bitişi tutmak gerekir; yardımcı bir liste tutmaya gerek yoktur. Bellek `O(1)` ek alandır (çıktı listesi hariç).

```python
# ornek1_toplanti.py: en fazla toplanti (activity selection).
# Bitis zamanina gore sirala; baslangici son bitisten once olani
# atla.
import random


def en_fazla_toplanti(t):
    secilen, son = [], float("-inf")
    for s, e in sorted(t, key=lambda x: x[1]):
        if s >= son:
            secilen.append((s, e))
            son = e
    return secilen


def kaba(t):
    # tum altkumeler; en buyuk uyumlu olanin boyutu ve kumesi
    n, en_iyi, kume = len(t), 0, []
    for maske in range(1 << n):
        sec = sorted(t[i] for i in range(n) if maske >> i & 1)
        if all(sec[i + 1][0] >= sec[i][1]
               for i in range(len(sec) - 1)):
            if len(sec) > en_iyi:
                en_iyi, kume = len(sec), sec
    return en_iyi, kume
```

```python
def main():
    t = [(1, 4), (3, 5), (0, 6), (5, 7), (3, 9), (5, 9), (6, 10),
         (8, 11)]
    print("toplantilar:", t[:4])
    print("            ", t[4:])
    son = float("-inf")
    for s, e in sorted(t, key=lambda x: x[1]):
        karar = "secildi" if s >= son else "cakisiyor"
        print("  (%d,%2d) son=%5s -> %s" % (s, e, son, karar))
        if s >= son:
            son = e
    print("secilen    :", en_fazla_toplanti(t))
    print("kaba kuvvet:", kaba(t)[0])
    rnd = random.Random(42)
    hata = ihlal = 0
    for _ in range(300):
        n = rnd.randint(1, 9)
        a = []
        for _ in range(n):
            s = rnd.randint(0, 15)
            a.append((s, s + rnd.randint(1, 6)))
        g = en_fazla_toplanti(a)
        boyut, kume = kaba(a)
        if len(g) != boyut:
            hata += 1
        # onde kalma: k. bitis, optimum kumesinin k. bitisinden once
        # ya da ona esit olmali
        ge = sorted(e for _, e in g)
        oe = sorted(e for _, e in kume)
        if any(x > y for x, y in zip(ge, oe)):
            ihlal += 1
    print("300 rastgele ornek, optimumdan farkli:", hata)
    print("300 rastgele ornek, onde kalma ihlali:", ihlal)


if __name__ == "__main__":
    main()
```

**Adım 6 — Doğrula.** Program şu çıktıyı verir:

```term
$ python ornek1_toplanti.py
toplantilar: [(1, 4), (3, 5), (0, 6), (5, 7)]
             [(3, 9), (5, 9), (6, 10), (8, 11)]
  (1, 4) son= -inf -> secildi
  (3, 5) son=    4 -> cakisiyor
  (0, 6) son=    4 -> cakisiyor
  (5, 7) son=    4 -> secildi
  (3, 9) son=    7 -> cakisiyor
  (5, 9) son=    7 -> cakisiyor
  (6,10) son=    7 -> cakisiyor
  (8,11) son=    7 -> secildi
secilen    : [(1, 4), (5, 7), (8, 11)]
kaba kuvvet: 3
300 rastgele ornek, optimumdan farkli: 0
300 rastgele ornek, onde kalma ihlali: 0
```

Aşağıdaki iz tablosu, çıktıdaki satırları elle yeniden üretir; son sütun, bu etkinliğin seçilip seçilmediğini gösterir.

| Sıra | Toplantı | Son bitiş | Karar |
|---|---|---|---|
| 1 | (1,4) | -inf | seçildi, son = 4 |
| 2 | (3,5) | 4 | çakışıyor (3 < 4) |
| 3 | (0,6) | 4 | çakışıyor (0 < 4) |
| 4 | (5,7) | 4 | seçildi, son = 7 |
| 5 | (3,9) | 7 | çakışıyor |
| 6 | (5,9) | 7 | çakışıyor |
| 7 | (6,10) | 7 | çakışıyor |
| 8 | (8,11) | 7 | seçildi, son = 11 |

Programın ikinci sınaması, 300 rastgele örnekte açgözlü sayının kaba kuvvetle eşleştiğini ve açgözlünün her `k` için `k`-inci bitişinin optimumunkinden önce ya da eşit olduğunu (önde kalma) doğrular; ikisinde de hata sıfırdır.

**Bunu AI'sız yazabilir misin?** Aynı problemi, toplantılar yerine her biri `(başlangıç, bitiş, değer)` taşıyan etkinlikler için düşün: her etkinliğin bir değeri var ve amaç toplam değeri en büyük yapmak. Bitiş sıralı açgözlü hâlâ optimal mi? Hangi karşı örnek bunu bozar?

### Örnek 2 (★★): Aralık bölümleme ve sweep line

**Problem:** `n` ders `[s, e)` aralıklarıyla verilmiş. Çakışan dersler aynı odada olamaz. En az kaç oda gerekir ve her ders hangi odaya atanmalıdır?

**Adım 1 — Anla.** Girdi aralık dizisi, çıktı oda sayısı ve atamalardır. Kenar durumlar: boş dizi (0 oda), tümü çakışan aralıklar (`n` oda), hiç çakışmayan aralıklar (1 oda).

**Adım 2 — Örnekle.** Yedi aralık: `[1,4), [2,6), [3,5), [5,8), [7,9), [6,10), [9,12)`. En büyük derinlik 3'tür: `t = 3` anında `[1,4), [2,6), [3,5)` birlikte aktiftir.

**Adım 3 — Kaba çöz.** Tüm atamaları dene (`k^n` olasılık) ve en az odalı geçerli olanı bul. Üstel.

**Adım 4 — Örüntü.** Başlangıca göre sırala; her ders için en erken boşalan odayı kontrol et. Boş varsa onu kullan, yoksa yeni oda aç. En erken boşalan oda bir min-yığınla bulunur. Optimallik, Bölüm 18.3'teki derinlik alt sınırı ve açılan odaların aktif aralıkla kanıtlanmasıyla gelir.

**Adım 5 — İyileştir.** Yığını yalnızca oda bitişlerini tutacak biçimde küçük tut. Dolu bir odanın bitişini yeni dersin bitişiyle değiştirmek, yığından bir çıkarma ve bir ekleme yerine tek bir "tepe değiştirip aşağı süzme" ile yapılır. Toplam `O(n log n)`.

Aşağıdaki C programı, C11'de yığını bir dizi üzerinde kendimiz kurar; `qsort` kararlı değildir, ama algoritma sıralamanın kararlılığına ihtiyaç duymaz (aynı başlangıçlı dersler herhangi bir sırada işlenir ve yine de doğru çalışır). Ana programda ayrıca bir alt sınır (en büyük derinlik) ve bir geçerlilik denetimi vardır.

```c
/* ornek2_oda.c: aralik bolumleme (interval partitioning).
 * Aralik [s, e) yari acik. Baslangica gore sirala; her aralik icin
 * en erken biten odayi kontrol et: bitisi <= s ise o odayi kullan,
 * degilse yeni oda ac. Oda bitisleri bir min-yigindadir.
 * Derleme (WSL): gcc -O2 -Wall -Wextra -std=c11 ornek2_oda.c
 */
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int s, e;   /* baslangic ve bitis (e > s) */
    int oda;    /* atanan oda numarasi */
} Aralik;

typedef struct {
    int bitis;  /* odanin mevcut bitis zamani */
    int oda;    /* oda numarasi */
} Oda;

typedef struct {
    Oda *a;
    size_t n;
} Yigin;

static void yukari(Yigin *y, size_t i) {
    while (i > 0) {
        size_t p = (i - 1) / 2;
        if (y->a[p].bitis <= y->a[i].bitis) break;
        Oda t = y->a[p];
        y->a[p] = y->a[i];
        y->a[i] = t;
        i = p;
    }
}
```

Yığının yukarı süzme işlemi, yeni oda bitişi eklendikten sonra çocuğun ebeveyninden küçükse yer değiştirmeyi sürdürür.

```c
static void asagi(Yigin *y, size_t i) {
    for (;;) {
        size_t sol = 2 * i + 1, sag = sol + 1, en = i;
        if (sol < y->n && y->a[sol].bitis < y->a[en].bitis)
            en = sol;
        if (sag < y->n && y->a[sag].bitis < y->a[en].bitis)
            en = sag;
        if (en == i) break;
        Oda t = y->a[en];
        y->a[en] = y->a[i];
        y->a[i] = t;
        i = en;
    }
}

static int s_karsilastir(const void *x, const void *y) {
    const Aralik *a = x, *b = y;
    return (a->s > b->s) - (a->s < b->s);
}
```

```c
/* Kullanilan oda sayisini dondurur; bellek hatasinda -1. */
static int oda_ata(Aralik *v, size_t n) {
    Yigin y;
    int oda_say = 0;
    y.a = malloc((n ? n : 1) * sizeof *y.a);
    if (y.a == NULL) return -1;
    y.n = 0;
    qsort(v, n, sizeof *v, s_karsilastir);
    for (size_t i = 0; i < n; i++) {
        if (y.n > 0 && y.a[0].bitis <= v[i].s) {
            v[i].oda = y.a[0].oda;  /* en erken biten odayi devral */
            y.a[0].bitis = v[i].e;  /* bitisi guncelle, asagi suz */
            asagi(&y, 0);
        } else {
            v[i].oda = oda_say++;   /* yeni oda ac */
            y.a[y.n].bitis = v[i].e;
            y.a[y.n].oda = v[i].oda;
            y.n++;
            yukari(&y, y.n - 1);
        }
    }
    free(y.a);
    return oda_say;
}
```

Algoritma bu fonksiyonda toplanır: sıralama, sonra her ders için yığının kökünü (en erken boşalan oda) kontrol eder. Kökün bitişi dersin başlangıcından küçük ya da eşitse odayı devralır ve kökün bitişini günceller; değilse yeni oda açar.

```c
/* Alt sinir: bir noktada ortusen en fazla aralik sayisi. */
static int derinlik(const Aralik *v, size_t n) {
    int en = 0;
    for (size_t i = 0; i < n; i++) {
        int c = 0;
        for (size_t j = 0; j < n; j++)
            if (v[j].s <= v[i].s && v[i].s < v[j].e) c++;
        if (c > en) en = c;
    }
    return en;
}
```

```c
/* Ayni odadaki iki aralik cakismiyor mu? */
static int gecerli(const Aralik *v, size_t n) {
    for (size_t i = 0; i < n; i++)
        for (size_t j = i + 1; j < n; j++)
            if (v[i].oda == v[j].oda &&
                !(v[i].e <= v[j].s || v[j].e <= v[i].s))
                return 0;
    return 1;
}
```

```c
/* Xorshift32, sabit tohum 42: her calistirmada ayni sayilar. */
static uint32_t durum = 42u;

static uint32_t rasgele(void) {
    durum ^= durum << 13;
    durum ^= durum >> 17;
    durum ^= durum << 5;
    return durum;
}
```

Son kısım, sabit tohumlu bir xorshift üretecidir: her çalıştırmada aynı 300 rastgele girdi üretilir. Ana program önce yedi dersin örneğini, sonra bu 300 girdiyi işler.

```c
int main(void) {
    Aralik ornek[] = {
        {1, 4, 0}, {2, 6, 0}, {3, 5, 0}, {5, 8, 0},
        {7, 9, 0}, {6, 10, 0}, {9, 12, 0}
    };
    size_t n = sizeof ornek / sizeof ornek[0];
    int k = oda_ata(ornek, n);
    if (k < 0) return 1;
    printf("oda sayisi: %d, derinlik: %d\n", k, derinlik(ornek, n));
    for (size_t i = 0; i < n; i++)
        printf("[%2d,%2d) oda %d\n", ornek[i].s, ornek[i].e,
               ornek[i].oda);
    printf("gecerli: %s\n", gecerli(ornek, n) ? "evet" : "hayir");

    int fark = 0, gecersiz = 0;
    for (int t = 0; t < 300; t++) {
        size_t m = 1 + rasgele() % 12;
        Aralik *v = malloc(m * sizeof *v);
        if (v == NULL) return 1;
        for (size_t i = 0; i < m; i++) {
            v[i].s = (int)(rasgele() % 20);
            v[i].e = v[i].s + 1 + (int)(rasgele() % 6);
            v[i].oda = -1;
        }
        int r = oda_ata(v, m);
        if (r < 0) return 1;
        if (r != derinlik(v, m)) fark++;
        if (!gecerli(v, m)) gecersiz++;
        free(v);
    }
    printf("300 rastgele: derinlik farki %d, gecersiz %d\n",
           fark, gecersiz);
    return 0;
}
```

Derlemeyi WSL içinde gcc ile yaptık; ardından aynı kaynağı AddressSanitizer ve UBSan ile derledik. Her iki çalıştırma da aynı çıktıyı verdi ve sanitizer hatası bildirmedi.

```term
$ gcc -O2 -Wall -Wextra -std=c11 ornek2_oda.c -o ornek2_oda
$ ./ornek2_oda
oda sayisi: 3, derinlik: 3
[ 1, 4) oda 0
[ 2, 6) oda 1
[ 3, 5) oda 2
[ 5, 8) oda 0
[ 6,10) oda 2
[ 7, 9) oda 1
[ 9,12) oda 0
gecerli: evet
300 rastgele: derinlik farki 0, gecersiz 0
```

```term
$ export ASAN=-fsanitize=address,undefined
$ gcc -g -O1 -std=c11 -Wall -Wextra $ASAN ornek2_oda.c -o ornek2_asan
$ ./ornek2_asan
oda sayisi: 3, derinlik: 3
[ 1, 4) oda 0
[ 2, 6) oda 1
[ 3, 5) oda 2
[ 5, 8) oda 0
[ 6,10) oda 2
[ 7, 9) oda 1
[ 9,12) oda 0
gecerli: evet
300 rastgele: derinlik farki 0, gecersiz 0
```

**Adım 6 — Doğrula.** Örnek çıktısı, Şekil 18.4'teki üç odayı verir. Elle iz sürme tablosu, sıralanmış derslerin ve oda atamalarının çıktıyla aynı olduğunu gösterir.

| Ders | Başlangıç | Bitiş | Oda | Oda kökünün bitişi (atamadan sonra) |
|---|---|---|---|---|
| 1 | 1 | 4 | 0 | 4 |
| 2 | 2 | 6 | 1 | 6 |
| 3 | 3 | 5 | 2 | 5 |
| 4 | 5 | 8 | 0 | 8 |
| 5 | 6 | 10 | 2 | 10 |
| 6 | 7 | 9 | 1 | 9 |
| 7 | 9 | 12 | 0 | 12 |

Beşinci ders (6–10) için yığının kökü, o anda en erken biten oda olan oda 2'dir (bitişi 5, `5 ≤ 6`). Oda 1'in bitişi 6 ve oda 0'ınki 8'dir; kökü bulmak için bu üç değeri karşılaştırmak yerine yığın bunu tek adımda verir. Bu ayrıntıyı elle izlemek, yığının neden gerekli olduğunu kavramanın en iyi yoludur.

**Bunu AI'sız yazabilir misin?** Derslerin yalnızca bitişi ve başlangıcı verildiğinde, en büyük derinliği `O(n log n)` içinde, yığın kullanmadan, sıralı iki dizi ve bir sayaçla hesaplayabilir misin? Bu iki yöntemin karmaşıklığını karşılaştır.

### Örnek 3 (★★): Jump Game II: en az sıçrama

**Problem:** `a[i]`, `i` konumundan en fazla kaç adım ileri gidilebileceğini gösterir. Başlangıç `0`, hedef `n-1`. En az kaç sıçrama gerekir? Hedef erişilemezse problem kapsam dışıdır.

**Adım 1 — Anla.** Girdi negatif olmayan tamsayı dizisi; çıktı sıçrama sayısı. Kenar durumlar: `n = 1` (0 sıçrama), `a[0] = 0` ve `n > 1` (erişilemez).

**Adım 2 — Örnekle.** `[2, 3, 1, 1, 4]`: `0`'dan `1` ya da `2`'ye, oradan `4`'e. İki sıçrama.

**Adım 3 — Kaba çöz.** Her konumdan olası tüm sıçramaları dene (BFS). Doğru ve `O(n²)`.

**Adım 4 — Örüntü.** Her "seviye" (bir sıçramayla erişilen konumlar kümesi) ardışık bir aralıktır. Mevcut seviyenin sonuna geldiğimizde, o zamana kadar görülen en uzak erişim yeni seviyenin sonu olur ve sıçrama sayısını bir artırırız. Bu, BFS'in tek geçişli hâlidir.

**Adım 5 — İyileştir.** Bir kez tarama yapılır; her konum için yalnızca `en_uzak` ve `son` değişkenleri tutulur. Toplam `O(n)`, ek bellek `O(1)`.

```python
# ornek3_sicrama.py: Jump Game II. a[i] = i'den en fazla kac adim
# ilerlenebilir. Hedef n-1'e en az kac sicrama? Tek gecisli acgozlu
# cozum; BFS ile kaba dogrulama (dugumler = indeksler).
import random
from collections import deque


def en_az_sicrama(a, izle=False):
    n = len(a)
    sicrama, simdiki_son, en_uzak = 0, 0, 0
    for i in range(n - 1):
        en_uzak = max(en_uzak, i + a[i])
        if i == simdiki_son:
            sicrama += 1
            simdiki_son = en_uzak
        if izle:
            print("i=%d a=%d en_uzak=%d sicrama=%d son=%d"
                  % (i, a[i], en_uzak, sicrama, simdiki_son))
        if simdiki_son >= n - 1:
            break
    return sicrama


def bfs_kaba(a):
    n = len(a)
    if n == 1:
        return 0
    dist = [-1] * n
    dist[0] = 0
    kuyruk = deque([0])
    while kuyruk:
        i = kuyruk.popleft()
        for j in range(i + 1, min(n - 1, i + a[i]) + 1):
            if dist[j] == -1:
                dist[j] = dist[i] + 1
                kuyruk.append(j)
    return dist[n - 1]
```

```python
def main():
    ornek = [2, 3, 1, 1, 4]
    print("dizi:", ornek)
    print("izleme:")
    sonuc = en_az_sicrama(ornek, izle=True)
    print("en az sicrama:", sonuc, "| BFS:", bfs_kaba(ornek))
    rnd = random.Random(42)
    hata = atlanan = 0
    for _ in range(300):
        n = rnd.randint(1, 10)
        a = [rnd.randint(0, 4) for _ in range(n)]
        b = bfs_kaba(a)
        if b == -1:
            atlanan += 1       # hedefe ulasilamaz: kapsam disi
            continue
        if en_az_sicrama(a) != b:
            hata += 1
    print("300 dizi (ulasilamayan atlanan):", atlanan,
          "hata:", hata)


if __name__ == "__main__":
    main()
```

**Adım 6 — Doğrula.** Program izleme modunda çalışır ve her adımdan sonra durumu yazdırır:

```term
$ python ornek3_sicrama.py
dizi: [2, 3, 1, 1, 4]
izleme:
i=0 a=2 en_uzak=2 sicrama=1 son=2
i=1 a=3 en_uzak=4 sicrama=1 son=2
i=2 a=1 en_uzak=4 sicrama=2 son=4
en az sicrama: 2 | BFS: 2
300 dizi (ulasilamayan atlanan): 74 hata: 0
```

Aşağıdaki tablo, `[2, 3, 1, 1, 4]` için izlemeyi elle yeniden üretir.

| `i` | `a[i]` | `en_uzak` | `sıçrama` | `son` |
|---|---|---|---|---|
| 0 | 2 | 2 | 1 | 2 |
| 1 | 3 | 4 | 1 | 2 |
| 2 | 1 | 4 | 2 | 4 |

`i = 0`'da `son = 0` olduğundan birinci sıçrama yapılır ve seviye sonu `2` olur. `i = 2` seviyenin sonuna gelir; `en_uzak = 4 ≥ n-1` olduğu için ikinci sıçrama yeterlidir. Rastgele 300 dizide (tohum 42) hedefe ulaşılabilen 226 dizinin tamamında açgözlü sonuç BFS'le eşleşir; 74 ulaşılamaz dizi kapsam dışıdır.

**Bunu AI'sız yazabilir misin?** Aynı problemi, her sıçramanın bir maliyetinin olduğu ama konuma göre değiştiği (`c[i]`) bir sürümde düşün. Açgözlü seviye yaklaşımı hâlâ çalışır mı? Hangi girdide başarısız olduğunu bir örnekle göster.

### Örnek 4 (★★★): Görev zamanlayıcı: soğuma süreli

**Problem:** Bir işlemci `n` birimlik bir soğuma süresiyle aynı görevi iki kez ardı ardına çalıştıramaz. Her görev türünün sayısı verildiğinde, bütün görevleri tamamlayan en kısa süre nedir? Boş bekleme adımları da sayılır.

**Adım 1 — Anla.** Girdi bir görev dizisi (harfler) ve tamsayı `n`; çıktı toplam zaman birimi sayısı. Kenar durumlar: tek görev türü (`k` tekrar, `(k-1)(n+1) + 1` zaman), `n = 0` (bekleme yok, yalnızca dizi uzunluğu).

**Adım 2 — Örnekle.** `AAABBBCC`, `n = 2`. `A` en sık görünen görevdir; üç kez çalışmalı ve her çalışmadan sonra iki birim beklemelidir.

**Adım 3 — Kaba çöz.** Her adımda hangi görevin (ya da beklemenin) seçileceğini tüm olasılıklar üzerinden ara: durum uzayı (kalan sayılar, soğuma süreleri) üstel ama küçük örnekler için yeterlidir. Doğru ama bu bölümdeki programda yalnızca doğrulama olarak kullanılır.

**Adım 4 — Örüntü.** Her adımda, o an hazır olan görevler arasından **en çok kalan sayıya sahip** olanı çalıştır; hazır görev yoksa bekle. Ayrıca kapalı bir formül vardır: en çok görülen görev `m` kez ve bu sayıda sahip görev `k` tane ise, cevap `max(|dizi|, (m-1)(n+1) + k)`dir.

**Adım 5 — İyileştir.** Açgözlü simülasyonu bir yığın ve bir bekleme kuyruğuyla yaparız: hazır olan görevler yığında, soğumadakiler bekleme listesinde. Simülasyon `O(T log g)` (`T` toplam süre, `g` görev türü sayısı) çalışır; kapalı formül ise `O(g)`dir. Bu iki yöntemin aynı sonucu verdiğini programda doğruluyoruz.

```python
# gorev_zamanlayici.py: ayni gorevler arasinda n adim soguma suresi
# olan zamanlayici. Her adimda hazir olan, en cok kalan gorevi
# calistir; hazir yoksa bekle. Sonuc uc yolla dogrulanir: acgozlu
# simulasyon, kapali formul ve tum durumlari tarayan tam arama (BFS).
import heapq
import random
from collections import Counter


def simulasyon(gorevler, n, plan=None):
    kalan = Counter(gorevler)
    yigin = [(-c, g) for g, c in kalan.items()]
    heapq.heapify(yigin)
    bekleme = []              # (hazir_olacagi_an, -kalan, gorev)
    t = 0
    while yigin or bekleme:
        while bekleme and bekleme[0][0] <= t:
            _, c, g = heapq.heappop(bekleme)
            heapq.heappush(yigin, (c, g))
        if yigin:
            c, g = heapq.heappop(yigin)
            if plan is not None:
                plan.append(g)
            if c + 1 < 0:     # kalan sayi bir azaldi
                heapq.heappush(bekleme, (t + n + 1, c + 1, g))
        elif plan is not None:
            plan.append("-")  # bekleme (bos adim)
        t += 1
    return t
```

```python
def formul(gorevler, n):
    sayac = Counter(gorevler)
    en_cok = max(sayac.values())
    k = sum(1 for c in sayac.values() if c == en_cok)
    return max(len(gorevler), (en_cok - 1) * (n + 1) + k)


def tam_arama(gorevler, n):
    sayac = Counter(gorevler)
    isimler = sorted(sayac)
    kalan0 = tuple(sayac[g] for g in isimler)
    baslangic = (kalan0, (0,) * len(isimler))
    seviye, t = {baslangic}, 0
    while True:
        yeni = set()
        for kalan, sogu in seviye:
            if sum(kalan) == 0:
                return t
            for i in range(len(isimler)):
                if kalan[i] > 0 and sogu[i] == 0:
                    k2 = list(kalan)
                    k2[i] -= 1
                    s2 = [max(x - 1, 0) for x in sogu]
                    s2[i] = n
                    yeni.add((tuple(k2), tuple(s2)))
            # bekleme: hicbir gorev calistirilmaz
            yeni.add((kalan, tuple(max(x - 1, 0) for x in sogu)))
        seviye = yeni
        t += 1
```

```python
def main():
    gorev = list("AAABBBCC")
    plan = []
    simulasyon(gorev, 2, plan)
    print("n=2 plan:", " ".join(plan))
    for n in (2, 3):
        print("gorevler=%s n=%d" % ("".join(gorev), n))
        print("  simulasyon:", simulasyon(gorev, n),
              "formul:", formul(gorev, n),
              "tam arama:", tam_arama(gorev, n))
    rnd = random.Random(42)
    hata = 0
    for _ in range(300):
        tip = rnd.randint(1, 3)
        m = rnd.randint(1, 8)
        gorev = [rnd.choice("ABC"[:tip]) for _ in range(m)]
        n = rnd.randint(0, 3)
        a = simulasyon(gorev, n)
        if not (a == formul(gorev, n) == tam_arama(gorev, n)):
            hata += 1
    print("300 rastgele ornek, uc yontem uyusmuyor:", hata)


if __name__ == "__main__":
    main()
```

**Adım 6 — Doğrula.** Program şu çıktıyı verir:

```term
$ python gorev_zamanlayici.py
n=2 plan: A B C A B C A B
gorevler=AAABBBCC n=2
  simulasyon: 8 formul: 8 tam arama: 8
gorevler=AAABBBCC n=3
  simulasyon: 10 formul: 10 tam arama: 10
300 rastgele ornek, uc yontem uyusmuyor: 0
```

Aşağıdaki tablo, `n = 2` için açgözlü simülasyonun çizelgesini gösterir; her satır bir zaman birimidir ve program bu sırayı `plan` listesiyle üretir.

| Zaman | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| Görev | A | B | C | A | B | C | A | B |

Üç `A`, üç `B` ve iki `C` toplam sekiz birim sürer. Kapalı formül `(3-1)·(2+1) + 2 = 8` verir ve tam arama da 8 bulur. `n = 3` için formül `(3-1)·4 + 2 = 10` verir; ikisi de programın çıktısıyla aynıdır. Rastgele 300 örnekte üç yöntem tamamen uyuşur (hata 0).

**Bunu AI'sız yazabilir misin?** Görev türlerinin sayısı en az iki olsun ve `n` soğuma süresi verilsin. Aynı kapalı formülü, her görevin sayısının eşit olduğu durumda yeniden türet. Eşit değilse ne değişir? Son olarak, hangi koşulda cevap yalnızca dizinin uzunluğu olur? Bu koşulu bekleme (boş adım) sayısı cinsinden yaz.

## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. Açgözlü algoritmanın asıl eğitimi, kuralı kendin seçmek, karşı örneği kendin bulmak ve kanıtı kendin yazmaktır. Bir aracın verdiği kural doğru görünse bile, sen karşı örnek aramadıkça onun doğru olduğunu bilmiyorsun.
:::

### Proje 1 (★★): Kutu paketleme için karşı örnek avcısı

**Amaç:** Bölüm 18.1'deki karşı örnek avcısını, farklı bir problem için yeniden kullanmak. Kutu paketleme (bin packing) problemi: `n` eşya, her biri `0` ile `1` arasında bir boyutta; eşyaları en az sayıda kutuya sığdır. Kutu kapasitesi `1`.

**Yapılacak / Beklenen davranış:**

1. İki açgözlü kuralı uygula: **ilk uyan** (first fit: eşyayı sırayla al, ilk sığdığı kutuya koy; sığmazsa yeni kutu aç) ve **azalan ilk uyan** (önce eşyaları büyükten küçüğe sırala, sonra ilk uyan).
2. `n ≤ 7` için kaba kuvvet yaz: tüm eşya-kutu atamalarını dene ve en az kutulu geçerli olanı bul.
3. Rastgele (tohum `42`) 500 küçük örnekte her iki kuralı kaba kuvvetle karşılaştır ve hata sayısını yazdır.
4. Her kural için en küçük karşı örneği bul ve neden başarısız olduğunu bir cümleyle açıkla.

**Önerilen yaklaşım (ipucu, tam çözüm değildir):** Karşı örnek avcısının `en_kucuk_karsi` işlevini, eşya listesi üreten bir fonksiyon ile birlikte kullan. Kaba kuvveti `itertools.product` ile kutu numaralarını tarayarak yapabilirsin; ama her eşyanın kaç kutuya girdiğini değil, hangi kutuya girdiğini tut. Kayan noktada toplam kapasite karşılaştırması hataya açıktır; eşyaları tam sayıya çevirip (ör. `0..100`) çalışmak daha güvenilir sonuç verir.

**Başarı kriterleri:**

- 500 rastgele örnekte (tohum `42`) iki kuralın hata sayıları yazdırılmıştır ve kaba kuvvetle tutarlıdır.
- Her kural için bulunan karşı örnek, kendi cevabının optimumdan farklı olduğunu gösteren elle hesaplanmış bir tabloyla birlikte verilmiştir.
- Kaba kuvvet fonksiyonu boş liste, tek eşya ve tüm eşyaların `1` boyutlu olduğu sınır durumlarında elle beklediğin çıktıyı verir.

### Proje 2 (★★★): Kendi Huffman sıkıştırıcın

**Amaç:** Bu bölümdeki Huffman kodunu bit düzeyinde bir sıkıştırıcıya dönüştürmek: bir dosyayı okuyup sıkıştırılmış bir dosyaya yazmak ve geri açmak. Sıkıştırılmış dosyanın başına Huffman tablosunu (her simge için frekans ya da kod uzunluğu) yazmak zorundasın.

**Yapılacak / Beklenen davranış:**

1. Dosyayı bayt olarak oku; frekans tablosunu çıkar; Huffman kodlarını kur. Kodları bit akışına çevirirken bitleri bir bayt tamponunda paketle; son baytta kalan boş bit sayısını başlığa yaz.
2. Başlığa tabloyu yaz: `n` (simge sayısı), her simge için bayt değeri ve frekansı (ya da kod uzunluğu). Kodların çözücüde yeniden üretilebilmesi için tablonun deterministik olduğundan emin ol.
3. Çözücü, başlığı okuyarak kodları yeniden kurar, bit akışını tek tek okur ve orijinal baytları üretir. Çıktı orijinal dosyayla bayt bayt aynı olmalı.
4. Bölüm 18.6'daki `bolum_16.md` metnini ve iki ek dosya (ikili bir dosya ve tek simgeli bir dosya) için sıkıştırma oranını (sıkıştırılmış / orijinal) ölç; aynı dosyaları `gzip` ile karşılaştır.

**Önerilen yaklaşım (ipucu):** Bit yazıcını küçük bir sınıf yap: `bit_yaz(b)` ve `bayt_bitir()`. Çözücüde bit okuyucu, tek bir baytın bitlerini sıradan sırayla döndürsün. Tek simgeli dosya özel bir durumdur (kod uzunluğu `0` olabilir, ama çözücü yine de bir bit okumalıdır; bu durumu bir kuralla düzelt). Gzip ile karşılaştırırken aynı seviyeyi (`compresslevel=9`) kullan ve başlık maliyetini dahil et; sadece veri bitlerini karşılaştırmak adil değildir.

**Başarı kriterleri:**

- Dört farklı girdi (boş dosya dahil değil; tek simgeli, metin, ikili, `bolum_16.md`) için geri çözme orijinali bayt bayt verir.
- Her girdi için sıkıştırma oranı, başlık dahil, bir tabloda raporlanmıştır; gzip ile yan yana.
- Metinde ve ikili dosyada oranların farklı olduğu, bunun neden olduğu (LZ77 tekrarları, simge dağılımı) bir paragrafla açıklanmıştır.

## Ek Alıştırmalar

Aşağıdaki problemlerin cevapları verilmemiştir. Önce kâğıtta düşün; son çare olarak kodla doğrula. Mülakat sorularının bir kısmı ayrıca işaretlidir.

1. ★ (Mülakat) Örtüşen aralıkları birleştir: `[[1,3],[2,6],[8,10]]` girdisinden `[[1,6],[8,10]]` çıktısını üret. Hangi ön işlem gerekir ve neden?
2. ★ Bir dizide tek geçişte, `a[i]` ile en fazla o kadar ilerleyerek sona ulaşıp ulaşamayacağını söyle. Bu, Jump Game II'nin hangi basitleştirilmiş sürümüdür?
3. ★ (Mülakat) Bir mağazada `n` müşterinin her birinin hizmet süresi var. Hizmeti sırayla verirken ortalama bekleme süresini en küçük yapacak sırayı bul ve neden doğru olduğunu açıkla.
4. ★★ Her eşyadan en fazla `c_i` kez alınabildiği kesirli sırt çantasında, değer/ağırlık sıralı açgözlü hâlâ doğru mu? Karşı örnek ya da kanıt ver.
5. ★★ (Mülakat) 0/1 sırt çantasında açgözlüyü "değeri en büyük" ve "ağırlığı en küçük" kurallarına göre dene. Her kural için bir karşı örnek bul.
6. ★★ Bağlantılı ağırlıklı bir çizgede her adımda en hafif kenarı seçip döngü oluşturmayanları ekleyerek MST kurabilirsin (Kruskal). Bunu kesme özelliğiyle açıkla: hangi kesim, hangi kenarı garanti eder?
7. ★★★ (Mülakat) Frekansları Fibonacci sayıları olan bir alfabede Huffman ağacının en derin yaprağının uzunluğunun `n - 1`e ulaşabildiğini göster. Bu durumun kod uzunluğu sınırını (15 bit gibi) neden aşabileceğini açıkla.
8. ★★ Negatif kenar içermeyen ama negatif ağırlıklı bir DAG'da en kısa yolu, topolojik sıralama ile hesapla. Bu yöntem açgözlü mü? Neden doğru olduğunu açıkla.
9. ★★ (Mülakat) Smith kuralında bazı işlerin ağırlığı `0` ise sıralama formülü (`p/w`) tanımsız olur. Bu durumu nasıl ele alırsın, toplam ağırlıklı süreyi etkiler mi?
10. ★★★ Bélády'nin optimalliğini değiş-tokuş argümanıyla kanıtla: bir optimal çözümü, Bélády'nin ilk kararına uyacak şekilde değiştirebileceğini göster.
11. ★★ (Mülakat) Bir önbellekte LRU ile Bélády arasındaki farkı, LRU'nun en kötü durumda neden çok kötü olabildiğini bir örnekle açıkla.
12. ★★★ `n` iş için Smith kuralını, işlerin ağırlıkları ve süreleri aynı oranda olduğunda (`p_j / w_j` sabit) nasıl yorumlarsın? Bu durumda hangi sıralama sonuçta fark yaratmaz?

## Kod Okuma Egzersizi

Bu egzersizde gerçek bir açık kaynak kodu okuyacaksın: zlib 1.3.1'in `trees.c` dosyası. Kaynak `https://raw.githubusercontent.com/madler/zlib/v1.3.1/trees.c` adresinden indirildi ve başlıktaki `1995-2024` telif satırıyla birlikte doğrulandı. Dosyanın içinde kurulan ağaç, DEFLATE'in Huffman kodlarıdır; bu bölümde incelediğimiz açgözlü algoritmanın gerçek bir uygulamasıdır.

Aşağıdaki üç kesit birebir kopyalanmıştır; tek fark, okunabilirlik için **yorum satırlarının ve `DUMP_BL_TREE` ile sarılı, varsayılan olarak derlenmeyen hata ayıklama bloğunun çıkarılmasıdır**. Kod satırlarının hiçbiri değiştirilmemiştir. İlk kesit yorumsuz olduğu için birebir alınmıştır.

Birinci kesit, `smaller` makrosudur (satır 497–499). Makro, iki düğümü karşılaştırır: önce frekansa, eşitlikte derinliğe bakar.

```c
#define smaller(tree, n, m, depth) \
   (tree[n].Freq < tree[m].Freq || \
   (tree[n].Freq == tree[m].Freq && depth[n] <= depth[m]))
```

İkinci kesit, yığın (heap) düzeltme fonksiyonudur: `pqdownheap` (satır 507–526). Yığını, en küçük elemanı köke getirecek şekilde aşağı süzer; çocuklardan küçük olanı seçer ve ebeveyn daha küçükse durur.

```c
local void pqdownheap(deflate_state *s, ct_data *tree, int k) {
    int v = s->heap[k];
    int j = k << 1;
    while (j <= s->heap_len) {
        if (j < s->heap_len &&
            smaller(tree, s->heap[j + 1], s->heap[j], s->depth)) {
            j++;
        }
        if (smaller(tree, v, s->heap[j], s->depth)) break;

        s->heap[k] = s->heap[j];  k = j;

        j <<= 1;
    }
    s->heap[k] = v;
}
```

Üçüncü kesit, Huffman ağacını kuran ana döngüdür (satır 670–693). En küçük iki düğümü çıkarır, yeni bir iç düğüm oluşturur ve onu yığına geri koyar.

```c
    node = elems;
    do {
        pqremove(s, tree, n);
        m = s->heap[SMALLEST];

        s->heap[--(s->heap_max)] = n;
        s->heap[--(s->heap_max)] = m;

        tree[node].Freq = tree[n].Freq + tree[m].Freq;
        s->depth[node] = (uch)((s->depth[n] >= s->depth[m] ?
                                s->depth[n] : s->depth[m]) + 1);
        tree[n].Dad = tree[m].Dad = (ush)node;
        s->heap[SMALLEST] = node++;
        pqdownheap(s, tree, SMALLEST);

    } while (s->heap_len >= 2);
```

**Sorular — cevaplamadan geçme:**

1. `smaller` makrosu eşit frekansta derinliğe bakar. Bu tie-break kuralı, Bölüm 18.6'da gördüğümüz hangi sorunu (ağacın en derin yaprağını) azaltmaya yarar? Bu kuralı kaldırırsan hangi sonuç değişebilir?
2. `pqdownheap` içinde `j <<= 1` ile `j` iki katına çıkarılır. Bu, Bölüm 10'daki yığın gösteriminin hangi özelliğine dayanır? `heap[0]` neden kullanılmaz?
3. `pqremove(s, tree, n)` ile en küçük düğüm `n` yığından çıkarılır; ardından yeni kök `m = s->heap[SMALLEST]` olarak okunur. Bu iki satırın birlikte yaptığını, Bölüm 18.6'daki "en küçük iki kökü birleştir" adımıyla karşılaştır.
4. Yeni iç düğüm `s->heap[SMALLEST] = node++;` ile yığına konur ve `pqdownheap` çağrılır. Bu neden yığına sona eklemek yerine kökte yapılır? İki seçeneğin karmaşıklığını yaz.
5. Kodda geçen `heap_len`, `heap_max` ve `HEAP_SIZE` değişkenlerini, kesitte görmediğin kısımları da okuyarak, aynı `heap` dizisinin bir ucunda yığını (`heap_len`), öteki ucunda sıralı çıktıyı (`heap_max`) tutmasının nedenini bul. Bulgunu kendi cümlelerinle yaz; kaynak yorumlarından alıntı yapma.
6. (Mülakat) Bu kodda kod uzunluklarının 15 bit ile sınırlandığını gösteren `gen_bitlen` içindeki düzeltme adımı nedir? Bu adım olmasaydı ne olurdu, bir örnek bul.

## Bölüm Özeti

Bu bölümde açgözlü algoritmayı, geri dönmeden her adımda yerel en iyi seçimi yapan bir yöntem olarak öğrendik. Doğruluğu, yalnızca kural makul göründüğü için değil, kanıtla ya da karşı örnek aramasıyla sınayarak kurduk.

- Açgözlü doğruluk için iki koşul ister: **açgözlü seçim özelliği** ve **optimal alt yapı**. İkisini kanıtlamadan kural kullanılmaz.
- Kanıt teknikleri üçtür: **değiş-tokuş argümanı**, **önde kalma** ve **kesme özelliği**. Her birini bir problemde uyguladık.
- Karşı örnek avı, bir kuralı reddetmenin en güvenilir yoludur; küçük rastgele girdilerde kaba kuvvetle karşılaştırmak bunu otomatikleştirir.
- Etkinlik seçimi bitiş sıralı açgözlüyle, aralık bölümleme ise başlangıç sıralı açgözlü ve en büyük derinlik alt sınırıyla çözülür.
- Kesirli sırt çantası açgözlüyle doğrudur; 0/1 sırt çantası değildir. Para bozma yalnızca kanonik sistemlerde açgözlüyle çözülür.
- Gecikme için EDF, ağırlıklı tamamlama süresi için Smith kuralı optimaldir; her ikisinin kanıtı adjacent-swap ile yapılır.
- Huffman öneksiz kodlarda optimal açgözlüdür; ortalama uzunluk entropinin üstünde ve bir bit altındadır (`H ≤ L < H + 1`). Gzip, LZ77 ile tekrarları da kullandığı için Huffman'dan çok daha iyi sıkıştırır.
- Kesme özelliği, Kruskal ve Prim'in doğruluğunun ortak temelidir. Dijkstra pozitif kenarlarda açgözlüdür; negatif kenar onu bozar.
- Matroidler açgözlünün her ağırlıkta doğru olduğu sınıfı tanımlar; küme örtme gibi problemlerde açgözlü yalnızca yaklaşım sağlar.

**Sonraki bölümde:** Bu bölümde bir problemi yerel en iyi seçimlerle çözdük; bu seçimlerin ne zaman doğru olduğunu sorguladık. Bölüm 19'da (Divide & Conquer) farklı bir strateji göreceğiz: problemi bağımsız alt problemlere bölüp her birini çözmek ve sonuçları birleştirmek. Bölüm 12'deki Master Theorem ile bu yöntemin karmaşıklığını hesaplayacağız, en yakın çift problemini ve Strassen'in matris çarpımını inceleyeceğiz.

::: mulakat
Klasik sorular, hemen cevaplamaya çalışma; her birini birkaç dakika düşün:

1. Bir açgözlü algoritmanın doğru olduğunu gösteren iki kanıt tekniğini (değiş-tokuş ve önde kalma) bir problem üzerinde anlat. Hangisi neden daha uygun?
2. Kesirli ve 0/1 sırt çantası aynı açgözlü kuralla çözülmeye çalışıldığında neden biri doğru, diğeri yanlış çıkar? Bir karşı örnek ver.
3. Huffman'ın optimalliğini nasıl kanıtlarsın? En düşük frekanslı iki simgenin rolü nedir?
4. Kesme özelliği ile Kruskal'ın doğruluğu arasındaki bağlantıyı açıkla. Kruskal'ın her eklediği kenar neden bir kesimin en hafif kenarıdır?
5. Dijkstra negatif kenarlı bir çizgede neden yanlış sonuç verir? Bellman-Ford'un bu sorunu nasıl çözdüğünü bir cümleyle söyle.
6. Açgözlü yaklaşım oranı nedir? Küme örtme probleminde açgözlünün optimuma göre garantisi ne demektir?
7. Bélády'nin algoritmasını neden gerçek bir işletim sisteminde uygulayamayız? LRU'nun bu boşluğu nasıl doldurmaya çalıştığını açıkla.
8. Bir problemin açgözlü ile çözülebilir olduğunu hangi koşul garanti eder? Matroid kavramı bunu nasıl ifade eder?
:::
