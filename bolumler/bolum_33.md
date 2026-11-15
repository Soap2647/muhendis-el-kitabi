%% kisim_no: VIII
%% kisim_ad: Veritabanı
%% kisim_ayrac: evet
%% bolum_no: 33
%% baslik: İlişkisel Model

## Giriş: Veriyi bir dosyaya yazmak ile veriyi yönetmek arasındaki fark

Bir ölçüm kaydını dosyaya yazmak kolaydır: bir satır eklersin, dosyayı kapatırsın, iş biter. Asıl zorluk bir yıl sonra başlar. Aynı dosyaya iki süreç aynı anda yazmaya kalkar, biri yarıda çöker, bir rapor için tüm dosyanın taranması gerekir ve kimse "bir öğrencinin iki kez kayıtlı olamayacağını" dosyanın kendisine söyletemez. Bu sorunların her biri ayrı ayrı çözülebilir; ama hepsini birden, her uygulama için yeniden yazmak, veritabanı yönetim sistemlerinin (VTYS) var olma sebebidir.

Bu bölüm veritabanı kısmının ilk bölümüdür ve konusu **model**dir: veriyi nasıl anlatırsın, hangi kuralları veriye zorlarsın ve bu kuralları bir tasarıma nasıl çevirirsin. İlişkisel model, 1970'te E. F. Codd'un önerisiyle başladı ve bugün hâlâ en yaygın modeldir. Bu bölümde modelin mantığını, yani ilişki, anahtar, kısıt, cebir ve normalizasyonu anlatacağız. SQL'in sorgu tarafını (JOIN türleri, alt sorgular, pencere fonksiyonları, sorgu planları) **Bölüm 34'te** derinlemesine göreceğiz; bu bölümde SQL'i tasarımı gösterecek kadar kullanıyoruz.

Savunma sanayiinde veritabanı kararları çoğu zaman gözle görünmez. Bir İHA'nın uçuş kayıtları, bir radarın hedef geçmişi ya da bir sensör ağının telemetrisi, sonunda bir tabloya düşer. Yanlış tasarlanmış bir tablo, bir kaydın iki farklı yerde farklı değerle durmasına yol açar; bu da bir analizde yanlış sonuç, bir görev raporunda yanlış karar demektir. Yani "şema" bir iş kararıdır, sadece teknik bir ayrıntı değildir.

Mert'in projelerinde de bu sorun tanıdıktır. **EV Dashboard** sensör verisini zaman damgasıyla saklar; **Mert Studio Code** proje meta verisini (dosyalar, bağımlılıklar, derleme çıktıları) tutar. İkisinde de "aynı bilgi iki yerde durmasın" kuralı, ilk günden itibaren karşına çıkar. Bu bölümün sonunda bu iki sistem için bir şema önerebilecek ve neden o şemayı seçtiğini savunabileceksin.

Bölüm 28'de gördüğün iki kural burada yeniden karşına çıkacak. Birincisi, veriyi kalıcı yapmak için önce diske sırayla yazmak ve `fsync` ile garanti altına almak gerektiği. İkincisi, yarım kalmış bir güncellemenin tutarsız bir dosya bırakabileceği. Veritabanları bu iki kuralı bir **günlük (WAL)** ile birleştirir; bunu 33.13'te göreceğiz.

::: not
Bu bölümün kodları Python 3.12.10 ile yazıldı ve çalıştırıldı. Python'un `sqlite3` modülü bu makinede SQLite **3.49.1** sürümünü kullanıyor (`sqlite3.sqlite_version` ile doğrulandı). Bölümdeki SQLite davranışları bu sürüme göre ölçüldü; SQLite'ın dosya biçimi uzun süredir kararlıdır, ama sürüme özgü ayrıntıları belgesinden kontrol etmeyi alışkanlık hâline getir.
:::

## 33.1 Dosyada veri tutmanın sorunları

