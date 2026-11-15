%% kisim_no: VIII
%% kisim_ad: Veritabanı
%% bolum_no: 34
%% baslik: SQL Derinlemesine

## Giriş: Sorgu yazmak kolay, doğru ve hızlı sorgu yazmak zor

Her yazılımcı bir gün `SELECT * FROM` yazar ve sonuç ekrana gelir. Zorluk, sonucun doğru olup olmadığını anlamakta, sorgunun on milyon satırda bir saniyede mi yoksa on dakikada mı döneceğini bilmekte ve yanlış bir `WHERE` yazıldığında bunun kimsenin dikkatini çekmeyeceğini fark etmekte başlar. SQL sana ne istediğini söyler; nasıl hesaplanacağını ise motor seçer. Bu ayrım, bölümün bütün konusudur.

Bölüm 33'te ilişkisel modeli, anahtarları, normalizasyonu ve B+ ağacının iç yapısını gördün. O bölüm "veri neden böyle tasarlanır" sorusuna cevap verdi. Bu bölüm bir sonraki soruya cevap verir: tasarlanmış veriyi sorgularken ne yazmalısın, motor bu sorguyu nasıl çalıştırır ve sonuç neden bazen yanlış, bazen yavaş çıkar?

Bölüm 16'da bir DP tablosunu satır satır doldurmuştun. Bölüm 17'de bir grafın üzerinde BFS ile dolaşmıştın. Özyinelemeli CTE, bu iki fikri SQL'in içinde yeniden kurmanın yoludur. Bölüm 28'de gördüğün `fsync` ve yazma sırası kuralları da işlemler bölümünde karşına çıkacak: bir `COMMIT`'in ne anlama geldiğini diskten bağımsız düşünemezsin.

Savunma sanayiinde bu konu günlük iştir. Bir İHA'nın uçuş kayıtları, sensör telemetrisi ve bakım geçmişi ilişkisel veritabanlarında tutulur. "Son otuz günde gerilimi 22 V'un altına düşen uçuşlar hangileri?" gibi bir soruya saniyeler içinde doğru yanıt vermek hem güvenlik hem işletme kararı için gerekir. Aynı sorgunun bir gün yanlış sonuç vermesi ya da iki yazıcının birbirini kilitlemesi yüzünden uçuş kayıtlarının bir kısmının kaybolması kabul edilemez.

Bu bölümde uydurma ama gerçekçi bir İHA filo veritabanı kuracağız: 60 uçak, 9 000 görev, 8 072 uçuş ve 213 992 telemetri satırı. Bütün veri sabit bir tohumla (`random.Random(34)`) üretildiği için sayıları sen de yeniden üretebilirsin. Kitapta gösterilen her çıktı bu koddan alındı. Süre ölçümleri makineye göre değişir; ama yönler ve oranlar, neden o yönde çıktıklarıyla birlikte, senin makinende de görülmelidir.

::: not
Bölümde ana motor SQLite. Bu makinedeki Python 3.12.10 ile gelen SQLite sürümü 3.49.1. PostgreSQL bu makinede kurulu değil; PostgreSQL ile ilgili her iddia "genel bilgi" olarak işaretlendi ve çalıştırılmadı. Belirli sürümle gelen özellikler (RIGHT ve FULL JOIN, pencere fonksiyonları, UPSERT) bu sürümde denenmiştir.
:::


## 34.1 Veri kümesi, DDL ve DML temelleri

SQL'in iki ana alt dili vardır. **DDL** (Data Definition Language) şemayı kurar: `CREATE TABLE`, `ALTER TABLE`, `DROP TABLE`, `CREATE INDEX`. **DML** (Data Manipulation Language) veriyi değiştirir: `INSERT`, `UPDATE`, `DELETE`. Veri okuyan `SELECT` ise çoğu kaynakta ayrı bir dil sayılır (DQL, Data Query Language). Bu bölümün ağırlığı oradadır.

Şema ilk bakışta süs gibi görünür, oysa iş görür. Sütun türleri, `NOT NULL` ve `UNIQUE` kısıtları, `PRIMARY KEY` ve `REFERENCES` motora verinin neye benzediğini söyler. Motor bu bilgiyle hatalı veriyi reddeder ve sorgu planını çıkarır. Kısıtı olmayan bir şema hızlı gibi görünür; ama tek bir hatalı `UPDATE` tüm raporları sessizce bozabilir.

Bölümün verisi sekiz tablodan oluşur:

- `ussler` (12 üs) ve `baglanti` (29 yönlü koridor): graf sorguları için.
- `ucak` (60 uçak) ve `gorev` (9 000 görev): iş ve atama ilişkisi. `gorev.ucak_id` **NULL olabilir**; bu, henüz uçağa atanmamış bir görevdir.
- `ucus` (8 072 uçuş) ve `telemetri` (213 992 örnek): zaman serisi. Her uçuş beş dakikada bir örnek üretir.
- `ekipman` (20 düğümlü ağaç) ve `bakim` (800 kayıt): özyinelemeli sorgular için.

Şemada iki tuzağa dikkat et. Birincisi, SQLite yabancı anahtarları varsayılan olarak **denetlemez**. `PRAGMA foreign_keys = ON` bağlantı başına açılmadıkça `REFERENCES` yalnızca bir not gibi davranır. Bunu bilmeden "motor zaten engelliyor" varsayımına düşmek kolaydır. İkincisi, SQLite sütun türlerini katı değil esnek uygular. Bu konuya sorgu yazarken dönüp bakacağız.

Aşağıdaki program şemayı kurar ve veriyi üretir. Veri üretiminde Python'un `random.Random(34)` nesnesi kullanılır. Global `random` durumuna dokunulmadığı için aynı tohum her çalıştırmada aynı dosyayı verir. Program sonunda her tablonun satır sayısını yazar. Program 225 satırdır; bloklara bölünmüş olarak okuyabilirsin.

Programın ilk bölümü başlığı, içe aktarmaları ve şemanın bir kısmını içerir. Şemanın tamamı bir `DDL` metni olarak tek bir dizgide tutulur; `executescript` onu tek seferde çalıştırır.

```python
# b34_sema.py: İHA filo şeması ve sabit tohumlu veri
import os
import random
import sqlite3
import sys
from datetime import datetime, timedelta

DDL = """
CREATE TABLE ussler (
  id INTEGER PRIMARY KEY,
  ad TEXT NOT NULL UNIQUE,
  kapasite INTEGER NOT NULL
);
CREATE TABLE baglanti (
  kaynak INTEGER NOT NULL REFERENCES ussler(id),
  hedef INTEGER NOT NULL REFERENCES ussler(id),
  mesafe_km REAL NOT NULL,
  PRIMARY KEY (kaynak, hedef)
);
CREATE TABLE ucak (
  id INTEGER PRIMARY KEY,
  kuyruk TEXT NOT NULL UNIQUE,
  tip TEXT NOT NULL,
  us_id INTEGER REFERENCES ussler(id),
  uretim_yili INTEGER NOT NULL,
  durum TEXT NOT NULL
);
CREATE TABLE gorev (
  id INTEGER PRIMARY KEY,
  ucak_id INTEGER REFERENCES ucak(id),
  baslangic TEXT NOT NULL,
  gorev_tipi TEXT NOT NULL,
  durum TEXT NOT NULL
);
CREATE TABLE ucus (
  id INTEGER PRIMARY KEY,
  gorev_id INTEGER NOT NULL REFERENCES gorev(id),
  kalkis TEXT NOT NULL,
  sure_dk INTEGER NOT NULL
);
```

Şemanın devamında `ucak`, `gorev` ve `telemetri` gibi tabloların sütunları yer alır. `telemetri` tablosundaki `irtifa_m` sütununda `NULL` izni vardır; bu, sensörün örnek alamadığı anlamına gelir.

```python
CREATE TABLE telemetri (
  id INTEGER PRIMARY KEY,
  ucus_id INTEGER NOT NULL REFERENCES ucus(id),
  zaman_sn INTEGER NOT NULL,
  irtifa_m REAL,
  gerilim_v REAL NOT NULL
);
CREATE TABLE ekipman (
  id INTEGER PRIMARY KEY,
  ust_id INTEGER REFERENCES ekipman(id),
  ad TEXT NOT NULL
);
CREATE TABLE bakim (
  id INTEGER PRIMARY KEY,
  ucak_id INTEGER NOT NULL REFERENCES ucak(id),
  ekipman_id INTEGER NOT NULL REFERENCES ekipman(id),
  tarih TEXT NOT NULL,
  maliyet_tl REAL NOT NULL
);
"""

USSLER = [
    "Ana Üs",
    "Kuzey Üs",
    "Doğu Üs",
    "Batı Üs",
    "Güney Üs",
    "Sahil Üs",
    "Dağ Üs",
    "Ova Üs",
    "Liman Üs",
    "Ara İst. A",
    "Ara İst. B",
    "Kapalı Üs",
]
EKIPMAN = [  # (id, ust_id, ad): kök İHA, alt sistemler, bileşenler
    (1, None, "İHA"),
    (2, 1, "Motor"),
    (3, 1, "Aviyonik"),
    (4, 1, "Güç"),
```

Üs ve ekipman listeleri sabit verilerdir. Bunlar rastgele değildir, çünkü bir sorgunun sonucunu insan gözüyle kontrol edebilmek istiyoruz. Ardından `kur` fonksiyonu başlar: önce üsleri ekler.

```python
    (5, 1, "Gövde"),
    (6, 1, "Haberleşme"),
    (7, 2, "Pervane"),
    (8, 2, "Şanzıman"),
    (9, 2, "Yakıt pompası"),
    (10, 3, "IMU"),
    (11, 3, "GPS"),
    (12, 3, "Uçuş bilgisayarı"),
    (13, 4, "Batarya"),
    (14, 4, "Regülatör"),
    (15, 13, "Hücre A"),
    (16, 13, "Hücre B"),
    (17, 5, "Kanat"),
    (18, 5, "Kuyruk"),
    (19, 6, "Veri linki"),
    (20, 6, "Anten"),
]


def kur(yol, seed=34):
    if os.path.exists(yol):
        os.remove(yol)
    con = sqlite3.connect(yol)
    con.executescript(DDL)
    r = random.Random(seed)
    con.executemany(
        "INSERT INTO ussler VALUES (?,?,?)",
        [
            (i + 1, ad, r.randint(4, 20))
            for i, ad in enumerate(USSLER)
        ],
    )
    # 1..11 birbirine bağlı; 12 (Kapalı Üs) yalnızca çıkış verir
    kenar = {(12, 1)}
    for a in range(1, 12):
        for b in r.sample(range(1, 12), 3):
            if a != b:
                kenar.add((a, b))
    con.executemany(
        "INSERT INTO baglanti VALUES (?,?,?)",
```

Bağlantı grafı rastgele kurulur ama sabit tohumla. `(12, 1)` kenarı, Kapalı Üs'ün yalnızca çıkış verdiğini garanti eder: kimse ona ulaşamaz. Bölüm sonunda bu özellik özyinelemeli CTE ile erişilebilirlik sorusunda işimize yarayacak.

```python
        [
            (a, b, round(r.uniform(40, 400), 1))
            for a, b in sorted(kenar)
        ],
    )
    tipler = ["KESIF", "TAARRUZ", "LOJISTIK"]
    ucak = []
    for i in range(1, 61):
        yil = r.randint(2016, 2025) if i <= 55 else 2025
        durum = r.choices(
            ["hazir", "bakimda", "devre_disi"], [7, 2, 1]
        )[0]
        ucak.append(
            (
                i,
                "UA-%03d" % i,
                r.choice(tipler),
                r.randint(1, 11),
                yil,
                durum,
            )
        )
    con.executemany("INSERT INTO ucak VALUES (?,?,?,?,?,?)", ucak)

    # 9000 görev; %3'ü henüz uçağa atanmamış (NULL), %8'i iptal
    bas = datetime(2025, 1, 1)
    gorev, ucus, tel = [], [], []
    for g in range(1, 9001):
        t = bas + timedelta(minutes=r.randrange(0, 60 * 24 * 630))
        ucak_id = None if r.random() < 0.03 else r.randint(1, 55)
        durum = "iptal" if r.random() < 0.08 else "tamam"
        gorev.append(
            (
                g,
                ucak_id,
                t.strftime("%Y-%m-%d %H:%M"),
                r.choice(["KESIF", "GOZETLEME", "ISARET"]),
                durum,
            )
        )
```

Uçak ve görev üretimi burada başlar. `%3` görevin `ucak_id` alanı `None` olur. Bu kasıtlıdır: `NOT IN` tuzağını Örnek 2'de bu NULL'lar üzerinden göstereceğiz.

```python
        if durum == "tamam" and ucak_id is not None:
            kalkis = t + timedelta(minutes=r.randint(0, 30))
            sure = r.randint(20, 240)
            uid = len(ucus) + 1
            ucus.append(
                (uid, g, kalkis.strftime("%Y-%m-%d %H:%M"), sure)
            )
            dusuk = r.random() < 0.03  # %3 uçuşta gerilim çöküşü
            for zs in range(0, sure * 60 + 1, 300):  # 5 dk örnek
                f = zs / (sure * 60)
                irt = 120 * min(1.0, 6 * f, 6 * (1 - f)) + r.gauss(
                    0, 3
                )
                ger = 25.2 - 3.0 * f + r.gauss(0, 0.05)
                if dusuk and 0.4 < f < 0.6:
                    ger -= 1.5
                tel.append(
                    (
                        len(tel) + 1,
                        uid,
                        zs,
                        None if r.random() < 0.02 else round(irt, 1),
                        round(ger, 2),
                    )
                )
    con.executemany("INSERT INTO gorev VALUES (?,?,?,?,?)", gorev)
    con.executemany("INSERT INTO ucus VALUES (?,?,?,?)", ucus)
    con.executemany("INSERT INTO telemetri VALUES (?,?,?,?,?)", tel)

    con.executemany("INSERT INTO ekipman VALUES (?,?,?)", EKIPMAN)
    bakim = [
        (
            i,
            r.randint(1, 60),
            r.randint(1, 20),
            "%04d-%02d-%02d"
            % (
                r.choice([2025, 2026]),
                r.randint(1, 12),
                r.randint(1, 28),
```

Uçuş ve telemetri döngüsü bir uçuşun her beş dakikasını ayrı bir satır olarak üretir. Gerilim, uçuş boyunca doğrusal azalır ve `%3` uçuşta orta bölümde bir çöküş eklenir; Örnek 3 bu çöküşleri arayacak. İrtifa profili yükselir, seyreder ve alçalır, `%2` örnek ise `None` olur.

```python
            ),
            round(r.uniform(500, 50000), 2),
        )
        for i in range(1, 801)
    ]
    con.executemany("INSERT INTO bakim VALUES (?,?,?,?,?)", bakim)
    con.commit()
    return con


if __name__ == "__main__":
    con = kur(sys.argv[1] if len(sys.argv) > 1 else "iha.db")
    for t in [
        "ussler",
        "baglanti",
        "ucak",
        "gorev",
        "ucus",
        "telemetri",
        "ekipman",
        "bakim",
    ]:
        n = con.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
        print("%-10s %8d" % (t, n))
    con.close()
```

Son bölümde bakım kayıtları üretilir ve veriler tek işlemde (`commit`) kalıcı yapılır. Ana program her tablonun satır sayısını yazdırır.

Programı `python b34_sema.py iha.db` komutuyla çalıştırdığında şu çıktıyı görmelisin:

```term
$ python b34_sema.py iha.db
ussler           12
baglanti         29
ucak             60
gorev          9000
ucus           8072
telemetri    213992
ekipman          20
bakim           800
```

Dosya yaklaşık 7 MB'a ulaşır. Bu veriyle bölüm boyunca çalışacağız; her örnek aynı `iha.db` dosyasını okur.

### Temel DML: ekle, güncelle, sil

Sorgu yazmadan önce veriyi nasıl değiştirdiğini bilmek gerekir. Aşağıdaki üç ifade, bölüm verisinde bir uçağın durumunu değiştirmenin en küçük örneğidir:

```sql
UPDATE ucak SET durum = 'bakimda' WHERE id = 7;
DELETE FROM gorev WHERE durum = 'iptal' AND id < 100;
INSERT INTO ucak (id, kuyruk, tip, us_id, uretim_yili, durum)
VALUES (61, 'UA-061', 'KESIF', 1, 2025, 'hazir');
```

`WHERE` yan tümcesi olmayan bir `UPDATE` ya da `DELETE` tabloyu tümüyle etkiler. Bu hata, ilk yıl aldığın en pahalı derslerden biri olabilir. Bu yüzden işleri bir işlem (transaction) içine koy ve önce bir `SELECT` ile etkilenecek satırları say. İşlemleri 34.10'da ayrıntılı göreceksin.

::: ipucu
Bir `UPDATE` ya da `DELETE` yazmadan önce aynı `WHERE` koşuluyla bir `SELECT COUNT(*)` çalıştır. Sayı beklediğinin dışındaysa dur. Bu alışkanlık, üretimde veri kaybını önlemenin en ucuz yoludur.
:::


## 34.2 SELECT'in mantıksal yürütme sırası

Bir `SELECT` ifadesini yazarken kafanda genellikle üstten alta okuduğun sıra vardır: önce hangi sütunlar, sonra hangi tablo, sonra koşul. Motor ise bu ifadeyi farklı bir sırayla düşünür. SQL standardı, bir sorgunun sonucunun şu mantıksal sıradan geldiğini tanımlar:

1. **FROM**: tabloları (ve birleşimleri) birleştirir.
2. **WHERE**: satırları süzer.
3. **GROUP BY**: kalan satırları gruplara ayırır.
4. **HAVING**: grupları süzer.
5. **SELECT**: çıktı sütunlarını hesaplar ve adlandırır.
6. **ORDER BY**: sonucu sıralar.
7. **LIMIT**: ilk birkaç satırı döndürür.

Motor fiziksel olarak bu sırayı birebir izlemek zorunda değildir. Planlayıcı, sonucu değiştirmemek koşuluyla işleri yeniden sıralayabilir. Ama sonucun **anlamı** bu sıraya göre tanımlanır. Bu yüzden bir sorguda bir adın nerede geçerli olduğunu bu sıradan okursun.

