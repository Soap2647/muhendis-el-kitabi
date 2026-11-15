%% kisim_no: IX
%% kisim_ad: Otomata & Derleme
%% kisim_ayrac: evet
%% bolum_no: 36
%% baslik: Formal Diller

## Giriş: Makine bir dili nasıl okur?

Bir e-posta adresinin biçimi doğru mu? Bir protokol paketi beklenen düzende mi? Bir kaynak dosyada `if x = 3:` yazdığında derleyici neden "bu bir atama, karşılaştırma değil" diye itiraz eder? Üçü de aynı soruya iner: verilen bir metin, tanımlı bir **dilin** üyesi mi? İnsan bu soruyu gözle yanıtlar; bir makinenin yanıtlaması için dili kesin, eksiksiz bir biçimde tanımlamak gerekir. Bu bölüm o tanımın matematiğini ve onu tanıyan makinelerin nasıl çalıştığını anlatır.

Konu, bilgisayar biliminin en eski ve en düzgün kısımlarından biridir. 1950'lerde Chomsky, dilleri üretim kurallarına göre sınıflandırdı; aynı dönemde Kleene düzenli ifadeleri, Rabin ve Scott sonlu otomatları inceledi. Bu sınıflar bugün her derleyicinin, her düzenli ifade motorunun ve her protokol ayrıştırıcısının altındaki iskelettir. Mülakatta "düzenli ifade ile DFA arasındaki fark nedir?", "neden bazı diller hiçbir regex ile tanımlanamaz?" ya da "bir regex neden işlemcinin bir süre kilitlenmesine yol açabilir?" soruları sık çıkar; bu bölümde üçüne de cevap vereceksin.

Savunma sanayiinde bu bilgi doğrudan kullanılır. Bir İHA yer istasyonunun aldığı telemetri çerçevesi, bir komut dili ya da bir yapılandırma dosyası, sistem tarafından **kabul edilmeden önce** doğrulanmalıdır. Doğrulama gevşekse bozuk ya da kötü niyetli bir girdi, kontrol yazılımının beklemediği bir duruma girebilir. Bölüm 31'de gördüğümüz çerçeve okuyucusu aslında bir durum makinesiydi; bu bölümde o makinenin soyut karşılığını ve sınırlarını göreceksin.

Bölüm dört büyük adımda ilerler. Önce alfabe, dizge ve dil gibi temel kavramları ve dil üzerindeki işlemleri kuruyoruz. Sonra en basit tanıyıcı olan sonlu otomatı (DFA ve NFA) ele alıp iki otomatın eşdeğerliğini ve minimal biçimini inceliyoruz. Üçüncü adımda düzenli ifadeleri, onları otomata çeviren Thompson yapısını ve Python'un `re` modülünün neden bazen üstel süre harcadığını görüyoruz. Dördüncü adımda bağlamdan bağımsız gramerlere, yığınlı otomata, CYK algoritmasına ve Chomsky hiyerarşisine, son olarak Turing makinesine geçiyoruz. Bölümün sonunda bu teoriyi Mert'in kendi yazdığı Doruk dilinin sözcüksel analizcisine (lexer) uyguluyoruz.

::: not
Bu bölümde kod bolca var ve hepsi çalıştırılabilir. Her programın çıktısını kendi makinende yeniden üret; sayıları ezberlemek yerine ölçmeyi öğren. Zaman ölçümleri 3.12.10 sürümlü Python ile tek bir Windows makinesinde alınmıştır; mutlak değerlerden çok büyüklük sırasına bak, çünkü makineye göre değişirler.
:::

## 36.1 Alfabe, dizge ve dil

Her şeyin başı üç kelime: **alfabe**, **dizge** ve **dil**. Alfabe (alphabet), sonlu ve boş olmayan bir sembol kümesidir; genellikle Σ ile gösterilir. Σ = {0, 1} ikili alfabedir, Σ = {a, b, c} üç harflik bir alfabedir. Bir Doruk kaynak dosyası için alfabe ASCII karakterler ve UTF-8 çok baytlı dizileri içeren büyük bir kümedir; ama sonlu olduğu sürece teorinin geri kalanı işler.

Dizge (string), alfabenin sembollerinin sonlu bir dizisidir. `0110` bir dizgedir, `ab` de öyle. Dizgenin uzunluğunu |w| ile gösteririz; |0110| = 4. Hiç sembol içermeyen dizgeye boş dizge denir ve ε (epsilon) ile yazılır; |ε| = 0. Bir alfabenin üzerindeki tüm dizgelerin kümesi `Σ*` ile gösterilir; `Σ*` sonsuzdur ama sayılabilirdir, yani her dizgeyi uzunluğa ve sözlük sırasına göre tek tek sıralayabilirsin. `Σ+` ise ε hariç tüm dizgelerdir.

Dil (language), `Σ*` üzerindeki herhangi bir alt kümedir: L ⊆ `Σ*`. Tanım bilerek çok geneldir. "Çift sayıda 1 içeren ikili dizgeler", "geçerli bir Python atamasının dizgeleri" ya da "a ile başlayıp b ile biten boş olmayan dizgeler" hepsi birer dildir. Dile üye olan dizgelere **kabul edilen**, olmayanlara **reddedilen** dizge denir. Bir dili tanımak, verilen bir dizgenin ona üye olup olmadığına karar veren bir yöntem bulmak demektir.

Diller üzerinde bazı işlemler tanımlanır ve bunlar ileride sık kullanılacak:

- **Birleşim:** L1 ∪ L2, her iki dilden de olan dizgelerin kümesi.
- **Kesişim:** L1 ∩ L2, iki dilin ortak dizgeleri.
- **Tümleyen:** L̄ = `Σ*` \ L, dilin dışında kalan her dizge.
- **Ekleme (concatenation):** L1·L2 = {xy : x ∈ L1, y ∈ L2}. Örneğin {a, ab} · {c, d} = {ac, ad, abc, abd}.
- **Kleene yıldızı:** `L*` = {ε} ∪ L ∪ LL ∪ LLL ∪ ..., yani L'den sıfır ya da daha fazla dizgenin art arda eklenmesi. Örneğin `{ab}*` = {ε, ab, abab, ababab, ...}.

Kleene yıldızı, düzenli ifadelerdeki `*` operatörünün tam karşılığıdır; bu bağlantıyı 36.5'te kuracağız. Birleşim `|` ile, ekleme bitişik yazımla karşılanır. Yani düzenli ifadeler, bu üç işlemle kurulan dillerin kısa bir yazımıdır.

## 36.2 Sonlu otomat (DFA): sınırlı bellekle tanımak

Bir dili tanımak için bilgisayarın dizgenin tamamını bir kerede görmesi gerekmez. Soldan sağa tek geçişte, sabit miktarda bellekle karar verebiliyorsa iş çok daha ucuzdur. Bu fikrin en sade biçimi **deterministik sonlu otomat** (DFA, deterministic finite automaton) kavramıdır. Bir DFA, sonlu sayıda **durum** (state) içeren bir makinedir: her adımda bir harf okur, bulunduğu durumu ve harfe göre yeni bir duruma geçer. Dizge bitince son durum **kabul** durumu ise dizge kabul edilir.

Resmî tanım beş parçadan oluşur ve bu yüzden **beşli** (5-tuple) olarak anılır:

M = (Q, Σ, δ, q0, F)

- **Q:** sonlu durum kümesi.
- **Σ:** girdi alfabesi.
- **δ:** geçiş fonksiyonu, δ: Q × Σ → Q. Her (durum, harf) çifti için tam olarak bir sonraki durum tanımlıdır; "deterministik" sözcüğünün anlamı budur.
- **q0 ∈ Q:** başlangıç durumu.
- **F ⊆ Q:** kabul durumları kümesi.

M'nin dili `L(M)` = {w ∈ `Σ*` : δ*(q0, w) ∈ F} olarak tanımlanır. δ*, geçiş fonksiyonunun dizgeye genişletilmiş hâlidir: δ*(q, ε) = q ve δ*(q, xa) = δ(δ*(q, x), a). Yani tanım, "dizgeyi harf harf izle, sonunda kabul durumunda mısın?" sorusunun biçimsel hâlidir.

Bunu somut bir örnekle görelim. Bir ikili sayının 3'e bölünüp bölünmediğini nasıl anlarsın? Klasik yol, sayıyı baştan sona okuyup her adımda **şimdiye kadar okunanın mod 3'ünü** tutmaktır. Yeni bir bit geldiğinde değer 2v + b olur; ikili sayılarda bir basamak sola kaydırmak değeri iki katına çıkarır, sonra bit eklenir. Modüler aritmetikte (2v + b) mod 3 yalnız v mod 3 ve b'ye bağlıdır. Dolayısıyla v'nin geri kalan kısmı önemsizdir: tek bir kalan tutmak yeter ve üç durum yeter. r0 kalan 0, r1 kalan 1, r2 kalan 2 demektir. Geçişler şöyledir:

- r0 --0--> r0 ve r0 --1--> r1 (2·0+1 = 1)
- r1 --0--> r2 (2·1+0 = 2) ve r1 --1--> r0 (2·1+1 = 3 ≡ 0)
- r2 --0--> r1 (2·2+0 = 4 ≡ 1) ve r2 --1--> r2 (2·2+1 = 5 ≡ 2)

Başlangıç r0'dır, kabul durumu da r0'dır: kalan 0 ise sayı 3'ün katıdır. Şekil 36.1 bu makineyi gösteriyor.