Bir dosyada veri tutmak, veriyi bayt dizisine çevirip bir yere yazmaktır. Bu, işletim sistemi açısından yeterlidir (Bölüm 28'de gördük); ama veri yönetimi açısından dört soruya cevap vermez.

**Eşzamanlılık.** İki süreç aynı kaydı aynı anda okuyup değiştirirse, sonuncu yazan öncekinin yazdığını sessizce siler. Bu, Bölüm 27'deki paylaşılan değişken yarışının bir veri sürümüdür. Dosya kilidi (Unix'te `flock`, Windows'ta `LockFileEx`) ile çözmek mümkündür, ama her uygulama kendi kilit kuralını yazarsa aralarındaki tutarlılık garanti edilemez.

**Tutarlılık.** Bir öğrencinin notu 0 ile 100 arasında olmalı; bir dersin kodu iki kez tanımlanmamalı; bir kayıt, var olmayan bir öğrenciye bağlanmamalı. Bu kuralların hiçbiri dosya biçiminde yoktur. Kuralı uygulayan kod yanlış yazılırsa veri kirlenir ve bunu sonradan fark etmek zordur.

**Sorgu.** "Bu dönemde 80'in üzerinde alan öğrencileri listele" sorusunu bir dosya ile cevaplamak için dosyanın tamamını okumak gerekir. Dosya büyüdükçe bu süre de büyür. Oysa doğru bir indeks, aynı soruyu tüm dosyayı taramadan cevaplayabilir (33.11).

**Çökme.** Yazma yarıda kesilirse dosya ne eski ne yeni durumdadır. Bölüm 28.8'deki atomik güncelleme kalıbı bu sorunu bir dosya için çözer; ama birden çok tabloyu aynı anda güncellemek gerektiğinde kalıbı her yerde yeniden kurmak gerekir.

Bu dört sorunun çözümü tek bir fikirde toplanır: veriyi bir **model** ile tanımla, kuralları bu modelin parçası yap ve bu kuralları veritabanı motorunun her işleminde kendisi uygulat. VTYS'nin işi budur. Model seçimi ise bu fikrin ilk ve en kalıcı kararıdır. Aşağıdaki tablo, bu bölümde ve sonraki bölümlerde karşılaşacağın kavramları özetler:

| Sorun | Dosyada | VTYS'de çözüm (bu bölümde) |
|---|---|---|
| Eşzamanlılık | Her uygulama kendi kilidini yazar | İşlem ve kilit yönetimi (33.14) |
| Tutarlılık | Kural kodda, dağınık | Bütünlük kısıtları (33.4) |
| Sorgu | Tam tarama | İndeks, sorgu planı (33.11, Bölüm 34) |
| Çökme | Elle atomik güncelleme | WAL ve kurtarma (33.13) |

## 33.2 İlişkisel model: ilişki, demet, nitelik, alan, şema

İlişkisel modelin temel fikri basittir: veri **ilişki (relation)** adı verilen tablolarda durur. Bir ilişki, bir *şema* (adlandırılmış nitelikler kümesi) ve bu şemaya uyan *demetler* (satırlar) kümesinden oluşur. Codd'un 1970 makalesi bu tanımı matematiksel olarak kurar; biz terimleri kendi dilimizle ve somut bir tablo üzerinden anlatacağız.

Aşağıdaki şekil, bir öğrenci tablosunun terimlerini gösterir. Terimler iki dünyadan gelir: matematikte ilişki–demet–nitelik, SQL'de tablo–satır–sütun. Mülakatta iki dili de bilmek gerekir.

![Şekil 33.1: İlişkisel terminoloji. Tablo (ilişki) bir şema ve bir demet kümesinden oluşur; sütunlar nitelikler, satırlar demetlerdir. Bir nitelik, izin verilen değerler kümesi olan bir alana bağlıdır.](gorseller/b33_terminoloji.png)

Şemayı bir cümleyle yazmanın standart biçimi budur: `ogrenci(no, ad, eposta, yas)`. Burada `ogrenci` ilişkinin adı, parantez içindekiler niteliklerdir. Her niteliğin bir **alanı** (domain) vardır: `yas` tam sayı, `ad` metin gibi. Alan, bir niteliğin alabileceği değerler kümesidir; SQL'de bunu veri tipi ile yaklaşık olarak ifade ederiz.

İlişkisel modelin iki katı kuralı vardır ve bu kurallar, dosyadan ayıran şeylerdir:

1. **Bir ilişki bir küme gibi davranır.** Aynı demet iki kez bulunamaz. Oysa SQL'de iki aynı satır eklenebilir; bu, SQL'in çoklu küme (bag) anlamını benimsemesinin bir sonucudur ve bunu 33.6'da cebir tarafında açıkça göreceğiz.
2. **Nitelikler sıralı değildir.** Sütunların yazılış sırası anlamı değiştirmez; bir demeti niteliğin adıyla okursun, konumuyla değil. Bu, kodunda `row[3]` yerine `row["yas"]` yazmanın matematiksel karşılığıdır.

Bu iki kural, sorguların bir **cebir** ile anlatılabilmesini sağlar (33.6). Sıra bağımsızlığı ise tablolar üzerinde optimizasyon yapmayı mümkün kılar: motor sütunları istediği sırada okuyabilir ya da yeniden düzenleyebilir.

Sık yapılan bir hata, dosya düşüncesiyle tablo tasarlamaktır: "bir satıra her şeyi koyarım, sonra ayrıştırırım". İlişkisel modelde ise tasarımın ilk adımı, *hangi gerçekler* (varlıklar ve aralarındaki ilişkiler) olduğunu ayırmaktır. Bunu 33.7'de ER modeliyle yapacağız; önce anahtarları görmek gerekir.

## 33.3 Anahtarlar: süper, aday, birincil, yabancı; doğal ve yapay

Anahtar, bir demeti diğerlerinden ayırt etmeye yarayan nitelik kümesidir. Anahtarlar yalnızca bir kolaylık değildir; veritabanının "aynı kayıt iki kez var" hatasını önlemesinin tek yoludur. Dört temel anahtar türü vardır.

**Süper anahtar (superkey).** Bir nitelik kümesi, ilişkideki hiçbir iki demetin aynı değerleri taşımamasını garanti ediyorsa süper anahtardır. Örneğin `ogrenci` tablosunda `no` bir süper anahtardır; `(no, ad)` de öyledir, ama gereksizdir.

**Aday anahtar (candidate key).** Süper anahtarların, *hiçbir alt kümesi de süper anahtar olmayan* olanlarıdır. Aday anahtarlar "minimal" süper anahtarlardır. Bir ilişkinin birden çok aday anahtarı olabilir; örneğin `eposta` benzersizse o da aday anahtardır.

**Birincil anahtar (primary key).** Aday anahtarlardan birinin seçilip tabloyu tanımlamak için kullanılmasıdır. Birincil anahtar değeri `NULL` olamaz; bu kural standarttır. SQLite ise tarihsel bir istisna taşır: `INTEGER PRIMARY KEY` dışındaki bir birincil anahtar `NULL` kabul eder, `NOT NULL` eklemezsen. Bu tuzağı 33.4'te deneyle göreceğiz. Bir tablo yalnızca bir birincil anahtar taşır.

**Yabancı anahtar (foreign key).** Bir tablodaki niteliğin, başka bir tablonun birincil (ya da benzersiz) anahtarındaki bir değeri göstermesi zorunluluğudur. `kayit.ogr_no` yabancı anahtarı, `ogrenci.no`'ya işaret eder. Böylece "var olmayan bir öğrenciye kayıt" yazılamaz. Şekil 33.2 bu ilişkiyi gösterir.

![Şekil 33.2: Birincil anahtar (PK) ve yabancı anahtar (FK). kayit.ogr_no, ogrenci.no'ya işaret eder; kayıt, var olmayan bir öğrenciyi gösteremez.](gorseller/b33_anahtar_fk.png)

Anahtar seçerken bir ikilem vardır. **Doğal anahtar**, gerçek dünyada zaten var olan bir bilgidir: TC kimlik numarası, bir dersin kodu, bir uçağın kuyruk numarası. **Yapay anahtar (surrogate key)** ise veritabanının ürettiği bir sayıdır: SQLite'ta `INTEGER PRIMARY KEY`, PostgreSQL'de `SERIAL` ya da `IDENTITY`. Doğal anahtar anlamlıdır ama zamanla değişebilir (bir kuyruk numarası yeniden atanabilir, bir öğrenci numarası düzeltilebilir). Yapay anahtar değişmez ve kısadır ama tek başına bir anlam taşımaz. Pratik kural: değişmesi muhtemel bir bilgiyi anahtar yapma; gerçekten değişmeyecek bir doğal anahtar yoksa yapay anahtar kullan ve doğal anahtarı `UNIQUE` ile koru.

Yabancı anahtar ile tablolar arasında bağ kurulur, bu da 33.4'teki bütünlük kurallarının kaynağıdır. Bir tablonun yabancı anahtarı, başka bir tablonun kaydını değiştirirken ya da silerken ne olacağını da tanımlar. Bu davranış `ON DELETE` seçeneğiyle belirlenir ve 33.4'te ayrıntılı olarak incelenecektir.

## 33.4 Bütünlük kısıtları: NOT NULL, UNIQUE, CHECK ve yabancı anahtar

Bir veritabanını "güvenilir" yapan şey, kötü veriyi reddetmesidir. Bütünlük kısıtı (integrity constraint), bir veri değişikliği tamamlanmadan önce motorun kontrol ettiği bir kuraldır. Kısıt ihlal edilirse işlem hata verir ve veri değişmez. Kuralı kodda yazmak ile kısıtı şemaya koymak arasındaki fark, bir sonraki uygulamanın da aynı kuralı hatırlamak zorunda olup olmadığıdır: şemadaki kısıt, her uygulama için geçerlidir.

Kısıtları dört sınıfta toplamak işe yarar. **Alan (domain) kısıtı** bir niteliğin değer kümesini sınırlar: `yas` bir tam sayıdır ve 15 ile 80 arasında olmalıdır. **Varlık (entity) kısıtı** birincil anahtarın tekil ve dolu olmasını ister. **Başvuru (referential) kısıtı** yabancı anahtarın var olan bir değere işaret etmesini ister. **Kullanıcı tanımlı kısıtlar** iş kurallarını yazar; SQL'de bunlar `CHECK` ve `UNIQUE` ile ifade edilir.

Dört kısıtın SQL karşılıkları şöyledir:

- `NOT NULL`: niteliğe `NULL` yazılamaz. Bir öğrencinin adı olmadan kaydı anlamsızdır.
- `UNIQUE`: bir niteliğin ya da niteliklerin bileşiminin değerleri tekrar edemez. Bir e-posta adresi iki öğrenciye ait olamaz.
- `CHECK (koşul)`: her satır bu koşulu sağlamalıdır. Koşul yalnızca aynı satırın değerlerine bakabilir.
- `REFERENCES tablo(nitelik)`: yabancı anahtar. Bir kayıt, gösterdiği satır yoksa eklenemez.

**Yabancı anahtar ve silme.** Asıl tartışma, bağlı bir satır silinmek istendiğinde başlar. Ana satırı silmenin iki sonucu olabilir: bağlı satırlar da silinir ya da silme engellenir. Hangisinin olacağı `ON DELETE` ile seçilir. Beş seçenek vardır: `CASCADE` bağlı satırları siler; `RESTRICT` bağlı satır varsa silmeyi hemen reddeder; `NO ACTION` (varsayılan) da reddeder, ama kontrolü ifade sonuna erteler; `SET NULL` yabancı anahtarı `NULL` yapar; `SET DEFAULT` varsayılan değere çeker. Hangisini seçeceğin bir iş kuralıdır. Bir öğrenci silindiğinde notları da gitmeli mi? Genellikle hayır; bu yüzden notlar için silmeyi engelleyen bir seçenek tercih edilir.

**SQLite'ta bir tuzak.** SQLite, geriye uyumluluk gereği yabancı anahtar kontrollerini varsayılan olarak **kapalı** başlatır. Kapalıyken yabancı anahtar tanımlamak tek başına bir şey yapmaz; her bağlantıda `PRAGMA foreign_keys = ON` komutunu vermen gerekir. Aşağıdaki program bu tuzağı da gösterir: aynı şema iki bağlantıda çalıştırılır, biri açık, diğeri kapalı.

**SQLite'ın tip gevşekliği.** Bir başka tuzak da tiplerdir. SQLite'ta `INTEGER` olarak tanımlı bir sütuna metin yazılabilir; motor değeri olduğu gibi saklar. Bunu sınamak için `STRICT` tablo seçeneği vardır (SQLite 3.37.0 ve sonrası; genel bilgi). Bu bölümün kodu tip sınamasına girmiyor, ama tasarımında bu gevşekliğin farkında olmalısın.

Aşağıdaki program üç tablo kurar: `ogrenci`, `kayit` ve `tez`. Her kısıtı kasıtlı olarak ihlal eder ve SQLite'ın verdiği hatayı yazdırır. Son bölümde silme davranışlarını (CASCADE ve RESTRICT) deneriz. Program 62 satırdır; önce kurulumu, sonra denemeleri okuyacağız.

```python
# b33_1_kisitlar.py: NOT NULL, UNIQUE, CHECK, yabancı anahtar
import sqlite3


def dene(bag, sql, args=()):
    try:
        bag.execute(sql, args)
        return "tamam"
    except sqlite3.IntegrityError as e:
        return "HATA: " + str(e)


SEMA = """
CREATE TABLE ogrenci(
  no     INTEGER PRIMARY KEY,
  ad     TEXT NOT NULL,
  eposta TEXT UNIQUE,
  yas    INTEGER CHECK (yas BETWEEN 15 AND 80));
CREATE TABLE kayit(
  id     INTEGER PRIMARY KEY,
  ogr_no INTEGER NOT NULL REFERENCES ogrenci(no)
         ON DELETE CASCADE,
  ders   TEXT NOT NULL,
  UNIQUE (ogr_no, ders));
CREATE TABLE tez(
  id     INTEGER PRIMARY KEY,
  ogr_no INTEGER REFERENCES ogrenci(no)
         ON DELETE RESTRICT);
"""
```

Programın ikinci yarısında, ihlal denemeleri ve silme davranışı vardır. Kodun geri kalanı şöyle:

```python
print("sqlite", sqlite3.sqlite_version)
c = sqlite3.connect(":memory:")
fk = c.execute("PRAGMA foreign_keys").fetchone()[0]
print("foreign_keys (varsayilan):", fk)
c.execute("PRAGMA foreign_keys = ON")
c.executescript(SEMA)
c.execute("INSERT INTO ogrenci VALUES (1,'Ayşe','a@x.com',21)")
c.execute("INSERT INTO ogrenci VALUES (2,'Mert','m@x.com',20)")
c.execute("INSERT INTO kayit(ogr_no,ders) VALUES (1,'VT')")
c.execute("INSERT INTO kayit(ogr_no,ders) VALUES (1,'OS')")
c.execute("INSERT INTO tez(ogr_no) VALUES (2)")

ekle = "INSERT INTO ogrenci VALUES (%s)"
print("NOT NULL :", dene(c, ekle % "3,NULL,'b',20"))
print("UNIQUE   :", dene(c, ekle % "3,'Ali','a@x.com',20"))
print("CHECK    :", dene(c, ekle % "4,'Veli','v@x',10"))
kay = "INSERT INTO kayit(ogr_no,ders) VALUES (%s)"
print("FK yok   :", dene(c, kay % "99,'AG'"))
print("UNIQUE(c):", dene(c, kay % "1,'VT'"))

# Aynı yabancı anahtar, FK kapalıyken sessizce kabul edilir.
d = sqlite3.connect(":memory:")
d.executescript(SEMA)
print("FK kapali:", dene(d, kay % "99,'AG'"))

print("--- silme davranisi ---")
c.execute("DELETE FROM ogrenci WHERE no = 1")
n = c.execute("SELECT COUNT(*) FROM kayit").fetchone()[0]
print("kayit satiri (CASCADE):", n)
print("silme (RESTRICT):",
      dene(c, "DELETE FROM ogrenci WHERE no = 2"))
```

Çıktı, her kısıtın gerçekten uygulandığını ve FK'nın kapalıyken nasıl sessizce geçtiğini gösterir:

```term
$ python b33_1_kisitlar.py
sqlite 3.49.1
foreign_keys (varsayilan): 0
NOT NULL : HATA: NOT NULL constraint failed: ogrenci.ad
UNIQUE   : HATA: UNIQUE constraint failed: ogrenci.eposta
CHECK    : HATA: CHECK constraint failed: yas BETWEEN 15 AND 80
FK yok   : HATA: FOREIGN KEY constraint failed
UNIQUE(c): HATA: UNIQUE constraint failed: kayit.ogr_no, kayit.ders
FK kapali: tamam
--- silme davranisi ---
kayit satiri (CASCADE): 0
silme (RESTRICT): HATA: FOREIGN KEY constraint failed
```

Çıktıyı okuyalım. Üç satır (`NOT NULL`, `UNIQUE`, `CHECK`) doğrudan şema kuralıdır ve motor hatayı adıyla söyler. `FK yok` satırı, `kayit` tablosuna var olmayan bir öğrenci numarası yazılamadığını gösterir. Aynı yazma FK kapalı bir bağlantıda `tamam` döner: veri kirlenmiştir ve bu, hiçbir hata mesajı olmadan olur. Silme bölümünde `CASCADE` ile öğrenci 1 silinince, ona bağlı iki kayıt da gitti (`kayit satiri ... 0`). `RESTRICT` ile tanımlanan `tez` tablosunda bağlı bir satır bulunan öğrenci 2 silinemedi.

::: ipucu
Yabancı anahtar kontrolünü her bağlantıda açmayı unutma. Bir ORM ya da sürücü bu ayarı varsayılan olarak kapalı bırakabilir; sorun, veri bozulduktan sonra fark edilir. Bağlantı kurulduğu anda `PRAGMA foreign_keys` değerini sorgulamak, kurulum testinin parçası olmalıdır.
:::

## 33.5 NULL ve üç değerli mantık

`NULL`, bir değerin **bilinmediğini** gösterir; `0` ya da boş metin gibi bir değer değildir. Bu fark, SQL'in en çok hata üreten yanıdır. Boolean mantığın iki değeri (DOĞRU, YANLIŞ) vardır; SQL'de bir koşul üç değerden birine değerlendirilir: DOĞRU, YANLIŞ ya da BİLİNMİYOR (UNKNOWN). `NULL = NULL` ifadesi DOĞRU değil, BİLİNMİYOR'dur. İki bilinmeyen değerin eşit olup olmadığını bilmiyorsun; bu yüzden bilinmiyorsa eşit olduklarını da söyleyemezsin.

Üç değerli mantığın kuralları, klasik iki değerli mantıktan farklı değildir; yalnızca BİLİNMİYOR değerini içerir. Aşağıdaki tablo bunu özetler:

| A | B | A AND B | A OR B |
|---|---|---|---|
| DOĞRU | BİLİNMİYOR | BİLİNMİYOR | DOĞRU |
| YANLIŞ | BİLİNMİYOR | YANLIŞ | BİLİNMİYOR |
| BİLİNMİYOR | BİLİNMİYOR | BİLİNMİYOR | BİLİNMİYOR |

`WHERE` yalnızca DOĞRU olan satırları alır. Bu, bilinmeyen koşulların da sonucu gizlediği anlamına gelir. Aşağıdaki program bu kuralları SQLite'ta sınar ve üç tuzağı gösterir: `= NULL` ile arama, `NOT IN` içinde `NULL` ve `COUNT(*)` ile `COUNT(x)` arasındaki fark.

```python
# b33_2_null.py: NULL ve üç değerli mantık
import sqlite3

c = sqlite3.connect(":memory:")


def q(ifade):
    return c.execute("SELECT " + ifade).fetchone()[0]


def goster(v):
    if v is None:
        return "UNKNOWN"
    return "DOĞRU" if v else "YANLIŞ"


print("sqlite", sqlite3.sqlite_version)
print("NULL = NULL   ->", goster(q("NULL = NULL")))
print("NULL IS NULL  ->", goster(q("NULL IS NULL")))
print()
print("DOĞRU AND ?   ->", goster(q("1 AND NULL")))
print("YANLIŞ AND ?  ->", goster(q("0 AND NULL")))
print("DOĞRU OR ?    ->", goster(q("1 OR NULL")))
print("YANLIŞ OR ?   ->", goster(q("0 OR NULL")))
print("NOT ?         ->", goster(q("NOT NULL")))
```

Programın ikinci yarısı tabloyu kurar ve tuzakları dener:

```python
print()

c.execute("CREATE TABLE n(x INTEGER)")
c.executemany("INSERT INTO n VALUES (?)", [(1,), (2,), (None,)])


def say(sorgu):
    return c.execute(sorgu).fetchone()[0]


print("x = NULL satir   :",
      say("SELECT COUNT(*) FROM n WHERE x = NULL"))
print("x IS NULL satir  :",
      say("SELECT COUNT(*) FROM n WHERE x IS NULL"))
print("x <> 1 satir     :",
      say("SELECT COUNT(*) FROM n WHERE x <> 1"))
print("COUNT(*)         :", say("SELECT COUNT(*) FROM n"))
print("COUNT(x)         :", say("SELECT COUNT(x) FROM n"))
print("AVG(x)           :", say("SELECT AVG(x) FROM n"))
print()
# Tuzak: NOT IN listesinde NULL varsa sonuç bilinmiyor olur.
print("3 NOT IN (1,2)      ->", goster(q("3 NOT IN (1, 2)")))
print("3 NOT IN (1,2,NULL) ->", goster(q("3 NOT IN (1, 2, NULL)")))
print("NULL'lu alt sorgu satir:",
      say("SELECT COUNT(*) FROM n "
          "WHERE 3 NOT IN (SELECT x FROM n)"))
```

Çıktı:

```term
$ python b33_2_null.py
sqlite 3.49.1
NULL = NULL   -> UNKNOWN
NULL IS NULL  -> DOĞRU

DOĞRU AND ?   -> UNKNOWN
YANLIŞ AND ?  -> YANLIŞ
DOĞRU OR ?    -> DOĞRU
YANLIŞ OR ?   -> UNKNOWN
NOT ?         -> UNKNOWN

x = NULL satir   : 0
x IS NULL satir  : 1
x <> 1 satir     : 1
COUNT(*)         : 3
COUNT(x)         : 2
AVG(x)           : 1.5

3 NOT IN (1,2)      -> DOĞRU
3 NOT IN (1,2,NULL) -> UNKNOWN
NULL'lu alt sorgu satir: 0
```

Çıktının iki noktası özellikle önemlidir. Birincisi, `x = NULL` ile arayan sorgu hiçbir satır döndürmez; `x IS NULL` ise bir satır döndürür. Bu yüzden `NULL` aramak için `IS NULL` kullanılır. İkincisi, `3 NOT IN (1, 2, NULL)` BİLİNMİYOR döner; bu da `WHERE 3 NOT IN (SELECT x FROM n)` sorgusunun hiçbir satır döndürmemesine yol açar. Alt sorgu `NULL` içerdiğinde `NOT IN` her zaman bilinmez sonuç verir. Bunu bilmeyen biri, "şu listede olmayanları bul" sorusunu yanlış cevaplar. Aynı sorunun güvenli karşılığı `NOT EXISTS` ile yazılan sorgudur; bunu Bölüm 34'te göreceksin.

::: dikkat
`NULL` ile yapılan karşılaştırmalar sessizdir: hata vermez, sadece yanlış satır sayısı döndürür. Bu yüzden kod incelemesinde her `= NULL` ve her `NOT IN (SELECT ...)` ifadesini şüpheli say.
:::

## 33.6 İlişkisel cebir: seçme, izdüşüm, birleşim, fark, çarpım, birleştirme

Bir sorgu, SQL yazmadan önce bir matematiksel dille ifade edilebilir. Bu dile **ilişkisel cebir** denir ve üç nedenle önemlidir. Birincisi, SQL'in her cümlesinin tam olarak neye karşılık geldiğini gösterir. İkincisi, sorgu optimizasyonunun temelidir: motor sorguyu cebir ifadelerine çevirir, eşdeğer ama daha ucuz ifadeler arar ve seçer (genel bilgi; ayrıntısı Bölüm 34'te). Üçüncüsü, bir sorgunun sonucunu kâğıt üzerinde doğrulamanı sağlar.

Altı temel işlem vardır; yedinci olan yeniden adlandırma ise bunları birleştirmek için gerekir:

| İşlem | Sembol | SQL karşılığı | Anlamı |
|---|---|---|---|
| Seçme | σ | `WHERE` | Koşulu sağlayan satırlar |
| İzdüşüm | π | `SELECT sütunlar` (+ `DISTINCT`) | Seçilen sütunlar, yinelenensiz |
| Birleşim | ∪ | `UNION` | İki ilişkinin satırları |
| Fark | − | `EXCEPT` | Birincide olup ikincide olmayan |
| Kartezyen çarpım | × | `CROSS JOIN` | Her satır her satırla |
| Birleştirme | ⋈ | `JOIN` (doğal) | Ortak nitelikte eşleşenler |
| Yeniden adlandırma | ρ | `AS` | Nitelik ya da ilişki adı |

Şekil 33.3, bu işlemleri bir bakışta gösterir.

![Şekil 33.3: İlişkisel cebir işlemleri. Her işlem bir ya da iki ilişki alır ve bir ilişki döndürür; bu kapanma özelliği, işlemlerin üst üste yazılmasına izin verir.](gorseller/b33_cebir.png)

Cebirin en önemli özelliği **kapanmadır**: her işlem bir ilişki alır ve bir ilişki döndürür. Bu sayede `π_ad(σ_yas>20(ogrenci))` gibi bir ifade, iç içe işlemlerin tek bir sonucudur. Ayrıca cebir küme anlamıyla çalışır: sonuçta yinelenen demet olmaz. SQL ise çoklu küme (bag) anlamıyla çalışır; bu yüzden cebirdeki `π` karşılığı `DISTINCT` ister. Bu fark, karşılaştırma yaparken en çok hata yapılan yerdir.

Cebirin kendisini anlamak için onu sıfırdan yazmak en iyi yoldur. Aşağıdaki program bir `Iliski` sınıfı ile altı işlemi uygular. Her ilişki, nitelik adlarının bir demeti (tuple) ve demetlerin bir listesidir; yinelenen demet eklenmez. İşlemler saf fonksiyonlardır: girdi ilişkiyi değiştirmez, yeni bir ilişki döndürür. Bu, sorgu optimizasyonunda kullanılan dönüşümlerin temel koşuludur.

```python
# b33_3_cebir.py: küçük bir ilişkisel cebir motoru
import random
import sqlite3


class Iliski:
    """Nitelikler + demetler. Küme anlamı: yinelenen yok."""

    def __init__(self, nitelikler, demetler=()):
        self.n = tuple(nitelikler)
        self.d = []
        for t in demetler:
            t = tuple(t)
            assert len(t) == len(self.n)
            if t not in self.d:
                self.d.append(t)

    def sut(self, ad):
        return self.n.index(ad)

    def satir(self, t):
        return dict(zip(self.n, t))
```

İlk iki ayrı fonksiyon (`sigma`, `pi`) seçme ve izdüşümü yapar. Koşul, bir sözlük alan bir fonksiyondur; böylece `lambda s: s["og"] > 4` gibi ifadeler yazılabilir.

```python
def sigma(r, kosul):
    """Seçme: koşulu sağlayan demetleri tut."""
    return Iliski(r.n, [t for t in r.d if kosul(r.satir(t))])


def pi(r, nitelikler):
    """İzdüşüm: istenen sütunlar, yinelenenler atılır."""
    idx = [r.sut(a) for a in nitelikler]
    return Iliski(nitelikler, [tuple(t[i] for i in idx) for t in r.d])


def birlesim(r, s):
    assert r.n == s.n
    return Iliski(r.n, r.d + s.d)


def fark(r, s):
    assert r.n == s.n
    kume = set(s.d)
    return Iliski(r.n, [t for t in r.d if t not in kume])


def kartezyen(r, s):
    assert not set(r.n) & set(s.n)
    return Iliski(r.n + s.n, [t + u for t in r.d for u in s.d])
```

Birleşim, fark ve kartezyen çarpım iki ilişki alır. Doğal birleştirme (`dogal_birlestirme`), ortak nitelikleri eşleştirir; bu, SQL'deki `NATURAL JOIN`'in birebir karşılığıdır. Yeniden adlandırma sadece nitelik adını değiştirir; kartezyen çarpımda iki ilişkinin adlarının çakışmaması gerektiği için bu gereklidir.

```python
def dogal_birlestirme(r, s):
    """Ortak niteliklerde eşit olan demet çiftleri."""
    ortak = [a for a in r.n if a in s.n]
    ek = [a for a in s.n if a not in r.n]
    sonuc = []
    for t in r.d:
        for u in s.d:
            if all(t[r.sut(a)] == u[s.sut(a)] for a in ortak):
                sonuc.append(t + tuple(u[s.sut(a)] for a in ek))
    return Iliski(r.n + tuple(ek), sonuc)


def yeniden_adlandir(r, eski, yeni):
    return Iliski(tuple(yeni if a == eski else a for a in r.n),
                  r.d)
```

Programın küçük bir örnek bölümü vardır. Burada yinelenen demetin eklenmediğini ve doğal birleştirmenin nasıl sonuç verdiğini görürüz.

```python
# ---- Küçük örnek ----
ogr = Iliski(("no", "ad"), [(1, "Ayşe"), (2, "Mert"), (1, "Ayşe")])
print("ogr (yinelenen atildi):", ogr.d)
print("pi(ad):", pi(ogr, ["ad"]).d)
kay = Iliski(("no", "ders"), [(1, "VT"), (1, "OS"), (2, "VT")])
print("ogr |x| kay:", dogal_birlestirme(ogr, kay).d)
```

Son bölüm, iki rastgele ilişki üretir (sabit tohum 33), bunları SQLite'a yükler ve her cebir işleminin sonucunu SQL'in kendi işlemiyle karşılaştırır. Bu, cebir motorumuzun doğruluğunu ölçen bir testtir.

```python
# ---- Rastgele verilerle SQLite karşılaştırması (tohum 33) ----
rnd = random.Random(33)
R = Iliski(("og", "ders"), [(rnd.randint(1, 8), rnd.choice("ABCD"))
                            for _ in range(30)])
R2 = Iliski(("og", "ders"), [(rnd.randint(1, 8), rnd.choice("ABCD"))
                             for _ in range(30)])
S = Iliski(("ders", "hoca"), [(rnd.choice("ABCDE"),
                               rnd.choice("XYZ")) for _ in range(12)])
db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE R(og, ders)")
db.execute("CREATE TABLE R2(og, ders)")
db.execute("CREATE TABLE S(ders, hoca)")
db.executemany("INSERT INTO R VALUES (?,?)", R.d)
db.executemany("INSERT INTO R2 VALUES (?,?)", R2.d)
db.executemany("INSERT INTO S VALUES (?,?)", S.d)


def sql(sorgu):
    return db.execute(sorgu).fetchall()


def esit(a, b):
    return sorted(a.d) == sorted(set(b))
```

Test kısmının son satırları, SQL sonuçlarını Python kümesine çevirip karşılaştırır:

```python
print()
print("sigma og>4 :", esit(sigma(R, lambda s: s["og"] > 4),
      sql("SELECT og, ders FROM R WHERE og > 4")))
print("pi ders    :", esit(pi(R, ["ders"]),
      sql("SELECT ders FROM R")))
print("R |x| S    :", esit(dogal_birlestirme(R, S),
      sql("SELECT og, ders, hoca FROM R NATURAL JOIN S")))
print("R u R2     :", esit(birlesim(R, R2),
      sql("SELECT og, ders FROM R UNION "
          "SELECT og, ders FROM R2")))
print("R - R2     :", esit(fark(R, R2),
      sql("SELECT og, ders FROM R EXCEPT "
          "SELECT og, ders FROM R2")))
kart = kartezyen(yeniden_adlandir(R, "ders", "rd"), S)
print("R x S      :", len(kart.d) == sql(
    "SELECT COUNT(*) FROM (SELECT DISTINCT og, ders FROM R) "
    "CROSS JOIN (SELECT DISTINCT ders, hoca FROM S)")[0][0])
print("sqlite", sqlite3.sqlite_version)
```

Çıktı:

```term
$ python b33_3_cebir.py
ogr (yinelenen atildi): [(1, 'Ayşe'), (2, 'Mert')]
pi(ad): [('Ayşe',), ('Mert',)]
ogr |x| kay: [(1, 'Ayşe', 'VT'), (1, 'Ayşe', 'OS'), (2, 'Mert', 'VT')]

sigma og>4 : True
pi ders    : True
R |x| S    : True
R u R2     : True
R - R2     : True
R x S      : True
sqlite 3.49.1
```

Çıktıdaki `True` değerleri, altı işlemin altısının da SQLite ile aynı kümeyi ürettiğini gösterir. Küçük örnekte `ogr` ilişkisinin iki satırı olduğunu görürsün: `(1, "Ayşe")` iki kez girildi ama tekrar eklenmedi. Doğal birleştirme `ogr ⋈ kay` sonucunda üç demet verir; bunlar ortak `no` niteliğinde eşleşen çiftlerdir.

Bu motoru yazarken üç şey fark edilmeli. Birincisi, `R × S` testinde satır sayısı `|R| · |S|`dir; yani kartezyen çarpım, büyük tablolarda hızla patlar. Bu yüzden gerçek sorgularda ×'ten çok ⋈ kullanılır ve motor birleştirme sırasını seçmeye çalışır (Bölüm 34). İkincisi, `pi` işlemi yinelenenleri atar; bu, SQL'de `SELECT DISTINCT` yazmamanın neden farklı sonuç verebileceğini açıklar. Üçüncüsü, bizim `dogal_birlestirme` fonksiyonu iç içe döngü kullanır ve `O(|R| · |S|)` çalışır; veritabanı motorları bunun yerine indeks ya da karma tabloyla eşleştirme yapar. Bu farkı 33.11'de indekslerle, Bölüm 34'te birleştirme algoritmalarıyla göreceksin.

::: baglanti
Cebirdeki birleştirmenin bir yarısı, Bölüm 9'daki karma tablo fikrine dayanır: iki ilişkinin ortak niteliklerini bir karma tabloya koyarak eşleştirme `O(n + m)` ortalama süreyle yapılabilir. Bu, Bölüm 9'da gördüğün "anahtara göre doğrudan erişim" fikridir; veritabanında aynı fikir indeks olarak yaşar.
:::

## 33.7 ER modelleme: varlık, ilişki, kardinalite ve zayıf varlık

Tabloları yazmaya başlamadan önce gerçek dünyayı çizmek daha güvenlidir. **Varlık-ilişki (ER, entity-relationship)** modeli, Peter Chen'in 1976'da önerdiği bir çizim dilidir (genel bilgi). Amacı, bir sistemde hangi *şeylerin* (varlıkların), onların hangi *özelliklerinin* (niteliklerin) ve aralarında hangi *bağların* (ilişkilerin) olduğunu, SQL'e geçmeden netleştirmektir.

Dört kavram yeter. **Varlık**, ayırt edilebilen bir şeydir: bir öğrenci, bir ders, bir uçuş. **Nitelik**, varlığın bir özelliğidir: `ad`, `bölüm`. Anahtar nitelik, varlığı tekil kılan niteliktir (birincil anahtar adayı). **İlişki**, iki ya da daha fazla varlığı bağlar: "öğrenci *alır* ders". **Kardinalite**, bir ilişkinin her tarafından kaç tane varlığın bağlanabileceğini söyler.

Kardinalite üç biçimde olur:

- **1:1**: Bir öğrenci en çok bir dolap anahtarına sahiptir ve bir dolap anahtarı en çok bir öğrenciye aittir.
- **1:N**: Bir danışman birçok öğrenciye danışmanlık yapar; her öğrencinin en çok bir danışmanı vardır.
- **N:M**: Bir öğrenci birçok ders alır, bir ders birçok öğrenciye açılır.

Bu üçü, tabloya dönüşümde farklı davranışlar gerektirir ve en sık yapılan tasarım hatası N:M ilişkisini tek bir tabloda sıkıştırmaktır. Aşağıdaki şekil öğrenci–ders örneğini gösterir: "alır" ilişkisi N:M'dir ve aldığı notu ilişkinin kendi niteliği olarak tutar.

![Şekil 33.4: Öğrenci–ders ER diyagramı. "Alır" ilişkisi N:M'dir; not, ne öğrenciye ne derse aittir, ikisinin ilişkisine aittir ve ilişkinin niteliği olarak çizilir.](gorseller/b33_er_diyagrami.png)

Şekildeki not, önemli bir ayrımı gösterir: bir nitelik, ilişkinin kendisine aitse ilişkiye bağlanır. "Not" bir öğrencinin özelliği değildir (aynı öğrencinin her dersteki notu farklıdır) ve bir dersin özelliği de değildir (aynı dersin her öğrencide notu farklıdır). İkisinin birleşimine aittir.

**Zayıf varlık (weak entity)** kendi başına tekil olamayan varlıktır; yalnızca bir sahip varlığa bağlı olarak anlam kazanır. Bir İHA görev planındaki **rota noktası** (waypoint) buna iyi bir örnektir: "3. nokta" tek başına anlamsızdır; hangi görevin üçüncü noktası olduğunu bilmek gerekir. Zayıf varlığın anahtarı, sahibin anahtarı ile kısmi bir anahtarın (burada sıra numarası) bileşimidir.

### ER'den şemaya dönüşüm

Bir ER diyagramını tabloya çevirmek, mekanik ama dikkat gerektiren bir işlemdir. Dönüşüm kuralları şöyle özetlenebilir:

1. Her güçlü varlık bir tablo olur; anahtar niteliği birincil anahtar olur.
2. 1:N ilişkisinde, "N" tarafındaki tabloya, "1" tarafının anahtarını taşıyan bir yabancı anahtar eklenir.
3. N:M ilişkisi için bir **ara (köprü) tablosu** açılır. İki yabancı anahtar, ara tablonun bileşik birincil anahtarını oluşturur; ilişkinin nitelikleri (ör. not) ara tabloya girer.
4. 1:1 ilişkisinde yabancı anahtar, iki taraftan birine konur ve `UNIQUE` ile tekil tutulur.
5. Zayıf varlığın tablosunun birincil anahtarı, sahibin anahtarını ve kısmi anahtarı içerir; sahip silinince zayıf varlık da silinir (`ON DELETE CASCADE` genellikle budur).
6. Çok değerli bir nitelik (bir öğrencinin birden çok telefonu gibi) ayrı bir tabloya taşınır.

Öğrenci–ders örneği için bu kurallar şu şemayı verir:

```sql
CREATE TABLE ogrenci (
  no  INTEGER PRIMARY KEY,
  ad  TEXT NOT NULL,
  bolum TEXT NOT NULL
);
CREATE TABLE ders (
  kod TEXT PRIMARY KEY,
  ad  TEXT NOT NULL
);
CREATE TABLE notu (                 -- N:M ara tablosu
  ogr_no   INTEGER REFERENCES ogrenci(no) ON DELETE CASCADE,
  ders_kod TEXT    REFERENCES ders(kod)   ON DELETE CASCADE,
  puan     INTEGER CHECK (puan BETWEEN 0 AND 100),
  PRIMARY KEY (ogr_no, ders_kod)
);
```

Bu şemada `notu` tablosunun bileşik birincil anahtarı, bir öğrencinin aynı dersten iki kez notu olmasını engeller. Şemanın gerekçesini Örnek 1'de adım adım kuracağız.

## 33.8 Fonksiyonel bağımlılıklar, Armstrong kuralları ve kapanış

Normalizasyonu anlamak için bir kavram daha gerekir: **fonksiyonel bağımlılık (FD)**. `X → Y` yazmak, şu anlama gelir: aynı `X` değerine sahip iki satır, `Y` değerlerinin de aynı olmasını gerektirir. Yani `X`, `Y`'yi *belirler*. Örneğin `ogr_no → ogr_ad` yazmak, bir öğrenci numarasının tek bir öğrenci adına karşılık geldiğini söyler.

FD'ler bir gerçektir, veriden çıkarılmaz; tasarımcı bunları iş kurallarından bilir. Veriye bakarak bir FD'yi *kanıtlayamazsın*, sadece *çürütebilirsin*. Bir FD'nin veride tutması, onun doğru olduğu anlamına gelmez; bu yüzden FD'leri iş bilgisinden yazmak gerekir.

Verilmiş bir FD kümesinden yeni FD'ler türetilebilir. Bunun kuralları **Armstrong aksiyomları** adını taşır ve üç temel kuraldan oluşur:

- **Yansıma:** `Y ⊆ X` ise `X → Y`. (Bir şey kendi parçasını belirler.)
- **Artırma:** `X → Y` ise `XZ → YZ`. (İki tarafa aynı şey eklenirse bağlılık korunur.)
- **Geçişlilik:** `X → Y` ve `Y → Z` ise `X → Z`.

Bu üçü hem sağlam (türetilen her FD gerçekten geçerlidir) hem tamdır (doğru olan her FD türetilebilir). Birleşim, ayrıştırma ve sözde geçişlilik gibi kurallar bunlardan çıkar. Bu bölüm için önemli olan araç **kapanış (closure)**tur. `X+`, `X`'ten FD kümesiyle türetilebilen tüm niteliklerin kümesidir. Hesabı basittir: `X` ile başla; sol tarafı `X+`'ta olan her FD'nin sağ tarafını ekle; ekleme olmayana kadar tekrarla.

Kapanış iki işe yarar. Birincisi, `X`'in bir **süper anahtar** olup olmadığını söyler: `X+` tüm şemayı kapsıyorsa `X` süper anahtardır. İkincisi, bir FD'nin kümeden türetilip türetilmediğini sınamak için kullanılır: `X → Y` türetilebilir mi? `Y ⊆ X+` ise evet.

Bir örnek üzerinde görelim. Şema `R(A, B, C, D, E, G)` olsun ve bağımlılıklar şunlar olsun: `AB → C`, `C → A`, `BC → D`, `ACD → B`, `D → EG`, `BE → C`, `CG → BD`, `CE → AG`. Bu küme, FD kitaplarında sık kullanılan bir örnektir; burada tek amacı, kapanış ve aday anahtar hesabını gösterecek kadar zengin olmasıdır. Aşağıdaki program kapanışı, süper anahtarları, aday anahtarları ve BCNF ihlallerini hesaplar. Aday anahtarları, tüm alt kümeleri deneyerek (kaba kuvvet) bulur; bu, algoritmanın doğruluğunu bağımsız bir yolla sınamak için yeterlidir.

```python
# b33_4_fd.py: FD kapanışı, aday anahtarlar, BCNF ihlali
from itertools import combinations


def fd(sol, sag):
    """'AB' -> 'C' biçiminde bir bağımlılık."""
    return (frozenset(sol), frozenset(sag))


def kapanis(X, F):
    """X+: X'ten Armstrong kurallarıyla türeyenler."""
    sonuc = set(X)
    degisti = True
    while degisti:
        degisti = False
        for sol, sag in F:
            if sol <= sonuc and not sag <= sonuc:
                sonuc |= sag
                degisti = True
    return frozenset(sonuc)


def altkumeler(R):
    R = sorted(R)
    for k in range(len(R) + 1):
        for c in combinations(R, k):
            yield frozenset(c)


def aday_anahtarlar(R, F):
    """Süper anahtarlardan kendisinden küçüğü olmayanlar."""
    R = frozenset(R)
    sup = [X for X in altkumeler(R) if kapanis(X, F) == R]
    return [X for X in sup if not any(Y < X for Y in sup)]
```

Programın geri kalanı, yani BCNF ihlallerini bulan fonksiyon ve örnek kısmı şöyledir:

```python
def bcnf_ihlalleri(R, F):
    """X+, R'nin tamamı değilse ve X'in dışına taşıyorsa ihlal."""
    R = frozenset(R)
    ihlal = []
    for X in altkumeler(R):
        Xp = kapanis(X, F) & R
        if Xp - X and Xp != R:
            ihlal.append((sorted(X), sorted(Xp - X)))
    return ihlal


if __name__ == "__main__":
    R = "ABCDEG"
    F = [fd("AB", "C"), fd("C", "A"), fd("BC", "D"),
         fd("ACD", "B"), fd("D", "EG"), fd("BE", "C"),
         fd("CG", "BD"), fd("CE", "AG")]
    print("{B,D}+ =", "".join(sorted(kapanis("BD", F))))
    print("{A}+   =", "".join(sorted(kapanis("A", F))))
    anah = aday_anahtarlar(R, F)
    print("aday anahtarlar:", ["".join(sorted(k)) for k in anah])
    ih = bcnf_ihlalleri(R, F)
    print("BCNF ihlal sayisi:", len(ih))
    print("ilk 3 ihlal:")
```

Çıktı:

```term
$ python b33_4_fd.py
{B,D}+ = ABCDEG
{A}+   = A
aday anahtarlar: ['AB', 'BC', 'BD', 'BE', 'CD', 'CE', 'CG']
BCNF ihlal sayisi: 7
ilk 3 ihlal:
  (['C'], ['A'])
  (['D'], ['E', 'G'])
  (['A', 'D'], ['E', 'G'])
```

`{B, D}+ = ABCDEG` sonucu, `BD`'nin bir süper anahtar olduğunu gösterir. Şekil 33.5 bu hesabı adım adım izler: `{B, D}` ile başlanır; `D → EG` ile `E` ve `G` eklenir; `BE → C` ile `C` eklenir; `CE → AG` ile `A` eklenir ve tüm şema kapsanır.

![Şekil 33.5: {B, D}+ kapanış izi. Dolu kutular kümeye giren nitelikleri gösterir; her adım, o adımda kullanılan bağımlılığı belirtir.](gorseller/b33_fd_kapanis.png)

Çıktıdaki aday anahtarlar yedi tanedir: `AB`, `BC`, `BD`, `BE`, `CD`, `CE`, `CG`. Bu, bir ilişkinin birden çok aday anahtarı olabileceğinin somut bir örneğidir ve hangisini birincil anahtar seçeceğin bir tasarım kararıdır. Son satır, BCNF ihlallerini sayar. `C → A` gibi bir bağımlılığın sol tarafı (`C`) süper anahtar değildir (`C+ = {A, C}` tüm şemayı kapsamaz), dolayısıyla bu bir ihlaldir. Bu ihlaller bir sonraki bölümde, normalizasyonda ele alınacak.

Kaba kuvvet yönteminin bedeli, `n` nitelik için `2^n` alt küme denemesidir. Gerçek şemalarda `n` genelde küçüktür; ama yüz nitelikli bir şemada bu yöntem işe yaramaz ve aday anahtar bulma, dikkatli algoritmalar gerektirir. Bu bölümde ölçek sorununu değil, kavramı öğreniyoruz.

::: dikkat
Bir FD'yi veriden çıkarma. Tek bir veri setinde `X → Y` sağlanıyor diye bu bir gerçek değildir; iş kuralı bilgisi olmadan yazılan bir FD, sonradan yanlış bir ayrıştırmaya yol açar. FD'leri her zaman iş bilgisinden başlat, veriyle sadece çelişkileri ara.
:::

## 33.9 Normalizasyon: anomaliler, 1NF'den BCNF'ye ve ayrıştırmanın kalitesi

Normalizasyon, bir şemayı FD'lerine bakarak daha küçük ve daha temiz tablolara ayırma sürecidir. Amacı, her gerçeğin tek bir yerde durmasını sağlamaktır. Kötü tasarımın sonucu **anomalidir**: bir veri değişikliği, tutarlılığı bozacak biçimde birden çok satırı etkiler ya da bir gerçeği yazmayı engeller.

Üç anomali türü vardır ve her birini kötü tasarlanmış bir tabloda üreteceğiz:

- **Güncelleme anomalisi:** Bir bölümün başkanı tek satırda değiştirilir, aynı bölümün diğer satırlarında eski değer kalır.
- **Ekleme anomalisi:** Bir ders, en az bir öğrenci olmadan eklenemez, çünkü birincil anahtar öğrenci numarasını içerir.
- **Silme anomalisi:** Bir öğrencinin son kaydı silindiğinde, öğrencinin adı ve bölümü de kaybolur.

Aşağıdaki program, `ogrenci_ders` adında tek bir tablo kurar. Bu tablo her şeyi bir arada tutar: öğrenci, bölüm, bölüm başkanı, ders ve not. Sonra üç anomaliyi de gerçekten üretir. Tablodaki bağımlılıklar FD olarak açıkça yazılmıştır; `aday_anahtarlar` fonksiyonu anahtarın `{ogr_no, ders_kodu}` olduğunu doğrular.

```python
# b33_5_normal.py: anomaliler, BCNF, kayıpsızlık, korunum
import itertools
import sqlite3

from b33_4_fd import fd, kapanis, aday_anahtarlar
from b33_4_fd import bcnf_ihlalleri

R = ("ogr_no ogr_ad bolum baskan ders_kodu ders_ad "
     "not_").split()
F = [fd(["ogr_no"], ["ogr_ad", "bolum"]),
     fd(["bolum"], ["baskan"]),
     fd(["ders_kodu"], ["ders_ad"]),
     fd(["ogr_no", "ders_kodu"], ["not_"])]
print("aday anahtar:", [sorted(k) for k in aday_anahtarlar(R, F)])

# ---- Kötü tasarım: tek tablo ----
db = sqlite3.connect(":memory:")
db.execute("""CREATE TABLE ogrenci_ders(
    ogr_no INTEGER NOT NULL, ogr_ad TEXT, bolum TEXT,
    baskan TEXT, ders_kodu TEXT NOT NULL, ders_ad TEXT,
    not_ INTEGER, PRIMARY KEY (ogr_no, ders_kodu))""")
db.executemany("INSERT INTO ogrenci_ders VALUES (?,?,?,?,?,?,?)", [
    (1, "Ayşe", "BM", "Dr. X", "VT", "Veritabanı", 88),
    (1, "Ayşe", "BM", "Dr. X", "OS", "İşletim Sis.", 75),
    (2, "Mert", "BM", "Dr. X", "VT", "Veritabanı", 91),
    (3, "Ali", "EE", "Dr. Y", "DEV", "Devre", 60)])
db.execute("UPDATE ogrenci_ders SET baskan='Dr. Z' "
           "WHERE ogr_no=1 AND ders_kodu='VT'")
print("guncelleme anomalisi:", db.execute(
    "SELECT DISTINCT bolum, baskan FROM ogrenci_ders "
    "WHERE bolum='BM'").fetchall())
try:
    db.execute("INSERT INTO ogrenci_ders(ogr_no,ders_kodu,ders_ad) "
               "VALUES (NULL,'MAT101','Matematik')")
except sqlite3.IntegrityError as e:
    print("ekleme anomalisi:", e)
db.execute("DELETE FROM ogrenci_ders WHERE ogr_no=3")
print("silme anomalisi (Ali):", db.execute(
    "SELECT COUNT(*) FROM ogrenci_ders "
    "WHERE ogr_ad='Ali'").fetchone()[0])
```

Çıktının ilk bölümü şunu gösterir: `BM` bölümü için iki farklı başkan vardır (güncelleme anomalisi), `NULL` öğrenci numarası ile ders eklenemez (ekleme anomalisi) ve Ali'nin kaydı silinince ismi de yok olur (silme anomalisi). Bu anomaliler, FD'lerin *tek bir tablo içinde* birbirine karışmasından gelir: `bolum → baskan` bağımlılığı, anahtar olmayan bir nitelikten başka bir niteliğe gider.

### Normal formlar

Normal formlar, anomalileri tek tek yok eden bir merdivendir. Her biri bir öncekini içerir ve belirli bir bağımlılık türünü yasaklar:

- **1NF:** Her hücre tek bir atomik değer taşır; tekrarlayan gruplar (`dersler = "VT,OS"` gibi) yoktur.
- **2NF:** 1NF'dir ve hiçbir **asal olmayan** nitelik, bir aday anahtarın **gerçek alt kümesine** bağlı değildir. Bu, *kısmi bağımlılığın* yasaklanmasıdır. Bizim tabloda `ogr_no → ogr_ad` bunun bir örneğidir: `ogr_ad`, anahtarın yalnızca yarısına bağlıdır.
- **3NF:** 2NF'dir ve her `X → A` bağımlılığında, `X` bir süper anahtardır ya da `A` bir **asal** niteliktir (bir aday anahtarın parçası). Bu, *geçişli bağımlılığın* yasaklanmasıdır: `bolum → baskan` bunun örneğidir; `bolum` süper anahtar değildir ve `baskan` asal değildir.
- **BCNF:** Her `X → A` bağımlılığında `X` bir süper anahtardır. 3NF'deki "asal nitelik" istisnası kalkar. BCNF, 3NF'den daha katıdır ve bazı şemalarda bağımlılıkları korumayı zorlaştırır (aşağıda).

Şekil 33.6 bu merdiveni ve her adımda hangi bağımlılığın ortadan kalktığını gösterir.

![Şekil 33.6: Normal formlar merdiveni. Her adım, bir önceki adımda kalan bir bağımlılık türünü yasaklar.](gorseller/b33_normal_formlar.png)

### Ayrıştırma: BCNF'ye kayıpsız ve korunumlu geçiş

Bir şemayı ayrıştırırken iki ölçüt vardır ve ikisini birlikte sağlamak her zaman mümkün değildir:

**Kayıpsız birleştirme (lossless join).** Ayrıştırılmış tabloları yeniden birleştirdiğinde, orijinal tabloyu hiç eksik ve hiç fazla satır olmadan geri elde etmelisin. Kayıplı bir ayrıştırma, birleştirmede hayalet satırlar üretir.

**Bağımlılık koruma (dependency preservation).** Orijinal FD'lerin her biri, ayrıştırılmış tablolardan birinde kontrol edilebilmelidir. Aksi halde bir kısıtı kontrol etmek için birden çok tabloyu birleştirmek gerekir ve bu pahalıdır.

BCNF ayrıştırması kuralı basittir: ihlal eden bir `X → Y` bulduğunda, şemayı `X+` ve `R − (X+ − X)` olarak iki parçaya böl ve her parçada tekrarla. Bu yöntem her zaman kayıpsızdır. Ama bağımlılık korumayı garanti etmez. Programın son kısmı bu ölçütleri test eder: birleştirme için **tablo (chase) testi**, korunum için ise "Z := X, ayrıklar üzerinden genişlet" döngüsü.

```python
def bcnf_ayir(S, F):
    """İhlal bulunca S'yi X+ ve S-(X+ - X) olarak böler."""
    S = frozenset(S)
    ihlal = bcnf_ihlalleri(S, F)
    if not ihlal:
        return [S]
    X, _ = ihlal[0]
    X = frozenset(X)
    Xp = kapanis(X, F) & S
    R1, R2 = Xp, S - (Xp - X)
    return bcnf_ayir(R1, F) + bcnf_ayir(R2, F)


def kayipsiz_mi(R, ayrik, F):
    """Tablo (chase) testi: bir satır tümüyle 'a' olursa kayıpsız."""
    idx = {a: i for i, a in enumerate(R)}
    T = [[("a", a) if a in S else ("b", i, a) for a in R]
         for i, S in enumerate(ayrik)]
    degisti = True
    while degisti:
        degisti = False
        for X, Y in F:
            for r1, r2 in itertools.combinations(T, 2):
                if not all(r1[idx[a]] == r2[idx[a]] for a in X):
                    continue
                for a in Y:
                    k = idx[a]
                    if r1[k] != r2[k]:
                        yeni = min(r1[k], r2[k])
                        eski = max(r1[k], r2[k])
                        for satir in T:
                            if satir[k] == eski:
                                satir[k] = yeni
                        degisti = True
    return any(all(h[0] == "a" for h in s) for s in T)
```

Korunum testi aşağıdadır. Her FD için, sol tarafından başlayıp her ayrık tabloda kapanışla genişleten bir döngü çalışır; sağ tarafa ulaşılırsa FD korunmuştur.

```python
def korunuyor_mu(F, ayrik):
    """Her FD için: Z := X; ayrıklar üzerinden genişlet; Y ⊆ Z?"""
    for X, Y in F:
        Z = set(X)
        degisti = True
        while degisti:
            degisti = False
            for S in ayrik:
                yeni = kapanis(Z & S, F) & S
                if not yeni <= Z:
                    Z |= yeni
                    degisti = True
        if not set(Y) <= Z:
            return False
    return True


if __name__ == "__main__":
    ayrik = bcnf_ayir(R, F)
    print("BCNF ayrisimi:")
    for S in ayrik:
        print("  ", sorted(S))
    print("kayipsiz:", kayipsiz_mi(R, ayrik, F),
          " korunuyor:", korunuyor_mu(F, ayrik))
    # Kayıp örneği: AB->C ve C->B; BCNF bağımlılığı kaybeder.
    RA, FA = "A B C".split(), [fd("AB", "C"), fd("C", "B")]
    ayrikA = bcnf_ayir(RA, FA)
    print("A,B,C ayrisimi:", [sorted(S) for S in ayrikA])
    print("  kayipsiz:", kayipsiz_mi(RA, ayrikA, FA),
          " korunuyor:", korunuyor_mu(FA, ayrikA))
    # Kayıplı ayrışım: ortak nitelik C'ye bağlı değil.
    print("kayipli {A,C},{B,C}:", kayipsiz_mi(
        "A B C".split(), [{"A", "C"}, {"B", "C"}], [fd("A", "B")]))
```

Çıktıların ikinci bölümü şunu gösterir: `ogrenci_ders` şeması dört tabloya bölündü, ayrışım kayıpsız ve bağımlılıklar korunuyor. Üçüncü bölüm ise bir karşıt örnek verir: `AB → C` ve `C → B` bağımlılıklarıyla `R(A, B, C)` şemasını BCNF'ye ayırmak, bağımlılıklardan birini (`AB → C`) kaybettirir. Ayrışım kayıpsızdır ama korunmaz. Bu bir tasarım takası (trade-off) demektir: BCNF'de bağımlılığı kaybetmek ya da 3NF'de kalıp anomalilerin bir kısmını kabul etmek.

::: ipucu
Ayrıştırma sonucunu bir kez doğrula, ama kanıt olarak değil, kontrol olarak. Gerçek bir şemada: (1) her tablonun anahtarını yaz, (2) ortak nitelikler üzerinden birleşimin kayıpsız olduğunu tablo testiyle doğrula, (3) her FD'nin bir tabloda kontrol edilebildiğini göster.
:::

## 33.10 Denormalizasyon: ne zaman bilinçli olarak kuralı çiğnersin

Normalizasyon, yazma tarafını korur: bir gerçek bir yerde durur ve güncelleme tek bir satırda yapılır. Bedeli, okumanın birden çok tabloyu birleştirmesidir. Okuma ağırlıklı bir sistemde (ör. bir raporlama panosu, saniyede binlerce sorgu alan bir API), bu birleştirme maliyeti kabul edilemez hâle gelebilir. İşte **denormalizasyon** bu noktada, kasıtlı bir çiğnemedir: bir veriyi birden çok yerde tutarsın, okumayı hızlandırmak için.

Denormalizasyonun tipik biçimleri şunlardır: sık okunan bir niteliği ana tabloya kopyalamak (ör. öğrencinin bölüm adını her kayıtta tutmak), toplamları önceden hesaplayıp sakladığın bir sütun (ör. bir öğrencinin ortalama notu) ya da bir sorgu sonucunu saklayan görünüm (materialized view).

Bunun bedeli tutarlılıktır. Kopya bir yerde değişirse diğerleri de değişmek zorundadır ve bunu ya veritabanı tetikleyicisi (trigger) ya da uygulama kodu sağlamalıdır. Kopyayı kimse güncellemezse, anomali geri gelir; üstelik bu kez bilinçsiz bir anomali olarak.

Pratik kural şöyledir. Önce normalize et; okuma darboğazı ölçümle kanıtlanırsa denormalize et; denormalize ettiğin her kopyanın **kaynağını** (tek doğru veriyi) ve güncelleme yolunu belgele. Ölçüm olmadan yapılan denormalizasyon, karmaşıklık kazandırır ama hız kazandırmaz.

## 33.11 Depolama içi: sayfalar, B+ ağacı ve indeksler

Model ve kısıtlar mantıksal tarafı oluşturur. Veritabanının performansı ise fiziksel tarafa bağlıdır: veri diskte nasıl dizilir ve onu nasıl hızlı bulursun. Bu bölümde, Bölüm 28'deki dosya sistemi ve Bölüm 25'teki bellek hiyerarşisi kavramlarını kullanacağız.

Veritabanı motorları veriyi **sayfa (page)** adı verilen sabit boyutlu bloklarda tutar. SQLite'ta varsayılan sayfa boyutu 4096 bayttır (SQLite 3.12.0 ve sonrası; bu bölümdeki makinede `PRAGMA page_size` de 4096 döndü). Bir sayfa, diskten ya da ağdan okunurken tek birimdir: yüz bayt okumak da 4096 bayt okumak da bir disk erişimidir. Bu yüzden veritabanı tasarımında ana ölçü, *kaç sayfa okunduğudur*.

Şekil 33.7, SQLite'ın B-ağaç sayfasının düzenini gösterir. Her sayfanın başında bir başlık vardır. Hemen ardından hücre işaretçi dizisi gelir; her işaretçi 2 bayttır ve sayfanın sonundan başlayan hücre içeriğine bir konum verir. Hücre içerikleri sayfanın sonundan başa doğru büyür; aradaki boşluk, yeni işaretçi ve hücre için kullanılır.

![Şekil 33.7: SQLite B-ağaç sayfasının düzeni. İşaretçiler aşağı, hücre içerikleri yukarı büyür; ortadaki boş alan ikisini ayırır. İlk sayfada, sayfa başlığından önce 100 baytlık dosya başlığı bulunur.](gorseller/b33_sayfa_duzen.png)

Bu düzen, değişken uzunluklu satırların sayfa içinde parçalanmadan saklanmasını sağlar. Bir hücre silinirse ya da küçülürse, boşluk "serbest blok" listesine eklenir ve gerektiğinde toplanır. Bu ayrıntılar, Bölüm 28'deki dosya sistemlerinin içindeki parça (fragmentasyon) sorununun veritabanındaki karşılığıdır.

### İkili arama ağacından B+ ağacına

Bölüm 10'da ikili arama ağacını (BST) ve AVL dengelemesini gördün. Bellekte, her düğüm tek bir anahtar taşıyan ve iki çocuğu olan bir yapı, `O(log₂ n)` arama sağlar. Veritabanında aynı yapı bir sorun yaratır: her düğüm ayrı bir sayfadadır ve her seviye bir disk okumasıdır.

Bir milyon anahtarlı bir ikili ağacın yüksekliği `⌈log₂(10⁶ + 1)⌉ = 20` seviyedir; yani bir aramada 20 disk okuması. Oysa bir sayfaya çok sayıda anahtar sığarsa, her düğüm çok sayıda çocuk taşır ve ağaç çok daha sığ olur. Bu, **dallanma faktörü**dür (fan-out). Bölüm 10'daki B-ağacı köprüsü tam olarak budur: ağacın derinliği, düğüm başına çocuk sayısıyla logaritmik olarak küçülür.

B+ ağacı, bu fikri veritabanı için düzenleyen yapıdır. Üç kuralı vardır. (1) Tüm veri **yapraklarda** durur; iç düğümler yalnızca **ayırıcı** anahtarları taşır. (2) Yapraklar birbirine **bağlıdır**: her yaprağın sağ komşusuna bir işaretçisi vardır. Bu, aralık sorgusunu tek bir yaprak zinciri üzerinde yürümeye indirger. (3) Ağaç dengelidir: tüm yapraklar aynı derinliktedir.

Bir milyon anahtar için bunun etkisi çarpıcıdır. 4096 bayt sayfada, 8 baytlık bir anahtar ve 4 baytlık bir işaretçi için yaklaşık `(4096 − 12) / (8 + 4) = 340` dallanma elde edilir (başlığın 12 bayt, anahtarın 8 bayt, işaretçinin 4 bayt olduğu kabulüyle). Bu durumda `340² = 115 600 < 10⁶ ≤ 340³` olduğundan ağaç üç seviyedir. Aynı anahtarlar ikili ağaçta 20 okuma gerektirirdi; B+ ağacında 3 okuma yeter.

Aşağıdaki program bellekte çalışan bir B+ ağacı kurar. Yalnızca ekleme ve aralık sorgusu desteklenir (silme, birleştirme ve eşzamanlılık dışarıda). Ağaç bölünmelerini gerçekten yapar: yaprak dolunca anahtarını **kopyalayarak** yukarı çıkarır, iç düğüm dolunca anahtarı **itilerek** yukarı taşır. Program ayrıca rastgele bir testle, yaprak zincirinin sıralı listeyle, aralık sorgularının kaba kuvvetle ve yapının dengesiyle uyumunu sınar.

```python
# b33_6_bplus.py: bellek içi B+ ağacı (ekleme ve aralık)
import bisect
import math
import random


class Dugum:
    def __init__(self, yaprak):
        self.yaprak = yaprak
        self.anahtar = []   # ayırıcılar (iç) ya da anahtarlar
        self.cocuk = []     # iç düğüm: çocuk düğümler
        self.deger = []     # yaprak: anahtarın değeri
        self.sonraki = None  # yaprak zinciri, sağ komşu


class BPlus:
    def __init__(self, m):
        self.m = m          # bir düğümde en fazla m anahtar
        self.kok = Dugum(True)

    def _yaprağa_in(self, k):
        """Kökten yaprağa iner; (yaprak, yol) döner."""
        yol, d = [], self.kok
        while not d.yaprak:
            i = bisect.bisect_right(d.anahtar, k)
            yol.append((d, i))
            d = d.cocuk[i]
        return d, yol

    def ekle(self, k, v):
        yaprak, yol = self._yaprağa_in(k)
        i = bisect.bisect_left(yaprak.anahtar, k)
        if i < len(yaprak.anahtar) and yaprak.anahtar[i] == k:
            yaprak.deger[i] = v
            return
        yaprak.anahtar.insert(i, k)
        yaprak.deger.insert(i, v)
        if len(yaprak.anahtar) > self.m:
            self._bol(yaprak, yol)
```

Ekleme, aralık sorgusu ve bölünme kodu şöyledir. `_bol` fonksiyonu iki farklı durumu ayırır: yaprağın bölünmesi ayırıcıyı *kopyalar*; iç düğümün bölünmesi ayırıcıyı *yukarı iter* ve onu alt düzeyde bırakmaz.

```python
    def aralik(self, lo, hi):
        """lo <= k <= hi olan (anahtar, değer) çiftleri."""
        d, _ = self._yaprağa_in(lo)
        sonuc = []
        while d is not None:
            for k, v in zip(d.anahtar, d.deger):
                if k > hi:
                    return sonuc
                if k >= lo:
                    sonuc.append((k, v))
            d = d.sonraki
        return sonuc

    def _bol(self, d, yol):
        if d.yaprak:
            mid = (len(d.anahtar) + 1) // 2
            sag = Dugum(True)
            sag.anahtar = d.anahtar[mid:]
            sag.deger = d.deger[mid:]
            d.anahtar = d.anahtar[:mid]
            d.deger = d.deger[:mid]
            sag.sonraki, d.sonraki = d.sonraki, sag
            ayirici = sag.anahtar[0]     # yapraktan KOPYALANIR
        else:
            mid = len(d.anahtar) // 2
            ayirici = d.anahtar[mid]     # iç düğümden YUKARI İTİLİR
            sag = Dugum(False)
            sag.anahtar = d.anahtar[mid + 1:]
            sag.cocuk = d.cocuk[mid + 1:]
            d.anahtar = d.anahtar[:mid]
            d.cocuk = d.cocuk[:mid + 1]
        if not yol:                      # kök bölündü: ağaç büyür
            kok = Dugum(False)
            kok.anahtar = [ayirici]
            kok.cocuk = [d, sag]
            self.kok = kok
            return
        ata, i = yol.pop()
        ata.anahtar.insert(i, ayirici)
        ata.cocuk.insert(i + 1, sag)
        if len(ata.anahtar) > self.m:
            self._bol(ata, yol)
```

Kalan kısım, ağacı seviye seviye yazdıran ve testleri yapan fonksiyonlardır:

```python
    def dok(self, d=None, seviye=0, satirlar=None):
        """Seviye seviye anahtarları yazdırır (ders amaçlı)."""
        if satirlar is None:
            satirlar = {}
            self.dok(self.kok, 0, satirlar)
            for s in sorted(satirlar):
                print("  seviye %d: %s"
                      % (s, " | ".join(satirlar[s])))
            return
        satirlar.setdefault(seviye, []).append(str(d.anahtar))
        if not d.yaprak:
            for c in d.cocuk:
                self.dok(c, seviye + 1, satirlar)


if __name__ == "__main__":
    print("--- ekleme izi (m = 3) ---")
    agac = BPlus(3)
    for k in [10, 20, 5, 6, 12, 30, 7, 17]:
        agac.ekle(k, k * 100)
        print("ekle %2d:" % k)
        agac.dok()
    print("aralik [6, 17]:",
          [k for k, _ in agac.aralik(6, 17)])
```

Test, ağacın yapısını ve sonuçlarını kontrol eden yardımcı fonksiyonlarla devam eder:

```python
def yaprak_zinciri(agac):
    d = agac.kok
    while not d.yaprak:
        d = d.cocuk[0]
    zincir = []
    while d is not None:
        zincir.extend(d.anahtar)
        d = d.sonraki
    return zincir


def yapi_gecerli_mi(agac):
    """Tüm yapraklar aynı derinlikte; düğüm dolulukları uygun."""
    derinlikler, sorun = set(), []

    def gez(d, seviye, kok_mu):
        if len(d.anahtar) > agac.m:
            sorun.append("fazla")
        if not kok_mu and len(d.anahtar) < agac.m // 2:
            sorun.append("az")
        if d.yaprak:
            derinlikler.add(seviye)
            return
        if len(d.cocuk) != len(d.anahtar) + 1:
            sorun.append("cocuk")
        for c in d.cocuk:
            gez(c, seviye + 1, False)

    gez(agac.kok, 0, True)
    return len(derinlikler) == 1 and not sorun
```

Son bölüm, rastgele test ile yükseklik karşılaştırmasını yapar:

```python
if __name__ == "__main__":
    print("--- rastgele test (tohum 33) ---")
    rnd = random.Random(33)
    for m in (3, 4, 8):
        anah = rnd.sample(range(10 ** 6), 2000)
        agac = BPlus(m)
        for k in anah:
            agac.ekle(k, -k)
        duz = sorted(anah)
        aralik_ok = True
        for _ in range(300):
            lo = rnd.randrange(10 ** 6)
            hi = lo + rnd.randrange(50000)
            bekl = [k for k in duz if lo <= k <= hi]
            if [k for k, _ in agac.aralik(lo, hi)] != bekl:
                aralik_ok = False
        print("m=%d zincir=%s yapi=%s aralik=%s" % (
            m, yaprak_zinciri(agac) == duz,
            yapi_gecerli_mi(agac), aralik_ok))

    print("--- yükseklik (N = 10^6) ---")
    N = 10 ** 6
    ikili = math.ceil(math.log2(N + 1))
    f = (4096 - 12) // (8 + 4)   # başlık 12, anahtar 8, işaretçi 4
    seviye = 1
    while f ** seviye < N:
        seviye += 1
    print("dallanma (kaba):", f)
    print("ikili agac yuksekligi:", ikili)
    print("B+ agac seviyesi:", seviye)
```

Çıktı:

```term
$ python b33_6_bplus.py
--- ekleme izi (m = 3) ---
ekle 10:
  seviye 0: [10]
ekle 20:
  seviye 0: [10, 20]
ekle  5:
  seviye 0: [5, 10, 20]
ekle  6:
  seviye 0: [10]
  seviye 1: [5, 6] | [10, 20]
ekle 12:
  seviye 0: [10]
  seviye 1: [5, 6] | [10, 12, 20]
ekle 30:
  seviye 0: [10, 20]
  seviye 1: [5, 6] | [10, 12] | [20, 30]
ekle  7:
  seviye 0: [10, 20]
  seviye 1: [5, 6, 7] | [10, 12] | [20, 30]
ekle 17:
  seviye 0: [10, 20]
  seviye 1: [5, 6, 7] | [10, 12, 17] | [20, 30]
aralik [6, 17]: [6, 7, 10, 12, 17]
--- rastgele test (tohum 33) ---
m=3 zincir=True yapi=True aralik=True
m=4 zincir=True yapi=True aralik=True
m=8 zincir=True yapi=True aralik=True
--- yükseklik (N = 10^6) ---
dallanma (kaba): 340
ikili agac yuksekligi: 20
B+ agac seviyesi: 3
```

Çıktının ilk kısmı ekleme izidir (m = 3, yani bir düğümde en fazla üç anahtar). Burada `6` eklenince yaprak `[5, 6, 10, 20]` olarak taşar, bölünür ve `10` kökte yeni bir seviye olarak çıkar. Bu, kopyalama kuralının bir örneğidir: `10` hem sağ yaprağın ilk anahtarı olarak yapraklarda kalır hem de kökte ayırıcı olur. Rastgele testte üç farklı dallanma (m = 3, 4, 8) için de yaprak zinciri, yapı ve 300 aralık sorgusunun tamamı doğrulanmıştır. Son iki satır, bölüm başında hesapladığımız yüksekliklerdir: 20 ile 3.

Şekil 33.8, bir yaprağın bölünmesini ve ayırıcının kopyalanmasını gösterir.

![Şekil 33.8: Yaprak bölünmesi. Taşan yaprak ikiye bölünür; sağ yaprağın ilk anahtarı (10) kökte ayırıcı olarak kopyalanır. Yapraklar arasındaki bağ, aralık sorgusu için korunur.](gorseller/b33_bplus_bolunme.png)

Bu programın sonuçları, B+ ağacının gerçek veritabanlarında neden tercih edildiğini gösterir. Ancak bir ayrıntı, SQLite'ın gerçek dosyasını incelerken daha da net görünecek: tablo ağacı ve indeks ağacı aynı sayfa düzenini kullanır, ama içerdikleri bilgi farklıdır (33.12).

### Indeks türleri

Bir indeks, bir sütunun değerlerini bir yapıda tutarak arama süresini düşürür. Üç temel ayrım vardır.

**Kümelenmiş (clustered) ve kümelenmemiş (non-clustered) indeks.** Kümelenmiş indeksin yaprakları asıl satırları taşır; yani veri, indeksin sırasına göre fiziksel olarak dizilmiştir. Bir tablo yalnızca bir kümelenmiş indekse sahip olabilir. Kümelenmemiş indeksin yaprakları ise satırın konumuna (SQLite'ta rowid'ye, bazı sistemlerde birincil anahtara) bir işaretçi taşır; asıl satır için ikinci bir okuma gerekir. SQLite'ta `WITHOUT ROWID` tabloları, veriyi birincil anahtara göre B-ağacında tutar ve bu yüzden kümelenmiş gibi davranır (genel bilgi).

**Kapsayan (covering) indeks.** Bir sorgunun ihtiyaç duyduğu tüm sütunlar indeksin içindeyse, motor asıl satıra hiç gitmez. Bu, en ucuz okumadır. SQLite bunu sorgu planında açıkça gösterir. Aşağıdaki kısa deney, aynı tabloda iki indeksle farklı sorguların nasıl planlandığını yazdırır:

Aşağıdaki kısa program, aynı tabloda iki indeksle üç sorgunun planını yazdırır:

```python
# b33_10_indeks.py: indeks türüne göre sorgu planı
import sqlite3

c = sqlite3.connect(":memory:")
c.execute("CREATE TABLE ogrenci(no INTEGER PRIMARY KEY, "
          "ad TEXT, bolum TEXT)")
c.execute("CREATE INDEX i_ad ON ogrenci(ad)")
c.execute("CREATE INDEX i_ad_bolum ON ogrenci(ad, bolum)")
for q in ["SELECT ad FROM ogrenci WHERE ad = 'x'",
          "SELECT ad, bolum FROM ogrenci WHERE ad = 'x'",
          "SELECT * FROM ogrenci WHERE ad = 'x'"]:
    plan = c.execute("EXPLAIN QUERY PLAN " + q).fetchone()[3]
    print(plan)
```

Çıktı:

```term
$ python b33_10_indeks.py
SEARCH ogrenci USING COVERING INDEX i_ad (ad=?)
SEARCH ogrenci USING COVERING INDEX i_ad_bolum (ad=?)
SEARCH ogrenci USING COVERING INDEX i_ad_bolum (ad=?)
```

Üçüncü satır ilginçtir: `SELECT *` de kapsayan indeks kullanır, çünkü `no` bir `INTEGER PRIMARY KEY`'dir ve SQLite'ta rowid ile aynıdır; her indeksin içinde zaten vardır. Sorgu planlarını ayrıntılı okumak ve yazmak Bölüm 34'ün konusudur.

**Hash indeksi.** Anahtarı bir karma fonksiyonla bir kovaya yerleştirir (Bölüm 9). Eşitlik sorgusunda ortalama `O(1)`'dir, ama aralık sorgusu yapamaz: `WHERE no BETWEEN 10 AND 20` için karma indeks işe yaramaz, çünkü anahtarların sırası bilgisi tutulmaz. SQLite kullanıcıya hash indeks sunmaz (genel bilgi); PostgreSQL gibi sistemlerde ise vardır.

Ölçek konusunda bir not: büyük bir tabloya indeks kurmak için verinin tamamını sıralamak gerekir. Veri belleğe sığmazsa bu, Bölüm 13'teki **dış birleştirme sıralaması** ile yapılır. Veritabanları indeks kurma sırasında bunu kullanır.

## 33.12 SQLite'ın gerçek dosyası: başlık ve sayfa türleri

Şimdiye kadar anlattığımız yapıların gerçek bir örneğini görmek için SQLite dosyasının içine bakacağız. SQLite'ın dosya biçimi belgelenmiştir ve dosya tek bir taşınabilir dosya olduğu için, Python ile birkaç bayt okuyarak yorumlamak mümkündür. Bu bölümde `sqlite3_analyzer` gibi bir araç kullanmıyoruz; dosyayı bayt bayt okuyoruz.

Dosyanın ilk 100 baytı, bir **dosya başlığıdır**. İlk 16 bayt `SQLite format 3` yazısı ve bir sıfır bayttır. Sonraki alanlar sayfa boyutu, değişiklik sayacı, dosyadaki sayfa sayısı ve metin kodlamasıdır. Bütün tamsayılar büyük uçlu (big-endian) yazılır: en anlamlı bayt önce gelir. SQLite'ın kendi belgesindeki tablodan bir kesit (kaynak kodu, aşağıdaki Kod Okuma Egzersizi'nde) bu alanların resmi tanımını verir.

Aşağıdaki program bir tablo ve bir indeks içeren bir veritabanı oluşturur, sonra başlığı çözer ve her sayfanın türünü ve hücre sayısını yazdırır. İç sayfalarda çocuk sayfa numaralarını da okur; böylece ağacın yapısını sayfa düzeyinde görebilirsin.

```python
# b33_7_sayfa.py: gerçek bir SQLite dosyasını ve sayfalarını oku
import os
import sqlite3
import struct

YOL = "b33_ornek.db"
for f in (YOL, YOL + "-wal", YOL + "-shm"):
    if os.path.exists(f):
        os.remove(f)

db = sqlite3.connect(YOL)
db.execute("PRAGMA journal_mode = DELETE")
db.execute("CREATE TABLE ogrenci(no INTEGER PRIMARY KEY, ad TEXT)")
db.execute("CREATE INDEX i_ad ON ogrenci(ad)")
db.executemany("INSERT INTO ogrenci(ad) VALUES (?)",
               [("ogr%04d" % i,) for i in range(300)])
db.commit()
db.close()

with open(YOL, "rb") as f:
    veri = f.read()


def u16(bas):
    return struct.unpack(">H", veri[bas:bas + 2])[0]


def u32(bas):
    return struct.unpack(">I", veri[bas:bas + 4])[0]


ilk = veri[:100]
sayfa = u16(16)
print("sqlite", sqlite3.sqlite_version)
print("baslik:", ilk[0:16])
print("sayfa boyutu (16-17):", sayfa)
print("yazma/okuma surumu (18,19):", ilk[18], ilk[19])
print("degisiklik sayaci (24):", u32(24))
print("veritabani boyutu (28):", u32(28), "sayfa")
print("sema cerezi (40):", u32(40))
print("metin kodlamasi (56):", u32(56))
print("dosya boyutu:", len(veri), "=", len(veri) // sayfa,
      "sayfa")
```

Sayfa türünü ve çocukları bulan kısım şöyledir:

```python
print()
TUR = {0x0D: "yaprak tablo", 0x05: "iç tablo",
       0x0A: "yaprak indeks", 0x02: "iç indeks"}


def baslik_konumu(no):
    """Sayfa başlığının bayt konumu (1. sayfada 100 bayt sonra)."""
    return (no - 1) * sayfa + (100 if no == 1 else 0)


def cocuklar(no):
    """İç sayfanın çocukları: ilk hücre + en sağ işaretçi."""
    bas = baslik_konumu(no)
    sag = u32(bas + 8)
    hucre = u16(bas + 12)
    sol = u32((no - 1) * sayfa + hucre)
    return [sol, sag]


for no in range(1, len(veri) // sayfa + 1):
    bas = baslik_konumu(no)
    tur = TUR.get(veri[bas], "?")
    ek = ""
    if tur.startswith("iç"):
        ek = "  cocuklar=%s" % cocuklar(no)
    print("sayfa %d: %-13s hucre=%d%s"
          % (no, tur, u16(bas + 3), ek))
```

Çıktı:

```term
$ python b33_7_sayfa.py
sqlite 3.49.1
baslik: b'SQLite format 3\x00'
sayfa boyutu (16-17): 4096
yazma/okuma surumu (18,19): 1 1
degisiklik sayaci (24): 3
veritabani boyutu (28): 7 sayfa
sema cerezi (40): 2
metin kodlamasi (56): 1
dosya boyutu: 28672 = 7 sayfa

sayfa 1: yaprak tablo  hucre=2
sayfa 2: iç tablo      hucre=1  cocuklar=[6, 7]
sayfa 3: iç indeks     hucre=1  cocuklar=[4, 5]
sayfa 4: yaprak indeks hucre=145
sayfa 5: yaprak indeks hucre=154
sayfa 6: yaprak tablo  hucre=281
sayfa 7: yaprak tablo  hucre=19
```

Başlık alanları beklediğimiz değerleri verir: sayfa boyutu 4096, dosya 7 sayfa (28 672 bayt), metin kodlaması UTF-8 (değer 1). Şema çerezi (`40`) 2'dir; çünkü şemaya iki nesne (tablo ve indeks) eklendi ve her şema değişikliği bu sayacı artırır.

Sayfa türleri, sayfa başlığının ilk baytında yazılır. Dosyadaki değerler, belgedeki bayrak tablosuna uyar: 0x0D (`1 + 4 + 8`) intkey + leafdata + leaf, yani tablonun yaprağıdır; 0x05 (`1 + 4`) tablonun iç düğümüdür; 0x0A (`2 + 8`) indeksin yaprağıdır; 0x02 (`2`) indeksin iç düğümüdür. Sayfa 2, tablonun kökü olan iç düğümdür ve iki çocuğu vardır: sayfa 6 ve 7. Sayfa 3, indeksin kökü olan iç düğümdür ve çocukları 4 ve 5'tir.

Dikkatli bir okuyucu iki sayım görmelidir. Tablonun yapraklarında `281 + 19 = 300` satır var: tablo 300 öğrenci içeriyor. İndeks yapraklarında `145 + 154 = 299` girdi var ama indeksin iç düğümünde de bir girdi (`hucre=1`) bulunuyor: `299 + 1 = 300`. Bu gözlem, önemli bir ayrımı gösterir. **Tablo ağacında** iç düğümler yalnızca ayırıcı tamsayıları (rowid'leri) taşır; veri yapraklardadır. Bu, 33.11'deki B+ ağacının tam bir örneğidir. **İndeks ağacında** ise iç düğümler de girdi (anahtar ve rowid) taşır; bu, klasik B-ağaç düzenidir. Yani SQLite'ta tablolar B+ benzeri, indeksler B benzeri ağaçlardır; belgeye göre de böyledir (genel bilgi, sayım olarak burada doğrulandı).

Dosya boyutu sayfa boyutunun tam katı olmalıdır; bunu da kontrol edebilirsin: `28 672 / 4096 = 7`.

## 33.13 ACID, WAL ve çökme kurtarma

Bir veritabanı işlemi (transaction), birlikte doğru olması gereken bir dizi işlemin tek birim olarak yürütülmesidir. Bir banka transferi buna iyi bir örnektir: A hesabından düşmek ve B hesabına eklemek ikisi birlikte olmalıdır. Bu birimin dört özelliği ACID olarak adlandırılır (kısaltma 1983'te Haerder ve Reuter tarafından önerildi; genel bilgi).

**Atomiklik (Atomicity).** İşlem ya tamamen uygulanır ya hiç uygulanmaz. Yarım kalan bir transfer, A'dan düşmüş ama B'ye eklenmemiş bir durum bırakmamalıdır.

**Tutarlılık (Consistency).** İşlem, veritabanını tutarlı bir durumdan yine tutarlı bir duruma taşır. Kısıtlar (33.4) bu tutarlılığın bir parçasını motora yaptırır; geri kalanı, yani "para korunur" gibi iş kuralları, uygulamanın sorumluluğundadır.

**Yalıtım (Isolation).** Eşzamanlı işlemler birbirinin ara durumlarını göremez. Bu, 33.14'ün konusudur.

**Kalıcılık (Durability).** Commit edilmiş bir işlem, sistem çökse bile kalır. Bunu Bölüm 28.7'de gördüğün kuralla sağlarız: veri, onu gösteren kayıttan önce diske inmelidir.

Atomiklik ve kalıcılık, bir **günlük (log)** ile sağlanır. Yaygın yaklaşım **yazmadan önce günlük (Write-Ahead Log, WAL)**dir: bir değişiklik önce günlüğe yazılır ve günlükteki kayıt, işlemin commit edildiğini gösteren bir işaretle tamamlanır. Ana veri dosyası sonra, daha uygun bir zamanda güncellenir (buna *checkpoint* denir). Açılışta motor günlüğü okur: commit işaretiyle biten işlemleri yeniden uygular, işaretsiz kalanları siler.

Şekil 33.9, bu akışı gösterir.

![Şekil 33.9: WAL akışı. Değişiklik önce WAL'a yazılır; commit çerçevesi fsync ile diske iner. Checkpoint, WAL'deki değişiklikleri ana dosyaya aktarır. Açılışta yalnızca commit edilmiş çerçeveler uygulanır.](gorseller/b33_wal_akis.png)

Bölüm 28'deki "önce veri, sonra kayıt" kuralının veritabanındaki doğrudan uygulaması budur. WAL'a yazılan değişiklik bir *veri* gibi davranır, commit çerçevesi ise *kayıt*tır. Commit çerçevesi diske inmeden işlem tamamlanmış sayılmaz; bu yüzden fsync bu noktada kritiktir.

SQLite'ın iki günlük modu vardır. Varsayılan mod `DELETE`'tir: eski değerleri içeren bir `-journal` dosyası kullanır, işlem bitince siler. `WAL` modunda değişiklikler `-wal` dosyasına yazılır ve okuyucular yazıcıyı engellemez (ayrıntılı olarak, bu sürümde belgeye göre; genel bilgi). Aşağıdaki program iki modu da çökme senaryosunda dener. Çocuk süreç, commit etmeden yirmi bin satır ekler ve `os._exit` ile anında ölür; ana süreç sonra veritabanını açar.

Önce atomikliği, yani yarım kalan bir transferin geri alınmasını göreceksin:

```python
# b33_8_acid.py: atomiklik (geri alma) ve çökme kurtarma
import os
import sqlite3
import subprocess
import sys

YOL = "b33_acid.db"


def sifirla(modu):
    for f in (YOL, YOL + "-wal", YOL + "-shm", YOL + "-journal"):
        if os.path.exists(f):
            os.remove(f)
    db = sqlite3.connect(YOL)
    db.execute("PRAGMA journal_mode = %s" % modu)
    db.execute("CREATE TABLE hesap(ad TEXT PRIMARY KEY, "
               "bakiye INTEGER CHECK (bakiye >= 0))")
    db.execute("INSERT INTO hesap VALUES ('A', 100), ('B', 50)")
    db.commit()
    db.close()


def transfer(db, a, b, miktar, kesinti=False):
    """A'dan düş, B'ye ekle. Aradaki kesinti iki yarıyı ayırır."""
    with db:                              # commit ya da rollback
        db.execute("UPDATE hesap SET bakiye=bakiye-? WHERE ad=?",
                   (miktar, a))
        if kesinti:
            raise RuntimeError("yarıda kesildi")
        db.execute("UPDATE hesap SET bakiye=bakiye+? WHERE ad=?",
                   (miktar, b))


# ---- 1. İçeride hata: yarım transfer geri alınır ----
sifirla("DELETE")
db = sqlite3.connect(YOL)
try:
    transfer(db, "A", "B", 30, kesinti=True)
except RuntimeError as e:
    print("hata:", e)
print("bakiyeler:",
      db.execute("SELECT ad, bakiye FROM hesap").fetchall())
print("toplam:", db.execute(
    "SELECT SUM(bakiye) FROM hesap").fetchone()[0])
db.close()
```

Çocuk süreç bölümü ise şöyledir: süreç, commit etmeden anında kapanır (`os._exit` temiz bir kapanış yapmaz; Python'un tamponlarını ve SQLite'ın bağlantısını düzgünce kapatmaz).

```python
# ---- 2. Süreç çöker: commit edilmemiş işlem geri alınır ----
COCUK = r'''
import os, sqlite3, sys
yol, n, kip = sys.argv[1], int(sys.argv[2]), sys.argv[3]
db = sqlite3.connect(yol)
for i in range(n):
    db.execute("INSERT INTO kayit(v) VALUES (?)", ("x" * 200,))
if kip == "commit":
    db.commit()
else:
    print("  cocuk: ana=%d bayt, -journal=%s, -wal=%s" % (
        os.path.getsize(yol), os.path.exists(yol + "-journal"),
        os.path.exists(yol + "-wal") and
        os.path.getsize(yol + "-wal")))
    sys.stdout.flush()
os._exit(3)     # temiz kapanış yok: süreç anında ölür
'''


def cocuk_calistir(modu, n, kip):
    sifirla(modu)
    db = sqlite3.connect(YOL)
    db.execute("CREATE TABLE kayit(id INTEGER PRIMARY KEY, v TEXT)")
    db.commit()
    db.close()
    sys.stdout.flush()
    r = subprocess.run([sys.executable, "-c", COCUK, YOL,
                        str(n), kip])
    db = sqlite3.connect(YOL)
    sayi = db.execute("SELECT COUNT(*) FROM kayit").fetchone()[0]
    db.close()
    return r.returncode, sayi


for modu in ("DELETE", "WAL"):
    for kip in ("kesik", "commit"):
        kod, sayi = cocuk_calistir(modu, 20000, kip)
        print("%-6s %-7s cikis=%d kayit=%d"
              % (modu, kip, kod, sayi))
print("sqlite", sqlite3.sqlite_version)
```

Çıktı:

```term
$ python b33_8_acid.py
hata: yarıda kesildi
bakiyeler: [('A', 100), ('B', 50)]
toplam: 150
  cocuk: ana=2580480 bayt, -journal=True, -wal=False
DELETE kesik   cikis=3 kayit=0
DELETE commit  cikis=3 kayit=20000
  cocuk: ana=16384 bayt, -journal=False, -wal=2570912
WAL    kesik   cikis=3 kayit=0
WAL    commit  cikis=3 kayit=20000
sqlite 3.49.1
```

Birinci bölüm bize atomikliği gösterir: `transfer` içinde A'dan düşüldükten sonra hata oluştu, `with db:` bloğu işlemi geri aldı ve bakiyeler değişmedi (100 ve 50); toplam 150 olarak korundu. İkinci bölüm çökmeyi gösterir ve burada ilginç olan, çocuk sürecin çıktısıdır. DELETE modunda, çökme anında ana dosya 2 580 480 bayta ulaşmış ve `-journal` dosyası var: uncommitted sayfalar zaten diske taşmış, ama geri alma bilgisi journal'da. Açılışta SQLite journal'ı geri oynattı ve kayıt sayısı sıfır. WAL modunda ana dosya 16 384 bayttır (yalnızca başlık ve şema), 2 570 912 bayt ise `-wal` dosyasındadır; açılışta commit işareti olmayan çerçeveler yok sayıldı ve sayı yine sıfır.

Commit edilen durumda (her iki modda, `commit`) kayıt sayısı 20 000'dir: commit işareti diske inmiş ve açılışta kurtarma tüm işlemi kalıcı kılmıştır.

Bir dürüst sınır: bu deney **süreç** çökmesini simüle eder; işletim sistemi açık ve sayfa önbelleği diske boşaltılmıştır. Gerçek bir elektrik kesintisine karşı dayanıklılık, diskin yazma önbelleğinin ve `fsync` davranışının da doğru olmasını gerektirir. Bu, Bölüm 28'deki sınırla aynıdır ve Windows'ta ortam farkları olabilir (genel bilgi). Bu bölümde gösterilen şey, mantığın doğru olduğudur; donanım garantisi ayrı bir konudur.

## 33.14 Eşzamanlılık: anomaliler, serileştirilebilirlik, kilitler ve MVCC

İki işlem aynı veriye aynı anda dokunduğunda üç tür anomali ortaya çıkabilir. Bu anomalilerin hepsi, işlemlerin *serileştirilmiş* (yani sanki sırayla çalışmış gibi) görünmesi ilkesinin ihlalidir.

**Kirli okuma (dirty read).** T2, T1'in commit etmediği bir değeri okur. T1 geri alırsa T2 hiç var olmayan bir değerle çalışmış olur.

**Tekrarlanamayan okuma (non-repeatable read).** T1 bir satırı iki kez okur; arada T2 o satırı değiştirip commit eder. T1'in iki okuması farklı çıkar.

**Hayalet (phantom).** T1 bir koşulla sorgu yapar; arada T2 o koşulu sağlayan yeni bir satır ekler ve commit eder. T1'in aynı sorgusu farklı sayıda satır döndürür.

Bir dördüncü anomali de vardır: **kayıp güncelleme (lost update)**. İki işlem aynı değeri okuyup üzerine yazarsa, birinin güncellemesi kaybolur. Bu, Bölüm 27'deki paylaşılan değişken yarışının veritabanındaki karşılığıdır. Şekil 33.10 üç anomaliyi zaman çizgisi olarak gösterir.

![Şekil 33.10: Eşzamanlılık anomalileri. Her satır bir işlemin zaman çizgisidir; noktalar işlemin yaptığı okuma ya da yazmadır. Üç durum da yalıtım ihlalidir.](gorseller/b33_anomaliler.png)

Serileştirilebilirlik bu anomalileri sınıflandırmanın ölçütüdür. Bir çalışma (schedule), hiçbir serileştirme eşdeğeri değilse yani hiçbir seri sıraya denk değilse, anomalidir. **Çakışma serileştirilebilirliği** için bir kolay test vardır: iki işlemin aynı nesneye eriştiğini ve en az birinin yazdığını **çakışma** sayarsın. Çakışmalardan bir **öncelik grafı** kurarsın: `Ti` önce gelip `Tj` ile çakışıyorsa `Ti → Tj` kenarı çizilir. Grafta döngü yoksa çalışma serileştirilebilirdir; topolojik sıra bir seri eşdeğer verir.

Aşağıdaki program bu testi uygular. İki çalışma sınanır: biri kayıp güncelleme içerir (döngü var), diğeri seri eşdeğerdir. Sonra 3000 rastgele çalışmada iki yöntemin (döngü testi ve kaba kuvvet, yani tüm seri sıralamaları denemek) her zaman aynı sonucu verdiğini doğrular.

```python
# b33_9_seri.py: çakışma serileştirilebilirliği
import itertools
import random


def cakisma_kenarlari(s):
    """s: [(islem, 'R' ya da 'W', nesne)], zaman sırasıyla.
    Farklı işlemler aynı nesneye erişir ve en az biri W ise
    çakışırlar; kenar, önce gelenden sonra gelene gider."""
    kenar = set()
    for i, j in itertools.combinations(range(len(s)), 2):
        ti, ai, xi = s[i]
        tj, aj, xj = s[j]
        if ti != tj and xi == xj and "W" in (ai, aj):
            kenar.add((ti, tj))
    return kenar


def dongu_var_mi(kenar, dugumler):
    komsu = {d: [b for a, b in kenar if a == d] for d in dugumler}
    durum = {d: 0 for d in dugumler}   # 0 yeni, 1 yolda, 2 bitti

    def ara(d):
        durum[d] = 1
        for e in komsu[d]:
            if durum[e] == 1:
                return True
            if durum[e] == 0 and ara(e):
                return True
        durum[d] = 2
        return False

    return any(durum[d] == 0 and ara(d) for d in dugumler)


def seri_olabilir_mi(s):
    """Kaba kuvvet: bir seri sıra tüm kenarları koruyor mu?"""
    kenar = cakisma_kenarlari(s)
    dugum = sorted({t for t, _, _ in s})
    for p in itertools.permutations(dugum):
        konum = {t: k for k, t in enumerate(p)}
        if all(konum[a] < konum[b] for a, b in kenar):
            return True
    return False
```

Ana bölümün kodu şöyledir:

```python
def goster(ad, s):
    dizi = " ".join("%s%d(%s)" % (a, t, x) for t, a, x in s)
    k = sorted(cakisma_kenarlari(s))
    dugum = sorted({t for t, _, _ in s})
    print(ad, dizi)
    print("   kenarlar:", k, " dongu:", dongu_var_mi(k, dugum))


if __name__ == "__main__":
    # S1: kayıp güncelleme (lost update)
    S1 = [(1, "R", "X"), (2, "R", "X"),
          (1, "W", "X"), (2, "W", "X")]
    # S2: iki işlem farklı verilerle; seri eşdeğer
    S2 = [(1, "R", "A"), (1, "W", "A"), (2, "R", "A"),
          (2, "W", "A"), (1, "R", "B"), (1, "W", "B")]
    goster("S1:", S1)
    goster("S2:", S2)
    print("S1 seri olabilir mi:", seri_olabilir_mi(S1))
    print("S2 seri olabilir mi:", seri_olabilir_mi(S2))

    # Doğrulama: iki yöntem her rastgele programda uyuşmalı.
    rnd = random.Random(33)
    uyusan = bozuk = 0
    for _ in range(3000):
        n = rnd.randint(3, 6)
        s = [(rnd.randint(1, 3), rnd.choice("RW"),
              rnd.choice("XYZ")) for _ in range(n)]
        dugum = sorted({t for t, _, _ in s})
        graf = not dongu_var_mi(sorted(cakisma_kenarlari(s)), dugum)
        if graf == seri_olabilir_mi(s):
            uyusan += 1
        else:
            bozuk += 1
    print("3000 rastgele: uyusan=%d uyusmayan=%d" % (uyusan, bozuk))
```

Çıktı:

```term
$ python b33_9_seri.py
S1: R1(X) R2(X) W1(X) W2(X)
   kenarlar: [(1, 2), (2, 1)]  dongu: True
S2: R1(A) W1(A) R2(A) W2(A) R1(B) W1(B)
   kenarlar: [(1, 2)]  dongu: False
S1 seri olabilir mi: False
S2 seri olabilir mi: True
3000 rastgele: uyusan=3000 uyusmayan=0
```

`S1` çalışmasında iki kenar vardır: `1 → 2` (R1, W2'den önce) ve `2 → 1` (R2, W1'den önce). Döngü, bu çalışmanın seri olamayacağını gösterir; gerçekten de her iki işlemin okuduğu `X`'in son değeri hangisinin yazdığına bağlıdır ve kayıp güncelleme olur. `S2`'de tek kenar vardır (`1 → 2`), dolayısıyla `T1, T2` sırası bir seri eşdeğerdir.

**İki kilitleme yaklaşımı.** Anomalileri önlemenin en eski yolu kilittir. **İki aşamalı kilitleme (2PL)** kuralı: bir işlem önce kilitleri alır (büyüme aşaması), sonra bırakır (küçülme aşaması); ilk bırakmadan sonra yeni kilit alamaz. 2PL, çakışma serileştirilebilirliği garanti eder. Sıkı 2PL ise yazma kilitlerini commit'e kadar tutar; bu da kirli okumayı engeller. Kilidin bedeli, eşzamanlılığın azalması ve **kilit beklemesinden doğan kilitlenme (deadlock)** riskidir. Kilitlenmeyi engellemek için kilit sırası kuralları ya da zaman aşımı gerekir.

**MVCC (Multiversion Concurrency Control).** Kilit yerine her satırın birden çok *sürümünü* saklarsın. Her işlem, başladığı andaki bir anlık görüntüyü (snapshot) okur; yazıcılar yeni bir sürüm üretir. Okuyucular yazıcıları, yazıcılar okuyucuları bekletmez. Bunun bedeli, eski sürümlerin temizlenmesi (vacuum ya da eşdeğeri) ve yazma-yazma çakışmalarının ayrıca yönetilmesidir. PostgreSQL ve Oracle gibi sistemler MVCC kullanır (genel bilgi). SQLite'ta WAL modu okuyucuların yazıcıyı beklemediği bir anlık görüntü davranışı sağlar; ancak SQLite'ın izolasyon garantilerinin ayrıntısı ve birden çok bağlantıyla yapılan deneyler Bölüm 34'ün konusudur.

**İzolasyon seviyeleri.** SQL standardı dört seviye tanımlar (okunmamış okuma, okunmuş okuma, tekrarlanabilir okuma, serileştirilebilir) ve her seviyenin hangi anomalilere izin verdiğini listeler. Bu bölümde seviyelerin *teorisini* gördün; her birini gerçek bir SQL sisteminde denemek, Bölüm 34'te yapılacaktır.

::: dikkat
Bir uygulamada "işlem var, o yüzden tutarlı" varsayımı en yaygın sessiz hatadır. Varsayılan izolasyon seviyesi sistemden sisteme değişir ve bazı seviyeler yukarıdaki anomalilerden birkaçına izin verir. Hangi anomaliye karşı korunduğunu bilmeden paralel yazan bir uygulama yazma.
:::

## 33.15 Gerçek dünya: üç şema tasarımı

Teoriyi üç gerçek kullanım alanında birleştirelim. Her biri farklı bir tasarım kararını öne çıkarır.

**İHA uçuş kayıt sistemi.** Bir uçuş, bir İHA'nın bir görev sırasındaki kayıtlı seferidir. Varlıklar: `iha` (araç), `gorev` (görev), `ucus` (sefer), `telemetri` (zaman damgalı ölçüm), `rota_noktasi` (zayıf varlık, görevin bir noktası). Doğal anahtar sorunu burada belirgindir: araç kuyruk numarası ya da seri numarası değişebilir; yapay anahtar tercih edilmelidir. `telemetri` tablosu çok büyür; bu yüzden zaman damgası ve araç üzerinde bir bileşik indeks, tipik sorguları (bir ucuşun zaman aralığı) hızlandırır. Bu, kümelenmiş indeks kararının somut bir örneğidir. Bu bölümün ilk proje önerisi bu sistemin tam şemasını ister.

**EV Dashboard telemetri şeması.** Bir sensör cihazı, zaman damgası ve birkaç ölçüm gönderir. Burada yazma yükü yüksek, okuma ise belirli zaman aralıklarında ve belirli cihazlar için yapılır. Tasarım önerisi: ölçümler normalize edilmiş bir tabloda (`olcum(cihaz_id, zaman, tur, deger)`) ve bileşik anahtar `(cihaz_id, zaman)` ile tutulsun. Cihaz bilgisi ayrı bir tabloda durur ve 3NF'dir (cihaz türü değiştiğinde yalnızca bir yer güncellenir). Bu şemayı, Bölüm 68'de zaman serileri konusuna geldiğinde yeniden ele alacağız.

**Mert Studio Code proje meta verisi.** Bir projenin dosyaları, her dosyanın bağımlılıkları ve derleme çıktıları ilişkisel bir yapıdır. Dosyalar bir ağaç oluşturur (klasörler), bağımlılıklar N:M bir ilişkidir (bir dosya birçok dosyayı içe aktarır; bir dosya birçok kez içe aktarılır). Burada N:M için ara tablo ve yol (path) için dikkatli bir anahtar seçimi gerekir: yol değişince ne olur? Yapay bir `dosya_id` ile yol üzerinde `UNIQUE` kısıtı, yol değişikliğini yönetilebilir kılar. Bu, doğal anahtarın değişken olduğu bir durumda yapay anahtarın kazancıdır.

Üç örnek de aynı sorunun farklı yüzleridir: doğru varlıkları bulmak, doğru anahtarı seçmek, doğru yerde kısıt koymak ve gerektiğinde kasıtlı olarak normalizasyonu bozmak.

## Çözümlü Örnekler

Bu bölümdeki dört örnek, zorluk sırasına göre (★, ★★, ★★, ★★★) dizilmiştir. Her örnek aynı altı adımı izler: anla, örnekle, kaba çöz, örüntü, iyileştir, doğrula. Doğrulama adımında elle iz sürme tablosu vardır; sonunda bir varyasyon sorusu bulunur.

### Örnek 1 (★): ER'den şema çıkarma ve N:M ilişkisi

**Adım 1 — Anla.** Bir üniversitede öğrenciler birden çok ders alır, her ders birçok öğrenciye açılır ve her öğrencinin her dersteki notu ayrıdır. Görev: bu ER'yi bir SQL şemasına çevirmek ve notun nerede durması gerektiğini gerekçelendirmek. Kısıt: bir öğrenci aynı dersten iki kez notlanamaz; not 0 ile 100 arasındadır.

**Adım 2 — Örnekle.** Örnek veri: öğrenci 1 "Ayşe", öğrenci 2 "Mert"; ders "VT" (Veritabanı). Ayşe VT dersinden 88 aldı. Mert de VT dersinden 70 aldı. Şimdi bir öğrenci, bir dersten iki kez notlanmaya çalışırsa ne olur?

**Adım 3 — Kaba çöz.** Tek bir tablo düşünelim: `(ogr_no, ad, ders_kod, ders_ad, puan)`. Bu, 33.9'daki anomalileri üretir: ders adı her öğrenci satırında tekrarlanır ve bir dersin adını değiştirmek birden çok satırı güncellemeyi gerektirir. Ayrıca bir dersin kayıtlı öğrencisi yoksa o ders tabloda hiç yer alamaz.

**Adım 4 — Örüntü.** İki varlık (öğrenci, ders) ve bir N:M ilişkisi var. N:M, bir ara tablo ister. Notun ilişkiye ait olduğu (33.7) ara tabloya girmeli. Bu örüntü, öğrenci ve ders bilgisinin kendi tablolarında, not bilgisinin ise ara tabloda durmasını söyler.

**Adım 5 — İyileştir.** Şema, 33.7'deki kuralları uygular: `ogrenci` ve `ders` güçlü varlıklardır; `notu` ara tablodur ve bileşik birincil anahtar `(ogr_no, ders_kod)` aynı dersin iki kez notlanmasını engeller. Yabancı anahtarlar `ON DELETE CASCADE` ile bağlanır: bir öğrenci silinince notları da gider. Puan için `CHECK (puan BETWEEN 0 AND 100)` kullanılır. Şema, 33.7'deki DDL ile aynıdır.

**Adım 6 — Doğrula.** Şemayı SQLite'ta kurup her senaryoyu denedik. İz tablosu:

| Adım | İşlem | Beklenen | Sonuç |
|---|---|---|---|
| 1 | `ogrenci(1, 'Ayşe')` | kabul | tamam |
| 2 | `ders('VT', 'Veritabanı')` | kabul | tamam |
| 3 | `notu(1, 'VT', 88)` | kabul | tamam |
| 4 | `notu(1, 'VT', 70)` (aynı çift) | reddet (birincil anahtar) | UNIQUE hatası |
| 5 | `notu(2, 'VT', 70)` (öğrenci 2 yok) | reddet (FK) | FOREIGN KEY hatası |
| 6 | `notu(1, 'YOK', 70)` (ders yok) | reddet (FK) | FOREIGN KEY hatası |
| 7 | `notu(1, 'VT', 101)` | reddet (CHECK) | CHECK hatası |
| 8 | `DELETE ogrenci 1` | notlar CASCADE ile gider | notu sayısı 0 |

Burada bir ayrıntı: SQLite'ta `FOREIGN KEY` kontrolü açık olmalıdır (33.4). Bu örnekte `PRAGMA foreign_keys = ON` verilmiştir.

**Bunu AI'sız yazabilir misin?** Boş bir dosyada, bu sayfaya bakmadan şemayı yaz. Sonra `notu` tablosunun birincil anahtarını `(ogr_no)` olarak değiştirdiğinde hangi senaryonun (adım 4 ya da adım 3 ile aynı öğrencinin ikinci dersi) başarısız olacağını tahmin et ve dene.

### Örnek 2 (★★): Anomalili bir tabloyu 3NF'e ayrıştırma

**Adım 1 — Anla.** Bir İHA filosunun uçuş kayıtları tek tabloda tutuluyor: `ucus(ucus_no, drone_kodu, drone_model, pilot_no, pilot_ad)`. Anahtar `ucus_no`'dur. Görev: tabloyu 3NF'e ayır ve ayrışımın kayıpsız olduğunu göster.

**Adım 2 — Örnekle.** Üç uçuş kaydı: 101 numaralı uçuş drone "D1" (model "Alfa") ile pilot 7'nin (ad "Kaan") uçuşu; 102 numaralı uçuş da "D1" ile pilot 8'in (ad "Ece") uçuşu; 103 numaralı uçuş "D2" (model "Beta") ile pilot 7. Şimdi "D1"in modelini "Alfa-2" yapmak istiyorsan kaç satır güncellemelisin?

**Adım 3 — Kaba çöz.** Tek tabloda üç anomali açıktır: `D1`'in modeli iki satırda tutuluyor (güncelleme anomalisi); bir drone ya da pilot, hiç uçuşu yokken eklenemez (ekleme anomalisi); bir pilotun son uçuşu silinirse adı kaybolur (silme anomalisi). Sezgisel olarak üç ayrı gerçek vardır: uçuş, drone ve pilot.

**Adım 4 — Örüntü.** FD'ler: `ucus_no → drone_kodu, pilot_no`; `drone_kodu → drone_model`; `pilot_no → pilot_ad`. Anahtar `ucus_no` tek nitelikli olduğundan kısmi bağımlılık yoktur (2NF geçer). Ama `drone_kodu → drone_model` ve `pilot_no → pilot_ad` geçişli bağımlılıklardır: `drone_kodu` süper anahtar değildir, `drone_model` asal değildir. Bu, 3NF ihlalidir. Örüntü: her tanımlayıcının kendi tablosuna çıkması.

**Adım 5 — İyileştir.** Üç tablo: `drone(drone_kodu, drone_model)`, `pilot(pilot_no, pilot_ad)`, `ucus(ucus_no, drone_kodu, pilot_no)`. Her tabloda bir FD'nin sol tarafı anahtardır. Ayrışım kayıpsız mı? Ortak nitelikler `drone_kodu` ve `pilot_no`'dur ve bunlar sırasıyla `drone` ile `pilot`'un anahtarıdır; yani her birleşim bir ana tablodan bir satırla eşleşir. Bağımlılıkların hepsi bir tabloda kontrol edilebilir: korunum da sağlanır.

**Adım 6 — Doğrula.** Aynı FD kümesini Python'daki `aday_anahtarlar` ve `bcnf_ayir` fonksiyonlarıyla da kontrol ettik (33.9 programı). Elle iz tablosu:

| FD | Sol taraf süper anahtar mı? | Hangi tabloda? | Sonuç |
|---|---|---|---|
| `ucus_no → drone_kodu, pilot_no` | evet (anahtar) | `ucus` | korunur |
| `drone_kodu → drone_model` | evet, `drone`'da | `drone` | korunur |
| `pilot_no → pilot_ad` | evet, `pilot`'ta | `pilot` | korunur |

Güncelleme anomalisi de yok olur: `D1`'in modelini değiştirmek için tek satır (`drone` tablosunda) güncellenir.

**Bunu AI'sız yazabilir misin?** Aynı tabloya bir `ucus_tarihi` ve `gorev_no` eklediğinde, bunların FD'lerini (ör. `gorev_no → gorev_adi`) belirle. Yeni bir ayrışım gerekir mi, yoksa mevcut üç tablo yeterli mi?

### Örnek 3 (★★): FD kümesinden kapanış ve aday anahtar bulma

**Adım 1 — Anla.** Şema `R(A, B, C, D)`; bağımlılıklar `AB → C`, `C → D`, `D → A`. Görev: `{A, B}+`'yı hesapla, bütün aday anahtarları bul ve BCNF ihlalini göster.

**Adım 2 — Örnekle.** `{A, B}+` ile başla: başlangıçta `{A, B}`. `AB → C` uygulanır, `C` eklenir: `{A, B, C}`. `C → D` uygulanır, `D` eklenir: `{A, B, C, D}`. Kapanış tüm şemayı kapsar.

**Adım 3 — Kaba çöz.** Her tek nitelik için kapanışa bakalım. `{A}+ = {A}`; `{B}+ = {B}`; `{C}+ = {C, D, A}` (`C → D`, `D → A`); `{D}+ = {D, A}`. Hiçbiri tüm şemayı kapsamıyor. Şimdi ikili kümeler: `{A, B}` tam şema; `{B, C}+ = {B, C, D, A}` tam şema; `{B, D}+` ise `D → A` ile `{A, B, D}` ve `AB → C` ile `{A, B, C, D}`, tam şema.

**Adım 4 — Örüntü.** Her aday anahtar `B` içeriyor. Bunun nedeni: `B`'nin hiçbir bağımlılığın sağ tarafında olmamasıdır; `B` türetilemez, anahtara mutlaka dahil olmalıdır. Örüntü: sağ tarafta görünmeyen nitelikler her anahtarın parçasıdır.

**Adım 5 — İyileştir.** Aday anahtarlar: `AB`, `BC`, `BD` (üçü de minimal; hiçbirinin gerçek alt kümesi tam şemayı kapsamaz). Birincil anahtar seçimi bir tasarım kararıdır; `AB` doğal görünebilir. BCNF ihlali, `C → D` (sol taraf `C` süper anahtar değil) ve `D → A` (`D` süper anahtar değil) gibi bağımlılıklardır. Bunları 33.9'daki yöntemle ayırabilirsin.

**Adım 6 — Doğrula.** Kapanış izi:

| Adım | Küme | Kullanılan bağımlılık | Yeni nitelik |
|---|---|---|---|
| 0 | `{A, B}` | — | — |
| 1 | `{A, B}` | `AB → C` | `C` |
| 2 | `{A, B, C}` | `C → D` | `D` |
| 3 | `{A, B, C, D}` | — | tam şema |

Kaba kuvvetle sınamak için bu şemayı `b33_4_fd.py` ile çalıştırdık: aday anahtarlar `AB`, `BC`, `BD`; çıktı bu sonucu verdi.

**Bunu AI'sız yazabilir misin?** Aynı şemaya `D → B` bağımlılığını ekle. Yeni aday anahtarları ve `BC`'nin hâlâ anahtar olup olmadığını elle belirle.

### Örnek 4 (★★★): B+ ağacına sırayla ekleme ve bölünme izleme

**Adım 1 — Anla.** Derecesi `m = 3` (bir düğümde en fazla üç anahtar) olan bir B+ ağacına şu sırayla ekle: `10, 20, 5, 6, 12, 30, 7, 17, 40, 50, 60, 70`. Görev: her eklemede düğümlerin durumunu izle; hangi eklemede yaprak, hangisinde iç düğüm bölünür, söyle.

**Adım 2 — Örnekle.** Önce basit bir durum: `10` eklenince ağaç tek yapraktır: `[10]`. `20` eklenince `[10, 20]`. `5` eklenince `[5, 10, 20]` (hâlâ üç anahtar; bölünme yok). Dördüncü anahtar, `6`, bölünmeye yol açar.

**Adım 3 — Kaba çöz.** Bölünme kuralını uygula: yaprak `m + 1 = 4` anahtar olunca ikiye bölünür; ayırıcı sağ yaprağın ilk anahtarı olarak kopyalanır. İç düğüm dolunca ise ayırıcı yukarı itilir ve iç düğümde kalmaz. Bu iki kuralın farkını da yakalamak için dolgun iç düğüm gereken bir sekansa ihtiyaç var; yukarıdaki dizi bunu verir.

**Adım 4 — Örüntü.** Yaprak bölünmesi bir ayırıcıyı yukarı *kopyalar* (ayırıcı yaprakta kalır), iç düğüm bölünmesi ise *iter* (ayırıcı artık iç düğümde değildir). Bölünme, kökün de bölünmesine yol açabilir; o zaman ağaç bir seviye büyür.

**Adım 5 — İyileştir.** Program bu kuralları zaten uyguluyor. Ancak iyileştirme için bir soru sor: yaprak bölünmesi `(m+1+1)//2` ya da `(m+1)//2` ile mi yapılmalı? Program ikinci yöntemi kullanır: sol yaprağa daha az anahtar düşer. Bu, ağacın dolulukla ilgili kuralını (`m // 2` alt sınırı) hiçbir zaman ihlal etmez.

**Adım 6 — Doğrula.** Program çıktısının bu sekans için ilgili kısmı:

| Eklenen | Kök | Seviye 1 | Seviye 2 | Olay |
|---|---|---|---|---|
| 6 | `[10]` | `[5, 6]` \| `[10, 20]` | — | yaprak bölündü, 10 kopyalandı |
| 30 | `[10, 20]` | `[5, 6]` \| `[10, 12]` \| `[20, 30]` | — | yaprak bölündü, 20 kopyalandı |
| 40 | `[10, 20]` | `[5, 6, 7]` \| `[10, 12, 17]` \| `[20, 30, 40]` | — | bölünme yok |
| 50 | `[10, 20, 40]` | ... \| `[40, 50]` | — | yaprak bölündü, 40 kopyalandı |
| 60 | `[10, 20, 40]` | ... \| `[40, 50, 60]` | — | bölünme yok |
| 70 | `[40]` | `[10, 20]` \| `[60]` | yapraklar | iç düğüm bölündü, 40 yukarı itildi, kök bir seviye büyüdü |

Son satırda, kök `[10, 20, 40, 60]` olarak dört anahtar taşıyordu. Bu, `m = 3` sınırını aştı; iç düğüm ikiye bölündü ve ortadaki `40` yukarı itildi. Kök artık `[40]`'tır ve ağaç üç seviyeli oldu. Son adımın düğüm durumu, programın çıktısında da görülür (yukarıdaki tam çıktının `ekle 70` bölümü).

**Doğrula, yukarıdaki iz üzerinden.** İç düğüm bölünmesi sonrası toplam anahtar sayısı 12 kalır (10, 20, 5, 6, 12, 30, 7, 17, 40, 50, 60, 70 dizisinin on iki elemanı): yaprakların anahtarları `5, 6, 7, 10, 12, 17, 20, 30, 40, 50, 60, 70`, yani on iki anahtar. Kökteki `40` ve `10, 20, 60` ayırıcıdır; yapraklarda kopyası bulunur.

**Bunu AI'sız yazabilir misin?** Aynı ağaca `80, 90, 100` eklediğinde, kökün ilk kez üç anahtarlı hâlden `m = 3` sınırını aştığı eklemeyi tahmin et ve her adım için düğüm durumunu bir tabloda çiz.

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ araçları **yasak**. Amaç çalışan bir şema ya da B+ ağacı üretmek değil, kendi tasarım ve kanıt kararlarını vermek. Takıl, kâğıda çiz, küçük testler yaz; çözümü dışarıdan alma.
:::

### Proje 1 (★★): İHA görev ve uçuş kayıt sistemi için tam şema

**Amaç:** Bir İHA filosunun görev ve uçuş kayıtlarını tutan bir veritabanı şeması tasarla. Şema; araç, görev, uçuş, rota noktası ve telemetri varlıklarını içermeli.

**Beklenen davranış:** SQLite'ta çalışan bir şema. Bir görevin birden çok rota noktası olabilir (zayıf varlık); bir uçuş bir görevin bir seferidir; telemetri ölçümleri zaman damgalı olarak uçuşa bağlanır. Her tablo en az 3NF olmalı ve her karar için bir gerekçe yazılmalı. Şema, geçersiz veriyi kısıtlarla (`CHECK`, `NOT NULL`, `UNIQUE`, yabancı anahtar) reddetmeli.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Önce varlıkları ve ilişkileri çiz (33.7). Her ilişkinin kardinalitesini yaz. N:M ilişkileri için ara tablo, zayıf varlık için bileşik anahtar kullan. Anahtar seçiminde doğal ve yapay anahtarı karşılaştır ve gerekçesini yaz. Sonra her tablonun FD'lerini çıkar ve 3NF'i kontrol et.

**Başarı kriterleri:**
- Her tablo için FD listesi ve anahtar yazılmış; 3NF ihlali yok.
- Geçersiz veriler (olmayan araç, aralık dışı ölçüm, tekrar eden rota sırası) reddediliyor; her biri için bir test var.
- Silme davranışları (`ON DELETE`) her ilişki için gerekçelendirilmiş.
- Örnek veri ile bir ayrışım ya da birleşim sorgusu çalıştırılmış ve sonuç elle doğrulanmış.

### Proje 2 (★★★): Disk tabanlı mini anahtar-değer deposu

**Amaç:** Tek bir dosyada tutulan, sayfa tabanlı bir anahtar-değer deposu yaz. Depo, sabit boyutlu sayfalar kullanmalı, anahtarları bir B+ ağacı indeksi ile bulmalı ve aralık sorgusu desteklemeli. Bu proje, 33.11'deki B+ ağacını ve 33.12'deki sayfa düzenini gerçek bir dosyada birleştirir.

**Beklenen davranış:** `koy(anahtar, deger)`, `al(anahtar)` ve `aralik(alt, ust)` işlemleri. Veri 4096 baytlık sayfalarda tutulur; her sayfa ya bir yaprak ya da bir iç düğümdür. Program kapatılıp açıldığında veri ve indeks aynı kalır. Değerler bir sayfaya sığmıyorsa açık bir hata verilir (taşma sayfaları bu projenin kapsamı dışındadır).

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Her düğümü bir sayfaya serileştirme biçimini kâğıtta tasarla: başlık (tür, anahtar sayısı), anahtar ve işaretçi dizisi. `pread` ve `pwrite` ile sayfa numarasından ofset hesapla. Yaprak zincirini sayfa numaralarıyla tut (işaretçi yerine sayfa no). Önce bellekte çalışan bir B+ ağacı yaz, sonra sayfalara taşı.

**Başarı kriterleri:**
- 10 000 rastgele anahtarla yazılan veri, dosya kapatılıp açıldıktan sonra tamamen aynı okunuyor.
- Aralık sorgusu, aynı verinin sıralı listesiyle rastgele 500 sorguda eşleşiyor.
- Bir `dogrula` komutu, yaprak derinliklerinin eşit olduğunu ve düğüm dolulukların kurala uyduğunu raporluyor.
- Bir aramada okunan sayfa sayısı ölçülmüş ve ağacın yüksekliğiyle tutarlı çıkıyor.

### Ek Alıştırmalar

Aşağıdaki problemlerin çözümü bu kitapta yok. Önce kâğıda, sonra editöre geç; yapay zekâ yasak. Zorluk etiketine göre sırala.

1. **★ — Anahtar mı, süper anahtar mı?** `(ad, dogum_tarihi)` bir öğrenci tablosunda aday anahtar olabilir mi? Hangi veriyle bu kararını çürütürsün?
2. **★ — NULL'lu birincil anahtar.** `TEXT PRIMARY KEY` tanımlı bir SQLite tablosuna `NULL` yazılabilir mi? `NOT NULL` eklersen davranış nasıl değişir?
3. **★ — Üç değerli karar.** `WHERE NOT (puan > 50)` ifadesi, `puan` NULL olan bir satırda ne döndürür? Bu satırı nasıl yakalarsın?
4. **★★ — Kapanış sayımı.** `n` niteliğe sahip bir şemada, `X+` hesabı en fazla kaç FD kuralı uygulaması gerektirir? Bu, `m` bağımlılık için hangi üst sınırı verir?
5. **★★ — Kayıplı mı?** `R(A, B, C)` şemasını `{A, B}` ve `{B, C}` olarak ayırırsan, `B → C` olduğunda ayrışım kayıpsız mıdır? `B → A` olduğunda ne olur?
6. **★★ — Ara tablo mu, iki FK mı?** Bir ilişkisi 1:N olan iki varlık için ara tablo gerekir mi? Hangi koşulda N:M gibi davranır?
7. **★★ — Dallanma.** Sayfa boyutu 8192 bayta çıkarılırsa, bölüm 33.11'deki B+ ağacının seviye sayısı bir milyon anahtar için değişir mi? Hesabı yap.
8. **★★ — WAL ve checkpoint.** Bir checkpoint'ten hemen sonra çökme olursa, açılışta kurtarma neyi okur? Checkpoint'in sık yapılması kurtarmayı nasıl etkiler?
9. **★★★ — Mülakat: kayıpsız ve korunumlu.** BCNF her zaman kayıpsız ama her zaman korunumlu değildir. Bu iki özelliği birlikte sağlayan bir normal form ve ayrıştırma yöntemi var mı? (Mülakat)
10. **★★★ — Mülakat: iki işlem, bir kayıt.** İki işlem aynı satırı okuyup sonra değiştiriyor. Kayıp güncellemeyi önleyen üç yaklaşım (kilit, koşullu güncelleme, sürüm numarası) hangi durumda hangisi daha iyi? (Mülakat)
11. **★★★ — Mülakat: indeks maliyeti.** Bir tabloya beş indeks eklemek, okumayı hızlandırır; yazma üzerindeki etkisi nedir? Hangi durumda bir indeksi kaldırmak doğrudur? (Mülakat)
12. **★★★ — Mülakat: denormalizasyon kararı.** Bir raporlama sorgusu 4 tabloyu birleştiriyor ve yavaş. Normalizasyonu bozmadan yapılabilecek üç çözüm say; her birinin tutarlılık bedelini belirt. (Mülakat)

## Kod Okuma Egzersizi

Bu egzersiz, SQLite'ın resmi kaynak kodundaki B-ağaç sayfa düzeni yorumunu okumanı ister. Kaynak: SQLite **3.46.0** sürümü, `src/btreeInt.h` dosyası (sqlite/sqlite GitHub deposunun `version-3.46.0` etiketi). Dosyayı bu bölüm için doğrudan indirdik. Aşağıdaki kesit, dosya başlığı tablosunun 55–70. satırlarıdır; yorum satırlarındaki `**` önekini ve boşlukları olduğu gibi bıraktık, bir karakter değiştirmedik. Kesitin başlangıç satırı olan 55 de dahil edildi.

```c
** The format of the file header is as follows:
**
**   OFFSET   SIZE    DESCRIPTION
**      0      16     Header string: "SQLite format 3\000"
**     16       2     Page size in bytes.  (1 means 65536)
**     18       1     File format write version
**     19       1     File format read version
**     20       1     Bytes of unused space at the end of each page
**     21       1     Max embedded payload fraction (must be 64)
**     22       1     Min embedded payload fraction (must be 32)
**     23       1     Min leaf payload fraction (must be 32)
**     24       4     File change counter
**     28       4     The size of the database in pages
**     32       4     First freelist page
**     36       4     Number of freelist pages in the file
**     40      60     15 4-byte meta values passed to higher layers
```

Bu tabloyu bölüm 33.12'de Python ile okuduğumuz alanlarla karşılaştır. Dosyada 16 ve 18 numaralı ofsetler, kaynaktaki tabloyla birebir örtüşür; bizim programımız 16–17'deki sayfa boyutunu ve 18–19'daki sürüm baytlarını bu tablodan okudu. Kesitin kalan kısmı (sayfa başlığı ve hücre düzeni) daha uzun olduğu için buraya alınmadı; kaynağın tam yorumunda ayrıca okunmalı.

**Sorular — cevaplamadan geçme:**

1. Tablodaki "Max embedded payload fraction (must be 64)" alanı, bir hücrenin sayfaya tek başına ne kadar sığabileceğini sınırlar. Bu sınır, sayfa içindeki dallanma faktörünü nasıl etkiler? Bölüm 33.11'deki 340 değerinin hesabıyla karşılaştır.
2. "Max embedded payload fraction" ile "Min embedded payload fraction" arasındaki fark nedir? Bir satır sayfadan büyük olduğunda ne olduğunu kaynaktaki açıklamadan bul ve yaz.
3. "File change counter" alanı, başka bir sürecin önbelleğini ne zaman geçersiz kılmasına izin verir? Bu, Bölüm 28'deki dosya önbelleği tutarlılığıyla nasıl ilişkilidir?
4. Başlıktaki her tamsayı "big-endian" (en anlamlı bayt önce) yazılmıştır. Bir Windows (x86-64, little-endian) makinede `struct.unpack(">I", ...)` çağrısı neden doğru sonuç verir? Bunu kendi kelimelerinle açıkla.
5. "Size of the database in pages" alanı, dosya boyutundan ne zaman farklı olabilir? Bu, Bölüm 33.12'deki "28 672 / 4096 = 7" kontrolünün hangi durumda yanıltıcı olacağını gösterir mi?
6. "Schema cookie" (40. ofset) neden her şema değişikliğinde artar? Açık bir bağlantı, başka bir bağlantının yaptığı şema değişikliğini nasıl fark eder?

## Bölüm Özeti

- Dosyada veri tutmak; eşzamanlılık, tutarlılık, sorgu ve çökme sorunlarını çözmez. VTYS bu dört sorunu bir model, kısıt, indeks ve günlük ile birlikte çözer.
- İlişkisel model, verinin ilişki (tablo), demet (satır), nitelik (sütun) ve alan olarak tanımlandığı bir modeldir. Bir ilişki küme gibi davranır; SQL bunu çoklu küme olarak uygular.
- Anahtarlar tekilliği sağlar: süper, aday, birincil ve yabancı anahtar. Doğal anahtar değişebilirse yapay anahtar tercih edilir.
- Bütünlük kısıtları (`NOT NULL`, `UNIQUE`, `CHECK`, yabancı anahtar) kötü veriyi motorda reddeder. SQLite'ta yabancı anahtar kontrolü her bağlantıda `PRAGMA foreign_keys = ON` ile açılmalıdır.
- `NULL` bilinmeyen bir değerdir; karşılaştırmalar üç değerli mantıkla çalışır. `= NULL` ve `NOT IN` ile alt sorgu, sessiz hatalara yol açar.
- İlişkisel cebir (σ, π, ∪, −, ×, ⋈, ρ) SQL'in matematiksel karşılığıdır ve sorgu optimizasyonunun dilidir.
- Normalizasyon, FD'lerden yola çıkarak anomalileri 1NF'den BCNF'ye kadar yok eder. Ayrıştırmada kayıpsızlık ve bağımlılık koruma birlikte her zaman sağlanamaz.
- B+ ağacı, sayfa tabanlı depolamada dallanma faktörünü yüksek tutarak derinliği küçültür: bir milyon anahtar için 3 seviye. Tablo ağacı ve indeks ağacı SQLite'ta farklı bilgi taşır.
- ACID; atomiklik, tutarlılık, yalıtım ve kalıcılıktır. WAL, "önce günlük" kuralıyla atomikliği ve kalıcılığı sağlar. Eşzamanlılıkta serileştirilebilirlik, 2PL ve MVCC ana araçlardır.

**Sonraki bölümde:** Bölüm 34 (SQL Derinlemesine) bu bölümün modelini sorgu dili olarak açar: JOIN türleri, alt sorgular, pencere fonksiyonları, sorgu planları ve izolasyon seviyelerinin pratikte denenmesi. Bu bölümde gördüğün cebir ve indeks kavramları, o bölümde SQL'in her cümlesinin altında nasıl çalıştığını anlamanı sağlayacak.

::: mulakat
Aşağıdaki sorular cevapsız bırakılmıştır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. Bir tabloda `(ogr_no, ders_kod)` bileşik anahtarı var. Bu anahtarın bir parçası olan `ogr_no`'yu tek başına yabancı anahtar yapabilir misin? Sonuçları nedir?
2. `NULL = NULL` neden DOĞRU değil? Bu tasarım kararının sorgu yazarına maliyeti nedir?
3. Bir şemayı BCNF'ye ayırdın ve bir bağımlılığı kaybettin. Bunu geri kazanmak için hangi yollar var? Her birinin bedelini say.
4. Bir B+ ağacı ile ikili arama ağacı arasında, bellek içi kullanımda bile fark var mı? Disk üzerinde fark neden büyür?
5. Bir veritabanında yazma ağırlıklı bir iş yükü için indeks sayısını nasıl seçersin? Hangi ölçümleri alırsın?
6. WAL'da commit çerçevesi diske inmeden çöküş olursa işlem ne olur? Bu, `fsync`'in neden her commit'te gerektiğini nasıl açıklar?
7. Bir sistemde iki işlem aynı satırı okuyup değiştirirse hangi anomali oluşur? Kilit, MVCC ve sürüm numarası arasında hangisini seçersin ve neden?
8. Ayrı bir sunucudaki bir veritabanına karşı çalışan bir uygulama, her sorguda yabancı anahtar kontrolünü açmayı unuttu. Bunu üretimde nasıl fark edersin ve düzeltmek için hangi test eklenmeli?
:::
