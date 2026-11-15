## 23.7 Sabitler, sihirli sayılar ve tekrar

### Sihirli sayılar

Bir kodda `60` yazılı görüyorsan, o 60'ın ne olduğunu koddan çıkaramazsın: sıcaklık eşiği mi, saniye mi, bir tablonun boyutu mu? Çıplak bir sayı, okurun bağlamı kendi kafasında yeniden kurmasını gerektirir. Buna sihirli sayı (magic number) denir. Aynı sayı birden çok yerde geçiyorsa daha kötü bir durum vardır: birini değiştirdiğinde diğerlerini de değiştirmeyi unutursun.

Bölüm 23.5'te gördüğümüz clang-tidy, `readability-magic-numbers` kontrolüyle `uyari.c` içindeki `100`, `10` ve `0.256` sayılarını işaretledi. Çözüm, sayıya bir ad vermektir. Bunun iki temel yolu var:

- **Sabit:** Değeri değişmeyen ve bir yerde tanımlanan bir ad. Python'da modül düzeyinde büyük harfli bir ad (`SICAKLIK_KRITIK = 60.0`) bu iş içindir. C'de tamsayı sabitleri için `enum` ya da `#define` kullanılır. Dikkat: C'de `const int` bir değişkendir; dizi boyutu ya da `case` etiketi gibi derleme zamanı sabiti gereken yerlerde kullanılamaz. Bu, C'ye özgü genel bilgidir ve burada derleyiciyle doğrulamadık.
- **Enum:** Birbiriyle ilişkili sabit kümeleri için. Enum'un asıl gücü, derleyicinin yeni bir değer eklendiğinde eksik kalan `switch` dallarını söylemesidir. Aşağıdaki dosyada `enum`'a `KRITIK` eklendi ama `switch` içinde karşılığı yazılmadı:

```c
#include <stdio.h>
enum durum { TAMAM, UYARI, KRITIK };
static int yardimci(void) { return 1; }
int kodu(enum durum d)
{
    switch (d) {
    case TAMAM: return 0;
    case UYARI: return 1;
    }
    return -1;
}
int main(void) { printf("%d\n", kodu(KRITIK)); return 0; }
```

Derleyici bu eksiği bildirir:

```term
$ gcc -std=c11 -Wall -c sw.c
sw.c: In function ‘kodu’:
sw.c:6:5: warning: enumeration value ‘KRITIK’ not handled
  in switch [-Wswitch]
sw.c: At top level:
sw.c:3:12: warning: ‘yardimci’ defined but not used
  [-Wunused-function]
```

Bu uyarının değeri şudur: enum'a yeni bir durum eklediğinde, o durumu işlemeyi unuttuğun her `switch` derleyicide işaretlenir. Aynı kodu `default:` dalı ile yazarsan bu koruma kaybolur; bu yüzden kod incelemesinde `default` dalının neden gerektiğini sormak iyi bir alışkanlıktır. Uyarıdaki ikinci mesaj ise bir sonraki alt bölümde, kod kokuları içinde ele alınacak.

### Tekrar (DRY) ve yanlış soyutlama