![Şekil 34.1: Yazılış sırası (üst) ile yürütülme sırası (alt). WHERE çalışırken SELECT'te tanımlanan takma adlar henüz yoktur.](gorseller/b34_yurutme_sirasi.png)

Şekil 34.1'in alt satırı, bu bölümde en çok karşılaşacağın tuzağı açıklar. `SELECT id + 1000 AS id ... WHERE id = 3` gibi bir ifadede WHERE, takma ada değil, tablodaki gerçek `id` sütununa bakar. Standart SQL, WHERE içinde SELECT takma adını **yasaklar**, çünkü o noktada ad henüz tanımlanmamıştır.

SQLite bu kuralı esnetir: WHERE içinde takma adı kabul eder. PostgreSQL gibi motorlar aynı sorguyu hata vererek reddeder (genel bilgi; bu makinede PostgreSQL çalıştırılmadı). Aşağıdaki program bu davranışları sınar.

```python
# b34_sira.py: sorgu yürütme sırası ve takma ad davranışı
import sqlite3
import sys

c = sqlite3.connect(sys.argv[1])
# 1) WHERE içinde SELECT takma adı: SQLite kabul eder (standart dışı)
print(
    "1)", c.execute("SELECT id AS u FROM ucak WHERE u = 3").fetchall()
)
# 2) Takma ad, aynı adlı sütunu gölgelemez: WHERE temel sütunu görür
print(
    "2)",
    c.execute(
        "SELECT id + 1000 AS id FROM ucak " "WHERE id = 3"
    ).fetchall(),
)
# 3) ORDER BY takma adı görür, çünkü SELECT bitmiştir
print(
    "3)",
    c.execute(
        "SELECT kuyruk, id + 1000 AS yeni FROM ucak "
        "ORDER BY yeni DESC LIMIT 2"
    ).fetchall(),
)
# 4) GROUP BY ve HAVING içinde takma ad (SQLite kabul eder)
print(
    "4)",
    c.execute(
        "SELECT us_id AS u, COUNT(*) AS n FROM ucak "
        "GROUP BY u HAVING n > 5 ORDER BY u "
        "LIMIT 3"
    ).fetchall(),
)
# 5) Standart çözüm: takma adı alt sorguda tanımla
print(
    "5)",
    c.execute(
        "SELECT u FROM (SELECT id AS u FROM ucak) " "WHERE u = 3"
    ).fetchall(),
)
```

Çıktıda ilk satır, SQLite'ın takma adı kabul ettiğini gösterir. İkinci satır, takma adın tabloda aynı adlı sütunu gölgelemediğini gösterir: WHERE `id = 3` koşulunu gerçek sütunla uygular, sonuçta ise 1003 görünür. Üçüncü satır ORDER BY'ın takma adı gördüğünü, dördüncü satır GROUP BY ve HAVING'in de takma adı kabul ettiğini gösterir. Beşinci satır standart çözümdür: adı alt sorguda üretip dış sorguda kullanırsın.

```term
$ python b34_sira.py iha.db
1) [(3,)]
2) [(1003,)]
3) [('UA-060', 1060), ('UA-059', 1059)]
4) [(2, 8), (3, 10), (5, 7)]
5) [(3,)]
```

Bu sonuçtan çıkarılacak pratik kural şudur: **WHERE ve GROUP BY içinde takma ad kullanma alışkanlığı edinme.** Bu, SQLite'ta çalışır ama taşınabilir değildir; başka bir motora geçtiğinde sorgun patlar. Hangi adın nerede geçerli olduğunu aklında tutmak, yazım hatalarını daha yazarken yakalatır.

::: dikkat
Mülakatlarda "neden WHERE'de takma ad kullanamazsın?" sorusu sık gelir. Doğru cevap "çünkü SQL öyle" değil, mantıksal sıradır: WHERE çalışırken SELECT henüz yürütülmemiştir. Bu cevabı kendi kelimelerinle, şekil 34.1'e bakmadan kurabiliyor musun?
:::


## 34.3 JOIN türleri, NULL ve LEFT JOIN tuzağı

İlişkisel modelin gücü, bilgiyi tablolara bölüp sorgu anında yeniden birleştirmekten gelir. Bölüm 33'te ilişki cebirindeki birleştirme işlemini gördün. Burada aynı fikrin SQL karşılığı olan JOIN türlerine ve bu türlerin NULL ile nasıl etkileştiğine bakıyoruz.

Dört temel tür, sonuçta hangi satırların kalacağını belirler:

- **INNER JOIN**: iki tarafta da eşleşen satırlar.
- **LEFT JOIN**: sol taraftaki tüm satırlar; eşleşmeyen sağ taraf sütunları NULL.
- **RIGHT JOIN**: sağ taraftaki tüm satırlar; eşleşmeyen sol taraf NULL. SQLite 3.39.0'da eklendi (genel bilgi; 3.49.1'de denendi).
- **FULL JOIN**: iki taraftaki tüm satırlar; eşleşmeyen her iki taraf da NULL olabilir. Aynı sürüm notu geçerlidir.
- **CROSS JOIN**: eşleşme koşulu olmadan kartezyen çarpım; satır sayısı iki tablonun çarpımıdır.

Bir de **öz birleşim** (self-join) vardır: aynı tablo iki kez, farklı takma adlarla birleştirilir. Ekipman ağacında "bu parçanın üst sistemi hangisi?" sorusu buna örnektir.

Şekil 34.2 aynı iki küçük tabloyla dört türün ürettiği satırları gösterir. Venn şeması bu konuyu öğretmek için yaygın kullanılır ama yanıltıcıdır: satır çoğalmasını (aynı anahtardan birden çok eşleşme) ve NULL dolgusunu göstermez. Bu yüzden satır eşleşme tabloları kullandık.

![Şekil 34.2: Dört JOIN türünün satır eşleşme tabloları. A = {1, 2, 3}, B = {2, 3, 4}; eşleşmeyen tarafta NULL yazılır.](gorseller/b34_join_turleri.png)

### NULL: bilinmeyen bir değer

NULL, "değer yok" değil, "bilinmiyor" anlamına gelir. Bu ayrım, koşulların sonucunu değiştirir. Bir karşılaştırma üç değerden birini üretir: doğru (T), yanlış (F) ya da bilinmiyor (U). Üçüncü değer, SQL'in üç değerli mantığının kalbidir.

Bu yüzden `NULL = NULL` ifadesi doğru değil **bilinmiyor** sonucunu verir. Motor WHERE koşulunu yalnızca T olan satırlar için geçirir; U ve F satırları atılır. Şekil 34.3, AND ve OR işlemlerinin tablosunu gösterir.