![Şekil 36.1: Üç'e bölünebilirlik DFA'sı: durum, şimdiye kadarki değerin mod 3'ü](gorseller/b36_dfa_uc.png)

Makineyi kodla kuralım. `dfa.py` dosyası genel bir DFA sınıfı, üç'e bölünebilirlik makinesi ve makineyi aritmetik tanımına karşı test eden bir doğrulama içerir. Sınıf beşlinin beş alanını birebir taşır. `calistir` metodu izi, yani her adımda hangi durumda olunduğunu döndürür; böylece makinenin çalışmasını gözle izleyebilirsin.

Önce `DFA` sınıfı ve üç'e bölünebilirlik makinesi gelir. `delta` bir sözlüktür: (durum, harf) çifti anahtar, sonraki durum değerdir. Geçiş tablosunu tek tek yazmak yerine formülden üretiyoruz: (2·r + b) mod 3.

```python
# dfa.py: DFA (beşli tanım) ve 3'e bölünebilirlik
import random


class DFA:
    """(Q, Sigma, delta, q0, F) beşlisi."""

    def __init__(self, Q, Sigma, delta, q0, F):
        self.Q, self.Sigma = set(Q), set(Sigma)
        self.delta = dict(delta)       # (durum, harf) -> durum
        self.q0, self.F = q0, set(F)

    def calistir(self, w):
        """w'nun izini (durum listesi) döndürür."""
        iz = [self.q0]
        for c in w:
            iz.append(self.delta[(iz[-1], c)])
        return iz

    def kabul(self, w):
        return self.calistir(w)[-1] in self.F
```

İkinci kısım doğrulama ve ana programdır. `dogrula`, uzunluğu 12'ye kadar bütün ikili dizgeleri (toplam 8191 dizge) ve 2000 rastgele uzun dizgeyi, aritmetik tanımla (`int(w, 2) % 3 == 0`) karşılaştırır. Boş dizgeyi 0 kabul ettiğimizi not et: bu, başlangıç durumu r0'ın kabul durumu olmasından gelir. Matematiksel olarak tutarlı bir tercihtir, ama bir kuralı açıkça seçtiğini bilmek gerekir; bölümün ilerisinde bu seçim yüzünden bir ayrıntıyı tekrar düşüneceğiz.

```python
def uc_bolunebilirlik():
    """Durum = şimdiye kadarki değerin mod 3'ü."""
    delta = {(r, b): (2 * r + int(b)) % 3
             for r in range(3) for b in "01"}
    return DFA(range(3), "01", delta, 0, {0})


def dogrula(seed=36):
    m = uc_bolunebilirlik()
    sayac = 0
    for uz in range(13):               # tüm dizgiler, |w| <= 12
        for bits in range(2 ** uz):
            w = format(bits, "0%db" % uz) if uz else ""
            beklenen = (int(w, 2) if w else 0) % 3 == 0
            assert m.kabul(w) == beklenen, w
            sayac += 1
    rng = random.Random(seed)          # rastgele uzun dizgiler
    for _ in range(2000):
        n = rng.randint(13, 80)
        w = "".join(rng.choice("01") for _ in range(n))
        assert m.kabul(w) == (int(w, 2) % 3 == 0), w
        sayac += 1
    return sayac


if __name__ == "__main__":
    m = uc_bolunebilirlik()
    for w in ["1011", "1001", ""]:
        print(repr(w), m.calistir(w),
              "kabul" if m.kabul(w) else "red")
    print("sinanan dizge:", dogrula())
```

Programın çıktısı, tanımladığımız makinenin davranışını doğrular:

```term
$ python dfa.py
'1011' [0, 1, 2, 2, 2] red
'1001' [0, 1, 2, 1, 0] kabul
'' [0] kabul
sinanan dizge: 10191
```

"1011" dizgesinin izi makinenin adım adım ne yaptığını gösterir. Bu iz 11 sayısının 3'e bölünmediğini (11 = 3·3 + 2) ve sonunda r2'de kaldığını ortaya koyar. "1001" (9) ise r0'a döner ve kabul edilir.

::: ipucu
DFA'yı bir tabloyla da tanımlayabilirsin: satırlar durumlar, sütunlar harfler. Bu tablo, geçiş fonksiyonunun kâğıttaki birebir karşılığıdır. Kodda `delta` sözlüğü aynı tabloyu saklar; yazmadan önce tabloyu kâğıda çizmek hata yapma olasılığını ciddi biçimde düşürür.
:::

## 36.3 NFA ve alt küme yapısı: belirsizlik de bir güç

DFA'da her (durum, harf) çifti tek bir sonraki duruma gider. Bu kısıt tasarımı kolaylaştırır ama bazı dilleri doğal biçimde anlatmayı zorlaştırır. Örneğin "sonu abb ile biten dizgeler" dilini düşün. Bir DFA okurken "abb'nin başlangıcını şimdi mi yakalıyorum?" sorusunun cevabını bilemez; bu yüzden her olası başlangıcı ayrı bir durumda taşımak zorunda kalır. Bir **belirsiz sonlu otomat** (NFA, nondeterministic finite automaton) ise bu tahmini yapmaya izin verir: aynı (durum, harf) çiftinden birden fazla ya da hiç geçiş çıkmayabilir, ve bir dizge, **en az bir** yoldan kabul edilirse kabul edilmiş sayılır.

Formel olarak NFA'da geçiş fonksiyonu δ: Q × (Σ ∪ {ε}) → P(Q) biçimindedir; yani sonucu bir durum kümesidir. Ek olarak **ε-geçişleri** vardır: bir ε-kenarıyla, girdi tüketmeden başka bir duruma geçebilirsin. Bir q durumundan yalnız ε-kenarlarıyla ulaşılabilen durumların kümesine q'nun **ε-kapanışı** denir. Bu kavram, Thompson yapısında (36.5) düzenli ifadelerin NFA'ya çevrilmesinin anahtarıdır.

Şekil 36.2'nin solunda, "sonu abb ile biten ikili dizgeler", yani (a|b)*abb dilinin NFA'sı var. q0 durumu bir döngüde her harfi okur (tahmin edilen başlangıç noktası yoksa), `a` gördüğünde ise bir kopyasını q1'e yollar. Sonra q1'de `b`, q2'de `b` okunursa ve q3'e varılırsa kabul edilir. Bu NFA dört durumludur. Aynı dili tanıyan DFA'yı bulmak için ne yapacağız?

![Şekil 36.2: (a|b)*abb için NFA (solda) ve alt küme yapısıyla elde edilen DFA (sağda)](gorseller/b36_nfa_altkume.png)

**Alt küme yapısı** (subset construction), Rabin ve Scott'ın (1959) gösterdiği genel yöntemdir ve şu fikre dayanır: NFA bir girdi okuduktan sonra **aynı anda olabileceği durumların kümesini** bilir. O hâlde bu kümeleri DFA'nın durumları olarak alabiliriz. Algoritma şöyledir:

1. Başlangıç DFA durumu, q0'ın ε-kapanışıdır.
2. Bir DFA durumu S ve bir harf a için, yeni durum T = ε-kapanış(S'den a ile ulaşılan durumlar) olur.
3. Yeni bulunan her T için adım 2'yi tekrarla; yeni durum kalmayınca dur.
4. Bir DFA durumu, içinde bir NFA kabul durumu varsa kabul durumudur.

Bu yöntem n durumlu bir NFA'dan en fazla 2^n durumlu bir DFA üretir. Durum sayısı üstel büyüyebilir; bunun gerçekten olabildiğini birazdan göreceğiz.

Örnek NFA için adım adım gidelim. Başlangıç: {0}. Bu NFA'da ε-kenarı yok, yani kapanış {0}'un kendisi. Harf `a`: q0 hem q0'a hem q1'e gider, yani {0,1}. Harf `b`: q0 yalnız q0'a gider, yani {0}. Bu biçimde devam edersek dört DFA durumu bulunur. Tablo, `nfa.py` içindeki `tablo` fonksiyonunun çıktısıdır: her satır bir DFA durumu, her sütun bir harfe geçiş.

| DFA durumu | a ile gidilen | b ile gidilen | Kabul mu? |
|---|---|---|---|
| {0} | {0,1} | {0} | hayır |
| {0,1} | {0,1} | {0,2} | hayır |
| {0,2} | {0,1} | {0,3} | hayır |
| {0,3} | {0,1} | {0} | evet |

Tablo, "sonu abb" dilinin DFA'sını verir. {0,3} kabul durumudur çünkü q3 içerir: son üç harf abb'yi tamamlamıştır. Şimdi `ababb` dizgesini bu DFA'dan geçirelim; her adım bir **iz** satırıdır.

| Adım | Okunan harf | Önceki durum | Sonraki durum |
|---|---|---|---|
| 0 | (başlangıç) | — | {0} |
| 1 | a | {0} | {0,1} |
| 2 | b | {0,1} | {0,2} |
| 3 | a | {0,2} | {0,1} |
| 4 | b | {0,1} | {0,2} |
| 5 | b | {0,2} | {0,3} |

Son durum {0,3} kabul durumudur, dizge kabul edilir. Aynı dizgeyi NFA üzerinde izlemek de aynı kümeleri verir; alt küme yapısı, NFA'nın bütün olası yollarını tek bir DFA izinde toplar.

Algoritmayı kodla uygulayalım. `nfa.py` dosyasında `NFA` sınıfı ε-kapanışı ve kabulü içerir; `alt_kume` yukarıdaki dört adımı uygular; `tablo` tabloyu basar; `dogrula` rastgele NFA'lar üretip her birinin DFA'sını tüm kısa dizgeler üzerinde NFA'nın kendisiyle karşılaştırır. Bu, iki otomatın eşdeğerliğini sınamanın pratik yoludur. Kesin bir karar için iki DFA'nın çarpım otomatında BFS yapmak yeterlidir (her iki tarafın da kabul durumunda olmadığı bir çift ulaşılabilir mi?); burada tüm kısa dizgeleri taradık, yani kanıt değil, güçlü bir sınamadır.

```python
# nfa.py: ε-NFA, ε-kapanış ve alt küme yapısı (NFA -> DFA)
import random
from itertools import product

EPS = ""                               # ε: boş harf


class NFA:
    def __init__(self, Q, Sigma, delta, q0, F):
        self.Q, self.Sigma = set(Q), set(Sigma)
        self.delta = {k: set(v) for k, v in delta.items()}
        self.q0, self.F = q0, set(F)

    def ileri(self, S, c):
        """S'den c harfiyle gidilen durumlar (kapanışsız)."""
        out = set()
        for q in S:
            out |= self.delta.get((q, c), set())
        return out

    def eps_kapanis(self, S):
        """S'ten yalnız ε-kenarlarla ulaşılanlar (S dahil)."""
        yigin, kap = list(S), set(S)
        while yigin:
            q = yigin.pop()
            for p in self.delta.get((q, EPS), set()):
                if p not in kap:
                    kap.add(p)
                    yigin.append(p)
        return frozenset(kap)

    def kabul(self, w):
        S = self.eps_kapanis({self.q0})
        for c in w:
            S = self.eps_kapanis(self.ileri(S, c))
        return bool(S & self.F)
```

Yukarıdaki sınıf, bir NFA'nın durumlarını ve geçişlerini bir sözlükte tutar. `ileri` bir durum kümesinden bir harfle gidilen durumları verir; `eps_kapanis` ε-kenarlarını yığınla (bir liste olarak) gezer. ε-kenarlarını yığınla gezmek, Bölüm 17'deki DFS'in kuzeni olan bir gezinmedir: her düğümü bir kez ziyaret eder ve kümeye ekler.

```python
def alt_kume(nfa):
    """DFA durumları NFA durum kümeleridir."""
    bas = nfa.eps_kapanis({nfa.q0})
    durumlar, yigin, delta = {bas}, [bas], {}
    while yigin:
        S = yigin.pop()
        for c in sorted(nfa.Sigma):
            T = nfa.eps_kapanis(nfa.ileri(S, c))   # boş olabilir
            delta[(S, c)] = T
            if T not in durumlar:
                durumlar.add(T)
                yigin.append(T)
    F = {S for S in durumlar if S & nfa.F}
    return bas, durumlar, delta, F


def ad(S):
    return "{" + ",".join(str(q) for q in sorted(S)) + "}"


def tablo(nfa):
    """Alt küme tablosu: her DFA durumu ve geçişleri."""
    bas, Q, delta, F = alt_kume(nfa)
    for S in sorted(Q, key=lambda s: (len(s), sorted(s))):
        satir = [ad(S)]
        for c in sorted(nfa.Sigma):
            satir.append("%s->%s" % (c, ad(delta[(S, c)])))
        satir.append("kabul" if S in F else "")
        print("  ".join(satir).rstrip())


def abb_nfa():
    """(a|b)*abb icin elle kurulmus NFA (ε yok)."""
    delta = {(0, "a"): {0, 1}, (0, "b"): {0}, (1, "b"): {2},
             (2, "b"): {3}}
    return NFA(range(4), "ab", delta, 0, {3})
```

Bu parça alt küme yapısının kendisidir. `durumlar` kümesi görülmüş DFA durumlarını, `yigin` işlenecek olanları tutar. Her yeni küme bir kez eklenir; bu yüzden döngü sonlu biter, çünkü en fazla 2^n küme vardır. `abb_nfa` elle kurulmuş dört durumlu NFA'dır ve Şekil 36.2'deki ile birebir aynıdır.

```python
def rastgele_nfa(rng, n, sigma="ab"):
    delta = {}
    for q in range(n):
        for c in sigma:
            for p in range(n):
                if rng.random() < 0.3:
                    delta.setdefault((q, c), set()).add(p)
        for p in range(n):
            if rng.random() < 0.1:
                delta.setdefault((q, EPS), set()).add(p)
    F = {q for q in range(n) if rng.random() < 0.3} or {n - 1}
    return NFA(range(n), sigma, delta, 0, F)


def dogrula(seed=36, n_nfa=200):
    """Rastgele NFA'lar ve kısa dizgilerle eşdeğerlik testi."""
    rng = random.Random(seed)
    sinanan = 0
    for _ in range(n_nfa):
        nfa = rastgele_nfa(rng, rng.randint(2, 6))
        bas, Q, delta, F = alt_kume(nfa)
        for uz in range(9):
            for t in product("ab", repeat=uz):
                w, S = "".join(t), bas
                for c in w:
                    S = delta[(S, c)]
                assert (S in F) == nfa.kabul(w), w
                sinanan += 1
    return sinanan
```

`rastgele_nfa` her geçişi ve ε-kenarını olasılıkla ekler, `dogrula` iki yüz NFA için bütün uzunluğu 8'e kadar olan dizgeleri sınar. Aynı tohumla (36) çalıştırdığında sonuç her zaman aynıdır; bu, sonuçları yeniden üretilebilir kılar.

```python
def ailesi_n(n):
    """Sondan n. harf 'a' olan dizgiler: NFA n+1, DFA 2^n."""
    delta = {(0, "a"): {0, 1}, (0, "b"): {0}}
    for i in range(1, n):
        delta[(i, "a")] = {i + 1}
        delta[(i, "b")] = {i + 1}
    return NFA(range(n + 1), "ab", delta, 0, {n})


if __name__ == "__main__":
    tablo(abb_nfa())
    print("sinanan dizge:", dogrula())
    for n in range(1, 9):
        Q = alt_kume(ailesi_n(n))[1]
        print("n=%d NFA=%d DFA=%d" % (n, n + 1, len(Q)))
```

`ailesi_n` ilginç bir aileyi kurar: "sondan n. harf a olan dizgeler". Bu dilin NFA'sı n+1 durumludur (NFA kendi tahminini basitçe yapar), ama DFA'sı 2^n durumludur. Neden? Sondan n. harfin ne olduğunu bilmek için DFA'nın son n harfin tam hâlini hatırlaması gerekir; bu n harflik 2^n olası hâlden biridir ve iki farklı hâl, birbirinden farklı devamlarla ayrılabilir. Çıktıda bunu sayıyla görürsün:

```term
$ python nfa.py
{0}  a->{0,1}  b->{0}
{0,1}  a->{0,1}  b->{0,2}
{0,2}  a->{0,1}  b->{0,3}
{0,3}  a->{0,1}  b->{0}  kabul
sinanan dizge: 102200
n=1 NFA=2 DFA=2
n=2 NFA=3 DFA=4
n=3 NFA=4 DFA=8
n=4 NFA=5 DFA=16
n=5 NFA=6 DFA=32
n=6 NFA=7 DFA=64
n=7 NFA=8 DFA=128
n=8 NFA=9 DFA=256
```

İlk dört satır alt küme tablosudur. "sinanan dizge: 102200" değeri, 200 NFA için toplam 102 200 dizge karşılaştırmasının hiçbirinde uyuşmazlık olmadığını söyler. Son sekiz satır ailenin büyümesini gösterir: NFA her adımda bir durum büyürken DFA iki katına çıkar. n=8'de DFA 256 durumludur. Bu, belirsizliğin hesabı nasıl bir **zaman-bellek** takası olduğunu gösterir: NFA'yı kurmak ucuz, ama onu DFA'ya çevirmek ve her girdiyi DFA ile okumak pahalı olabilir. Gerçek düzenli ifade motorları çoğu zaman NFA'yı doğrudan simüle eder ya da DFA'yı gerektikçe (tembelce) kurar; bunu Bölüm 36.5'te ve Kendin Yap 1'de göreceğiz.

## 36.4 DFA minimizasyonu: aynı dili tanıyan en küçük makine

Alt küme yapısı bize bir DFA verir, ama bu DFA gereksiz durumlar taşıyor olabilir. İki durum, **her** devam dizgesi için aynı sonucu veriyorsa birbirinden ayrılamaz ve tek bir durum olarak birleştirilebilir. Tam tanım şöyledir: p ve q durumları denktir (p ≡ q), ancak ve ancak her w ∈ `Σ*` için δ*(p, w) ∈ F ⇔ δ*(q, w) ∈ F. Eşdeğerlik bir denklik bağıntısıdır (yansıyan, simetrik, geçişken), dolayısıyla durumları denklik sınıflarına ayırabiliriz.

Burada Myhill–Nerode teoremi (genel bilgi) devreye girer: bir dilin minimal DFA'sı durum sayısı açısından **tek**tir ve durumları denklik sınıflarıdır. Minimal DFA'yı bulmak için tanımdan yola çıkan bir yöntem, **tablo doldurma** (table filling) algoritmasıdır:

1. Erişilemeyen durumları at (q0'dan hiçbir girdiyle gidilemeyen durumlar).
2. Her (p, q) çifti için: biri kabul, diğeri değilse çifti "ayrışık" (distinguishable) işaretle.
3. Kalan her çift (p, q) ve her harf a için, eğer (δ(p,a), δ(q,a)) çifti ayrışıksa, (p, q)'yu da ayrışık işaretle. İşaretleme değişmeyene kadar tekrarla.
4. İşaretlenmeyen çiftler denktir; denk durumları birleştir.

Bu algoritmanın doğruluğu şuradan gelir: iki durumu ayıran bir w dizgesi varsa, bu dizgenin ilk harfi a ise (p, q) çifti, (δ(p,a), δ(q,a)) çiftinin ayrışıklığına bağlıdır; sonsuz gerileyen bir zincir olmadığı için adım 3 ayrışıklığı doğru yayar. Hopcroft'un (1971) algoritması aynı işi O(n log n · |Σ|) sürede yapar (genel bilgi); burada daha basit olan tablo doldurmayı kodluyoruz, n küçük olduğunda bu yeterlidir.

Örnek olarak iki bitlik bir paritenin DFA'sını alalım: a harfi sayılan "a sayısının paritesi" ve b harfi sayılan "b sayısının paritesi" birlikte tutuluyor, dört durum var; kabul koşulu yalnız a sayısının çift olmasıdır. Dikkat et: b'nin paritesi kabul kararını etkilemiyor, yani fazla bilgi taşıyan bir durum var. Şekil 36.3, bu DFA'nın minimize edilmiş hâlini gösteriyor.

![Şekil 36.3: Dört durumlu parite DFA'sı (solda) ve minimal hâli, iki durum (sağda)](gorseller/b36_minimizasyon.png)

Tablo doldurma ile bu makinenin iki durumlu minimal hâle indiğini doğrulayalım. Adım 1'de kabul ile red durumlarını ayırıyoruz: (0,0)-(1,0), (0,0)-(1,1), (0,1)-(1,0), (0,1)-(1,1) ayrışık. Adım 2'de geriye kalan (0,0)-(0,1) ve (1,0)-(1,1) çiftlerine bakıyoruz: (0,0) ve (0,1) durumları b ile gidildiğinde kendi çiftlerine döner, a ile gidildiğinde (1,0)-(1,1) çiftine gider; bu çift de ayrışık değil. Hiçbir ayrışma olmadığı için bu iki çift denktir. Sonuç iki sınıf: {(0,0), (0,1)} ve {(1,0), (1,1)}.

Kodu yazalım. `minimize.py` içinde `erisilebilir` BFS ile erişilebilir durumları bulur; `tablo_doldur` yukarıdaki iki adımı uygular; `minimize` sınıfları tek temsilciye indirip yeni bir DFA kurar. `imza_sayisi` bağımsız bir doğrulama yöntemi sağlar: bir durumun imzası, o durumdan başlayarak kısa dizgelerin kabul/red vektörüdür. Farklı imzaya sahip durumlar ayrışır, aynı imzaya sahip olanlar (kısa dizgelerle) ayrışmaz. Moore'un gözleminden, n durumlu bir DFA'da iki durumun ayrışıyorsa uzunluğu n-2'yi aşmayan bir dizgeyle ayrışacağını biliyoruz; biz daha güvenli olması için n-1 kullanıyoruz.

```python
# minimize.py: DFA minimizasyonu (tablo doldurma) ve doğrulama
import random
from itertools import product
from dfa import DFA


def erisilebilir(d):
    """q0'dan okunabilen durumlar (BFS)."""
    gor, kuyruk = {d.q0}, [d.q0]
    while kuyruk:
        q = kuyruk.pop(0)
        for c in d.Sigma:
            p = d.delta[(q, c)]
            if p not in gor:
                gor.add(p)
                kuyruk.append(p)
    return gor
```

Bu ilk parça erişilebilirlik ve tablo doldurmanın ilk yarısıdır. `erisilebilir` bir kuyruk (liste) kullanan BFS'tir; Bölüm 17'de gördüğün BFS'in birebir aynısıdır, yalnız düğümler DFA durumlarıdır.

```python
def tablo_doldur(d):
    """ayrik[(p, q)] = True ise p ve q ayrışabilir (simetrik)."""
    Q = sorted(erisilebilir(d))
    ayrik = {}
    for i, p in enumerate(Q):          # 1. adım: kabul/red ayrımı
        for q in Q[:i]:
            ayrik[(q, p)] = ayrik[(p, q)] = (p in d.F) != (q in d.F)
    degisti = True                     # 2. adım: yayılım
    while degisti:
        degisti = False
        for i, p in enumerate(Q):
            for q in Q[:i]:
                if ayrik[(q, p)]:
                    continue
                for c in d.Sigma:
                    a, b = d.delta[(q, c)], d.delta[(p, c)]
                    if a != b and ayrik[(a, b)]:
                        ayrik[(q, p)] = ayrik[(p, q)] = True
                        degisti = True
                        break
    return Q, ayrik


def minimize(d):
    """Denk durumları tek temsilciye indirir."""
    Q, ayrik = tablo_doldur(d)
    temsil = {}
    for q in Q:
        temsil[q] = q
        for p in Q[:Q.index(q)]:
            if not ayrik[(p, q)]:
                temsil[q] = temsil[p]
                break
    rep = sorted(set(temsil.values()))
    delta = {(t, c): temsil[d.delta[(t, c)]]
             for t in rep for c in d.Sigma}
    F = {t for t in rep if t in d.F}
    return DFA(rep, d.Sigma, delta, temsil[d.q0], F)
```

`tablo_doldur` ayrışıklık tablosunu simetrik olarak tutar: (p, q) ve (q, p) aynı değeri taşır, böylece sıralama kaygısı kalmaz. İki adım, değişiklik kalmayana kadar tekrarlanan bir `while` döngüsü içindedir. `minimize` her durumu, kendinden önce gelen ve denk olduğu ilk temsilciye bağlar; bu, sınıfların tutarlı biçimde kurulmasını sağlar çünkü denklik geçişkendir.

```python
def _son(d, q, w):
    for c in w:
        q = d.delta[(q, c)]
    return q


def imza_sayisi(d, L):
    """|w| <= L dizgilerin kabul vektörü: ayrık sınıf sayısı."""
    dizgiler = ["".join(t) for k in range(L + 1)
                for t in product(sorted(d.Sigma), repeat=k)]
    imzalar = set()
    for q in erisilebilir(d):
        imzalar.add(tuple(_son(d, q, w) in d.F for w in dizgiler))
    return len(imzalar)


def parite_dfa():
    """a-paritesi x b-paritesi: 4 durum; minimal olan 2."""
    delta = {}
    for x in (0, 1):
        for y in (0, 1):
            delta[((x, y), "a")] = (1 - x, y)
            delta[((x, y), "b")] = (x, 1 - y)
    Q = [(x, y) for x in (0, 1) for y in (0, 1)]
    return DFA(Q, "ab", delta, (0, 0), {(0, 0), (0, 1)})


def rastgele_dfa(rng, n, sigma="ab"):
    delta = {(q, c): rng.randrange(n)
             for q in range(n) for c in sigma}
    F = {q for q in range(n) if rng.random() < 0.4} or {0}
    return DFA(range(n), sigma, delta, 0, F)
```

Bu parça bağımsız doğrulamanın araçlarını ve parite örneğinin kurulumunu içerir. `parite_dfa` dört durumlu DFA'yı açık bir döngüyle kurar: (x, y) durumunda a harfi x'i, b harfi y'yi çevirir. `rastgele_dfa` 2 ile 9 arasında durumlu rastgele DFA'lar üretir.

```python
def dogrula(seed=36, n_dfa=300):
    rng = random.Random(seed)
    for _ in range(n_dfa):
        n = rng.randint(2, 9)
        d = rastgele_dfa(rng, n)
        m = minimize(d)
        # Moore: n durumlu DFA'da |w| <= n-2 yeter; n-1 ile güvenli.
        assert len(m.Q) == imza_sayisi(d, max(n - 1, 1)), n
        for uz in range(9):            # aynı dili tanımalı
            for t in product("ab", repeat=uz):
                w = "".join(t)
                assert d.kabul(w) == m.kabul(w), w
    return n_dfa


if __name__ == "__main__":
    d = parite_dfa()
    m = minimize(d)
    print("ön durum:", len(d.Q), " minimal:", len(m.Q))
    Q, ayrik = tablo_doldur(d)
    for i, p in enumerate(Q):
        for q in Q[:i]:
            print(q, p, "AYRIK" if ayrik[(q, p)] else "denk")
    print("dogrulanan DFA:", dogrula())
```

`dogrula` her rastgele DFA için iki şeyi kontrol eder: minimal durum sayısı, imza sayısına eşit mi ve minimal DFA orijinal DFA ile aynı dili tanıyor mu (uzunluğu 8'e kadar bütün dizgelerle). Çıktı, parite örneğinin tablosunu ve iki sayıyı verir:

```term
$ python minimize.py
ön durum: 4  minimal: 2
(0, 0) (0, 1) denk
(0, 0) (1, 0) AYRIK
(0, 1) (1, 0) AYRIK
(0, 0) (1, 1) AYRIK
(0, 1) (1, 1) AYRIK
(1, 0) (1, 1) denk
dogrulanan DFA: 300
```

Çıktının ilk satırı 4 durumdan 2 duruma indirgemeyi gösterir. Tablonun her satırı bir çiftin durumunu verir; "denk" yazan çiftler birleştirilir. "dogrulanan DFA: 300" ise üç yüz rastgele makinede minimal boyutun imza sayısına eşit olduğunu ve dillerin korunduğunu doğrular.

::: dikkat
Minimal DFA'nın **tekliği** önemlidir: iki farklı tasarımcı aynı dili tanıyan iki DFA kurarsa, minimizasyondan sonra birebir aynı yapıyı (durum adları dışında) elde ederler. Bu, bir dilin "en iyi" makinesinin tanımlanabilir olduğunu söyler; ama "en iyi" kelimesi burada durum sayısı içindir, çalışma hızı için her zaman en iyi olmak zorunda değildir.
:::

## 36.5 Düzenli ifadeler ve Thompson yapısı

Düzenli ifade (regular expression), bir dili kısa bir yazımla anlatır. Tanım özyinelemelidir: boş dil ∅, boş dizge ε ve her a ∈ Σ düzenli ifadedir; R1 ve R2 düzenli ifadeyse R1|R2 (birleşim), R1R2 (ekleme) ve R1* (Kleene yıldızı) da düzenli ifadedir. Ek olarak parantez kullanılır. Bu tanımla kurulan dillere **düzenli diller** denir.

Kleene teoremi (genel bilgi) üç kavramın aynı dil sınıfını tanımladığını söyler: düzenli ifadeyle tanımlanabilen diller, DFA ile tanınabilen diller ve NFA ile tanınabilen diller. Teoremin bir yönü (düzenli ifadeden otomata) bu bölümün asıl konusu: Thompson'ın (1968) kurduğu yapı, her düzenli ifadeye karşılık bir NFA üretir. Yapı **kompozisyonel**dir: her operatör için sabit sayıda yeni durum ve ε-kenarı eklenir, parçalar birleştirilir. Bu yüzden NFA'nın boyutu ifadenin boyutuyla doğrusal büyür.

Yapının kuralları şöyledir. Her parçanın tek bir başlangıç ve tek bir bitiş durumu vardır; bu yalnızca bir kolaylık değil, bütün kuralların birbirine güvenle takılmasını sağlar.

- **Harf a:** s --a--> t (iki durum, bir kenar).
- **Birleştirme XY:** X'in bitişinden Y'nin başlangıcına ε-kenarı.
- **Birleşim X|Y:** yeni bir başlangıç s ve bitiş t; s'den iki parçanın başlangıçlarına, iki parçanın bitişlerinden t'ye ε-kenarları.
- **Yıldız** `X*`: yeni s ve t; s'den X'in başlangıcına ve s'den t'ye (sıfır tekrar), X'in bitişinden X'in başlangıcına (tekrar) ve X'in bitişinden t'ye ε-kenarları.

Şekil 36.4 dört yapıyı tek tek gösteriyor.

![Şekil 36.4: Thompson yapısının parçaları: harf, birleştirme, birleşim ve yıldız](gorseller/b36_thompson.png)

Bu yapıyı kendi düzenli ifade motorumuzda kuracağız. Motorun desteklediği söz dizimi küçüktür: harfler a ve b, birleştirme (bitişik yazım), `|` birleşim, `*`, `+` ve `?` tekrarları ve parantezler. Ayrıştırma, Bölüm 15'te gördüğün özyinelemeli iniş yöntemiyle yapılır: her gramer kuralı bir fonksiyondur. Gramer şudur:

- birlesim := sira ('|' sira)*
- sira := tekrar+
- tekrar := atom ('*' | '+' | '?')?
- atom := harf | '(' birlesim ')'

Tekrarlayan kural (`sira`'da `tekrar+`) soldan sağa yürüyerek bir dizi birleştirmeyi okur. Bu gramerin neden bu biçimde yazıldığını 36.8'de, belirsizlik konusunda yeniden ele alacağız.

Kodun ilk bölümü ayrıştırıcıdır. `Ayristirici` sınıfı, ayrıştırılan dizgedeki konumu (`self.i`) tutar ve gramerin her kuralına bir yöntem karşılık gelir. Çıktı bir ağaçtır: düğümler ('alt', 'cat', '*', '+', '?', 'chr') etiketlerinden oluşur.

```python
# regex.py: düzenli ifade motoru (ayrıştırıcı + Thompson NFA)
import random
import re
from itertools import product


class Ayristirici:
    """birlesim := sira ('|' sira)*
    sira     := tekrar+
    tekrar   := atom ('*' | '+' | '?')?
    atom     := harf | '(' birlesim ')'"""

    def __init__(self, desen):
        self.s, self.i = desen, 0

    def bak(self):
        return self.s[self.i] if self.i < len(self.s) else None

    def tuket(self, bekl=None):
        c = self.bak()
        if bekl is not None and c != bekl:
            raise SyntaxError("%r bekleniyordu" % bekl)
        self.i += 1
        return c

    def birlesim(self):
        dallar = [self.sira()]
        while self.bak() == "|":
            self.tuket()
            dallar.append(self.sira())
        return ("alt", dallar) if len(dallar) > 1 else dallar[0]

    def sira(self):
        parca = [self.tekrar()]
        while self.bak() not in (None, "|", ")"):
            parca.append(self.tekrar())
        return ("cat", parca) if len(parca) > 1 else parca[0]
```

Ayrıştırıcının ikinci bölümü, `tekrar` ve `atom` kurallarını ve tek giriş noktası `ayristir`'i içerir. `ayristir` sonunda girdinin tamamen tüketilip tüketilmediğini kontrol eder; aksi hâlde "fazladan" hatası verir. Bu kontrol, `a)b` gibi dengesiz bir ifadenin sessizce yanlış anlaşılmasını önler.

```python
    def tekrar(self):
        n = self.atom()
        if self.bak() in ("*", "+", "?"):
            n = (self.tuket(), n)
        return n

    def atom(self):
        c = self.bak()
        if c == "(":
            self.tuket("(")
            n = self.birlesim()
            self.tuket(")")
            return n
        if c is None or c in "|)*+?":
            raise SyntaxError("beklenmeyen %r" % c)
        return ("chr", self.tuket())


def ayristir(desen):
    p = Ayristirici(desen)
    ag = p.birlesim()
    if p.bak() is not None:
        raise SyntaxError("fazladan %r" % p.bak())
    return ag


class Grafik:
    def __init__(self):
        self.n, self.kenar = 0, []     # kenar: (kaynak, harf, hedef)

    def yeni(self):
        self.n += 1
        return self.n - 1

    def ekle(self, a, h, b):
        self.kenar.append((a, h, b))
```

Thompson yapısının kompozisyonel kurallarını doğrudan bu özyinelemeli fonksiyon kodlar. `Grafik` kenarları bir liste olarak tutar; `yeni` her çağrıda yeni bir durum numarası üretir. `thompson` her AST düğümü için iki durum ve gerekli ε-kenarlarını ekler.

```python
def thompson(ag, g):
    """AST'den (baslangic, bitis) kurar. Harf None ise ε-kenardır."""
    tur = ag[0]
    if tur == "chr":
        s, t = g.yeni(), g.yeni()
        g.ekle(s, ag[1], t)
        return s, t
    if tur == "cat":
        s, t = thompson(ag[1][0], g)
        for alt in ag[1][1:]:
            s2, t2 = thompson(alt, g)
            g.ekle(t, None, s2)
            t = t2
        return s, t
    if tur == "alt":
        s, t = g.yeni(), g.yeni()
        for dal in ag[1]:
            s2, t2 = thompson(dal, g)
            g.ekle(s, None, s2)
            g.ekle(t2, None, t)
        return s, t
    s2, t2 = thompson(ag[1], g)        # '*', '+', '?'
    s, t = g.yeni(), g.yeni()
    g.ekle(s, None, s2)
    g.ekle(t2, None, t)
    if tur in ("*", "?"):
        g.ekle(s, None, t)             # sıfır tekrar
    if tur in ("*", "+"):
        g.ekle(t2, None, s2)           # tekrar
    return s, t
```

Burada `tekrar` (`*`, `+`, `?`) için kenar kurulumu dikkat gerektirir. `*` için hem sıfır tekrar (s'den t'ye) hem tekrar (t2'den s2'ye) kenarları gerekir; `+` için sıfır tekrar kenarı yoktur; `?` için yalnızca sıfır tekrar kenarı vardır. Bu üç durumun ayrımı tek bir `if` çiftiyle yapılır.

```python
class Motor:
    """Derlenmiş düzenli ifade; tam eşleşme simülasyonu."""

    def __init__(self, desen):
        g = Grafik()
        self.bas, self.son = thompson(ayristir(desen), g)
        self.n = g.n
        self.komsu = {}
        for a, h, b in g.kenar:
            self.komsu.setdefault(a, []).append((h, b))

    def kapanis(self, S):
        yigin, sonuc = list(S), set(S)
        while yigin:
            q = yigin.pop()
            for h, b in self.komsu.get(q, ()):
                if h is None and b not in sonuc:
                    sonuc.add(b)
                    yigin.append(b)
        return sonuc

    def tam_eslesir(self, w):
        S = self.kapanis({self.bas})
        for c in w:
            T = {b for q in S for h, b in self.komsu.get(q, ())
                 if h == c}
            S = self.kapanis(T)
            if not S:
                return False
        return self.son in S
```

`Motor` bir düzenli ifadeyi derler ve tam eşleşme için simüle eder. `kapanis` ε-kapanışıdır (DFS ile). `tam_eslesir` girdiyi harf harf okur: her adımda mevcut durum kümesinden bu harfle gidilen durumların ε-kapanışını alır. Küme boşalırsa girdi reddedilir; bitince bitiş durumunun kümede olup olmadığına bakılır. Her adımın maliyeti NFA'nın kenar sayısıyla orantılıdır; bu yüzden toplam süre girdi uzunluğuyla doğrusaldır. Bu, 36.6'da ölçeceğimiz özelliktir.

```python
def desen_uret(rng, d):
    """(desen, boş_eşleşir) çifti. Boş eşleşen grup üzerine * ve +
    konmaz: Python re bu tür iç içe döngülerde takılabiliyor."""
    if d <= 0 or rng.random() < 0.35:
        atom, bos = rng.choice("ab"), False
    else:
        s, bos = birlesim_uret(rng, d - 1)
        atom = "(" + s + ")"
    op = rng.choice(["?", "", "*", "+"])
    if op in ("*", "+") and bos:
        op = ""
    if op in ("?", "*"):
        bos = True
    return atom + op, bos


def sira_uret(rng, d):
    parca = [desen_uret(rng, d) for _ in range(rng.randint(1, 3))]
    return "".join(s for s, _ in parca), all(b for _, b in parca)


def birlesim_uret(rng, d):
    dallar = [sira_uret(rng, d) for _ in range(rng.randint(1, 2))]
    return "|".join(s for s, _ in dallar), any(b for _, b in dallar)
```

Test için rastgele desen üreticisine ihtiyacımız var. Üretici her atomun ardına en çok bir operatör koyar ve **boş eşleşebilen bir gruba `*` ya da `+` koymaz**. Bu kuralı sonradan ekledik: ilk sürümde `((a|a?)+|...)` gibi desenlerde Python'un `re` modülü on saniyeler boyunca takıldı. Bunun nedenini 36.6'da göreceğiz; şimdilik bilmen gereken, bu kuralın yalnızca test üreticisine uygulandığı ve motorun kendisini değiştirmediğidir.

```python
def dogrula(seed=36, n_desen=600, boy=6):
    rng = random.Random(seed)
    sinanan = 0
    for _ in range(n_desen):
        desen = birlesim_uret(rng, 2)[0]
        m, ref = Motor(desen), re.compile(desen)
        for k in range(boy + 1):
            for t in product("ab", repeat=k):
                w = "".join(t)
                beklenen = bool(ref.fullmatch(w))
                assert m.tam_eslesir(w) == beklenen, (desen, w)
                sinanan += 1
    return sinanan


if __name__ == "__main__":
    m = Motor("(a|b)*abb")
    print("düğüm:", m.n, "kenar:",
          sum(len(v) for v in m.komsu.values()))
    for w in ["abb", "aabb", "abab", "ab"]:
        print(w, m.tam_eslesir(w),
              bool(re.fullmatch("(a|b)*abb", w)))
    print("sinanan dizge:", dogrula())
```

`dogrula` 600 rastgele desen üretir, her birini hem kendi motorumuzla hem `re.fullmatch` ile derler, ve uzunluğu 6'ya kadar bütün {a, b} dizgelerinde sonuçları karşılaştırır. Toplam 76 200 karşılaştırmada tek bir uyuşmazlık yoksa motor doğru kabul edilir.

```term
$ python regex.py
düğüm: 14 kenar: 16
abb True True
aabb True True
abab False False
ab False False
sinanan dizge: 76200
```

Çıktı üç şeyi söyler. "düğüm: 14 kenar: 16" değeri `(a|b)*abb` için kurduğumuz NFA'nın boyutudur; Thompson yapısı düzenli ifadeye göre doğrusal boyutlu bir makine üretir. Dört örnek dizge, kendi motorumuzun `re` ile aynı kararı verdiğini gösterir. Son satır diferansiyel testin sonucudur. Bu testin değeri şuradadır: iki bağımsız gerçekleme (bizim motorumuz ve Python'un C ile yazılmış motoru) yüzlerce farklı desende aynı dili tanıyorsa, hatanın bir ihtimali çok düşüktür. Yine de kanıt değildir; ama mühendislikte pratik güvence budur.

## 36.6 Geri izleme ve katastrofik geri izleme (ReDoS)

Python'un `re` modülü, Perl ailesinin **geri izlemeli** (backtracking) motorudur. Bir tekrarlama düğümüne geldiğinde bir seçim yapar ve seçimi bir yığında saklar; eşleşme başarısız olursa geri döner ve başka bir seçim dener. Bu strateji çoğu desende hızlıdır ve geri referans (backreference) gibi düzenli dil dışındaki özellikleri de destekleyebildiği için yaygındır. Bedeli şudur: bazı desenlerde, girdiye bağlı olarak, olası seçim sayısı üstel büyür.

Klasik örnek `(a+)+b` desenidir. Bu desen, `a` karakterlerinden oluşan bir dizgeyi ve sonunda bir `b` ister. Girdi `aaaa...a` (sonda b yok) olduğunda motor her `a` dizisini iç `a+` ile ve dış `+` ile parçalara bölebilir: n tane a'yı kaç farklı biçimde gruplayabileceğin 2^(n-1) tanedir. Motor bunların hepsini dener, çünkü sonunda `b` bulamaz. Süre, n'de üstel büyür.

Bu, **katastrofik geri izleme** (catastrophic backtracking) olarak bilinir ve güvenlik açığı olduğunda **ReDoS** (Regular expression Denial of Service) adını alır. Saldırgan, sunucunun bir doğrulama regex'ini işlemesi için özel bir girdi gönderir; sunucu işlemcisini dakikalarca ya da saatlerce bu girdiye harcar. Girdinin uzunluğu birkaç yüz karakter bile olsa, üstel süre sunucuyu kullanılamaz kılar. Web sunucularında ve form doğrulamada bu tür olaylar bilinmektedir.

Teoriyi ölçümle doğrulayalım. Naif bir geri izleme eşleştiricisi yazacağız: her çağrı bir adım sayılır, böylece süre yerine **adım sayısı** üzerinden deterministik bir karşılaştırma yapabiliriz. Süre ölçümü ayrıca Python'un `re`'si ile yapılacak ve üçüncü olarak bizim Thompson simülasyonumuz aynı girdide ölçülecek.

Naif eşleştirici, ayrıştırıcının AST'sini (regex.py'deki biçimde) alır ve devamlılık geçişli (continuation-passing) bir yapıyla çalışır: her düğüm, eşleştiğinde "devamını" çağıran bir fonksiyon alır. Bu yapı geri izlemenin doğal ifadesidir: bir seçim başarısız olursa, aynı devam farklı bir seçimle tekrar çağrılır.

```python
# redos.py: katastrofik geri izleme ölçümü, desen (a+)+b
# Kullanım: python redos.py <veri_klasörü>
import csv
import os
import re
import sys
import time

sys.setrecursionlimit(10000)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regex import Motor, ayristir

ADIM = [0]


def esle(ag, w, i, k):
    """Naif geri izleme. Her çağrı bir adım sayılır."""
    ADIM[0] += 1
    t = ag[0]
    if t == "chr":
        return i < len(w) and w[i] == ag[1] and k(i + 1)
    if t == "cat":
        return seq(ag[1], 0, w, i, k)
    if t == "alt":
        return any(esle(d, w, i, k) for d in ag[1])
    if t == "?":
        return esle(ag[1], w, i, k) or k(i)
    if t == "*":
        def tekrar(j):
            return j > i and esle(ag, w, j, k)
        return esle(ag[1], w, i, tekrar) or k(i)
    if t == "+":
        return esle(ag[1], w, i,
                    lambda j: esle(("*", ag[1]), w, j, k))
```

`esle` fonksiyonu her düğüm türü için bir dal içerir. Tekrarlamada (`*`) bir koruma vardır: `j > i` koşulu, boş bir eşleşmenin sonsuz döngü yaratmasını engeller. Bu koruma olmasaydı `(a*)*` gibi desenlerde motor aynı konumda sonsuz tekrar ederdi. `+` düğümü `ilk eşleşme` + `sıfır veya daha fazla` olarak tanımlanır.

```python
def seq(parca, idx, w, i, k):
    if idx == len(parca):
        return k(i)
    return esle(parca[idx], w, i,
                lambda j: seq(parca, idx + 1, w, j, k))


def naif_adim(desen, w):
    ADIM[0] = 0
    ok = esle(ayristir(desen), w, 0, lambda j: j == len(w))
    return ok, ADIM[0]


def en_kisa_sure(f, tekrar=3):
    """Üç ölçümün en küçüğü (gürültüyü azaltmak için)."""
    en = float("inf")
    for _ in range(tekrar):
        t0 = time.perf_counter()
        f()
        en = min(en, time.perf_counter() - t0)
    return en
```

`naif_adim` adım sayacını sıfırlar ve eşleştirir. `en_kisa_sure` her ölçümü üç kez tekrarlar ve en küçüğünü alır; bu, işletim sistemi gürültüsünü azaltmanın basit ve yaygın bir yoludur. Bir süre ölçümünde en küçük değer, ölçümün "gerçek" maliyetine en yakın olandır.

```python
if __name__ == "__main__":
    DESEN = "(a+)+b"
    VERI = sys.argv[1] if len(sys.argv) > 1 else "."
    print("python", sys.version.split()[0])
    with open(os.path.join(VERI, "b36_redos.csv"), "w", newline="",
              encoding="utf-8") as f:
        yaz = csv.writer(f)
        yaz.writerow(["n", "naif_adim", "re_ms"])
        for n in range(10, 25, 2):
            w = "a" * n
            ok, adim = naif_adim(DESEN, w)
            assert ok is False
            t = en_kisa_sure(lambda: re.fullmatch(DESEN, w))
            yaz.writerow([n, adim, round(t * 1000, 3)])
            print("n=%2d naif=%9d re_ms=%.3f" % (n, adim, t * 1000))
    m = Motor(DESEN)
    with open(os.path.join(VERI, "b36_thompson.csv"), "w", newline="",
              encoding="utf-8") as f:
        yaz = csv.writer(f)
        yaz.writerow(["n", "thompson_ms"])
        for n in [1000, 2000, 4000, 8000, 16000]:
            w = "a" * n
            assert m.tam_eslesir(w) is False
            t = en_kisa_sure(lambda: m.tam_eslesir(w))
            yaz.writerow([n, round(t * 1000, 3)])
            print("thompson n=%6d ms=%.2f" % (n, t * 1000))
```

Ana bölüm iki CSV dosyası yazar: `b36_redos.csv` (naif adım sayısı ve Python'un süresi) ve `b36_thompson.csv` (Thompson simülasyonunun süresi). Betiği bir veri klasörü argümanıyla çalıştırırsın; ölçümleri Kitap'ın `engine/veri/` klasörüne yazmak için:

```term
$ python redos.py engine/veri
python 3.12.10
n=10 naif=     6142 re_ms=0.030
n=12 naif=    24574 re_ms=0.113
n=14 naif=    98302 re_ms=0.456
n=16 naif=   393214 re_ms=1.826
n=18 naif=  1572862 re_ms=7.372
n=20 naif=  6291454 re_ms=30.702
n=22 naif= 25165822 re_ms=122.989
n=24 naif=100663294 re_ms=480.764
thompson n=  1000 ms=1.54
thompson n=  2000 ms=3.08
thompson n=  4000 ms=6.18
thompson n=  8000 ms=12.62
thompson n= 16000 ms=25.22
```

Çıktıdaki `re_ms` sütunu ile CSV'deki değerler aynıdır. Önce adım sayılarını okuyalım. n=10'dan n=24'e kadar, her iki artışta adım sayısı tam olarak dört kat artıyor: 6 142, 24 574, 98 302, 393 214 ... Bu, adım sayısının yaklaşık 2^n olduğu anlamına gelir: her yeni `a` karakteri, olası bölme sayısını iki katına çıkarır. Python'un `re` süresi de aynı biçimde büyüyor: 0,030 ms'den 480 ms'ye. Aynı desenin Thompson simülasyonunda süre ise girdi uzunluğuyla doğrusal artıyor.

| n (girdi uzunluğu) | Naif geri izleme adımı | Python re süresi (ms) |
|---|---|---|
| 10 | 6 142 | 0,030 |
| 12 | 24 574 | 0,113 |
| 14 | 98 302 | 0,456 |
| 16 | 393 214 | 1,826 |
| 18 | 1 572 862 | 7,372 |
| 20 | 6 291 454 | 30,702 |
| 22 | 25 165 822 | 122,989 |
| 24 | 100 663 294 | 480,764 |

Thompson simülasyonu için ölçüm ise ayrı bir tabloda:

| n | Thompson süresi (ms) |
|---|---|
| 1 000 | 1,538 |
| 2 000 | 3,076 |
| 4 000 | 6,181 |
| 8 000 | 12,621 |
| 16 000 | 25,223 |

Thompson tablosunda girdi on altı kat büyüdüğünde süre de on altı kat (yaklaşık 16,4 kat) büyüyor. Bu doğrusallığın sebebi basit: her karakter için durum kümesi, desenin sabit boyutlu NFA'sı üzerinde bir kez güncellenir. Şekil 36.5 iki ölçümü birlikte gösteriyor.

![Şekil 36.5: Solda naif geri izleme adımları (log ölçek), sağda Thompson simülasyonunun süresi](gorseller/b36_redos.png)

Savunma için üç kural çıkar. Birincisi, **iç içe tekrar** ve **örtüşen alternatif** içeren desenleri gözden geçirmektir: `(a+)+`, `(a|a)*`, `(\w+\s?)+` gibi yapılar tehlikelidir. İkincisi, doğrusal zamanlı motorları tercih etmektir; RE2 gibi motorlar geri izleme yerine NFA simülasyonu kullanır ve üstel patlamayı yapısal olarak önler (genel bilgi). Üçüncüsü, girdiyi regex'e vermeden önce sınırlamaktır: Bölüm 31'de satır uzunluğuna üst sınır koymanın nedeni de budur. Bir doğrulama regex'i yalnızca makul uzunluktaki girdide çalışırsa, en kötü durum da sınırlı kalır.

Bu konunun kenarında iki dürüst not düşmek gerekir. İlki, bu bölümdeki desen bilerek seçilmiş en kötü örnektir; gerçek desenlerin çoğu bu kadar kötü değildir, ama uyarı bir şeyi değiştirmez. İkincisi, Python'un `re` modülünün bütün desenleri üstel değildir; geri izlemenin ne zaman patladığını desenin yapısı belirler. Bu yüzden kalıp tasarımında bu yapıları tanımak bir beceridir.

## 36.7 Düzenli olmayan diller ve pompalama lemması

Düzenli diller güçlü ama sınırlıdır. Sonlu bellekle yapabildikleri, sayma gerektirmeyen işlerdir. Şimdi bu sınırın gerçek olduğunu kanıtlayacağız. Dil L = {a^n b^n : n ≥ 0}: önce n tane a, sonra aynı sayıda b. Bu dil bir DFA ile tanınabilir mi?

Sezgi şöyle: DFA sonlu sayıda duruma sahiptir. Eğer çok sayıda a okuduktan sonra bu a'ların kaç tane olduğunu hatırlaman gerekiyorsa, sonlu durum yetmez; bir kutunun içinde sonsuz sayıda farklı sayıyı tutamazsın. Bu sezgiyi kesin bir kanıta dönüştüren araç **pompalama lemması** (pumping lemma) adını taşır.

**Lemma (düzenli diller için pompalama).** L düzenliyse, öyle bir p (pompalama sabiti) vardır ki her w ∈ L için |w| ≥ p ise w = xyz şeklinde yazılabilir ve şunlar sağlanır: |y| ≥ 1, |xy| ≤ p ve her i ≥ 0 için xy^i z ∈ L.

**Kanıt fikri.** L'yi tanıyan bir DFA'nın p durumu olsun. Uzunluğu p'den büyük olan bir w'yi okurken, ilk p harfi okurken en az p+1 durum ziyaret edilir (başlangıç dahil). Kutu prensibine göre bir durum iki kez ziyaret edilmiştir. Bu iki ziyaret arasındaki okunmuş parça y'dir; x, ilk ziyarete kadar okunan kısımdır, z kalan kısımdır. DFA y'yi okuduğunda aynı duruma geri döner, dolayısıyla y'yi istediğin kadar tekrar etmek (ya da hiç etmemek) aynı son durumu verir. Bu yüzden xy^i z ∈ L her i için.

**Uygulama: aⁿbⁿ dili düzenli değildir.** Varsayalım ki L'yi tanıyan bir DFA ve pompalama sabiti p var. Seçelim w = a^p b^p ∈ L; |w| = 2p ≥ p. Lemmaya göre w = xyz, |xy| ≤ p, |y| ≥ 1. İlk p harf hep a'dır, dolayısıyla y = a^k, 1 ≤ k ≤ p. Şimdi i = 0 alalım: xz = a^(p−k) b^p. Bu dizge L'de değildir, çünkü a sayısı p−k ≠ p. Ama lemma xz'nin de L'de olmasını gerektirir (i = 0). Çelişki. Demek ki böyle bir DFA yoktur ve aⁿbⁿ düzenli değildir.

Bu kanıtta dikkat edilmesi gereken iki nokta var. Birincisi, pompalama lemması bir **gerek koşuldur**: bir dili düzenli yapmaz, sadece düzensiz olduğunu göstermek için kullanılır. Yani lemmanın koşulunu sağlayan bir dil düzenli olmak zorunda değildir; ama koşulu sağlamayan bir dil kesinlikle düzenli değildir. İkincisi, kanıtta "sen seçersin" oyunu oynanır: karşı taraf p'yi verir, sen w'yi seçersin, o x, y, z'yi seçer, sen i'yi seçersin. Çelişki elde etmek için doğru w ve doğru i seçimi gerekir.

Bu sınır pratikte önemlidir. Bir protokol ayrıştırıcısı "açılan parantez sayısı kapanan kadar olmalı" gibi bir kural istiyorsa, düzenli ifadeler bunu yapamaz; bu bir yığın (stack) ya da sayaç gerektirir. Bu yüzden derleyiciler regex ile değil, yığınlı otomatlarla ya da gramerlerle çalışır. 36.10'da bu gücü göreceğiz.

## 36.8 Bağlamdan bağımsız gramerler: türetme, ağaç ve belirsizlik

Bağlamdan bağımsız gramer (CFG, context-free grammar), bir dilin üretim kurallarıyla tanımlanmasıdır. Dört parçadan oluşur: G = (V, Σ, R, S). V değişkenler (ara semboller), Σ uç semboller (terminaller), R üretim kuralları (A → α biçiminde, A ∈ V, α ∈ (V ∪ Σ)*), S başlangıç değişkenidir. Bir kuralın solunda tek bir değişken vardır; "bağlamdan bağımsız" adı buradan gelir: A'yı çevresi ne olursa olsun α ile değiştirebilirsin.

Bir dizgeyi **türetmek**, başlangıç sembolünden başlayıp kuralları art arda uygulayarak uç sembollerden oluşan dizgeye ulaşmaktır. Her adımda hangi değişkeni genişleteceğin bir seçimdir. **En sol türetme** (leftmost derivation) her zaman en soldaki değişkeni genişletir; **en sağ türetme** en sağdakini. Bir dizgenin farklı türetmeleri olabilir, ama bunların ağaç hâli, yani **türetme ağacı** (parse tree), seçimlerden bağımsız bir yapı verir: kök başlangıç değişkeni, iç düğümler uygulanan kuralların sol tarafları, yapraklar dizgenin harfleridir.

Bir gramer, bir dizgenin **iki farklı türetme ağacı** olmasını sağlıyorsa **belirsiz** (ambiguous) denir. Belirsizlik bir dil özelliği değil, bir gramer özelliğidir: aynı dili daha az belirsiz bir gramerle anlatmak çoğu zaman mümkündür. Ama bazı diller için (ör. belirli taşmalı diller) her gramer belirsizdir; bu **kendiliğinden belirsiz dil** (inherently ambiguous language) kavramıdır.

Basit bir aritmetik gramer alalım: E → E + E | E * E | n. Burada n bir sayıyı temsil eden uç sembol. Dizge n + n * n'in iki türetme ağacı var: birinde + en üstte (n + (n * n)), diğerinde * en üstte ((n + n) * n). Şekil 36.6 iki ağacı gösteriyor. n yerine sırasıyla 1, 2, 3 yazarsak değer de değişir: birinci ağaç 1 + 2·3 = 7, ikincisi (1 + 2)·3 = 9 verir. Derleyici için bu kabul edilemez, çünkü aynı kaynak kodun iki farklı anlamı olur.

![Şekil 36.6: n + n * n dizgesinin iki türetme ağacı: belirsizlik](gorseller/b36_turetme.png)

Bu gramerde kaç türetme ağacı olduğunu saymak için bir yöntem yazalım. Kural: w[i..j) dilimini türeten A değişkeninin ağaç sayısı, A'nın kurallarının her biri için, o kuralın sağ tarafındaki sembollerin dilimleri bölerek türetmesinin sayılarının çarpımlarının toplamıdır. Bu bir **dinamik programlama** tablosudur (Bölüm 16'daki aralık DP'sinin aynısı): alt problemler (A, i, j) üçlüleridir ve her biri bir kez hesaplanır. ε-üretimi ve birim döngüsü (A → B, B → A) olmayan gramerlerde bu özyineleme sonlanır.

```python
# cfg.py: bağlamdan bağımsız gramerde türetme ağacı sayımı
import random
from functools import lru_cache

# Belirsiz: E -> E + E | E * E | n
G_ISLEM = {"E": [("E", "+", "E"), ("E", "*", "E"), ("n",)]}
# Belirsiz asılı else: S -> iEtS | iEtSeS | a ; E -> b
G_ASILI = {"S": [("i", "E", "t", "S"),
                 ("i", "E", "t", "S", "e", "S"), ("a",)],
           "E": [("b",)]}
# Tek ağaçlı: E -> T + E | T ; T -> F * T | F ; F -> n | ( E )
G_TEK = {"E": [("T", "+", "E"), ("T",)],
         "T": [("F", "*", "T"), ("F",)],
         "F": [("n",), ("(", "E", ")")]}


def agac_sayisi(G, bas, w):
    """w kaç farklı türetme ağacıyla bas'tan türetilir?
    G'de ε-üretimi ve birim döngüsü olmadığı varsayılır."""
    @lru_cache(maxsize=None)
    def A(X, i, j):              # X, w[i:j]'yi kaç ağaçla türer?
        if X not in G:           # uç sembol: tek harf
            return int(j == i + 1 and w[i] == X)
        return sum(B(rhs, i, j) for rhs in G[X])

    @lru_cache(maxsize=None)
    def B(seq, i, j):            # seq dizisi w[i:j]'yi kaç ağaçla?
        if len(seq) == 1:
            return A(seq[0], i, j)
        return sum(A(seq[0], i, k) * B(seq[1:], k, j)
                   for k in range(i + 1, j))

    return A(bas, 0, len(w))
```

Dosyanın ilk parçası üç gramer tanımlar ve sayım fonksiyonunu içerir. `agac_sayisi` iki yardımcı fonksiyonu (A: değişken, B: sağ taraf dizisi) `lru_cache` ile önbelleğe alır. `B` tek sembollü dizide doğrudan A'ya düşer; daha uzunsa ilk sembolü w[i..k) ile, kalanı w[k..j) ile eşler ve çarpımları toplar. `G_ISLEM` belirsiz, `G_TEK` ise belirsizliği giderilmiş gramerdir; bunu birazdan göreceğiz.

```python
def agaclar(G, bas, w):
    """Tüm ağaçlar: (X, (alt ağaçlar...)); uç harf düz metin."""
    def A(X, i, j):
        if X not in G:
            return [X] if j == i + 1 and w[i] == X else []
        return [(X, o) for rhs in G[X] for o in B(rhs, i, j)]

    def B(seq, i, j):
        if len(seq) == 1:
            return [(t,) for t in A(seq[0], i, j)]
        return [(t,) + kal for k in range(i + 1, j)
                for t in A(seq[0], i, k) for kal in B(seq[1:], k, j)]

    return A(bas, 0, len(w))
```

`agaclar` aynı özyinelemeyi kullanarak ağaçların kendisini üretir (küçük girdiler için). Ağaç, (etiket, alt ağaçlar) demetleriyle temsil edilir; uç harfler düz metin olarak durur. Sayım ile listeleme yan yana koşulunca, sayının listenin uzunluğuna eşit olduğunu görebilirsin.

```term
$ python cfg.py
n+n*n belirsiz: 2 tek: 1
n+n belirsiz: 1 tek: 1
n*n+n*n belirsiz: 5 tek: 1
asılı else: 2
('E', (('E', ('n',)), '+', ('E', (('E', ('n',)), '*', ('E', ('n',))))))
('E', (('E', (('E', ('n',)), '+', ('E', ('n',)))), '*', ('E', ('n',))))
dogrulanan: 3000
```

Çıktı belirsizliği somut gösterir. "n+n*n" için belirsiz gramer 2 ağaç, tek ayrıştırıcı grameri 1 ağaç verir. "n*n+n*n" için belirsiz gramer 5 ağaç üretir: üç operatörlü bir ifadede (dört n, üç operatör) ağaç sayısı 5'tir; genel olarak n operatörde Catalan sayısı kadar ağaç çıkar. "asılı else" satırını birazdan açıklayacağız. Çıktının son iki satırı ağaçların kendisidir: ilk demet `n+n*n`'in + en üstte olan ağacıdır.

Belirsizliği gidermek için öncelik ve birleşme katmanları kullanılır. Düşünce şudur: `*` `+`'tan daha sıkı bağlanır, dolayısıyla `*` terimi (terim) `+` ifadesinin (ifade) içinde yer almalıdır. Bunu katmanları ayrı değişkenlerle yazarak elde ederiz: E (toplamalar) → T (çarpmalar) → F (çarpanlar, n ya da parantezli ifade). Bu gramer, Bölüm 15'teki özyinelemeli iniş ayrıştırıcısının doğrudan karşılığıdır: her değişken bir fonksiyondur.

```python
def ayristirici_tek(w):
    """G_TEK için özyinelemeli iniş tanıyıcı (Bölüm 15)."""
    konum = [0]

    def bak():
        return w[konum[0]] if konum[0] < len(w) else None

    def ileri(c):
        if bak() != c:
            raise SyntaxError(c)
        konum[0] += 1

    def E():
        T()
        if bak() == "+":
            ileri("+")
            E()

    def T():
        F()
        if bak() == "*":
            ileri("*")
            T()

    def F():
        if bak() == "n":
            ileri("n")
        else:
            ileri("(")
            E()
            ileri(")")

    try:
        E()
    except SyntaxError:
        return False
    return konum[0] == len(w)
```

`G_TEK` gramerinde E → T + E, T → F * T ve F → n | (E) kuralları var. Bu yapı sağ özyinelemeli bir gramerdir, çünkü + ve * sağa doğru bağlanır: n + n + n dizgesi n + (n + n) olarak ayrıştırılır. Toplama ve çarpma işlemleri matematiksel olarak birleşmeli olduğu için bu sayısal sonucu değiştirmez; ama `-` ve `/` gibi birleşmeli olmayan operatörlerde sağ özyineleme yanlış anlam verir. Bu yüzden gerçek derleyiciler çoğunlukla sol özyinelemeli gramer kullanır ve ayrıştırıcıyı döngüyle yazar; bu, Bölüm 37'de ayrıntılı göreceğimiz bir karardır. Yukarıdaki `ayristirici_tek` ise bu gramerin yalnızca tanıma yönünü özyinelemeli iniş ile yapar ve sonucu sayımla karşılaştırır.

```python
def dogrula(seed=36, n=3000):
    rng = random.Random(seed)
    for _ in range(n):
        w = "".join(rng.choice("n+*()")
                    for _ in range(rng.randint(1, 9)))
        dogru = ayristirici_tek(w)
        k = agac_sayisi(G_TEK, "E", w)
        assert k == (1 if dogru else 0), w   # tek ağaç
    return n


if __name__ == "__main__":
    for w in ["n+n*n", "n+n", "n*n+n*n"]:
        print(w, "belirsiz:", agac_sayisi(G_ISLEM, "E", w),
              "tek:", agac_sayisi(G_TEK, "E", w))
    print("asılı else:", agac_sayisi(G_ASILI, "S", "ibtibtaea"))
    for t in agaclar(G_ISLEM, "E", "n+n*n"):
        print(t)
    print("dogrulanan:", dogrula())
```

`dogrula` rastgele 3000 dizgede iki yöntemi karşılaştırır: tanıyıcı kabul ederse sayım tam 1, reddederse 0 olmalı. Çıktının son satırı bunun tutulduğunu gösterir.

Şimdi "asılı else" (dangling else) problemine bakalım; bu, programlama dillerinin tarihindeki en bilinen belirsizliklerden biridir. Gramer:

- S → i E t S | i E t S e S | a
- E → b

Burada i (if), t (then), e (else), a (diğer ifadeler), b (koşul) uç sembollerdir. `ibtibtaea` dizgesi iki farklı şekilde okunur: birinde else ilk if'e, diğerinde ikinci if'e ait olur. Hangisi doğru? Kural koymadan gramer bunu söyleyemez; C ve Java gibi dillerde kural "else en yakın if'e bağlanır" biçiminde yazılır. Bu bir **anlamsal** karardır ve gramerin kendisi bunu bilmez. Çözüm, gramerde "eşleşmemiş if" ve "eşleşmiş if" ayrımı yapmaktır; bu, sözdizimi tasarımının bir parçasıdır.

## 36.9 BNF ve EBNF: gramerleri yazmak için notasyon

Gramerleri yazmanın standart yolu BNF (Backus–Naur Form) notasyonudur. Kuralın solu `<ad>` ile, sağı `::=` sonrasında yazılır. Alternatifler `|` ile ayrılır. Gramer bölüm 36.8'deki aritmetik ifade için BNF olarak şöyle görünür:

```text
<ifade>  ::= <terim> | <ifade> "+" <terim>
<terim>  ::= <carpan> | <terim> "*" <carpan>
<carpan> ::= "n" | "(" <ifade> ")"
```

Bu biçim, sol özyinelemeli olduğu için öncelik ve birleşme bilgisini açıkça taşır. EBNF (Extended BNF) aynı fikri üç kısayolla kısaltır: `{ ... }` sıfır veya daha fazla tekrar, `[ ... ]` isteğe bağlı, `( ... )` gruplama. Aynı gramer EBNF'te:

```text
ifade  = terim, { "+", terim } ;
terim  = carpan, { "*", carpan } ;
carpan = "n" | "(", ifade, ")" ;
```

Bu notasyon, döngü kullanan ayrıştırıcıya doğrudan çevrilebilir: `{ ... }` bir `while`, `[ ... ]` bir `if`'tir. Bu yüzden EBNF, dil tasarımında ve belgelemede yaygındır. Gerçek bir dilin resmî tanımı çoğunlukla EBNF'te yazılır. CPython 3.9'dan beri ayrıştırıcısı PEG (Parsing Expression Grammar) tabanlıdır ve gramer dosyası da buna yakın bir notasyonla yazılır (genel bilgi); PEG'in sıralı seçim (ordered choice) özelliği belirsizliği ortadan kaldırmak için tasarlanmıştır, ama bu başka bir konu.

Mülakatta "BNF ile EBNF arasındaki fark nedir?" sorusu sık gelir. Cevap şudur: ikisi aynı güçtedir, EBNF yalnızca yazım kolaylığı sağlar; hiçbir EBNF kuralı BNF'te yazılamayacak bir dili tanımlamaz.

## 36.10 Yığınlı otomat (PDA): sayma yeteneğinin bedeli

Düzenli dillerin sınırını gördük: aⁿbⁿ'i tanımak için sayma gerekir. Yığınlı otomat (PDA, pushdown automaton) bu eksiği bir yığınla giderir. Bir PDA, sonlu kontrol birimi (durumlar) ve sonsuz (ama yalnız sona ekleme-çıkarma yapılan) bir yığından oluşur. Her adımda bir girdi harfi ve yığının tepesine bakarak, durumunu değiştirir, yığına bir sembol iter ya da yığından bir sembol çıkarır. Resmî tanımı bir yedili (Q, Σ, Γ, δ, q0, Z0, F) olarak yazılır; burada Γ yığın alfabesi ve Z0 yığının başlangıç sembolüdür (genel bilgi).

Yığın, Bölüm 8'deki yığın veri yapısının aynısıdır: son giren ilk çıkar. Bölüm 8'de ifade değerlendirmeyi postfix ile yığın kullanarak yaptık; parantez dengeleme örneğinde açılan parantezleri yığına itip kapanan parantezde tepeye bakmıştık. Bu bölümde aynı fikri bir dilin tanıyıcısı olarak kullanıyoruz.

Dengeli parantez dili, yani açılan ve kapanan parantezlerin doğru iç içe geçtiği dizgeler, bağlamdan bağımsız bir dildir. Tek tür parantez için bir sayaç yeter (sayaç bir yığın gibi davranır, ama tek sembol içerir); iki ya da daha fazla tür için yığına ihtiyaç vardır, çünkü hangi parantezin açık olduğunu hatırlamak gerekir. Örneğin `([)]` dizgesi bütün sayıları dengelese de yanlıştır: `[`, `(`'den sonra açıldığı için `)` önce `]` ile kapanmalıdır.

Şekil 36.7, süslü, köşeli ve yuvarlak parantezlerden oluşan `{[()]}` dizgesinde yığının her adımdaki durumunu gösteriyor.

![Şekil 36.7: Süslü, köşeli ve yuvarlak parantezlerden oluşan bir dizgede yığının her adımdaki durumu](gorseller/b36_pda_yigin.png)

Kodu yazalım. `dengeli.py`, yığınlı tanıyıcıyı ve izini üretir; doğrulama için bağımsız bir oracle kullanır: (), [] ve {} çiftlerini tekrar tekrar silmek. Bu yeniden yazma sistemi, dizge tamamen silinebiliyorsa dengelidir. Silme kuralı doğru sırayla (sadece komşu çiftler) uygulandığında dengeli dizgeler her zaman boşa iner ve dengesiz dizgeler boşa inemez; bu, yığın algoritmasından tamamen bağımsız bir doğrulamadır.

```python
# Yığınlı tanıyıcı (PDA mantığı): üç tür parantez dengesi.
from itertools import product
import random

KARSI = {")": "(", "]": "[", "}": "{"}


def yigin_tani(s):
    """Kabul/red ve her adımda (harf, yığın) izi döndürür."""
    yigin, iz = [], []
    for c in s:
        if c in "([{":
            yigin.append(c)
        elif c in KARSI:
            if not yigin or yigin[-1] != KARSI[c]:
                iz.append((c, "".join(yigin) + " <- HATA"))
                return False, iz
            yigin.pop()
        else:
            raise ValueError("bilinmeyen harf %r" % c)
        iz.append((c, "".join(yigin)))
    return (not yigin), iz


def yeniden_yaz(s):
    """Bağımsız oracle: (), [], {} çiftlerini tekrar tekrar sil."""
    while True:
        t = s.replace("()", "").replace("[]", "").replace("{}", "")
        if t == s:
            return s == ""
        s = t
```

`yigin_tani` her açılan parantezi yığına iter ve her kapanan parantezde tepeyle eşleşip eşleşmediğine bakar; eşleşmezse hata izi ile döner. Döndürdüğü `iz` listesi, her adımda harf ile yığının o anki içeriğini tutar; bu, Şekil 36.7'nin verisidir. `yeniden_yaz` ise yalnızca çiftleri silen basit bir döngüdür; yığın kullanmaz.

```python
def dogrula(seed=36, n_rastgele=5000):
    sinanan = 0
    for n in range(0, 7):
        for t in product("()[]{}", repeat=n):
            w = "".join(t)
            assert yigin_tani(w)[0] == yeniden_yaz(w), w
            sinanan += 1
    rng = random.Random(seed)
    for _ in range(n_rastgele):
        n = rng.randint(0, 30)
        w = "".join(rng.choice("()[]{}") for _ in range(n))
        assert yigin_tani(w)[0] == yeniden_yaz(w), w
        sinanan += 1
    return sinanan


if __name__ == "__main__":
    for w in ["{[()]}", "([)]", "((]"]:
        ok, iz = yigin_tani(w)
        print(w, "kabul" if ok else "red")
        for harf, yigin in iz:
            print("   %s  yığın=%r" % (harf, yigin))
    print("sinanan:", dogrula())
```

`dogrula` her uzunluğa kadar (en fazla 6) altı sembollük bütün dizgeleri ve beş bin rastgele dizgeyi iki yöntemle karşılaştırır. Ana programın çıktısı üç örnek için izi gösterir.

```term
$ python dengeli.py
{[()]} kabul
   {  yığın='{'
   [  yığın='{['
   (  yığın='{[('
   )  yığın='{['
   ]  yığın='{'
   }  yığın=''
([)] red
   (  yığın='('
   [  yığın='(['
   )  yığın='([ <- HATA'
((] red
   (  yığın='('
   (  yığın='(('
   ]  yığın='(( <- HATA'
sinanan: 60987
```

`([)]` örneği hatanın tam nerede tespit edildiğini gösterir: `)` geldiğinde yığının tepesi `[`'dir, ama beklenen `(`'dir. Bu noktada dizge, daha fazla okumadan reddedilir. Ayrıca `((]` dizgesinde, `]` geldiğinde yığının tepesinin `(` olduğuna dikkat et: hatayı yakalayan kural, tepenin türünü kontrol eder, sayısını değil.

Bu bölümün kavramsal özeti şudur: düzenli diller için sonlu durum yeterliyken, dengeli parantez için yığın gerekir. Ama yığın da her dili tanıyamaz: PDA'lar tam olarak bağlamdan bağımsız dilleri tanır (genel bilgi). Bu, Chomsky hiyerarşisinin bir sonraki basamağıdır; 36.12'de bütününe bakacağız.

## 36.11 CYK algoritması ve FIRST/FOLLOW kümeleri

Bir bağlamdan bağımsız gramer verildiğinde, bir dizgenin o gramerle türetilip türetilemeyeceğine polinom sürede karar verebilmek isteriz. Bu soru ayrıştırıcıların temel sorusudur. Cocke–Younger–Kasami (CYK) algoritması bunu, gramerin **Chomsky normal formu** (CNF) üzerinde, dinamik programlamayla yapar.

CNF'de her üretim ya A → BC (iki değişken) ya da A → a (tek uç sembol) biçimindedir; isteğe bağlı olarak S → ε da eklenebilir. Her bağlamdan bağımsız gramer (ε içermeyen kısmı) CNF'ye çevrilebilir; dönüşüm standart bir algoritmadır ve gramerin boyutunu en fazla polinom katına çıkarır (genel bilgi). CNF'nin güzelliği, her kuralın tam olarak iki çocuklu bir düğüm (ya da bir yaprak) üretmesidir: ağaç ikili bir yapı olur.

Algoritmanın fikri şu tabloyla verilir: T[i][j], w[i..j] alt dizgisini türetebilen değişkenlerin kümesidir. Taban durum: T[i][i] = {A : A → w_i}. Özyineleme: uzunluğu artan aralıklar için, A → BC kuralı ve bir k (i ≤ k < j) noktası için B ∈ T[i][k] ve C ∈ T[k+1][j] ise A ∈ T[i][j]. Sonuç: S ∈ T[0][n−1] ise dizge gramerle türetilebilir. Tablo n² hücredir ve her hücre O(n·|G|) işle doldurulur; toplam O(n³·|G|).

Bu, Bölüm 16'daki aralık DP'sinin (matris zinciri çarpımı, 16.9) aynı kalıbıdır: bir aralığın çözümü, daha kısa iki aralığın çözümlerinden bir kesme noktası üzerinden kurulur. Tabloyu sayı yerine derleme sayısıyla doldurursan, aynı algoritma türetme ağacı sayısını verir; 36.8'de sayıdığımız şey buydu.

Dengeli parantez dilini CNF'de yazalım. Gramer şöyledir:

- S → S S | L R | L T
- T → S R
- L → (
- R → )

Bu gramer boş olmayan dengeli dizgeleri üretir. S → L T ve T → S R, "açılan parantez, dengeli bir dizge, kapanan parantez" yapısını verir; S → S S ise iki dengeli dizgenin ardışık gelmesini sağlar. Gramer belirsizdir (bunu birazdan göreceğiz), ve tam da bu yüzden iyi bir sınavdır: CYK belirsiz gramerlerle de çalışır, sadece sayı birden fazla çıkar.

```python
# CYK: Chomsky normal formda (CNF) tanıma ve türetme ağacı sayımı.
from itertools import product
import random

# Dengeli parantez dili (boş olmayan), CNF:
#   S -> S S | L R | L T     T -> S R     L -> (     R -> )
CNF = {
    "S": [("S", "S"), ("L", "R"), ("L", "T")],
    "T": [("S", "R")],
    "L": ["("],
    "R": [")"],
}


def cyk(G, bas, w):
    """T[i][j]: w[i..j]'yi türeten {değişken: ağaç sayısı}."""
    n = len(w)
    T = [[{} for _ in range(n)] for _ in range(n)]
    for i, harf in enumerate(w):              # uzunluk 1: A -> harf
        for A, uretimler in G.items():
            if harf in uretimler:
                T[i][i][A] = 1
    for uz in range(2, n + 1):                # kısa aralıktan uzuna
        for i in range(n - uz + 1):
            j = i + uz - 1
            for k in range(i, j):   # sol [i..k], sağ [k+1..j]
                for A, uretimler in G.items():
                    for u in uretimler:
                        if isinstance(u, str):
                            continue          # uç üretim: atla
                        B, C = u
                        sol = T[i][k].get(B, 0)
                        sag = T[k + 1][j].get(C, 0)
                        if sol and sag:
                            T[i][j][A] = T[i][j].get(A, 0) + sol * sag
    return T, (T[0][n - 1].get(bas, 0) if n else 0)
```

`cyk` fonksiyonu tabloyu bir sözlük listesi olarak tutar: T[i][j] bir sözlük, değişkenden ağaç sayısına eşler. Taban durum döngüsü uzunluk-1 hücreleri doldurur. Ana döngü uzunluğu 2'den n'e artırır ve her (i, j) aralığı için bütün kesme noktalarını ve kuralları dener; sayılar çarpılıp toplanır. Dönüş değeri hem tablo hem S için ağaç sayısıdır.

```python
def dengeli_mi(w):
    """Bağımsız doğru: tek tür parantez için sayaçla kontrol."""
    sayac = 0
    for c in w:
        sayac += 1 if c == "(" else -1
        if sayac < 0:
            return False
    return sayac == 0


def dogrula(maks=10):
    sinanan = 0
    for n in range(1, maks + 1):
        for t in product("()", repeat=n):
            w = "".join(t)
            _, sayi = cyk(CNF, "S", w)
            assert (sayi > 0) == dengeli_mi(w), w
            sinanan += 1
    return sinanan


if __name__ == "__main__":
    w = "()()()"
    T, sayi = cyk(CNF, "S", w)
    print("ağaç sayısı:", sayi)
    for i in range(len(w)):
        print(" ".join(str(T[i][j].get("S", 0)) if j >= i else "."
                       for j in range(len(w))))
    print("sinanan:", dogrula())
```

`dengeli_mi` bağımsız bir doğruluk ölçütüdür: bir sayaç tutar, sayaç negatife inerse ya da sonda sıfırdan farklıysa reddeder. `dogrula` bütün uzunluk-10'a kadar dizgeler için CYK'nın kabul kararını bu sayaçla karşılaştırır. Ana program "()()()" dizgesini çalıştırır ve tabloyu basar:

```term
$ python cyk.py
ağaç sayısı: 2
0 1 0 1 0 2
. 0 0 0 0 0
. . 0 1 0 1
. . . 0 0 0
. . . . 0 1
. . . . . 0
sinanan: 2046
```

Tablo satır i, sütun j hücresindeki S sayısını gösterir (boş yerler nokta). Tablo yalnız S sayılarını gösteriyor; L ve R değişkenleri köşegendeki taban hücrelerinde durur, burada gösterilmez. Hücre (0,5) iki S sayısı içeriyor: bu, "()()()" dizgesinin iki farklı türetme ağacı olduğu anlamına gelir. Bunu Çözümlü Örnek 4'te hücre hücre izleyeceğiz.

### FIRST ve FOLLOW: ayrıştırıcının iki gözü

CYK tanıma yapar ama her zaman pratik değildir; derleyiciler **öngörülü** (predictive) ayrıştırıcılar kullanır: girdinin bir sonraki sembolüne bakarak, tek bir kural seçerler. Bu seçimi yapabilmek için iki küme gerekir.

- **FIRST(X):** X'ten türetilebilen dizgelerin başında görünebilen uç sembollerin kümesi. X ε türetebiliyorsa ε da dahildir.
- **FOLLOW(A):** Bir türetmede A'nın hemen sağında görünebilen uç sembollerin kümesi. Başlangıç değişkeninin FOLLOW kümesine bitiş işareti $ eklenir.

Bu kümeler, sabit nokta algoritmasıyla hesaplanır. FIRST için: bir terminal a ise FIRST(a) = {a}; A → X1 X2 ... Xk kuralında, X1'in FIRST kümesinin ε olmayan kısmı FIRST(A)'ya girer; X1 ε türetebiliyorsa X2'ninki de girer, ve böyle devam eder; bütün Xi ε türetebiliyorsa ε da FIRST(A)'ya eklenir. FOLLOW için: A → αBβ kuralında FIRST(β)'nın ε olmayan kısmı FOLLOW(B)'ye girer; β ε türetebiliyorsa (ya da β boşsa) FOLLOW(A) da FOLLOW(B)'ye eklenir. Değişiklik kalmayana kadar tekrarlanır.

Örnek olarak ifade gramerinin LL(1)'e uygun biçimini alalım. Sol özyineleme kaldırılmış, E' ve T' yardımcı değişkenleri eklenmiştir:

- E → T E'
- E' → + T E' | ε
- T → F T'
- T' → * F T' | ε
- F → ( E ) | id

```python
# FIRST ve FOLLOW kümeleri (sabit noktaya kadar).
EPS = "ε"
G = {
    "E":  [["T", "E'"]],
    "E'": [["+", "T", "E'"], [EPS]],
    "T":  [["F", "T'"]],
    "T'": [["*", "F", "T'"], [EPS]],
    "F":  [["(", "E", ")"], ["id"]],
}
BAS = "E"


def ilk_dizi(seq, first):
    """Bir sembol dizisinin FIRST kümesi (ε dahil olabilir)."""
    sonuc = set()
    for X in seq:
        if X == EPS:
            continue
        f = first[X] if X in G else {X}
        sonuc |= f - {EPS}
        if EPS not in f:
            return sonuc
    sonuc.add(EPS)                 # her sembol ε türetebiliyorsa
    return sonuc
```

Bu parça gramerin kendisini ve FIRST'ü hesaplayan `ilk_dizi` fonksiyonunu içerir. `ilk_dizi` bir sembol dizisinin FIRST kümesini hesaplar: bir sembol ε içermiyorsa döngüden çıkar; hepsi ε türetebiliyorsa sonuca ε eklenir. ε'yi ayrı bir sabit (`EPS`) olarak tutmak, "boş üretim" ile "hiçbir şey yok" arasındaki farkı açıkça korur.

```python
def ilk_kumeleri(G):
    first = {A: set() for A in G}
    degisti = True
    while degisti:
        degisti = False
        for A, uretimler in G.items():
            for u in uretimler:
                yeni = ilk_dizi(u, first)
                if not yeni <= first[A]:
                    first[A] |= yeni
                    degisti = True
    return first


def takip_kumeleri(G, bas, first):
    follow = {A: set() for A in G}
    follow[bas].add("$")
    degisti = True
    while degisti:
        degisti = False
        for A, uretimler in G.items():
            for u in uretimler:
                for i, B in enumerate(u):
                    if B not in G:
                        continue
                    kalan = ilk_dizi(u[i + 1:], first)
                    yeni = follow[B] | (kalan - {EPS})
                    if EPS in kalan:
                        yeni |= follow[A]
                    if yeni != follow[B]:
                        follow[B] = yeni
                        degisti = True
    return follow
```

`ilk_kumeleri` her kuralı sabit noktaya kadar tarar; `takip_kumeleri` FOLLOW'u ve başlangıçta $ işaretini hesaplar. İkisi de yukarıdaki kuralların birebir kodudur.

```term
$ python ll1.py
FIRST(E) = ['(', 'id']
FIRST(E') = ['+', 'ε']
FIRST(T) = ['(', 'id']
FIRST(T') = ['*', 'ε']
FIRST(F) = ['(', 'id']
FOLLOW(E) = ['$', ')']
FOLLOW(E') = ['$', ')']
FOLLOW(T) = ['$', ')', '+']
FOLLOW(T') = ['$', ')', '+']
FOLLOW(F) = ['$', ')', '*', '+']
```

Çıktı birkaç şeyi açık eder. FIRST(E) ve FIRST(F) yalnız ( ve id içerir, çünkü bu iki yolla başlamak zorundadır. FIRST(E') içinde ε vardır, çünkü E' → ε kuralı var. FOLLOW(T)'nin içinde + bulunuyor: E → T E' kuralında T'nin sağında E' vardır, E'nin FIRST'ü ise + (ve ε) içerir; ε olduğu için FOLLOW(E) da FOLLOW(T)'ye girer; FOLLOW(E) ise ) ve $'dır. Bu kümeler, ayrıştırıcının "şimdi hangi kuralı seçeyim?" sorusunu cevaplar: girdinin sonraki sembolü FIRST(α) içindeyse α kuralını seçersin; ε kuralı ise sonraki sembol FOLLOW(A) içindeyse seçilir. Bu seçimlerin tablosu LL(1) tablosudur ve Bölüm 37'de, derleyici bağlamında kuracağız.

## 36.12 Chomsky hiyerarşisi: dört sınıf, dört makine

Noam Chomsky (1956) gramerleri üretim kurallarının biçimine göre dört sınıfa ayırdı. Her sınıf bir öncekini kapsar ve her birinin bir tanıyıcı makine modeli vardır. Bu hiyerarşi, bu bölümün iskeletidir.

| Sınıf | Üretim biçimi | Tanıyıcı | Örnek dil |
|---|---|---|---|
| Tip 3: düzenli | A → aB veya A → a | DFA, NFA, düzenli ifade | a*b, sonu abb olan dizgeler |
| Tip 2: bağlamdan bağımsız | A → α (sol taraf tek değişken) | Yığınlı otomat (PDA) | aⁿbⁿ, dengeli parantez |
| Tip 1: bağlama duyarlı | αAβ → αγβ, γ boş değil | Doğrusal sınırlı otomat (LBA) | aⁿbⁿcⁿ |
| Tip 0: özyinelemeli sayılabilir | Kısıt yok | Turing makinesi | Durma problemi kümesi |

Şekil 36.8 bu sınıfları iç içe kümeler olarak gösteriyor.

![Şekil 36.8: Chomsky hiyerarşisi: düzenli ⊂ bağlamdan bağımsız ⊂ bağlama duyarlı ⊂ özyinelemeli sayılabilir](gorseller/b36_chomsky.png)

Kapsamaların hepsi kesindir (genel bilgi): her düzenli dil bağlamdan bağımsızdır, ama aⁿbⁿ bağlamdan bağımsız olup düzenli değildir (36.7). aⁿbⁿcⁿ dili bağlama duyarlıdır ama bağlamdan bağımsız değildir; bunu gösterme yöntemi pompalama lemmasına benzer ama daha karmaşıktır. Bağlama duyarlı dillerin tümü özyinelemelidir, yani üyelik için her zaman duran bir karar algoritması vardır. Özyinelemeli sayılabilir diller ise yalnızca tanınabilir: onları kabul eden bir makine vardır, ama reddeden makine olması gerekmez (36.13).

Sınıflar arasındaki fark yalnızca teorik değildir; karar verme karmaşıklığına yansır (genel bilgi). Düzenli bir dizgenin bir DFA ile kontrolü doğrusal zamanda, bağlamdan bağımsız bir dizgenin CYK ile kontrolü O(n³) zamanda yapılabilir (daha iyi algoritmalar bilinir). Bağlama duyarlı dillerin üyelik sorusu PSPACE-tamdır; özyinelemeli sayılabilir dillerde ise, 36.13'te göreceğin gibi, üyelik sorusu genel olarak karar verilemez.

Mühendislik açısından en öğretici örnek, derleyicilerde bağlamın nasıl girdiğidir. C dilinde `a * b;` satırı, `a` bir tipse bir işaretçi tanımıdır; `a` bir değişkense bir çarpma ifadesidir. Gramer bu iki okumayı ayıramaz; ayırt etmek için sembol tablosuna, yani bağlama bakmak gerekir. Bu yüzden derleyici, sözdizimi için bağlamdan bağımsız bir gramer, anlamsal kontroller için bağlamı kullanan ek bir aşama kullanır. Bu ayrım Bölüm 37'nin ana konularından biridir.

## 36.13 Turing makinesi ve durma problemi

Turing makinesi (TM), sonsuz uzunlukta bir bant, bantı okuyup yazabilen bir başlık ve sonlu bir durum kümesinden oluşur. Her adımda başlık, bulunduğu hücredeki sembole ve mevcut duruma göre bir sembol yazar, sola ya da sağa hareket eder ve yeni bir duruma geçer. Resmî tanım bir yedilidir (Q, Σ, Γ, δ, q0, _, F); burada _ boş hücre sembolü ve F durdurma durumlarıdır (genel bilgi). Church–Turing tezi (genel bilgi), etkin olarak hesaplanabilen her fonksiyonun bir TM ile hesaplanabileceğini söyler; bu bir tanımdan çok, hesaplanabilirlik sezgisinin doğrulanmış bir ifadesidir.

Bir TM'nin ne kadar güçlü olduğunu görmek için küçük bir örnek yazalım: bir ikili sayıyı 1 artıran makine. Algoritma sağdan sola taşıyı yayar: sonda 1 gelirse 0 yazıp sola taşır, 0 gelirse 1 yazıp durur. Başlık önce sağa gider, sonu bulur, sonra geri döner.

Geçiş tablosu (durum, okunan sembol) → (yazılacak, hareket, yeni durum) biçimindedir:

- (q0, 0) → (0, R, q0) ve (q0, 1) → (1, R, q0): bütün sayıyı sağa doğru tara.
- (q0, _) → (_, L, q1): sona gelince geri dön ve taşımaya başla.
- (q1, 1) → (0, L, q1): 1 + 1 = 0 taşı, sola devam.
- (q1, 0) → (1, L, dur): 0 + 1 = 1, bitir.
- (q1, _) → (1, L, dur): sayının başından taşarsan yeni bir basamak aç.

Makinenin sayıyı gerçekten 1 artırdığını görmek için 1011 (11) dizgesini çalıştıralım. Her satır bir adımın sonrasıdır: durum, bant (−1. konumdan 4. konuma kadar) ve başlığın konumu.

```python
# Turing makinesi simülatörü: ikili sayıyı 1 artırır.
# Geçiş: (durum, okunan) -> (yazılacak, hareket, yeni durum)
DELTA = {
    ("q0", "0"): ("0", "R", "q0"),     # sağa git, sonu bul
    ("q0", "1"): ("1", "R", "q0"),
    ("q0", "_"): ("_", "L", "q1"),     # sonda: geri dön
    ("q1", "1"): ("0", "L", "q1"),     # 1 + 1 = 0, taşı sürer
    ("q1", "0"): ("1", "L", "dur"),    # 0 + 1 = 1, dur
    ("q1", "_"): ("1", "L", "dur"),    # baştan taştı: yeni basamak
}


def calistir(girdi, adim_siniri=10000):
    """Sonucu (boşlukları atılmış bant) ve adım sayısını döndürür."""
    bant = dict(enumerate(girdi))
    kafa, durum, adim = 0, "q0", 0
    while durum != "dur":
        sembol = bant.get(kafa, "_")
        yaz, hareket, yeni = DELTA[(durum, sembol)]
        bant[kafa] = yaz
        kafa += 1 if hareket == "R" else -1
        durum = yeni
        adim += 1
        if adim > adim_siniri:
            raise RuntimeError("durmadı")
    son = [bant.get(i, "_") for i in range(min(bant), max(bant) + 1)]
    return "".join(son).strip("_"), adim
```

Geçiş tablosu bir sözlüktür ve `calistir` tek döngüde makineyi çalıştırır. Döngüde `adim_siniri`, yanlışlıkla sonsuz döngüye giren bir makineyi yakalamak için bir güvenlik kuşağıdır; bu, durma probleminin pratikteki yüzüdür.

```python
def izle(girdi):
    """Her adımda (durum, bant metni, başlık konumu) döndürür."""
    bant = dict(enumerate(girdi))
    kafa, durum, iz = 0, "q0", []
    while durum != "dur":
        iz.append((durum, dict(bant), kafa))
        sembol = bant.get(kafa, "_")
        yaz, hareket, yeni = DELTA[(durum, sembol)]
        bant[kafa] = yaz
        kafa += 1 if hareket == "R" else -1
        durum = yeni
    iz.append((durum, dict(bant), kafa))
    return iz
```

`izle` her adımda bandın kopyasını saklar. Kopya almak önemlidir: sözlük bir referanstır ve kopya alınmazsa bütün satırlar son hâlini gösterirdi. Bu, dikkat edilmesi gereken küçük ama gerçek bir tuzaktır.

```python
def dogrula(n_max=1000):
    for n in range(0, n_max + 1):
        sonuc, _ = calistir(format(n, "b"))
        assert sonuc == format(n + 1, "b"), n
    return n_max + 1


if __name__ == "__main__":
    for durum, bant, kafa in izle("1011"):
        son = [bant.get(i, "_") for i in range(-1, 5)]
        print("%-4s %s  kafa=%2d" % (durum, "".join(son), kafa))
    print("1011 + 1 =", calistir("1011"))
    print("dogrulanan:", dogrula())
```

`dogrula` 0'dan 1000'e kadar bütün sayılar için makinenin sonucunu ikili `n+1` ile karşılaştırır. Ana program izi ve sonucu yazar:

```term
$ python tm.py
q0   _1011_  kafa= 0
q0   _1011_  kafa= 1
q0   _1011_  kafa= 2
q0   _1011_  kafa= 3
q0   _1011_  kafa= 4
q1   _1011_  kafa= 3
q1   _1010_  kafa= 2
q1   _1000_  kafa= 1
dur  _1100_  kafa= 0
1011 + 1 = ('1100', 8)
dogrulanan: 1001
```

İz, makinenin iki aşamasını açıkça gösterir. Üst beş satırda başlık (q0 durumu) sağa gider: dört adım rakamların üstünde, bir adım sondaki boş hücrede; bant 1011'i olduğu gibi korur. Sonra q1 durumunda başlık geri döner, sırasıyla 1'i 0'a, 1'i 0'a çevirir ve 0'ı 1'e çevirip durur. Toplam 5 adım tarama ve 3 adım taşıma: 8 adım. Sonuç 1100, yani 12; bu da 11 + 1'dir.

![Şekil 36.9: 1011 + 1 için TM bant izi: her satır bir adım, kırmızı kare başlığın konumu](gorseller/b36_tm_bant.png)

Makine küçük olmasına rağmen üç önemli gözlem yapmamızı sağlar. Birincisi, bant sonsuzdur: makine bir sayıyı istediği kadar büyük yapabilir, sonlu bellekli bir DFA yapamaz. İkincisi, bir TM'nin gerçek bilgisayara benzerliği buradan gelir: bir bilgisayar sonlu bellekle sınırlıdır, ama o belleğin büyüklüğü pratikte bizim sorunlarımızın ölçeğinden çok büyüktür; yine de teorik olarak sonlu bir DFA'dır. Üçüncüsü, TM'lerin her dili tanıyamayacağını görmek için bir sonraki paragrafa geçiyoruz.

**Durma problemi.** H = {(M, w) : M makinesi w girdisinde durur} dili özyinelemeli değildir; yani onu tanıyan ve her girdide duran bir TM yoktur. Kanıt, Cantor'un köşegenleştirmesine benzeyen bir çelişkidir (Turing, 1936; genel bilgi). Varsayalım bir `halts(p, x)` fonksiyonu var: p programı x girdisiyle çalıştırılırsa duruyorsa `True`, sonsuz döngüye giriyorsa `False` döndürür. Bu fonksiyonla şu programı yazalım:

```python
def paradoks(p):
    if halts(p, p):
        while True:
            pass
    return
```

`paradoks` kendisine verildiğinde ne olur? `halts(paradoks, paradoks)` `True` dönerse `paradoks` sonsuz döngüye girer, yani durmaz: çelişki. `False` dönerse `paradoks` hemen durur: yine çelişki. Demek ki `halts` fonksiyonu yazılamaz. Snippet'i derleyebilirsin (ast ile doğruladık); `halts` tanımlı değil, bu yüzden çalıştıramazsın; amaç tam olarak budur: varsayımsal bir fonksiyonun çelişki doğurduğunu görmek.

Bu sonucun pratik mesajı şudur: bir programın sonsuz döngüye girip girmeyeceğini **her** program için genel olarak kanıtlayan bir araç yazamazsın. Statik analiz araçları (derleyici uyarıları, tip sistemleri) bu yüzden ya bazı programları reddeder ya da bazı hataları kaçırır. Bu, Bölüm 37'de tip sistemleri ve Bölüm 39'da test yazmayı anlatırken yeniden karşına çıkacak.

Mülakatta bu bölümden gelebilecek en sık soru "neden her programın durup durmadığını bilemezsin?" sorusudur. Cevabın kısa hâli şudur: çelişki kanıtını yukarıdaki gibi kurmak; uzun hâli, bu sonucun Gödel'in eksiklik teoremleri ve Kolmogorov karmaşıklığı ile akraba olduğunu anlatmaktır (genel bilgi).

## 36.14 Sözcüksel analiz: Doruk lexer'ı bir DFA olarak

Şimdiye kadar anlattığımız her şey bir derleyicinin ilk aşamasında doğrudan çalışır: sözcüksel analiz (lexical analysis). Kaynak metni, belirteç (token) denilen anlamlı birimlere ayırmak bu aşamanın işidir. `değişken x = 3;` satırı beş belirtece dönüşür: anahtar kelime, tanımlayıcı, eşittir işareti, tam sayı ve noktalı virgül. Bu ayrıştırma, düzenli dillerin en çok kullanıldığı yerdir; bu yüzden Bölüm 37'nin ilk adımı olan bu aşamayı tamamen bu bölümün araçlarıyla inceleyebiliriz.

Konuyu somut kılmak için Mert'in kendi yazdığı Doruk programlama dilinin sözcüksel analizcisini (lexer) inceleyeceğiz. Doruk, anahtar kelimeleri Türkçe olan bir dil; kaynak kodu UTF-8 olarak okur. Bu bölümde kaynak dosyalarını yalnızca okudum ve derlemek için yeri değiştirmeden geçici bir kopyasını (Temp altında) kullandım; depoya hiçbir dosya yazılmadı. İncelediğimiz dosyalar şunlar: `engine/include/Token.h` (belirteç türleri), `engine/include/Lexer.h` (arayüz), `engine/src/Lexer.cpp` (asıl tarayıcı), `engine/src/Token.cpp` ve `tests/test_lexer.cpp` (testler).

Belirteç türleri, `Token.h` içindeki bir `enum class`'tır. Literal türleri, anahtar kelimeler, tanımlayıcı, operatörler ve noktalama burada sıralanır:

```cpp
enum class TokenTuru {
    // ── Literaller ──────────────────────────────────────────
    TAM_SAYI_LIT,      // 42, 100, 0
    ONDALIK_LIT,       // 3.14, 0.5, 2.718
    METIN_LIT,         // "merhaba dünya"
```

Bu enum, Bölüm 22'deki State kalıbında durumları bir enum ile tanımlamanın aynısıdır: her belirtecin türü bu sonlu kümenin bir üyesidir. Lexer'ın işi, bir kaynak dizgeyi bu kümenin üyelerine böldüğü bir yolu bulmaktır.

### Sözcüksel analizin üç kuralı

Bir sözcüksel analizci üç temel kuralla çalışır. Birincisi, her belirteç türü bir düzenli ifadeyle tanımlanır: tam sayı `[0-9]+`, tanımlayıcı harfle başlar ve harf, rakam ya da alt çizgiyle devam eder, vb. İkincisi, **en uzun eşleşme** (maximal munch) kuralı: girdinin başından başlayarak en uzun olası belirteç alınır. `==` karakterleri bir belirteç olarak okunur, iki tane `=` değil. Üçüncüsü, **öncelik** kuralı: aynı uzunlukta iki eşleşme varsa, daha önce tanımlanan kazanır. Anahtar kelime `eğer` ile tanımlayıcı `eğer` aynı dizgeyi eşler; anahtar kelime öncelikli olmalıdır.

Doruk'ta bu üç kural şöyle uygulanır. Ana dağıtım, `sonrakiToken`'ın ilk karakterine bakan bir koşullar zinciridir. Boşluk ve yorumlar atlanır, sonra ilk karaktere göre dal seçilir: tırnak için metin, rakam için sayı, harf ya da `_` için tanımlayıcı, geri kalanı için operatör ve noktalama.

```cpp
Token Lexer::sonrakiToken() {
    bosluklarAtla();

    if (bitti()) {
        return Token(TokenTuru::DOSYA_SONU, "", satir_, sutun_);
    }

    uint32_t basSatir = satir_;
    uint32_t basSutun = sutun_;
    char     c        = mevcutKar();

    // ── Metin literal ──────────────────────────────────────
    if (c == '"' || c == '\'') {
        return metinTara(basSatir, basSutun);
    }

    // ── Sayı literal ────────────────────────────────────────
    if (std::isdigit(static_cast<unsigned char>(c))) {
        return sayiTara(basSatir, basSutun);
    }

    // ── Tanımlayıcı veya anahtar kelime ─────────────────────
    uint32_t cp = utf8MevcutBak();
    if (kimlikBaslangiciMi(cp)) {
        return kimlikTara(basSatir, basSutun);
    }
```

Yukarıdaki dağıtımda `if (c == '"' || c == '\'')` ile başlayan metin dalı, `std::isdigit` ile sayı dalı ve `kimlikBaslangiciMi` ile tanımlayıcı dalı, ilk karakter ayrımıdır. Bu ayrım bir DFA'nın başlangıç durumundan çıkan ilk kenarlara karşılık gelir (Şekil 36.10). Her dal, tek bir girdi karakterine bakarak doğru yolu seçer; bu yüzden tarayıcı, kaynak dizgeyi tek geçişte işler.

En uzun eşleşme için bir karakterlik ileri bakış gerekir. Doruk'ta bu, `eslestir` fonksiyonuyla yapılır: mevcut karakter beklenenle eşleşiyorsa tüketir ve doğru döner.

```cpp
// eslestir — mevcut karakter beklenenle eşleşiyorsa tüket
bool Lexer::eslestir(char beklenen) {
    if (bitti() || mevcutKar() != beklenen) return false;
    ilerle();
    return true;
}
```

`=` ile `==` ayrımı `case '='` dalında bu fonksiyonla yapılır: önce `eslestir('=')` denenir, eşleşirse `==` belirteci üretilir, eşleşmezse tek `=` üretilir (`Lexer.cpp`, satır 417–420). Bu, tek karakterlik bir ileri bakışla çözülen en uzun eşleşmenin en basit örneğidir. Düzenli dil teorisinde bu, kenarların bir sonraki karaktere bakarak seçildiği bir DFA'dır.

### Sayılar: 1e ve 0x neden hata vermiyor?

Sayı tarayıcısı üç biçimi destekler: tam sayı, ondalık ve bilimsel gösterim. Bilimsel gösterim kısmı tam olarak bir DFA'nın durumlarını izler: rakamlar, nokta ve ardından rakam, sonra `e` ya da `E`, isteğe bağlı işaret ve rakamlar.

```cpp
        } else if ((c == 'e' || c == 'E') && !lexem.empty()) {
            // Bilimsel gösterim: 1.5e10 veya 1e-3
            lexem += c;
            ilerle();
            ondalikVar = true;
```

Bu kesitte bilimsel gösterim dalı, `e` ya da `E` gördüğünde ondalık bayrağını açar, isteğe bağlı işareti alır ve üs rakamlarını tüketir. Dikkat edilmesi gereken nokta şudur: üs rakamı yoksa (örneğin `1e` yazılmışsa) tarayıcı bunu hata olarak bildirmez. Bu bölümün sonunda gösterdiğimiz deney bunu doğrular: `1e` girdisi `ONDALIK_LIT` olarak, `0x` girdisi `TAM_SAYI_LIT` olarak (lexem `0x`) hata üretmeden çıkar. Bu bir **eksik kural** hatasıdır; düzenli ifade `[0-9]+([eE][+-]?[0-9]+)` olsaydı `1e` reddedilirdi.

### Tanımlayıcı mı, anahtar kelime mi?

Tanımlayıcı tarayıcısı, bir kimlik başlangıcı bulduğunda kabul edilen en uzun kimlik dizgesini tüketir ve sonra anahtar kelime tablosuna bakar. Bu, en uzun eşleşme ile öncelik kuralının birleşimidir: önce en uzun olası dizge alınır, sonra o dizgenin bir anahtar kelime olup olmadığına karar verilir.

```cpp
Token Lexer::kimlikTara(uint32_t basSatir, uint32_t basSutun) {
    // Kaynak byte konumunu kaydet — lexem için slice alacağız
    size_t bas = konum_;

    // İlk kod noktasını tüket (zaten başlangıç olduğu doğrulandı)
    utf8OkuIlerle();

    // Devam karakterlerini tüket
    while (!bitti() && kimlikDevamMi(utf8MevcutBak())) {
        utf8OkuIlerle();
    }

    // Kaynak metinden slice al — ham byte'lar (UTF-8)
    std::string lexem = kaynak_.substr(bas, konum_ - bas);

    // Anahtar kelime tablosunda ara
    const auto& tablo = anahtarKelimeler();
    auto it = tablo.find(lexem);
```

`kimlikTara` önce ilk kod noktasını tüketir (zaten bir kimlik başlangıcı olduğu doğrulanmıştır), sonra devam karakterlerini ve en sonda `lexem` dizgesini kaynağın bir dilimi olarak alır. Anahtar kelime tablosu, `lexem` ile bir `unordered_map` arasında bir arama yapar; bulunursa anahtar kelime belirtecini, bulunmazsa `TANIMLAYICI`'yı döndürür (satır 691 ve 694). Bu, anahtar kelimelerin büyük-küçük harf duyarlı olduğu anlamına gelir: `Eğer` bir tanımlayıcıdır. Test dosyası bu davranışı açıkça sınar ("Anahtar kelimeden büyük harfli identifier farklı tanınır" testi, `tests/test_lexer.cpp`).

Anahtar kelime tablosu şu girdilerle başlar. Her bir girdi, UTF-8 bayt dizisi olarak bir anahtar kelimeyi belirteç türüne eşler:

```cpp
        { "değişken",  TokenTuru::DEGISKEN   }, // değişken
        { "eğer",             TokenTuru::EGER        }, // eğer
        { "değilse",          TokenTuru::DEGILSE     }, // değilse
```

### UTF-8 ve Türkçe karakterler

Doruk'un en çok dikkat isteyen kısmı Türkçe karakterlerin işlenmesidir. Harfler UTF-8 ile kodlanır: `ş` iki bayttır (`0xC5 0x9F`), `ı` de iki bayt, `𝑥` gibi bazı karakterler dört bayt. Tarayıcı bayt bayt ilerler; ama tanımlayıcı kuralı karakter bazında yazılmalıdır. Bu yüzden `utf8OkuIlerle` bir kod noktası okur ve konumu ona göre ilerletir. Hangi kod noktalarının bir kimliğin parçası olabileceği ise `kimlikBaslangiciMi` ile belirlenir:

```cpp
    if (cp >= 0x00C0 && cp <= 0x024F) return true;
    // Kiril, Çince vb. için genel BMP harf kontrolü
    // (0x0250 ve üzeri — ileriki sürümlerde genişletilebilir)
    if (cp >= 0x0370 && cp <= 0xFFFF) return true;
    return false;
}
```

Bu aralıklar Latin-1 Ek, Latin Genişletilmiş-A ve B (U+00C0 – U+024F) ile geniş bir BMP aralığını (U+0370 – U+FFFF) kapsar. Türkçe harfler ilk aralıkta olduğu için doğru çalışır; ama ikinci aralık, yorumda da belirtildiği gibi, "geçici" bir genelleştirmedir ve bu yüzden bazı karakterleri yanlışlıkla tanımlayıcıya dahil eder. Bunu deneyle göreceğiz.

### Deney: lexer'ı çalıştırmak

Bir lexer'ı gerçekten anlamanın yolu onu çalıştırıp girdilere bakmaktır. Aşağıdaki `dump.cpp`, Doruk'un `Lexer` sınıfını kullanarak bir dosyanın token akışını yazar. Kod, yalnızca lexer'ı çağıran bir sarmalayıcıdır; Doruk'un kendi kodu değişmez.

```cpp
// dump.cpp: Doruk Lexer'ını çalıştırır, token akışını yazar.
// Kullanım: ./dump dosya.drk   veya   ./dump -s "metin"
#include "Lexer.h"
#include <fstream>
#include <iostream>
#include <sstream>

using namespace Doruk;

int main(int argc, char** argv) {
    std::string kaynak;
    if (argc >= 3 && std::string(argv[1]) == "-s") {
        kaynak = argv[2];
    } else {
        std::ifstream f(argv[1], std::ios::binary);
        std::stringstream ss;
        ss << f.rdbuf();
        kaynak = ss.str();
    }
    Lexer lx(kaynak, "test.drk");
    LexerSonucu r = lx.tara();
    for (const auto& t : r.tokenler) {
        std::cout << t.satir << ":" << t.sutun << "\t"
                  << tokenTuruAdi(t.tur) << "\t[" << t.lexem
                  << "]\n";
    }
    std::cout << "hata var mi: "
              << (r.basarili() ? "hayir" : "evet") << "\n";
    return 0;
}
```

Derleme için kaynak ağacının `engine/` klasörünü ve `dump.cpp`'yi Temp altındaki bir klasöre kopyalayıp aşağıdaki komutu çalıştırırsın. Windows'ta bu derleyici WSL2 içindeki `g++` (13.3) ile yapıldı; çalıştırma da WSL içinde yapılır. Testlerin Catch2 bağımlılığı vardır ve bu çalışmada yüklenmediği için `test_lexer.cpp` çalıştırılmadı; deneylerin tümü `dump` ile yapıldı.

```bash
g++ -std=c++17 -O2 -Wall -Wextra \
    -Iengine/include dump.cpp \
    engine/src/Lexer.cpp engine/src/Token.cpp \
    engine/src/Diagnostics.cpp -o dump
```

Deney dosyalarını `printf` ile üretiyoruz; böylece her girdinin baytları açıkça görünür. İlk örnek bir sanity kontroldür: Türkçe anahtar kelimeler ve tanımlayıcı doğru tanınmalı.

```term
$ ./dump temel.drk
1:1	DEGISKEN	[değişken]
1:12	TANIMLAYICI	[x]
1:14	ESIT	[=]
1:16	TAM_SAYI_LIT	[3]
1:17	NOKTALI_VIRGUL	[;]
2:1	TANIMLAYICI	[Eğer]
3:1	DOSYA_SONU	[]
hata var mi: hayir
```

Çıktı beklediğimiz gibidir: `değişken` bir `DEGISKEN` anahtar kelimesi, `Eğer` ise `TANIMLAYICI`'dır. Şimdi zor girdilere geçelim. Her deneyin girdisini `printf` ile oluşturup `dump`'a veriyoruz.

```term
$ printf 'a \xe2\x80\x94 b\n' > emdash.drk
```

Bu girdide ortadaki karakter U+2014 (uzun tire, —) ve UTF-8'de üç bayttır (`e2 80 94`). Çıktı şöyle:

```term
$ ./dump emdash.drk
1:1	TANIMLAYICI	[a]
1:3	TANIMLAYICI	[—]
1:7	TANIMLAYICI	[b]
2:1	DOSYA_SONU	[]
hata var mi: hayir
```

Uzun tire bir `TANIMLAYICI` olarak kabul edildi ve hiçbir hata üretilmedi. Bunun sebebi, `kimlikBaslangiciMi` içindeki ikinci aralığın (U+0370–U+FFFF) U+2014'ü de kapsamasıdır. Aynı davranış tırnaklar için de geçerlidir: Word'den kopyalanan akıllı tırnaklar bir tanımlayıcının parçası olur.

```term
$ printf '\xe2\x80\x9cmerhaba\xe2\x80\x9d\n' > akilli.drk
```

```term
$ ./dump akilli.drk
1:1	TANIMLAYICI	[“merhaba”]
2:1	DOSYA_SONU	[]
hata var mi: hayir
```

Sonuç `“merhaba”` tek bir tanımlayıcıdır. Yani derleyici, bir dizgenin tırnaklarını yanlışlıkla bir tanımlayıcının parçası sayıp tek bir yanlış anlam üretir; kullanıcı ise bir hata mesajı yerine garip bir "tanımlanmamış değişken" uyarısı görür. Bu, bir karakter sınıfının çok geniş tanımlanmasının klasik sonucudur.

İkinci deney, bir kodlama sorunudur. Bir ayrıntı: Doruk kaynakları UTF-8 kabul eder, ama bir emoji dört bayttır ve kimlik aralığının dışında kalır.

```term
$ printf 'x \xf0\x9f\x98\x80\n' > emoji.drk
```

```term
$ ./dump emoji.drk
1:1	TANIMLAYICI	[x]
1:3	BILINMEYEN	[�]
1:4	TANIMLAYICI	[���]
2:1	DOSYA_SONU	[]
hata var mi: evet
```

Çıktıdaki davranış iki hatanın bileşimidir. Birinci bayt (`f0`) bir kimlik başlangıcı değildir; `default` dalına düşer ve tek bir bayt olarak `BILINMEYEN` olur (satır 459–470). Kalan üç bayt (`9f 98 80`) ise geçersiz UTF-8 devam baytlarıdır; `utf8MevcutBak` bunları U+FFFD (replacement karakteri) olarak çözer, U+FFFD ise BMP aralığının içindedir, dolayısıyla bir kimlik başlangıcı sayılır ve üç baytlık tanımlayıcı üretilir. Yani bir emoji, bir hata ve bir "tanımlayıcı" olarak görünür.

Bunun pratik karşılığı, kopyala-yapıştırdığın bir kaynak dosyada görünmez bir boşluk karakteridir. Metin editörlerinde sık görülen **NBSP** (U+00A0, bayt dizisi `c2 a0`) bu biçimde ortaya çıkar:

```term
$ printf 'a\xc2\xa0b\n' > nbsp.drk
```

```term
$ ./dump nbsp.drk
1:1	TANIMLAYICI	[a]
1:2	BILINMEYEN	[�]
1:3	TANIMLAYICI	[�b]
2:1	DOSYA_SONU	[]
hata var mi: evet
```

Görünürde `a b` gibi duran bu satır üç belirteç yerine iki tanımlayıcı ve bir hataya dönüşür: `a`, `BILINMEYEN` (tek bayt `c2`) ve `U+FFFD` ile başlayan `�b` tanımlayıcısı. Hata mesajı "beklenmeyen karakter" der, ama ekranda neyin beklenmeyen olduğu görünmez. Bu, sözcüksel hata mesajlarının kullanıcıya yeterli bağlam vermesi gerektiğinin somut bir örneğidir.

Üçüncü deney Unicode normalizasyonudur. Türkçe `ğ` harfi iki biçimde kodlanabilir: tek kod noktası U+011F (NFC) ya da `g` ile birleştirici breve U+0306 (NFD). Doruk anahtar kelimeleri NFC biçiminde tanımlar. Aynı görünen bir kelime NFD ile yazılırsa, sonuç farklı olur:

```term
$ printf 'g\xcc\x86\xc4\xb1\n' > nfd.drk
```

```term
$ ./dump nfd.drk
1:1	TANIMLAYICI	[g]
1:2	BILINMEYEN	[�]
1:3	TANIMLAYICI	[�ı]
2:1	DOSYA_SONU	[]
hata var mi: evet
```

Burada `g` bir tanımlayıcı olur, birleştirici breve (`cc 86`) tek bayt olarak `BILINMEYEN` hatasına döner ve kalan `ı` yeni bir tanımlayıcı olur. Ekranda `ğı` gibi görünen bir sözcük üç parçaya bölünmüştür. Bu, anahtar kelime tablosunun bayt bazlı karşılaştırma yapmasının ve kaynağın normalize edilmemesinin doğal sonucudur.

Son iki deney, sayı ve operatör sınırlarını gösterir. Önce `1e` ve `0x`'in hatasız kabul edildiğini gördük. Bir de çarpma işareti: `×` (U+00D7) Latin-1 aralığında olduğu için bir kimlik harfi sayılır:

```term
$ printf 'a\xc3\x97b\n' > carpi.drk
```

```term
$ ./dump carpi.drk
1:1	TANIMLAYICI	[a×b]
2:1	DOSYA_SONU	[]
hata var mi: hayir
```

Yani `a×b` bir çarpma ifadesi olarak değil, tek bir tanımlayıcı olarak tanınır. Bunu düzeltmek için tanımlayıcı harflerini bir kategori tablosuyla (Unicode `L*` kategorileri) belirlemek gerekir; bu bir dil tasarım kararıdır ve Kod Okuma egzersizinde ele alacağız.

### Bulguların özeti

Deneyleri sıralarsak, Doruk lexer'ı için beş gözlem çıkar. Hepsi derleyip çalıştırarak doğrulanmıştır; kaynak kodda bunları gösteren satırlar parantez içinde verilmiştir.

1. **Tanımlayıcı kümesi gereğinden geniş.** U+2014 (—), U+00D7 (×) ve akıllı tırnaklar tanımlayıcı sayılır (`kimlikBaslangiciMi`, 273–278).
2. **Geçersiz baytlar tanımlayıcıya dönüşür.** U+FFFD BMP aralığındadır; emoji ve kopyala-yapıştır kalıntıları "tanımlayıcı" olarak çıkar (`utf8MevcutBak`, `kimlikBaslangiciMi`).
3. **Hata kurtarma tek bayt ilerler.** Tanınmayan çok baytlı karakterde `default` dalı tek bayt tüketir; böylece bir karakter birden fazla hataya ve tanımlayıcıya bölünür (satır 379, 459–470).
4. **Eksik üs ve hex rakamları hata vermez.** `1e` ve `0x` hatasız belirteçlerdir (`sayiTara`, 645–649; hex dalı 607–625).
5. **Unicode normalizasyonu yoktur.** NFC ve NFD aynı görünen kelimeleri farklı tanımlar; anahtar kelime tablosu bayt karşılaştırmasıdır.

Bu bulgular Doruk'un ciddi bir kusuru değil, bir tasarım sınırıdır: kod kısa ve okunabilir; sadece bir DFA'nın alfabesini (kabul edilen karakterleri) bilinçli olarak tanımlamadan büyümüş. Kendi lexer'ını yazacak bir mühendis için ders şudur: alfabeni açıkça tanımla, her kod noktası kategorisini bir tablo ile yönet, ve hata durumlarında tam olarak ne tükettiğini belgele.

Son olarak Şekil 36.10'a bakalım. Bu şekil, `sonrakiToken` ve yardımcı fonksiyonların kaynağından çıkarılmış bir durum diyagramıdır; düğümler, kaynakta ayrı dal olarak görünen durumlardır.

![Şekil 36.10: Doruk lexer'ının durum diyagramı: kaynaktaki dalların sonlu otomat gösterimi](gorseller/b36_doruk_lexer.png)

Şekil eksiktir ve bunu bilerek bıraktım: hata durumları (BILINMEYEN dalları) ve '&' ile '|' tek başına kullanıldığında oluşan hatalar çizilmedi; alt metinde bunu belirttim. Tam bir DFA çizmek, hata durumlarını da bir "çöp durumu" olarak eklemeyi gerektirir; bu, Kod Okuma egzersizinin bir parçasıdır.

## 36.15 Gerçek dünya: girdi doğrulama, protokoller ve sözdizimi vurgulama

Düzenli diller ve sonlu otomatlar yalnızca derleyici teorisi değildir; her gün karşılaştığın birçok yazılım parçasının çekirdeğidir.

**Girdi doğrulama.** Web formlarındaki e-posta, telefon numarası ve tarih kontrolleri çoğu zaman düzenli ifadelerle yapılır. Bu uygundur, ama sınırlarını bilmek gerekir: düzenli ifadeler iç içe yapıları (örneğin eşleşen parantezleri) doğrulayamaz; bunun için 36.10'daki yığın gerekir. Ayrıca regex'in katastrofik geri izleme riski (36.6) doğrulama kodunu bir hizmet reddi saldırısına açık bırakabilir. Savunma olarak, girdi uzunluğunu regex'ten önce sınırlamak ve mümkünse doğrusal zamanlı bir motor kullanmak gerekir.

**Protokol ayrıştırıcıları.** Bölüm 31'de gördüğümüz uzunluk önekli çerçeve okuyucusu bir durum makinesidir: "başlık bekle", "uzunluğu oku", "gövdeyi oku" gibi durumları ve her durumdan geçişleri vardır. Burada ilginç bir nokta var: uzunluk alanı sabit genişlikteyse (ör. 16 bit), makinenin durumları sonludur, ama bu sonlu sayı uzunluk alanının değer aralığıyla orantılıdır. Uzunluk sınırsız olsaydı, 36.7'deki pompalama argümanı bunun düzenli olmadığını gösterirdi; bu yüzden gerçek protokoller her zaman bir üst sınır koyar. Gömülü sistemlerdeki UART/SPI çerçeveleri (Bölüm 45) için de aynı mantık geçerlidir.

**İHA komut dili.** Bir yer istasyonunun gönderdiği komutlar (ör. `GIT 41.0 29.0 ALT 120` gibi bir satır) düzenli bir dil oluşturur: anahtar kelime, sayılar, boşluklar ve bir sonlandırıcı. Böyle bir komut dilini tanımak, bir sözcüksel analizciyle başlar ve ardından, Bölüm 37'de göreceğimiz gibi, bir ayrıştırıcıya geçer. Burada önemli olan, gelen komutun tam olarak tanımlı bir dile ait olması ve tanınmayan her karakterin açıkça reddedilmesidir; sessiz bir düzeltme, uçuş yazılımında kabul edilemez bir davranıştır.

**Sözdizimi vurgulama.** Bu kitabın kendi motoru, `engine/kitap_engine.py` içindeki `highlight_line` işlevi, kod kartlarındaki renklendirmeyi yapar. Bu, basit bir sözcüksel analizcidir: `_TOKEN` (satır 343–351) adlı tek bir düzenli ifade, yorum, dizge, sayı, ön işlemci satırı, tanımlayıcı ve boşluk gruplarını sırayla dener (`re` modülünde dallar ilk eşleşmeyle seçilir). Bu, en uzun eşleşme yerine **ilk eşleşme** kuralıdır; Doruk'un tarayıcısından farkı budur. Ayrıca her satır bağımsız işlenir, çünkü çok satırlı bir yorum ya da dizge yakalanmaz. Bu sınırlamalar, bir vurgulayıcı için kabul edilebilir bir ödünleşmedir; bir derleyici için değildir.

Savunma sanayiinde bu bölümün bilgisi üç yerde hemen karşına çıkar: telemetri ve komut çerçevelerinin doğrulanması, kaynak kod ve yapılandırma dosyalarının güvenli ayrıştırılması ve bu ayrıştırıcıların ReDoS'a karşı dayanıklılığının ölçülmesi. Kural şudur: her girdi düşmandır; kabul ettiğin dili açıkça tanımla, reddettiğin her şeyi gör, ve ayrıştırıcının en kötü girdideki süresini bir ölçümle kanıtla.

## Çözümlü Örnekler

Aşağıdaki dört örnek ★ den ★★★'e doğru zorlaşır. Her birinde Bölüm 5'teki altı adımı izliyoruz: anla, örnekle, kaba çöz, örüntü, iyileştir, doğrula. Doğrulama adımında elle izlediğin tabloyu programın çıktısıyla karşılaştırmak zorundasın; tablo tutmazsa düşüncende bir hata vardır.

### Örnek 1 (★): 5'e bölünebilen ikili sayılar

**Problem.** Girdi yalnızca 0 ve 1 harflerinden oluşan bir ikili sayıdır. Sayının ondalık değeri 5'in katıysa dizgeyi kabul eden bir DFA kur. Örnek olarak 10 (`1010`) kabul, 13 (`1101`) red olmalı.

**Adım 1 — Anla.** Girdi bir ikili dizgedir ve sonunda kabul/red kararı istenir. Dikkat edilecek nokta, sayının değerini tutmak yerine yalnızca 5'e bölümünden kalanı tutmamız gerektiğidir. Kalan 0'dan 4'e kadar beş değer alabilir; dolayısıyla beş durum gerekir.

**Adım 2 — Örnekle.** Küçük örnekler: 0 (kalan 0, kabul), 1 (kalan 1), 2 (kalan 2), 5 (`101`, kalan 0, kabul), 10 (`1010`, kalan 0, kabul), 13 (`1101`, kalan 3, red). Bu örnekler, kalan değerinin adım adım nasıl değiştiğini görmek için yeterli.

**Adım 3 — Kaba çöz.** Her durum bir kalanı taşır. Bir bit geldiğinde yeni değer 2v + b'dir; bu yüzden yeni kalan (2r + b) mod 5 olur. Beş durumun her biri için iki geçiş vardır: toplam on geçiş. Kaba çözüm, bu on geçişi tek tek hesaplayıp bir tabloya yazmaktır.

**Adım 4 — Örüntü.** Üç'e bölünebilirlik DFA'sının (36.2) formülü aynıdır, yalnızca modül değişmiştir. Örüntü: modül m ise durumlar 0..m−1 ve geçiş (2r + b) mod m. Kabul durumu yalnız 0'dır, çünkü başlangıç da 0'dır ve yalnız kalanı 0 olan sayılar kabul edilir.

**Adım 5 — İyileştir.** Tabloyu koda çevirirken `delta` sözlüğünü formülle üretmek hem kısa hem güvenilirdir. Kodda `DFA` sınıfını yeniden kullanıyoruz; yeni bir sınıf yazmaya gerek yok.

**Adım 6 — Doğrula.** Elle izleme tablosu, kabul ve red örneklerini gösterir. Önce `1010` için: başlangıç 0; birinci bit 1 → (0·2+1) mod 5 = 1; ikinci bit 0 → (1·2+0) mod 5 = 2; üçüncü bit 1 → (2·2+1) mod 5 = 0; dördüncü bit 0 → (0·2+0) mod 5 = 0. Son durum 0, kabul.

| Adım | Okunan bit | Eski kalan | Hesap | Yeni kalan |
|---|---|---|---|---|
| 1 | 1 | 0 | (0·2+1) mod 5 | 1 |
| 2 | 0 | 1 | (1·2+0) mod 5 | 2 |
| 3 | 1 | 2 | (2·2+1) mod 5 | 0 |
| 4 | 0 | 0 | (0·2+0) mod 5 | 0 (kabul) |

Şimdi `1101` (13): 0 → 1 (1), 1 → 3 (2·1+1), 0 → 1 (6 mod 5), 1 → 3 (3). Son kalan 3, red. Programın çıktısı bu iki izi doğrular:

```python
from dfa import DFA
m = {(r, b): (2 * r + int(b)) % 5 for r in range(5) for b in "01"}
D = DFA(range(5), "01", m, 0, {0})
for w in ["1010", "1101"]:
    print(w, int(w, 2), D.calistir(w), D.kabul(w))
```

Çıktı: `1010 10 [0, 1, 2, 0, 0] True` ve `1101 13 [0, 1, 3, 1, 3] False`. İz ve tablo eşleşiyor.

**Bunu AI'sız yazabilir misin?** Aynı yöntemle 4'e bölünebilen ikili sayıların DFA'sını kurabilir misin? Bu DFA'da kaç durum var ve kabul koşulunu bir cümleyle, sayının son bitlerine bakarak nasıl ifade edersin?

### Örnek 2 (★★): İkinci harfi b olan dizgeler: alt küme yapısıyla DFA

**Problem.** Σ = {a, b} üzerinde, ikinci harfi b olan bütün dizgelerin dilini tanıyan bir NFA kur ve alt küme yapısıyla DFA'ya çevir. Örnek olarak `abb` kabul, `bab` red olmalı.

**Adım 1 — Anla.** Dilin koşulu tek bir konuma bağlıdır: ikinci harf. Bu, bir DFA'da da kurulabilir, ama bir NFA ile kurmak daha doğaldır: ilk harf serbest, ikinci harf b ise kabul yolunu aç.

**Adım 2 — Örnekle.** `ab` (ikinci harf b, kabul), `bb` (kabul), `aa` (red), `ba` (red), `a` (ikinci harf yok, red). Sonuç: kabul için en az iki harf gerekir ve ikinci harf b olmalıdır.

**Adım 3 — Kaba çöz.** NFA üç durum kullanır: q0 başlangıç (her harfi okur ve q1'e gider), q1 (yalnız b okuyabilir ve q2'ye gider), q2 kabul (her harfi okuyup kendinde kalır). Kaba çözümde iki sorun var: q1'de a okunursa ne olur (hiçbir yol yok, dizge ölür) ve q2'de her harf kabul kalır.

**Adım 4 — Örüntü.** Alt küme yapısında bir DFA durumu, NFA'nın o anda olabileceği durumların kümesidir. Bir durum kümesinden hiçbir yol çıkmıyorsa, boş küme ∅ bir **çöp durumudur**: bir kez oraya düşen dizge reddedilir. Bu, her DFA'da kullanılan bir örüntüdür.

**Adım 5 — İyileştir.** Alt küme yapısını, boş kümeyi de bir durum olarak kabul ederek uygularız. Durum sayısı sekiz yerine dört çıkar, çünkü pek çok olası küme erişilemez. Yalnız erişilebilir kümeler DFA'ya girer: {0}, {1}, {2}, ∅.

**Adım 6 — Doğrula.** İz tablosu iki dizge için aşağıdadır. Önce `abb`: {0} → a → {1} → b → {2} → b → {2}. Son durum {2} kabul. Sonra `bab`: {0} → b → {1} → a → ∅ → b → ∅. Son durum ∅, red.

| Adım | Okunan | Önceki durum | Sonraki durum | Kabul mu? |
|---|---|---|---|---|
| 0 | (başlangıç) | — | {0} | hayır |
| 1 | a | {0} | {1} | hayır |
| 2 | b | {1} | {2} | evet |
| 3 | b | {2} | {2} | evet |

Bunu programla doğrulamak için `nfa.py`'deki `alt_kume` fonksiyonunu bu NFA'ya uygularsın; aynı dört durum çıkar ve iz aynı olur. (Burada NFA'yı elle kurduk; kendi dosyanda `NFA(range(3), "ab", delta, 0, {2})` ile tanımlayabilirsin.)

**Bunu AI'sız yazabilir misin?** İkinci harfi b olan dizgeleri **sondan** ikinci harf olarak değiştirirsen, NFA'nın kaç durumu olur ve DFA'daki durum kümeleri nasıl değişir? Dizgenin sonundan iki harf gerektiğinde hangi durumun ∅ olmak yerine ne zaman anlamlı hâle geldiğini düşün.

### Örnek 3 (★★): Belirsiz aritmetik gramerini öncelikle düzeltmek

**Problem.** E → E + E | E * E | n gramerinde n + n * n dizgesinin iki türetme ağacı var. Gramerdeki belirsizliği, `*`'ın `+`'tan önce bağlanmasını sağlayarak gider. Düzeltilmiş gramerin n + n * n için tek ağaç vermesini göster.

**Adım 1 — Anla.** İstenen, bir gramerin iki farklı ağaç vermesini tek bir ağaca indirmek. Ölçüt: düzeltilmiş gramerde n + n * n için sayı 1 olmalı ve dil değişmemeli.

**Adım 2 — Örnekle.** n + n: iki yöntem de tek ağaç verir (belirsiz gramerde 1). n * n + n * n: belirsiz gramerde 5 ağaç vardır. Bu örnekler, belirsizliğin sadece iki operatör yan yana geldiğinde ortaya çıktığını gösterir.

**Adım 3 — Kaba çöz.** Bir çözüm: çarpmayı toplamadan önce bağlamak için bir ara değişken eklemek. Ama `*` ve `+` için iki ayrı kural yazıp bunların sırasını belirtmek gerekir.

**Adım 4 — Örüntü.** Öncelik katmanları: her seviye bir değişkendir; üst seviye alt seviyeyi kendi operatörüyle bağlar. Toplama en dış seviye (E), çarpma orta (T), çarpan en iç (F). Bu, matematikteki işlem önceliğinin gramer karşılığıdır.

**Adım 5 — İyileştir.** Katmanlı gramer: E → T + E | T, T → F * T | F, F → n | ( E ). Burada `+` ve `*` sağa doğru birleşir. Sol birleşim istersen (`a - b - c` için gereken) yapı değişir; bunu düşün.

**Adım 6 — Doğrula.** Her iki gramerde n + n * n için en sol türetmeleri yazalım. Belirsiz gramerde iki türetme vardır.

- Ağaç 1 (+ en üstte): E ⇒ E + E ⇒ n + E ⇒ n + E * E ⇒ n + n * E ⇒ n + n * n.
- Ağaç 2 (* en üstte): E ⇒ E * E ⇒ E + E * E ⇒ n + E * E ⇒ n + n * E ⇒ n + n * n.

Katmanlı gramerde yalnız bir türetme vardır: E ⇒ T + E ⇒ F + E ⇒ n + E ⇒ n + T ⇒ n + F * T ⇒ n + n * T ⇒ n + n * F ⇒ n + n * n. Programın sayımı ile bu tutarlıdır:

```text
n+n*n belirsiz: 2 tek: 1
n*n+n*n belirsiz: 5 tek: 1
```

**Bunu AI'sız yazabilir misin?** Gramerinde `-` ve `/` gibi birleşmeli olmayan operatörler varsa, sağ özyinelemeli katmanlı gramer neden yanlış olur? `8 - 3 - 2` ifadesinin iki farklı değerini yazarak bu sorunun cevabını göster ve düzeltilmiş gramerin hangi yönde özyinelemeli olması gerektiğini söyle.

### Örnek 4 (★★★): CYK tablosunu elle doldurmak

**Problem.** Dengeli parantez gramerinin CNF biçimi (36.11) ile "()()()" dizgesini CYK'yla tara. Her hücredeki S sayısını bul ve dizgenin kaç türetme ağacı olduğunu söyle.

**Adım 1 — Anla.** Girdi altı karakterdir. CYK tablosu 6 × 6 üst üçgendir; her hücre T[i][j] bir aralığın türetildiği değişkenleri ve sayılarını tutar. Sonuç T[0][5]'in S sayısıdır.

**Adım 2 — Örnekle.** "()" (S, 1 ağaç), "()()" (1 ağaç: S → SS), "()()()" (iki ayrı ağaç: ilk bölme "()" ile "()()" arasında ya da "()()" ile "()" arasında). Örnekler ağaç sayısının kesme noktalarına bağlı olduğunu gösterir.

**Adım 3 — Kaba çöz.** Taban hücreler: T[i][i] içinde ( için L, ) için R. Bunların dışındaki her hücre için, her k kesme noktası ve her A → BC kuralı denenir.

**Adım 4 — Örüntü.** Her kesme noktası bir dengeli çift ayrımı yapar. Uzunluk iki olan her hücre yalnızca "()" olabilir, yani S içerir ve sayısı 1'dir. Uzunluk dört olan hücreler, (0,3) ve (2,5) gibi iki çiftin birleşimidir; bu yüzden sayıları 0 ya da 1'dir.

**Adım 5 — İyileştir.** Tabloyu soldan sağa ve kısa aralıktan uzuna doldurmak gerekir; aksi hâlde bir hücre ihtiyaç duyduğu alt hücreyi henüz hesaplanmamış görür. Hesaplamayı, kendi sayıdan (`sol · sag`) toplayarak yaparız.

**Adım 6 — Doğrula.** Program "()()()" için aşağıdaki tabloyu verir (boş ve L/R hücreleri gösterilmez; yalnızca S sayıları):

| i \ j | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| 0 | L | 1 | - | 1 | - | **2** |
| 1 | - | R | - | - | - | - |
| 2 | - | - | L | 1 | - | 1 |
| 3 | - | - | - | R | - | - |
| 4 | - | - | - | - | L | 1 |
| 5 | - | - | - | - | - | R |

Hücre (0,5) elle izlenebilir. Kesme noktaları k = 0, 1, 2, 3, 4 için: k = 1'de T[0][1] = {S:1} ve T[2][5] = {S:1}, çarpım 1 ve S → SS kuralı verir. k = 3'te T[0][3] = {S:1} ve T[4][5] = {S:1}, çarpım 1 ve yine S → SS. Diğer kesme noktalarında ya sol ya sağ hücre boştur. Toplam 2, yani dizgenin iki türetme ağacı vardır. Program da `ağaç sayısı: 2` yazar.

**Bunu AI'sız yazabilir misin?** "(()())" dizgesinin tablosunu elle doldur. Kaç türetme ağacı var ve neden "()()()" kadar belirsiz değil? Hangi kesme noktası tek bir ağacın oluşmasını sağlıyor?

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ araçları **yasak**. Amaç çalışan bir sistem üretmekten çok, düzenli dillerin ve otomatların nasıl çalıştığını kendi elinle yaşamak. Kâğıda çiz, küçük testler yaz, hataları ölç; çözümü dışarıdan alma.
:::

### Proje 1 (★★): Kendi regex motorunu genişlet: karakter sınıfları ve DFA önbelleği

**Amaç:** 36.5'teki Thompson tabanlı motoru üç yönde genişlet: karakter sınıfları (`[a-z]`, `[^0-9]`), nokta (`.`) ve kaçış karakteri (`\`); ayrıca NFA'yı tembelce (lazily) DFA'ya çeviren bir önbellek ekle. Sonra motorunun doğruluğunu Python `re` ile diferansiyel testle, hızını da 36.6'daki ReDoS desenleriyle ölç.

**Yapılacak / Beklenen davranış:** `Motor("[a-c]x.")` kabul etmeli `ax!`, `bxy` ve reddetmeli `dx!`. Kaçış `\.` nokta karakterini eşlemeli. Önbellek, aynı durum kümesine ikinci kez gelindiğinde yeniden hesaplamamalı. Hız ölçümünde önbellekli ve önbelletsiz sürümleri aynı girdide karşılaştır.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Karakter sınıfını ayrıştırıcıda yeni bir atom türü olarak ekle; NFA'da bu atom tek bir kenar olur ve kenarın etiketi bir küme ya da yüklem olabilir. Önbellek için durum kümesini (frozenset) anahtar, sonraki durum kümesini değer alan bir sözlük kullan; her harf için yalnız bir kez hesapla. Diferansiyel testi 36.5'teki `dogrula` fonksiyonunu temel alarak yaz, ama alfabeyi `{a, b, c, x}` olarak genişlet ve kısa dizgeleri sınırlamayı unutma.

**Başarı kriterleri:**
- Rastgele 600 desende ve uzunluğu 6'ya kadar dizgelerde Python `re` ile sıfır uyuşmazlık.
- Önbellekli sürüm, 16 000 karakterlik `(a+)+b` girdisinde önbelletsiz sürüme göre ölçülebilir biçimde daha hızlı (ölçümü kendin yap ve tablo olarak raporla).
- `(a+)+b` için naif geri izleme adım sayısını ve Thompson süresini aynı tabloda ver.

### Proje 2 (★★★): Tablo güdümlü bir lexer üreticisi

**Amaç:** Bir belirteç tanım dosyası (her satırda `ad: düzenli_ifade` ve öncelik) okuyan, bu tanımlardan tek bir birleşik DFA kuran ve bir kaynak dizgeyi en uzun eşleşme ve öncelik kurallarıyla belirteçlere ayıran bir araç yaz. Araç her belirtecin türünü, lexemini ve satır/sütun konumunu döndürsün. Hatalı karakterleri belirtip tarayıcıyı durdurmadan devam etsin.

**Yapılacak / Beklenen davranış:** Küçük bir dilin belirteçleri için (tam sayı, ondalık, tanımlayıcı, anahtar kelimeler `eğer`, `değilse`, `döngü`, operatörler `==`, `=`, `<=`, `<`, yorumlar `//`) tanım dosyası yaz. `x <= 10 // yorum` girdisinde `<=` tek belirteç olmalı; `eğer` anahtar kelime, `eğerx` tanımlayıcı olmalı. Hatalı bir karakter (ör. `@`) bir hata listesine yazılmalı ve tarama devam etmeli.

**Önerilen yaklaşım (ipucu):** Her tanımı kendi NFA'na çevir (Thompson), bütün NFA'ları yeni bir başlangıç durumuna ε-kenarlarıyla bağla, sonra alt küme yapısıyla DFA kur. Her kabul durumuna, o kabul durumunu üreten tanımların en yüksek önceliğini ata. Tarama sırasında son kabul durumunu ve girdi konumunu kaydet; en uzun eşleşmeye ulaşınca o belirteci üret ve konumu ilerlet. Anahtar kelime ile tanımlayıcı çakıştığında öncelik kuralını kullan. Hata durumunda tek karakter tüket ve hata kaydet.

**Başarı kriterleri:**
- En az altı belirteç türünde doğru sonuç; her biri için beş örnek girdi (kabul ve red) içeren bir test dosyası.
- `==` ve `=`, `<=` ve `<`, `1e5` ve `1e` ayrımlarının doğru olduğu gösterilmiş olmalı (bunların son ikisi bu bölümde incelenen Doruk davranışının karşılaştırmasıdır).
- Rastgele 2000 kaynak satırında, her belirtecin lexemlerinin birleştirilmesi girdiye eşit olmalı (kayıp ya da çoğalma yok).
- Tarayıcının toplam süresi, girdi boyutuyla doğrusal olarak artmalı; bunu iki farklı boyutla ölçüp raporla.

## Ek Alıştırmalar

Aşağıdaki problemlerin çözümü bu kitapta yok. Önce kâğıda, sonra editöre geç. Zorluk etiketi ile sırala. Mülakat olarak işaretlenenler klasik sorulardır.

1. **★ — Son iki bit.** Yalnızca 0 ve 1 harflerinden oluşan dizgelerde sonu `01` ile biten dizgeleri tanıyan bir DFA çiz. Kaç durumu var ve neden üç yeterli?

2. **★ — Eşit sayıda.** Σ = {a, b} üzerinde, a ve b sayıları eşit olan dizgelerin dilinin düzenli olup olmadığını pompalama lemmasıyla karar ver. Kanıtını kendi sözlerinle yaz.

3. **★★ — Parantez dengesi (Mülakat).** Tek tür parantezle (sadece `(` ve `)`) dengeli dizgeleri tanıyan bir yığınsız makine olabilir mi? Düşüncen için iki dizge karşılaştır: `(()` ve `()()`.

4. **★★ — Subset ile durum sayısı.** n durumlu bir NFA'yı alt küme yapısıyla DFA'ya çevirdiğinde en fazla kaç DFA durumu olabilir? Bu üst sınırı ulaşan bir NFA ailesini kur (36.3'teki L_n ailesini ipucu olarak kullan).

5. **★★ — Minimal DFA (Mülakat).** Yalnız üç durumlu bir DFA verildiğinde, bu DFA minimal değilse hangi tabloyla bunu gösterirsin? Tablo doldurmada hangi çiftler ilk adımda işaretlenir?

6. **★★ — Düzenli ifade (Mülakat).** `(a|aa)*` ifadesinin dildeki anlamını yaz. Bu desenin Python `re` ile `aaaa...!` girdisinde neden yavaşlayabileceğini açıkla; ipucu: iki farklı yol aynı dizgeyi eşler.

7. **★★ — Belirsizlik (Mülakat).** Aşağıdaki gramerin hangi dizgeyi belirsiz kıldığını bul ve bir düzeltme öner: S → a S | S a | a.

8. **★★ — FIRST kümeleri.** S → A B, A → a | ε, B → b. FIRST(S), FIRST(A), FIRST(B) ve FOLLOW(A) kümelerini kâğıtta hesapla. Sonra `ll1.py`'nin mantığına uygun olarak kodla doğrula.

9. **★★★ — CYK'nın karmaşıklığı (Mülakat).** CYK algoritmasının O(n³·|G|) zamanda çalıştığını gösteren döngü sayımını yap. Gramer boyutu |G| büyüdüğünde bu neden ayrı bir sorun olur?

10. **★★★ — Turing'den PDA'ya.** İki yığınlı bir makine, tek bant Turing makinesini simüle edebilir (genel bilgi). Bu gerçeği kullanarak tek yığınlı bir PDA'nın neden aⁿbⁿcⁿ'yi tanıyamayacağı sezgisini açıkla.

11. **★★★ — Lexer hatası (Mülakat).** Varsayımsal bir lexer, `1..5` girdisini `1.` (ondalık) ve `.5` olarak ayırıyor. Hangi kural bu yanlış ayrıma yol açtı ve nasıl düzeltilir? İpucu: en uzun eşleşme kuralı burada ne diyor?

12. **★★★ — ReDoS savunması (Mülakat).** Bir web formu e-posta doğrulaması için `^([a-z0-9]+)*@` gibi bir desen kullanıyor. Bu desenin hangi girdiyle patlayacağını açıkla ve iki farklı düzeltme öner: biri deseni değiştiren, diğeri girdiyi sınırlayan.

## Kod Okuma Egzersizi

Aşağıdaki kesit Mert'in kendi Doruk dilinin sözcüksel analizcisinden alınmıştır: `D:\Mevcut Projeler\GitHub\Mert-Studio-Code-v2\doruk\engine\src\Lexer.cpp`, satır 672–689 (birebir, değiştirilmeden). Fonksiyon, tanımlayıcı ve anahtar kelime ayrımını yapar.

```cpp
Token Lexer::kimlikTara(uint32_t basSatir, uint32_t basSutun) {
    // Kaynak byte konumunu kaydet — lexem için slice alacağız
    size_t bas = konum_;

    // İlk kod noktasını tüket (zaten başlangıç olduğu doğrulandı)
    utf8OkuIlerle();

    // Devam karakterlerini tüket
    while (!bitti() && kimlikDevamMi(utf8MevcutBak())) {
        utf8OkuIlerle();
    }

    // Kaynak metinden slice al — ham byte'lar (UTF-8)
    std::string lexem = kaynak_.substr(bas, konum_ - bas);

    // Anahtar kelime tablosunda ara
    const auto& tablo = anahtarKelimeler();
    auto it = tablo.find(lexem);
```

**Sorular — cevaplamadan geçme:**

1. Bu fonksiyon hangi durum makinesinin hangi kısmını gerçekler? Başlangıç durumunu, döngü durumunu ve kabul durumlarını kaynakta göster (satır numaralarıyla).
2. En uzun eşleşme kuralı nerede sağlanıyor? `while` döngüsü neden bir karakterde durmaz, ne zaman durur?
3. `lexem` dizgesi neden `kaynak_.substr` ile alınıyor, neden karakter karakter biriktirilmiyor? Bu seçimin UTF-8 çok baytlı karakterler için ne faydası var?
4. Anahtar kelime tablosu neden tanımlayıcı üretilmeden önce aranıyor ve sıra değişirse hangi girdi yanlış sınıflanır?
5. 36.14'te gösterdiğimiz `printf 'g\xcc\x86\xc4\xb1\n'` (NFD) girdisi bu fonksiyonda neden üç parçaya bölünüyor? Tam olarak hangi satırda devam karakteri testi başarısız olur? (İpucu: `while` koşulu.)
6. Bir düzeltme öner: `kimlikDevamMi` ve `kimlikBaslangiciMi`'ni, Unicode kategorilerine (`L*`, `Nd`, `_`) dayanan bir tabloyla değiştirirsen hangi girdiler değişir, hangileri değişmez? Değişikliği uygulamadan önce hangi testleri eklemen gerekir?

## Bölüm Özeti

- **Dil**, `Σ*` üzerinde bir alt kümedir; dillerin birleşimi, eklemesi ve Kleene yıldızı düzenli ifadelerin temelidir.
- **DFA** beşlisi (Q, Σ, δ, q0, F) ile tanımlanır; sınırlı belleğle, tek geçişte tanır. Üç'e bölünebilirlik bunun en küçük örneğidir.
- **NFA** belirsizlik içerir ama alt küme yapısıyla her NFA'ya eşdeğer bir DFA vardır; durum sayısı en fazla 2^n'e çıkabilir ve bu sınır ulaşılabilir (L_n ailesi).
- **Minimizasyon**, denk durumları tablo doldurmayla bulur; minimal DFA tektir ve Myhill–Nerode ile karakterize edilir.
- **Thompson yapısı** düzenli ifadeyi doğrusal boyutlu bir NFA'ya çevirir; NFA simülasyonu girdi uzunluğuyla doğrusal çalışır.
- **Katastrofik geri izleme** (ReDoS): geri izlemeli motorlar üstel süre harcayabilir; ölçümde 2^n büyümeyi gördük ve savunma kurallarını çıkardık.
- **Pompalama lemması** aⁿbⁿ gibi dillerin düzenli olmadığını kanıtlar; **bağlamdan bağımsız gramerler** ağaçla ve belirsizlikle anlatılır, öncelik katmanları belirsizliği giderir.
- **CYK** CNF gramerleri O(n³·|G|) sürede tanır ve ağaç sayar; **FIRST/FOLLOW** öngörülü ayrıştırıcının seçim kümeleridir.
- **Chomsky hiyerarşisi** dört sınıf ve tanıyıcılarını (DFA, PDA, LBA, TM) verir; **Turing makinesi** ve durma problemi, hesaplanabilirliğin sınırını gösterir.
- **Sözcüksel analiz** en uzun eşleşme, öncelik ve tanımlayıcı-anahtar kelime ayrımıyla çalışır; Doruk lexer'ı bu kuralların gerçek bir uygulamasıdır ve Unicode sınırlarında somut hatalar gösterir.

**Sonraki bölümde:** Bölüm 37 (Derleyici Nasıl Çalışır) bu bölümde kurduğumuz sözcüksel analizi bir derleyicinin bütününe bağlıyor: belirteçler ayrıştırıcıdan (parser) geçip bir sözdizim ağacına (AST), oradan anlamsal analize, ara koda, optimizasyona ve kod üretimine ya da yorumlayıcıya dönüşüyor. Bu bölümdeki LL(1) kümelerinin (FIRST ve FOLLOW) tabloya nasıl dönüştüğünü ve Doruk'un gerçek ayrıştırıcısının bunları nasıl kullandığını orada göreceksin. Bu bölümde açık bıraktığımız "bağlam nerede girer?" sorusu da orada, anlamsal analiz başlığı altında cevaplanacak.

::: mulakat
Aşağıdaki sorular cevapsızdır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. Düzenli ifade ile DFA arasındaki ilişki nedir? Bir regex'i DFA'ya çevirmek neden her zaman üstel durum patlamasına yol açmaz, ama bazen açar?
2. NFA ile DFA aynı dili tanıyorsa, neden NFA kullanmak bazen daha iyidir? Bir sürüm kontrol sisteminin dal adlarını doğrulayan bir sistemde hangisini seçersin ve neden?
3. `(a*)*b` gibi bir desen neden tehlikelidir? Bir ReDoS saldırısının olabilmesi için girdide hangi özelliklerin bulunması gerekir?
4. Pompalama lemmasını bir dil için kullandığında, "karşı taraf" ve "sen" hangi seçimleri yapar? Neden çelişki elde etmek için w'yi dikkatli seçmek gerekir?
5. Bir ayrıştırıcıda `if (a) if (b) x; else y;` yazıldığında else hangi if'e bağlanır? Gramerde bunu nasıl yazarsın ve hangi kural C ve Java'da kullanılır?
6. Bir sözcüksel analizci neden bir ayrıştırıcıdan önce gelir? Bu iki aşamayı tek bir gramer olarak yazmak neden pratik değildir?
7. Bir programın verilen girdide sonsuz döngüye girip girmeyeceğini bilen genel bir araç yazılabilir mi? Cevabını köşegenleştirme argümanıyla açıkla ve bu sonucun statik analiz araçlarını nasıl sınırladığını anlat.
:::