DRY (Don't Repeat Yourself, kendini tekrarlama) ilkesi, aynı bilginin kodda birden çok yerde yaşamaması gerektiğini söyler. Önemli kelime "bilgi"dir, "metin" değil. İki kod parçası metin olarak aynı görünebilir ama farklı kavramları temsil ediyorsa birleştirmek hata üretir. Bu yüzden iki kural birlikte düşünülmelidir.

Pratik bir ölçüt: bir kod parçasını ilk iki kez tekrar edilirken görürsen, çoğu zaman tekrara izin ver. Üçüncü kez tekrar ettiğinde ortak bir soyutlama düşün (buna "üç kez kuralı" denir; genel bilgi). Neden iki kez? Çünkü iki kopyanın değişme nedenleri hâlâ farklı olabilir ve yanlış bir ortak fonksiyon ikisini birden bozar.

Yanlış soyutlamanın belirtisi, ortak fonksiyonun içinde bir `mod` ya da `bayrak` parametresi ile dallanan bir if zincirinin oluşmasıdır. Böyle bir fonksiyon iki işi birden yapar ve her çağrıda hangi işin yapıldığını parametreden çözmek zorunda kalırsın. Bu durumda iki ayrı fonksiyon, birbirine benzeyen ama kendi başına anlaşılır iki kod, çoğu zaman daha iyidir.

## 23.8 Kod kokuları: belirtiden tedaviye

Kod kokusu (code smell), kodun bir hata olmadığı ama bir sorun işaret ettiği durumdur. Kokuyu gördüğünde hemen bir hata aramak yerine, o kokunun giderilmesinin davranışı koruyup korumadığına bakarsın. Martin Fowler ve arkadaşlarının refactoring kitabı bu fikri adlandırılmış bir kataloğa dönüştürdü (genel bilgi). Aşağıdaki şekil, bu bölümde gördüğümüz başlıca kokuları ve her biri için kullanılan giderme adımını bir arada veriyor.

![Şekil 23.4: Kod kokusu ile refactoring arasındaki eşleşme. Her koku, davranışı koruyan belirli bir dönüşümle giderilir.](gorseller/b23_koku_haritasi.png)

Koku listesini ve belirtilerini kısaca açıklayalım:

- **Uzun fonksiyon:** Birden çok soyutlama seviyesi aynı gövdede. Örnek 4'teki `rapor_uret` 42 satırlık bir gövdeydi ve beş ayrı iş yapıyordu. Giderme: Extract Function.
- **Uzun parametre listesi:** Dört ve üzeri parametre, özellikle aynı tipte olanlar. Giderme: Introduce Parameter Object (ilgili parametreleri bir yapıda toplamak).
- **Sihirli sayı:** Bölüm 23.7'de gördüğümüz gibi. Giderme: sabit ya da enum.
- **İlkel takıntısı (primitive obsession):** Bir kavramı tuple ya da düz sayı ile temsil etmek. Örnek 1'de `ham[3]` bir indeksti; dördüncü alanın ne olduğunu her seferinde hatırlaman gerekirdi. Giderme: Replace Primitive with Object (Python'da `NamedTuple` ya da `dataclass`).
- **Kopya kod:** Aynı bilginin birden çok yerde yaşaması. Giderme: ortak fonksiyon, ama yalnızca aynı değişme nedenine sahip kopyalar için.
- **Ölü kod:** Hiçbir yerden çağrılmayan fonksiyon, kullanılmayan değişken. Giderme: sil. Ölü kod, okuru boşuna meşgul eder ve yanlış bir güven verir ("bu bir yerde kullanılıyor olmalı").
- **Yorum kokusu:** Kodun ne yaptığını tekrar eden ya da eskimiş yorumlar. Giderme: adı iyileştir ve yorumu sil (Bölüm 23.4).
- **Tip koşullarının zinciri:** Bir tipe göre dallanan uzun if/elif yapısı. Giderme: Replace Conditional with Polymorphism.

Ölü kodun derleyici tarafından nasıl yakalandığını gördük. `sw.c` içindeki `yardimci` fonksiyonu `static` olarak tanımlandığı ve kullanılmadığı için `-Wunused-function` uyarısı aldı. Dikkat: fonksiyon `static` değilse derleyici bunun kullanılmadığını bilemez, çünkü başka bir dosya onu çağırabilir. Bu yüzden `static` anahtar sözcüğü hem kapsülleme hem de ölü kod tespiti için değerlidir.

### Tip zincirini polimorfizme çevirmek

Tip koşullarının zinciri en sık görülen kokulardan biridir. Aşağıdaki kod, üç farklı sensör tipini bir `if-elif` zinciriyle dönüştürüyor. Her yeni sensör tipinde bu zinciri ve onu çağıran her yeri değiştirmen gerekir.

```python
def olc_kosul(tip, ham):
    if tip == "sicaklik":
        return ham * 0.1 - 40.0
    elif tip == "basinc":
        return ham * 0.01
    elif tip == "nem":
        return min(max(ham, 0.0), 100.0)
    raise ValueError(tip)
```

Aynı davranışı her tip için bir sınıf ile yazabiliriz. Her sınıf kendi dönüşümünü bilir; çağıran yalnızca "dönüştür" der. Bu, polimorfizmin (çok biçimliliğin) en küçük örneğidir. Sistem düzeyinde aynı fikir Bölüm 22'de Strategy kalıbı olarak karşına çıkacak.

```python
from abc import ABC, abstractmethod


class Olcekleyici(ABC):
    @abstractmethod
    def donustur(self, ham: float) -> float: ...


class Sicaklik(Olcekleyici):
    def donustur(self, ham: float) -> float:
        return ham * 0.1 - 40.0


class Basinc(Olcekleyici):
    def donustur(self, ham: float) -> float:
        return ham * 0.01


class Nem(Olcekleyici):
    def donustur(self, ham: float) -> float:
        return min(max(ham, 0.0), 100.0)


SINIFLAR = {"sicaklik": Sicaklik(), "basinc": Basinc(), "nem": Nem()}
```

