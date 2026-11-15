%% kisim_no: XII
%% kisim_ad: Matematik
%% kisim_ayrac: evet
%% bolum_no: 47
%% baslik: Ayrık Matematik

## Giriş: Sürekli değil, ayrık bir dünya

Bilgisayarın içinde süreklilik yoktur. Bir sensörden okunan değer 12 bitlik bir sayıdır; bir dosyanın boyutu bayt sayısıdır; bir ağdaki iki düğüm ya bağlıdır ya değildir. Her şey sonlu sayıda adımla, sonlu sayıda değerle, ayrık olarak çalışır. Matematiğin bu dünyayı anlatan dalına **ayrık matematik** (discrete mathematics) denir. Mantık, kümeler, sayma, sayılar teorisi ve graflar bu dalın ana başlıklarıdır.

Bu konular mülakatlarda sık gelir, çünkü algoritma yazmanın dilidir. "İki sayının en büyük ortak böleni nasıl bulunur?", "Bir ağda iki düğüm arasında döngüsüz bir yol var mı?", "Bir dizide her elemanın kaç farklı sıralaması vardır?" soruları bu bölümün konularıdır. Bunları ezberlemek yetmez; her birinin neden doğru olduğunu kanıtlayabilmen gerekir. Bu bölümde hem kâğıtta ispat yapacak hem de her iddiayı Python'da denetleyeceksin.

Bölüm, kitabın önceki bölümlerinde zaten kullandığın fikirlere bir çatı kurar. Bölüm 1'de bitlerle sayı yazdın; burada aynı bitlerin mantık kapılarından nasıl devre oluştuğunu göreceksin. Bölüm 12'de özyinelemeli bağıntılarla ve Master teoremiyle tanıştın; burada bu bağıntıların kapalı biçimini bulacaksın. Bölüm 15'te Catalan sayılarını ve geri izlemeyi gördün; burada onların sayma tarafını tamamlayacaksın. Bölüm 17'de Union-Find ve topolojik sıralama vardı; burada onların bağıntı ve sıralı küme dilini kuracaksın.