![Şekil 34.3: AND ve OR için üç değerli mantık tabloları. U, NULL'dan gelen bilinmiyor değeridir.](gorseller/b34_null_mantik.png)

Bu tablolardan iki pratik sonuç çıkar. Birincisi, `NOT U` hâlâ U'dur; `WHERE NOT (ucak_id = 5)` ifadesi `ucak_id` NULL olan satırları da atar, çünkü onlar için koşul U'ya düşer. İkincisi, NULL'u eşitlik ile değil `IS NULL` ile kontrol edersin. Aşağıdaki SQLite ifadeleri bu kuralların hepsini gösterir:

```sql
SELECT NULL = NULL, NULL IS NULL, NULL AND 0, NULL OR 1;
-- sonuç: NULL, 1, 0, 1
SELECT 1 IN (2, NULL), 1 IN (1, NULL);
-- sonuç: NULL, 1
```

### Örnekle: LEFT JOIN ve WHERE tuzağı

Aşağıdaki program, aynı birleşimin koşulu `ON` ya da `WHERE` içine koymakla nasıl farklı sonuç verdiğini gösterir. Ayrıca tüm JOIN türlerinin satır sayılarını ve bir öz birleşimi çalıştırır.

```python
# b34_join.py: JOIN türleri, LEFT JOIN + WHERE tuzağı, öz birleşim
import sqlite3
import sys

c = sqlite3.connect(sys.argv[1])


def say(sql):
    return c.execute(sql).fetchone()[0]


print(
    "INNER:",
    say(
        "SELECT COUNT(*) FROM ucak u JOIN gorev g "
        "ON g.ucak_id = u.id"
    ),
)
print(
    "LEFT :",
    say(
        "SELECT COUNT(*) FROM ucak u LEFT JOIN gorev g "
        "ON g.ucak_id = u.id"
    ),
)
print(
    "RIGHT:",
    say(
        "SELECT COUNT(*) FROM ucak u RIGHT JOIN gorev g "
        "ON g.ucak_id = u.id"
    ),
)
print(
    "FULL :",
    say(
        "SELECT COUNT(*) FROM ucak u FULL JOIN gorev g "
        "ON g.ucak_id = u.id"
    ),
)
print(
```

Program ikinci yarıda birleşimin sonuçlarını yazdırır. Dikkat: `WHERE` ile filtrelemek, LEFT JOIN'i sessizce bir INNER JOIN'e çevirir.

```python
    "CROSS:", say("SELECT COUNT(*) FROM ussler a CROSS JOIN ussler b")
)
print(
    "WHERE ile filtre:",
    say(
        "SELECT COUNT(*) FROM ucak u LEFT JOIN gorev g "
        "ON g.ucak_id = u.id WHERE g.durum = 'iptal'"
    ),
)
print(
    "ON ile filtre   :",
    say(
        "SELECT COUNT(*) FROM ucak u LEFT JOIN gorev g "
        "ON g.ucak_id = u.id AND g.durum = 'iptal'"
    ),
)
print("öz birleşim (ekipman -> üst):")
for ad, ust in c.execute(
    "SELECT c.ad, p.ad FROM ekipman c "
    "LEFT JOIN ekipman p ON p.id = c.ust_id "
    "WHERE c.id IN (1, 7, 15) ORDER BY c.id"
):
    print("  %-10s -> %s" % (ad, ust))
```

```term
$ python b34_join.py iha.db
INNER: 8744
LEFT : 8749
RIGHT: 9000
FULL : 9005
CROSS: 144
WHERE ile filtre: 672
ON ile filtre   : 677
öz birleşim (ekipman -> üst):
  İHA        -> None
  Pervane    -> Motor
  Hücre A    -> Batarya
```

Çıktı iki tuzağı birlikte gösterir. `LEFT JOIN`'de 8 749 satır var; bunun 5'i, hiç görev almamış beş uçağın NULL dolgusudur. `WHERE g.durum = 'iptal'` koşulu bu NULL satırları da eler: 672 satır kalır. Oysa aynı koşulu `ON` içine koyduğumuzda 677 satır kalır; beş uçak da korunur, çünkü koşul yalnızca birleşmeyi süzer, dış satırları silmez.

Kural basittir: **sağ tarafa ait bir koşul bir LEFT JOIN'in ON yan tümcesine aittir**. WHERE'e koyarsan birleşimin dış satırlarını öldürürsün. Bu hata, raporların "neden bazı uçaklar yok?" sorusuyla ortaya çıkar, sorgu hata vermez.

### Öz birleşim: ekipman ağacı

Son satırlar, aynı `ekipman` tablosunun iki kez kullanıldığı bir öz birleşimdir. `c` çocuk, `p` üst düğüm olarak adlandırılır. Kök düğümün (İHA) üstü yoktur; bu yüzden LEFT JOIN ile NULL döner. Ağacın tamamını bu tek birleşimle değil, 34.5'te özyinelemeli CTE ile gezeceksin.

::: not
Bölüm 16'da DP tablolarında her hücrenin iki komşuya baktığını gördün. Öz birleşim de benzer bir yapıdır: her satırın kendi tablosundaki başka bir satıra bakması. Bu bakışın derinleşmiş hâli özyinelemedir (34.5).
:::


## 34.4 Toplama, GROUP BY, HAVING ve alt sorgular

Toplama fonksiyonları (`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`) bir grup satırı tek bir değere indirger. `GROUP BY` hangi satırların aynı grupta olduğunu söyler. Bu iki kavram birlikte, "her uçağın kaç görevi var?" gibi soruların temelidir.

Bu bölümün verisinde bir tuzak var: `COUNT(*)` tüm satırları sayar, `COUNT(sütun)` ise yalnızca o sütunun NULL olmadığı satırları sayar. `gorev` tablosunda 9 000 satır vardır, ama `ucak_id` dolu olan yalnızca 8 744'tür. Aynı tabloda iki sayım farklı sonuç verir; hangisini istediğini sorguda açıkça yazmalısın.

```sql
SELECT COUNT(*), COUNT(ucak_id) FROM gorev;
-- 9000 | 8744
SELECT durum, COUNT(*) FROM gorev GROUP BY durum;
-- iptal 691, tamam 8309
```

`HAVING`, grupları süzen yan tümcedir. `WHERE` satırları gruplamadan önce süzer; `HAVING` gruplandıktan sonra süzer. Toplamı kullanan bir koşul (`HAVING COUNT(*) >= 170`) yalnızca `HAVING`'de yazılabilir; WHERE'de yazılamaz, çünkü o noktada grup yoktur.

### Alt sorgular

Bir sorgu, başka bir sorgunun sonucunu kullanabilir. Üç biçimi vardır:

- **Skaler alt sorgu**: tek satır, tek sütun döndürür ve bir değer gibi kullanılır. Örneğin her uçağın görev sayısı:

```sql
SELECT u.id,
       (SELECT COUNT(*) FROM gorev g
        WHERE g.ucak_id = u.id) AS gorev_sayisi
FROM ucak u ORDER BY u.id LIMIT 3;
```

- **IN ve EXISTS**: bir değerin bir kümede olup olmadığını ya da bir ilişkinin var olup olmadığını sorar.
- **İlişkili alt sorgu** (correlated subquery): iç sorgu dış sorgunun satırına bağlıdır ve her dış satır için yeniden değerlendirilir. Yukarıdaki örnekte `u.id` bunun bir parçasıdır.

Mantıksal olarak ilişkili alt sorgu, her dış satır için ayrı bir döngü gibi düşünülebilir. Planlayıcı bunu çoğu zaman bir birleşime çevirir; ama "bu yazım her satır için bir kez çalışır" sezgisi, performans sorunlarını yakalamak için iyi bir başlangıçtır. 34.8'de bu sezgiyi ölçerek göreceksin.

`NOT IN` ile `NOT EXISTS` aynı işi yapıyor gibi görünür; ama alt sorgu NULL döndürdüğünde sonuçları tamamen farklıdır. Bu tuzağı Örnek 2'de gerçek veriyle üretip inceleyeceğiz. Şimdilik kural: **NOT IN kullanacaksan alt sorgunun NULL döndürmediğinden emin ol**, ya da `NOT EXISTS` kullan.

::: dikkat
`NOT IN (SELECT ucak_id FROM gorev)` sorgusu, `ucak_id` içinde tek bir NULL olduğu için hiçbir satır döndürmeyebilir. Hata vermez, sessizce boş döner. Bu, raporlarda en pahalı sessiz hatalardan biridir.
:::


## 34.5 CTE ve özyinelemeli CTE

**CTE** (Common Table Expression), `WITH` ile adlandırılan geçici bir sorgu sonucudur. Bir alt sorguyu adlandırıp yukarıdan okumanın yoludur; sorgunun okunabilirliğini artırır ve aynı sonucu birden fazla kez kullanmana izin verir. Motor CTE'yi bazen bir alt sorgu gibi satır satır işler, bazen geçici bir tabloya yazar; bu seçim sürüme ve sorguya göre değişir (genel bilgi).

Özyinelemeli CTE, bir CTE'nin kendisine başvurmasıdır. Yapısı her zaman iki parçadır:

1. **Tohum** (anchor): ilk satır ya da satırlar. Bu sonuç bir kez üretilir.
2. **Özyinelemeli üye**: önceki iterasyonun satırlarını kullanarak yeni satırlar üretir.

Motor şöyle çalışır: tohumu sonuca ekler ve bir "çalışma tablosuna" koyar. Sonra özyinelemeli üyeyi **yalnızca çalışma tablosunun son satırlarına** uygular, ürettiği satırları sonuca ve yeni çalışma tablosuna ekler. Yeni satır kalmayınca durur. Şekil 34.4 bunu Fibonacci dizisi üzerinde gösterir.

Bu yapı, Bölüm 16'daki DP tablosunun satır satır doldurulmasıyla aynıdır: her satır bir önceki satırlardan hesaplanır ve tablo alttan üste büyür. Bölüm 16.3'teki tabulation ile bu sorgu arasındaki fark, dönüşümün SQL'de kendiliğinden tablo üretmesidir.

![Şekil 34.4: Fibonacci'nin özyinelemeli CTE ile satır satır üretilmesi. Her iterasyon yalnızca bir önceki satırı kullanır.](gorseller/b34_ozyinelemeli_cte.png)

Özyinelemenin sonsuza gitmesini önlemek sorumluluğunuzdadır. Ağaç gibi yapılarda döngü olmaz, ama bir grafın içinde döngü olabilir. `UNION` (`UNION ALL` değil) kullanmak, aynı satırın tekrar üretilmesini eler ve döngüde sonsuz döngüyü keser. Ayrıca bir derinlik sınırı (`WHERE d < 10`) koymak güvenli bir ikinci savunmadır.

Aşağıdaki program dört özyinelemeli sorgu çalıştırır: Fibonacci, grafta erişilebilirlik, en kısa adım sayısı (Bölüm 17'deki BFS'nin SQL karşılığı) ve ekipman ağacında alt ağaç toplamı.

```python
# b34_ozyin.py: özyinelemeli CTE: Fibonacci, erişilebilirlik, ağaç
import sqlite3
import sys

c = sqlite3.connect(sys.argv[1])

FIB = """
WITH RECURSIVE f(n, a, b) AS (
  SELECT 1, 0, 1
  UNION ALL
  SELECT n + 1, b, a + b FROM f WHERE n < 93)
SELECT n, b, typeof(b) FROM f WHERE n IN (2, 10, 92, 93)
"""
print("Fibonacci (n, F(n), tür):")
for satir in c.execute(FIB):
    print("  ", satir)

ERISIM = """
WITH RECURSIVE r(id) AS (
  SELECT ?
  UNION
  SELECT b.hedef FROM r JOIN baglanti b ON b.kaynak = r.id)
SELECT COUNT(*) FROM r
"""
print(
    "Ana Üs'ten erişilebilen üs:",
    c.execute(ERISIM, (1,)).fetchone()[0],
)
print(
    "Kapalı Üs'ten erişilebilen:",
    c.execute(ERISIM, (12,)).fetchone()[0],
)
```

Programın devamı, grafın üzerinde en kısa adım sayılarını ve ağaç toplamlarını hesaplar. Bu iki sorgu, BFS'de her düğüme ilk ulaşılan adımı ve bir alt ağacın bütün düğümlerinin verisini toplamak için iki farklı özyineleme biçimi kullanır.

```python
MESAFE = """
WITH RECURSIVE r(id, d) AS (
  SELECT ?, 0
  UNION
  SELECT b.hedef, r.d + 1 FROM r JOIN baglanti b ON b.kaynak = r.id
  WHERE r.d < 10)
SELECT id, MIN(d) AS adim FROM r GROUP BY id ORDER BY adim, id LIMIT 4
"""
print("Ana Üs'ten en az adım (ilk 4):")
for satir in c.execute(MESAFE, (1,)):
    print("  ", satir)

AGAC = """
WITH RECURSIVE alt(kok, id) AS (
  SELECT id, id FROM ekipman
  UNION ALL
  SELECT alt.kok, e.id FROM alt JOIN ekipman e ON e.ust_id = alt.id)
SELECT e.ad, ROUND(SUM(b.maliyet_tl), 2) AS toplam
FROM alt JOIN ekipman e ON e.id = alt.kok
JOIN bakim b ON b.ekipman_id = alt.id
GROUP BY e.id ORDER BY toplam DESC LIMIT 4
"""
print("Alt ağaç toplam bakım maliyeti (TL, ilk 4):")
for satir in c.execute(AGAC):
    print("  ", satir)
```

```term
$ python b34_ozyin.py iha.db
Fibonacci (n, F(n), tür):
   (2, 1, 'integer')
   (10, 55, 'integer')
   (92, 7540113804746346429, 'integer')
   (93, 1.2200160415121877e+19, 'real')
Ana Üs'ten erişilebilen üs: 11
Kapalı Üs'ten erişilebilen: 12
Ana Üs'ten en az adım (ilk 4):
   (1, 0)
   (3, 1)
   (9, 1)
   (10, 1)
Alt ağaç toplam bakım maliyeti (TL, ilk 4):
   ('İHA', 20453812.46)
   ('Güç', 5257166.62)
   ('Aviyonik', 4015674.3)
   ('Batarya', 3527945.54)
```

Çıktının iki noktası dikkate değer. Birincisi, **93. Fibonacci sayısı 64 bitlik işaretli tamsayıya sığmaz** ve SQLite taşan toplamı sessizce REAL türüne çevirir; bu yüzden `typeof` 'real' döner ve değer 1.22e19 biçiminde yazılır. Bu, Bölüm 16'daki `F(92)` sınırının neden önemli olduğunu gösterir. İkincisi, Ana Üs'ten 11 üs erişilebilirken Kapalı Üs'ten 12 (kendisi dahil) erişilebilir; çünkü Kapalı Üs yalnızca çıkış verir ve oradan Ana Üs'e geçilir. Yani "erişilebilirlik" yönlüdür.

Ağaç sorgusunda her düğüm, kendi alt ağacındaki tüm bakım maliyetlerinin toplamını taşır. İHA kökünün toplamı, beklendiği gibi, tüm bakım maliyetinin toplamıdır. Bu tür raporları özyinelemesiz yazmak, düzey sayısı kadar birleşim gerektirir ve her yeni düzeyde sorguyu yeniden yazmak zorunda kalırsın.

::: ipucu
Özyinelemeli bir CTE'yi yazmadan önce, tohum satırını ve her iterasyonda ne üretildiğini kâğıda çiz. Şekil 34.4 gibi bir tablo, hatalı bir koşulu (örneğin sonsuz döngüye yol açan `UNION ALL`) çalıştırmadan görmeni sağlar.
:::


## 34.6 Pencere fonksiyonları

`GROUP BY` satırları birleştirir; bir grubun ayrıntısı kaybolur. Pencere fonksiyonu (window function) ise satırları korur ve her satıra, kendi "penceresindeki" satırlara bakarak bir değer ekler. Söz dizimi `OVER (...)` yan tümcesidir: `PARTITION BY` satırları gruplara ayırır, `ORDER BY` her grup içindeki sırayı verir, çerçeve (frame) ise pencerenin hangi satırları kapsadığını belirler.

Telemetri gibi zaman serilerinde bu ayrım belirleyicidir. Bir uçuşun her örneğini korumak ve o örneğin çevresindeki değerleri görmek istersin. `GROUP BY` bu isteği karşılamaz; pencere fonksiyonu karşılar.

Sık kullanılan fonksiyonlar:

- **ROW_NUMBER()**: her satıra benzersiz bir sıra numarası verir; eşitlikte keyfi sıralama yapar.
- **RANK() ve DENSE_RANK()**: eşitlikleri aynı sıraya koyar. RANK sıra numaralarında boşluk bırakır (1, 1, 3), DENSE_RANK bırakmaz (1, 1, 2).
- **LAG() ve LEAD()**: önceki ya da sonraki satırın değerini verir.
- **SUM, AVG, COUNT ... OVER**: hareketli ya da kümülatif toplamlar.

Çerçeve tanımı, toplamların hangi satırlar üzerinde hesaplanacağını söyler. `ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING` geçerli satırın iki önceki, iki sonraki ve kendisini kapsar. `ROWS UNBOUNDED PRECEDING` ise başlangıçtan geçerli satıra kadar olan kümülatif toplamı verir. ORDER BY varken çerçeve yazılmazsa, SQL'in varsayılan çerçevesi `RANGE` tabanlıdır (genel bilgi): eşit sıralı satırlar birlikte hesaplanır. Hareketli ortalamada bu fark önemlidir; çerçeveyi açıkça yazmak bu sürpriz kaynağını ortadan kaldırır.

![Şekil 34.5: Beş noktalı hareketli ortalamanın çerçevesi. Geçerli satırın iki komşusu her iki yanda kapsanır; kenarlarda pencere kısalır.](gorseller/b34_pencere_cercevesi.png)

Aşağıdaki program ilk olarak küçük bir kümede sıralama fonksiyonlarını, ardından gerçek veride uçak toplamlarını, kümülatif dakikaları ve bir uçuşun gerilim farklarını hesaplar.

```python
# b34_pencere.py: pencere fonksiyonları, sıralama ve zaman serisi
import sqlite3
import sys

c = sqlite3.connect(sys.argv[1])
print("sıralama farkı (küçük örnek: 10, 10, 8):")
for satir in c.execute("""
  SELECT v, ROW_NUMBER() OVER (ORDER BY v DESC),
         RANK() OVER (ORDER BY v DESC),
         DENSE_RANK() OVER (ORDER BY v DESC)
  FROM (SELECT 10 AS v UNION ALL SELECT 10 UNION ALL SELECT 8)"""):
    print("  ", satir)

print("uçak toplam uçuş dakikası, ilk 5 (RANK / DENSE_RANK):")
for satir in c.execute("""
  SELECT u, toplam, RANK() OVER (ORDER BY toplam DESC),
         DENSE_RANK() OVER (ORDER BY toplam DESC)
  FROM (SELECT g.ucak_id AS u, SUM(x.sure_dk) AS toplam
        FROM ucus x JOIN gorev g ON g.id = x.gorev_id
        WHERE g.ucak_id IS NOT NULL GROUP BY g.ucak_id)
  ORDER BY 3 LIMIT 5"""):
    print("  ", satir)

print("kümülatif dakika, uçak 1 ve 2 (PARTITION BY):")
for satir in c.execute("""
  SELECT g.ucak_id, x.kalkis, x.sure_dk,
    SUM(x.sure_dk) OVER (PARTITION BY g.ucak_id ORDER BY x.kalkis
      ROWS UNBOUNDED PRECEDING) AS kumulatif
  FROM ucus x JOIN gorev g ON g.id = x.gorev_id
  WHERE g.ucak_id IN (1, 2) ORDER BY g.ucak_id, x.kalkis LIMIT 4"""):
    print("  ", satir)

print("telemetri, LAG ile örnekler arası fark (uçuş 2, ilk 4):")
for satir in c.execute("""
  SELECT zaman_sn, gerilim_v,
    ROUND(gerilim_v - LAG(gerilim_v) OVER (ORDER BY zaman_sn), 2)
  FROM telemetri WHERE ucus_id = 2 ORDER BY zaman_sn LIMIT 4"""):
    print("  ", satir)
```

```term
$ python b34_pencere.py iha.db
sıralama farkı (küçük örnek: 10, 10, 8):
   (10, 1, 1, 1)
   (10, 2, 1, 1)
   (8, 3, 3, 2)
uçak toplam uçuş dakikası, ilk 5 (RANK / DENSE_RANK):
   (52, 23065, 1, 1)
   (1, 21784, 2, 2)
   (44, 21512, 3, 3)
   (21, 21357, 4, 4)
   (54, 21269, 5, 5)
kümülatif dakika, uçak 1 ve 2 (PARTITION BY):
   (1, '2025-01-10 14:12', 219, 219)
   (1, '2025-01-16 08:30', 56, 275)
   (1, '2025-01-21 08:59', 161, 436)
   (1, '2025-01-30 17:23', 30, 466)
telemetri, LAG ile örnekler arası fark (uçuş 2, ilk 4):
   (0, 25.2, None)
   (300, 25.03, -0.17)
   (600, 25.02, -0.01)
   (900, 25.01, -0.01)
```

İlk çıktı, eşitlikte üç fonksiyonun ne yaptığını gösterir: 10, 10 ve 8 değerleri için ROW_NUMBER 1, 2, 3 verir (eşitlikleri keyfi ayırır), RANK 1, 1, 3 verir, DENSE_RANK 1, 1, 2 verir. Kümülatif dakikalarda, her uçağın toplamı kendi bölümünde başlar (`PARTITION BY`), bu yüzden uçak 2'nin satırları uçak 1'in toplamına karışmaz. LAG'in ilk satırı için önceki değer olmadığından `None` döner.

::: not
Pencere fonksiyonları bir sorgunun SELECT aşamasında hesaplanır. Yani WHERE koşulu onlardan önce uygulanır; bu yüzden "en son uçuşu bul" gibi bir soruyu pencere fonksiyonuyla yapmak istersen, sıra numarasını bir alt sorguda üretip dış sorguda süzmen gerekir. Örnek 1 bu deseni gösterecek.
:::


## 34.7 Koşul, tarih, eksik değer ve UPSERT

### CASE, COALESCE ve NULLIF

`CASE` bir koşullu ifadedir ve SQL'in if-else karşılığıdır. Telemetri örneklerini "düşük gerilim" ve "normal" diye etiketlemek için kullanılır. Bu etiketlere göre gruplamak için `CASE` ifadesini `GROUP BY` ile birlikte kullanırsın:

```sql
SELECT CASE WHEN gerilim_v < 23 THEN 'dusuk' ELSE 'normal' END
           AS etiket,
       COUNT(*) AS n
FROM telemetri GROUP BY 1;
-- dusuk 57450, normal 156542
```

`COALESCE(a, b, ...)`, ilk NULL olmayan argümanı döndürür. Eksik irtifa değerini sıfırla değiştirmeden önce, bunun bir anlam taşıyıp taşımadığını sor: sıfır irtifa gerçek bir ölçüm mü, yoksa sensör boşluğu mu? `NULLIF(a, b)` ise `a = b` ise NULL, değilse `a` döndürür; bölme sıfıra karşı korumada yaygın kullanılır (`x / NULLIF(y, 0)`).

### Tarih ve saat

SQLite'ta tarihler ayrı bir tür değildir; metin, sayı ya da Julian gün olarak tutulabilir. Bu bölümde tarihler ISO biçiminde (`YYYY-MM-DD HH:MM`) metin olarak saklanır. Bu biçim sözlük sıralamasıyla doğru sıralanır, bu yüzden `kalkis < '2026-03-08'` gibi karşılaştırmalar çalışır. Tarih fonksiyonları şunlardır:

```sql
SELECT DATE('2026-03-05 09:00');                 -- 2026-03-05
SELECT strftime('%H:%M', '2026-03-05 09:00');    -- 09:00
SELECT julianday('2026-03-08') - julianday('2026-03-05');  -- 3.0
```

Tuzak: ISO biçimi dışındaki bir metin (`05.03.2026`) sıralamada yanlış yere düşer. Tarihleri her zaman ISO olarak yaz; yazmadan önce `strftime` ile normalleştir.

### UPSERT: ekle ya da güncelle

Bir özet tabloyu her gün güncellemek için iki işlemi ayırmak gerekir: satır yoksa ekle, varsa güncelle. Bu, `INSERT ... ON CONFLICT ... DO UPDATE` ile tek ifadede yapılır (UPSERT). SQLite 3.24.0 ile geldi (genel bilgi). `excluded` takma adı, çakışan yeni satırın değerlerine erişim sağlar.

UPSERT'ün sessiz bir tuzağı vardır: güncelleme **toplama** mı yoksa **yerine koyma** mı yapıyor? Aşağıdaki program aynı partiyi iki kez yükleyerek iki davranışı yan yana gösterir.

```python
# b34_upsert.py: UPSERT ile günlük özet, toplama ve yerine koyma
import sqlite3
import sys

kaynak = sqlite3.connect(sys.argv[1])
c = sqlite3.connect(":memory:")
c.execute(
    "CREATE TABLE ozet (ucak_id INTEGER, gun TEXT, "
    "ucus INTEGER, PRIMARY KEY (ucak_id, gun))"
)
parti = kaynak.execute(
    "SELECT g.ucak_id, DATE(x.kalkis), COUNT(*) FROM ucus x "
    "JOIN gorev g ON g.id = x.gorev_id "
    "WHERE g.ucak_id IN (1, 2, 3) AND x.kalkis < '2026-03-08' "
    "GROUP BY g.ucak_id, DATE(x.kalkis)"
).fetchall()
print("parti satır sayısı:", len(parti))

TOPLA = """INSERT INTO ozet VALUES (?, ?, ?)
  ON CONFLICT (ucak_id, gun) DO UPDATE
  SET ucus = ucus + excluded.ucus"""
YERINE = """INSERT INTO ozet VALUES (?, ?, ?)
  ON CONFLICT (ucak_id, gun) DO UPDATE
  SET ucus = excluded.ucus"""
for ad, sql in [("toplama", TOPLA), ("yerine koyma", YERINE)]:
    c.execute("DELETE FROM ozet")
    c.executemany(sql, parti)
    c.executemany(sql, parti)  # aynı partiyi ikinci kez yükle
    toplam = c.execute("SELECT SUM(ucus) FROM ozet").fetchone()[0]
    print("%-13s iki yükleme sonrası toplam uçuş = %s" % (ad, toplam))
print("kaynakta gerçek uçuş sayısı =", sum(p[2] for p in parti))
```

```term
$ python b34_upsert.py iha.db
parti satır sayısı: 291
toplama       iki yükleme sonrası toplam uçuş = 652
yerine koyma  iki yükleme sonrası toplam uçuş = 326
kaynakta gerçek uçuş sayısı = 326
```

Toplama yapan sürüm, aynı partiyi iki kez yükleyince uçuş sayısını 326'dan 652'ye çıkarır. Bu, gerçek veriyle çakıştığında raporun iki katına çıkması demektir. Yerine koyan sürüm ise 326'da kalır: **idempotent** olur, yani aynı işlemi kaç kez çalıştırsan sonuç değişmez. Bir günlük özet güncellemesini tekrar edilebilir (idempotent) yapmak, yarıda kalan bir işi yeniden başlatmanın güvenli yoludur. Bu kararı, sorgu yazmadan önce bilinçli olarak vermelisin.


## 34.8 İndeksler ve sorgu planı

İndeks, bir sütunun değerlerinden satırın konumuna giden sıralı bir yapıdır. Veritabanı kitabında bu yapı çoğunlukla B+ ağacı olarak anlatılır; ağacın iç düğümlerini, bölünmelerini ve yaprak zincirini Bölüm 33'te gördün. Burada indeksi, bir sorgunun **hangi yolla** çalışacağını değiştiren bir araç olarak ele alıyoruz.

Bir sorgunun yolunu gösteren araç `EXPLAIN QUERY PLAN`'dır. Çıktıdaki kelimeler kısa ama anlamlıdır:

- **SCAN**: tablonun tamamı ya da bir indeksin tamamı okunur. Satır sayısı arttıkça maliyet doğrusal büyür.
- **SEARCH**: bir indeks, koşulla eşleşen satır aralığına doğrudan gider. `USING INDEX` ya da `USING INTEGER PRIMARY KEY` ifadesi eşlik eder.
- **COVERING INDEX**: sorgunun ihtiyaç duyduğu bütün sütunlar indekste bulunur, tabloya dönmeye gerek kalmaz.
- **USE TEMP B-TREE FOR ORDER BY / GROUP BY**: motor sıralamayı ya da gruplamayı ayrı bir geçici yapıda yapar. Bu, indeksin sıralamayı sağlayamadığını gösterir.

Bir indeksin işe yarayıp yaramadığı üç şeye bağlıdır: koşulun indeksin sütun sırasına uyması, koşulun sütun üzerinde doğrudan olması ve koşulun **seçici** olması, yani satırların küçük bir bölümünü seçmesi.

### Bileşik indeks ve en sol önek kuralı

Birden çok sütunlu indeks (bileşik indeks) sütunlarını sırayla sıralar. `(ucus_id, zaman_sn)` indeksinde önce uçuş numarasına, sonra zamana göre sıralanmış bir liste vardır. Şekil 34.6 bu listeyi gösterir.

![Şekil 34.6: Bileşik indeks (ucus_id, zaman_sn) ve en sol önek kuralı. İlk sütun sınırlanmazsa aranan satırlar dizinin her yerine dağılır.](gorseller/b34_bilesik_indeks.png)

Kural şudur: indeks, sorgu koşulu **en soldaki sütundan başlayarak** kullanılabilir ve arada boşluk bırakılamaz. `(ucus_id, zaman_sn)` indeksi `ucus_id = 5 AND zaman_sn > 600` için kullanılır; `zaman_sn = 600` için kullanılmaz. Sütun sırasını seçerken, eşitlik koşulu olan sütunu önce koyarsın; aralık koşulu olan sütunu sona bırakırsın. Bu kuralın SQLite belgesindeki karşılığını Kod Okuma bölümünde gerçek planlarla sınayacağız.

### Indeksi kullanılamaz kılan ifadeler

Bir sütunu bir ifadenin içine sarmak, indeksi devre dışı bırakır. `ucus_id + 0 = 5` ifadesi `ucus_id`'yi değil `ucus_id + 0`'ı karşılaştırır ve indeks bu değeri bilmez. Aynı şey fonksiyon sarmalarında da geçerlidir: `WHERE LOWER(kuyruk) = ...`.

LIKE için kural ayrıdır. Önek aramasında (`LIKE 'UA-00%'`) indeks kullanılabilir, ama baştaki joker karakter (`LIKE '%001'`) hiçbir zaman kullanılamaz. SQLite'ta ayrıca LIKE varsayılan olarak büyük-küçük harf duyarsızdır ve bu durumda indeks kullanılmaz; `PRAGMA case_sensitive_like = ON` ile önek optimizasyonu açılır. Bu, hangi ayarın planı değiştirdiğini ölçmek için iyi bir örnektir.

Aşağıdaki program bu kuralların her birini gerçek planlarla sınar. Program veriyi bir kopyaya uygular, çünkü indeks oluşturmak veritabanını değiştirir.

```python
# b34_plan.py: indeks kullanım kuralları, gerçek planlarla
import os
import shutil
import sqlite3
import sys
import tempfile

kopya = os.path.join(tempfile.mkdtemp(), "plan.db")
shutil.copyfile(sys.argv[1], kopya)
c = sqlite3.connect(kopya)
c.execute("CREATE INDEX ix_tel_uz ON telemetri(ucus_id, zaman_sn)")
c.execute("CREATE INDEX ix_uk ON ucak(kuyruk)")
SORGULAR = [
    "WHERE ucus_id = 5 AND zaman_sn > 600",
    "WHERE zaman_sn = 600",
    "WHERE ucus_id + 0 = 5",
    "WHERE ucus_id BETWEEN 5 AND 9 ORDER BY zaman_sn",
    "WHERE ucus_id = 5 ORDER BY zaman_sn",
]
for kosul in SORGULAR:
    plan = c.execute(
        "EXPLAIN QUERY PLAN SELECT * FROM telemetri " + kosul
    ).fetchall()
    print(kosul)
    for satir in plan:
        print("    ", satir[3])
for kosul in [
    "WHERE kuyruk = 'UA-001'",
    "WHERE kuyruk LIKE 'UA-00%'",
    "WHERE kuyruk LIKE '%001'",
]:
    print("ucak", kosul)
    print(
        "    ",
        c.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM ucak " + kosul
        ).fetchone()[3],
    )
c.execute("PRAGMA case_sensitive_like = ON")
print("case_sensitive_like = ON, ucak LIKE 'UA-00%':")
```

```python
print(
    "    ",
    c.execute(
        "EXPLAIN QUERY PLAN SELECT * FROM ucak "
        "WHERE kuyruk LIKE 'UA-00%'"
    ).fetchone()[3],
)
c.close()
```

```term
$ python b34_plan.py iha.db
WHERE ucus_id = 5 AND zaman_sn > 600
     SEARCH telemetri USING INDEX ix_tel_uz (ucus_id=? AND zaman_sn>?)
WHERE zaman_sn = 600
     SCAN telemetri
WHERE ucus_id + 0 = 5
     SCAN telemetri
WHERE ucus_id BETWEEN 5 AND 9 ORDER BY zaman_sn
     SEARCH telemetri USING INDEX ix_tel_uz (ucus_id>? AND ucus_id<?)
     USE TEMP B-TREE FOR ORDER BY
WHERE ucus_id = 5 ORDER BY zaman_sn
     SEARCH telemetri USING INDEX ix_tel_uz (ucus_id=?)
ucak WHERE kuyruk = 'UA-001'
     SEARCH ucak USING INDEX sqlite_autoindex_ucak_1 (kuyruk=?)
ucak WHERE kuyruk LIKE 'UA-00%'
     SCAN ucak
ucak WHERE kuyruk LIKE '%001'
     SCAN ucak
case_sensitive_like = ON, ucak LIKE 'UA-00%':
     SEARCH ucak USING INDEX ix_uk (kuyruk>? AND kuyruk<?)
```

Çıktı kuralları tek tek doğrular. `ucus_id = 5 AND zaman_sn > 600` iki sütunun da kullanıldığı bir SEARCH'tür. `zaman_sn = 600` için SCAN çıkar. `ucus_id + 0 = 5` için de SCAN çıkar. `BETWEEN` aralığı ilk sütunda olduğunda arama yapılır, ama satırlar `zaman_sn` sırasında gelmez; bu yüzden `USE TEMP B-TREE FOR ORDER BY` eklenir. Eşitlik koşulunda ise ORDER BY ek bir yapı gerektirmez. Son kısımda, `case_sensitive_like` açılınca aynı LIKE sorgusu SEARCH'e döner.

### Seçicilik: indeks her zaman kazandırmaz

İndeks, satırların küçük bir bölümünü seçtiğinde kazandırır. Satırların büyük bölümü seçiliyorsa tam tarama, indeks üzerinden rastgele erişimden daha ucuz olabilir. Bunu Örnek 4'te bir raporla göstereceğiz: geniş bir sorguda indeks süreyi düşürmedi, dar bir sorguda ise bu çalıştırmada yaklaşık 250 kat hızlandırdı.

### Ölçüm: indeksin etkisi

Aşağıdaki program bu bölümün ve 34.9'un tüm ölçümlerini üretir. Önce bir veri kümesi kurar (`kur`), ardından indeks öncesi ve sonrası medyan süreleri ölçer. Ölçüm çerçevesi: her sorgu 50 farklı parametreyle çalıştırılır ve medyan alınır; böylece tek bir şanslı ya da şanssız çalıştırma sonucu bozmaz. Program bu bölümde yalnızca `indeks_olcumu` fonksiyonunu kullanır, ama tüm dosya tek bir programdır ve 34.9'daki yazma ile N+1 ölçümlerini de içerir.

Programın ilk bölümü içe aktarmaları, medyan ölçüm yardımcısını ve CSV yazıcısını içerir.

```python
# b34_olcum.py: indeks, yazma ve N+1 ölçümleri (tohum: 34)
import csv
import os
import random
import sqlite3
import statistics
import sys
import tempfile
import time

from b34_sema import kur
from sqlalchemy import ForeignKey, create_engine, event, func, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    selectinload,
)


def medyan_ms(fn, tekrar):
    sure = []
    for i in range(tekrar):
        t0 = time.perf_counter()
        fn(i)
        sure.append((time.perf_counter() - t0) * 1000.0)
    return round(statistics.median(sure), 4)


def yaz_csv(yol, satirlar, basliklar):
    with open(yol, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(basliklar)
        w.writerows(satirlar)


def indeks_olcumu(db, cikti):
    r = random.Random(34)
```

Bir sonraki bölüm, sorgu parametrelerini ve indeks tanımlarını bir sözlükte toplar. Her sorgu için indeks yokken ve indeksle ayrı ayrı süre alınır.

```python
    ucuslar = [r.randint(1, 8072) for _ in range(50)]
    aracler = [r.randint(1, 55) for _ in range(50)]
    con = sqlite3.connect(db)
    sorgular = {
        "telemetri_ucus_zaman": (
            "SELECT zaman_sn, gerilim_v FROM telemetri "
            "WHERE ucus_id = ? AND zaman_sn BETWEEN 600 AND 3600",
            ucuslar,
            [None, "ix_tel_uz ON telemetri(ucus_id, zaman_sn)"],
        ),
        "gorev_ucak_durum": (
            "SELECT COUNT(*) FROM gorev "
            "WHERE ucak_id = ? AND durum = 'tamam'",
            aracler,
            [None, "ix_g_ud ON gorev(ucak_id, durum)"],
        ),
        "gorev_ucak_tarih": (
            "SELECT id FROM gorev WHERE ucak_id = ? "
            "AND baslangic >= '2026-01-01'",
            aracler,
            [
                None,
                "ix_g_ub ON gorev(ucak_id, baslangic)",
                "ix_g_bu ON gorev(baslangic, ucak_id)",
            ],
        ),
    }
    satirlar = []
    for ad, (sql, parametreler, indeksler) in sorgular.items():
        for tanim in indeksler:
            ix = tanim.split(" ")[0] if tanim else ""
            if tanim:
                con.execute("CREATE INDEX %s" % tanim)
            ms = medyan_ms(
                lambda i: con.execute(
                    sql, (parametreler[i % 50],)
                ).fetchall(),
                50,
            )
            satirlar.append((ad, ix or "yok", ms))
```

Döngü her indeks tanımını oluşturur, medyanı ölçer, sonra indeksi siler. Bu sayede her ölçüm bir önceki ölçümün kalıntısından etkilenmez.

```python
            if tanim:
                con.execute("DROP INDEX %s" % ix)
    yaz_csv(
        os.path.join(cikti, "b34_indeks_olcum.csv"),
        satirlar,
        ["sorgu", "indeks", "medyan_ms"],
    )
    con.close()
    for s in satirlar:
        print("%-22s %-22s %9.4f ms" % s)


def yazma_olcumu(tmp, cikti):
    p = os.path.join(tmp, "yazma.db")
    satirlar = []
    for kip in ("otomatik", "tek_islem"):

        def koş(i, kip=kip):
            if os.path.exists(p):
                os.remove(p)
            c = sqlite3.connect(p, autocommit=True)
            c.execute(
                "CREATE TABLE kayit (id INTEGER PRIMARY KEY, "
                "ucus_id INTEGER, zaman_sn INTEGER, "
                "gerilim_v REAL)"
            )
            if kip == "tek_islem":
                c.execute("BEGIN")
            for k in range(1000):
                c.execute(
                    "INSERT INTO kayit (ucus_id, zaman_sn, "
                    "gerilim_v) VALUES (?, ?, ?)",
                    (k % 50, k * 300, 24.5),
                )
            if kip == "tek_islem":
                c.execute("COMMIT")
            c.close()

        ms = medyan_ms(koş, 5 if kip == "otomatik" else 9)
        satirlar.append(("ekle_1000_satir", kip, ms))
```

Yazma ölçümünün fonksiyonu, otomatik işlem ve tek işlem senaryolarını ayrı ayrı çalıştırır. Bu iki senaryonun farkı 34.9'da yorumlanacak.

```python
        print("%-18s %-10s %10.2f ms" % ("ekle_1000_satir", kip, ms))
    # indeksin yazma maliyeti: 100 000 satır tek işlemde
    for k, ixler in enumerate(
        [
            [],
            ["ucus_id"],
            ["ucus_id", "zaman_sn"],
            ["ucus_id", "zaman_sn", "gerilim_v"],
        ]
    ):

        def koş2(i, ixler=ixler):
            if os.path.exists(p):
                os.remove(p)
            c = sqlite3.connect(p)
            c.execute(
                "CREATE TABLE kayit (id INTEGER PRIMARY KEY, "
                "ucus_id INTEGER, zaman_sn INTEGER, "
                "gerilim_v REAL)"
            )
            for c_ad in ixler:
                c.execute(
                    "CREATE INDEX ix_%s ON kayit(%s)" % (c_ad, c_ad)
                )
            c.executemany(
                "INSERT INTO kayit (ucus_id, zaman_sn, "
                "gerilim_v) VALUES (?, ?, ?)",
                ((j % 50, j * 300, 24.5) for j in range(100000)),
            )
            c.commit()
            c.close()

        ms = medyan_ms(koş2, 9)
        satirlar.append(
            ("100k_satir_%d_indeks" % len(ixler), "tek_islem", ms)
        )
        print(
            "%-18s %-10s %10.2f ms"
            % ("100k_%d_indeks" % len(ixler), "tek_islem", ms)
        )
```

Aynı fonksiyonun devamında, indeks sayısına göre 100 000 satırlık yazma maliyeti ölçülür.

```python
    yaz_csv(
        os.path.join(cikti, "b34_yazma_olcum.csv"),
        satirlar,
        ["senaryo", "kip", "medyan_ms"],
    )


class Base(DeclarativeBase):
    pass


class Ucak(Base):
    __tablename__ = "ucak"
    id: Mapped[int] = mapped_column(primary_key=True)
    kuyruk: Mapped[str]
    tip: Mapped[str]
    us_id: Mapped[int | None]
    uretim_yili: Mapped[int]
    durum: Mapped[str]
    gorevler: Mapped[list["Gorev"]] = relationship(
        back_populates="ucak"
    )


class Gorev(Base):
    __tablename__ = "gorev"
    id: Mapped[int] = mapped_column(primary_key=True)
    ucak_id: Mapped[int | None] = mapped_column(ForeignKey("ucak.id"))
    baslangic: Mapped[str]
    gorev_tipi: Mapped[str]
    durum: Mapped[str]
    ucak: Mapped[Ucak | None] = relationship(
        back_populates="gorevler"
    )


def n1_olcumu(db, cikti):
    satirlar = []
    engine = create_engine("sqlite:///" + db)
    con = sqlite3.connect(db)
```

Bu aralıkta N+1 karşılaştırması için kullanılan ORM modelleri tanımlanır: `Ucak` ve `Gorev` arasında bire çok ilişki vardır. Modeller SQLAlchemy 2.0 biçimindedir.

```python
    sayac = [0]
    con.set_trace_callback(
        lambda sql: sayac.__setitem__(0, sayac[0] + 1)
    )

    @event.listens_for(engine, "before_cursor_execute")
    def say(conn, cur, sql, params, ctx, many):
        sayac[0] += 1

    def ham_dongu(n):
        for uid in range(1, n + 1):
            con.execute(
                "SELECT MAX(x.kalkis) FROM ucus x JOIN gorev g "
                "ON g.id = x.gorev_id WHERE g.ucak_id = ?",
                (uid,),
            ).fetchone()

    def ham_tek(n):
        con.execute(
            "SELECT g.ucak_id, MAX(x.kalkis) FROM ucus x "
            "JOIN gorev g ON g.id = x.gorev_id "
            "WHERE g.ucak_id <= ? GROUP BY g.ucak_id",
            (n,),
        ).fetchall()

    def orm_skaler_n1(n):
        with Session(engine) as s:
            for uid in range(1, n + 1):
                s.scalar(
                    select(func.max(Gorev.baslangic)).where(
                        Gorev.ucak_id == uid
                    )
                )

    def orm_skaler_tek(n):
        with Session(engine) as s:
            s.execute(
                select(Gorev.ucak_id, func.max(Gorev.baslangic))
                .where(Gorev.ucak_id <= n)
                .group_by(Gorev.ucak_id)
```

N+1 fonksiyonu, dört yöntemi (ham döngü, ham tek sorgu, ORM skaler, ORM yüklemeleri) aynı girdi üzerinde çalıştırır. Sorgu sayısını bağlantı izleyicisiyle sayar.

```python
            ).all()

    def orm_tembel(n):
        with Session(engine) as s:
            for u in s.scalars(select(Ucak).where(Ucak.id <= n)):
                len(u.gorevler)  # her uçak için ayrı SELECT

    def orm_secmeli(n):
        with Session(engine) as s:
            for u in s.scalars(
                select(Ucak)
                .where(Ucak.id <= n)
                .options(selectinload(Ucak.gorevler))
            ):
                len(u.gorevler)  # iki SELECT, toplam

    for n in (10, 30, 60):
        for ad, fn in [
            ("ham_dongu_n1", ham_dongu),
            ("ham_tek_join", ham_tek),
            ("orm_skaler_n1", orm_skaler_n1),
            ("orm_skaler_tek", orm_skaler_tek),
            ("orm_tembel_n1", orm_tembel),
            ("orm_selectinload", orm_secmeli),
        ]:
            sayac[0] = 0
            fn(n)
            sorgu = sayac[0]
            ms = medyan_ms(lambda i, fn=fn, n=n: fn(n), 20)
            satirlar.append((ad, n, sorgu, ms))
            print(
                "%-16s n=%2d sorgu=%3d %9.3f ms" % (ad, n, sorgu, ms)
            )
    con.close()
    engine.dispose()
    yaz_csv(
        os.path.join(cikti, "b34_n1_olcum.csv"),
        satirlar,
        ["yontem", "ucak_sayisi", "sorgu_sayisi", "medyan_ms"],
    )
```

Son bölüm, üç ölçümü sırayla çalıştırır ve sonuçları CSV dosyalarına yazar.

```python


if __name__ == "__main__":
    cikti = sys.argv[1] if len(sys.argv) > 1 else "."
    tmp = tempfile.mkdtemp(prefix="b34_")
    db = os.path.join(tmp, "iha.db")
    kur(db)
    print("== indeks ==")
    indeks_olcumu(db, cikti)
    print("== yazma ==")
    yazma_olcumu(tmp, cikti)
    print("== N+1 ==")
    n1_olcumu(db, cikti)
```

Programı `python b34_olcum.py <cikti_klasoru>` ile çalıştırdığında, sonuçları ham olarak şöyle görürsün:

```term
$ python b34_olcum.py ../engine/veri
== indeks ==
telemetri_ucus_zaman   yok                      10.5373 ms
telemetri_ucus_zaman   ix_tel_uz                 0.0762 ms
gorev_ucak_durum       yok                       0.3332 ms
gorev_ucak_durum       ix_g_ud                   0.0632 ms
gorev_ucak_tarih       yok                       0.3606 ms
gorev_ucak_tarih       ix_g_ub                   0.0757 ms
gorev_ucak_tarih       ix_g_bu                   0.1887 ms
== yazma ==
ekle_1000_satir    otomatik      2410.54 ms
ekle_1000_satir    tek_islem        7.11 ms
100k_0_indeks      tek_islem       81.98 ms
100k_1_indeks      tek_islem      161.47 ms
100k_2_indeks      tek_islem      196.74 ms
100k_3_indeks      tek_islem      232.73 ms
== N+1 ==
ham_dongu_n1     n=10 sorgu= 10     5.858 ms
ham_tek_join     n=10 sorgu=  1     0.852 ms
orm_skaler_n1    n=10 sorgu= 10     5.093 ms
orm_skaler_tek   n=10 sorgu=  1     0.929 ms
orm_tembel_n1    n=10 sorgu= 11    13.588 ms
orm_selectinload n=10 sorgu=  2    15.057 ms
ham_dongu_n1     n=30 sorgu= 30    19.707 ms
ham_tek_join     n=30 sorgu=  1     1.589 ms
orm_skaler_n1    n=30 sorgu= 30    16.349 ms
orm_skaler_tek   n=30 sorgu=  1     1.729 ms
orm_tembel_n1    n=30 sorgu= 31    55.730 ms
orm_selectinload n=30 sorgu=  2    62.642 ms
ham_dongu_n1     n=60 sorgu= 60    38.684 ms
ham_tek_join     n=60 sorgu=  1     2.144 ms
orm_skaler_n1    n=60 sorgu= 60    41.298 ms
orm_skaler_tek   n=60 sorgu=  1     3.063 ms
orm_tembel_n1    n=60 sorgu= 61    93.810 ms
orm_selectinload n=60 sorgu=  2   125.095 ms
```

Üç satır bu bölüm için önemlidir. `telemetri` tablosunda `ucus_id ve zaman_sn` indeksi, arama süresini 10,54 ms'den 0,076 ms'ye indirir; bu yaklaşık 138 kat. `gorev` tablosu yalnızca 9 000 satır olduğu için kazanç daha küçüktür: `ucak_id, durum` indeksi yaklaşık 5 kat, `ucak_id, baslangic` indeksi yaklaşık 5 kat sağlar. Son satır, indeks sütunlarını ters sırayla (`baslangic, ucak_id`) koyduğunda kazancın yaklaşık 4,8 kattan 1,9 kata düştüğünü gösterir: bu, en sol önek kuralının ölçülebilir bedelidir.

![Şekil 34.7: İndeks öncesi ve sonrası medyan süreler (logaritmik ölçek). Sayılar makineye göre değişir; oranlar ve sıra korunur.](gorseller/b34_indeks_olcum.png)

::: dikkat
Bu sayılar Windows 11 üzerinde, Python 3.12.10 ve SQLite 3.49.1 ile alındı; ardışık çalıştırmalarda telemetri sorgusunun indekssiz süresi 10 ile 11 ms arasında kaldı. Senin makinende mutlak değerler farklı olur. Ölçümün gerçek sonucu şudur: indeks büyük tabloda çarpan kazandırır, küçük tabloda kazanç sınırlıdır.
:::


## 34.9 Uygulama tarafı: toplu yazma ve N+1 sorunu

Sorgu tek başına hızlı olsa da, uygulamanın onu nasıl çağırdığı toplam süreyi çoğu zaman belirler. Bu bölümde iki yaygın hatayı ölçüyoruz: her satırı ayrı bir işlemle yazmak ve bir listeyi döngüde tek tek sorgulamak (N+1 problemi).

### Her satır için ayrı işlem mi, tek işlem mi?

Bölüm 28'de gördüğün gibi, bir işlemin kalıcı olması için günlüğün diske inmesi gerekir; bu da bir `fsync` maliyetidir. Otomatik işlem kipinde (autocommit) her `INSERT`, kendi `COMMIT`'ini ve dolayısıyla kendi `fsync`'ini getirir. Tüm satırları tek bir işlemde yazmak ise bu maliyeti bir kez öder.

Aşağıdaki ölçüm, 1 000 satırın iki kipte yazılma süresini ve 100 000 satırın indeks sayısına göre yazılma süresini karşılaştırır. Ölçüm kodu 34.8'deki programın içindedir.

![Şekil 34.8: Solda 1 000 satırın ayrı işlemlerle ve tek işlemle yazılma süreleri (log ölçek); sağda 100 000 satırın tek işlemle, indeks sayısına göre süresi.](gorseller/b34_yazma_olcum.png)

Son ölçümde (`olcum_ham.txt`) iki kip arasındaki fark şöyleydi: her satır ayrı işlem 2 410,5 ms, tek işlem 7,1 ms. Yani yaklaşık 340 kat. Aynı ölçümü beş farklı çalıştırmada yaptık: ayrı işlemlerle yazma 2,3 ile 6,0 saniye arasında, oran ise 300 ile 830 kat arasında çıktı. Mutlak sayılar disk ve sistem yüküne göre değişir; ama her satırın ayrı `fsync` aldığı kip, tek işlem kipinden her zaman çok daha yavaştır. Sayıyı kendi makinende yeniden ölçmek için programı çalıştır.

İndeksin yazma maliyeti de buradan görülür. Aynı 100 000 satır tek işlemde yazıldığında, hiç indeks yokken 82 ms, bir indeksle 161 ms, iki indeksle 197 ms, üç indeksle 233 ms sürdü. Her indeks, her yeni satır için ek bir B+ ağacı güncellemesi demektir. Bu yüzden indeks okuma sorgularını hızlandırır ama yazmayı yavaşlatır. Bir tabloya kaç indeks ekleyeceğine, o tablodaki okuma ve yazma oranına bakarak karar verirsin.

Toplu ekleme için uygulama tarafında iki ilke yeterlidir: satırları `executemany` ile tek çağrıda ver ve tüm partiyi tek bir işlem içinde commit et. Python'da bu, `sqlite3` bağlantısını otomatik işlem dışında tutup son adımda bir kez `COMMIT` çağırmak demektir.

### N+1 sorunu

N+1 sorunu şöyle başlar: bir sorgu N satır döndürür ve uygulama her satır için ek bir sorgu çalıştırır. Toplam N+1 sorgu olur. Örneğin 60 uçağın her birinin son görev tarihini ayrı ayrı sormak, bunu tek bir `GROUP BY` ile almaktan 61 kat fazla sorgu demektir.

ORM'lerde bu daha sinsidir. Bir uçak nesnesinin `gorevler` özelliğine erişmek, arka planda bir sorgu tetikleyebilir (tembel yükleme, lazy loading). Döngü içinde bunu yaparsan, kod kısa ve temiz görünür ama veritabanı sorgu patlaması yaşar.

![Şekil 34.9: N+1 yöntemi ile tek sorgunun karşılaştırması. Sol: ham sqlite3. Sağ: SQLAlchemy ORM. Yatay eksen uçak sayısı, dikey eksen medyan süredir.](gorseller/b34_n1_olcum.png)

Ölçüm sonuçları (son çalıştırma, 60 uçak için) şöyledir:

| Yöntem | Sorgu sayısı | Medyan süre |
|---|---|---|
| Ham sqlite3, döngüde sorgu (N+1) | 60 | 38,7 ms |
| Ham sqlite3, tek GROUP BY | 1 | 2,1 ms |
| ORM skaler sorgu, döngüde | 60 | 41,3 ms |
| ORM skaler sorgu, tek GROUP BY | 1 | 3,1 ms |
| ORM tembel yükleme (N+1) | 61 | 93,8 ms |
| ORM selectinload | 2 | 125,1 ms |

İki sonuç dikkat çekicidir. Birincisi, sorgu sayısını düşürmek, aynı veriyi işleyen iki yöntem arasında bile 13 ila 18 kat fark yaratır. İkincisi, `selectinload` sorgu sayısını 61'den 2'ye düşürmesine rağmen daha yavaştır. Sebep, yüklenen veri hacmidir: `selectinload` tüm görev nesnelerini (yaklaşık 9 000 satır) ORM nesnelerine çevirir; bu, sorgu sayısından bağımsız bir maliyettir. Yani N+1'i düzeltmek her zaman yeterli değildir; yüklediğin veri miktarını da sorgulamalısın. Yalnızca özet değerler gerekiyorsa, skaler `GROUP BY` sorgusu en iyi yoldur.

Bu ölçüm yerel bir dosya veritabanında, aynı süreçte yapıldı. Sunucu tabanlı bir veritabanında her sorgu bir ağ gidiş-dönüşü de ekler (genel bilgi). Bu durumda N+1'in cezası çok daha büyür, çünkü sorgu sayısı doğrudan ağ gecikmesiyle çarpılır. Bu makinede ölçmediğimiz bu fark, sorgu sayısını azaltmanın neden her zaman doğru yön olduğunu açıklar.

::: dikkat
N+1'i bir testte yakalamak için sorgu sayısını saymak, süreyi ölçmekten daha güvenilirdir. Yukarıdaki programda `set_trace_callback` ve SQLAlchemy olayları bu sayıyı verir. Yeni bir endpoint yazdığında, bir istekte kaç sorgu çalıştığını bir test içinde doğrula.
:::


## 34.10 İşlemler: kilit, izolasyon ve kayıp güncelleme

Bir işlem (transaction), birden çok ifadenin ya hep birlikte ya hiç uygulanmasını sağlayan bir sınırdır. Bölüm 33'te ACID özelliklerini ve izolasyon anomalilerini kuramsal olarak gördün. Bu bölümde aynı kavramların pratik karşılığına bakıyoruz: `BEGIN`, `COMMIT`, `ROLLBACK`, kilitler ve gerçek bir kayıp güncelleme.

Temel komutlar kısadır: `BEGIN` işlemi başlatır, `COMMIT` değişiklikleri kalıcı yapar, `ROLLBACK` hepsini geri alır. Bir işlemin içinde `SAVEPOINT` ile daha küçük bir geri dönüş noktası tanımlayabilirsin; `ROLLBACK TO` yalnızca o noktaya kadar olan değişiklikleri geri alır ve işlemi açık bırakır.

Aşağıdaki program bu davranışı tek bir işlemde gösterir.

```python
# b34_savepoint.py: işlem içinde SAVEPOINT ile kısmi geri alma
import sqlite3

c = sqlite3.connect(":memory:", isolation_level=None)
c.execute(
    "CREATE TABLE bakim_log (id INTEGER PRIMARY KEY, "
    "aciklama TEXT)"
)


def say():
    return c.execute("SELECT COUNT(*) FROM bakim_log").fetchone()[0]


c.execute("BEGIN")
c.execute(
    "INSERT INTO bakim_log (aciklama) VALUES ('motor kontrolü')"
)
c.execute("SAVEPOINT kisim")
c.execute(
    "INSERT INTO bakim_log (aciklama) VALUES ('pervane değişimi')"
)
c.execute("INSERT INTO bakim_log (aciklama) VALUES ('hatalı kayıt')")
print("savepoint içinde kayıt:", say())
c.execute("ROLLBACK TO kisim")
print("ROLLBACK TO sonrası   :", say())
c.execute("RELEASE kisim")
c.execute("COMMIT")
print("COMMIT sonrası        :", say())
print("işlem açık mı         :", c.in_transaction)
```

```term
$ python b34_savepoint.py
savepoint içinde kayıt: 3
ROLLBACK TO sonrası   : 1
COMMIT sonrası        : 1
işlem açık mı         : False
```

Çıktı, üç kaydın eklendiğini, `ROLLBACK TO` ile son iki kaydın geri alındığını ve ilk kaydın işlemde kaldığını gösterir. `COMMIT`'ten sonra işlem kapanır (`in_transaction` False). Bu, SAVEPOINT'in bir işlemin içindeki kısmi bir geri alma aracı olduğunu açıkça ortaya koyar.

::: not
Python'un `sqlite3` modülünün işlem davranışı sürüme göre değişmiştir. Python 3.12 ile `connect` çağrısına `autocommit` parametresi eklendi. Bu bölümde iki kipi de kullanıyoruz: `autocommit=True` ile her ifade kendi işlemidir; varsayılan kipte ise modül DML ifadelerinden önce kendisi `BEGIN` verir ve `commit()` ile kapatmanı bekler. Hangi kipte olduğunu bilmeden işlem sınırı çizemezsin.
:::

### İzolasyon seviyeleri

Eşzamanlı işlemler birbirinin ara durumunu ne kadar görmelidir? SQL standardı dört seviye tanımlar ve her seviyenin hangi anomalilere izin verdiğini belirtir (genel bilgi):

| Seviye | Kirli okuma | Tekrarlanamayan okuma | Hayalet satır |
|---|---|---|---|
| READ UNCOMMITTED | olabilir | olabilir | olabilir |
| READ COMMITTED | olmaz | olabilir | olabilir |
| REPEATABLE READ | olmaz | olmaz | olabilir |
| SERIALIZABLE | olmaz | olmaz | olmaz |

Kirli okuma, başka bir işlemin commit etmediği değişikliği görmektir. Tekrarlanamayan okuma, aynı satırı aynı işlemde iki kez okuyup farklı değer görmektir. Hayalet satır, aynı koşulla iki kez sorgulandığında yeni bir satırın belirmesidir.

SQLite'ta durum farklıdır: SQLite belgesi, eşzamanlı işlemlerin serileştirilebilir (SERIALIZABLE) davranışını temel alır (genel bilgi). PostgreSQL'in varsayılanı READ COMMITTED'dır (genel bilgi; bu makinede çalıştırılmadı). Yani aynı SQL, iki motorda farklı eşzamanlılık davranışı gösterir; bu, taşınabilir uygulama yazarken bilinmesi gereken bir gerçektir.

### SQLite'ta kilitlenme: database is locked

SQLite'ta yazma işlemleri tüm veritabanını kilitler (ya da kilit yazıcı için ayrılır). Varsayılan günlük kipi `DELETE`'tir (bu makinede `journal_mode` sorgusuyla doğrulandı). Bu kipte bir yazıcı commit yapana kadar başka bir yazıcı bekler ya da hata alır. `WAL` (write-ahead log) kipine geçince okuyucular yazıcıyı engellemez; bu, eşzamanlı okuma ağırlıklı uygulamalar için önemli bir kazançtır.

Aşağıdaki program dört senaryoyu tek bir dosyada çalıştırır: kayıp güncelleme, sürüm sütunu ile iyimser kilit, kilitlenme ve zaman aşımı, WAL kipinde okuyucu davranışı. Senaryolar, iki bağlantının sırayla yaptığı işlemlerle deterministik olarak üretilir; zamanlamaya bağlı değildir. Yalnızca `busy_timeout` senaryosu kısa bir iş parçacığı kullanır ve bekleme süresi bir yarış sonucunu değiştirmez.

```python
# b34_kilit.py: kayıp güncelleme, iyimser kilit, kilitlenme ve WAL
import os
import sqlite3
import tempfile
import threading
import time

p = os.path.join(tempfile.mkdtemp(prefix="b34_"), "kilit.db")


def kur():
    c = sqlite3.connect(p, autocommit=True)
    c.execute("DROP TABLE IF EXISTS sayac")
    c.execute(
        "CREATE TABLE sayac (id INTEGER PRIMARY KEY, "
        "deger INTEGER NOT NULL, surum INTEGER NOT NULL DEFAULT 0)"
    )
    c.execute("INSERT INTO sayac (id, deger) VALUES (1, 100)")
    return c


def kayip_guncelleme():
    print("== kayıp güncelleme (kilit yok) ==")
    kur()
    a = sqlite3.connect(p, autocommit=True)
    b = sqlite3.connect(p, autocommit=True)
    da = a.execute("SELECT deger FROM sayac WHERE id=1").fetchone()[0]
    db_ = b.execute("SELECT deger FROM sayac WHERE id=1").fetchone()[
        0
    ]
    print("A okudu:", da)
    print("B okudu:", db_)
    a.execute("UPDATE sayac SET deger=? WHERE id=1", (da + 10,))
    print("A yazdı (+10):", da + 10)
    b.execute("UPDATE sayac SET deger=? WHERE id=1", (db_ + 5,))
    print("B yazdı (+5):", db_ + 5, "-> beklenen 115")
    son = a.execute("SELECT deger FROM sayac WHERE id=1").fetchone()[
        0
    ]
    print("son değer:", son)
```

Başta yardımcı `kur()` fonksiyonu, her senaryo için aynı başlangıç durumunu kurar: tek satırlık bir sayaç tablosu, değeri 100 ve sürümü 0. Her senaryo bu durumdan başlar, böylece sonuçlar birbirini etkilemez.

```python
    a.close()
    b.close()


def iyimser_kilit():
    print("== iyimser kilit (surum sütunu) ==")
    kur()
    a = sqlite3.connect(p, autocommit=True)
    b = sqlite3.connect(p, autocommit=True)
    ra = a.execute(
        "SELECT deger, surum FROM sayac WHERE id=1"
    ).fetchone()
    rb = b.execute(
        "SELECT deger, surum FROM sayac WHERE id=1"
    ).fetchone()
    print("A okudu:", ra)
    print("B okudu:", rb)
    n = a.execute(
        "UPDATE sayac SET deger=?, surum=surum+1 "
        "WHERE id=1 AND surum=?",
        (ra[0] + 10, ra[1]),
    ).rowcount
    print("A yazdı: satır =", n)
    n = b.execute(
        "UPDATE sayac SET deger=?, surum=surum+1 "
        "WHERE id=1 AND surum=?",
        (rb[0] + 5, rb[1]),
    ).rowcount
    print("B yazdı: satır =", n, "-> çakışma, yeniden okunuyor")
    rb = b.execute(
        "SELECT deger, surum FROM sayac WHERE id=1"
    ).fetchone()
    print("B yeniden okudu:", rb)
    n = b.execute(
        "UPDATE sayac SET deger=?, surum=surum+1 "
        "WHERE id=1 AND surum=?",
        (rb[0] + 5, rb[1]),
    ).rowcount
    print("B yazdı: satır =", n)
    print(
```

Kayıp güncelleme senaryosu, iki bağlantının aynı değeri okuyup kendi değişikliğini yazmasının sonucunu gösterir. Okuma ve yazma ayrı ifadeler olduğu için aralarında bir kilit yoktur.

```python
        "son değer:",
        a.execute(
            "SELECT deger, surum FROM sayac " "WHERE id=1"
        ).fetchone(),
    )
    a.close()
    b.close()


def kilitlenme():
    print("== kilitlenme (rollback journal) ==")
    kur()
    a = sqlite3.connect(p, autocommit=True)
    b = sqlite3.connect(p, timeout=0, autocommit=True)
    a.execute("BEGIN IMMEDIATE")
    a.execute("UPDATE sayac SET deger=deger+1 WHERE id=1")
    print("A BEGIN IMMEDIATE ve yazdı, commit yok")
    try:
        b.execute("UPDATE sayac SET deger=deger+1 WHERE id=1")
        print("B yazdı")
    except sqlite3.OperationalError as e:
        print("B yazamadı:", e)
    a.execute("COMMIT")
    a.close()
    b.close()
    print("== kilitlenme: busy_timeout ile bekleme ==")
    kur()
    a = sqlite3.connect(p, autocommit=True)
    a.execute("BEGIN IMMEDIATE")
    a.execute("UPDATE sayac SET deger=deger+1 WHERE id=1")
    sonuc = []

    def b_is():
        b = sqlite3.connect(p, timeout=5, autocommit=True)
        b.execute("UPDATE sayac SET deger=deger+1 WHERE id=1")
        sonuc.append("B yazdı (bekledi)")
        b.close()

    t = threading.Thread(target=b_is)
    t.start()
```

İyimser kilit fonksiyonu, `surum` sütununu koşul olarak kullanır. Yazma yalnızca sürüm hâlâ okunan değerdeyse gerçekleşir; değilse satır sayısı 0 döner ve uygulama yeniden okuyup denemelidir.

```python
    time.sleep(0.5)
    print("A commit ediyor")
    a.execute("COMMIT")
    t.join()
    print(sonuc[0])
    print(
        "son değer:",
        a.execute("SELECT deger FROM sayac").fetchone()[0],
    )
    a.close()


def wal():
    print("== WAL: okuyucu yazıcıyı engellemez ==")
    kur()
    c = sqlite3.connect(p, autocommit=True)
    print(
        "journal_mode:",
        c.execute("PRAGMA journal_mode=WAL").fetchone()[0],
    )
    a = sqlite3.connect(p, autocommit=True)
    b = sqlite3.connect(p, timeout=0, autocommit=True)
    a.execute("BEGIN IMMEDIATE")
    a.execute("UPDATE sayac SET deger=999 WHERE id=1")
    print(
        "B okudu (A commit etmedi):",
        b.execute("SELECT deger FROM sayac WHERE id=1").fetchone()[0],
    )
    try:
        b.execute("UPDATE sayac SET deger=1 WHERE id=1")
    except sqlite3.OperationalError as e:
        print("B yazamadı:", e)
    a.execute("COMMIT")
    print(
        "A commit sonrası B okudu:",
        b.execute("SELECT deger FROM sayac WHERE id=1").fetchone()[0],
    )
    for x in (a, b, c):
        x.close()
```

Kilitlenme fonksiyonu iki yolu sınar: sıfır zaman aşımıyla hemen hata, ardından `busy_timeout` ile bekleme. Kodun son kısmı WAL senaryosunu ve ana programı içerir.

```python

if __name__ == "__main__":
    kayip_guncelleme()
    iyimser_kilit()
    kilitlenme()
    wal()
```

```term
$ python b34_kilit.py
== kayıp güncelleme (kilit yok) ==
A okudu: 100
B okudu: 100
A yazdı (+10): 110
B yazdı (+5): 105 -> beklenen 115
son değer: 105
== iyimser kilit (surum sütunu) ==
A okudu: (100, 0)
B okudu: (100, 0)
A yazdı: satır = 1
B yazdı: satır = 0 -> çakışma, yeniden okunuyor
B yeniden okudu: (110, 1)
B yazdı: satır = 1
son değer: (115, 2)
== kilitlenme (rollback journal) ==
A BEGIN IMMEDIATE ve yazdı, commit yok
B yazamadı: database is locked
== kilitlenme: busy_timeout ile bekleme ==
A commit ediyor
B yazdı (bekledi)
son değer: 102
== WAL: okuyucu yazıcıyı engellemez ==
journal_mode: wal
B okudu (A commit etmedi): 100
B yazamadı: database is locked
A commit sonrası B okudu: 999
```

Çıktının ilk bölümü bu bölümün ana uyarısıdır. İki bağlantı da bakiyeyi 100 olarak okudu; biri +10, diğeri +5 yazdı. Son değer 105 oldu: A'nın +10'u kayboldu. Bu, bir uçuş saati sayacında ya da bir görev kotasında olduğunda, yanlış bir toplam anlamına gelir ve sistem bunu hata olarak fark etmez.

![Şekil 34.10: Kayıp güncelleme (solda) ve sürüm sütunu ile iyimser kilit (sağda). Sağda B'nin ilk yazması reddedilir, yeniden okuyup yazar.](gorseller/b34_kayip_guncelleme.png)

Sağ taraf düzeltmeyi gösterir. Kilit tutmadan, koşullu yazmayla çakışmayı tespit etmek ve yeniden denemek mümkündür. Bu desen, yüksek eşzamanlılıkta kilit bekleme maliyetinden kaçınmanın yaygın yoludur. Çakışma sık oluyorsa iyimser kilit yerine açık kilit (`BEGIN IMMEDIATE` ya da satır kilidi) tercih edilir.

Kilitlenme senaryosu, bir bağlantı `BEGIN IMMEDIATE` ile yazma kilidini aldığında, zaman aşımı sıfır olan diğer bağlantının `database is locked` hatası aldığını gösterir. Aynı ilk bağlantıdan sonra `busy_timeout` (Python'da `timeout` parametresi) verilen ikinci bağlantı, commit'e kadar bekler ve yazar. Son değer 102 olur: iki artış da uygulandı, ikisi de kaybolmadı. Sınır şudur: bekleme süresi uzunsa kullanıcı yanıt süresi uzar; kısaysa hata sık görünür. Üretimde bekleme süresi ölçülerek seçilmelidir.

WAL senaryosu, A commit etmeden önce B'nin eski değeri (100) okuyabildiğini, ama yazamadığını gösterir. A commit ettikten sonra B yeni değeri (999) görür. Bu, izolasyonun okuma tarafının WAL ile nasıl çalıştığını gösterir: okuyucu bir anlık görüntü (snapshot) okur.

### Yazma sırası ve işlem sınırı

Bir işlemin sınırını nerede çizdiğin, hangi değişikliklerin birlikte kalıcı olacağını belirler. İki kuralı ayırt etmek gerekir. Birincisi, birbirine bağlı değişiklikler (bir bakım kaydı ve uçağın durumu gibi) tek bir işlemde olmalıdır; aksi halde biri kalıcı, diğeri değil olabilir. İkincisi, işlem ne kadar uzun açık kalırsa, o kadar çok kilit tutulur ve diğer işlemler o kadar çok bekler. Bu nedenle işlemi, ihtiyaç duyan en küçük iş birimini kapsayacak kadar tut, ama bağlantı beklemesi (kullanıcı girdisi, ağ çağrısı) içine koyma.


## 34.11 Güvenli SQL ve uygulamadan kullanım

SQL, bir metin dilidir. Uygulama bir sorguyu metin birleştirerek kurarsa, kullanıcı girdisi sorgunun parçası olur ve girdi, sorguyu değiştirebilir. Buna **SQL enjeksiyonu** denir. Açık kaynak dünyasında en eski ve en yaygın güvenlik açıklarından biridir; bugün de sık görülür, çünkü hatalı kod hâlâ yazılabilir.

Mekanizma basittir. Kullanıcı girdisi `x' OR '1'='1` olduğunda, `kuyruk = '<girdi>'` koşulu her zaman doğru olur ve tüm satırlar döner. Daha kötü bir girdi, sorguya ikinci bir deyim ekleyebilir. Aşağıdaki program iki yaklaşımı yan yana koyar: birleştirme ve parametre bağlama.

```python
# b34_enjeksiyon.py: birleştirme ile parametre bağlama; salt okunur
import sqlite3
import sys

c = sqlite3.connect(":memory:")
c.executescript("""
CREATE TABLE ucak (id INTEGER PRIMARY KEY, kuyruk TEXT, durum TEXT);
INSERT INTO ucak VALUES (1, 'UA-001', 'hazir'),
  (2, 'UA-002', 'bakimda'), (3, 'UA-003', 'devre_disi');
""")


def tehlikeli(kuyruk):
    sql = (
        "SELECT id, kuyruk FROM ucak WHERE kuyruk = '" + kuyruk + "'"
    )
    return c.execute(sql).fetchall()


def guvenli(kuyruk):
    return c.execute(
        "SELECT id, kuyruk FROM ucak WHERE kuyruk = ?", (kuyruk,)
    ).fetchall()


saldiri = "x' OR '1'='1"
print("birleştirme, normal girdi:", tehlikeli("UA-002"))
print("birleştirme, saldırı     :", tehlikeli(saldiri))
print("parametre, normal girdi  :", guvenli("UA-002"))
print("parametre, saldırı       :", guvenli(saldiri))
try:
    tehlikeli("x'; DELETE FROM ucak; --")
except sqlite3.Error as e:
    print("birden fazla deyim:", type(e).__name__)
    print("  mesaj:", e)
print(
    "kayıt sayısı:",
    c.execute("SELECT COUNT(*) FROM ucak").fetchone()[0],
)
```

```python
ro = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
try:
    ro.execute("DELETE FROM ucak")
except sqlite3.OperationalError as e:
    print("salt okunur bağlantı:", e)
```

```term
$ python b34_enjeksiyon.py iha.db
birleştirme, normal girdi: [(2, 'UA-002')]
birleştirme, saldırı     : [(1, 'UA-001'), (2, 'UA-002'), (3, 'UA-003')]
parametre, normal girdi  : [(2, 'UA-002')]
parametre, saldırı       : []
birden fazla deyim: ProgrammingError
  mesaj: You can only execute one statement at a time.
kayıt sayısı: 3
salt okunur bağlantı: attempt to write a readonly database
```

Çıktı üç şeyi gösterir. Birleştirme ile yazılan sorgu saldırı girdisinde üç satırın tamamını döndürür. Parametre bağlama ile yazılan sorgu aynı girdiyle hiçbir satır döndürmez, çünkü girdi artık bir **değer**dir, sorgunun parçası değildir. Üçüncü olarak, Python'un `sqlite3` modülü bir `execute` çağrısında yalnızca tek deyime izin verir; bu, ikinci deyimli bir saldırıyı bu sürücüde engeller. Bu ek bir yan etkidir, savunmanın kendisi değildir. Asıl savunma parametre bağlamadır.

**Kural:** SQL'i asla metin birleştirerek kurma. Değer için her zaman yer tutucu (`?` ya da adlı yer tutucu) kullan. Tablo ve sütun adları parametre olamaz; onları dinamik kuracaksan bir izin listesiyle doğrula.

### En az ayrıcalık

Uygulamanın veritabanına bağlanırken kullandığı hesabın yetkisi, bir saldırı olduğunda hasarı sınırlar. Bir rapor servisine yalnızca okuma yetkisi vermek, enjeksiyon olsa bile verinin silinmesini engeller. Bu ilkeye en az ayrıcalık (least privilege) denir.

SQLite'ta kullanıcı ve yetki modeli yoktur; ama dosyayı salt okunur açarak aynı ilkeyi uygulayabilirsin. Yukarıdaki programda `mode=ro` ile açılan bağlantı, silme denemesinde `attempt to write a readonly database` hatası verdi. Sunucu tabanlı veritabanlarında aynısını yetki tanımlarıyla yaparsın (genel bilgi: `GRANT SELECT`).

### ORM'ler ve soyutlamanın bedeli

ORM'ler (SQLAlchemy, Django ORM gibi) SQL'i nesneler üzerinden yazmanı sağlar. Parametre bağlamayı otomatik yaparlar; bu büyük bir kazançtır. Ama bedelleri vardır ve 34.9'da gördük: tembel yükleme N+1 sorununu gizleyebilir, nesne oluşturma maliyeti sorgu süresinden büyük olabilir. Bir ORM'nin ürettiği SQL'i her zaman görmeli, kritik sorguları ise elle yazmalısın.

Pratik bir yaklaşım: ORM'i kullan, ama sorguyu çalıştırmadan önce ürettiği SQL'i yazdır ve sorgu sayısını bir testte doğrula. Bu, soyutlamanın sana ne ödettiğini görmenin en ucuz yoludur.

### PostgreSQL ile farklar (genel bilgi)

Bu bölümün sorguları SQLite'ta çalıştırıldı. Aşağıdaki farklar bilinen genel bilgilerdir ve bu makinede PostgreSQL ile sınanmadı:

| Konu | SQLite (bu bölümde denendi) | PostgreSQL (genel bilgi) |
|---|---|---|
| WHERE'de SELECT takma adı | kabul eder | hata verir |
| Varsayılan izolasyon | serileştirilebilir | READ COMMITTED |
| Dinamik tür | esnek, sütun türü önerisi | katı, tür denetimi sıkı |
| RIGHT / FULL JOIN | 3.39.0 ve üstü | eski sürümlerden beri |
| Yabancı anahtar denetimi | varsayılan kapalı | varsayılan açık |

Bu tablo, bir sorguyu başka motora taşırken hangi satırlara bakman gerektiğini gösterir.

### Gerçek dünya: telemetri analitiği

Bu bölümdeki veri kümesi, bir İHA filosunun işletim verisini modeller. Gerçek sistemde telemetri çok daha büyüktür; bu nedenle üç ilke öne çıkar. Birincisi, ham telemetriyi değil, özetleri raporlamak: uçuş başına ortalama gerilim, düşük gerilim süresi, bakım aralığı. İkincisi, raporları yazma işlemlerinden ayrı tutmak: rapor sorguları salt okunur bir bağlantıdan çalışır ve yazma yollarını kilitlemez. Üçüncüsü, her raporun sorgu planını ve süresini izlemek: indeksin bozulduğu gün, rapor sessizce yavaşlar ve bunu ancak ölçen fark eder.

::: not
Bölüm 35'te yapılandırılmamış ve yarı yapılandırılmış veri için NoSQL modellerini göreceksin. Oradaki kararların çoğu, bu bölümde gördüğümüz sorgu maliyeti ve tutarlılık kararlarının bir uzantısıdır.
:::


## Çözümlü Örnekler

Dört örnek, zorluk sırasıyla ★, ★★, ★★, ★★★ ile ilerler. Her örnek Bölüm 5'in altı adımını izler. Adım 6'da elle izlenebilen bir tablo ve gerçek veriyle doğrulama vardır.

### Örnek 1 (★): Her uçağın son uçuşu

**Adım 1 — Anla.** Her uçak için, en son kalkan uçuşun numarasını ve kalkış zamanını istiyoruz. "En son" kelimesi bir sıralama ister; eşit zamanda iki uçuş varsa hangisinin son olduğu belirsizdir. Bu belirsizliği görmek, örneğin asıl konusudur.

**Adım 2 — Örnekle.** Altı uçuşlu küçük bir küme alalım. Uçak 7'nin uçuşları 10, 11, 14 ve 15 numaralı; 11 ve 15 ikisi de 5 Mart 09:00'da kalkıyor. Uçak 8'in uçuşları 12 ve 13. Uçak 7'nin son uçuşu 11 mi 15 mi? Kuralı belirlemezsek sonuç motora bağlı kalır.

**Adım 3 — Kaba çöz.** En basit yol: her uçak için ayrı bir sorgu çalıştırıp en büyük kalkış zamanını almak (N+1). Bu doğru, ama uçak sayısı kadar sorgu demek. Ardından ikinci bir yol: tüm uçuşları Python'a çekip sözlükte en büyük olanı tutmak. Her iki yol da çalışır, ama veriyi veritabanında sıralamayı tercih ederiz.

**Adım 4 — Örüntü.** Örüntü şudur: *uçakları grupla, her grup içinde sırala, ilk satırı al*. SQL'de bunu iki standart biçimde yazarsın: pencere fonksiyonu `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)` ve ilişkili alt sorgu `ORDER BY ... LIMIT 1`. Eşitliği kırmak için ikinci bir sıralama anahtarı eklemek (uçuş numarası) her iki yazımda da gerekir.

**Adım 5 — İyileştir.** İki sorgu birlikte aşağıda. Pencere sürümü ve ilişkili alt sorgu sürümü aynı sonucu verir; ikisini karşılaştırarak doğrulayacağız.

```python
# b34_ornek1.py: her uçağın son uçuşu, iki yöntem
import sqlite3
import sys

SQL_PENCERE = """
WITH s AS (
  SELECT g.ucak_id AS ucak, x.id AS ucus, x.kalkis,
    ROW_NUMBER() OVER (PARTITION BY g.ucak_id
                       ORDER BY x.kalkis DESC, x.id DESC) AS rn
  FROM ucus x JOIN gorev g ON g.id = x.gorev_id
  WHERE g.ucak_id IS NOT NULL)
SELECT ucak, ucus, kalkis FROM s WHERE rn = 1 ORDER BY ucak
"""

SQL_ALT = """
SELECT g.ucak_id, x.id, x.kalkis
FROM ucus x JOIN gorev g ON g.id = x.gorev_id
WHERE g.ucak_id IS NOT NULL
  AND x.id = (SELECT x2.id FROM ucus x2
              JOIN gorev g2 ON g2.id = x2.gorev_id
              WHERE g2.ucak_id = g.ucak_id
              ORDER BY x2.kalkis DESC, x2.id DESC
              LIMIT 1)
ORDER BY g.ucak_id
"""


def iz():
    c = sqlite3.connect(":memory:")
    c.executescript("""
    CREATE TABLE gorev (id INTEGER PRIMARY KEY, ucak_id INTEGER);
    CREATE TABLE ucus (id INTEGER PRIMARY KEY, gorev_id INTEGER,
                       kalkis TEXT);
    INSERT INTO gorev VALUES (1,7),(2,7),(3,8),(4,8),(5,7);
    INSERT INTO ucus VALUES (10,1,'2026-03-01 10:00'),
      (11,2,'2026-03-05 09:00'),(12,3,'2026-02-20 08:00'),
      (13,4,'2026-03-05 09:00'),(14,5,'2026-03-02 12:00'),
      (15,2,'2026-03-05 09:00');
    """)
    print("küçük küme, pencere:")
```

İlk yarıda küçük kümenin verisi ve pencere sorgusu var; ikinci yarıda ilişkili alt sorgu sürümü ve iki sonucu karşılaştıran sınama bulunur.

```python
    for satir in c.execute(SQL_PENCERE):
        print("  ", satir)
    print("küçük küme, alt sorgu:")
    for satir in c.execute(SQL_ALT):
        print("  ", satir)
    c.close()


if __name__ == "__main__":
    iz()
    c = sqlite3.connect(sys.argv[1])
    a = c.execute(SQL_PENCERE).fetchall()
    b = c.execute(SQL_ALT).fetchall()
    print("veri: uçak sayısı =", len(a), ", eşit =", a == b)
    print("ilk üç satır:")
    for satir in a[:3]:
        print("  ", satir)
```

**Adım 6 — Doğrula.** Önce küçük kümeyi elle izleyelim. `ROW_NUMBER`, `kalkis DESC, id DESC` sıralamasına göre numara verir:

| Uçuş | Uçak | Kalkış | Sıra (uçak içinde) | Seçildi |
|---|---|---|---|---|
| 15 | 7 | 2026-03-05 09:00 | 1 | evet |
| 11 | 7 | 2026-03-05 09:00 | 2 | hayır |
| 14 | 7 | 2026-03-02 12:00 | 3 | hayır |
| 10 | 7 | 2026-03-01 10:00 | 4 | hayır |
| 13 | 8 | 2026-03-05 09:00 | 1 | evet |
| 12 | 8 | 2026-02-20 08:00 | 2 | hayır |

Eşitlik kırıldı: 15 numaralı uçuşun numarası 11'den büyük olduğu için (id DESC) önce gelir. Bu kural, sorguyu her çalıştırmada aynı sonucu vermeye zorlar.

Gerçek veride iki yöntem de 55 uçak için aynı listeyi verdi. Çıktının ilk üç satırı şöyledir:

```term
$ python b34_ornek1.py iha.db
küçük küme, pencere:
   (7, 15, '2026-03-05 09:00')
   (8, 13, '2026-03-05 09:00')
küçük küme, alt sorgu:
   (7, 15, '2026-03-05 09:00')
   (8, 13, '2026-03-05 09:00')
veri: uçak sayısı = 55 , eşit = True
ilk üç satır:
   (1, 4344, '2026-09-22 01:16')
   (2, 7914, '2026-09-21 16:16')
   (3, 7966, '2026-09-21 00:32')
```

**Bunu AI'sız yazabilir misin?** Boş bir dosyada: iki uçağın üç uçuşlu küçük bir kümesini kur. Yalnızca "son uçuşu" bulan pencere sorgusunu yaz; sonra eşitlik olan bir durum ekle ve önce tahmin et, hangi uçuşun seçileceğini. Ardından sorguyu çalıştır ve tahminini karşılaştır.

### Örnek 2 (★★): Hiç görev almamış uçaklar

**Adım 1 — Anla.** Görev tablosunda hiç satırı olmayan uçakları bulmak istiyoruz. Kolay görünüyor; ama `gorev.ucak_id` NULL olabilir ve bu, kullanacağımız yöntemin sonucunu değiştirebilir.

**Adım 2 — Örnekle.** Üç uçak (1, 2, 3) ve üç görev düşünelim: görev 1 ve 3 uçak 1'e atanmış, görev 2 henüz atanmamış (NULL). Doğru cevap: uçak 2 ve uçak 3, çünkü ikisinin de görevi yok.

**Adım 3 — Kaba çöz.** Üç yöntem akla gelir: `LEFT JOIN ... WHERE g.id IS NULL`, `NOT IN (SELECT ucak_id ...)` ve `NOT EXISTS`. İlk ve son yöntem doğru olmalı; ikincisinin bir tuzağı olduğundan şüpheleniriz.

**Adım 4 — Örüntü.** Üç yöntemi üç sonuca karşı sınamak; NULL'un her birinde ne yaptığını izlemek gerekir. `x NOT IN (a, NULL)` ifadesi, `x = a` yanlışsa bile NULL döner (üç değerli mantık, 34.3). NOT IN sonucu NULL olunca satır seçilmez.

**Adım 5 — İyileştir.** Aşağıdaki program üç yöntemi hem küçük kümede hem gerçek veride çalıştırır.

```python
# b34_ornek2.py: hiç görev almamış uçaklar ve NULL tuzağı
import sqlite3
import sys

SORGULAR = {
    "LEFT JOIN": """
        SELECT u.id FROM ucak u
        LEFT JOIN gorev g ON g.ucak_id = u.id
        WHERE g.id IS NULL ORDER BY u.id""",
    "NOT IN": """
        SELECT u.id FROM ucak u
        WHERE u.id NOT IN (SELECT ucak_id FROM gorev)
        ORDER BY u.id""",
    "NOT EXISTS": """
        SELECT u.id FROM ucak u
        WHERE NOT EXISTS (SELECT 1 FROM gorev g
                          WHERE g.ucak_id = u.id)
        ORDER BY u.id""",
}


def kucuk_kume():
    c = sqlite3.connect(":memory:")
    c.executescript("""
    CREATE TABLE ucak (id INTEGER PRIMARY KEY);
    CREATE TABLE gorev (id INTEGER PRIMARY KEY, ucak_id INTEGER);
    INSERT INTO ucak VALUES (1), (2), (3);
    INSERT INTO gorev VALUES (1, 1), (2, NULL), (3, 1);
    """)
    for ad, sql in SORGULAR.items():
        print("küçük %-10s:" % ad, c.execute(sql).fetchall())
    c.close()


if __name__ == "__main__":
    kucuk_kume()
    c = sqlite3.connect(sys.argv[1])
    for ad, sql in SORGULAR.items():
        sonuc = [r[0] for r in c.execute(sql)]
        print("veri %-10s: %d uçak" % (ad, len(sonuc)))
```

Programın ikinci kısmı, gerçek veride üç sorgunun satır sayısını yazar ve NULL görevlerin sayısını ekler.

```python
    print(
        "NULL'lu görev sayısı:",
        c.execute(
            "SELECT COUNT(*) FROM gorev WHERE ucak_id IS NULL"
        ).fetchone()[0],
    )
```

**Adım 6 — Doğrula.** İz tablosu, küçük kümede her uçağın her yöntemde nasıl değerlendirildiğini gösterir:

| Uçak | LEFT JOIN, g.id NULL | NOT IN (1, NULL, 1) | NOT EXISTS |
|---|---|---|---|
| 1 | hayır (görev 1 ve 3) | yanlış (1 bulunur) | hayır |
| 2 | evet | NULL (bilinmiyor) | evet |
| 3 | evet | NULL (bilinmiyor) | evet |

Sonuç: LEFT JOIN ve NOT EXISTS {2, 3} verir; NOT IN ise boş döner. Gerçek veride de aynı şey görüldü: LEFT JOIN ve NOT EXISTS 5 uçak buldu, NOT IN 0 buldu. Gerçek veride 256 görev NULL'dur ve bunlardan biri yeterlidir.

```term
$ python b34_ornek2.py iha.db
küçük LEFT JOIN : [(2,), (3,)]
küçük NOT IN    : []
küçük NOT EXISTS: [(2,), (3,)]
veri LEFT JOIN : 5 uçak
veri NOT IN    : 0 uçak
veri NOT EXISTS: 5 uçak
NULL'lu görev sayısı: 256
```

**Bunu AI'sız yazabilir misin?** Boş bir dosyada: bir `NOT IN` sorgusunun NULL nedeniyle boş döndüğü bir küçük küme kur. Sonra aynı işi `NOT IN`'e NULL filtresi ekleyerek düzelt ve sonucu da `NOT EXISTS` ile karşılaştır. Son soru: `NOT IN (SELECT ucak_id FROM gorev WHERE ucak_id IS NOT NULL)` her zaman doğru mu? Neden?

### Örnek 3 (★★): Gerilim çöküşü aralıkları (gaps-and-islands)

**Adım 1 — Anla.** Her uçuşun telemetrisinde, gerilimin hareketli ortalamasının 23,0 V'un altına düştüğü ardışık zaman aralıklarını bulmak istiyoruz. Bir aralığın başını ve sonunu, kaç örnek içerdiğini raporlamalıyız. Bu problemin adı gaps-and-islands'tır: uygun satırlardan oluşan adaları bulmak.

**Adım 2 — Örnekle.** Altı örnekten oluşan bir dizi düşünelim: sıra numaraları 2, 3, 4, 7, 8, 11. Adalar {2, 3, 4}, {7, 8} ve {11} olmalı; bunlar birbirinden boşluklarla ayrılmıştır.

**Adım 3 — Kaba çöz.** Python'da bir döngüyle: önceki değer adaya aitse devam et, değilse yeni ada başlat. Bu doğrudur, ama veriyi taşımak gerekir. SQL'de aynı işi yapmanın bir numarası vardır.

**Adım 4 — Örüntü.** Numarası kendisiyle ardışık olan satırlar için `sıra − ROW_NUMBER()` sabittir. Ada içinde iki değer de bir artar, fark değişmez; ada değişince fark sıçrar. Bu farka göre gruplarsan, her ada bir gruba düşer. Pencere ortalaması `AVG(...) OVER (ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING)` ile hesaplanır.

**Adım 5 — İyileştir.** Aşağıdaki sorgu hareketli ortalamayı, eşiğin altındaki satırları ve adaları üretir. Python ile bağımsız bir hesap, sonuçları karşılaştırmak için yanında yer alır.

```python
# b34_ornek3.py: gerilim çöküşü aralıkları (gaps-and-islands)
import sqlite3
import sys

ESIK = 23.0
SQL = """
WITH ort AS (
  SELECT zaman_sn,
    AVG(gerilim_v) OVER (ORDER BY zaman_sn
      ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING) AS m,
    ROW_NUMBER() OVER (ORDER BY zaman_sn) AS sira
  FROM telemetri WHERE ucus_id = ?
),
dusuk AS (
  SELECT zaman_sn, sira,
    sira - ROW_NUMBER() OVER (ORDER BY sira) AS grup
  FROM ort WHERE m < ?
)
SELECT MIN(zaman_sn), MAX(zaman_sn), COUNT(*)
FROM dusuk GROUP BY grup ORDER BY MIN(zaman_sn)
"""


def kucuk_dizi():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE t (sira INTEGER)")
    c.executemany(
        "INSERT INTO t VALUES (?)",
        [(s,) for s in (2, 3, 4, 7, 8, 11)],
    )
    sql = """SELECT sira, sira - ROW_NUMBER() OVER (ORDER BY sira)
             FROM t"""
    print("sira, grup:", c.execute(sql).fetchall())
    c.close()


def aralik_bul(c, ucus):
    return c.execute(SQL, (ucus, ESIK)).fetchall()
```

Bu ilk parça üç sorguyu tanımlar: hareketli ortalama, eşiğin altındaki satırların adaları ve küçük dizinin iz hesabı. Ada hesabının sırrı grup sütunudur.

```python
def python_ile(c, ucus):
    """Aynı sonucu düz Python ile bağımsız hesapla."""
    satir = c.execute(
        "SELECT zaman_sn, gerilim_v FROM telemetri "
        "WHERE ucus_id = ? ORDER BY zaman_sn",
        (ucus,),
    ).fetchall()
    g = [v for _, v in satir]
    m = []
    for i in range(len(g)):
        pen = g[max(0, i - 2) : i + 3]  # kenarda pencere kısalır
        m.append(sum(pen) / len(pen))
    aralik, acik = [], None
    for i, (zs, _) in enumerate(satir):
        if m[i] < ESIK:
            if acik is None:
                acik = [zs, zs, 0]
            acik[1] = zs
            acik[2] += 1
        elif acik is not None:
            aralik.append(tuple(acik))
            acik = None
    if acik is not None:
        aralik.append(tuple(acik))
    return aralik


if __name__ == "__main__":
    kucuk_dizi()
    c = sqlite3.connect(sys.argv[1])
    adaylar = [
        r[0]
        for r in c.execute(
            "SELECT DISTINCT ucus_id FROM telemetri "
            "WHERE gerilim_v < 23.5 ORDER BY ucus_id LIMIT 200"
        )
    ]
    bulunan = []
    for u in adaylar:
        aralik = aralik_bul(c, u)
```

Python'daki bağımsız hesap, aynı mantığı düz döngüyle yapar. Kenarda pencerenin kısalmasını burada da açıkça kodladık.

```python
        if aralik:
            bulunan.append(u)
            print("uçuş %d:" % u)
            for bas, son, n in aralik:
                print("  %5d .. %5d sn, %d örnek" % (bas, son, n))
            print("  Python ile aynı mı:", python_ile(c, u) == aralik)
        if len(bulunan) == 2:
            break
```

**Adım 6 — Doğrula.** Küçük dizinin iz tablosu:

| Sıra | ROW_NUMBER | Fark (grup) | Ada |
|---|---|---|---|
| 2 | 1 | 1 | A |
| 3 | 2 | 1 | A |
| 4 | 3 | 1 | A |
| 7 | 4 | 3 | B |
| 8 | 5 | 3 | B |
| 11 | 6 | 5 | C |

Gerçek veride iki uçuş, Python'daki bağımsız hesapla aynı aralıkları verdi. Uçuş 1'de tek bir örnek (2 100 sn) eşiğin altında kaldı; uçuş 2'de 8 700 ile 11 700 saniye arasında 11 örnek. Bu sonuç, verideki gerilim çöküşlerinin (uçuşların yaklaşık %3'ü) sorgu tarafından gerçekten bulunduğunu gösterir.

```term
$ python b34_ornek3.py iha.db
sira, grup: [(2, 1), (3, 1), (4, 1), (7, 3), (8, 3), (11, 5)]
uçuş 1:
   2100 ..  2100 sn, 1 örnek
  Python ile aynı mı: True
uçuş 2:
   8700 .. 11700 sn, 11 örnek
  Python ile aynı mı: True
```

**Bunu AI'sız yazabilir misin?** Boş bir dosyada: sıra numaraları 1, 2, 3, 6, 7, 10 olan bir küme için adaları elle bul, sonra SQL'i yaz ve sonucu karşılaştır. Son soru: zaman damgaları eşit aralıklı değilse (örnekler 5 dakikada bir değil de düzensiz geliyorsa) fark tekniği hâlâ çalışır mı? Hangi sütunu sayarsın?

### Örnek 4 (★★★): Yavaş rapor sorgusu, plan ve indeks

**Adım 1 — Anla.** Bir rapor her uçağın telemetri özetini (örnek sayısı, ortalama gerilim, düşük gerilim sayısı) üretiyor ve yavaş. Görevi hızlandırmak, ama sonucun aynı kalmasını sağlamak.

**Adım 2 — Örnekle.** İki sorgu tanımlıyoruz. Geniş olan, 2026 yılının tamamlanmış tüm görevlerini kapsar ve telemetrinin büyük bölümünü okur. Dar olan, tek bir uçağın tek bir ayını kapsar. İndeksin işe yarayıp yaramayacağını, bu iki sorgunun satır seçiciliği belirler.

**Adım 3 — Kaba çöz.** Sorguyu çalıştırıp süreyi ölçmek ilk adımdır. Ardından `EXPLAIN QUERY PLAN` ile planı okumak gerekir: hangi tablo SCAN ediliyor?

**Adım 4 — Örüntü.** Plan `SCAN t` gösteriyorsa, telemetri tablosu baştan sona okunuyor demektir. Bu, ilişkiyi indekslersen SEARCH'e dönüşebilir. Ama her zaman dönüşmez: seçici olmayan bir sorguda indeks, tabloyu zaten okumak zorundasın demektir ve rastgele erişim ek maliyet getirir. Yani örüntü şudur: *indeks yalnızca satırların küçük bir kısmını seçtiğinde kazandırır*.

**Adım 5 — İyileştir.** Aşağıdaki program her iki sorguyu indeks öncesi ve sonrası ölçer. Her ölçüm yedi çalıştırmanın medyanıdır. İndeksler bir kopya veritabanına eklenir.

```python
# b34_ornek4.py: rapor sorgusu, plan ve indeks (geniş ve dar)
import shutil
import sqlite3
import statistics
import sys
import textwrap
import time

GENIS = """
SELECT g.ucak_id, COUNT(*) AS ornek,
       ROUND(AVG(t.gerilim_v), 3) AS ort_ger,
       SUM(CASE WHEN t.gerilim_v < 23.0 THEN 1 ELSE 0 END) AS dusuk
FROM gorev g
JOIN ucus x ON x.gorev_id = g.id
JOIN telemetri t ON t.ucus_id = x.id
WHERE g.durum = 'tamam' AND g.baslangic >= '2026-01-01'
GROUP BY g.ucak_id
ORDER BY dusuk DESC, g.ucak_id
LIMIT 5
"""
DAR = """
SELECT COUNT(*), ROUND(AVG(t.gerilim_v), 3),
       SUM(CASE WHEN t.gerilim_v < 23.0 THEN 1 ELSE 0 END)
FROM gorev g
JOIN ucus x ON x.gorev_id = g.id
JOIN telemetri t ON t.ucus_id = x.id
WHERE g.ucak_id = 7 AND g.baslangic >= '2026-03-01'
  AND g.baslangic < '2026-04-01'
"""


def plan(c, sql, baslik):
    print("--", baslik)
    for satir in c.execute("EXPLAIN QUERY PLAN " + sql):
        print(
            textwrap.fill(
                satir[3],
                70,
                initial_indent="   ",
                subsequent_indent="       ",
```

Bu parça iki sorguyu ve planı yazdıran yardımcıları tanımlar. Ölçüm fonksiyonu sorguyu yedi kez çalıştırıp medyanı alır.

```python
            )
        )


def olc(c, sql, n=7):
    sure = []
    for _ in range(n):
        t0 = time.perf_counter()
        sonuc = c.execute(sql).fetchall()
        sure.append((time.perf_counter() - t0) * 1000)
    return statistics.median(sure), sonuc


if __name__ == "__main__":
    kopya = "b34_rapor_kopya.db"
    shutil.copyfile(sys.argv[1], kopya)
    c = sqlite3.connect(kopya)
    for ad, sql in [("geniş", GENIS), ("dar", DAR)]:
        plan(c, sql, ad + " sorgu, indeks yokken")
        ms, s0 = olc(c, sql)
        print("medyan: %.3f ms" % ms)
    c.execute(
        "CREATE INDEX ix_gorev_ucak_bas ON gorev(ucak_id, baslangic)"
    )
    c.execute(
        "CREATE INDEX ix_gorev_durum ON gorev(durum, baslangic)"
    )
    c.execute("CREATE INDEX ix_ucus_gorev ON ucus(gorev_id)")
    c.execute("CREATE INDEX ix_tel_ucus ON telemetri(ucus_id)")
    for ad, sql in [("geniş", GENIS), ("dar", DAR)]:
        plan(c, sql, ad + " sorgu, indeksler sonrası")
        ms, s1 = olc(c, sql)
        print("medyan: %.3f ms" % ms)
        print("sonuç aynı mı:", olc(c, sql, 1)[1] == s1)
    print("dar sonuç:", s1)
    c.close()
```

**Adım 6 — Doğrula.** Plan satırları, iki sorgunun indeks öncesi ve sonrası nasıl değiştiğini gösterir:

- Geniş sorgu: önce `SCAN t`, sonra `SEARCH g USING INDEX ix_gorev_durum`. Plan değişti, ama süre değişmedi: bu çalıştırmada 52,5 ms'den 58,7 ms'ye çıktı. Sebep, 2026 tamamlanmış görevlerin telemetrinin %42'sini kapsaması; indeks üzerinden rastgele erişim, tam taramadan daha pahalıya geldi.
- Dar sorgu: önce `SCAN t`, sonra `SEARCH g USING COVERING INDEX ix_gorev_ucak_bas` ve telemetri için `ix_tel_ucus`. Süre 20,8 ms'den 0,082 ms'ye düştü, yaklaşık 250 kat. Sonuçlar iki durumda da aynı.

Bu sayılar makineye göre değişir; ama geniş sorgunun indeksle kazanmaması, dar sorgunun ise kazanması, seçicilik kuralının ölçülebilir kanıtıdır.

```term
$ python b34_ornek4.py iha.db
-- geniş sorgu, indeks yokken
   SCAN t
   SEARCH x USING INTEGER PRIMARY KEY (rowid=?)
   SEARCH g USING INTEGER PRIMARY KEY (rowid=?)
   USE TEMP B-TREE FOR GROUP BY
   USE TEMP B-TREE FOR ORDER BY
medyan: 52.470 ms
-- dar sorgu, indeks yokken
   SCAN t
   SEARCH x USING INTEGER PRIMARY KEY (rowid=?)
   SEARCH g USING INTEGER PRIMARY KEY (rowid=?)
medyan: 20.795 ms
-- geniş sorgu, indeksler sonrası
   SEARCH g USING INDEX ix_gorev_durum (durum=? AND baslangic>?)
   SEARCH x USING COVERING INDEX ix_ucus_gorev (gorev_id=?)
   SEARCH t USING INDEX ix_tel_ucus (ucus_id=?)
   USE TEMP B-TREE FOR GROUP BY
   USE TEMP B-TREE FOR ORDER BY
medyan: 58.687 ms
sonuç aynı mı: True
-- dar sorgu, indeksler sonrası
   SEARCH g USING COVERING INDEX ix_gorev_ucak_bas (ucak_id=? AND
       baslangic>? AND baslangic<?)
   SEARCH x USING COVERING INDEX ix_ucus_gorev (gorev_id=?)
   SEARCH t USING INDEX ix_tel_ucus (ucus_id=?)
medyan: 0.082 ms
sonuç aynı mı: True
dar sonuç: [(98, 23.718, 27)]
```

**Bunu AI'sız yazabilir misin?** Boş bir dosyada: geniş sorguyu hızlandırmak için seçicilik hesabını yap (kaç telemetri satırı kapsanıyor?). Sonra indeksi değil, sorgunun kendisini değiştirmeyi dene: yalnızca gerekli sütunları seç, iç içe bir alt sorguda önceden filtrele. Hangisi süreyi düşürür ve neden?


## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ araçları **yasak**. Amaç çalışan bir rapor paketi ya da bir sorgu yorumlayıcısı üretmek değil; sorgunun ne yaptığını, planın neden o olduğunu ve sonucun doğru olduğunu kendi kararlarınla savunabilmek. Takıl, kâğıda yaz, `EXPLAIN QUERY PLAN` çıktısını oku; çözümü dışarıdan alma.
:::

### Proje 1 (★★): İHA filo yönetimi raporlama paketi

**Amaç:** Filo yöneticisinin on iş sorusunu, her biri için bir SQL sorgusu ve bir indeks gerekçesiyle yanıtlayan bir rapor paketi yaz. Her sorgunun sonucu, Python ile bağımsız olarak hesaplanmış bir değerle karşılaştırılmalıdır.

**Beklenen davranış:** Paket, `iha.db` üzerinde çalışır ve on rapor üretir. Örnek sorular: her uçağın toplam uçuş dakikası; son otuz günde görev yapan uçaklar; bakım maliyeti en yüksek üç ekipman (alt ağaç toplamıyla); her uçuşun en düşük gerilim değeri; iptal oranı ussa göre; düşük gerilim (23,0 V altı) yaşayan uçuşların listesi; hiç görev almamış uçaklar; bir uçağın bakım geçmişi; üs başına ortalama uçuş süresi; ve filo sağlık özeti (hazır, bakımda, devre dışı sayıları). Her rapor, kullandığı sorguyu ve `EXPLAIN QUERY PLAN` çıktısını bir dosyaya yazar.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Her soruyu önce düz kelimelerle yaz, sonra hangi tabloların ve hangi birleşimlerin gerektiğini çiz. Hangi sorguların pencere, CTE ya da alt sorgu istediğine karar ver. Her sorgu için planı oku: SCAN görürsen, hangi koşulun indekslenmesi gerektiğini sor ve gerekçesini yaz. Bağımsız doğrulama için aynı sonucu Python'da liste ve sözlükle hesapla; iki sonuç uyuşmuyorsa önce sorguyu değil, kendi Python kodunu da sorgula.

**Başarı kriterleri:**
- On raporun tamamı, Python'daki bağımsız hesapla birebir aynı sonucu veriyor.
- Her rapor için plan çıktısı ve bir indeks gerekçesi (ya da "indeks gerekmez, çünkü ...") yazılı.
- Düşük gerilim raporu, Örnek 3'teki hareketli ortalamayı kullanıyor ve Python ile uyuşuyor.
- En az bir rapor için, indeks öncesi ve sonrası süre ölçülmüş ve bir seçicilik açıklaması eklenmiş.

### Proje 2 (★★★): Küçük bir SELECT yorumlayıcısı

**Amaç:** `SELECT ... FROM ... WHERE ...` alt kümesini ayrıştıran ve Bölüm 33'teki ilişkisel cebir işlemlerine (seçme, izdüşüm, birleştirme) çeviren küçük bir yorumlayıcı yaz. Yorumlayıcı, tek tablo ve iki tablolu eşitlik birleşimi destekler.

**Beklenen davranış:** `python yorumla.py iha.db "SELECT kuyruk, tip FROM ucak WHERE durum = 'hazir'"` biçiminde bir komut, sonucu SQLite ile aynı satırlar ve sütunlarla yazdırır. Yorumlayıcı, desteklemediği bir yapı (ör. GROUP BY) gördüğünde açık bir hata verir, sessizce yanlış sonuç üretmez. Her çalıştırmada, aynı sorguyu SQLite'a da verip sonuçları karşılaştıran bir sınama modu bulunur.

**Önerilen yaklaşım (ipucu):** Ayrıştırıcı için en küçük parçayla başla: önce `SELECT sütun FROM tablo` çalışsın. Sonra `WHERE` koşullarını, yalnızca `=` ve `AND` destekleyerek ekle. İlişkisel cebir işlemlerini Python'da düz döngülerle yaz: seçme bir filtre, izdüşüm bir sütun seçimi, birleştirme iç içe bir döngü (ya da bir sözlük) olabilir. Ayrıştırmayı basit tut; bir ayrıştırıcı kütüphanesi kullanmadan, bölünmüş metin ve düzenli ifadelerle ilerleyebilirsin.

**Başarı kriterleri:**
- Beş farklı sorguda (tek tablo, koşul, birleşim) sonuçlar SQLite ile birebir aynı.
- Desteklenmeyen bir yapı, anlaşılır bir hata mesajıyla reddediliyor.
- Yorumlayıcının birleştirme işlemi için, iç içe döngü ile sözlük tabanlı yaklaşımın süresi ölçülmüş ve bir tablo halinde raporlanmış.
- Kendi yorumlayıcının neyi yapamadığını açıklayan kısa bir not var; bu not, SQLite'ın plan optimizasyonunun neden gerekli olduğunu gösteriyor.

### Ek Alıştırmalar

Aşağıdaki problemlerin çözümü bu kitapta yok. Önce kâğıda, sonra editöre geç; yapay zekâ yasak. Zorluk etiketine göre sırala.

1. **★ — Eşleşmeyen NULL.** `ucak` ile `bakim` tablosunu LEFT JOIN ile birleştirip "hiç bakım görmemiş uçaklar"ı bul. Sonucun, `WHERE bakim.id IS NULL` yerine `ON` içinde bir koşul kullanmanın neden farklı olacağını açıkla.
2. **★ — Takma ad mı, sütun mu?** `SELECT id + 1 AS id FROM ucak WHERE id > 10` sorgusu hangi satırları döndürür? WHERE'de hangi `id` kullanılır? Cevabını 34.2'deki yürütme sırasıyla gerekçelendir.
3. **★ — Sıra numarası.** Bir uçuş listesinde eşit kalkış zamanlarında `RANK` ile `DENSE_RANK` farkını bir örnek kümeyle göster. Üçüncü sıranın değeri nasıl değişir?
4. **★★ — Üs hesabı.** `baglanti` tablosunda Ana Üs'ten Kuzey Üs'e en az kaç adımda ulaşılır? Özyinelemeli bir CTE yaz; döngü olmasına rağmen sonsuz döngüye girmediğini açıkla.
5. **★★ — Kümülatif toplam.** Her uçağın uçuş dakikalarını, yalnızca son otuz gün içindeki uçuşlar için, kümülatif olarak hesaplayan bir sorgu yaz. Çerçeve tanımında `ROWS` ile `RANGE` farkını açıkla.
6. **★★ — Mülakat: NOT IN ve NULL.** Bir alt sorgu NULL döndürdüğünde `NOT IN` neden boş sonuç verebilir? Bunu iki satırlık bir örnekle kanıtla.
7. **★★ — Mülakat: Sorgu sayısı.** Bir API endpoint'i, bir kullanıcının 50 uçağının son bakımını ORM ile yüklüyor ve her uçak için ayrı sorgu çalışıyor. Bunu tek bir sorguya nasıl indirgersin? Hangi ölçümü yaparak düzelttiğini doğrularsın?
8. **★★ — Mülakat: Kilit beklemesi.** İki işlem aynı satırı güncellemeye çalışıyor. Birinci işlem uzun sürüyor. İkinci işlem neden hemen hata vermeyebilir, `busy_timeout` değerini nasıl seçersin?
9. **★★ — Mülakat: İdempotent özet.** Günlük özet tablosunu her saat başı güncelleyen bir iş, bazen aynı partiyi iki kez işliyor. Toplama yapan UPSERT ile yerine koyan UPSERT arasında hangisi güvenlidir ve neden?
10. **★★★ — Mülakat: İndeks sırası.** `(zaman_sn, ucus_id)` ve `(ucus_id, zaman_sn)` indeksleri, `ucus_id = 5 AND zaman_sn BETWEEN 300 AND 900` sorgusu için aynı derecede iyi mi? Hangi koşulda ikincisi kesinlikle daha iyi olur?
11. **★★★ — Mülakat: Seçicilik eşiği.** Bir sorgu tabloların yüzde kaçını seçtiğinde indeksin sıralı tam taramadan daha pahalı olmaya başladığını nasıl tahmin edersin? Bu eşik sabit midir?
12. **★★★ — Mülakat: Güvenlik ve ORM.** Bir ORM, dinamik `ORDER BY` sütun adını kullanıcıdan alıyor. Parametre bağlama bu durumda neden yetmez? Güvenli bir yaklaşım ne olurdu?

## Kod Okuma Egzersizi

Bu bölümün kod okuma kesiti, SQLite'ın resmi belgesi olan "The SQLite Query Optimizer Overview" sayfasının WHERE yan tümcesi analizi bölümünden (2. ve 2.1. başlıklar) alındı. Kaynak: `https://www.sqlite.org/optoverview.html`, indirildi 2026-10-19; belgede sürüm numarası yok, bu yüzden doğrulamayı SQLite 3.49.1 ile yaptık.

Bu egzersizde belgeyi birebir kopyalamadık. Bunun yerine belgedeki kuralları Türkçe özetledik, kuralların bir kısmını gerçek planlarla sınadık ve tek bir kısa alıntı kullandık. Belgenin ilgili kuralı şudur: indeksin ilk sütunları `=`, `IN` ya da `IS` ile kullanılmalıdır; kuralın kendisine ait ayrıntılar belgede okunabilir.

Aşağıdaki program, belgedeki kuralların beşini bir tablo üzerinde denetler. Tablo, `idx_ex1(a, b, c, d)` bileşik indeksine sahiptir.

```python
# b34_kodokuma.py: SQLite optimizer belgesi 2.1 kurallarını sına
import sqlite3

c = sqlite3.connect(":memory:")
c.execute("CREATE TABLE ex1 (a, b, c, d, e)")
c.execute("CREATE INDEX idx_ex1 ON ex1(a, b, c, d)")
ORNEKLER = [
    "a=5 AND b IN (1,2,3) AND d='hello'",
    "a=5 AND b=1 AND c=2 AND d='x'",
    "b IN (1,2,3) AND c NOT NULL AND d='hello'",
    "a=5 OR b IN (1,2,3) OR c NOT NULL OR d='hello'",
    "a>5 AND b=1",
]
for kosul in ORNEKLER:
    plan = c.execute(
        "EXPLAIN QUERY PLAN SELECT * FROM ex1 WHERE " + kosul
    ).fetchall()
    print("WHERE", kosul)
    print("   ->", plan[0][3])
```

```term
$ python b34_kodokuma.py
WHERE a=5 AND b IN (1,2,3) AND d='hello'
   -> SEARCH ex1 USING INDEX idx_ex1 (a=? AND b=?)
WHERE a=5 AND b=1 AND c=2 AND d='x'
   -> SEARCH ex1 USING INDEX idx_ex1 (a=? AND b=? AND c=? AND d=?)
WHERE b IN (1,2,3) AND c NOT NULL AND d='hello'
   -> SCAN ex1
WHERE a=5 OR b IN (1,2,3) OR c NOT NULL OR d='hello'
   -> SCAN ex1
WHERE a>5 AND b=1
   -> SEARCH ex1 USING INDEX idx_ex1 (a>?)
```

Çıktı kuralları doğrular. `a = 5 AND b IN (...) AND d = '...'` için yalnızca `a` ve `b` kullanılır, çünkü `c` kısıtlanmamıştır ve belgedeki boşluk kuralı nedeniyle `d` kullanılamaz. Hepsi eşitlik olan dört koşul ise dört sütunun tamamını kullanır. `b IN ... AND c NOT NULL ...` için tam tarama çıkar, çünkü ilk sütun `a` kısıtlanmamıştır. OR ile bağlanmış koşullar belgede de tek bir terim sayılır ve tam taramaya düşer. Son satır, bir aralık koşulunun (`a > 5`) bileşik indeksin sonraki sütunlarını (`b`) kullanılamaz kıldığını gösterir.

**Sorular, cevaplamadan geçme:**

1. Belgedeki "indeksin ilk sütunları eşitlikle kullanılmalıdır" kuralını, `a > 5 AND b = 1` sonucuyla karşılaştır. Neden `b` bu sorguda kullanılmıyor? Eşitlik ile aralık koşullarının sıralı listede farkı nedir?
2. `b IN (1,2,3) AND c NOT NULL AND d = 'hello'` sorgusunda `a` eksik. Bu sorguyu tam tarama yerine hızlandırmak için hangi indeks tanımı yeterli olurdu? Yeni indeks, mevcut indeksin yerine mi, yanında mı olmalı?
3. Plan çıktısındaki `SEARCH ex1 USING INDEX idx_ex1 (a=? AND b=?)` ifadesindeki `?` yer tutucuları ne anlama gelir? Bu ifade, sorgu metnindeki sabit değerlerden nasıl ayrılır?
4. `a = 5 OR b IN (1,2,3) OR c NOT NULL OR d = 'hello'` sorgusu için belge "OR optimizasyonu" der: her terim için ayrı indeks gerekebilir. Bu dört terim için kaç ayrı indeks gerekir? Her birinin sütun sırasını yaz.
5. Belge bir sorgu terimi için `column LIKE pattern` biçimini indeksle kullanılabilir sayar. Bu makinede `LIKE 'UA-00%'` için planın değişmesi için hangi PRAGMA gerekti ve bunun varsayılanı neydi? Bu, belgenin koşulunu nasıl sınırlar?
6. Belgedeki kurallar, gerçek sorguda yaptığın seçicilik ölçümüyle (Örnek 4) çelişiyor mu, yoksa tamamlıyor mu? İndeks kullanılabilirliği ile indeksin kazandırması arasındaki farkı tek cümleyle yaz.

## Bölüm Özeti

- SELECT'in mantıksal sırası FROM, WHERE, GROUP BY, HAVING, SELECT, ORDER BY, LIMIT'tir; takma ad, adın tanımlandığı aşamadan sonra görünür. SQLite WHERE'de takma adı kabul eder, ama bu taşınabilir değildir.
- JOIN türleri, sonuçta hangi satırların kalacağını belirler; koşulun ON mu WHERE mi olduğu, bir LEFT JOIN'in dış satırlarını korur mu yoksa siler mi, bunu belirler.
- NULL üç değerli mantık taşır; `NOT IN` alt sorguda bir NULL ile sessizce boş dönebilir. `COUNT(*)` ve `COUNT(sütun)` farklı sayılar verir.
- Özyinelemeli CTE, bir tohum ve bir özyinelemeli üyeden oluşur; `UNION` döngüyü eler. SQLite'ta 93. Fibonacci sayısı 64 bit sınırını aşar ve REAL'e dönüşür.
- Pencere fonksiyonları satırları koruyarak her satıra kendi penceresinden bir değer ekler; çerçeve tanımı toplamların hangi satırlara uygulandığını belirler.
- EXPLAIN QUERY PLAN, sorgunun SCAN ile mi SEARCH ile mi çalıştığını gösterir. Bileşik indekste en sol önek kuralı, ifadeye sarılan sütun ve baştaki joker karakter indeksi devre dışı bırakır.
- İndeks, seçici sorgularda çarpan kazandırır; seçici olmayan bir sorguda kazanç yoktur ya da kayıp olabilir. Her zaman ölçerek karar ver.
- Her satır için ayrı işlem (autocommit) ya da döngüde tek tek sorgu, süreyi çarpan kadar artırır. Toplu yazma ve tek sorguya indirgeme, bu iki hatanın ölçülebilir düzeltmesidir.
- İşlem sınırı, kilit beklemesi ve kayıp güncelleme birlikte düşünülmelidir. İyimser kilit (sürüm sütunu) ve idempotent UPSERT, çakışmayı tespit etmenin ve yeniden denemenin pratik yollarıdır.
- Güvenli SQL, değerler için parametre bağlamayı ve en az ayrıcalığı birlikte gerektirir. Salt okunur bağlantı, rapor sorgusu için en ucuz savunmadır.

**Sonraki bölümde:** Bölüm 35'te NoSQL'e geçiyoruz. Bu bölümde gördüğün sorgu maliyeti ve tutarlılık kararları orada da geçerlidir; yalnızca şema, ölçek ve tutarlılık modeli değişir. Ne zaman ilişkisel modelin, ne zaman belge ya da anahtar-değer modelinin daha uygun olduğunu o bölümde tartışacağız.

::: mulakat
Aşağıdaki sorular cevapsızdır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. `SELECT id + 1 AS id FROM ucak WHERE id > 10` ifadesinde WHERE hangi `id`'yi kullanır? Bu neden standart SQL'de sorun yaratabilir?
2. `LEFT JOIN` yaptın ama sonuçta bazı satırlar eksik. Koşulun ON yerine WHERE'de olması bunu açıklar mı? Bunu nasıl ayırt edersin?
3. Bir alt sorgu NULL döndürdüğünde `NOT IN` neden beklenmedik sonuç verir? Aynı işi güvenle yapan iki yöntem nedir?
4. Özyinelemeli bir CTE'de `UNION` ile `UNION ALL` arasındaki fark nedir? Bir graf üzerinde hangisini ve neden seçersin?
5. `(ucus_id, zaman_sn)` bileşik indeksi var. `zaman_sn = 600` sorgusu neden indeksi kullanmaz? Hangi indeks sırası bunu çözer?
6. Bir işlem içinde yüz satır yazıyorsun, her satır ayrı commit ediliyor. Süre neden bu kadar artar ve bunu nasıl düzeltirsin?
7. İki bağlantı aynı satırı okuyup farklı değerle yazıyor. Kayıp güncellemeyi hangi üç yöntemle önlersin ve her birinin bedeli nedir?
8. Bir sorguyu ORM ile yazdın ve üretimde yavaş. Önce hangi ölçümü yaparsın ve bu ölçüm hangi tür sorunu ayırt etmene yardım eder?
:::