Yeni yapı, yeni bir sensör tipi eklemeyi bir sınıf eklemeye ve sözlüğe bir satır yazmaya indirger. Eski zincirin davranışını korumak için ilk olarak ikisini karşılaştırdık: 10000 rastgele girdi (tohum 42) için iki yöntemin sonuçları birebir eşitti (uyuşmayan: 0).

Dikkat: her if-elif zinciri kötü değildir. Zincir sabit ve az sayıda durum için yazıldıysa ve başka yerde tekrarlanmıyorsa, sınıf hiyerarşisi gereksiz karmaşıklık getirir. Kötü olan, zincirin her yeni durumda büyümesi ve aynı zincirin birden çok yerde kopyalanmasıdır.

## 23.9 Refactoring: güvenlik ağı ve karmaşıklık ölçümü

Refactoring, davranışı değiştirmeden kodun iç yapısını iyileştirmektir. Kritik kelime "davranış"tır: eski ve yeni sürüm, ilgilendiğin girdilerin hepsi için aynı çıktıyı üretmelidir. Bu tanım, refactoring ile "bir de şunu ekleyeyim" arasındaki farkı belirler. İkisini aynı commit'te yaparsan hangisinin bir hataya yol açtığını ayıramazsın.

Refactoring'in ikinci kuralı küçük adımlardır: her adım derlenebilir ve test edilebilir olmalı, adımlar birbirinin üstüne yığılmamalı. Üçüncü kural, bir güvenlik ağı kurmadan başlamamaktır. Bu güvenlik ağı, "şu an bu kod ne yapıyor?" sorusunu cevaplayan bir testtir.

### Karakterizasyon testi ve güvenlik döngüsü

Elinde test yoksa, önce eski davranışı kaydet. Bu, bir karakterizasyon testidir: kodun ne yaptığını bugünkü haliyle belgeleyen bir test (bu terim, eski kodla çalışmayı anlatan literatürden gelir; genel bilgi). Doğru mu yanlış mı olduğu önemli değildir; amaç değişikliği görünür kılmaktır.

![Şekil 23.5: Refactoring güvenlik döngüsü. Her küçük dönüşüm, kayıtlı çıktılarla karşılaştırılır; uyuşmazlıkta adım geri alınır.](gorseller/b23_guvenlik_dongusu.png)

Örnek 4'te bu döngüyü uyguluyoruz. Karakterizasyon testimiz, 300 farklı rastgele girdi üretir (her biri 0-25 satırlık ölçüm kaydı; bazıları hatalı biçimde) ve her girdinin çıktısının SHA-256 özetini bir dosyaya kaydeder. Girdi üretici, bilerek hatalı satırları da içerir; çünkü davranışın asıl kırılma noktaları genellikle hata yollarıdır.

Karakterizasyon betiğinin tamamı iki parçada aşağıda. İlk parça girdi üreticisidir; bozuk satırları bilerek üretir.

```python
import hashlib
import importlib
import json
import random
import sys


def girdi_uret(rng):
    satirlar = []
    for _ in range(rng.randint(0, 25)):
        r = rng.random()
        if r < 0.05:
            satirlar.append("   ")
        elif r < 0.08:
            satirlar.append("# yorum satiri")
        elif r < 0.12:
            satirlar.append("ALFA;12;abc;V")
        elif r < 0.15:
            satirlar.append("BETA;xy;1.0;V")
        elif r < 0.18:
            satirlar.append("GAMA;5;2.0;kV")
        else:
            cihaz = rng.choice(["ALFA", "BETA", "GAMA", "DELTA"])
            zaman = str(rng.randint(0, 999))
            deger = "%.4f" % rng.uniform(2.0, 4.5)
            if rng.random() < 0.3:
                deger = "%.1f" % rng.uniform(2000, 4500)
            birim = rng.choice(["V", "V", "mV"])
            satirlar.append(";".join([cihaz, zaman, deger, birim]))
    return satirlar
```

İkinci parça, her girdi için çıktının özetini alır, altın kaydı yazar ya da kayıtla karşılaştırır:

```python
def ozet(modul_adi):
    modul = importlib.import_module(modul_adi)
    rng = random.Random(42)
    sonuc = []
    for _ in range(300):
        cikti = modul.rapor_uret(girdi_uret(rng))
        ham = cikti.encode("utf-8")
        sonuc.append(hashlib.sha256(ham).hexdigest())
    return sonuc


if __name__ == "__main__":
    if sys.argv[1] == "--kaydet":
        ozetler = ozet(sys.argv[2])
        with open("golden.json", "w", encoding="utf-8") as f:
            json.dump(ozetler, f)
        print("kaydedildi:", sys.argv[2], len(ozetler))
    else:
        with open("golden.json", encoding="utf-8") as f:
            beklenen = json.load(f)
        gercek = ozet(sys.argv[1])
        bozuk = [i for i, (a, b) in enumerate(zip(beklenen, gercek))
                 if a != b]
        print("sinanan:", len(gercek), "bozuk:", len(bozuk),
              "ilk:", bozuk[:3])
```

Altın kayıt, eski `rapor_uret`'ten alındı (`karakter.py --kaydet adim0`). Her yeni sürüm bu 300 özetle karşılaştırılır; tek bir bayt farklılığı bile bozukluk olarak sayılır. Burada kritik nokta, testin kendisinin hata yakalayıp yakalamadığıdır. Bunu mutasyon testi ile sınadık: eski kodun bilerek bozulmuş kopyalarını üretip karakterizasyon testinden geçirdik.

| Mutant | Değişiklik | Bozuk çıktı (300 içinden) |
|---|---|---|
| Eşik kayması | `ESIK = 3.6` yerine `3.5` | 22 |
| Sütun sırası | `minimum` ve `maksimum` yer değiştirdi | 244 |

İki mutant da yakalandı. Eşik kayması az sayıda girdide görünür (yalnızca maksimumu eşik civarında olan cihazlarda), sütun sırası ise neredeyse her çıktıda. Bu fark bir şey söyler: testin duyarlılığı girdi dağılımına bağlıdır. Eşik gibi sınır değerlerini hedefleyen girdiler eklemek bu boşluğu kapatır.

### Döngüsel karmaşıklık

Refactoring'in başarısını ölçmek için bir metriğe ihtiyacımız var. En bilinen metriklerden biri döngüsel karmaşıklık (cyclomatic complexity, CC) ölçüsüdür; McCabe 1976'da tanımladı (genel bilgi). Tanım şöyledir: bir fonksiyonun kontrol akış grafiğinde bağımsız yolların sayısı. Pratikte kolay hesap şudur:

**CC = karar noktası sayısı + 1**