Savunma sanayiinde bu bilgi doğrudan kullanılır. Bir İHA'nın uçuş kontrol yazılımındaki koşulların her kombinasyonunun test edildiğini kanıtlamak için MC/DC kapsaması gerekir; bu kapsamanın mantığı bu bölümün 47.1'indedir (Bölüm 39.12'de uygulamasını göreceksin). Haberleşmede kullanılan açık anahtarlı şifreleme RSA'dır; onun güvenliği sayılar teorisine dayanır (47.8). Bir görev planlamasındaki kısıtların sağlanabilirliği ise SAT problemidir (47.2). Bu bağlantıları Bölüm 32 (güvenlik) ve Bölüm 78 (güvenilir AI ve doğrulama) ile birlikte yeniden kuracağız.

Bu bölümün yaklaşımı şudur: her kavramı önce bir sezgiyle, sonra kesin bir tanımla, sonra bir kanıtla ve en sonunda bir programla anlatıyoruz. Programların çıktısını kendi makinende yeniden üretmen beklenir. Bu bölümde kapsam geniştir; her konuyu bir ders kitabı derinliğinde değil, bir mühendisin ihtiyaç duyacağı derinlikte işliyoruz. Derinleşmek istersen bölüm sonundaki alıştırmalar ve Kendin Yap projeleri bunun yoludur.

::: not
Bölümdeki tüm programlar Python 3.12.10 ile çalıştırıldı ve çıktıları birebir gösterildi. Python tamsayıları keyfi büyüklükte olduğu için sayma ve tam sayı sonuçları her makinede aynıdır. Kayan nokta (float) sonuçları ise IEEE 754 standardına bağlıdır; bunu 47.6'da Fibonacci örneğinde göreceksin.
:::

## 47.1 Mantık ve Boole cebiri: önermeler, eşdeğerlik, devre

**Önerme** (proposition), doğru ya da yanlış olduğu kesin olarak söylenebilen bir ifadedir. "Sıcaklık 80'in üstündedir" bir önermedir; "Bu motor güzel" değildir, çünkü doğruluk değeri yoktur. Önermeleri p, q, r gibi harflerle gösteririz ve bunları şu bağlaçlarla birleştiririz:

- **¬p** (değil p): p yanlışsa doğru, doğruysa yanlış.
- **p ∧ q** (ve): ikisi de doğruysa doğru.
- **p ∨ q** (veya): en az biri doğruysa doğru.
- **p → q** (gerektirir): p doğru ve q yanlışsa yanlış; diğer tüm durumlarda doğru.
- **p ↔ q** (eşdeğer): ikisi aynı doğruluk değerine sahipse doğru.

Türkçedeki "veya" bazen "ya bu ya da o" anlamına gelir. Mantıkta ∨ **kapsayıcıdır**: p ve q birlikte doğruyken p ∨ q da doğrudur. Bu ayrım yazılımda hata kaynağıdır; "kullanıcı yönetici veya denetçi ise erişebilir" dediğinde ikisine birden sahip kullanıcının erişebilmesini istiyorsan ∨ doğru bağlaçtır.

Gerektirme (→) en çok karıştırılan bağlaçtır. "Yağmur yağıyorsa şemsiye taşırım" önermesi, yağmur yağmadığı günlerde şemsiyesiz çıkmakla yalanlanmaz. Yalanlanan tek durum, yağmur yağmasına rağmen şemsiye taşımamaktır. Bu yüzden p → q, ¬p ∨ q ile aynıdır. Bu özdeşliği her yerde kullanacağız.

**Doğruluk tablosu.** Bir bileşik önermenin davranışını, tüm değişken değerleri için tek tek yazarak görürsün. n değişkenli bir formül için tablo 2^n satır tutar. Bir formül her satırda doğruysa **tautoloji** (tautology), hiçbir satırda doğru değilse **çelişki** (contradiction), en az bir satırda doğruysa **sağlanabilir** (satisfiable) denir. Sonraki konulardaki SAT problemi tam olarak bu sonuncuyu sorar.

**Eşdeğerlik.** İki formül her girişte aynı değeri veriyorsa eşdeğerdir ve bunu ≡ ile yazarız. Bu, bir kod yeniden düzenlemesinin güvenliğinin matematiksel karşılığıdır: koşulu değiştirirsin ama davranış aynı kalır. En ünlü eşdeğerlik **De Morgan yasasıdır**:

| p | q | ¬(p ∧ q) | ¬p ∨ ¬q |
|---|---|---|---|
| 0 | 0 | 1 | 1 |
| 0 | 1 | 1 | 1 |
| 1 | 0 | 1 | 1 |
| 1 | 1 | 0 | 0 |

Son iki sütun her satırda aynıdır; dolayısıyla ¬(p ∧ q) ≡ ¬p ∨ ¬q. Aynı yasa ∨ ve ∧ yer değiştirerek de geçerlidir: ¬(p ∨ q) ≡ ¬p ∧ ¬q. Bu, bir koşulu "dışarıdan" değil "içeriden" olumsuzlamanın yoludur. Python'da `if not (a and b):` ile `if (not a) or (not b):` aynı davranışı gösterir; ikincisi bazen daha okunaklıdır, bazen değildir. Asıl önemli olan, iki yazımın eşdeğer olduğunu bir tabloyla kanıtlayabilmendir.

Programlamada koşulları sadeleştirirken iki tuzağa dikkat et. Birincisi, `and` ve `or` **kısa devre** yapar: `a and b` yazılırsa ve a yanlışsa b hiç değerlendirilmez. Bu, b'nin yan etkisi varsa (örneğin bir sensör okuması) davranışı değiştirir. İkincisi, karmaşık bir karardaki her koşulun gerçekten sonucu etkileyip etkilemediğini bilmek zordur. Bu sorunun ciddi bir cevabı **MC/DC** (Modified Condition/Decision Coverage) kapsamasıdır; Bölüm 39.12'de savunma sanayiinde bu kapsamanın neden zorunlu olduğunu göreceksin.

**Niceleyiciler.** Önermeler yalnızca sonlu sayıda "evet/hayır" sorusunu anlatır. "Dizideki her eleman pozitiftir" ya da "bir eleman sıfırdır" gibi ifadeler için niceleyicilere ihtiyaç vardır:

- **∀x P(x)**: her x için P(x) doğrudur (evrensel niceleyici).
- **∃x P(x)**: P(x) doğru olan en az bir x vardır (varoluşsal niceleyici).

Olumsuzlama kuralı şudur: ¬∀x P(x) ≡ ∃x ¬P(x) ve ¬∃x P(x) ≡ ∀x ¬P(x). "Her eleman pozitiftir" değildir demek, "en az bir eleman pozitif değildir" demektir. Bu kural, hata ayıklarken en çok yapılan mantık hatasının kaynağıdır. Sonlu bir alanda niceleyiciler Python'daki `all` ve `any` ile doğrudan karşılanır:

```python
dizi = [3, -1, 7]
print(all(x > 0 for x in dizi))   # her x > 0 mı?
print(any(x < 0 for x in dizi))   # en az bir x < 0 mı?
```

Sonsuz bir alanda (örneğin tüm doğal sayılarda) bu kontrol yapılamaz; orada doğruluk ispatla kurulur. Bu yüzden bir sonraki konu ispat tekniklerine ayrılmıştır (47.3).

**Boole cebiri ve mantık devreleri.** Bilgisayar donanımı mantığı elektronik kapılarla uygular. Üç temel kapı vardır: VE kapısı (∧), VEYA kapısı (∨) ve DEĞİL kapısı (¬). Bir devrenin çıkışı, girişlerinin bir mantık formülüdür. Şekil 47.1'de De Morgan yasasının iki devresini görüyorsun: sol devre ¬(a ∧ b) hesaplar, sağ devre ¬a ∨ ¬b hesaplar. Girişlerin her kombinasyonunda çıkışları aynıdır; yani bu iki devre aynı işi yapar, ama farklı sayıda ve farklı türde kapı kullanır. Gerçek bir tasarımda bu eşdeğerlik, kapı sayısını ve gecikmeyi değiştirebilir.

![Şekil 47.1: De Morgan yasasının iki devresi. Sol: ¬(a ∧ b). Sağ: ¬a ∨ ¬b. Her girişte çıkışlar aynıdır.](gorseller/b47_kapi_devre.png)

Bir devreyi sadeleştirmenin sistematik yolu **Karnaugh haritasıdır**. Önce üç değişkenli bir örnekle düşünelim. f(a, b, c) fonksiyonunun çıkışı 1 olan girişlerini minterm numaralarıyla verelim: f = Σm(0, 1, 2, 5, 6, 7). Bu, girişler 000, 001, 010, 101, 110 ve 111 iken çıkışın 1 olduğu anlamına gelir.

| a | b | c | f |
|---|---|---|---|
| 0 | 0 | 0 | 1 |
| 0 | 0 | 1 | 1 |
| 0 | 1 | 0 | 1 |
| 0 | 1 | 1 | 0 |
| 1 | 0 | 0 | 0 |
| 1 | 0 | 1 | 1 |
| 1 | 1 | 0 | 1 |
| 1 | 1 | 1 | 1 |

Karnaugh haritasında sütunlar, komşu iki sütun yalnızca bir bit farklı olacak biçimde (Gray kodu sırasıyla: 00, 01, 11, 10) dizilir. Her hücre bir minterm'dir:

| a \ bc | 00 | 01 | 11 | 10 |
|---|---|---|---|---|
| 0 | 1 | 1 | 0 | 1 |
| 1 | 0 | 1 | 1 | 1 |

Kural basittir: 1'lerden oluşan 2'nin kuvvetine uygun dikdörtgen gruplar (ikili, dörtlü) çizilir ve her grup bir çarpım terimi verir. Burada üç ikili grup görünür. Sütun 00 ve 01 satır 0'da: a'b' (b = 0 ve a = 0). Sütun 01 ve 11 satır 1'de: ac (a = 1, c = 1). Sütun 10, iki satırda: bc' (b = 1, c = 0). Sonuç:

f = a'b' ∨ ac ∨ bc'

Bu ifadenin doğru olduğunu tablonun her satırında kontrol edebilirsin. Ama bu sadeleştirme **en az terimli** mi? Burada bir alt sınır argümanı var. Altı minterm'i kapsamamız gerekir ve iki literalli her terim en fazla iki minterm kapsar. Tek literalli bir terim dört minterm kapsar, ama bunun için dört hücrelik bir 1 dikdörtgeni gerekir ve bu haritada yoktur. O hâlde en az üç terim gerekir; bulduğumuz üç terim bu sınıra ulaşır. Bunu aşağıdaki programla da kontrol edebilirsin.

```python
# -*- coding: utf-8 -*-
# karnaugh.py - f(a,b,c) = Σm(0,1,2,5,6,7) icin SOP dogrulamasi.
import itertools

ON = {0, 1, 2, 5, 6, 7}


def f_sop(a, b, c):
    """Karnaugh gruplari: a'b' + ac + bc'."""
    return (not a and not b) or (a and c) or (b and not c)


if __name__ == "__main__":
    print("a b c  f  SOP")
    hata = 0
    for a, b, c in itertools.product([0, 1], repeat=3):
        m = 4 * a + 2 * b + c
        f = int(m in ON)
        s = int(bool(f_sop(a, b, c)))
        print(a, b, c, " ", f, " ", s)
        hata += f != s
    print("hata:", hata)
```

Programın çıktısı, sadeleştirilmiş ifadenin tablonun her satırıyla uyuştuğunu gösterir:

```term
$ python karnaugh.py
a b c  f  SOP
0 0 0   1   1
0 0 1   1   1
0 1 0   1   1
0 1 1   0   0
1 0 0   0   0
1 0 1   1   1
1 1 0   1   1
1 1 1   1   1
hata: 0
```

Karnaugh haritası üç veya dört değişkenle insan eliyle çalışılabilir. Daha fazla değişkende yöntem üstel büyür; bunun yerine **Quine–McCluskey** veya sezgisel araçlar kullanılır. Hepsinin ortak fikri, bu bölümde gördüğümüz kapsama problemidir.

## 47.2 SAT ve DPLL: bir formülü sağlayan atama var mı?

47.1'de bir formülün doğruluk değerlerini tablo tarayarak bulduk. n değişken için 2^n satır vardı. Bu, n = 30'da bir milyardan fazla satır demektir. Gerçek donanım doğrulama problemlerinde binlerce değişken vardır; tablo yöntemi tamamen imkânsızdır. Bu noktada karşımıza **SAT problemi** çıkar: "Verilen bir mantık formülü sağlanabilir mi, yani en az bir atama onu doğru yapar mı?"

Önce gösterim. Bir **literal**, bir değişken ya da onun olumsuzlamasıdır: x veya ¬x. Bir **madde** (clause), literallerin VEYA'sıdır: (x1 ∨ ¬x2 ∨ x3). Formül, maddelerin VE'sidir. Bu biçime **konjonktif normal form** (CNF) denir. Her mantık formülü CNF'ye çevrilebilir; ama bu çeviri bazen formülün boyutunu üstel büyütür, bu yüzden SAT çözücüler genellikle ek değişkenlerle dönüştürme yapar (genel bilgi).

Python'da bir literali tamsayıyla gösteririz: 3 pozitif x3'tür, -3 ise ¬x3'tür. Bir madde bir liste, formül liste listelerdir. Örnek: [[1, 2], [-1, 3], [-2, -3], [-3, 1]] formülü (x1 ∨ x2) ∧ (¬x1 ∨ x3) ∧ (¬x2 ∨ ¬x3) ∧ (¬x3 ∨ x1) demektir.

SAT problemi **NP-tamdır** (Cook, 1971; genel bilgi). Bu sonucu Bölüm 47.10'da açıklayacağız. Şimdilik şunu bilmen yeter: bugüne kadar bilinen hiçbir algoritma, en kötü durumda, değişken sayısında polinomsal bir sürede çalışmaz. Ama pratikte birçok gerçek SAT örneği çok hızlı çözülür. Bu ikilem, SAT'ı hem zor hem de çok faydalı yapar.

**DPLL algoritması.** 1960'larda Davis, Putnam, Logemann ve Loveland'ın geliştirdiği yöntem, kaba kuvvetin çok daha akıllı bir hâlidir. İki temel fikri vardır:

1. **Birim yayılım** (unit propagation): bir maddede yalnızca bir literal kalmış ve diğerleri yanlış olmuşsa, o literal zorunlu olarak doğru olmalıdır. Bunu atamaya ekleriz ve diğer maddeleri yeniden gözden geçiririz. Bu zincirleme ilerler.
2. **Dallanma ve geri izleme**: zincir durduğunda, atanmamış bir değişken seçilir, önce doğru sonra yanlış denenir. Bir çelişki bulunursa geri dönülür. Bu, Bölüm 15'teki geri izleme (backtracking) şablonunun aynısıdır: seç, keşfet, geri al.

Aşağıdaki program DPLL'in bu iki adımını gerçekler. Önce birim yayılım fonksiyonu gelir.

```python
# -*- coding: utf-8 -*-
# dpll.py - birim yayilimi ve geri izlemeli kucuk SAT cozucu.
import itertools
import random


def birim_yay(form, atama):
    """Birim maddeleri atar. Celiski varsa False doner."""
    while True:
        birim = None
        for c in form:
            kalan, sat = [], False
            for lit in c:
                v = abs(lit)
                if v in atama:
                    if atama[v] == (lit > 0):
                        sat = True
                        break
                else:
                    kalan.append(lit)
            if sat:
                continue
            if not kalan:
                return False          # madde yalanlandi: celiski
            if len(kalan) == 1 and birim is None:
                birim = kalan[0]
        if birim is None:
            return True
        atama[abs(birim)] = birim > 0
```

Şimdi dallanma yapan ana fonksiyon. Her çağrı yeni bir atama sözlüğü kopyalar; böylece geri dönüşte önceki durum bozulmaz. Bu, bellek maliyetli olsa da mantığı açık tutar.

```python
def dpll(form, atama=None):
    atama = dict(atama or {})
    if not birim_yay(form, atama):
        return None
    vars_ = sorted({abs(l) for c in form for l in c})
    bos = [v for v in vars_ if v not in atama]
    if not bos:
        return atama
    for deger in (True, False):
        sonuc = dpll(form, {**atama, bos[0]: deger})
        if sonuc is not None:
            return sonuc
    return None
```

Son bölümde kaba kuvvet denetleyicisi ve rastgele testler var. Testte 8 değişkenli 300 rastgele formül üretiyoruz; her biri için DPLL'in kararı ile tablo taramasının kararını karşılaştırıyoruz.

```python
def kaba(form, n):
    for bits in itertools.product([False, True], repeat=n):
        a = dict(zip(range(1, n + 1), bits))
        if all(any(a[abs(l)] == (l > 0) for l in c) for c in form):
            return True
    return False


if __name__ == "__main__":
    iz = [[1, 2], [-1, 3], [-2, -3], [-3, 1]]
    print("iz:", dpll(iz))
    rnd = random.Random(47)
    sat = uyusmaz = 0
    for _ in range(300):
        n = 8
        m = rnd.randint(10, 40)
        form = [[v if rnd.random() < 0.5 else -v
                 for v in rnd.sample(range(1, n + 1), 3)]
                for _ in range(m)]
        a = dpll(form)
        sat += a is not None
        uyusmaz += (a is not None) != kaba(form, n)
    print("sat:", sat, "/ 300  uyusmazlik:", uyusmaz)
```

Programın çıktısı, iki yöntemin 300 formülün hepsinde aynı kararı verdiğini gösterir:

```term
$ python dpll.py
iz: {1: True, 3: True, 2: False}
sat: 274 / 300  uyusmazlik: 0
```

Küçük örnek olan iz formülünü elle izleyelim; bu, algoritmanın mantığını kâğıtta görmenin en iyi yoludur. Formül (x1 ∨ x2) ∧ (¬x1 ∨ x3) ∧ (¬x2 ∨ ¬x3) ∧ (¬x3 ∨ x1) olsun. Başlangıçta hiçbir atama yok, birim madde de yok. Sıradaki değişken x1'dir ve önce x1 = doğru denenir.

| Adım | Atama | Birim madde | Sonuç |
|---|---|---|---|
| 1 | x1 = 1 | (¬x1 ∨ x3) → x3 zorunlu | x3 = 1 |
| 2 | x1 = 1, x3 = 1 | (¬x2 ∨ ¬x3) → ¬x2 zorunlu | x2 = 0 |
| 3 | x1 = 1, x3 = 1, x2 = 0 | Tüm maddeler doğru | Model bulundu |

Üç adımda, dallanmadan, bir model bulduk: x1 = 1, x2 = 0, x3 = 1. Programın çıktısındaki sözlük ({1: True, 3: True, 2: False}) aynı atamadır. Dikkat edersen, x1 = 0 hiç denenmedi; birim yayılım zaten bir modeli kanıtladı. Bu, DPLL'in kaba kuvvetten farkıdır: yanlış dalları erken keser.

Yine de DPLL bir sihir değildir. En kötü durumda hâlâ üstel sürede çalışabilir. Gerçek SAT çözücüler (modern CDCL çözücüleri) buna ek olarak çatışma öğrenme, akıllı dal seçimi ve yeniden başlatma kullanır (genel bilgi). Ama bu teknikler de DPLL'in dallanma ve birim yayılım çekirdeğine dayanır. Bu yüzden bu çekirdeği kendi elinle yazmak, gerçek çözücülerin davranışını anlamanın en kısa yoludur. Proje bölümünde bu çekirdeği kullanarak bir Sudoku çözücü yazacaksın.

::: baglanti
SAT çözücüler savunma sanayiinde, bir sistemin bütün çalışma kombinasyonlarının güvenli olup olmadığını doğrulamak için kullanılır. Örneğin bir görev bilgisayarındaki kilit (interlock) mantığının "iki motor aynı anda açık olamaz" kuralını ihlal eden bir girdi olup olmadığı bir SAT sorusudur. Bölüm 78'de bu tür biçimsel doğrulamayı ele alacağız.
:::

## 47.3 İspat teknikleri: neden doğru olduğunu göstermek

Bir programı test etmek, onun yanlış olduğunu gösterebilir ama doğru olduğunu gösteremez. Bir fonksiyonu on bin girdide denemek, on birinci girdide bir hata olmadığını garanti etmez. Bir iddianın her durumda doğru olduğunu göstermenin yolu **ispattır**. İspat, mantığın kurallarıyla ilerleyen, kuşkuya yer bırakmayan bir argümandır. Mülakatta "bunun neden doğru olduğunu kanıtlayabilir misin?" sorusu geldiğinde kastedilen budur.

Aşağıda dört temel ispat tekniğini ve her birinin tipik bir kullanımını göreceksin. Önce bunların adlarını ve şablonlarını öğren; sonra kendi problemlerine uygula.

**Doğrudan ispat.** p → q iddiasını göstermek için p'den başlayıp adım adım q'ya varırsın. "Bir tam sayının karesi çiftse, kendisi de çifttir" iddiasını ele alalım. Bir n tam sayısının karesi çiftse, n^2 = 2k olacak biçimde bir k vardır. n tek olsaydı n = 2m + 1 olurdu ve n^2 = 4m^2 + 4m + 1 tek olurdu; bu bir çelişkidir. Dolayısıyla n çifttir. Burada adım adım ilerleyip kesin bir sonuca vardık.

**Karşıt-ters (contrapositive).** p → q iddiasının karşıt-tersi ¬q → ¬p'dir ve mantıksal olarak eşdeğerdir. Bazen q'nun yanlışlığından p'nin yanlışlığına gitmek, doğrudan yolu açmaktan kolaydır. Yukarıdaki örnekte "n^2 çift ise n çifttir" iddiasını ispatlamanın bir yolu, "n tekse n^2 tektir" demektir; bu, doğrudan hesapla hemen görülür.

**Çelişki (reductio ad absurdum).** Bir iddianın doğru olmadığını varsayarsın, bu varsayımdan bir çelişki çıkarsın ve iddianın doğru olduğu sonucuna varırsın. Klasik örnek **√2'nin irrasyonel olmasıdır**. Varsayalım √2 = p/q, burada p ve q aralarında asal tam sayılar. O hâlde p^2 = 2q^2, yani p^2 çifttir; dolayısıyla p çifttir, p = 2k. Bu durumda 4k^2 = 2q^2, q^2 = 2k^2 olur ve q da çifttir. Ama p ve q'nun ikisi birden çift olamaz, çünkü aralarında asaldır. Bu çelişki, varsayımın yanlış olduğunu gösterir.

Aynı teknikle **asal sayıların sonsuz olduğu** gösterilir (Öklid'in argümanı). Varsayalım sonlu bir p1, p2, ..., pk asal listesi tam listedir. N = p1·p2·...·pk + 1 sayısını ele alalım. N, listedeki hiçbir asala bölünmez, çünkü her birine bölümünden 1 kalır. Ama N, 1'den büyük olduğu için en az bir asal çarpanı vardır ve bu asal listede olamaz. Çelişki; liste tamdır varsayımı yanlıştır. Dikkat et: N'nin kendisinin asal olduğunu söylemiyoruz; yalnızca listedeki asallara bölünmediğini söylüyoruz.

**Tümevarım (induction).** Bir P(n) iddiasını her doğal sayı n için kanıtlamak istediğinde iki adım yeterlidir:

1. **Taban**: P(1) (ya da başlangıç değeri) doğrudur.
2. **Adım**: Her k için P(k) doğruysa P(k+1) de doğrudur.

Bu iki adım, bir domino zinciri gibi çalışır. İlk taş devrilir ve her taş bir sonrakini devirirse bütün taşlar devrilir. Örnek: 1 + 2 + ... + n = n(n+1)/2. Taban n = 1 için 1 = 1·2/2. Adım: P(k) doğruysa, P(k+1) için S(k+1) = S(k) + (k+1) = k(k+1)/2 + (k+1) = (k+1)(k+2)/2 olur. Bu tam olarak P(k+1)'in iddiasıdır. Bu örneğin tümevarım, sayısal kontrol ve Python ile birlikte tam çözümlü hâlini Çözümlü Örnek 1'de göreceksin.

**Güçlü tümevarım** bir adım daha ileri gider: P(k) için sadece P(k-1) değil, bütün P(1), ..., P(k-1)'in doğru olduğunu varsayarsın. Her n ≥ 2 sayısının bir asal çarpanlarına ayrılması bu yöntemle kanıtlanır: n asal değilse n = a·b, a ve b'nin her biri daha küçüktür ve onlar da çarpanlarına ayrılır. Dinamik programlamadaki (Bölüm 16) alt problemlere bölme, aslında bu güçlü tümevarımın algoritmik karşılığıdır.

**Hatalı tümevarım.** Tümevarımın en tehlikeli hatası, adımı sağlamadan iddiayı kanıtlamaktır. Şu iddiayı ele alalım: "Her n atlık kümede bütün atlar aynı renktir." Taban P(1) doğrudur: tek bir at, kendisiyle aynı renktedir. Adım için P(n) doğru varsayalım. n+1 atlık bir küme alalım, bir at çıkaralım; kalan n at aynı renktir. Başka bir at çıkaralım; yine n at aynı renktir. Bu iki küme ortak en az bir atı paylaşır, dolayısıyla hepsi aynı renktedir. Bu, adımın n ≥ 2 için geçerli olduğunu gösterir. Ama n = 1'den 2'ye adım? Burada iki küme {A} ve {B} olur ve ortak at yoktur. Zincirin bu halkası kopmuştur; iddia n = 2 için bile yanlıştır. Her tümevarım adımında "ortak eleman var mı?" sorusunu sor.

**Yapısal tümevarım.** Sayılar yerine yapılar üzerinde tümevarım yaparsın: ifadeler, ağaçlar ve gramerler. Tanım gereği her yapı ya temel bir durumdur (yaprak, değişken) ya da daha küçük yapılardan birleştirilmiştir. İspat da iki adımdır: temel durumda özelliği göster, birleştirme durumunda parçalardan bütüne özelliği taşı. Örneğin her iç düğümünün tam iki çocuğu olan bir ikili ağaçta, yaprak sayısı iç düğüm sayısından bir fazladır. Temel: tek yaprak (0 iç düğüm, 1 yaprak). Birleştirme: iki alt ağacın yaprak sayıları L1 = I1 + 1 ve L2 = I2 + 1 ise, yeni ağacın yaprakları L1 + L2 = I1 + I2 + 2, iç düğümleri I1 + I2 + 1'dir; L = I + 1. Bu tekniği Bölüm 36'daki gramer ağaçlarında ve Bölüm 37'deki sözdizimi ağacında tekrar kullanacaksın.

**Değişmez (invariant) ile algoritma doğruluğu.** Bir döngünün doğruluğunu kanıtlamanın tümevarım biçimi, **döngü değişmezi**dir (Bölüm 14.2). Üç soruya cevap verirsin: başlangıçta değişmez doğru mu (başlatma)? Her yinelemede doğru kalıyor mu (sürdürme)? Döngü bitince değişmez ve bitiş koşulu birlikte istenen sonucu veriyor mu (sonlandırma)? Bir dizinin toplamını hesaplayan döngüde değişmez "acc, a[0..i-1] toplamıdır" olabilir. Başlangıçta i = 0 ve acc = 0. Her adımda acc += a[i] ve i += 1 ile değişmez korunur. Bitişte i = n, dolayısıyla acc tüm dizinin toplamıdır.

::: ipucu
Bir kanıtı yazarken her adımın hangi kurala dayandığını yanına yaz. "Çünkü" diyemiyorsan adım boşluklu olabilir. Bu alışkanlık, mülakatta iddiayı sözle savunmanın da temelidir.
:::

Bir kanıtın yerini test almaz; ama bir kanıtı test etmek iyi bir refleks. Bu bölümdeki her programı, anlattığımız iddiayı küçük örneklerde denemek için yazdık. Bunu bir alışkanlık hâline getir.

## 47.4 Kümeler, bağıntılar ve fonksiyonlar

**Küme** (set), farklı elemanların belirli bir koleksiyonudur. Python'da `set` veri yapısı tam olarak bu tanımı uygular: aynı eleman iki kez bulunmaz ve sırası yoktur. Bir küme A ile gösterilir, x ∈ A bir elemanı belirtir, A ⊆ B bir alt kümeyi belirtir. Birleşim (A ∪ B), kesişim (A ∩ B), fark (A \ B) ve kuvvet kümesi (P(A), A'nın bütün alt kümelerinin kümesidir) temel işlemlerdir. n elemanlı bir kümenin kuvvet kümesi 2^n elemandan oluşur; bu, Bölüm 9'daki hash tablosunun neden kümeleri hızlı tuttuğunu anlamanın da zeminidir.

**Sıralı çift ve kartezyen çarpım.** (a, b) sıralı çifttir ve sırası önemlidir. A × B, bütün (a, b) çiftlerinin kümesidir. Bir ilişki, A × B'nin bir alt kümesidir. Veritabanında bir tablo (bağıntı, relation) bu tanımın doğrudan karşılığıdır; Bölüm 33'teki ilişkisel model bu kökten gelir.

**Bağıntının özellikleri.** A üzerindeki bir R bağıntısı için üç özellik önemlidir:

- **Yansıma** (reflexive): her a için (a, a) ∈ R.
- **Simetri** (symmetric): (a, b) ∈ R ise (b, a) ∈ R.
- **Geçişlilik** (transitive): (a, b) ve (b, c) ∈ R ise (a, c) ∈ R.

Üçünü birden sağlayan bağıntıya **denklik bağıntısı** denir. Bir denklik bağıntısı, kümeyi ayrık **denklik sınıflarına** böler; her eleman tam bir sınıfta bulunur. Örneğin tam sayılar üzerinde "a ≡ b (mod 3)" bir denklik bağıntısıdır ve 0'dan 11'e kadar sayılar üç sınıfa ayrılır: {0, 3, 6, 9}, {1, 4, 7, 10} ve {2, 5, 8, 11}. Bu sınıfların birleşimi, tüm kümeyi verir ve kesişimleri boştur. Bölüm 17.10'daki Union-Find veri yapısı, bu sınıfları dinamik olarak birleştirmek için tasarlanmıştır.

**Kısmi sıra ve Hasse diyagramı.** Bir bağıntı yansıma, antisimetri (a ≤ b ve b ≤ a ise a = b) ve geçişlilik sağlıyorsa **kısmi sıradır**. Bağıntının bütün elemanları karşılaştırılabilir olmak zorunda değildir; bu yüzden "kısmi" der. Bir kısmi sıranın yapısını görmek için **Hasse diyagramı** çizilir: yalnızca **örtme ilişkisi** (a < b ve arada hiçbir c yok) kenar olarak gösterilir, geçişli kenarlar atılır. 12'nin bölenleri üzerindeki "bölen" ilişkisi bunun iyi bir örneğidir.

![Şekil 47.2: 12'nin bölenleri üzerindeki bölme ilişkisinin Hasse diyagramı. Kenarlar yalnızca örtme ilişkilerini gösterir.](gorseller/b47_hasse.png)

Şekil 47.2'de 1 ve 12 arasında 2 ve 3 gibi yollar var, ama 1'den 12'ye doğrudan kenar yok; çünkü arada 2 ve 6 gibi bölenler var. Bu, Hasse diyagramının kuralıdır. Kısmi sıralarda en önemli uygulama **topolojik sıralamadır**: bir bağımlılık grafında (örneğin derleme sırasındaki modüller) her elemanı, ondan önce gelmesi gerekenlerden sonra yerleştiren bir doğrusal sıra. Bunun doğrusal sıra olabilmesi için bağımlılığın bir döngü içermemesi gerekir (Bölüm 17.3). Aşağıdaki programda Hasse kenarlarını bulup Python'un `graphlib` modülüyle topolojik sırasını alıyoruz. Aynı programda Bölüm 9'daki hash çakışmasını ve doğum günü paradoksunu da ölçüyoruz.

```python
# -*- coding: utf-8 -*-
# kume_graf.py - Hasse kenarlari, topolojik sira, dogum gunu.
import graphlib
import itertools
import math
import random


def hasse_kenarlari(sayilar):
    """a -> b: a | b ve arada baska bolen yok (orten kenar)."""
    kenar = []
    for a, b in itertools.permutations(sayilar, 2):
        if a < b and b % a == 0:
            ara = [c for c in sayilar
                   if a < c < b and c % a == 0 and b % c == 0]
            if not ara:
                kenar.append((a, b))
    return sorted(kenar)
```

İkinci parça, M kovalı bir hash tablosuna rastgele anahtar atıp ilk çakışmaya kadar geçen adım sayısını ortalayan simülasyondur. Rastgele sayı üreteci sabit tohumla (47) başlatılır, böylece sonuçlar yeniden üretilebilir.

```python
def dogum_gunu(M, deneme, rnd):
    """M kovaya rastgele atarken ilk cakisma icin ortalama adim."""
    toplam = 0
    for _ in range(deneme):
        gorulen, k = set(), 0
        while True:
            k += 1
            h = rnd.randrange(M)
            if h in gorulen:
                break
            gorulen.add(h)
        toplam += k
    return toplam / deneme
```

Son parça ana programdır: Hasse kenarlarını, topolojik sırayı ve iki tablo boyutu için simülasyonu yazdırır.


```python
if __name__ == "__main__":
    kenar = hasse_kenarlari([1, 2, 3, 4, 6, 12])
    print("Hasse kenarlari:", " ".join(f"{a}->{b}" for a, b in kenar))
    ts = graphlib.TopologicalSorter()
    for a, b in kenar:
        ts.add(b, a)
    print("Topolojik sira:", list(ts.static_order()))
    rnd = random.Random(47)
    for M in (365, 10000):
        ort = dogum_gunu(M, 4000, rnd)
        print("M =", M, " ort. ilk cakisma:", round(ort, 1),
              " sqrt(pi*M/2) =", round(math.sqrt(math.pi * M / 2), 1))
```

Programın çıktısı Hasse kenarlarını, topolojik sırayı ve iki tablo boyutu için doğum günü simülasyonunun sonucunu verir:

```term
$ python kume_graf.py
Hasse kenarlari: 1->2 1->3 2->4 2->6 3->6 4->12 6->12
Topolojik sira: [1, 2, 3, 4, 6, 12]
M = 365  ort. ilk cakisma: 24.6  sqrt(pi*M/2) = 23.9
M = 10000  ort. ilk cakisma: 126.6  sqrt(pi*M/2) = 125.3
```

Topolojik sıra, bütün kenarların soldan sağa gittiği bir doğrusal sıradır: 1, 2, 3, 4, 6, 12. Hasse diyagramındaki her kenar, sıralamada daha küçük olan elemanı önce gösterir.

**Fonksiyonlar: birebir, örten, eşleme.** f: A → B bir fonksiyon, her a ∈ A'ya tek bir f(a) ∈ B atar. Birebir (injective) fonksiyonda farklı girdiler farklı çıktılar verir. Örten (surjective) fonksiyonda her b ∈ B, bir a için f(a) = b olacak şekilde görülür. İkisi birden varsa eşlemedir (bijective) ve tersi tanımlıdır. Bu üç kavram, hash fonksiyonlarını anlamanın temelidir: bir hash fonksiyonu çok büyük bir evrenden (tüm dizgeler) küçük bir kümeye (0..M-1) gider. Bu fonksiyon birebir olamaz; her zaman çakışmalar olur.

**Güvercin yuvası ilkesi.** n nesneyi m kutuya koyarken n > m ise en az bir kutuda en az iki nesne vardır. Bu ilkenin ispatı basittir ama sonuçları şaşırtıcıdır. 366 kişinin doğum gününü 365 kutuya (her gün bir kutu) yerleştirirsen, en az iki kişinin doğum günü çakışır. Daha ilginç soru, ilk çakışmanın ne zaman olduğudur: **doğum günü paradoksu**. M kovalı bir hash tablosunda ilk çakışma için beklenen eleman sayısı yaklaşık √(πM/2)'dir. Bu, yukarıdaki programın çıktısında görülüyor: M = 365 için simülasyon 24.6 verir, formül 23.9 verir ve fark rastgele örneklemeden gelir. Bu sonuç, 23 kişilik bir sınıfta iki kişinin aynı doğum gününü paylaşma olasılığının yarıdan büyük olmasının nedenidir. Hash tablosu tasarlarken çakışmanın sezgimizden çok daha erken geldiğini bilmek, Bölüm 9.3'teki "çakışma kaçınılmazdır" uyarısının matematiksel karşılığıdır.

**Sayılabilirlik ve köşegenleştirme.** Doğal sayılar (ℕ), tam sayılar (ℤ) ve rasyonel sayılar (ℚ) **sayılabilirdir**: onları 1, 2, 3, ... diye bir listeye yerleştirebilirsin. Gerçek sayılar (ℝ) ise sayılamaz. Bunu Cantor'un **köşegenleştirme** argümanıyla görürsün. Sonsuz bir ikili dizi listesi düşün: her satır bir dizidir. Yeni bir dizi oluştur: i. konumdaki bit, listedeki i. dizinin i. bitinin tersi olsun. Bu yeni dizi listedeki hiçbir diziye eşit olamaz; çünkü her birinden en az bir konumda farklıdır. Yani hiçbir liste tam değildir.

Aynı argüman **durma problemini** de yıkar: "Her programın durup durmayacağını belirleyen genel bir program yazılabilir mi?" sorusunun cevabı hayırdır (Bölüm 36.13). Köşegenleştirme burada da kullanılır. Bu, statik analiz araçlarının neden her zaman kesin cevap veremediğinin matematiksel nedenidir.

## 47.5 Sayma: kombinatorik

Sayma (kombinatorik), bir kümenin kaç farklı biçimde düzenlenebileceğini ya da seçilebileceğini hesaplamaktır. Mühendislikte sayma, bir parolanın kırılma süresini, bir algoritmanın olası durumlarını ve bir testin kapsamını tahmin etmek için kullanılır.

**Toplama ve çarpma kuralları.** İki işlem ayrık ve sırayla seçiliyorsa seçim sayısı çarpılır; iki ayrık durumdan biri seçiliyorsa sayılar toplanır. Sekiz karakterli, yalnızca küçük harf ve rakamlardan oluşan bir parolanın sayısı 36^8 ≈ 2.8·10^12'dir. Bu sayı, kaba kuvvet denemesinin ne kadar sürdüğünü anlamanın ilk adımıdır.

**Permütasyon ve kombinasyon.** n farklı nesnenin tamamının sıralanışı n! ile verilir. n nesneden k tanesinin sıralı seçimi P(n, k) = n!/(n−k)! ile verilir. Sırasız seçim, yani kombinasyon, C(n, k) = n!/(k!(n−k)!) ile verilir; bu sayıya "n üzeri k" denir ve Python'da `math.comb(n, k)` ile hesaplanır. Sıra önemliyse permütasyon, önemli değilse kombinasyon kullanırsın. Bu ayrım, mülakattaki sayma sorularının çoğunda hatanın kaynağıdır.

**Binom teoremi ve Pascal üçgeni.** (x + y)^n = Σ C(n, k)·x^(n−k)·y^k. Bu, x = y = 1 alınarak Σ C(n, k) = 2^n sonucunu verir: bir kümenin alt küme sayısı 2^n'dir. Katsayılar, C(n, k) = C(n−1, k−1) + C(n−1, k) yinelemesiyle üretilir; bu, bir elemanın seçilip seçilmemesine göre ayrım yapmanın sayma karşılığıdır. Bu yinelemeyi bir tablo ile görüyorsun; aynı tablo, dinamik programlamadaki tabulation (Bölüm 16.3) ile birebir aynı mantıktır.

![Şekil 47.3: Pascal üçgeni, 0. satırdan 6. satıra kadar. Bordo çerçeveli satır C(6, k) değerlerini verir.](gorseller/b47_pascal.png)

**Tekrarlı seçimler ve yıldızlar ve çubuklar.** x1 + x2 + x3 = 10 denkleminin negatif olmayan tam sayı çözümlerinin sayısı kaçtır? On yıldızı üç kutuya çubuklarla bölmek gibi düşün: iki çubuk, on üç yerden ikisine konur: C(12, 2) = 66. Genel olarak n eşit nesnenin k kutuya dağıtımı C(n+k−1, k−1) ile verilir. Bu, sayım problemlerinde en sık kullanılan kalıplardan biridir ve bir sonraki bölümde yazacağımız özyinelemeli bağıntılarda da karşımıza çıkar.

**İçerme-dışlama ilkesi.** İki kümenin birleşiminin eleman sayısı |A ∪ B| = |A| + |B| − |A ∩ B| ile verilir: kesişimi iki kez saydığımız için bir kez çıkarırız. Üç küme için |A ∪ B ∪ C| = |A| + |B| + |C| − |A ∩ B| − |A ∩ C| − |B ∩ C| + |A ∩ B ∩ C|. Genel formül bu desenin devamıdır: tek sayıda kümenin kesişimi eklenir, çift sayıda olanı çıkarılır. Şekil 47.4'te üç kümeli bir örneği, 1'den 1000'e kadar 2, 3 veya 5'e bölünebilen sayıları görüyorsun. Sayıların bölge dağılımı ve 734 toplamı Çözümlü Örnek 3'te ayrıntılı çözülüyor.

![Şekil 47.4: 1..1000 arasında 2'ye, 3'e ve 5'e bölünebilen sayıların Venn bölgeleri. Dış bölgede 266 sayı vardır.](gorseller/b47_icerme_venn.png)

**Bozuk permütasyonlar (derangement).** Bir permütasyon, hiçbir elemanı kendi yerinde bırakmıyorsa bozuktur. D_n, n elemanlı bozuk permütasyonların sayısıdır. İçerme-dışlama ile D_n = Σ_{k=0}^{n} (−1)^k · n!/k! formülü elde edilir: sabit noktaları olan permütasyonları çıkar, sonra çift sabit noktalı olanları geri ekle ve böyle devam et. Aşağıdaki programda formülü, n ≤ 8 için kaba kuvvetle (bütün permütasyonları tek tek deneyerek) karşılaştırıyoruz. Programı üç parçada veriyoruz.

```python
# -*- coding: utf-8 -*-
# sayma.py - bozuk permutasyon, Catalan ve Binet denetimi.
import itertools
import math


def bozuk_formul(n):
    """D_n = sum_{k=0}^{n} (-1)^k * n!/k!"""
    return sum((-1) ** k * (math.factorial(n) // math.factorial(k))
               for k in range(n + 1))


def bozuk_kaba(n):
    return sum(1 for p in itertools.permutations(range(n))
               if all(p[i] != i for i in range(n)))


def catalan(n):
    return math.comb(2 * n, n) // (n + 1)
```

İkinci parça, uzunluğu 2n olan dengeli parantez dizgilerini sayan kaba kuvvet fonksiyonudur. Her dizginin dengeli olup olmadığını, açık parantez sayacının hiç negatife düşmemesi ve sonunda sıfır olması ile denetler.

```python
def dengeli_kaba(n):
    """Uzunlugu 2n olan dengeli parantez dizgilerini sayar."""
    say = 0
    for dizgi in itertools.product("()", repeat=2 * n):
        d, gecerli = 0, True
        for c in dizgi:
            d += 1 if c == "(" else -1
            if d < 0:
                gecerli = False
                break
        if gecerli and d == 0:
            say += 1
    return say
```

Üçüncü parça Binet formülünü ve doğrudan yinelemeli Fibonacci hesabını tanımlar; bu ikisini 47.6'da karşılaştıracağız.

```python
def binet(n):
    s5 = math.sqrt(5)
    return round(((1 + s5) / 2) ** n / s5
                 - ((1 - s5) / 2) ** n / s5)


def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
```

Son parça ana programdır; her sayı dizisini kendi formülüyle karşılaştırır ve Binet'in ilk yanlış n değerini arar.

```python
if __name__ == "__main__":
    print("n  kaba  formul")
    for n in range(9):
        print(n, bozuk_kaba(n), bozuk_formul(n))
    print("n  dengeli  catalan")
    for n in range(7):
        print(n, dengeli_kaba(n), catalan(n))
    ilk = next(n for n in range(200) if binet(n) != fib(n))
    print("Binet ilk yanlis n:", ilk)
    print("F(71) =", fib(71), " binet(71) =", binet(71))
```

Çıktının ilk bölümü bozuk permütasyonları, ikinci bölümü dengeli parantez dizgilerini ve Catalan sayılarını, son satırları ise Fibonacci sayısının Binet formülüyle hesaplanmasını gösterir. Son kısmı 47.6'da açıklayacağız; önce ilk iki bölüme bakalım.

```term
$ python sayma.py
n  kaba  formul
0 1 1
1 0 0
2 1 1
3 2 2
4 9 9
5 44 44
6 265 265
7 1854 1854
8 14833 14833
n  dengeli  catalan
0 1 1
1 1 1
2 2 2
3 5 5
4 14 14
5 42 42
6 132 132
Binet ilk yanlis n: 71
F(71) = 308061521170129  binet(71) = 308061521170130
```

Formül ile kaba kuvvet tam olarak eşleşiyor. Bozuk permütasyon oranı D_n/n!, n büyüdükçe 1/e ≈ 0.36788'e yakınsar. Şekil 47.5 bu yakınsamayı gösterir. Bu oran, rastgele bir permütasyonun hiçbir elemanını kendi yerinde bırakmama olasılığıdır ve bu olasılığın n'den bağımsız olarak neredeyse sabit kalması şaşırtıcıdır. Ayrıca n ≥ 1 için D_n, n!/e sayısına en yakın tam sayıdır (bilinen sonuç).

![Şekil 47.5: Bozuk permütasyon oranı D_n/n! ile 1/e değerinin n'ye göre yakınsaması. Veri engine/veri/b47_derangement.csv dosyasındadır.](gorseller/b47_derangement.png)

**Catalan sayıları.** C_n = C(2n, n)/(n+1) ile tanımlanan bu dizi 1, 1, 2, 5, 14, 42, 132, ... diye gider. Programın ikinci bölümü, uzunluğu 2n olan dengeli parantez dizgilerinin sayısının bu formülle aynı olduğunu gösterir. Catalan sayılarının aynı dizinin başka yorumları da vardır: n iç düğümlü tam ikili ağaçların sayısı, (n+2)-kenarlı bir dışbükey çokgenin üçgenlemelerinin sayısı ve n+1 matrisli bir zincirin parantezlenme sayısı. Bölüm 15'te geri izlemeyle parantez dizgilerini ürettik; Bölüm 16.9'da ise matris zincirinin parantezlenme sayısının Catalan olduğunu gördük. Üç yorum da aynı sayıya dayanır: bir yapının yinelemeli tanımı, Catalan'ın özyinelemesine uyar. Bu özyinelemeyi kendin kanıtlamaya çalış (Ek Alıştırmalar).

**Üretici fonksiyonlara kısa bir giriş.** Bir sayı dizisini (a_0, a_1, a_2, ...) bir kuvvet serisinin katsayıları olarak yazabilirsin: A(x) = Σ a_n·x^n. Para bozma problemi bu gösterimle çok temiz görünür: 1, 2 ve 5 kuruşluk madenilerle n kuruşu kaç farklı yolla oluşturabilirsin? Cevap, 1/((1−x)(1−x^2)(1−x^5)) fonksiyonunun x^n katsayısıdır. Bu seriyi açmak yerine Bölüm 16'daki para bozma dinamik programlaması aynı katsayıyı hesaplar. Üretici fonksiyon, sayma problemlerini cebirsel bir dile çevirerek çözmenin yoludur.

## 47.6 Özyinelemeli bağıntılar: diziyi kapalı biçimle anlamak

Birçok sayma ve algoritma analizi problemi bir dizi tanımlar: a_n, a_{n−1} ve belki a_{n−2} cinsinden verilir. Bu tanıma **özyinelemeli bağıntı** denir. Bölüm 12.9'da bu bağıntıları yerine koyma ve ağaç yöntemiyle çözdük. Burada ise **kapalı biçim** (closed form) arıyoruz: a_n'yi doğrudan n'nin bir fonksiyonu olarak veren formül. Kapalı biçim, n çok büyükken bile a_n'yi hızlıca hesaplamanın yoludur.

**Doğrusal homojen bağıntılar.** Bir a_n = c_1·a_{n−1} + c_2·a_{n−2} bağıntısı, katsayılar sabitse ve sağ taraf yalnızca önceki terimlerden oluşuyorsa doğrusal homojendir. Çözüm için a_n = r^n denemesi yaparsın; bu, r^2 = c_1·r + c_2 **karakteristik denklemini** verir. Kökler r_1 ve r_2 ise genel çözüm a_n = A·r_1^n + B·r_2^n'dir; A ve B başlangıç değerlerinden bulunur. Kökler çakışıksa çözüm (A + Bn)·r^n biçimini alır.

**Fibonacci ve Binet formülü.** F_n = F_{n−1} + F_{n−2}, F_0 = 0, F_1 = 1 bağıntısının karakteristik denklemi r^2 = r + 1'dir. Kökleri φ = (1 + √5)/2 ve ψ = (1 − √5)/2'dir. Başlangıç değerleri ile F_n = (φ^n − ψ^n)/√5 buluruz. Bu **Binet formülüdür**. Formül, F_n'yi n'nin bir fonksiyonu olarak verir; ama ilginç bir tuzağı var: formülde √5 ve φ gerçek sayılardır ve bilgisayar bunları kayan nokta ile hesaplar. Yukarıdaki programın son satırları bu tuzağı gösterir: kayan nokta ile hesaplanan Binet formülü, n = 71'de ilk kez yanlış tam sayı verir.

Bu, kayan nokta aritmetiğinin temel bir sınırıdır. Gerçek sayılar sonsuz hassasiyetli olsa da bilgisayar yalnızca 53 bit mantisle çalışır; φ^n büyüdükçe küçük yuvarlama hataları da büyür. Büyük Fibonacci sayılarını doğru hesaplamanın yolu, tamsayı aritmetiğiyle yinelemeli hesaptır veya matris üssüdür (Bölüm 19.4). Bu, bir matematiksel formülün her zaman bir bilgisayar algoritması olarak doğru olmadığının iyi bir örneğidir.

**Homojen olmayan bağıntılar.** Hanoi kulesi problemi T_n = 2·T_{n−1} + 1 bağıntısını verir: n diski taşımak için önce n−1 diski taşı, en alttakini taşı, sonra n−1 diski tekrar taşı. Sağ tarafta sabit 1 olduğu için bağıntı homojen değildir. Çözüm, homojen kısım ile özel bir çözümün toplamıdır. Özel çözüm sabit c olsun: c = 2c + 1, yani c = −1. Homojen kısım A·2^n'dir. T_0 = 0 ise A = 1 ve T_n = 2^n − 1 elde edilir. Bu, Hanoi'de n diski taşımanın en az 2^n − 1 hamle gerektirdiğini gösterir. Bu sonucu tümevarımla ispatlamak, 47.3'teki tekniğin doğrudan uygulamasıdır.

**Master teoremi ile bağlantı.** Bölüm 12.9 ve 19.2'de gördüğümüz T(n) = a·T(n/b) + f(n) biçimindeki bağıntılar, bölen ve fethet algoritmalarının analizini verir. Birleştirme sort'unun T(n) = 2·T(n/2) + n bağıntısı, Master teoremiyle n·log n sonucunu verir. Bölme-fetih bağıntıları doğrusal homojen değildir ama karakteristik denklem yöntemiyle çözülemez; onun için Master teoremi kullanılır. Bu iki bakış, aynı problemin iki yüzüdür: biri kapalı biçim arar, diğeri büyüme sınıfı arar.

::: dikkat
Bir özyinelemeli bağıntının kapalı biçimini bulduğunda, ilk birkaç değeri tümevarımla doğrulamadan kullanma. Fibonacci örneğinde formül n = 70'e kadar doğru çıkar, n = 71'de yanlış çıkar. Bir formülü her zaman küçük ve büyük değerlerle sına.
:::

## 47.7 Sayılar teorisi: bölme, modüler aritmetik ve asallık

Sayılar teorisi, tam sayıların yapısını inceler. Bilgisayar biliminde bu konu neredeyse her yerde karşımıza çıkar: hash fonksiyonlarında, rastgele sayı üretiminde, hata düzeltme kodlarında ve en önemlisi kriptografide. Bölüm 19'da hızlı üs alma ile modüler üssü gördün; burada bu araçların matematiksel zeminini kuruyoruz.

**Bölünebilirlik ve en büyük ortak bölen.** a | b, a'nın b'yi böldüğü anlamına gelir: b = a·k olacak bir tam sayı k vardır. Hem a'yı hem b'yi bölen en büyük sayı gcd(a, b)'dir. Bunu bulmanın en eski ve en iyi yolu **Öklid algoritmasıdır**: gcd(a, b) = gcd(b, a mod b). Bu eşitlik neden doğrudur? a = q·b + r ise a ile b'nin ortak bölenleri, b ile r'nin ortak bölenleriyle aynıdır, çünkü r = a − q·b. Yani kalan küçülür ve sıfıra ulaşana kadar devam ederiz; son sıfır olmayan kalan gcd'dir.

Adım sayısı, sayıların büyüklüğüne göre logaritmik büyür; en kötü durum Fibonacci sayılarıyla gelir (genel bilgi). Şekil 47.6, gcd(240, 46) için adımları gösterir.

![Şekil 47.6: Öklid algoritmasının gcd(240, 46) hesabındaki adımları. Son sıfır olmayan kalan 2'dir.](gorseller/b47_oklid.png)

**Genişletilmiş Öklid algoritması.** Öklid, bir gcd bulmakla kalmaz; aynı adımlarla a·x + b·y = gcd(a, b) denklemini sağlayan x ve y tam sayılarını da verir. Bu, **Bézout özdeşliği**dir. Her adımda kalanı, kalanın a ve b cinsinden katsayılarıyla birlikte takip edersin. Bu katsayılar, modüler tersi bulmanın anahtarıdır. Aşağıdaki kütüphane modülü, bu fonksiyonu ve bu bölümün sayılar teorisi araçlarının çoğunu içerir. Modülü üç parçada veriyoruz.

```python
# -*- coding: utf-8 -*-
# sayilar.py - Oklid ailesi, CRT, Euler totient, asallik testleri.
import math

TABAN = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


def ext_gcd(a, b):
    """Doner: (g, x, y), oyle ki a*x + b*y = g = gcd(a, b)."""
    if b == 0:
        return a, 1, 0
    g, x1, y1 = ext_gcd(b, a % b)
    return g, y1, x1 - (a // b) * y1


def mod_ters(a, m):
    g, x, _ = ext_gcd(a % m, m)
    if g != 1:
        raise ValueError("ters yok")
    return x % m


def crt(kalanlar, modler):
    """x = kalan_i (mod m_i); moduller ikişerli asal olmali."""
    x, M = 0, 1
    for r, m in zip(kalanlar, modler):
        t = (r - x) * mod_ters(M, m) % m
        x += M * t
        M *= m
    return x % M, M
```

İkinci parçada Eratosthenes eleği ve Miller–Rabin testi, üçüncü parçada Euler totient fonksiyonu vardır. Eleme, iç döngü sayısını da döndürür; bu sayı karmaşıklık ölçümü için kullanılacak.

```python
def eleme(n):
    """Eratosthenes. Doner: (asal listesi, ic dongu sayisi)."""
    ele = [True] * (n + 1)
    ele[0:2] = [False, False]
    ops = 0
    for p in range(2, math.isqrt(n) + 1):
        if ele[p]:
            for k in range(p * p, n + 1, p):
                ele[k] = False
                ops += 1
    return [i for i in range(n + 1) if ele[i]], ops


def mr(n, tabanlar=TABAN):
    """Saf Miller-Rabin. n tek ve 37'den buyuk varsayilir."""
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in tabanlar:
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def asal_mi(n):
    if n < 2:
        return False
    for p in TABAN:
        if n % p == 0:
            return n == p
    return mr(n)
```

Son parça, Euler totient fonksiyonudur:

```python
def phi(n):
    """Euler totient: asal carpanlari uzerinden."""
    sonuc, m, p = n, n, 2
    while p * p <= m:
        if m % p == 0:
            while m % p == 0:
                m //= p
            sonuc -= sonuc // p
        p += 1
    if m > 1:
        sonuc -= sonuc // m
    return sonuc
```

**Modüler aritmetik ve ters.** a ≡ b (mod n), n | (a − b) demektir: a ve b, n'e bölümlerinden aynı kalanı bırakır. Modüler aritmetik saat aritmetiğidir: 11 saat sonra 3 değil, 14 mod 12 = 2 sonrası vardır. Modüler bölme yoktur; yerine **modüler ters** kullanılır. a'nın m'ye göre tersi, a·x ≡ 1 (mod m) çözümüdür. Bu çözüm ancak gcd(a, m) = 1 ise vardır ve Bézout özdeşliğinden hemen gelir: a·x + m·y = 1 ise a·x ≡ 1 (mod m). Python 3.8'den beri `pow(a, -1, m)` bunu doğrudan yapar; ters yoksa `ValueError` fırlatır. Kendi `mod_ters` fonksiyonumuz aynı işi genişletilmiş Öklid ile yapar.

**Çin kalan teoremi (CRT).** Sun Zi'nin klasik sorusu: 3'e bölünce 2, 5'e bölünce 3, 7'ye bölünce 2 kalanını veren en küçük doğal sayı nedir? Moduller ikişerli asal olduğunda, her sistemin tek bir çözümü vardır ve bu çözüm moduller çarpımına göre tanımlanır. Cevap 23'tür (mod 105). CRT, büyük sayılarla çalışırken aynı işi küçük parçalarda yapmanın yoludur; RSA'nın hızlandırılmış çözümünde ve hata düzeltme kodlarında kullanılır. Kodumuz, her adımda kısmi çözümü yeni modülle uzlaştırır ve gerekli tersi `mod_ters` ile hesaplar.

**Euler totient ve Fermat'ın küçük teoremi.** φ(n), 1 ≤ k ≤ n aralığında n ile aralarında asal olan sayıların sayısıdır. Asal bir p için φ(p) = p − 1'dir. Asal kuvvetlerde φ(p^k) = p^k − p^(k−1)'dir ve çarpımsaldır: aralarında asal m, n için φ(mn) = φ(m)·φ(n). Bu iki kuraldan φ(n) hesaplanır. Bunun iki önemli sonucu vardır:

- **Fermat'ın küçük teoremi**: p asalsa ve p, a'yı bölmüyorsa a^(p−1) ≡ 1 (mod p).
- **Euler teoremi**: gcd(a, n) = 1 ise a^φ(n) ≡ 1 (mod n).

Euler teoremi, RSA'nın neden çalıştığının kalbidir (47.8). Yukarıdaki kütüphanedeki `phi` fonksiyonu, asal çarpanlarına ayırarak φ(n) hesaplar: önce n'nin her asal çarpanını bulup her birinde sonucu p'nin payıyla (1 − 1/p) çarpar gibi küçültür. Bu, φ(n) = n·Π(1 − 1/p) formülünün tam sayı hâlidir.

**Asallık testleri.** Bir sayının asal olup olmadığını anlamak için üç yöntem karşılaştırabiliriz. Deneme bölmesi, √n'e kadar bütün sayılara bölmeyi dener: n = 10^12 için yaklaşık 10^6 adım gerekir. Eratosthenes eleği, 1'den N'e kadar bütün asalları bir seferde bulur ve iç döngü sayısı n·ln(ln n) büyüklüğündedir. Miller–Rabin ise tek bir sayı için birkaç üssel mod hesabı yapar ve olasılıksal bir testtir.

Eleme ile Miller–Rabin'in karşılaştırıldığı programı şimdi çalıştıralım. Bu program, kütüphanedeki fonksiyonları kullanır ve RSA örneğinin sayılarını da hesaplar.

```python
# -*- coding: utf-8 -*-
# sayilar_test.py - sayilar.py icin denetim ve RSA ornegi.
import math
from sayilar import ext_gcd, mod_ters, crt, eleme, asal_mi, mr, phi

if __name__ == "__main__":
    print("ext_gcd(240, 46) =", ext_gcd(240, 46))
    print("17^-1 mod 3120 =", mod_ters(17, 3120))
    print("CRT:", crt([2, 3, 2], [3, 5, 7]))
    asal, ops = eleme(10 ** 6)
    print("N=10^6: asal =", len(asal), " ic dongu =", ops)
    print("1000000007 asal mi:", asal_mi(1000000007))
    print("3215031751, taban (2,3,5,7):",
          mr(3215031751, (2, 3, 5, 7)))
    print("2047, taban (2):", mr(2047, (2,)))
    kume = set(eleme(10 ** 5)[0])
    hata = sum(asal_mi(n) != (n in kume) for n in range(10 ** 5))
    print("n < 10^5 icin eleme ile hata:", hata)
    tasar = [a for a in range(2, 561) if math.gcd(a, 561) == 1]
    print("561 Fermat'i geciren taban:",
          sum(pow(a, 560, 561) == 1 for a in tasar), "/", len(tasar))
    print("phi(36) =", phi(36), " phi(3233) =", phi(3233))
    # RSA: p=61, q=53
    p, q = 61, 53
    n, f, e = p * q, (p - 1) * (q - 1), 17
    d = mod_ters(e, f)
    print("n, phi, e, d =", n, f, e, d)
    c = pow(65, e, n)
    print("65 sifreli:", c, " cozulmus:", pow(c, d, n))
    print("tum m icin (m^e)^d == m:",
          all(pow(pow(m, e, n), d, n) == m for m in range(n)))
```

Programın çıktısı, kütüphanenin ve RSA örneğinin sonuçlarını sırayla verir:

```term
$ python sayilar_test.py
ext_gcd(240, 46) = (2, -9, 47)
17^-1 mod 3120 = 2753
CRT: (23, 105)
N=10^6: asal = 78498  ic dongu = 2122048
1000000007 asal mi: True
3215031751, taban (2,3,5,7): True
2047, taban (2): True
n < 10^5 icin eleme ile hata: 0
561 Fermat'i geciren taban: 319 / 319
phi(36) = 12  phi(3233) = 3120
n, phi, e, d = 3233 3120 17 2753
65 sifreli: 2790  cozulmus: 65
tum m icin (m^e)^d == m: True
```

Çıktıda birkaç şey dikkatini çekmeli. N = 10^6 için eleme 78498 asal bulur ve iç döngüyü 2,122,048 kez çalıştırır; bu sayı n·ln(ln n) ≈ 2.6·10^6 ile aynı büyüklük sırasındadır. Deneme bölmesi 10^9+7 sayısı için yaklaşık √(10^9) ≈ 31.6 bin bölme adımı atardı; Miller–Rabin ise aynı soruyu 12 üssel mod hesabıyla yanıtlar. Bu fark, büyük sayılarda neden deneme bölmesinin yetmediğini gösterir.

**Miller–Rabin ve sözde asallar.** Fermat testi, a^(n−1) ≡ 1 (mod n) koşulunu denetler. Asal n için her taban geçer, ama bazı bileşik sayılar da bütün tabanlarla geçer. Bu sayılara **Carmichael sayıları** denir; en küçüğü 561 = 3·11·17'dir. Çıktıda 561'in, 561 ile aralarında asal olan 319 tabanın hepsiyle Fermat testini geçtiği görülüyor. Yani aralarında asal olan hiçbir tabanla Fermat testi 561'in bileşik olduğunu yakalayamaz. Aralarında asal olmayan tabanlar (3, 11, 17 gibi) ise testi zaten geçemez.

Miller–Rabin bu zaafı **güçlü sözde asal** koşuluyla kapatır: n − 1 = 2^s·d olarak yazılır ve a^d, sonra a^(2d), a^(4d), ... dizisinde 1 ya da −1 ile karşılaşılması beklenir. Bu koşulu sağlayan bir bileşik sayıya güçlü sözde asal denir. Çıktıdaki iki satır bunu gösterir. 2047 = 23·89'dur ve taban 2 ile güçlü sözde asaldır; yani yalnızca 2 tabanı kullanılırsa test yanlış "asal" der. 3215031751 = 151·751·28351'dir ve taban (2, 3, 5, 7) ile de yanlış "asal" der. Bu yüzden testte tek bir taban yetmez: birden fazla taban kullanılır.

Bilinen bir sonuç: ilk 12 asal (2'den 37'ye) tabanıyla yapılan Miller–Rabin testi, n < 3.18·10^23 için kesindir (Sorenson ve Webster, 2015; genel bilgi). 64 bit sayılar için daha küçük, yaygın olarak kullanılan bir 7 tabanlı küme de vardır (genel bilgi). Kütüphanedeki `asal_mi`, küçük asallarla hızlı eleme yapar ve sonra 12 tabanla Miller–Rabin uygular; 10^5'e kadar tüm sayılarda eleme ile aynı sonucu verir (çıktıdaki "hata: 0"). Bir bileşik sayının tek bir tabanla testi geçme olasılığı en fazla 1/4'tür (genel bilgi); 12 taban bu hatayı pratikte yok eder.

::: not
Miller–Rabin'in olasılıksal bir test olarak yaygın kullanımı, deterministik tabanlarla birlikte yapıldığında bile "kesin" değil "bilinen sınırlar içinde kesin"dir. Bir kriptografik sistemde anahtar üretiminde bu kadar yeterlidir; ama her zaman bir kütüphanenin (örneğin OpenSSL) uygulamasını kullan, kendi testini yazma.
:::

## 47.8 RSA'nın matematiği: neden çalışır?

RSA, 1977'de Rivest, Shamir ve Adleman'ın önerdiği açık anahtarlı şifreleme yöntemidir. Bölüm 32'de imzayı ve TLS'i gördük; bu imzaların altında yatan matematik işte budur. Bu bölümde RSA'yı küçük bir anahtarla elle çalıştırıp neden çalıştığını kanıtlayacağız.

**Anahtar üretimi.** İki büyük asal p ve q seç; n = p·q. φ(n) = (p − 1)(q − 1). Bir e seç ki gcd(e, φ(n)) = 1 olsun (pratikte 65537 yaygındır). d = e^(−1) mod φ(n) hesapla. **Açık anahtar** (n, e), **özel anahtar** d'dir. p, q ve φ(n)'i kimse bilmemelidir.

**Şifreleme ve çözme.** Mesaj m (0 ≤ m < n) için şifreli metin c = m^e mod n'dir. Çözme m = c^d mod n'dir. Bu iki işlem modüler üssü gerektirir ve Bölüm 19'daki hızlı üs alma ile yapılır.

**Neden çalışır?** ed ≡ 1 (mod φ(n)) olduğu için ed = 1 + k·φ(n) yazabiliriz. Şimdi c^d = (m^e)^d = m^(ed) = m · (m^φ(n))^k. Eğer gcd(m, n) = 1 ise Euler teoremi m^φ(n) ≡ 1 verir ve sonuç m'dir. Peki m, p veya q ile bölünebiliyorsa ne olur? Bu durumda da çalışır; kanıt CRT'ye dayanır. p'ye göre bakalım: m ≡ 0 (mod p) ise m^(ed) ≡ 0 ≡ m'dir. Değilse Fermat'a göre m^(p−1) ≡ 1 ve (p−1) | (ed − 1) olduğu için m^(ed) ≡ m (mod p). Aynı argümanı q için yaparsak m^(ed) ≡ m (mod q) elde ederiz. p ve q aralarında asal olduğu için CRT, m^(ed) ≡ m (mod pq) verir. Yani her m için doğrudur.

Bunu küçük bir sayıyla elle yapalım: p = 61, q = 53, n = 3233, φ(n) = 60·52 = 3120, e = 17 ve d = 2753. Kontrol: 17·2753 = 46801 = 15·3120 + 1. Bu, ed − 1'in φ(n)'in katı olduğunun doğrudan görülmesidir.

**Çözümlü Örnek 4'te** bu şifrelemeyi, üssü kare-çarpma yöntemiyle elle hesaplayarak izleyeceksin. 47.7'deki programın son üç satırı bu sayıları üretti: 65 mesajı 2790'a şifreleniyor, çözülüyor ve 3233'ün bütün mesajları için (m^e)^d = m eşitliği tutuyor.

**Güvenlik: neden küçük anahtar kırılır, büyük anahtar neden kırılmaz?** Bir saldırgan n'yi çarpanlarına ayırabilirse p ve q'yu bulur, φ(n)'i hesaplar ve d'yi çıkarır. Bu yüzden RSA'nın güvenliği, büyük sayıların çarpanlarına ayrılmasının zorluğuna dayanır. 3233 gibi bir sayıyı deneme bölmesiyle saniyeler içinde çarpanlarına ayırabilirsin. 2048 bitlik bir n için bilinen algoritmalar pratikte çalışmaz (genel bilgi). Ama bu güvenlik, yalnızca çarpanlara ayırmanın zorluğuna dayanmaz; kullanım biçimi de önemlidir.

::: dikkat
Bu bölümde gösterilen RSA, "kitap RSA"sıdır (textbook RSA) ve gerçek bir sistemde kullanılmamalıdır. Aynı m her zaman aynı c'yi verir; bu, bir saldırganın tahmin ettiği mesajı doğrulamasına izin verir. Ayrıca şifreli metin üzerinde yapılan değişiklikler kontrol edilmez. Gerçek sistemler OAEP gibi dolgu (padding) şemaları ve imzalar için PSS kullanır. Kendi RSA'nı yazma; bir kütüphane kullan ve anahtar üretimini ona bırak.
:::

**Mod çarpımda taşma tuzağı.** RSA'nın hesaplamasında, iki 64 bitlik sayının çarpımı 64 biti aşabilir. Bu, modüler çarpımda sessiz hataya yol açar. C'de bunu aşağıdaki kısa programla görebilirsin. Program iki farklı çarpma yöntemi kullanır: birincisi 64 bitlik çarpımı doğrudan kullanır, ikincisi 128 bitlik ara sonuç kullanır.

```c
#include <stdio.h>
#include <stdint.h>

/* a*b mod m: 64 bitlik çarpım taşarsa sonuç yanlış olur. */
static uint64_t carp_kaba(uint64_t a, uint64_t b, uint64_t m)
{
    return (a * b) % m;
}

/* 128 bitlik ara sonuçla doğru çarpım (GCC/Clang uzantısı). */
static uint64_t carp_dogru(uint64_t a, uint64_t b, uint64_t m)
{
    return (uint64_t)(((unsigned __int128)a * b) % m);
}

int main(void)
{
    uint64_t m = 1000000000039ULL;   /* yaklaşık 10^12 */
    uint64_t a = 999999999989ULL;

    printf("kaba  : %llu\n", (unsigned long long)carp_kaba(a, a, m));
    printf("dogru : %llu\n", (unsigned long long)carp_dogru(a, a, m));
    printf("sizeof(long) = %zu\n", sizeof(long));
    return 0;
}
```

Programı önce derleyelim. Kendi makinende WSL içinde şu komutu kullanabilirsin:

```term
$ gcc -O2 -Wall -Wextra -std=c11 mulmod.c -o mulmod
```

Derleme uyarısız bitiyor. Çalıştırdığında çıktı şöyledir:

```term
$ ./mulmod
kaba  : 205128750823
dogru : 2500
sizeof(long) = 8
```

Birinci satır yanlıştır: 64 bitlik çarpım taşmış ve kalan rastgele bir değer olmuştur. İkinci satır, Python'un `999999999989 * 999999999989 % 1000000000039` hesabıyla aynıdır: 2500. Taşma, işaretsiz (unsigned) tamsayılarda tanımlı bir davranıştır ve değer modulo 2^64 sarar. İşaretli tamsayılarda ise taşma tanımsız davranıştır (UB); Bölüm 32.5'teki tamsayı taşması tablosu, UBSan'ın bu tür taşmaları işaretlediğini gösterir. Derleyiciyi `-fsanitize=undefined` ile çalıştırsak da bu işaretsiz taşmayı hata olarak bildirmez, çünkü standart bunu tanımlı sayar. Doğru sonuç için ara değeri 128 bite genişletiyoruz; ancak `unsigned __int128` bir GCC ve Clang uzantısıdır, MSVC'de yoktur.

**Platform notu.** Çıktıdaki `sizeof(long) = 8` satırı WSL'deki Linux'a özgüdür (LP64 modeli: `long` 64 bit). Windows'ta MSVC ve MinGW'nin çoğu sürümünde `long` 32 bittir (LLP64 modeli); bu yüzden taşınabilir kodda `long` yerine `uint64_t` (`<stdint.h>`) kullan. Okur Windows kullandığı için bu fark, aynı C kodunun iki platformda farklı davranmasının somut örneğidir. Gerçek bir RSA uygulamasında bu tür taşmaları çözen kütüphaneler (örneğin GMP) vardır.

::: baglanti
Modüler üssün ve CRT'nin donanımdaki karşılığı, gömülü sistemlerde kriptografik işlemlerin hızlandırılmasıdır. Bölüm 43'te donanım yazmaçlarına bitlerle erişmeyi ve Bölüm 46'da kısıtlı donanımda sayısal hesabı gördün; bu kısıtlar, büyük sayıların modüler aritmetiğini zorlaştırır.
:::

## 47.9 Graf teorisi temelleri: el sıkışma, Euler, ağaç, düzlemsellik, boyama

Graf (graph), düğümlerden (vertex) ve bu düğümleri birleştiren kenarlardan (edge) oluşan bir yapıdır. Bölüm 11'de graf veri yapısını, komşuluk matrisi ve listesiyle tanıdın; Bölüm 17'de DFS, BFS ve en kısa yolları yazdın. Burada graf teorisinin **ispat tarafını** kuruyoruz: bir grafın hangi özelliklerinin zorunlu olduğunu, hangilerinin mümkün olduğunu ve hangilerinin hesaplanmasının neden zor olduğunu.

**El sıkışma lemması.** Bir düğümün derecesi, ona bağlı kenar sayısıdır. Her kenar iki uçta sayıldığından, bütün dereceler toplamı kenar sayısının iki katıdır: Σ deg(v) = 2|E|. Bu, bir partide herkesin el sıkışma sayısı toplamının çift olmasıyla aynıdır. Bir sonuç hemen çıkar: tek dereceli düğümlerin sayısı çifttir, çünkü toplam çifttir ve çift dereceli düğümler çift toplama katkı yapar. Bu basit gözlem, Königsberg problemini çözen anahtardır.

**Königsberg köprüleri ve Euler yolu.** 1736'da Euler, Königsberg şehrindeki yedi köprüden her birini tam bir kez geçerek bir turun mümkün olup olmadığını sordu. Adaları düğüm, köprüleri kenar olarak düşünürsek grafın dereceleri 5, 3, 3, 3'tür. Şekil 47.7 bu grafı gösterir.

![Şekil 47.7: Königsberg köprüleri grafı. Dört düğümün üçü tek dereceli olduğu için her kenarı bir kez geçen yol yoktur.](gorseller/b47_konigsberg.png)

**Euler'in teoremi** (genel bilgi): bağlı bir grafta her kenarı tam bir kez geçen bir yol (Euler yolu) vardır ancak ve ancak tek dereceli düğüm sayısı 0 veya 2'dir. Tek dereceli düğüm sayısı 0 ise kapalı bir tur (Euler devresi) vardır. Königsberg'de dört tek dereceli düğüm var; yol yoktur. Programın çıktısındaki derece listesi bu hesabı verir.

Euler yolu ile **Hamilton yolu** arasındaki fark çok önemlidir. Hamilton yolu, her düğümü tam bir kez ziyaret eder (kenarları değil). Euler yolunun varlığı kolay denetlenir, Hamilton yolunun varlığı ise NP-tam bir problemdir (47.10). Aynı görünen iki soru, hesaplama açısından uçurumla ayrılır.

**Ağaçlar.** Bağlı ve döngüsüz bir grafa **ağaç** denir. n düğümlü her ağacın tam n − 1 kenarı vardır. İspatı tümevarımla verebiliriz (47.3'teki tekniğin bir uygulaması). n = 1 için tek düğüm vardır ve 0 kenarı vardır. n > 1 olan bir ağaçta en az iki yaprak (derecesi 1 olan düğüm) bulunur, çünkü en uzun yolun iki ucu yapraktır. Bir yaprağı kenarıyla birlikte çıkardığımızda kalan graf n − 1 düğümlü, bağlı ve döngüsüz, yani bir ağaçtır. Tümevarım hipotezine göre bu ağacın n − 2 kenarı vardır. Çıkardığımız yaprağın kenarını geri eklersek orijinal ağacın n − 2 + 1 = n − 1 kenarı olur.

Ağaçlar, Bölüm 17'deki DFS ağacı, Kruskal'ın minimum yayılan ağacı ve Bölüm 37'deki sözdizimi ağacının ortak ataları olarak karşımıza çıkar. Her biri bu tanımın bir kullanımıdır.

**Düzlemsel graflar ve Euler formülü.** Bir graf kenarları kesişmeden düzleme çizilebiliyorsa **düzlemseldir**. Bağlı bir düzlemsel grafın köşe sayısı V, kenar sayısı E ve yüz sayısı F ise (dış yüz dâhil) **V − E + F = 2** eşitliği geçerlidir. Şekil 47.8'deki K4 (dört düğümün her çifti bağlı) için V = 4, E = 6, F = 4 ve 4 − 6 + 4 = 2.

![Şekil 47.8: K4 grafının düzlemsel gösterimi. V − E + F = 4 − 6 + 4 = 2. Dört yüzden üçü iç, biri dış yüzdür.](gorseller/b47_euler_formul.png)

Bu formülden bir kısıt çıkar: basit ve düzlemsel bir grafta E ≤ 3V − 6 (her yüz en az üç kenarla sınırlıdır). K5'in V = 5, E = 10'u vardır; 3·5 − 6 = 9 < 10 olduğu için K5 düzlemsel değildir. Üç ev ve üç kuyuyu kesişmeden birbirine bağlamanın imkânsız olduğu problemi (K3,3) ise bir tek kısıtla ele alınır: iki parçalı düzlemsel bir grafta E ≤ 2V − 4'tür. K3,3'te V = 6, E = 9 > 8 olduğu için düzlemsel değildir. Düzlemsellik, devre tasarımında iz (trace) kesişmelerinin olmadığını garanti etmek için önemlidir.

**Graf boyama.** Bir grafı boyamak, komşu düğümlere farklı renk vermektir. En az kaç renk gerektiğine **kromatik sayı** χ(G) denir. Renk sayısı iki ise graf **iki parçalıdır** (bipartite) ve bu, Bölüm 17.4'te gördüğümüz tek uzunluklu döngü yokluğuyla aynıdır. Üç renk ve üzeri ise problem zorlaşır: 3-renklendirme karar problemi NP-tamdır (genel bilgi).

Düzlemsel graflar için **dört renk teoremi** (Appel ve Haken, 1976): her düzlemsel grafın 4 renkle boyanabileceği kanıtlanmıştır. Kanıt, bilgisayar yardımıyla çok sayıda durumun denetlenmesine dayanır (genel bilgi).

Boyama bulmak için en basit sezgisel yöntem **açgözlü boyamadır** (greedy coloring): düğümleri bir sırayla gez, her düğüme komşularının kullanmadığı en küçük rengi ver. Bu yöntem her zaman geçerli bir boyama üretir, ama renk sayısı sıraya bağlıdır. Şekil 47.9'daki taç graf (crown graph) bunu iyi gösterir. Sol kümedeki i düğümü ile sağ kümedeki j düğümü, yalnızca i ≠ j iken birbirine bağlıdır. Bu graf iki parçalıdır, yani 2 renkle boyanabilir; ama kötü sıra 3 renk kullanır.

![Şekil 47.9: Taç grafta açgözlü boyama. Solda kötü sıra 3 renk, sağda iyi sıra 2 renk kullanır. Renkler düğümün dolgusuyla gösterilir.](gorseller/b47_boyama.png)

Aşağıdaki program aynı grafı iki sırayla boyar. Ayrıca Königsberg derecelerini de hesaplar. Programı iki parçada veriyoruz.

```python
# -*- coding: utf-8 -*-
# graf_boyama.py - derece, Konigsberg, tac graf ve acgozlu boyama.


def derece(n, kenarlar):
    d = [0] * n
    for u, v in kenarlar:
        d[u] += 1
        d[v] += 1
    return d


def tac_graf(m):
    """i ~ m+j, i != j: iki parcali, boyama sayisi 2."""
    kom = [[] for _ in range(2 * m)]
    for i in range(m):
        for j in range(m):
            if i != j:
                kom[i].append(m + j)
                kom[m + j].append(i)
    return kom


def acgozlu_boya(n, kom, sira):
    renk = [-1] * n
    for u in sira:
        yasak = {renk[v] for v in kom[u] if renk[v] != -1}
        c = 0
        while c in yasak:
            c += 1
        renk[u] = c
    return renk
```

Ana program, Königsberg derecelerini ve taç grafın iki sırayla boyamasını hesaplar:


```python
if __name__ == "__main__":
    kon = [(0, 1), (0, 1), (0, 2), (0, 2), (0, 3), (1, 3), (2, 3)]
    print("Konigsberg dereceleri:", derece(4, kon))
    m = 3
    kom = tac_graf(m)
    kotu = [0, 3, 1, 4, 2, 5]
    iyi = [0, 1, 2, 3, 4, 5]
    rk = acgozlu_boya(2 * m, kom, kotu)
    ri = acgozlu_boya(2 * m, kom, iyi)
    print("kotu sira:", rk, "->", max(rk) + 1, "renk")
    print("iyi sira: ", ri, "->", max(ri) + 1, "renk")
```

Programın çıktısı, iki sıralamanın kullandığı renk sayısını gösterir:

```term
$ python graf_boyama.py
Konigsberg dereceleri: [5, 3, 3, 3]
kotu sira: [0, 1, 2, 0, 1, 2] -> 3 renk
iyi sira:  [0, 0, 0, 1, 1, 1] -> 2 renk
```

Kötü sırada önce 0 ve 3 gelir; aralarında kenar olmadığı için ikisi de renk 0 alır. Sonra 1 renk 1 alır, çünkü komşusu olan 3 renk 0'dır. 4 de renk 1 alır, çünkü komşusu 0'dır. 2 düğümünün komşuları 3 (renk 0) ve 4 (renk 1)'tür; bu yüzden renk 2 alır. 5 de komşuları 0 ve 1 nedeniyle renk 2 alır ve üç renk gerekir. İyi sırada ise önce sol kümenin üç düğümü gelir ve hepsi renk 0 alır, çünkü aralarında kenar yoktur. Sağ kümenin düğümleri de renk 1 alır ve iki renk yeter.

**Yazmaç tahsisi.** Derleyici optimizasyonunda değişkenler aynı anda canlı oldukları sürece farklı yazmaçlara konmak zorundadır. Bu, bir **çakışma grafı** kurarak modellenir: iki değişken aynı anda canlıysa aralarında kenar vardır. Yazmaç ataması, bu grafın boyamasıdır; kullanılan renk sayısı gerekli yazmaç sayısıdır. Bu yüzden derleyiciler sezgisel boyama yapar ve yazmaç sayısı yetmezse değişkenleri belleğe taşır (spill). Bölüm 37.8'de yazmaç tahsisinin bu modelini ayrıntılı göreceksin. Burada gördüğün açgözlü boyama, pratikte kullanılan bu sezgisel yöntemin de temelidir.

## 47.10 Karmaşıklık sınıfları: P, NP, NP-tam

Bu bölümdeki birçok problem, bir sorunun çözülebilir olup olmadığından çok, **ne kadar hızlı** çözülebileceğiyle ilgilidir. Bölüm 12'de Big-O ile algoritmanın büyüme hızını ölçtük. Burada, problemlerin kendi zorluğunu sınıflandırıyoruz.

- **P**: girdi boyutu n'de polinomsal sürede (n^k gibi) çözülen karar problemlerinin sınıfı. Euler yolu, bağlantısallık ve en kısa yol gibi birçok graf problemi buradadır.
- **NP**: bir "evet" cevabı polinomsal sürede **doğrulanabilen** problemlerin sınıfı. SAT'ta bir atamanın modeli kolayca kontrol edilir; bu yüzden SAT NP'dedir. Hamilton yolunda da aday bir yolun geçerli olup olmadığı kolayca kontrol edilir.
- **NP-tam**: NP'de olan ve NP'deki her problemin ona **indirgenebildiği** problemler. Bir NP-tam problemi polinomsal sürede çözen bir algoritma, bütün NP problemlerini polinomsal sürede çözer.

**İndirgeme.** A problemi B'ye indirgenir, A'nın her örneğini polinomsal sürede B'nin bir örneğine çevirip cevabı koruyabiliyorsan. O hâlde B'yi hızlı çözebiliyorsan A'yı da hızlı çözersin. Cook (1971), SAT'ın NP-tam olduğunu gösterdi; Karp (1972) bu tekniği kullanarak 21 klasik problemin NP-tam olduğunu gösterdi (genel bilgi). Bunlardan biri **bağımsız küme** problemidir: bir grafta birbirine kenarla bağlı olmayan k düğümden oluşan bir küme var mı? 3-SAT'tan bağımsız kümeye bir indirgeme, her madde için üç düğümlü bir üçgen kurar ve çelişen literalleri kenarla bağlar. Bu inşa, bir formülün sağlanabilir olmasını bir bağımsız kümenin varlığına çevirir (genel bilgi).

Şekil 47.10 bu sınıfların ilişkisini gösterir. P ⊆ NP'dir; çünkü polinomsal sürede çözülebilen bir problemin doğrulaması da polinomsal sürede yapılabilir. NP-tam problemler NP'nin içinde, en zor parçasıdır. NP-zor problemler ise NP'de olmak zorunda değildir; örneğin bazı oyun ve optimizasyon problemleri bu sınıftadır.

![Şekil 47.10: Karmaşıklık sınıflarının kabaca ilişkisi. P, NP'nin içindedir. NP-tam problemler NP'nin en zor kısmıdır. P ≠ NP varsayımında P ile NP-tam ayrıktır.](gorseller/b47_pnp.png)

**P = NP sorusu.** P ile NP'nin aynı olup olmadığı, bilgisayar biliminin en önemli açık sorusudur (genel bilgi). Çoğu uzman P ≠ NP olduğunu düşünür, ama bunun kanıtı yoktur. Pratik sonuç şudur: bir NP-tam problemle karşılaşırsan, en iyi çözümü polinomsal sürede bekleme. Üç yol vardır:

1. **Küçük girdi**: n küçükse üstel algoritma kabul edilebilir (Bölüm 15'teki geri izleme ve N-Queens).
2. **Sezgisel ve yaklaşım**: makul sürede yakın bir çözüm (Bölüm 18'deki açgözlü yaklaşımlar, bu bölümdeki açgözlü boyama).
3. **Özel yapı**: sözde-polinomsal algoritmalar (Bölüm 16.10'daki sırt çantası DP'si) ya da SAT ve tamsayılı programlama çözücüleri.

Savunma sanayiinde görev planlama, rota optimizasyonu ve kaynak atama çoğu zaman NP-zordur. Bu yüzden gerçek sistemler ya sezgisel yöntemlerle, ya da SAT ve kısıt çözücülerle, gerektiğinde zaman sınırı koyarak çalışır. Problemin NP-zor olduğunu fark etmek, boşuna mükemmel çözüm aramayı durdurmanın ilk adımıdır.

::: ipucu
Bir problemle karşılaştığında önce "bu NP-tam mı?" diye sorma alışkanlığı kazan. Cevap evetse, mükemmel bir çözüm yerine hangi kısıtlarla yetinebileceğini tartış. Mülakatta bu soruyu sormak, problemi çözmek kadar değerlidir.
:::

## Çözümlü Örnekler

Dört örnek ★'dan ★★★'e doğru zorlaşır. Her birinde Bölüm 5'teki altı adımı izliyoruz: anla, örnekle, kaba çöz, örüntü, iyileştir, doğrula. Altıncı adımda elle izlediğin tabloyu programın çıktısıyla karşılaştırıyorsun. Tablo tutmuyorsa düşüncende ya da tablonda bir hata vardır; hangisi olduğunu bulmak, öğrenmenin asıl kısmıdır.

### Örnek 1 (★): 1 + 2 + ... + n için kapalı formül

**Problem.** S(n) = 1 + 2 + ... + n toplamı için kapalı bir formül bul, tümevarımla kanıtla ve Python ile doğrula.

**Adım 1 — Anla.** S(n), ilk n doğal sayının toplamıdır. Kapalı formül, n'nin bir fonksiyonu olarak S(n)'yi tek bir ifadeyle verir. Kanıt için iki şey gerekir: taban (n = 1) ve adım (S(k)'den S(k+1)'e geçiş).

**Adım 2 — Örnekle.** S(1) = 1, S(2) = 3, S(3) = 6, S(4) = 10, S(5) = 15. Bu sayılar, dizinin "üçgensel sayılar" olduğunu düşündürür: 1, 3, 6, 10 bir üçgenin sıralarındaki nokta sayısıdır.

**Adım 3 — Kaba çöz.** Bir döngüyle 1'den n'ye kadar toplar ve sonucu yazarsın. Bu çözüm doğrudur ama n adım atar; n = 10^9 için bu bir milyar tur demektir.

**Adım 4 — Örüntü.** Gauss'un eşleştirme fikri: 1 ile n'yi, 2 ile n−1'i topla. Her çift n + 1 eder ve n/2 çift vardır. Sonuç n(n + 1)/2'dir. Tümevarımla aynısını kanıtlarsın: S(k+1) = S(k) + (k+1) = k(k+1)/2 + (k+1) = (k+1)(k+2)/2. Bu, P(k+1)'in iddiasıdır ve taban ile birlikte kanıt tamamlanır (47.3).

**Adım 5 — İyileştir.** Formül n(n+1)/2 tek bir çarpma ve bir bölme ile hesaplanır. Python'da tam sayılar sınırsız olduğu için taşma olmaz. C'de ise n(n + 1) çarpımı n = 10^5 için 10^10'u aşar ve 32 bitlik işaretsiz tamsayıda taşar. Bu yüzden C'de `unsigned long long` kullanılmalıdır ve bölme çarpımdan sonra yapılmalıdır. Aşağıdaki program, döngü ile formülü her n ≤ 1000 için karşılaştırır.

```python
# -*- coding: utf-8 -*-
# ornek1.py - 1+2+...+n formulunun tumevarimla denetimi.


def toplam(n):
    s = 0
    for i in range(1, n + 1):
        s += i
    return s


def formul(n):
    return n * (n + 1) // 2


if __name__ == "__main__":
    print("n  toplam  formul")
    for n in range(1, 6):
        print(n, toplam(n), formul(n))
    print("taban (n=1):", formul(1) == 1)
    adim = all(formul(k + 1) - formul(k) == k + 1
               for k in range(1000))
    print("adim (k<1000):", adim)
    print("n<=1000 icin toplam == formul:",
          all(toplam(n) == formul(n) for n in range(1, 1001)))
```

**Adım 6 — Doğrula.** Elle iz: S(3) = 6 bilindiğine göre S(4) = 6 + 4 = 10'dur ve formül 4·5/2 = 10 verir. Tablonun tamamı şöyle:

| n | S(n−1) | + n | S(n) | n(n+1)/2 |
|---|---|---|---|---|
| 1 | 0 | 1 | 1 | 1 |
| 2 | 1 | 2 | 3 | 3 |
| 3 | 3 | 3 | 6 | 6 |
| 4 | 6 | 4 | 10 | 10 |

Programın çıktısı tabloyla ve tümevarım adımıyla birebir uyuşur:

```term
$ python ornek1.py
n  toplam  formul
1 1 1
2 3 3
3 6 6
4 10 10
5 15 15
taban (n=1): True
adim (k<1000): True
n<=1000 icin toplam == formul: True
```

**Bunu AI'sız yazabilir misin?** 1 + 3 + 5 + ... + (2n − 1) = n^2 eşitliğini tümevarımla kanıtla. Adım kısmında hangi cebirsel özdeşliği kullandığını yaz ve bu özdeşliği Python'da bir kez de sayısal olarak denetle.

### Örnek 2 (★★): 17'nin 3120'ye göre tersi: genişletilmiş Öklid izi

**Problem.** 17 · x ≡ 1 (mod 3120) denklemini çöz. Cevabı genişletilmiş Öklid ile bul, her adımın q, r, s, t değerlerini tabloya yaz ve sonucu doğrula. Bu sayılar, 47.8'deki RSA örneğinin φ(n) = 3120 ve e = 17 değerleridir; çözüm d = 2753'tür.

**Adım 1 — Anla.** x'in var olması için gcd(17, 3120) = 1 olmalıdır. 3120 = 2^4·3·5·13 ve 17 asal olduğundan bu koşul sağlanır. x'i bulmak için 17·s + 3120·t = 1 denklemini sağlayan s ve t'yi bulmak yeterlidir; sonra x = s mod 3120.

**Adım 2 — Örnekle.** Küçük bir örnek: 3·x ≡ 1 (mod 7). Denemeyle x = 5 bulunur, çünkü 3·5 = 15 = 2·7 + 1. Bu, genel yöntemin sonucunu kontrol etmek için kullanacağımız tanıktır.

**Adım 3 — Kaba çöz.** x = 1, 2, ..., 3119 diye dene. En fazla 3119 adım gerekir; her biri 17x mod 3120 hesaplar. Doğru bir yöntemdir ama m büyüdükçe kullanılamaz hâle gelir.

**Adım 4 — Örüntü.** Öklid algoritması m ve a'nın kalanlarını üretir. Her kalan r, bir s ve bir t için r = s·a + t·m biçiminde yazılabilir: başlangıçta m = 0·a + 1·m ve a = 1·a + 0·m. Her Öklid adımında yeni kalan, önceki iki satırın q katlı farkıdır, dolayısıyla s ve t de aynı farkla güncellenir. Son sıfır olmayan kalan 1 olduğunda, onun s değeri tersi verir.

**Adım 5 — İyileştir.** Üç sütunu (r, s, t) tek bir döngüde tutarız. Aşağıdaki fonksiyon her satırı yazdırır ve sonunda tersi döndürür.

```python
# -*- coding: utf-8 -*-
# ornek2.py - genisletilmis Oklid ile modüler ters izi.


def ters_iz(a, m):
    """Doner: (gcd, a'nin m'ye gore tersi).
    Her satir: r = s*a + t*m olacak bicimde tutulur."""
    satirlar = [(m, 0, 1), (a % m, 1, 0)]
    print("  q       r       s       t")
    while satirlar[-1][0] != 0:
        (r0, s0, t0), (r1, s1, t1) = satirlar[-2], satirlar[-1]
        q = r0 // r1
        yeni = (r0 - q * r1, s0 - q * s1, t0 - q * t1)
        satirlar.append(yeni)
        print("%3d %7d %7d %7d" % (q, yeni[0], yeni[1], yeni[2]))
    g, s, _ = satirlar[-2]
    return g, s % m


if __name__ == "__main__":
    g, ters = ters_iz(17, 3120)
    print("gcd =", g, "  ters =", ters)
    print("17 * ters mod 3120 =", 17 * ters % 3120)
    print("pow(17, -1, 3120) =", pow(17, -1, 3120))
```

**Adım 6 — Doğrula.** Tabloda başlangıç satırlarını (r0 = 3120, r1 = 17) da ekledim; program bunları yazdırmaz, ilk yazdırdığı satır r2'dir.

| Satır | q | r | s | t |
|---|---|---|---|---|
| r0 = m | | 3120 | 0 | 1 |
| r1 = a | | 17 | 1 | 0 |
| 2 | 183 | 9 | −183 | 1 |
| 3 | 1 | 8 | 184 | −1 |
| 4 | 1 | 1 | −367 | 2 |
| 5 | 8 | 0 | 3120 | −17 |

Son sıfır olmayan kalan 1'dir ve onun s katsayısı −367'dir. Tersi bulmak için −367'yi 3120'ye göre düzeltiriz: −367 + 3120 = 2753. Denetim: 17 · 2753 = 46801 = 15 · 3120 + 1. Programın çıktısı da aynıdır:

```term
$ python ornek2.py
  q       r       s       t
183       9    -183       1
  1       8     184      -1
  1       1    -367       2
  8       0    3120     -17
gcd = 1   ters = 2753
17 * ters mod 3120 = 1
pow(17, -1, 3120) = 2753
```

**Bunu AI'sız yazabilir misin?** 7 · x ≡ 1 (mod 26) denklemini genişletilmiş Öklid ile çöz. Her adımın tablosunu yaz, sonra cevabı 7 ile çarpıp 26'ya göre kalanını alarak doğrula. Bu denklemin bir çözümü olmadığını gösteren bir a değeri (26 ile aralarında asal olmayan) bul ve nedenini bir cümleyle açıkla.

### Örnek 3 (★★): 1 ile 1000 arasında 2, 3 veya 5'e bölünebilen sayılar

**Problem.** 1'den 1000'e kadar olan tam sayılardan kaçı 2, 3 ya da 5'e bölünür? Kaba kuvvetle değil, içerme-dışlama ile çöz ve sonucu programla doğrula.

**Adım 1 — Anla.** Üç küme var: A (2'ye bölünenler), B (3'e bölünenler) ve C (5'e bölünenler). Birleşimin eleman sayısı istenen cevaptır. Bir sayı birden fazla kümeye ait olabileceği için basit toplama yanlış sonuç verir.

**Adım 2 — Örnekle.** 1'den 30'a kadar olan sayılar: 2'ye bölünen 15, 3'e bölünen 10, 5'e bölünen 6 tanedir. Toplarsak 31 buluruz; ama 30 sayı vardır. Fazlalık, kesişimlerden gelir: 6, 12, 18, 24, 30 hem 2 hem 3'e, 10 ve 20 hem 2 hem 5'e, 15 hem 3 hem 5'e bölünür. Bu fazlalığı çıkarmadan sonuç yanlış olur.

**Adım 3 — Kaba çöz.** 1'den 1000'e kadar her sayıyı tek tek kontrol et ve üçünden birine bölünenleri say. Bu 1000 adımdır ve doğrudur.

**Adım 4 — Örüntü.** Genel formül: |A ∪ B ∪ C| = |A| + |B| + |C| − |A ∩ B| − |A ∩ C| − |B ∩ C| + |A ∩ B ∩ C|. Kesişimler, bölenlerin en küçük ortak katına (2 ve 3 için 6, 2 ve 5 için 10, 3 ve 5 için 15, üçü için 30) göre hesaplanır. Bir n sayısının m'ye bölünen sayısı ⌊n/m⌋'dir.

**Adım 5 — İyileştir.** ⌊N/d⌋ hesapları ile yedi terimi bir ifadede topluyoruz; hiçbir liste tutmamız gerekmez.

```python
# -*- coding: utf-8 -*-
# ornek3.py - 1..1000 icinde 2, 3 veya 5'e bolunenler.
N = 1000

if __name__ == "__main__":
    print("tekli :", N // 2, N // 3, N // 5)
    print("ikili :", N // 6, N // 10, N // 15)
    print("uclu  :", N // 30)
    formul = N // 2 + N // 3 + N // 5 - N // 6 - N // 10 - N // 15 \
        + N // 30
    print("formul:", formul)
    kaba = sum(1 for x in range(1, N + 1)
               if x % 2 == 0 or x % 3 == 0 or x % 5 == 0)
    print("kaba  :", kaba)
    print("hicbirine bolunmeyen:", N - kaba)
```

**Adım 6 — Doğrula.** Elle tablo (N = 1000):

| Terim | Hesap | Değer | İşaret |
|---|---|---|---|
| ⌊N/2⌋ | 1000 / 2 | 500 | + |
| ⌊N/3⌋ | 1000 / 3 | 333 | + |
| ⌊N/5⌋ | 1000 / 5 | 200 | + |
| ⌊N/6⌋ | 1000 / 6 | 166 | − |
| ⌊N/10⌋ | 1000 / 10 | 100 | − |
| ⌊N/15⌋ | 1000 / 15 | 66 | − |
| ⌊N/30⌋ | 1000 / 30 | 33 | + |
| Toplam | | 734 | |

Toplam 500 + 333 + 200 − 166 − 100 − 66 + 33 = 734'tür. Dış bölge, yani üçüne de bölünmeyen sayılar, 1000 − 734 = 266'dır; bu, Şekil 47.4'teki dış bölgenin değeridir. Programın çıktısı aynı sonucu verir:

```term
$ python ornek3.py
tekli : 500 333 200
ikili : 166 100 66
uclu  : 33
formul: 734
kaba  : 734
hicbirine bolunmeyen: 266
```

**Bunu AI'sız yazabilir misin?** 1'den 1000'e kadar olan sayılardan 2, 3 veya 7'ye bölünmeyenlerin sayısını içerme-dışlama ile bul. Önce üç kümeyi, sonra ikili ve üçlü kesişimleri yaz; sonucu kaba kuvvetle doğrula. Dikkat et: 6 ve 14 gibi kesişim sayılarını 2 ile 7'nin ortak katından hesaplamalısın.

### Örnek 4 (★★★): Küçük bir RSA anahtarıyla şifreleme, çözme ve kanıt

**Problem.** p = 61, q = 53 olan RSA anahtarıyla m = 65 mesajını şifrele (e = 17), çözülmüş hâlini doğrula ve bu işlemin neden çalıştığını kanıtla. Üssü kâğıtta izleyebilmek için kare-çarpma yöntemini kullan.

**Adım 1 — Anla.** p ve q'dan n = 3233 ve φ(n) = 3120 elde edilir; e = 17 verilmiştir. Şifreleme c = 65^17 mod n, çözme m = c^d mod n'dir; d = 2753. İki işlemin de bir üssü vardır. Hesap, 65^17 sayısını tamamen yazmadan yapılmalıdır.

**Adım 2 — Örnekle.** Uç durumlar: m = 0 ve m = 1 için c = m olur ve çözme de m'yi verir. Bu, şifrenin uç değerlerde bile bozulmadığını gösteren hızlı bir denetimdir. Ayrıca gcd(65, 3233) = 1 olduğundan Euler teoremi doğrudan uygulanabilir.

**Adım 3 — Kaba çöz.** 65'i 16 kez 65 ile çarparsın ve her adımda 3233'e göre kalanı alırsın. Bu 16 çarpma verir; doğru ama anlaşılması zor bir yoldur.

**Adım 4 — Örüntü.** 17 ikili yazılınca 10001_2'dir. Bu, 17 = 1 + 16 demektir ve 65^17 = 65^1 · 65^16. Gerekli tabanlar 65, 65^2, 65^4, 65^8, 65^16'dır ve her biri bir öncekinin karesidir. Yani dört karesel yükseltme ve iki çarpma yeter. Bu, üssün ikili gösteriminin çarpanlarına ayrılmasıdır.

**Adım 5 — İyileştir.** Aşağıdaki fonksiyon bitleri en düşükten yüksek bitlere doğru tarar; her bit için tabanı karesini alır, bit 1 ise sonucu tabanla çarpar. İz yazdırma özelliği açıktır.

```python
# -*- coding: utf-8 -*-
# ornek4.py - kucuk RSA: kare-carpma izi ve neden calistigi.


def ikili_us(a, e, m, izle=True):
    """a^e mod m; e'nin bitlerini en dusukten basa tarar."""
    sonuc, taban = 1, a % m
    if izle:
        print("bit  taban  sonuc")
    while e > 0:
        bit = e & 1
        if bit:
            sonuc = sonuc * taban % m
        taban = taban * taban % m
        if izle:
            print("%3d %6d %6d" % (bit, taban, sonuc))
        e >>= 1
    return sonuc


if __name__ == "__main__":
    p, q = 61, 53
    n, f = p * q, (p - 1) * (q - 1)
    e = 17
    d = 2753
    c = ikili_us(65, e, n)
    print("sifreli c =", c, " pow kontrol:", pow(65, e, n))
    print("e*d =", e * d, " e*d - 1 =", e * d - 1,
          " = 15 * phi?", (e * d - 1) == 15 * f)
    m = ikili_us(c, d, n, izle=False)
    print("cozulmus m =", m)
```

**Adım 6 — Doğrula.** İz tablosu (her satır bir biti işler; "taban", o turda karesi alınmış değer):

| bit | taban | sonuç |
|---|---|---|
| 1 | 992 | 65 |
| 0 | 1232 | 65 |
| 0 | 1547 | 65 |
| 0 | 789 | 65 |
| 1 | 1785 | 2790 |

Son satırda bit 1 olduğu için sonuç, o turdan önceki tabana yani 789 = 65^16 mod 3233 değerine çarpılır: 65 · 789 = 51285 ve 51285 − 15 · 3233 = 2790. Çözme için e·d − 1 = 46800 = 15 · 3120 olduğunu da kontrol etmiş olmalısın; bu, neden çalıştığının kalbidir. Programın çıktısı tablo ve kanıtla uyumludur:

```term
$ python ornek4.py
bit  taban  sonuc
  1    992     65
  0   1232     65
  0   1547     65
  0    789     65
  1   1785   2790
sifreli c = 2790  pow kontrol: 2790
e*d = 46801  e*d - 1 = 46800  = 15 * phi? True
cozulmus m = 65
```

**Kanıt.** ed = 1 + 15·φ(n) olduğu için c^d = m^(ed) = m · (m^φ(n))^15. Asal p = 61 için, m ≡ 0 (mod p) ise iki taraf da 0'dır; değilse Fermat m^60 ≡ 1 (mod 61) verir ve m^(ed) ≡ m (mod 61). Aynı argüman q = 53 için geçerlidir. p ve q aralarında asal olduğundan CRT, m^(ed) ≡ m (mod 3233) sonucunu verir. Bu, her m için şifrelemenin doğru çözüldüğünü kanıtlar.

**Bunu AI'sız yazabilir misin?** p = 11, q = 13 için n, φ(n), e = 7 ve d'yi bul (d = 103 değerini kontrol et). Sonra m = 9 mesajını kâğıtta şifrele ve çöz. Hangi adımda ara değerlerin 143'ten küçük kalmasını beklediğini ve neden bu anahtarın gerçek bir sistemde kullanılamayacağını yaz.

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ araçları **yasak**. Amaç çalışan bir kütüphane üretmekten çok, sayılar teorisinin ve SAT'ın nasıl çalıştığını kendi elinle yaşamak. Kâğıda çiz, küçük testler yaz, hataları ölç; çözümü dışarıdan alma.
:::

### Proje 1 (★★): Sayılar teorisi kütüphanesi

**Amaç:** 47.7'deki `sayilar.py` modülünü genişlet ve test et. Eklemen gerekenler: Pollard rho ile çarpanlara ayırma, yinelemeli (iteratif) bir genişletilmiş Öklid, `sayilar.py`'deki Miller–Rabin için birim testleri ve her fonksiyonun büyüme ölçümü.

**Yapılacak / Beklenen davranış:** `faktorle(n)` fonksiyonu, n'nin asal çarpanlarının sıralı listesini döndürmeli (ör. 8051 için [83, 97]). `ext_gcd` özyinelemesiz de çalışmalı ve her girdi için a·x + b·y = gcd(a, b) sağlanmalı. Miller–Rabin, 10^5'e kadar tüm sayılarda eleme sonucuyla aynı olmalı. Pollard rho, 10^12 civarındaki bir bileşik için birkaç saniyede bitmeli; süreyi ve denenen adım sayısını ölç.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Pollard rho'da f(x) = (x² + c) mod n rastgele dizisini kullan; Floyd'un döngü bulma yöntemiyle iki işaretçinin (yavaş ve hızlı) aynı değeri ne zaman verdiğini izle. Bulunan farkın gcd'si n'nin bir bölenidir. Testlerde n'nin asal kuvvetlerini (ör. 9, 25) ve iki asal çarpımını ayrı ayrı dene. Ölçümde adım sayılarını ve yapılan modüler çarpımları say; zaman ölçümünü makineye bağlı olduğu için yalnızca büyüklük sırası olarak yorumla.

**Başarı kriterleri:**
- `faktorle` 1000'e kadar tüm sayılar için doğru sonuç verir (kaba kuvvetle karşılaştırılmış).
- Miller–Rabin, 10^5'e kadar tüm sayılarda eleme ile aynı sonucu verir.
- Her fonksiyon için en az on birim testi var ve hepsi geçiyor.
- Pollard rho'nun 10^12 civarındaki bileşiklerdeki adım sayısı, deneme bölmesinin √n adımıyla karşılaştırılmış ve bir tablo halinde rapor edilmiş.

### Proje 2 (★★★): Küçük bir SAT çözücü ve Sudoku'nun SAT'a indirgenmesi

**Amaç:** 47.2'deki DPLL çekirdeğini genişlet: saf literal kuralını ekle ve dal seçimini "en sık geçen değişken" sezgisiyle yap. Ardından 9×9 bir Sudoku'yu SAT problemine indirgeyip çöz. Sonuçları Bölüm 15.9'daki geri izleme çözücüsüyle düğüm sayısı açısından karşılaştır.

**Yapılacak / Beklenen davranış:** Çözücü, bir CNF formülü için ya bir model ya da "sağlanamaz" yanıtı vermeli. Sudoku indirgemesi, her hücre-rakam çifti için bir değişken kullanmalı (729 değişken) ve kurallar (her hücrede bir rakam, her satır, sütun ve kutuda her rakam bir kez) madde olarak yazılmalı. Çözülen Sudoku'nun kuralları ihlal etmediği bağımsız bir denetimle kontrol edilmeli.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Her hücre (r, c) ve rakam d için 81 çarpanlı bir tamsayı kodu tanımla, örneğin 81·(r−1) + 9·(c−1) + d. "Her hücrede en az bir rakam" maddesi 9 literalli bir madde, "en çok bir rakam" maddesi ise her rakam çifti için ikili bir ¬x ∨ ¬y maddesidir. Satır, sütun ve kutu kuralları aynı mantıkla yazılır. Sudoku'nun ilk ipuçlarını birim maddeler olarak ekle; böylece birim yayılım devreye girer.

**Başarı kriterleri:**
- Çözücü, 47.2'deki 300 rastgele formülde kaba kuvvetle aynı kararı verir.
- En az üç farklı Sudoku (kolay, orta, zor) doğru çözülür ve her çözüm bağımsız denetimden geçer.
- Her Sudoku için DPLL'in düğüm sayısı ile Bölüm 15.9'daki geri izleme çözücüsünün düğüm sayısı bir tabloda karşılaştırılır.
- Rapor, hangi kuralın (saf literal, birim yayılım, dal sezgisi) düğüm sayısını ne kadar değiştirdiğini ölçülerle açıklar.

### Ek Alıştırmalar

Aşağıdaki problemlerin çözümü bu kitapta yok. Önce kâğıda, sonra editöre geç. Mülakat olarak işaretlenenler klasik sorulardır.

1. **★ — Tautoloji sayımı.** Üç değişkenli bir formülü doğruluk tablosuyla denetlerken kaç satır yazarsın? On değişken için bu sayı ne olur? Bu büyümeyi DPLL'in birim yayılımıyla karşılaştır.
2. **★ — De Morgan'ı genişlet.** ¬(a ∧ b ∧ c) formülünü yalnızca ¬, ∨ ve gerekirse ∧ kullanarak eşdeğer bir biçime çevir. Tabloyla doğrula.
3. **★★ — Kuş iddiası (Mülakat).** "Her kuş uçar" iddiası, "bu kuş uçmuyor" diye çürütülebilir mi? Niceleyicilerle iddianın olumsuzlamasını yaz ve bir penguenin neyi gösterdiğini açıkla.
4. **★★ — √3 irrasyonel.** √3'ün irrasyonel olduğunu çelişki yöntemiyle kanıtla. Aynı adımların neden √4 için işlemediğini açıkla.
5. **★★ — Tek sayıların toplamı.** 1 + 3 + 5 + ... + (2n − 1) = n^2 formülünü tümevarımla kanıtla ve Python ile n ≤ 500 için doğrula.
6. **★★ — Eşit el sıkışma (Mülakat).** n ≥ 2 kişilik bir partide en az iki kişi eşit sayıda el sıkışmıştır. Bu iddiayı güvercin yuvası ilkesiyle kanıtla.
7. **★★ — Pascal'ı hesapla.** C(20, 10)'u Pascal yinelemesiyle hesapla, sonucu math.comb ile karşılaştır. Yinelemenin kaç toplama gerektirdiğini sayarak bu hesabın karmaşıklığını yaz.
8. **★★★ — Bozuk permütasyon bağıntısı.** D_n = (n − 1)(D_(n−1) + D_(n−2)) bağıntısını içerme-dışlama kullanmadan, doğrudan kombinatorik bir argümanla kanıtla. Ardından bu bağıntıyla D_10'u hesapla ve 47.5'teki formülle karşılaştır.
9. **★★ — Fibonacci'yi matris üssüyle.** F_n'yi 2×2 matris üssüyle O(log n) adımda hesapla (Bölüm 19.4'e bak). F_(10^18) mod (10^9 + 7) değerini bul ve yöntemini açıkla.
10. **★★ — gcd ve lcm (Mülakat).** gcd(a, b) · lcm(a, b) = a · b özdeşliğini kanıtla. Bu özdeşlik, lcm'yi bulmanın hangi pratik yolunu verir?
11. **★ — Ters ne zaman yok?** m = 12 için 5'in tersini bul. 4'ün tersinin neden olmadığını gcd kavramıyla açıkla ve Python'da `pow(4, -1, 12)` çağrısının ne verdiğini gözle.
12. **★★★ — İki parçalılık testi (Mülakat).** Bir grafın iki parçalı olup olmadığını döngü uzunluklarını tek tek aramadan nasıl test edersin? Algoritmanı yaz, zaman karmaşıklığını söyle ve neden tek bir BFS'in yeterli olduğunu kanıtla.

## Kod Okuma Egzersizi

Aşağıdaki kesit CPython 3.12.10'un `Lib/fractions.py` dosyasından alınmıştır. Dosya, raw.githubusercontent.com/python/cpython/v3.12.10/Lib/fractions.py adresinden etiket üzerinden indirildi; yerel Python kurulumundaki kopyayla satır sonları dışında aynıdır. Kesit, dosyanın 280–289. satırlarıdır ve hiçbir satır değiştirilmedi; girintiler de kaynaktaki gibi bırakıldı (kesit, `__new__` metodunun içinden alınmıştır). Bu kod, `Fraction(pay, payda)` yapıcısının sadeleştirmesini yapar: ortak böleni bulur, paydayı pozitif yapar ve ikisini böler.

```python
        if denominator == 0:
            raise ZeroDivisionError('Fraction(%s, 0)' % numerator)
        g = math.gcd(numerator, denominator)
        if denominator < 0:
            g = -g
        numerator //= g
        denominator //= g
        self._numerator = numerator
        self._denominator = denominator
        return self
```

Bu kesit, Öklid'in yaşayan bir kullanımıdır. Okuma sırasında şu soruların her birini kâğıtta cevapla.

**Sorular — cevaplamadan geçme:**

1. `math.gcd` hangi algoritmayı kullanıyor olabilir? Bu bölümdeki Öklid adım sayısı ile bir kaynak koddaki gerçek uygulamayı nasıl karşılaştırırsın? Kesitten bu algoritmanın adını çıkaramazsın; bunu belgelerden doğrula.
2. `if denominator < 0: g = -g` satırı neden var? `Fraction(10, -8)` için satır satır izle ve sonucun `-5/4` olmasını sağla.
3. `numerator //= g` tam bölme ile yapılıyor. g'nin numerator'ı tam böldüğünü neden garanti edebiliriz? `Fraction(0, -5)` için g nedir ve sonuç neden `0/1`'dir?
4. `denominator == 0` denetimi, gcd hesabından önce yapılıyor. Bu sıra değişseydi, payda sıfır olduğunda hangi davranış ortaya çıkardı? Bu denetimin yokluğunda `Fraction(5, 0)` ne üretirdi, bir mantık hatasını öncesinde yakalamanın önemi nedir?
5. Bu kodda `math.gcd` yerine kendi `ext_gcd` fonksiyonumuzu kullansaydın hangi davranış değişirdi? `ext_gcd` negatif girdilerde negatif bir g döndürebilir; bu, `if denominator < 0` satırıyla nasıl etkileşir?
6. Bu sadeleştirme her `Fraction` oluşturulduğunda yapılıyor. Toplama ve çarpma sonuçlarında da bu adım gerekir mi? Çarpımda `a/b · c/d` için sadeleştirmeyi önce yapmanın (çapraz sadeleştirme) avantajı nedir?

## Bölüm Özeti

- **Mantık** önermeler ve bağlaçlarla kurulur; doğruluk tabloları eşdeğerliği kanıtlar (De Morgan). Mantıkta ∨ kapsayıcıdır ve → yalnızca p doğru, q yanlış iken yanlıştır.
- **Karnaugh haritası** komşu minterm'leri gruplayarak mantık ifadesini sadeleştirir; bizim örneğimizde üç terim en az sayıdır.
- **SAT** bir formülün sağlanabilirliğini sorar; **DPLL**, birim yayılım ve geri izlemeyle kaba kuvvetten çok daha hızlıdır, ama en kötü durumda hâlâ üstel olabilir.
- **İspat teknikleri**: doğrudan, karşıt-ters, çelişki (√2 ve sonsuz asal), tümevarım (zayıf, güçlü, yapısal) ve döngü değişmezi. Test bir kanıtın yerini tutmaz.
- **Bağıntılar ve sıralar**: denklik sınıfları kümeyi böler, kısmi sıralar Hasse diyagramıyla gösterilir ve topolojik sıralama bağımlılıkları çözer. Güvercin yuvası ve köşegenleştirme, hash ve hesaplanabilirlik sınırlarının temelidir.
- **Sayma**: permütasyon, kombinasyon, içerme-dışlama, bozuk permütasyon (1/e'ye yakınsar) ve Catalan sayıları birçok yapının ortak dilidir.
- **Özyinelemeli bağıntılar** karakteristik denklemle kapalı biçime indirgenir; kayan nokta Binet formülü n = 71'de yanlış sonuç verir.
- **Sayılar teorisi**: Öklid, genişletilmiş Öklid, modüler ters, CRT, Euler φ ve Miller–Rabin. **RSA**, Euler teoreminin ve CRT'nin doğrudan uygulamasıdır; kitap RSA'yı kendi başına gerçek sistemlerde uygulama.
- **Graf teorisi**: el sıkışma lemması, Euler ve Hamilton yolları arasındaki fark, ağaçların n − 1 kenarı, düzlemsellik ve Euler formülü, boyama ve açgözlü boyamanın sıraya bağlılığı.
- **Karmaşıklık**: P, NP ve NP-tam; indirgeme ile sert problemlerin birbirine bağlanması. P = NP açık sorusu ve NP-zor problemlerde pratik yaklaşımlar.

**Sonraki bölümde:** Bölüm 48 (Lineer Cebir) bu bölümdeki sayısal yapıyı sürekli bir zemine taşıyor. Bölüm 11'de graf komşuluk matrislerini gördün; bu bölümde modüler aritmetiği kurduk. Bir sonraki kısımda vektörler, matrisler ve matris çarpımının geometrisini, özdeğer ve özvektörleri, SVD'yi ve normları işleyeceğiz. Bu kavramlar, Bölüm 55'te otomatik türevin, Bölüm 63'te sinir ağlarının ve Bölüm 61'de PCA'nın temelidir. Ayrık yapıdan sürekli yapıya geçişin matematiği, Bölüm 49'da olasılık ve istatistikle devam ediyor.

::: mulakat
Aşağıdaki sorular cevapsızdır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. "Veya" bağlacının mantıkta kapsayıcı olması, bir erişim kuralında hangi hataya yol açabilir? Bunu bir koşul ifadesiyle göster ve düzeltmeyi yaz.
2. DPLL'in birim yayılımı, bir Sudoku çözücüsünde hangi ipuçlarıyla başlar ve bu, geri izlemeyle karşılaştırıldığında neden daha hızlı olabilir?
3. Bir tümevarım kanıtında adımı sağlamadan taban ile yetinen bir öğrenci hangi hatayı yapar? Hatalı "bütün atlar aynı renk" kanıtını örnek vererek anlat.
4. Hash tablosunda çakışmanın yaklaşık √(πM/2) adımda olması, bir sistem tasarımında kovaları ne kadar büyük seçmen gerektiğini nasıl etkiler?
5. Bir ağda iki düğüm arasındaki en kısa yolu, her kenarın bir kez geçilmesini zorunlu kılan bir yolla karıştırırsan hangi problemi çözmüş olursun? Euler ve Hamilton arasındaki zorluk farkını açıkla.
6. RSA'da neden e = 65537 gibi bir değer seçilir ve neden d'yi bulmak için φ(n)'in bilinmesi gerekir? Bir saldırganın n'yi çarpanlarına ayırabilmesi, bu iki noktadan hangisini hedefler?
7. Bir problemin NP-tam olduğunu fark ettiğinde mühendis olarak hangi üç yolu değerlendirirsin? Savunma sanayiinde bir görev planlama problemi için hangisini seçerdin ve neden?
:::