Karar noktaları `if`, `for`, `while`, `case`, `&&`, `||` (Python'da `and` / `or`), koşullu ifade ve istisna yakalama bloklarıdır. Şekil 23.6, Örnek 2'deki `alarm_karari` fonksiyonunun akış grafiğini gösteriyor: yedi karar noktası ve sekiz çıkış. Her çıkış ayrı bir yoldur; bu yüzden CC = 8.

![Şekil 23.6: alarm_karari için kontrol akış grafiği. Yedi karar noktası, sekiz çıkış; döngüsel karmaşıklık 8.](gorseller/b23_cfg_alarm.png)

CC'nin neyi ölçtüğünü görmek için kendi ölçüm aracımızı yazalım. Araç, Python'un `ast` modülüyle kaynak kodu soyut sözdizimi ağacına çevirir ve her fonksiyon için dört ölçü hesaplar: satır sayısı, parametre sayısı, en derin iç içe yapı (derinlik) ve döngüsel karmaşıklık. Ayrıca bilişsel karmaşıklığa benzer bir puan verir: iç içe yapıyı derinliğe göre cezalandırır. Bu puan, resmi bir tanım değil, basitleştirilmiş bir yaklaşımdır; sonuçlarını bu nedenle yorumlarken dikkatli olmalısın.

Aracın ilk parçası karar noktalarını sayar ve derinliği ölçer:

```python
# karmasiklik.py: fonksiyon basina satir, parametre, derinlik, CC
import ast
import sys

KARAR = (ast.If, ast.For, ast.While, ast.IfExp, ast.ExceptHandler,
         ast.comprehension, ast.Assert)
DERIN = (ast.If, ast.For, ast.While, ast.With, ast.Try)


def cc_hesapla(dugum):
    """McCabe: 1 + karar noktalari (BoolOp'ta her ek islem +1)."""
    sayi = 1
    for d in ast.walk(dugum):
        if isinstance(d, KARAR):
            sayi += 1
        elif isinstance(d, ast.BoolOp):
            sayi += len(d.values) - 1
    return sayi


def derinlik(dugum, seviye=0):
    en_derin = seviye
    for c in ast.iter_child_nodes(dugum):
        if isinstance(c, DERIN):
            en_derin = max(en_derin, derinlik(c, seviye + 1))
        else:
            en_derin = max(en_derin, derinlik(c, seviye))
    return en_derin
```

İkinci parça bilişsel puanı hesaplar. Her `if` ve döngü, bulunduğu iç içelik seviyesi kadar ek puan alır; `else` ve mantıksal işleçler de puana katkı verir:

```python
def bilissel_hesapla(dugum, seviye=0):
    """Ic ice yapiyi cezalandiran sayim (bilissel karmasiklik benzeri)."""
    puan = 0
    for c in ast.iter_child_nodes(dugum):
        if isinstance(c, ast.If):
            puan += 1 + seviye
            if c.orelse and not (len(c.orelse) == 1
                                 and isinstance(c.orelse[0], ast.If)):
                puan += 1
            puan += bilissel_hesapla(c, seviye + 1)
        elif isinstance(c, (ast.For, ast.While)):
            puan += 1 + seviye
            puan += bilissel_hesapla(c, seviye + 1)
        elif isinstance(c, ast.BoolOp):
            puan += len(c.values) - 1
            puan += bilissel_hesapla(c, seviye)
        else:
            puan += bilissel_hesapla(c, seviye)
    return puan
```

Üçüncü parça dosyayı tarar ve tabloyu basar:

```python
def tara(yol):
    with open(yol, encoding="utf-8") as f:
        agac = ast.parse(f.read(), filename=yol)
    sonuc = []
    for d in ast.walk(agac):
        if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef)):
            satir = d.end_lineno - d.lineno + 1
            param = len(d.args.args) + len(d.args.kwonlyargs)
            sonuc.append((yol, d.name, satir, param,
                          derinlik(d), cc_hesapla(d), bilissel_hesapla(d)))
    return sonuc


if __name__ == "__main__":
    print("%-22s %5s %4s %4s %4s %5s" % ("fonksiyon", "satir", "par",
                                         "der", "cc", "bilis"))
    for yol in sys.argv[1:]:
        for _, ad, s, p, dr, c, b in tara(yol):
            print("%-22s %5d %4d %4d %4d %5d" % (ad, s, p, dr, c, b))
```

Örnek 1 ve 2'nin eski ve yeni sürümleri üzerinde çalıştırdığımızda:

```term
$ python karmasiklik.py ex1_eski.py ex1_yeni.py ex2_eski.py ex2_yeni.py
fonksiyon              satir  par  der   cc bilis
f                         22    3    2   11    14
kayit_oku                  5    1    1    4     3
kayit_uygun_mu             2    2    0    2     1
skor_hesapla               3    1    0    1     0
kritik_skorlar            10    2    2    5     6
kritik_ozet               12    3    2    5     5
alarm_karari              17    3    6    8    26
alarm_karari              17    3    2    8     8
```

Bu tabloda dikkat edilecek üç şey var. Birincisi, Örnek 1'de eski `f` 11 CC'ye ve 22 satıra sahipken, yeni fonksiyonların en büyüğü 5 CC'de kalıyor. Ayrıca `radon` (yaygın bir Python karmaşıklık aracı) aynı dosyalar için `f` fonksiyonuna C (11), `alarm_karari` fonksiyonuna B (8) notu verdi; yani aracımızın CC hesabı bu iki durumda radon ile uyuşuyor.

İkincisi ve daha önemlisi: Örnek 2'de eski ve yeni `alarm_karari` fonksiyonlarının CC'si ikisinde de 8. Koruma cümleleri karar noktası sayısını azaltmadı; bir `if` yine bir `if`. Buna karşılık derinlik 6'dan 2'ye indi ve bilişsel puan 26'dan 8'e düştü. Yani CC, koşulların sayısını ölçer; okurun zihinsel yükünü ölçmez. İç içe yapının cezası, ancak derinlik ya da bilişsel bir puan ile yakalanır. Bu yüzden tek bir metriğe güvenmek yanıltıcıdır.

Üçüncüsü: "daha az karmaşık" her zaman "daha az kod" anlamına gelmez. Örnek 4'te fonksiyon sayısı arttı, ama en karmaşık fonksiyonun CC'si 12'den 6'ya düştü. Toplam karmaşıklık artabilir; ama parça başına okunabilirlik artar, ve bu okurun gerçekten ihtiyaç duyduğu şeydir.

Şekil 23.7 Örnek 1, 2 ve 4'ün en karmaşık fonksiyonunun önce ve sonra değerlerini karşılaştırıyor. Değerler, yukarıdaki aracın çıktısından ve `engine/veri/b23_karmasiklik.csv` dosyasından okunmuştur.

![Şekil 23.7: Üç örnekte en karmaşık fonksiyonun döngüsel ve bilişsel ölçümü, önce ve sonra.](gorseller/b23_karmasiklik_olcum.png)

Ekip kuralı olarak CC için sık kullanılan bir eşik, McCabe'in önerdiği 10 değeridir (genel bilgi). Bu eşik bir yasa değildir; ama bir fonksiyon bu sınırı aşıyorsa, neden aştığını açıklayabilmen gerekir.

## 23.10 Savunma sanayiinde kod: standartlar ve kod incelemesi

Savunma ve havacılık yazılımında kod, yalnızca çalışması değil, kanıtlanabilir biçimde güvenli olması için yazılır. Bu yüzden ekipler, hangi C ve C++ kalıplarının yasak ya da kısıtlı olduğunu belirleyen kodlama standartlarını kullanır. Aşağıdaki liste genel bilgidir; kural numaralarını ve tam kapsamını burada vermiyoruz, çünkü bunları kendi standardının güncel metninden doğrulamak gerekir.

- **MISRA C:** Güvenlik kritik gömülü C için yaygın bir kurallar kümesidir. Dinamik bellek ayırmayı (standart kütüphanedeki bellek ayırma fonksiyonları) kısıtlar, işaretli ve işaretsiz tamsayıların karıştırılmasını sınırlar, tanımsız davranışa yol açabilecek yapıları yasaklar. Bu bölümdeki `-Wsign-compare` örneği, bu tür kısıtların neden önemli olduğunu somut olarak gösterir.
- **CERT C:** Güvenli C kodlama için SEI/CERT'in standardıdır. Bellek sahipliği, kaynakların serbest bırakılması, standart kütüphane hata dönüş değerlerinin kontrolü gibi konuları kapsar. Örnek 3'teki `fclose` ve tek temizleme yolu tartışması bu alana girer.
- **JSF AV C++:** Bir savaş uçağı programı için yazılmış C++ kodlama standardıdır. Dinamik bellek ayırmayı ve istisnaları kısıtladığı genel olarak bilinir; bu kısıtların tam kapsamı için standardın metnine bakmak gerekir.

Standartlar iki türlü denetlenir. Bazı kurallar derleyici ve statik analiz araçlarıyla otomatik denetlenebilir: bu bölümde gördüğümüz `-Wall -Wextra -Wshadow -Wconversion`, clang-tidy ve `-fanalyzer` bu türdendir. Kalanı insan incelemesi ister: bir fonksiyonun niyeti, bir sınırın doğruluğu, bir hata yolunun tamamlığı gibi şeyler araçla kolay ölçülmez. Bu yüzden kod incelemesi (code review), bu standartların son ve en önemli kapısıdır.

Kod incelemesinde kullanabileceğin bir kontrol listesi:

- Adlar niyeti söylüyor mu? Yorum kodu tekrar etmek yerine neden'i anlatıyor mu?
- Fonksiyon tek bir iş yapıyor mu? Adından anlaşılmayan bir yan etki var mı?
- Her dönüş kodu kontrol ediliyor mu? Her hata yolunda kaynaklar serbest bırakılıyor mu?
- Sihirli sayı var mı? Varsa neden orada olduğu bağlamla açıklanmış mı?
- Derleyici uyarısı var mı (en azından `-Wall -Wextra` ile)?
- Değişiklik karakterizasyon ya da birim testiyle korunuyor mu?
- Tekrar var mı, yoksa yanlış bir soyutlama mı yapılmış?
- Değişiklik tek bir amaca hizmet ediyor mu (küçük bir diff mi)?
- Yeni bir `if` zinciri ya da `switch` eklenmiş mi; enum değişince eksik dallar derleyici tarafından yakalanıyor mu?

Son madde, daha önce gördüğümüz `-Wswitch` uyarısına doğrudan bağlanır: bir enum'a değer eklendiğinde derleyicinin uyarısı, incelemeci için "bu switch'i de güncelle" sinyalidir.
