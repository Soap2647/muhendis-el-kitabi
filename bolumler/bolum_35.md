%% kisim_no: VIII
%% kisim_ad: Veritabanı
%% bolum_no: 35
%% baslik: NoSQL

## Giriş: Tek bir sunucuya sığmayan veri

Bölüm 33'te ilişkisel modelin neden bu kadar yaygın olduğunu gördün: tablolar, anahtarlar, JOIN ve ACID birlikte güçlü bir sözleşme veriyor. Bölüm 34'te bu sözleşmeyi SQL ile konuşmayı ve indekslerin işlem maliyetini öğrendin. Peki veri tek bir disk ve tek bir makineye sığmıyorsa, her saniyede yüz binlerce yazma geliyorsa, şema her hafta değişiyorsa ne olur? İşte NoSQL bu sorunun cevabı olarak doğdu. "NoSQL" adı tam bir tanım değildir; "SQL değil" yerine daha doğru bir okuma "SQL'in tek çözüm olmadığı" demektir.

Bu bölümün bakış açısı şu: her NoSQL sistemi, bir şeyi kazanmak için başka bir şeyi bırakır. Anahtar-değer deposu hızlı nokta okuma verir ama sorgu dilini bırakır. Geniş sütun deposu yoğun yazmayı kaldırır ama esnek JOIN'i yok eder. Bu değiş-tokuşları anlamadan bir veritabanı seçmek, kulağa hoş gelen bir isme bakarak karar vermeye benzer. Bu yüzden bölüm, veritabanı "marka"larını değil, arkalarındaki iki şeyi anlatır: **verinin diske nasıl yazıldığı** (depolama motoru) ve **verinin birden çok makinede nasıl tutulduğu** (dağıtık sistem).

Savunma sanayiinde ve gömülü sistemlerde bu konu somuttur. Bir İHA'nın uçuş telemetrisi saniyede yüzlerce ölçüm üretir; bu veriyi yerde bir sunucuya yazmak, ağ kesilse de kaybetmemek, sonra da belirli bir zaman aralığını hızla sorgulamak gerekir. Mert'in EV Dashboard projesinde STM32'den gelen sensör akışını düşün: o akışın bir zaman serisi olduğunu fark ettiğin anda, bu bölümdeki kararların neden gerekli olduğu kendiliğinden ortaya çıkar.

Bölüm boyunca küçük bir LSM anahtar-değer deposunu sıfırdan yazacak, bir Bloom filtresinin yanlış pozitif oranını ölçecek, tutarlı hash halkasında düğüm eklemenin bedelini sayacak ve quorum okumalarında bayat veri olasılığını simülasyonla göreceksin. Her sayının üretildiği kod kitapta, çıktısı da metinde.

::: not
Bu bölümdeki sayılar Windows 11 Pro üzerinde, Python 3.12.10 ile alındı. SQLite sürümü 3.49.1'dir. Makinede Redis kurulu değildir; Redis ile ilgili kısımlar kavramsaldır ve "genel bilgi" olarak işaretlidir. Tüm rastgele deneyler sabit tohumla (seed) çalıştı: tohum değeri 35. Sayılar makineye bağlı değildir ama farklı bir tohum ya da farklı bir hash fonksiyonu oranları değiştirir; neden o yönde çıktıklarını anlamak asıl kazanımdır.
:::

## 35.1 İlişkisel modelin sınırları

İlişkisel veritabanının iki büyük gücü vardır. Birincisi, veriyi **normalize** ederek tekrarı azaltır ve her gerçeği tek bir yerde tutar (Bölüm 33). İkincisi, **JOIN** ile bu parçaları sorgu anında birleştirir ve bunu bir optimize edici yapar (Bölüm 34). Bu iki güç, tek bir makinede çalışırken çok değerlidir. Ama üç yerde sürtünme çıkar.

**Şema değişimi.** Bir tablonun şemasını değiştirmek, tabloda milyarlarca satır varsa basit bir iş değildir. Yeni bir sütun eklemek bazı sistemlerde tabloyu yeniden yazmayı gerektirir; bu, bakım penceresi ve kilit demektir. Üstelik her satırın aynı şekle sahip olmasını zorlar. Oysa bir telemetri paketi her firmware sürümünde biraz farklı alanlar taşıyabilir.

**Yatay ölçekleme.** Dikey ölçeklemek, yani daha güçlü bir makine almak, bir noktada ekonomik ve fiziksel olarak biter. Yatay ölçekleme, yani veriyi birkaç makineye bölmek, ilişkisel modelin varsayımlarını bozar. İki tabloyu JOIN etmek için veri iki makinede de olabilir ve sorgu bir ağ turu gerektirir. Bu gecikme, mikrosaniyelerden milisaniyelere çıkar; her JOIN'de bu cezayı ödemek zorunda kalırsın.

**Birleştirme maliyeti dağıtık ortamda.** Tek makinede bir işlemi tamamlamak için diskteki bir sayfayı kilitlemek yeterlidir. Dağıtık bir işlemde ise iki makine "birlikte evet" demelidir. Bu, iki aşamalı işlem (two-phase commit) gibi protokollerle yapılır ve bir makine yanıt vermezse herkes bekler. Bölüm 41'de bu protokolün ve alternatiflerinin sistem tasarımına etkisini göreceksin.

Bu üç sürtünme NoSQL'in doğuş nedenidir, ama bir noktayı netleştirmek gerekir: NoSQL, ilişkisel modelin bu sorunlarını **çözmez**, belirli bir yönde **ertelemeyi** seçer. Şema esnekliği için tutarlılık kuralını uygulamaya bırakırsın. Yatay ölçekleme için çoğu zaman JOIN'i bırakır ve veriyi sorguya göre önceden birleştirirsin (denormalizasyon, 35.9). Dağıtık işlem yerine tek bir anahtarın üzerinde atomik işlem verirsin.

## 35.2 Dört artı bir aile: karar tablosu

NoSQL, tek bir teknoloji değil beş yaygın veri modelinin ailesidir. Her ailenin varsayımı, hangi erişim deseninde iyi olduğunu belirler.

**Anahtar-değer (key-value)** en basit modeldir: bir anahtar verilir, bir değer (bayt dizisi) döner. Önbellek, oturum, sayaç ve yapılandırma için idealdir. Redis (bellek içi, isteğe bağlı kalıcılık) ve RocksDB (LSM tabanlı gömülü depo) bu ailedendir. Bölüm 4'te Redis'in Makefile'ını okumuştun; o projenin asıl işi bu ailenin bir örneğidir.

**Belge (document)** değeri bir JSON benzeri yapı olarak saklar ve belgenin içini sorgulamaya izin verir. Şema her belgede farklı olabilir. MongoDB bu ailenin en bilinen örneğidir. Birlikte okunan, iç içe ve değişken yapılı veride güçlüdür; birden çok belge arasında JOIN gerektiren sorgularda zayıftır.

**Geniş sütun (wide-column)** satır anahtarı ve sütun aileleri üzerine kuruludur. Her satırın farklı sütunları olabilir ve veriler satır anahtarına göre fiziksel olarak sıralı tutulur. Cassandra ve HBase bu ailendendir. Yoğun yazma ve belirli bir anahtar aralığını okuma için tasarlanmıştır (genel bilgi).

**Graf (graph)** düğümleri ve kenarları birinci sınıf veri olarak tutar. "Arkadaşımın arkadaşları" ya da "bu parçanın tedarik zinciri" gibi çok adımlı ilişki gezintisi, ilişkisel modelde her adımda bir JOIN ister ve derinleştikçe çöker. Neo4j bu ailenin bilinen örneğidir.

**Zaman serisi (time series)** veriyi zaman damgası ile etiketlenmiş ölçümler olarak tutar. Yazmalar hemen hemen her zaman sondadır, sorgular da çoğunlukla bir zaman aralığı üzerindedir. Telemetri, metrik ve IoT verisi bu ailenin tipik işidir. InfluxDB ve TimescaleDB (PostgreSQL üzerine kurulu bir eklenti) bu ailendendir.

![Şekil 35.1: NoSQL ailelerinin karar haritası: erişim deseni ailenin seçimini belirler.](gorseller/b35_aileler.png)

Şekil 35.1 karar mantığını özetliyor. Kararı tek bir soruya indirgemek gerekirse: **verinin ana erişim deseni nedir?** Sorgu bir anahtarla nokta okuma mı, belge içinde filtreleme mi, satır aralığı taraması mı, ilişki gezintisi mi, yoksa zaman aralığı mı? Bu cevap ailenin seçimini belirler.

| Erişim deseni | Önerilen aile | Bedel |
|---|---|---|
| Anahtarla nokta okuma/yazma | Anahtar-değer | Değer içinde sorgu yok |
| Değişken yapılı belgeyi bir arada okuma | Belge | Belgeler arası JOIN zor |
| Yoğun yazma, anahtar aralığı tarama | Geniş sütun | Esnek sorgu ve JOIN yok |
| Çok adımlı ilişki gezintisi | Graf | Toplu analiz ve yazma ölçeği ayrı sorun |
| Zaman damgalı yazma, zaman aralığı sorgusu | Zaman serisi | Genel amaçlı ilişki modeli zayıf |
| Tutarlılık, JOIN, karmaşık sorgu | İlişkisel | Yatay ölçekleme daha pahalı |

Bu tablo bir kural değil, bir başlangıç noktasıdır. Gerçek bir sistemde çoğu zaman birden çok aile birlikte kullanılır: uygulama ilişkisel veritabanında iş verisini, Redis'te önbelleği, zaman serisi deposunda telemetriyi tutar. Her veri parçası kendi erişim desenine göre bir yere gider; buna **polyglot persistence** denir.

## 35.3 Depolama motorunun içi: B+ ağacı ve LSM ağacı

Veritabanını ailelere göre seçmek, arkasındaki depolama motoruna bakmayı gerektirir. Çünkü iki temel sorunun cevabı burada yatar: veri nasıl **okunur** ve nasıl **yazılır**. Bu sorunları çözmek için iki ana yaklaşım vardır.

**B+ ağacı** (Bölüm 33'te derinleşir) veriyi diskte sabit boyutlu sayfalar halinde tutan bir ağaçtır. Bir anahtarı aramak kökten yaprağa kadar birkaç sayfa okumaktır; güncelleme ise ilgili yaprak sayfasını bulup **yerinde** değiştirmek ve gerekirse sayfayı bölmektir. Okuma çok hızlıdır çünkü ağaç dengelidir ve dallanma faktörü büyük olduğu için derinlik küçüktür. Bedeli, yazmanın **rastgele** sayfalara dokunmasıdır: her yazma diskin farklı bir yerine gider ve bu, dönen disklerde ve hatta SSD'lerde kendi maliyetini getirir.

**LSM ağacı** (Log-Structured Merge-tree) tam tersine yazmayı sıralı tutar. Her yazma önce bellekteki bir tabloya (memtable) girer ve günlüğe (WAL) eklenir. Memtable dolunca sıralı bir dosya (SSTable) olarak diske yazılır ve bu dosya bir daha değiştirilmez. Dosyalar zamanla birikir; arka planda **birleştirme** (compaction) ile bir araya getirilip temizlenir. Yazma hep dosyanın sonuna ekleme olduğu için sıralıdır ve hızlıdır. Bedeli, okumanın birden çok dosyaya bakmasıdır.

![Şekil 35.2: B+ ağacı yerinde güncelleme yapar; LSM yazmayı sıralı bir günlüğe ve değişmez dosyalara dönüştürür.](gorseller/b35_bplus_lsm.png)

Şekil 35.2 iki yolu yan yana gösteriyor. Sol sütunda B+ ağacı her yazmada rastgele bir sayfayı okuyup yazar. Sağ sütunda LSM önce günlüğe sıralı bir ekleme yapar, sonra her şeyi belleğe koyar ve dolunca sıralı bir dosya üretir. Diskin rastgele erişimdeki yavaşlığı ile sıralı erişimdeki hızı arasındaki farkı, Bölüm 28'deki tampon ve `fsync` ölçümlerinde görmüştün; bu bölümün yazma tasarımı o farkın üzerine kurulu.

Bu iki yaklaşımın hangisinin kazandığı iş yüküne bağlıdır. Okuma ağırlıklı, rastgele güncellemeli bir veri (bir ürün katalogu gibi) B+ ağacında daha iyi çalışır. Yazma ağırlıklı, sıralı akan bir veri (telemetri, günlük) LSM'de daha iyi çalışır. Aradaki farkı sayıyla görmek için şimdi bir LSM'yi kendin yazacaksın.

::: ipucu
Sık yapılan bir hata, LSM'nin "her zaman daha hızlı" olduğunu düşünmektir. LSM yazmayı hızlandırır ama okumayı ve alanı bedel olarak öder. Hangi tarafı seçtiğin, veri akışının hangi tarafının daha pahalı olduğuna bağlıdır.
:::

## 35.4 Kendi LSM deponu: memtable, SSTable, birleştirme, mezar taşı

Kavramı pekiştirmenin en iyi yolu, çalışan küçük bir sürümü yazmaktır. Aşağıdaki depo dört parçadan oluşur. **memtable** RAM'de bir sözlüktür. **SSTable** diskte, anahtara göre sıralı bir dosyadır; dosyalar bloklara bölünmüştür ve bellekte her bloğun ilk anahtarını gösteren bir **seyrek indeks** tutulur. Her SSTable'ın bir **Bloom filtresi** vardır (35.6). **Birleştirme**, birden çok SSTable'ı tek bir tabloda toplar. Silme ise anahtarı hemen diskten silmek yerine bir **mezar taşı** (tombstone) yazmakla yapılır.

Bu depo için önemli bir sadeleştirme yapıyoruz: WAL bu sürümde yok. Günlük ve kalıcılık, Kendin Yap Projesi 1'in konusu. Şimdilik memtable'ın RAM'de kaldığını ve dolunca dosyaya yazıldığını varsay.

LSM her SSTable için bir Bloom filtresi kullanır; filtrenin kodu ve formülü 35.6'da. Şimdilik onu "kesinlikle yok" diyebilen bir kutu olarak bil.

Aşağıdaki kod LSM'nin tamamını içerir. Önce `SSTable` sınıfına bakalım. Kurucu, sıralı kayıtları bloklara bölerek yazar ve her bloğun başlangıç ve bitiş ofsetini seyrek indekse koyar. Sorgu sırasında bir anahtar aranırken önce Bloom filtresine sorulur; "kesinlikle yok" cevabı gelirse dosyaya hiç dokunulmaz.

```python
# -*- coding: utf-8 -*-
"""Küçük LSM anahtar-değer deposu (Bölüm 35.4).

memtable (RAM, dict) -> flush -> SSTable (diskte sıralı dosya)
SSTable: bloklara bölünmüş, bellekte seyrek indeks + Bloom filtresi.
Silme: mezar taşı (değeri None olan kayıt). Birleştirme: tüm
tabloları tek tabloda toplar, en yeni kayıt kazanır, mezar taşları
(tüm tablolar birleştiğinde artık gizleyecek eski kayıt yoktur)
atılır.
WAL bu sürümde yok; Kendin Yap Projesi 1'de eklenecek.
"""
import bisect
import json
import os

from bloom import BloomFilter


class SSTable:
    BLOK = 16  # blok başına kayıt sayısı

    def __init__(self, yol, kayitlar, m, k, say):
        # kayitlar: anahtara göre sıralı [(anahtar, deger)]
        self.yol = yol
        self.bloom = BloomFilter(m, k)
        self.seyrek = []  # her blok için (ilk_anahtar, bas, son)
        bas = 0
        with open(yol, "wb") as f:
            for i, (anahtar, deger) in enumerate(kayitlar):
                if i % self.BLOK == 0:
                    if self.seyrek:
                        self.seyrek[-1][2] = f.tell()
                    self.seyrek.append([anahtar, f.tell(), None])
                f.write(json.dumps([anahtar, deger]).encode() + b"\n")
                self.bloom.ekle(anahtar)
            if self.seyrek:
                self.seyrek[-1][2] = f.tell()
        self.bayt = os.path.getsize(yol)
        self.ilk = [b[0] for b in self.seyrek]
        say["disk_yazma"] += self.bayt
```

Bu ilk parçada iki şey önemli. Birincisi, `SSTable` dosyayı `wb` (ikili yazma) kipinde açar; böylece `tell()` ile aldığımız ofsetler diskteki gerçek bayt konumlarıdır. Metin kipinde Windows'ta satır sonu dönüşümü ofsetleri kaydırabilir. İkincisi, her kayıt bir JSON dizisi olarak `[anahtar, değer]` biçiminde yazılır; değer `None` ise bu bir mezar taşıdır. Silinmiş bir anahtar ile hiç var olmamış bir anahtar, diskte farklı bir ize sahiptir; bu ayrım birleştirmede önemlidir.

```python

    def oku(self, anahtar, bloom_kullan, say):
        # Dönüş: None (tabloda yok) ya da (True, deger)
        if bloom_kullan and not self.bloom.icerir(anahtar):
            say["bloom_red"] += 1
            return None
        i = bisect.bisect_right(self.ilk, anahtar) - 1
        if i < 0:
            return None
        _, bas, son = self.seyrek[i]
        say["sorgu_disk_okuma"] += 1
        with open(self.yol, "rb") as f:
            f.seek(bas)
            veri = f.read(son - bas)
        for satir in veri.splitlines():
            k, v = json.loads(satir.decode())
            if k == anahtar:
                return (True, v)
        say["bloom_yanlis"] += 1  # filtre "var" dedi, yoktu
        return None

    def tum_kayitlar(self, say):
        say["birlestirme_okuma"] += self.bayt
        kayitlar = []
        with open(self.yol, "rb") as f:
            for satir in f.read().splitlines():
                k, v = json.loads(satir.decode())
                kayitlar.append((k, v))
        return kayitlar


class LSM:
    def __init__(self, dizin, esik=64, m=4096, k=4,
                 bloom_kullan=True):
        self.dizin = dizin
        os.makedirs(dizin, exist_ok=True)
        self.memtable = {}
        self.esik = esik
        self.m, self.k = m, k
        self.bloom_kullan = bloom_kullan
```

`oku` metodu, LSM'nin okuma yolunun özüdür. Bloom filtresi `False` derse işlem burada biter ve `bloom_red` sayacı artar. Filtre `True` derse seyrek indeksten doğru bloğu bulur ve yalnızca o bloğu okur. Bloğun içinde bulunamazsa bu bir **yanlış pozitiftir**: filtre "var" dedi ama yoktu. Bu sayaç, Bloom filtresinin gerçekten işe yarayıp yaramadığını ölçmemizi sağlar.

```python
        self.tablolar = []  # eskiden yeniye sıralı
        self.sira = 0
        self.say = {"kullanici": 0, "disk_yazma": 0,
                    "sorgu_disk_okuma": 0,
                    "bloom_red": 0, "bloom_yanlis": 0,
                    "birlestirme_okuma": 0}

    def put(self, anahtar, deger):
        self.say["kullanici"] += len(anahtar) + len(deger)
        self.memtable[anahtar] = deger
        self._kontrol()

    def sil(self, anahtar):
        self.say["kullanici"] += len(anahtar)
        self.memtable[anahtar] = None  # mezar taşı
        self._kontrol()

    def get(self, anahtar):
        if anahtar in self.memtable:
            return self.memtable[anahtar]
        for t in reversed(self.tablolar):  # en yeni tablo önce
            r = t.oku(anahtar, self.bloom_kullan, self.say)
            if r is not None:
                return r[1]
        return None

    def _kontrol(self):
        if len(self.memtable) >= self.esik:
            self.flush()

    def _yeni_tablo(self, kayitlar):
        yol = os.path.join(self.dizin, "%06d.sst" % self.sira)
        self.sira += 1
        return SSTable(yol, kayitlar, self.m, self.k, self.say)

    def flush(self):
        if not self.memtable:
            return
        kayitlar = sorted(self.memtable.items())
        self.tablolar.append(self._yeni_tablo(kayitlar))
```

`LSM` sınıfının `get` metodu, en yeni veriyi önce arar. Önce memtable'a bakar; yoksa tabloları en yeniden en eskiye doğru dolaşır. İlk eşleşme kazanır. Bu sıralama, aynı anahtarın birden çok tabloda bulunabileceği gerçeğinden gelir: bir anahtar önce 1 değeriyle, sonra 3 değeriyle yazılmış olabilir ve eski tablo hâlâ diskte duruyordur. Bu yüzden en yeni kayıt her zaman en önce gelir.

Silme de bir yazmadır. `sil` metodu anahtarı memtable'a `None` olarak koyar. `get` bu `None` değerini bulduğunda "silinmiş" olarak yorumlanır ve eski tablolardaki değer gizlenir. Mezar taşı, eski kopyayı hemen silemediğimiz için gerekli bir yer tutucudur.

```python
        self.memtable = {}

    def birlestir(self):
        self.flush()
        if len(self.tablolar) <= 1:
            return
        birlesik = {}
        for t in self.tablolar:  # eskiden yeniye: yeni olan kazanır
            for k, v in t.tum_kayitlar(self.say):
                birlesik[k] = v
        kayitlar = [(k, v) for k, v in sorted(birlesik.items())
                    if v is not None]
        for t in self.tablolar:
            os.remove(t.yol)
        self.tablolar = []
        if kayitlar:
            self.tablolar.append(self._yeni_tablo(kayitlar))

    def tablo_sayisi(self):
        return len(self.tablolar)
```

Birleştirme metodu, tüm tabloları eskiden yeniye sırayla okur ve bir sözlüğe yazar. Aynı anahtar birden çok kez gelirse sonraki (daha yeni) değer önceki değerin üstüne yazılır. Böylece en yeni kayıt kazanır. Son adımda `None` değerli kayıtlar filtrelenir: birleştirme tüm tabloları kapsadığı için, mezar taşının gizleyeceği eski bir kopya artık yoktur ve mezar taşı atılabilir. Bu koşulu bir kez daha düşün: eğer tüm tablolar birleştirilmemişse, mezar taşı atılamaz; çünkü onun gizlediği bir kopya hâlâ daha eski bir tabloda duruyor olabilir.

![Şekil 35.3: LSM seviyeleri: seviye 0'da aralıklar çakışır, birleştirme ile seviye 1'de ayrık ve sıralı tablolar oluşur.](gorseller/b35_lsm_seviye.png)

Şekil 35.3, bu üç katmanı (memtable, seviye 0, seviye 1) ve birleştirmenin yönünü gösteriyor. Seviye 0'daki tablolar birbirinin aralığına girebilir; bu yüzden okuma hepsine bakmak zorundadır. Seviye 1'deki tablolar ise ayrık ve sıralıdır. Birleştirme, seviye 0'ı sıralı ve ayrık bir hâle getirir.

Şimdi bu kodun doğru çalışıp çalışmadığını sınamalıyız. Bir veritabanını test etmenin en sağlam yolu, **kendi yavaş ama doğru referansıyla** karşılaştırmaktır. Referans bir Python `dict`idir: her işlemi hem LSM'ye hem sözlüğe uygularız ve her okumada iki cevabın eşit olup olmadığına bakarız. Rastgele işlemler sabit bir tohumla üretilir; böylece aynı dizi her çalıştırmada aynı olur.

```python
# -*- coding: utf-8 -*-
"""LSM deposunu dict modeline karşı test eder ve ölçüm yapar."""
import random
import shutil
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lsm import LSM

KOK = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "_dizin")


def dizin(ad):
    yol = os.path.join(KOK, ad)
    shutil.rmtree(yol, ignore_errors=True)
    return yol


def rastgele_islemler(seed, adet, anahtar_say):
    rnd = random.Random(seed)
    for _ in range(adet):
        k = "k%04d" % rnd.randrange(anahtar_say)
        r = rnd.random()
        if r < 0.55:
            yield ("put", k, "v%d" % rnd.randrange(10 ** 6))
        elif r < 0.75:
            yield ("sil", k, None)
        else:
```

Test fonksiyonu, 20 000 rastgele işlemden oluşan bir dizi üretir: %55 yazma, %20 silme, %25 okuma. Anahtar uzayı yalnızca 400 anahtardır, böylece aynı anahtarlar sık sık yeniden yazılır ve silinir; bu, yeniden yazma ve mezar taşı mantığını zorlar.

```python
            yield ("get", k, None)


def model_karsilastir(seed, adet=20000):
    # esik küçük: sık flush, sık birleştirme; bloom açık
    db = LSM(dizin("tst_%d" % seed), esik=50, m=2048, k=4)
    model = {}
    hata = 0
    kontrol = 0
    islemler = rastgele_islemler(seed, adet, 400)
    for i, (op, k, v) in enumerate(islemler):
        if op == "put":
            db.put(k, v)
            model[k] = v
        elif op == "sil":
            db.sil(k)
            model.pop(k, None)
        else:
            kontrol += 1
            if db.get(k) != model.get(k):
                hata += 1
        if i % 2500 == 2499 and i != adet - 1:
            db.birlestir()
    # son tam karşılaştırma
    for k in sorted({"k%04d" % j for j in range(400)}):
        kontrol += 1
        if db.get(k) != model.get(k):
            hata += 1
    return hata, kontrol, db.tablo_sayisi()
```

Bu parçada iki kritik ayrıntı var. Küçük bir eşik (`esik=50`) sık sık flush yapar, böylece birçok SSTable oluşur. Her 2500 işlemde bir birleştirme yapılır, ama son işlemde yapılmaz: böylece test sonunda birden çok tablo varken de tüm anahtarlar kontrol edilir. Son döngü her anahtarı bir kez daha karşılaştırır.

```term
== Model karşılaştırması (dict modeline karşı) ==
tohum 1: kontrol=5371 hata=0 son_tablo=35
tohum 2: kontrol=5308 hata=0 son_tablo=36
tohum 3: kontrol=5369 hata=0 son_tablo=36
tohum 4: kontrol=5406 hata=0 son_tablo=35
tohum 5: kontrol=5401 hata=0 son_tablo=36
Toplam hata: 0

== Yazma yükseltmesi ==
kullanıcı bayt      : 520000
flush ile diske     : 680960  (tablo=76)
birleştirme sonrası : 855295  (tablo=1)
yazma yük. (önce)   : 1.31
yazma yük. (sonra)  : 1.64

== Okuma yükseltmesi: var olmayan anahtar ==
bloom=1  sorgu başına disk okuma=1.683  tablo=77  bloom_red=150633
bloom=0  sorgu başına disk okuma=77.000  tablo=77  bloom_red=0
```

Çıktı, beş farklı tohumun her birinde 0 hata verdiğini gösteriyor. Toplam kontrol sayısı 26 855: bu, okuma işlemleri ile son tam taramanın toplamıdır. Son tablo sayısının 35-36 olması, test sonunda çok sayıda tablo olduğunu, yani okuma yolunun gerçekten birden çok dosyaya baktığını gösterir.

Bu test tek başına bir "kanıt" değildir; hata bulamamak, hata olmadığını göstermez. Testin gerçekten hata yakalayıp yakalamadığını görmek için bilerek hatalı bir birleştirme yazdık: birleştirmede eskiden yeniye değil, yeniden eskiye okuyan ve böylece eski değeri tutan bir sürüm. Bu hatalı sürümde test **4 377** hata buldu. Testin hatayı yakalayabildiğini bu sayı gösteriyor. Mutasyon betiği arşivdedir (`mutasyon.py`).

## 35.5 Yükseltme (amplification) ve kendi deponda ölçüm

Depolama motorlarını karşılaştırmanın standart dili **yükseltme** (amplification) kavramıdır. Bir kullanıcı işlemi, diskte olması gerekenden fazla iş üretebilir. Bu fazlalığın oranına yükseltme denir ve üç türü vardır.

**Yazma yükseltmesi (write amplification)**: kullanıcının yazdığı bayt başına diske yazılan toplam bayt. Flush, birleştirme ve günlük yazmaları hepsi bu toplama girer. **Okuma yükseltmesi (read amplification)**: bir okuma için diskte kaç sayfa ya da dosya okunduğu. **Alan yükseltmesi (space amplification)**: diskte tutulan toplam bayt ile kullanıcının fiilen tuttuğu verinin oranı; eski kopyalar ve mezar taşları bu alanı şişirir.

Bu üç yükseltme birbirinin karşısındadır. Birleştirmeyi sık yaparsan okuma yükseltmesi düşer (az dosya okursun) ama yazma yükseltmesi artar (aynı veriyi tekrar tekrar yazarsın). Birleştirmeyi seyrek yaparsan yazma ucuzlar ama okuma ve alan pahalılaşır. Genel bir sonuç olarak bu üç ölçütü aynı anda en iyi yapan bir ayar yoktur (genel bilgi: bu, RUM konjektürü olarak bilinir).

Şimdi bunu kendi deponda ölç. Ölçüm için 20 000 yazma yapıyoruz; anahtarlar 0 ile 4999 arasında rastgele seçiliyor ve her değer 20 baytlık. Eşik 256 kayıt. Önce flush sonrasındaki yazma toplamını, sonra tam birleştirmeden sonrakini alıyoruz.

```python

def yukseltme_olcumu():
    rnd = random.Random(35)
    db = LSM(dizin("olcum"), esik=256, m=1 << 17, k=7)
    for _ in range(20000):
        k = "k%05d" % rnd.randrange(5000)
        db.put(k, "x" * 20)
    yaz_once = db.say["disk_yazma"]
    kul = db.say["kullanici"]
    tablo_once = db.tablo_sayisi()
    db.birlestir()
    yaz_sonra = db.say["disk_yazma"]
    return {"kullanici": kul, "flush_yazma": yaz_once,
            "birlestirme_sonra": yaz_sonra, "tablo_once": tablo_once,
            "tablo_sonra": db.tablo_sayisi(),
            "wa_once": yaz_once / kul, "wa_sonra": yaz_sonra / kul}


def okuma_olcumu(bloom):
    rnd = random.Random(35)
    db = LSM(dizin("okuma_%d" % bloom), esik=256, m=1 << 11, k=6,
             bloom_kullan=bool(bloom))
    for _ in range(20000):
        db.put("k%05d" % rnd.randrange(20000), "x" * 20)
    db.say["sorgu_disk_okuma"] = 0
    db.say["bloom_red"] = 0
    sorgu = 2000
    for _ in range(sorgu):  # yalnızca YOK olan anahtarlar
        db.get("y%05d" % rnd.randrange(10 ** 5))
    return db.say["sorgu_disk_okuma"] / sorgu, db.tablo_sayisi(), \
```

Okuma yükseltmesini ölçmek için ayrı bir deneme yapıyoruz: 20 000 yazmadan sonra, **yalnızca var olmayan** 2000 anahtar sorguluyoruz. Burada her sorgunun diskte kaç tablo bloğu okuduğunu sayıyoruz. Bloom filtresini iki kez çalıştırıyoruz: bir kez açık, bir kez kapalı.

```python
        db.say["bloom_red"]


if __name__ == "__main__":
    print("== Model karşılaştırması (dict modeline karşı) ==")
    toplam_hata = 0
    for seed in range(1, 6):
        hata, kont, tab = model_karsilastir(seed)
        toplam_hata += hata
        print("tohum %d: kontrol=%d hata=%d son_tablo=%d"
              % (seed, kont, hata, tab))
    print("Toplam hata:", toplam_hata)

    print("\n== Yazma yükseltmesi ==")
    y = yukseltme_olcumu()
    print("kullanıcı bayt      : %d" % y["kullanici"])
    print("flush ile diske     : %d  (tablo=%d)"
          % (y["flush_yazma"], y["tablo_once"]))
    print("birleştirme sonrası : %d  (tablo=%d)"
          % (y["birlestirme_sonra"], y["tablo_sonra"]))
    print("yazma yük. (önce)   : %.2f" % y["wa_once"])
    print("yazma yük. (sonra)  : %.2f" % y["wa_sonra"])

    print("\n== Okuma yükseltmesi: var olmayan anahtar ==")
    for b in (1, 0):
        r, tab, red = okuma_olcumu(b)
        print("bloom=%d  sorgu başına disk okuma=%.3f  tablo=%d  "
              "bloom_red=%d" % (b, r, tab, red))
    shutil.rmtree(KOK, ignore_errors=True)
```

```term
== Model karşılaştırması (dict modeline karşı) ==
tohum 1: kontrol=5371 hata=0 son_tablo=35
tohum 2: kontrol=5308 hata=0 son_tablo=36
tohum 3: kontrol=5369 hata=0 son_tablo=36
tohum 4: kontrol=5406 hata=0 son_tablo=35
tohum 5: kontrol=5401 hata=0 son_tablo=36
Toplam hata: 0

== Yazma yükseltmesi ==
kullanıcı bayt      : 520000
flush ile diske     : 680960  (tablo=76)
birleştirme sonrası : 855295  (tablo=1)
yazma yük. (önce)   : 1.31
yazma yük. (sonra)  : 1.64

== Okuma yükseltmesi: var olmayan anahtar ==
bloom=1  sorgu başına disk okuma=1.683  tablo=77  bloom_red=150633
bloom=0  sorgu başına disk okuma=77.000  tablo=77  bloom_red=0
```

Son üç satır ölçümlerin özüdür. Yazma yükseltmesi, birleştirme öncesinde 1,31 (680 960 / 520 000) iken birleştirmeden sonra 1,64 (855 295 / 520 000) oluyor: birleştirme, yazılan toplam bayt sayısını artırıyor çünkü her tabloyu yeniden yazıyor. Bu, LSM'nin temel bedelidir. Kullanıcı tek bir bayt yazsa da birleştirmeler bu baytı defalarca diske taşır.

Okuma yükseltmesi ise çarpıcı. Bloom filtresi kapalıyken her "yok" sorgusu 77 tablo okuyor (birleştirme öncesinde 77 tablo vardı). Filtre açıkken aynı sorgu ortalama 1,683 disk okuması yapıyor. Bu, filtrenin 77 tablodan yalnızca birkaçına gitmek zorunda kaldığı anlamına gelir. Sayının neden 1,66 civarında olması gerektiğini bir sonraki bölümde, Bloom formülüyle hesaplayacağız.

Bu ölçümlerin ne gösterdiğini dürüstçe söylemek gerekir: sayılar Python ile yazılmış ve disk yerine dosya işletim sisteminin önbelleğinden okunan küçük bir depodan geliyor. Gerçek bir veritabanında mutlak süreler çok farklı olur. Ama **oranlar ve yön** (birleştirme yazmayı artırır, filtre okumayı azaltır) her LSM'de geçerlidir.

## 35.6 Bloom filtresi: formül ve ölçüm

Bloom filtresi, 1970'te Burton Bloom'un tanıttığı olasılıksal bir üyelik yapısıdır (genel bilgi). Bir kümenin elemanlarını bir bit dizisinde tutar ve bir sorguya iki türlü cevap verir: "**kesinlikle yok**" ya da "**muhtemelen var**". Bu asimetri her şeydir: "yok" cevabı kesindir, "var" cevabı yanlış olabilir. Yanlış negatif (var olan bir şeyi yok demek) hiç olmaz; yalnızca yanlış pozitif (yok olan bir şeye var demek) olabilir.

Mekanizma basittir. Bir dizi `m` bit, `k` tane bağımsız hash fonksiyonu. Bir eleman eklendiğinde `k` hash değeri hesaplanır ve her biri bir bit olarak açılır. Bir eleman sorulduğunda aynı `k` konuma bakılır: hepsi 1 ise "muhtemelen var", herhangi biri 0 ise "kesinlikle yok". Bit silinemez, çünkü aynı bit başka elemanlar için de açık olabilir.

![Şekil 35.4: Bloom filtresi bit dizisi: 0 gören sorgu kesinlikle yok der; D sorgusu tüm bitleri 1 gördüğü için yanlış pozitiftir.](gorseller/b35_bloom_bit.png)

Şekil 35.4'te bu mekanizma bir dizi üzerinde görülüyor. A ve B eklenmiş; A'nın bitleri 1, 6, 13, B'ninki 3, 6, 11. Sorgu C'nin 2. biti 0: C kesinlikle yok. Sorgu D'nin bitleri 3, 6, 13 ve üçü de 1: D muhtemelen var, ama aslında yok. Bit 6 iki elemanın ortak bitidir; bu paylaşım yanlış pozitifin kaynağıdır.

Yanlış pozitif oranı için standart formül şudur (`n` eklenen eleman sayısı):

`p = (1 - e^(-k n / m))^k`

Bu formülün arkasındaki sezgi şudur: bir bit tek bir eleman için **açılmamış** kalma olasılığı `1 - 1/m`'dir; `k` hash ve `n` eleman için bu `(1 - 1/m)^(kn)` yaklaşık `e^(-kn/m)` olur. Bir sorgunun yanlış pozitif olması için `k` bitin **hepsinin** açık olması gerekir; bu da `(1 - e^(-kn/m))^k` verir.

Bu formülden iki sonuç çıkar. Birincisi, `k` için bir optimum vardır. Çok az hash fonksiyonu bitleri yeterince doldurmaz; çok fazlası bit dizisini aşırı doldurur. Optimum `k = (m/n) ln 2` civarındadır (ayrıntısı için ilerideki Kod Okuma'ya bak). İkincisi, belirli bir hedef yanlış pozitif oranı için gereken bit sayısı şuna eşittir: `m = -n ln p / (ln 2)^2`. Bu, eleman başına yaklaşık 9,6 bit demektir; %1 hedef için.

Formülü kendi filtremizle sınamak için, `n = 10 000` elemanı ekleyip `100 000` var olmayan anahtarı sorguluyoruz. `m/n` oranını 4, 8, 10 ve 16 olarak, `k`'yı 1'den 10'a kadar değiştiriyoruz. Teorik değerle ölçülen değeri yan yana koyuyoruz.

```python
# -*- coding: utf-8 -*-
"""Bloom filtresi: m bit, k hash fonksiyonu (Bölüm 35.6)."""
import hashlib
import math


class BloomFilter:
    def __init__(self, m, k):
        self.m = m
        self.k = k
        self.bitler = bytearray((m + 7) // 8)

    def _konumlar(self, anahtar):
        # Tek bir 128 bitlik özetten iki hash üret (çift hash):
        # h_i = (h1 + i * h2) mod m. Kirsch-Mitzenmacher tekniği.
        ozet = hashlib.blake2b(anahtar.encode("utf-8"),
                               digest_size=16).digest()
        h1 = int.from_bytes(ozet[:8], "little")
        h2 = int.from_bytes(ozet[8:], "little") | 1
        return [(h1 + i * h2) % self.m for i in range(self.k)]

    def ekle(self, anahtar):
        for p in self._konumlar(anahtar):
            self.bitler[p >> 3] |= 1 << (p & 7)

    def icerir(self, anahtar):
        # False: kesinlikle yok. True: muhtemelen var.
        for p in self._konumlar(anahtar):
            if not (self.bitler[p >> 3] >> (p & 7)) & 1:
                return False
        return True


def teorik_yanlis_pozitif(m, n, k):
    return (1.0 - math.exp(-k * n / m)) ** k


def optimal_k(m, n):
    return max(1, round((m / n) * math.log(2)))
```

Bu sınıf LSM'deki ile aynı; burada yalnızca `teorik_yanlis_pozitif` ve `optimal_k` yardımcıları var. Hash olarak BLAKE2b kullanıyoruz ve tek bir 128 bitlik özetten iki hash üretip `h1 + i * h2` ile `k` konum türetiyoruz. Bu çift hash tekniği Kirsch ve Mitzenmacher'in 2006 analizine dayanır; böylece her eleman için tek bir hash hesabı yeter.

```python
# -*- coding: utf-8 -*-
"""Bloom filtresi: teorik ve gözlenen yanlış pozitif oranı (Bölüm
35.6).
Tohum: 35. Çıktı: engine/veri/b35_bloom.csv"""
import csv
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bloom import BloomFilter, teorik_yanlis_pozitif, optimal_k

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
N = 10000
SORGU = 100000


def olc(m, k, rnd):
    bf = BloomFilter(m, k)
    for i in range(N):
        bf.ekle("anahtar-%d" % i)
    yanlis = 0
    for j in range(SORGU):
        if bf.icerir("yok-%d" % j):
            yanlis += 1
    return yanlis / SORGU
```

```python
if __name__ == "__main__":
    rnd = random.Random(35)
    satirlar = []
    print("m/n  k   teorik      olculen     (n=%d, sorgu=%d)"
          % (N, SORGU))
    for oran in (4, 8, 10, 16):
        m = oran * N
        kopt = optimal_k(m, N)
        for k in range(1, 11):
            t = teorik_yanlis_pozitif(m, N, k)
            o = olc(m, k, rnd)
            satirlar.append([oran, k, N, SORGU,
                             "%.6f" % t, "%.6f" % o])
            if k == kopt or k in (1, 4, 10):
                print("%-4d %-3d %.6f    %.6f%s" % (oran, k, t, o,
                      "   <- optimal" if k == kopt else ""))
    with open(os.path.join(VERI, "b35_bloom.csv"), "w",
              encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["m_n", "k", "n", "sorgu", "teorik", "olculen"])
        w.writerows(satirlar)
    print("CSV yazildi:", len(satirlar), "satir")
```

```term
m/n  k   teorik      olculen     (n=10000, sorgu=100000)
4    1   0.221199    0.218030
4    3   0.146892    0.148470   <- optimal
4    4   0.159661    0.159430
4    10  0.424644    0.418210
8    1   0.117503    0.116690
8    4   0.023969    0.023990
8    6   0.021577    0.021560   <- optimal
8    10  0.034191    0.034610
10   1   0.095163    0.094760
10   4   0.011813    0.012100
10   7   0.008194    0.008210   <- optimal
10   10  0.010186    0.010640
16   1   0.060587    0.060780
16   4   0.002394    0.002440
16   10  0.000470    0.000410
CSV yazildi: 40 satir
```

Çıktıda her `m/n` için teorik ve ölçülen değerler yan yana. Örneğin `m/n = 10` ve `k = 7` (optimum) için teorik 0,008194, ölçülen 0,008210; fark binde birin altında. `m/n = 8` ve `k = 6` için 0,021577'ye karşı 0,021560. Tabloda yalnızca optimum ve `k = 1, 4, 10` satırları yazılıyor; tam tablo `engine/veri/b35_bloom.csv` dosyasında 40 satır olarak duruyor ve Şekil 35.5'te çizildi.

![Şekil 35.5: Bloom yanlış pozitif oranı: teorik eğriler ve 100 000 sorguluk ölçümler (n = 10 000).](gorseller/b35_bloom_olcum.png)

Şekil 35.5, yanlış pozitif oranının `k` ile nasıl değiştiğini gösteriyor. Her eğri bir `m/n` oranına ait; düz çizgi teori, nokta ölçüm. Eğriler önce düşüyor, sonra yükseliyor: bu, optimumun varlığının görsel kanıtı. Ayrıca `m/n` büyüdükçe tüm eğrilerin aşağı indiğini görüyorsun: birim eleman başına daha fazla bit, daha az hata demek.

Bu bölümde bir dengeyi bilinçli olarak gördük: Bloom filtresi **bellek** karşılığında **sorgu süresi** verir. LSM örneğinde bunun karşılığı, 77 tablodan 1,7 okumaya inmekti. Ters yönde ise bir filtrenin hafızada tutulması gerekir; bu da büyük kümelerde bellek bütçesini belirler.

::: baglanti
Bloom filtresi hash tekniğinin bir uygulamasıdır. Hash tablosunda çakışmayı zincirle ya da açık adresleme ile çözdüğün Bölüm 9'daki kavramlar burada da geçerli: iyi bir hash fonksiyonu, bitlerin düzgün dağılmasını sağlar. Farkı ise Bloom filtresinin eleman saklamamasıdır; bu yüzden hem daha az bellek kullanır hem de silinemez.
:::

## 35.7 Dağıtık temeller: çoğaltma, bölümleme ve tutarlı hash

Tek bir makinedeki depo, makinenin çökmesiyle birlikte çöker. Dağıtık sistemde iki soru kaçınılmaz olur: aynı veri birden çok makinede **kopyalansın mı** (çoğaltma, replication) ve veri makineler arasında **bölünsün mü** (bölümleme, partitioning)? Üç çoğaltma modeli ve iki bölümleme yöntemi vardır.

**Lider-takipçi** (leader-follower, master-slave): tüm yazmalar tek bir lider üzerinden geçer; lider değişikliği takipçilere iletir. Okumalar takipçilerden yapılabilir. Basittir ve yazma sırası nettir, ama lider tek nokta hatasıdır ve okumalar takipçinin gerisinde kalabilir.

**Çok lider** (multi-leader): birden çok veri merkezinde her biri yazma kabul eder. Coğrafi gecikmeyi azaltır, ama aynı anahtara iki yerde farklı değer yazılabilir ve bu bir **çakışma** (conflict) yaratır. Çakışma çözümü (son yazma kazanır, birleştirme, uygulamaya bırakma) ayrı ve zor bir konudur.

**Lidersiz** (leaderless): hiçbir kopya özel değildir; istemci yazmayı `W` kopyaya, okumayı `R` kopyaya gönderir. Dynamo (2007) ve ondan esinlenen sistemler bu modeli kullanır (genel bilgi). Tutarlılık, `R` ve `W` sayılarının seçimiyle ayarlanır (35.8).

![Şekil 35.6: Çoğaltma modelleri: lider-takipçi, çok lider ve lidersiz.](gorseller/b35_cogaltma.png)

Şekil 35.6 üç modeli yan yana gösteriyor. Lider-takipçide yazmanın tek kapıdan geçtiğine, çok liderde iki lider arasında çakışma riskinin doğduğuna, lidersizde ise istemcinin birden çok kopyaya doğrudan yazdığına dikkat et.

Bölümleme, veriyi makinelere dağıtmaktır. Anahtar aralığına göre bölümlemede (örneğin A-F, G-M, N-Z) aralık sorguları verimlidir, ama sıcak bir anahtar aralığı bir makineyi boğabilir. Hash ile bölümlemede anahtar bir hash fonksiyonundan geçer ve yük düzgün dağılır, ama aralık sorgusu tüm makinelere dağılır.

Burada bir sorun doğar. Düğümler arasında `hash(anahtar) % N` ile bölümleme yaparsan, `N` değiştiğinde (bir düğüm eklersin ya da çıkarırsın) neredeyse her anahtar başka bir düğüme gider. Bu, büyük bir veri taşıma demektir. **Tutarlı hash** (consistent hashing) bu sorunu çözer: hash değerlerini bir halkaya yerleştirir, her anahtarı saat yönünde ilk düğüme atar. Düğüm eklendiğinde yalnızca yeni düğümün halkadaki komşusundan bazı anahtarlar taşınır.

![Şekil 35.7: Tutarlı hash halkası: sanal düğümler ve anahtarların saat yönünde ilk düğüme atanması.](gorseller/b35_halka.png)

Şekil 35.7'de halka görülüyor. Her düğüm halkada birden çok **sanal düğüm** (virtual node) olarak yer alır: A'nın iki sanal kopyası A1 ve A2. Sanal düğümler, birkaç fiziksel düğümün halkada daha düzgün dağılmasını sağlar. Anahtar `k1` halkada A1'in biraz altında; saat yönünde ilk sanal düğüm A1 olduğu için sahibi A. `k2` D2'nin önünde; sahibi D. Bu kural her anahtar için aynıdır ve halkada yalnızca yerel bir değişiklik düğüm eklemeyi etkiler.

Bu fikri sınamak için 100 000 anahtarı 10 düğüme dağıttık, sonra 11. düğüm ekledik ve kaç anahtarın taşındığını saydık. Karşılaştırma: naif `hash % N` ve tutarlı halka, sanal düğüm sayısı `v` ∈ {1, 10, 40, 100, 200}. İdeal taşınma oranı, yeni düğümün payı olan `1/11 ≈ 0,0909`'dur: düğümler eşit yükte olsaydı yeni düğüm bu kadar anahtar alırdı ve başka hiçbir anahtar taşınmazdı.

```python
# -*- coding: utf-8 -*-
"""Naif hash % N ile tutarlı hash halkasını karşılaştırır (Bölüm
35.7).
Tohum yok: anahtarlar deterministik. Çıktı:
engine/veri/b35_tutarli_hash.csv
"""
import bisect
import csv
import hashlib
import statistics

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
ANAHTAR = 100000


def h32(metin):
    return int.from_bytes(hashlib.blake2b(metin.encode(),
                                          digest_size=8).digest()[:4],
                          "little")


KEYS = ["anahtar-%06d" % i for i in range(ANAHTAR)]


class Halka:
    def __init__(self, dugumler, v):
        self.v = v
        self.nokta = []  # (konum, dugum)
        for d in dugumler:
            self.dugum_ekle(d)

    def dugum_ekle(self, d):
        for i in range(self.v):
            self.nokta.append((h32("%s#%d" % (d, i)), d))
        self.nokta.sort()

    def dugum_sil(self, d):
        self.nokta = [p for p in self.nokta if p[1] != d]

    def sahip(self, anahtar):
```

Halka sınıfı `dugum_ekle` ile her fiziksel düğüm için `v` sanal konum hesaplar ve listeyi sıralı tutar. `sahip` metodu bir anahtarın hash değerini alır ve `bisect` ile listedeki ilk büyük konumu bulur; listenin sonundaysa halkayı sarar (en küçük konuma döner). Bu, bir arama işlemidir ve `O(log n)` sürer; `n` burada toplam sanal düğüm sayısıdır.

```python
        konum = h32(anahtar)
        i = bisect.bisect_right(self.nokta, (konum, "\uffff"))
        if i == len(self.nokta):
            i = 0  # halkayı tamamla: en küçük konuma dön
        return self.nokta[i][1]


def naif(anahtar, n):
    return h32(anahtar) % n


def dugumler(n):
    return ["dugum-%02d" % i for i in range(n)]


def yuk_cv(sahipler, n):
    sayac = {}
    for s in sahipler:
        sayac[s] = sayac.get(s, 0) + 1
    degerler = [sayac.get(d, 0) for d in dugumler(n)]
    ort = statistics.mean(degerler)
    return statistics.pstdev(degerler) / ort


def tasinan_naif(n):
    once = [naif(k, n) for k in KEYS]
    sonra = [naif(k, n + 1) for k in KEYS]
    return sum(1 for a, b in zip(once, sonra) if a != b) / ANAHTAR


def tasinan_halka(v, n):
    once = Halka(dugumler(n), v)
    sahip_once = [once.sahip(k) for k in KEYS]
    yeni = dugumler(n + 1)[-1]
    sonra_h = Halka(dugumler(n + 1), v)
    sahip_sonra = [sonra_h.sahip(k) for k in KEYS]
    tasinan = 0
    for a, b in zip(sahip_once, sahip_sonra):
        if a != b:
            tasinan += 1
```

`tasinan_halka` fonksiyonu iki halka kurar: biri 10, biri 11 düğümle. Her anahtarın sahibi değiştiyse taşınmış sayılır. Bir `assert` de koyduk: taşınan her anahtarın **yeni** düğüme gittiğini doğruluyoruz. Eğer yeni düğüm dışında bir yere gidiyorsa halka mantığı bozulmuş demektir.

```python
            # kanıt: taşınan her anahtar YENİ düğüme gitmeli
            assert b == yeni, "beklenmeyen taşıma"
    return tasinan / ANAHTAR


if __name__ == "__main__":
    satirlar = []
    print("Anahtar sayısı: %d, düğüm: 10 -> 11" % ANAHTAR)
    t_naif = tasinan_naif(10)
    print("naif hash%%N   taşınan oranı: %.4f  (ideal 1/11 = %.4f)"
          % (t_naif, 1 / 11))
    satirlar.append(["naif", 1, 10, 11, "%.6f" % t_naif,
                     "%.6f" % (1 / 11), "%.4f" % yuk_cv(
                         ["dugum-%02d" % naif(k, 10) for k in KEYS],
                         10)])
    for v in (1, 10, 40, 100, 200):
        t = tasinan_halka(v, 10)
        sahipler = [Halka(dugumler(10), v).sahip(k) for k in KEYS]
        cv = yuk_cv(sahipler, 10)
        print("halka v=%-4d taşınan=%.4f  "
              "yük_cv=%.4f" % (v, t, cv))
        satirlar.append(["halka", v, 10, 11, "%.6f" % t,
                         "%.6f" % (1 / 11), "%.4f" % cv])
    naif_sahip = ["dugum-%02d" % naif(k, 10) for k in KEYS]
    print("naif yük_cv = %.4f" % yuk_cv(naif_sahip, 10))
    with open(VERI + "/b35_tutarli_hash.csv", "w", encoding="utf-8",
              newline="") as f:
        w = csv.writer(f)
        w.writerow(["yontem", "vnode", "n_once", "n_sonra", "tasinan",
                    "ideal", "yuk_cv"])
        w.writerows(satirlar)
    print("CSV yazildı")
```

```term
Anahtar sayısı: 100000, düğüm: 10 -> 11
naif hash%N   taşınan oranı: 0.9103  (ideal 1/11 = 0.0909)
halka v=1    taşınan=0.0074  yük_cv=0.7693
halka v=10   taşınan=0.0788  yük_cv=0.2800
halka v=40   taşınan=0.0813  yük_cv=0.1149
halka v=100  taşınan=0.0925  yük_cv=0.0723
halka v=200  taşınan=0.0890  yük_cv=0.0509
naif yük_cv = 0.0123
CSV yazildı
```

Sonuçlar çarpıcı. Naif `hash % N` yönteminde anahtarların **%91,03**'ü taşınıyor; ideal oran %9,09 iken bu, on kattan fazla. Tutarlı halkada `v = 1` ile taşınma 0,0074, `v = 10` ile 0,0788, `v = 100` ile 0,0925, `v = 200` ile 0,0890. Yani sanal düğüm sayısı yeterince büyüdüğünde taşınma ideal orana yaklaşıyor.

Ama yük dengesi ayrı bir hikâye. Sütunlardaki yük CV'si (standart sapma / ortalama; düşük iyi) `v = 1` için 0,7693: tek konumlu düğümler halkada büyük bir yay alabiliyor, bazıları neredeyse hiç anahtar almıyor. `v` arttıkça CV 0,0509'a iniyor (`v = 200`). Naif `hash % N` yönteminin CV'si ise 0,0123: en dengeli yöntem o, ama en çok taşıyan da o. Tutarlı hash bu iki sorunu sanal düğüm sayısıyla dengeler: `v` büyük seçilirse hem taşınma hem yük dengesi iyi olur; bedeli halkanın daha büyük olması ve arama maliyetinin biraz artmasıdır.

![Şekil 35.8: Düğüm eklemede taşınan anahtar oranı (solda) ve yük dengesi (sağda, CV); 100 000 anahtar.](gorseller/b35_tasinan.png)

Şekil 35.8 aynı sonucu iki panelde veriyor: solda taşınan oran (kesikli çizgi ideal), sağda yük CV'si. Naif yöntemin solda devasa, sağda ise en küçük çubuk olduğunu görüyorsun.

Gerçek sistemlerde bu tekniği kullanan bir sistem düğüm çıkarma ve yük dengesi için de aynı mantığa dayanır; burada yalnızca ekleme ölçtük, çıkarma simetriktir: yalnızca çıkarılan düğümün anahtarları komşulara taşınır (genel bilgi). Bölüm 41'de bu bileşenin büyük bir sistemin tasarımında nasıl yer aldığını göreceksin.

## 35.8 Tutarlılık: CAP, PACELC, quorum ve Raft'a bakış

Çoğaltma ve bölümleme dağıtık bir sistemi kurar; ama kopyalar arasında veri tutarlı mı? Bu, dağıtık sistemlerde en çok yanlış anlaşılan konudur. Önce bir terim netleştirelim: **tutarlılık** (consistency) bu bağlamda, bir okumanın hangi yazmayı görebileceğini tanımlayan bir sözleşmedir; ACID'deki C ile aynı şey değildir.

**CAP teoremi.** Brewer 2000'de bir konferansta, Gilbert ve Lynch da 2002'de bir kanıtla bunu formalize etti (genel bilgi). Teoremin doğru ifadesi şudur: bir ağ **bölünmesi** (partition) olduğunda, bir sistem ya **tutarlılık** (her okuma en son yazmayı görür) ya da **erişilebilirlik** (her istek bir yanıt alır) seçmek zorundadır; ikisini birden garanti edemez. Sık yapılan yanlış yorumlar: "CAP'te her zaman C ya da A seçersin" (hayır; bölünme yoksa ikisi birlikte olabilir), "P bir seçimdir" (hayır; ağ bölünmesi gerçekte olur, yalnızca nasıl davranacağını seçersin), "CA sistemler vardır" (dağıtık bir sistemde bölünme olduğunda CA diye bir şey yoktur).

**PACELC.** Abadi'nin önerisi CAP'in eksik kısmını tamamlar (genel bilgi): bölünme yokken (Else) bile bir **gecikme** (Latency) ile **tutarlılık** (Consistency) arasında bir seçim vardır. Bir yazmayı üç kopyaya kadar bekletmek tutarlılığı artırır ama gecikmeyi büyütür. Pratikte çoğu zaman sorun bu ikinci dengedir.

**Tutarlılık modelleri.** Güçlü tutarlılık (linearizability) her okumanın en son yazmayı görmesini ister: sistem tek bir kopya gibi davranır. Nihai tutarlılık (eventual consistency) ise yazmalar durduğunda kopyaların zamanla aynı değere yakınsayacağını söyler, ama anlık okumada bayat değer görebilirsin. Oku-yazdığını-oku (read-your-writes) tutarlılığı, bir kullanıcının kendi yazdığını hemen görmesini garanti eder ama diğer kullanıcıların bayat görmesine izin verir. Bu modeller bir hiyerarşi oluşturur ve her biri farklı bir gecikme-doğruluk dengesidir.

**Quorum: R + W > N.** Lidersiz bir sistemde `N` kopya olsun. Bir yazma `W` kopyaya ulaşınca tamam sayılır, bir okuma `R` kopyadan veri alır ve en yeni sürümü döndürür. Eğer `R + W > N` ise okuma kümesi ile yazma kümesi **en az bir kopyada kesişir** (kutu ilkesi): okuma en az bir tane en yeni kopyayı görür. Bu, bayat okumayı engeller; ama önemli bir uyarı var: bu yalnızca kopyalar sürümü doğru tutuyorsa işe yarar. Kesişim garantisi, sürüm çatışmasını (vektör saatleri) ya da kopyaların onarımını çözmez.

Şimdi bunu sayıyla görelim. `N = 3` kopya, farklı `(R, W)` çiftleri için bir yazma tamamlandıktan **hemen sonra** yapılan bir okumanın bayat olma olasılığını hesaplıyoruz. Model şöyle: yazma `W` kopyaya gider; okuma `R` rastgele kopyadan okur; okunan kopyaların hiçbiri yazılmış kopyalardan biri değilse bayat okuma olur. Bu durumda olasılık `C(N-W, R) / C(N, R)`'dir. Simülasyon bunu 200 000 denemeyle doğruluyor.

```python
# -*- coding: utf-8 -*-
"""Quorum (R, W, N=3): bayat okuma olasılığı (Bölüm 35.8).
Model: bir yazma W kopyaya ulaşınca tamamlanmış sayılır. Ardından
hemen bir okuma R rastgele kopyadan okur ve en yüksek sürümü alır.
Bayat okuma: okunan en yüksek sürüm, tamamlanmış yazmadan eski.
Tohum: 35. Çıktı: engine/veri/b35_quorum.csv
"""
import csv
import random
from math import comb

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"
N = 3
DENEME = 200000


def teorik(r, w):
    # Yazılmayan kopya sayısı N-W; okunan R kopyanın hepsi onlardan
    # oluşursa bayat okuma olur.
    if r + w > N:
        return 0.0
    return comb(N - w, r) / comb(N, r)


def simule(r, w, rnd):
    bayat = 0
    kopyalar = list(range(N))
    for _ in range(DENEME):
        yazilan = set(rnd.sample(kopyalar, w))
        okunan = rnd.sample(kopyalar, r)
        if not (yazilan & set(okunan)):
            bayat += 1
    return bayat / DENEME
```

```python

if __name__ == "__main__":
    rnd = random.Random(35)
    satirlar = []
    print("N=%d, deneme=%d" % (N, DENEME))
    print("R W  R+W>N  teorik    olculen")
    for r, w in [(1, 1), (1, 2), (2, 1), (2, 2), (1, 3), (3, 1)]:
        t = teorik(r, w)
        o = simule(r, w, rnd)
        print("%d %d  %-5s  %.5f  %.5f"
              % (r, w, r + w > N, t, o))
        satirlar.append([r, w, N, "%.6f" % t, "%.6f" % o])
    with open(VERI + "/b35_quorum.csv", "w", encoding="utf-8",
              newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["R", "W", "N", "teorik", "olculen"])
        wr.writerows(satirlar)
```

```term
N=3, deneme=200000
R W  R+W>N  teorik    olculen
1 1  False  0.66667  0.66587
1 2  False  0.33333  0.33367
2 1  False  0.33333  0.33259
2 2  True   0.00000  0.00000
1 3  True   0.00000  0.00000
3 1  True   0.00000  0.00000
```

Sonuçlar teoriyle uyumlu: `(R, W) = (1, 1)` için bayat okuma olasılığı 2/3 ≈ 0,667 (simülasyon 0,666), `(1, 2)` ve `(2, 1)` için 1/3 ≈ 0,333. `R + W > N` olan `(2, 2)`, `(1, 3)` ve `(3, 1)` durumlarında olasılık tam olarak sıfır. Bu sıfır bir kesişim garantisi, yani matematiksel bir kesinlik; diğer satırlar ise olasılık.

![Şekil 35.9: Quorum N = 3: teorik ve ölçülen bayat okuma olasılığı; R + W > N iken sıfır.](gorseller/b35_quorum.png)

Şekil 35.9 bu sonucu görselleştiriyor. Bir okuma ile yazma kümesinin kesişmemesi, yalnızca `R + W ≤ N` iken mümkün. Ama dikkat: bu tablo "yazma tamamlandıktan hemen sonra" durumunu gösteriyor. Gerçek sistemde asıl sorun, takipçilerin güncellemeyi ne kadar geç aldığıdır.

**Vektör saatleri ve sürüm çatışması.** Lidersiz ve çok liderli sistemlerde iki yazma birbirinden habersiz gerçekleşebilir. Hangisinin "daha yeni" olduğu zaman damgasıyla belirlenirse, saatlerin senkron olmaması bir yazmayı sessizce kaybettirebilir. **Vektör saati**, her düğüm için bir sayaç taşıyan bir vektördür (genel bilgi). İki sürüm, birinin vektörü diğerinin her bileşeninden büyük ya da eşitse sırayla gelmiş (birbirinin devamı) sayılır; hiçbiri diğerini kapsamıyorsa **eşzamanlı** (concurrent) ve bir **çatışma**dır. Bu durumda sistemin çatışmayı kullanıcıya ya da bir birleştirme kuralına bırakması gerekir. Hesabı elle görmek için: düğüm A'nın yazdığı sürüm `[A=2, B=0]`, düğüm B'nin yazdığı `[A=1, B=1]`. İlki ikinciyi kapsamıyor (`B` bileşeninde 0 < 1), ikincisi de ilkini kapsamıyor (`A` bileşeninde 1 < 2): bunlar eşzamanlı, yani bir çatışma.

**Konsensüs ve Raft.** Quorum, bir değerin "kabul edildiğini" bir çoğunlukla belirler; ama birden çok düğümün **aynı sırada** aynı kararı vermesi (örneğin hangi düğüm lider olacak, hangi işlem önce gelecek) ayrı bir problemdir: konsensüs. Raft (2014, Ongaro ve Ousterhout) bu problemi anlaşılır biçimde çözer: lider seçimi, bir günlüğün (log) lider üzerinden takipçilere çoğaltılması ve güvenlik kuralları. Bu bölümde yalnızca kavramını görmen yeterli; algoritmanın ayrıntılı işleyişi ve bir sistem tasarımında nasıl kullanıldığı Bölüm 41'in konusu.

## 35.9 Belge modeli: gömme mi, referans mı?

Belge veritabanında asıl tasarım sorusu, ilişkili verinin **aynı belgeye gömülüp gömülmeyeceğidir**. Bir siparişin kalemlerini sipariş belgesinin içine mi koyarsın, yoksa ayrı bir koleksiyonda tutup kimliğe göre mi bağlarsın? Bu soru, Bölüm 33'teki normalizasyon kararının belge dünyasındaki karşılığıdır.

**Gömme (embedding)** ilgili veriyi belgenin içine koyar. Bir sorguda tek belgeyi okuyup her şeyi alırsın; bu, okuma hızını artırır. Bedeli tekrardır: aynı ürün birden çok belgede yazılıysa, ürün adı değiştiğinde hepsini güncellemek zorundasın. Bu bilinçli bir **denormalizasyon** kararıdır.

**Referans (reference)** ilgili veriyi ayrı bir belgede tutar ve kimliğiyle bağlar. Güncelleme tek yerde yapılır, tutarlılık korunur; ama okumak için birden çok sorgu, yani bir tür JOIN gerekir. Kural kabaca şudur: birlikte okunan ve birlikte değişen veri gömülür; birçok yerden paylaşılan ve sık değişen veri referanslanır.

**Şema evrimi.** Belge veritabanlarının çekici yanı, şemanın belgeye özgü olmasıdır. Yeni bir alan ekleyince eski belgeler güncellenmek zorunda değildir; uygulama eksik alanı varsayılan kabul eder. Bu esneklik, sıkı şemanın tersi bir sorumluluk doğurur: şema artık uygulama kodunda yaşar ve belgelerin hangi sürümde yazıldığını takip etmek senin işindir.

Bu fikirleri, bir SQLite veritabanında JSON1 fonksiyonlarıyla deneyeceğiz. SQLite, sürüm 3.38'den beri JSON işlevlerini çekirdekte bulundurur; bu makinedeki sürüm 3.49.1'dir. Kullanılacak iki fonksiyon: `json_extract`, bir JSON belgesinden bir yolu okur; `json_each`, bir JSON dizisini satırlara açar.

```python
# -*- coding: utf-8 -*-
"""Belge modeli: gömme ile sorgu ve şema evrimi (Bölüm 35.9).
SQLite JSON1 fonksiyonları (json_extract, json_each) kullanılır.
Bu makinedeki SQLite sürümü: sqlite3.sqlite_version."""
import json
import sqlite3


def kur():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE musteri (id INTEGER PRIMARY KEY, "
              "veri TEXT)")
    belgeler = [
        {"ad": "Ali", "sehir": "Ankara", "siparisler": [
            {"no": 1, "tutar": 250.0, "urun": "sensör"},
            {"no": 2, "tutar": 1200.0, "urun": "kart"}]},
        {"ad": "Ayşe", "telefon": "0555", "siparisler": [
            {"no": 3, "tutar": 80.0, "urun": "kablo"}]},
        {"ad": "Mert", "sehir": "İzmir", "siparisler": []},
        {"ad": "Can", "sehir": "Ankara", "siparisler": [
            {"no": 4, "tutar": 80.0, "urun": "kablo"}]},
    ]
    for i, b in enumerate(belgeler, 1):
        c.execute("INSERT INTO musteri VALUES (?, ?)",
                  (i, json.dumps(b, ensure_ascii=False)))
    return c


if __name__ == "__main__":
    print("SQLite sürümü:", sqlite3.sqlite_version)
```

```python
    c = kur()
    print("\n-- 1. Alan okuma (şema yok, yol ifadesi var)")
    for ad, sehir in c.execute(
            "SELECT json_extract(veri,'$.ad'), "
            "json_extract(veri,'$.sehir') FROM musteri ORDER BY id"):
        print("%-6s sehir=%s" % (ad, sehir))
    print("\n-- 2. Tutarı 1000'i aşan siparişi olan müşteriler")
    for (ad,) in c.execute(
            "SELECT json_extract(m.veri,'$.ad') FROM musteri m, "
            "json_each(m.veri,'$.siparisler') s "
            "WHERE json_extract(s.value,'$.tutar') > 1000"):
        print(ad)
    print("\n-- 3. Şema evrimi: eksik alan NULL döner, hata vermez")
    for ad, tel in c.execute(
            "SELECT json_extract(veri,'$.ad'), "
            "json_extract(veri,'$.telefon') FROM musteri "
            "ORDER BY id"):
        print("%-6s telefon=%s" % (ad, tel))
    print("\n-- 4. Gömülü veride aynı ürünü içeren belge "
          "sayısı")
    n = c.execute("SELECT COUNT(*) FROM musteri m, "
                  "json_each(m.veri,'$.siparisler') s WHERE "
                  "json_extract(s.value,'$.urun') = "
                  "'kablo'").fetchone()[0]
    print("'kablo' geçen sipariş sayısı:", n)
    print("Ürün adı değişirse güncellenecek belge (gömülü): "
          "%d" % n)
    print("Aynı ürün ayrı bir 'urun' tablosunda olsaydı: "
          "1 satır")
```

```term
SQLite sürümü: 3.49.1

-- 1. Alan okuma (şema yok, yol ifadesi var)
Ali    sehir=Ankara
Ayşe   sehir=None
Mert   sehir=İzmir
Can    sehir=Ankara

-- 2. Tutarı 1000'i aşan siparişi olan müşteriler
Ali

-- 3. Şema evrimi: eksik alan NULL döner, hata vermez
Ali    telefon=None
Ayşe   telefon=0555
Mert   telefon=None
Can    telefon=None

-- 4. Gömülü veride aynı ürünü içeren belge sayısı
'kablo' geçen sipariş sayısı: 2
Ürün adı değişirse güncellenecek belge (gömülü): 2
Aynı ürün ayrı bir 'urun' tablosunda olsaydı: 1 satır
```

İlk iki bölümde belgeler sorgulanabiliyor. Üçüncü bölüm şema evrimini gösteriyor: `telefon` alanı yalnızca Ayşe'de var; diğerleri için `json_extract` hata vermeden `None` dönüyor. Dördüncü bölümde `kablo` ürününü içeren iki belge var; ürün adı değişirse iki belgeyi güncellemen gerekir. Aynı veriyi ayrı bir `urun` tablosunda tutsaydın tek satır yeterdi. Bu sayı, gömmenin bedelini somut hâle getiriyor.

::: dikkat
Belge veritabanı ilk bakışta "şema yok" gibi görünür, ama bu bir yanılsamadır. Şema vardır; yalnızca yanlış yere, uygulama koduna taşınmıştır. Uygulamanın okuduğu her alanın varlığını ve türünü kendin doğrulamalı, eski belge sürümlerini ele almalısın.
:::

## 35.10 Zaman serisi: telemetri ve delta-of-delta sıkıştırma

Zaman serisi, zaman damgası ile etiketlenmiş ölçümlerin dizisidir ve diğer verilerden belirgin biçimde farklıdır. Bu farkların her biri bir tasarım kararı doğurur.

**Ekle-yaz.** Telemetri neredeyse yalnızca eklenir; bir ölçüm geçmişini değiştirmek nadirdir. Bu, bölüm 35.3'teki LSM'nin doğal alanıdır: sıralı yazma ve değişmez dosyalar.

**Zaman aralığı sorgusu.** Tipik soru "son bir saatteki sıcaklık ortalaması" gibidir. Veri zamana göre sıralıysa, bir aralığı bulmak bir ikili aramadır; sıkıştırma ve bloklama bu aramayı hızlandırır.

**Örnekleme azaltma (downsampling).** Bir yıllık 1 Hz veri çok büyüktür. Eski veriyi dakikalık ortalamalara indirgeyerek saklarsın; yeni veri ham hâlinde kalır. Bu, yakın geçmişte ayrıntı, uzak geçmişte özet tutan bir **saklama politikasıdır** (retention policy).

**Saklama süresi.** Eski veriyi belirli bir süreden sonra silmek, disk maliyetini sınırlar. Bu bir silme işlemidir ama LSM'de bu, tüm bir dosyayı atmak gibi ucuz olabilir; çünkü zamana göre bölümlenmiş dosyalar kolayca düşürülür.

**Delta-of-delta sıkıştırma.** Zaman damgaları genellikle sabit bir periyoda yakındır. Ardışık farkları (delta) almak onları küçültür; ama her farkın kendisi de yakın değerler aldığı için **farkın farkını** (delta-of-delta) tutmak daha da küçük sayılar üretir. Gorilla (Facebook, 2015) bu fikri, değişken uzunluklu önek kodlarıyla birleştirdi (genel bilgi). Aşağıdaki kodda bu kodlamayı yazıp ölçüyoruz.

Kodlama kuralı şöyle: ilk zaman damgası 64 bit ham; ilk fark 32 bit ham; sonraki her nokta için `dod = (t_i - t_{i-1}) - (t_{i-1} - t_{i-2})`. `dod = 0` ise yalnızca `0` biti yazılır (1 bit). `dod` küçükse önek `10` ve 7 bit, daha büyükse `110` ve 9 bit, sonra `1110` ve 12 bit, en sonunda `1111` ve 32 bit kullanılır. Negatif sayılar iki tümleyenle yazılır.

```python
# -*- coding: utf-8 -*-
"""Zaman damgası delta-of-delta sıkıştırması (Gorilla tarzı, Bölüm
35.10).

Kodlama:
  ilk zaman damgası: 64 bit ham
  ilk delta (t1 - t0): 32 bit ham
  sonraki her nokta: dod = (t_i - t_{i-1}) - (t_{i-1} - t_{i-2})
    dod == 0          -> '0'                      (1 bit)
    -64 <= dod <= 63  -> '10' + 7 bit           (9 bit)
    -256 <= dod <= 255 -> '110' + 9 bit         (12 bit)
    -2048..2047       -> '1110' + 12 bit         (16 bit)
    diğerleri         -> '1111' + 32 bit         (36 bit)
Çıktı bit dizisidir (str '0'/'1'); boyut = len(bit dizisi).
Tohum: 35. Çıktı: engine/veri/b35_zaman.csv
"""
import csv
import random

VERI = "D:/Mevcut Projeler/Kitap/engine/veri"


def ikili(deger, bit):
    # two's complement, bit genişliğinde
    return format(deger & ((1 << bit) - 1), "0%db" % bit)


def aralik_icinde(deger, bit):
    return -(1 << (bit - 1)) <= deger < (1 << (bit - 1))


def sikistir(zamanlar):
    bits = []
    bits.append(ikili(zamanlar[0], 64))
    if len(zamanlar) == 1:
        return "".join(bits)
    d_onceki = zamanlar[1] - zamanlar[0]
    bits.append(ikili(d_onceki, 32))
    for i in range(2, len(zamanlar)):
        d = zamanlar[i] - zamanlar[i - 1]
```

```python
        dod = d - d_onceki
        if dod == 0:
            bits.append("0")
        elif aralik_icinde(dod, 7):
            bits.append("10" + ikili(dod, 7))
        elif aralik_icinde(dod, 9):
            bits.append("110" + ikili(dod, 9))
        elif aralik_icinde(dod, 12):
            bits.append("1110" + ikili(dod, 12))
        else:
            bits.append("1111" + ikili(dod, 32))
        d_onceki = d
    return "".join(bits)


def coz(bits, n):
    p = 0

    def oku(k):
        nonlocal p
        s = bits[p:p + k]
        p += k
        return s

    def isaretli(s):
        v = int(s, 2)
        return v - (1 << len(s)) if s[0] == "1" else v

    zamanlar = [isaretli(oku(64))]
    if n == 1:
        return zamanlar
    d_onceki = isaretli(oku(32))
    zamanlar.append(zamanlar[0] + d_onceki)
    for _ in range(2, n):
        if oku(1) == "0":
            dod = 0
        else:
            b = oku(1)
            if b == "0":
                dod = isaretli(oku(7))
```

```python
            elif oku(1) == "0":
                dod = isaretli(oku(9))
            elif oku(1) == "0":
                dod = isaretli(oku(12))
            else:
                dod = isaretli(oku(32))
        d = d_onceki + dod
        zamanlar.append(zamanlar[-1] + d)
        d_onceki = d
    return zamanlar


def senaryo(ad, adim, jitter, kayip_orani, rnd, n=20000):
    # Telemetri: nominal periyot adim ms, her nokta +-jitter sapar.
    # Kayıp: bazı noktalar atlanır (boşluk), delta büyür.
    t = 1_700_000_000_000
    zamanlar = [t]
    while len(zamanlar) < n:
        t += adim + (rnd.randint(-jitter, jitter) if jitter else 0)
        if rnd.random() < kayip_orani:
            t += adim * rnd.randint(2, 40)  # birkaç periyot boşluk
        zamanlar.append(t)
    return ad, zamanlar


if __name__ == "__main__":
    rnd = random.Random(35)
    senaryolar = [
        senaryo("mükemmel periyodik (1 Hz)", 1000, 0, 0.0, rnd),
        senaryo("1 Hz, ±3 ms titreme", 1000, 3, 0.0, rnd),
        senaryo("1 Hz, ±40 ms titreme", 1000, 40, 0.0, rnd),
        senaryo("1 Hz, ±3 ms, %1 boşluk", 1000, 3, 0.01, rnd),
        senaryo("10 Hz, ±1 ms, %5 boşluk", 100, 1, 0.05, rnd),
    ]
    satirlar = []
    print("%-28s %10s %10s %8s"
          % ("senaryo", "bit/nokta", "ham64", "oran"))
    for ad, z in senaryolar:
        bits = sikistir(z)
        geri = coz(bits, len(z))
```

```python
        assert geri == z, "çözme hatalı: " + ad
        bpn = len(bits) / len(z)
        print("%-28s %10.2f %10d %8.1f" % (ad, bpn, 64,
                                          64 / bpn))
        satirlar.append([ad, "%.4f" % bpn, 64, "%.2f" % (64 / bpn)])
    with open(VERI + "/b35_zaman.csv", "w", encoding="utf-8",
              newline="") as f:
        w = csv.writer(f)
        w.writerow(["senaryo", "bit_nokta", "ham", "oran"])
        w.writerows(satirlar)
    print("Geri çözme: tüm senaryolarda birebir eşleşti")
```

Bu kod üç şey yapar: sıkıştırır, çözer ve sonucu doğrular. `senaryo` fonksiyonu gerçek telemetriye yakın örnekler üretir: sabit periyot, titreme (jitter) ve arada kayıp nedeniyle oluşan boşluklar. `coz` fonksiyonu bit dizisini tekrar zaman damgalarına çevirir ve `assert` ile orijinalle birebir eşleştiğini doğrular. Bu doğrulama, sıkıştırmanın kayıpsız olduğunun kanıtıdır.

```term
senaryo                       bit/nokta      ham64     oran
mükemmel periyodik (1 Hz)          1.00         64     63.7
1 Hz, ±3 ms titreme                7.88         64      8.1
1 Hz, ±40 ms titreme               9.04         64      7.1
1 Hz, ±3 ms, %1 boşluk             8.45         64      7.6
10 Hz, ±1 ms, %5 boşluk            8.24         64      7.8
Geri çözme: tüm senaryolarda birebir eşleşti
```

Sonuçlar kuralın gücünü gösteriyor. Mükemmel periyodik bir akışta her nokta yalnızca 1 bit tutuyor (64 bitlik ham değere karşı yaklaşık 64 kat küçük). Titreme ±3 ms olduğunda nokta başına 7,88 bit; titreme ±40 ms olduğunda 9,04 bit; yani titreme büyüdükçe `dod` değerleri 7 bitlik aralığı aşıyor ve daha pahalı önekler kullanılıyor. Boşluklu (kayıplı) akışlarda da 8 bit civarında kalıyor, çünkü bir boşluk tek bir büyük `dod` üretir ama sonraki noktalar tekrar düzene girer.

Bu sayılar, zaman damgası **dizisinin düzenliliğine** bağlıdır; veri değerlerinin (sıcaklık, basınç) sıkıştırması ayrıdır. Gorilla makalesi değerler için de XOR tabanlı bir kodlama önerir; bu bölümde yalnızca zaman damgasını sıkıştırdık.

![Şekil 35.10: Delta-of-delta sıkıştırma: nokta başına bit sayısı; ham 64 bit çizgisinin altında.](gorseller/b35_zaman_dod.png)

Şekil 35.10 bit oranlarını ve ham 64 bit çizgisini gösteriyor. Sıkıştırmanın kazancı, veriniz ne kadar düzenli olursa o kadar büyüyor. Telemetri sistemlerinde bu nedenle örnekleme hızının ve zamanlayıcı kararlılığının bile depolama maliyetini etkilediğini unutma.

## 35.11 Önbellek ve Redis: kullanım kalıpları

Önbellek (cache), yavaş ama doğru bir kaynağın (veritabanı, ağ servisi) sonucunu daha hızlı bir yerde tutmaktır. Bölüm 9'da hash tablosunun bu işe nasıl uyduğunu gördün; Bölüm 9'daki LRU önbelleği örneği, sınırlı bellekte hangi kaydın atılacağını belirleyen bir politikaydı. Burada asıl sorun, önbelleği **kaynakla senkron tutmaktır**.

**Cache-aside (yan önbellek).** En yaygın kalıp: uygulama önce önbelleğe bakar; yoksa kaynağı okur ve önbelleğe yazar. Yazmada ise kaynağı günceller ve önbelleği siler (ya da günceller). Basittir ve kaynak ile önbellek arasında bağımlılık yaratmaz; bedeli, bir süre bayat veri görebilmendir.

**Write-through.** Yazmada hem önbelleğe hem kaynağa yazılır. Okuma hep tutarlıdır ama her yazma iki kat iştir ve önbellek şişebilir.

**Write-back (write-behind).** Yazma önce önbelleğe yapılır, kaynağa sonradan toplu olarak yazılır. En hızlı yazmadır, ama önbellek çökerse kaybolan yazmalar olabilir. Bu, Bölüm 28'deki `fsync` ve sıralama tartışmasının önbellek düzeyindeki karşılığıdır.

**TTL (yaşam süresi).** Her önbellek kaydına bir süre verilir; süre dolunca kayıt atılır. TTL, bayatlık süresini sınırlar ama kesinlikle sıfırlamaz. Doğru TTL, verinin ne sıklıkta değiştiğine bağlıdır.

**Önbellek damgası ve stampede.** Popüler bir anahtarın TTL'i aynı anda dolduğunda binlerce istek aynı anda kaynağa gider; buna **cache stampede** (önbellek sel baskını) denir. Çözümler: TTL'e rastgele bir sapma eklemek, bir anahtar için yalnızca bir isteğin kaynağa gitmesine izin veren bir kilit (single-flight) kullanmak, ya da değer dolmadan önce arka planda yenilemek (genel bilgi).

Redis, bu kalıpların bellek içi bir sunucuda uygulandığı en yaygın sistemdir. Veri yapıları kullanım amacına göre seçilir: sayaçlar için `INCR`, oturum ve önbellek için `SET` ile `EX` (saniye cinsinden TTL), sıralı bir lider tablosu için sıralı küme (sorted set) ve `ZADD`/`ZREVRANGE`. Aşağıdaki komutlar genel bilgi olarak verilmiştir; bu makinede Redis kurulu olmadığı için çalıştırılmadı.

```term
$ SET oturum:42 "veri" EX 60 NX
$ INCR ziyaret:ana-sayfa
$ ZADD lider 1520 "ali" 1310 "ayse"
$ ZREVRANGE lider 0 2 WITHSCORES
```

Bu komutların anlamı: `SET` anahtarı değerle yazar; `EX 60` 60 saniyelik bir TTL verir; `NX` yalnızca anahtar yoksa yazar, yani bir kilidi taklit etmek için kullanılır. `INCR` atomik bir artırmadır. `ZADD` bir üyeyi bir puanla ekler; `ZREVRANGE` puan sırasına göre tersten bir aralık döner (genel bilgi).

## 35.12 Gerçek dünya: İHA telemetrisi, uçta ve merkezde

Bir İHA telemetri sistemini düşün. Uçaktaki bir bilgisayar IMU, GPS, motor sıcaklığı ve batarya gibi onlarca sensörden saniyede yüzlerce ölçüm toplar. Bu veri üç farklı yerde üç farklı işi görür.

**Uçta (edge).** Uçaktaki bilgisayar, veriyi kısa süreli bir tampona alır ve sıkıştırarak kaydeder. Bağlantı yoksa bile veri kaybolmaz; bu, Bölüm 28'deki ekle-yaz günlüğünün ve Bölüm 35.4'teki WAL'in doğrudan uygulamasıdır. Uçaktaki işlemci sınırlıdır; bu yüzden sıkıştırma ve örnekleme kararları burada verilir.

**Yer istasyonu.** Yer istasyonu, uçtan gelen parçaları birleştirir ve gerçek zamanlı izleme için bir önbellekte son değerleri tutar. Burada önbellek kalıpları (35.11) ve TTL kararları devreye girer: operatör yalnızca son birkaç saniyeye bakar.

**Merkez.** Uzun süreli saklama, analiz ve model eğitimi için veri merkezde bir zaman serisi deposunda tutulur. Burada downsampling ve saklama politikası kullanılır: uçuşun ham verisi bir süre saklanır, sonra dakikalık özetlere indirgenir. Bölüm 68'de bu zaman serisi verisi üzerinde modeller kuracaksın.

Bu üç katmanın her biri, bu bölümde gördüğün bir kararın uygulamasıdır: uçta sıralı yazma ve sıkıştırma, yer istasyonunda önbellek ve TTL, merkezde zaman serisi deposu ve saklama politikası. Tek bir "doğru veritabanı" yoktur; her katman kendi erişim deseniyle seçilir.

Bu düzenin bir bedeli var: uçtan merkeze veri taşınırken ağ kesintisi olabilir. Veri sırasız gelebilir, tekrarlanabilir. Bu, çoğaltma ve tutarlılık konularının (35.7-35.8) gerçek karşılığıdır. Bölüm 46'da kenar (edge) çıkarımının donanım tarafını, Bölüm 41'de bu tür bir dağıtık mimarinin tasarımını göreceksin.

## Çözümlü Örnekler

### Örnek 1 (★): Bloom filtresi için m ve k seçimi

**Adım 1 — Anla.** Bir sensör kimliği kümesi var: `n = 10 000` kimlik. Yeni gelen bir kimliğin kümede olup olmadığını sormak istiyoruz; yanlış pozitif oranının en fazla `%1` olması gerekiyor. Bellek bütçesi bilinmiyor; `m` (bit sayısı) ve `k` (hash sayısı) seçmemiz isteniyor.

**Adım 2 — Örnekle.** Diyelim ki hedef `p = 0,01`. Önce kaç bit gerektiğini hesaplayalım: `m = -n ln p / (ln 2)^2`. `ln 0,01 = -4,605` ve `(ln 2)^2 = 0,4805`. Bu durumda `m ≈ 10 000 · 4,605 / 0,4805 ≈ 95 851` bit. Eleman başına `m/n ≈ 9,585` bit.

**Adım 3 — Kaba çöz.** En basit yol: `m`'yi yukarı yuvarla (96 000 bit, yani `m/n = 9,6`) ve `k`'yı optimum formülüyle seç: `k = (m/n) ln 2 ≈ 9,6 · 0,693 ≈ 6,65`. Tam sayıya yuvarlarsak `k = 7`.

**Adım 4 — Örüntü.** Örüntü: `k` tam sayıya yuvarlanırken hedef oranın altında kalmak için `m/n` yeterince büyük olmalı; `k` optimumdan sapınca oran yükselir. Bu, Bölüm 35.6'daki formülün iki ucunun (az hash / çok hash) dengelenmesidir.

**Adım 5 — İyileştir.** Teorik değer `m/n = 9,6` ve `k = 7` için: `(1 - e^(-7/9,6))^7`. Bu, `1 - e^(-0,729) = 0,5176` ve `0,5176^7 ≈ 0,00997` verir: `%0,997`, hedefin altında. `k = 6` ile aynı `m`'de `%1,008` çıkar; yani bu durumda `k = 7` daha iyi. Gerçek sistemde `m` bayt'a yuvarlanır ve bu küçük fark önemsizdir.

**Adım 6 — Doğrula.** Aşağıdaki tablo, deneyimizden (`bloom_cikti.txt`) alınan `m/n = 8` ve `m/n = 10` değerlerini gösteriyor. Elle hesapladığımız `m/n = 9,6, k = 7` için değer 0,00997; ölçümü `m/n = 10` ile karşılaştır.

| m/n | k | Teorik p | Ölçülen p |
|---|---|---|---|
| 8 | 6 (optimum) | 0,021577 | 0,021560 |
| 10 | 7 (optimum) | 0,008194 | 0,008210 |
| 10 | 4 | 0,011813 | 0,012100 |

Ölçüm teoriye yakın; `m/n = 9,6` için elle hesaplanan `0,00997` ile `m/n = 10` için `0,00819` arasında, hedefin altında bir değer beklenir ve ölçüm bunu doğrular.

**Bunu AI'sız yazabilir misin?** `n = 50 000` kimlik ve `p = 0,001` hedefi için `m/n` ve optimum `k`'yı kâğıtta hesapla. Sonra `k`'yı bir tam sayıya yuvarla ve teorik `p`'yi yeniden çıkar.

### Örnek 2 (★★): Tutarlı hash halkasında taşınan anahtarlar

**Adım 1 — Anla.** Üç düğüm (A, B, C) bir halkada. Düğüm D eklendiğinde hangi anahtarların taşınacağını bulmak istiyoruz. Halka `0` ile `100` arasında sarılı; her düğüm bir konumda (`v = 1`). Anahtar, konumundan saat yönünde (değer artan yönde) bulunan ilk düğüme gider.

**Adım 2 — Örnekle.** Varsayımsal konumlar: `A = 10`, `B = 40`, `C = 70`. Dört anahtar: `k1 = 25`, `k2 = 55`, `k3 = 80`, `k4 = 5`. Bu konumlar gerçek hash değerleri değil; mantığı görmek için seçilmiş küçük sayılardır.

**Adım 3 — Kaba çöz.** Her anahtar için, konumundan büyük ilk düğümü bul; yoksa halkayı sar ve en küçük düğümü al. `k1 = 25` → `B(40)`. `k2 = 55` → `C(70)`. `k3 = 80` → yoksa sarılır → `A(10)`. `k4 = 5` → `A(10)`.

**Adım 4 — Örüntü.** Düğüm eklenince yalnızca yeni düğümün halkadaki **öncesindeki** arkasına düşen anahtarlar etkilenir. D konumu `60`: `C(70)`'ten önce ve `B(40)`'tan sonra. Yani sahibi C olan ve konumu 40 ile 60 arasında kalan anahtarlar D'ye geçer; konumu 60 ile 70 arasında olanlar C'de kalır.

**Adım 5 — İyileştir.** Bu sayıdan genel kural çıkar: `n` düğümlü bir halkaya bir düğüm eklendiğinde taşınan anahtar oranı yaklaşık `1/(n+1)`'dir. Düğüm sayısı az olduğunda bu oran sapabilir; sanal düğümler bu sapmayı azaltır (Bölüm 35.7'deki `v = 1` sonucu bunu gösteriyor).

**Adım 6 — Doğrula.** Her anahtar için sahibi, eklemeden önce ve sonra:

| Anahtar | Konum | Eklemeden önce | D eklenince | Taşındı mı? |
|---|---|---|---|---|
| k1 | 25 | B (40) | B (40) | Hayır |
| k2 | 55 | C (70) | D (60) | **Evet** |
| k3 | 80 | A (10) | A (10) | Hayır |
| k4 | 5 | A (10) | A (10) | Hayır |

Tabloda yalnızca `k2` taşındı ve yeni düğüme gitti. Bu, kodda `assert b == yeni` ile doğruladığımız kuralın elle izidir: taşınan her anahtar yeni düğüme gider.

**Bunu AI'sız yazabilir misin?** `A = 15`, `B = 45`, `C = 80` ve `D = 30` olsun; anahtarlar `10, 50, 85, 20`. Eklemeden önce ve sonra sahipleri tablo hâlinde yaz; kaç anahtarın taşındığını ve hepsinin D'ye gidip gitmediğini söyle.

### Örnek 3 (★★): LSM'de put, delete ve get dizisinin durum izi

**Adım 1 — Anla.** Bir LSM deposunda `put a=1`, `put b=2`, `put a=3`, `delete b`, `get b`, `get a` ve sonra birleştirme yapılıyor. Her adımdan sonra bellekte ve diskte ne olduğunu izlemek istiyoruz. Eşik `2`: bellek iki kayda ulaşınca dosyaya yazılır.

**Adım 2 — Örnekle.** `put a=1` belleğe girer (1 kayıt). `put b=2` belleği 2 kayda çıkarır; eşik dolduğu için `000000.sst` yazılır ve bellek boşalır. `put a=3` yeni bir değerdir ve belleğe girer. `delete b` bir mezar taşıdır: bellekte `b = None` olarak yazılır, bellek 2 kayda ulaşınca `000001.sst` oluşur.

**Adım 3 — Kaba çöz.** `get b`: bellekte yok, sonra en yeni tablo `000001.sst`'de `b = None` bulunur; bu bir silinmiş anahtardır, `None` döner. `get a`: bellekte yok, `000001.sst`'de `a = 3` bulunur; döner.

**Adım 4 — Örüntü.** Örüntü: en yeni kayıt her zaman önce bulunur; `None` bir gizleyicidir. Eski tablo (`000000.sst`) hâlâ `b = 2` tutuyor ama `000001.sst`'deki mezar taşı onu gizliyor.

**Adım 5 — İyileştir.** Birleştirme tüm tabloları eskiden yeniye okur, sözlükte en yeni değer kazanır ve `None` kayıtlar atılır. Sonuç tek bir tablo olur. Bu sayede disk alanı geri kazanılır ve okuma tek dosyaya düşer.

**Adım 6 — Doğrula.** Betik (`iz.py`), aynı işlemleri yapıp her adımda durumu yazdırır:

```python
# -*- coding: utf-8 -*-
"""Çözümlü Örnek 3 için: küçük LSM'de durum izi."""
import os
import shutil
from lsm import LSM

dizin = "iz_dizin"
shutil.rmtree(dizin, ignore_errors=True)
db = LSM(dizin, esik=2, m=256, k=3)


def durum(ad):
    tablolar = [os.path.basename(t.yol) for t in db.tablolar]
    print("%-14s bellek=%s tablolar=%s"
          % (ad, db.memtable, tablolar))


db.put("a", "1")
durum("put a=1")
db.put("b", "2")
durum("put b=2")
db.put("a", "3")
durum("put a=3")
db.sil("b")
durum("sil b")
print("get b ->", db.get("b"), "| get a ->", db.get("a"))
db.birlestir()
durum("birlestir")
print("get a ->", db.get("a"), "| get b ->", db.get("b"))
with open(os.path.join(dizin, "000002.sst"), encoding="utf-8") as f:
    print("000002.sst:", f.read().strip())
shutil.rmtree(dizin, ignore_errors=True)
```

Gerçek çıktı (`iz_cikti.txt`):

```term
put a=1        bellek={'a': '1'} tablolar=[]
put b=2        bellek={} tablolar=['000000.sst']
put a=3        bellek={'a': '3'} tablolar=['000000.sst']
sil b          bellek={} tablolar=['000000.sst', '000001.sst']
get b -> None | get a -> 3
birlestir      bellek={} tablolar=['000002.sst']
get a -> 3 | get b -> None
000002.sst: ["a", "3"]
```

Elle izimizle karşılaştırırsak: `put b=2`'den sonra tablo sayısı 1, mezar taşından sonra 2, birleştirmeden sonra 1. `000002.sst` içinde yalnızca `a` var; `b` hem eski değeriyle hem mezar taşıyla birlikte atılmış. Bu, beklediğimiz birleştirme davranışıdır.

**Bunu AI'sız yazabilir misin?** Aynı işlemleri `esik = 2` ile yap, ancak son sırada `put b=5` ekle ve birleştirmeden önce `get b`'nin ne döndüreceğini tahmin et. Sonra birleştirmeden sonra `000002.sst`'nin içeriğini yaz.

### Örnek 4 (★★★): Quorum ile bayat okumanın izlenmesi

**Adım 1 — Anla.** `N = 3` kopya (r1, r2, r3). Bir istemci `v1` değerini yazıyor; sonra başka bir istemci okuyor. Hangi `(R, W)` seçimlerinde okuma `v0` (bayat) değerini görebilir? Yazma tamamlandıktan sonra okumanın olduğunu varsayıyoruz.

**Adım 2 — Örnekle.** Başlangıçta üç kopyada da `v0` var. Sonra `W = 1` ile `v1` yalnızca `r1`'e yazılır. Okuma `R = 1` ile yalnızca `r2`'den yapılır: `r2` hâlâ `v0` tutuyor, yani bayat.

**Adım 3 — Kaba çöz.** Bayat okuma, okunan kopyaların hiçbirinin yazılmış kümede olmamasıdır. Kesişim boşsa bayat. Kesişim boş olasılığı `C(N-W, R) / C(N, R)`.

**Adım 4 — Örüntü.** `R + W > N` ise iki küme kesişmek zorundadır: kutu ilkesi. Kesişim kopyası yeni değeri taşır, okuma onu seçer. Bu yalnızca `R + W ≤ N` için bayat okumaya izin verir.

**Adım 5 — İyileştir.** Tasarım seçimi: `(R, W) = (2, 2)` `N = 3` için `R + W = 4 > 3`; garanti verir ama her okuma ve yazma iki kopyaya gider. `(1, 3)` okumayı ucuzlatır, yazmayı pahalılaştırır ve tek bir kopya çökünce yazma durur. Hangisini seçeceğin, okuma-yazma oranına ve hata toleransı gereksinimine bağlı.

**Adım 6 — Doğrula.** Bir senaryonun iz tablosu (sürümler: r1, r2, r3 üzerinde):

| Adım | İşlem | r1 | r2 | r3 | Sonuç |
|---|---|---|---|---|---|
| 0 | Başlangıç | v0 | v0 | v0 | - |
| 1 | Yazma `v1`, W=1 (yalnızca r1) | v1 | v0 | v0 | Tamamlandı |
| 2 | Okuma R=1 (r2) | v1 | v0 | v0 | **v0 (bayat)** |
| 3 | Okuma R=2 (r1, r2) | v1 | v0 | v0 | v1 (en yeni) |
| 4 | Yazma `v1`, W=2 (r2, r3 de) | v1 | v1 | v1 | Tamamlandı |
| 5 | Okuma R=1 (r3) | v1 | v1 | v1 | v1 |

Adım 2'deki bayat okuma, `R + W = 2 ≤ 3` olduğu için mümkün. Adım 3'teki `R = 2` okuması, `r1`'i içerdiği için en yeni değeri alır. `W = 2`'ye çıkardığımızda ise Adım 5'teki okuma artık bayat olamaz.

**Bunu AI'sız yazabilir misin?** `N = 5` için `(R, W) = (2, 3)` ve `(2, 2)` durumlarında bayat okuma olasılığını `C(N-W,R)/C(N,R)` ile hesapla. Hangisi `R + W > N` kuralıyla sıfır olur?

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ araçları **yasak**. Amaç çalışan bir veritabanı üretmek değil; yazma yolunu, kalıcılığı ve ölçüm yapmayı kendi kafanla kurmak. Takıl, kâğıda çiz, küçük testler yaz; çözümü dışarıdan alma.
:::

### Proje 1 (★★): Kalıcı LSM deposu: WAL ve çökme kurtarma

**Amaç:** Bölüm 35.4'teki LSM deposuna bir yazma öncesi günlük (WAL) ekle; böylece memtable'da olup da dosyaya inmemiş kayıtlar, süreç aniden kapansa bile açılışta geri kazanılsın.

**Beklenen davranış:** Her `put` ve `sil` önce günlüğe eklenir ve `fsync` ile diske iner; sonra memtable'a yazılır. Açılışta günlük baştan okunur ve memtable yeniden kurulur. Flush sonrası günlük sıfırlanır. Günlüğün sonundaki yarım bir kayıt (kesilmiş yazma) fark edilip atılmalıdır.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Kayıt biçimini `[uzunluk][CRC][tür][anahtar][değer]` olarak tasarla; Bölüm 28'deki telemetri kaydedici projesindeki kalıbı kullan. Flush'ın sırasına dikkat et: önce SSTable'ı yaz ve `fsync` et, sonra günlüğü sıfırla. Ters sıra, kayıtların hiçbir yerde kalmadığı bir pencere yaratır. Testi Bölüm 28'deki `kill -9` kalıbıyla yap: bir süreç rastgele bir anda öldürülsün, sonra açılıp dict modeliyle karşılaştırılsın. Windows'ta `kill -9` yerine `taskkill /F` ya da Python'da `os._exit` kullanabilirsin; gerçek `kill -9` davranışı için WSL'de test etmek daha güvenilirdir.

**Başarı kriterleri:**
- 300 rastgele öldürme denemesinin hiçbirinde açılış çökmüyor.
- Yazma döndükten sonra `fsync` edilmiş her kayıt açılışta mevcut.
- Yarım kalmış son kayıt atılıyor ve ortadaki bozuk bir kayıt hata olarak raporlanıyor.

### Proje 2 (★★★): İHA telemetrisi için mini zaman serisi deposu

**Amaç:** Zaman damgalı ölçümleri blok bazlı, sıkıştırılmış dosyalarda saklayan ve zaman aralığı sorgusu yapan küçük bir depo yaz. Depo downsampling ve saklama süresi de desteklesin.

**Beklenen davranış:** Ölçümler, belirli bir süre penceresine (örneğin bir dakika) düşen bloklarda tutulur. Her blokta zaman damgaları delta-of-delta ile sıkıştırılır (35.10). `sorgu(baslangic, bitis)` yalnızca ilgili blokları açar. `azalt(pencere)` eski blokları dakikalık ortalamalara indirger. `temizle(sure)` saklama süresinden eski blokları siler.

**Önerilen yaklaşım (ipucu):** Blok başlığında blok başlangıç ve bitiş zamanını tut; sorguda yalnızca kesişen blokları aç. Değerler için şimdilik ham `float` kullan ve sıkıştırmayı yalnızca zaman damgalarına uygula. Sorgu sonucunu sıralı tut; blok sınırlarındaki örtüşmeyi (aynı zamanda iki blok) ele al. Saklama süresi için eski blok dosyalarını zaman adına göre bul ve sil.

**Başarı kriterleri:**
- Rastgele bir aralık sorgusunun sonucu, tüm verinin düz taramasıyla birebir aynı.
- Düzenli bir 1 Hz akışta nokta başına bit sayısı ölçülmüş ve raporlanmış.
- Downsampling sonrası toplam dosya boyutu, ham hâle göre belirgin şekilde küçük.

### Ek Alıştırmalar

Aşağıdaki problemlerin çözümü bu kitapta yok. Önce kâğıda, sonra editöre geç; yapay zekâ yasak. Zorluk etiketine göre sırala.

1. **★ — Mezar taşı neden gerekli?** Bir anahtar silinmiş ama eski bir SSTable'da hâlâ duruyor. Silme işlemi mezar taşı yazmasaydı `get` ne döndürürdü? Neden birleştirme öncesi mezar taşını atamazsın?
2. **★ — Bloom'da silme.** Bir Bloom filtresinden bir elemanı silmek neden doğrudan mümkün değil? Her bit yerine bir sayaç koysaydın ne kazanır, ne kaybederdin?
3. **★ — Tutarlı hash'te düğüm çıkarma.** Düğüm C halkadan çıkarılırsa taşınan anahtarlar nereye gider? Bu, ekleme işlemiyle simetrik mi?
4. **★★ — Yazma yükseltmesi hesabı.** Bir LSM'de her kayıt 10 kez birleştirilerek yeniden yazılıyor (ortalama). Kullanıcı 1 GB yazarsa diske yaklaşık kaç GB yazılır? Bu sayı B+ ağacında neden farklı olur?
5. **★★ — Mülakat: iki lider.** İki veri merkezinde aynı anahtara eş zamanlı iki farklı değer yazıldı. Son yazma kazanır kuralı hangi durumda veri kaybettirir? Bu kuralın yerine geçebilecek bir çakışma çözümü öner.
6. **★★ — Mülakat: CAP'in yanlış yorumu.** "Bizim sistemimiz CA, yani CAP'i aşıyoruz" diyen bir ekip var. Bir ağ bölünmesi olduğunda ne olur? Bu iddiayı nasıl çürütürsün?
7. **★★ — Mülakat: Bloom ve önbellek.** Bir önbellek önünde Bloom filtresi kullanmak yanlış pozitifleri nasıl etkiler? Yanlış pozitif olan bir sorgu önbellekte bulunmayan bir değeri veritabanından aramaya zorlar; bunun bedelini nasıl ölçersin?
8. **★★ — Mülakat: belge mi, ilişkisel mi?** Bir e-ticaret sitesi ürün kataloğunu ve sipariş geçmişini nasıl modellemeli? Hangi kısmı belge, hangisini ilişkisel tutarsın ve neden?
9. **★★ — Mülakat: zaman damgası sırası.** Telemetri paketleri ağda sırasız gelirse LSM tabanlı bir zaman serisi deposu bunu nasıl ele alır? Sırasız bir yazma, sıralı SSTable varsayımını nasıl bozar?
10. **★★★ — Mülakat: quorum ve onarım.** `R + W > N` olsa bile bir kopya uzun süre eski değer tutabilir. Bu bayatlığı azaltmak için hangi mekanizmalar gerekir (okuma onarımı, arka plan karşılaştırması)? Bu mekanizmaların bedeli nedir?
11. **★★★ — Mülakat: önbellek stampede'i.** Bir ürün sayfası saniyede 10 000 istek alıyor ve önbellek TTL'i dolduğunda hepsi veritabanına gidiyor. Tek bir isteğin veritabanına gitmesini sağlayan bir tasarım çiz; eşzamanlılık sorunlarını (kilit bekleme, zaman aşımı) tartış.
12. **★★★ — Mülakat: LSM ve SSD.** SSD'lerde rastgele yazma pahalıdır ama sıralı yazma ucuzdur. LSM bu donanım gerçeğiyle nasıl uyumlu, ama aynı zamanda nasıl bir sorun yaratır (yazma yükseltmesi, aşınma)?

## Kod Okuma Egzersizi

Bu bölümde Bloom filtresinin **gerçek** bir gerçeklemesini okuyacaksın. Kaynak: LevelDB **1.23** sürümü, `util/bloom.cc` dosyası. Dosya, `google/leveldb` deposunun 1.23 etiketinden (raw.githubusercontent.com üzerinden) indirildi ve birebir alındı. **Sadeleştirme:** lisans başlığı (dosyanın ilk 4 satırı) ve `#include` satırları çıkarıldı; 70 karakteri aşan on satır, anlam değişmeden iki satıra bölündü (ya da yorum satırı yukarı alındı). Hiçbir kod satırı silinmedi veya değiştirilmedi.

```cpp
namespace leveldb {

namespace {
static uint32_t BloomHash(const Slice& key) {
  return Hash(key.data(), key.size(), 0xbc9f1d34);
}

class BloomFilterPolicy : public FilterPolicy {
 public:
  explicit BloomFilterPolicy(int bits_per_key)
      : bits_per_key_(bits_per_key) {
    // We intentionally round down to reduce probing cost a little bit
    k_ = static_cast<size_t>(bits_per_key * 0.69);  // 0.69 =~ ln(2)
    if (k_ < 1) k_ = 1;
    if (k_ > 30) k_ = 30;
  }

  const char* Name() const override {
    return "leveldb.BuiltinBloomFilter2";
  }

  void CreateFilter(const Slice* keys, int n,
                    std::string* dst) const override {
    // Compute bloom filter size (in both bits and bytes)
    size_t bits = n * bits_per_key_;

    // For small n, we can see a very high false positive rate.
    // Fix it by enforcing a minimum bloom filter length.
    // by enforcing a minimum bloom filter length.
    if (bits < 64) bits = 64;

    size_t bytes = (bits + 7) / 8;
    bits = bytes * 8;
```

```cpp
    const size_t init_size = dst->size();
    dst->resize(init_size + bytes, 0);
    // Remember # of probes in filter
    dst->push_back(static_cast<char>(k_));
    char* array = &(*dst)[init_size];
    for (int i = 0; i < n; i++) {
      // Use double-hashing to generate a sequence of hash values.
      // See analysis in [Kirsch,Mitzenmacher 2006].
      uint32_t h = BloomHash(keys[i]);
      // Rotate right 17 bits
      const uint32_t delta = (h >> 17) | (h << 15);
      for (size_t j = 0; j < k_; j++) {
        const uint32_t bitpos = h % bits;
        array[bitpos / 8] |= (1 << (bitpos % 8));
        h += delta;
      }
    }
  }

  bool KeyMayMatch(const Slice& key,
                   const Slice& bloom_filter) const override {
    const size_t len = bloom_filter.size();
    if (len < 2) return false;

    const char* array = bloom_filter.data();
    const size_t bits = (len - 1) * 8;

    // Use the encoded k so that we can read filters generated by
    // bloom filters created using different parameters.
    const size_t k = array[len - 1];
    if (k > 30) {
      // Reserved for potentially new encodings for short bloom
      // filters.
      // Consider it a match.
```

```cpp
      return true;
    }

    uint32_t h = BloomHash(key);
    // Rotate right 17 bits
    const uint32_t delta = (h >> 17) | (h << 15);
    for (size_t j = 0; j < k; j++) {
      const uint32_t bitpos = h % bits;
      if ((array[bitpos / 8] & (1 << (bitpos % 8))) == 0)
        return false;
      h += delta;
    }
    return true;
  }

 private:
  size_t bits_per_key_;
  size_t k_;
};
}  // namespace

const FilterPolicy* NewBloomFilterPolicy(int bits_per_key) {
  return new BloomFilterPolicy(bits_per_key);
}

}  // namespace leveldb
```

**Sorular — cevaplamadan geçme:**

1. `k_` bir `bits_per_key * 0.69` ile hesaplanıyor ve `static_cast<size_t>` ile kesiliyor. Bu, Bölüm 35.6'daki `k = (m/n) ln 2` optimumuna nasıl karşılık gelir? `bits_per_key = 10` için `k_` kaç olur ve bu değer neden yaklaşık 0,84% yanlış pozitif verir?
2. `CreateFilter` içinde `bits` en az 64 olacak şekilde zorlanıyor. Yorumda neden "küçük n için çok yüksek yanlış pozitif" denmiş? Bölüm 35.6'daki formülle bu durumu kendin hesapla.
3. Her eleman için tek bir `BloomHash` çağrısı yapılıyor ve `delta` ile bitler türetiliyor: `h += delta`. Bu, Bölüm 35.6'da kullandığımız çift hash tekniğinin hangi versiyonu? İki bağımsız hash yerine neden tek hash ve bir döndürme (rotate) yeterli?
4. `KeyMayMatch` içinde `k > 30` ise `true` dönüyor ve "ayrılmış kodlama" yorumu var. Filtrenin son baytı neden `k`'yı tutuyor? Bu tasarım, farklı parametrelerle yazılmış filtrelerin okunmasını nasıl mümkün kılar?
5. `bits = (len - 1) * 8` hesabı, filtrenin son baytının (`k`) dışında kalan kısmını bit sayısı olarak alıyor. Filtre dizisinin uzunluğu ile `bits` arasındaki ilişkiyi bir örnekle açıkla.
6. Bu kod bir **bit silme** desteği sunmuyor. Bölüm 35.6'daki bit silinemezlik argümanı ile LevelDB'nin tercihi arasında bir bağ kur: LSM'de filtreler zaten değişmez SSTable'lara bağlı olduğu için silmeye neden ihtiyaç yok?

## Bölüm Özeti

- NoSQL, ilişkisel modelin ölçek, şema esnekliği ve dağıtık birleştirme sürtünmelerine karşı, her biri belirli bir erişim desenine göre optimize edilmiş ailelerden oluşur: anahtar-değer, belge, geniş sütun, graf, zaman serisi. Seçim, verinin ana erişim desenine göre yapılır.
- Depolama motorunun iki ana yaklaşımı vardır: yerinde güncelleyen B+ ağacı (okuma güçlü, yazma rastgele) ve sıralı ekleyen LSM ağacı (yazma güçlü, okuma birden çok dosyaya bakar). Bunun bedeli yazma, okuma ve alan yükseltmesi arasında bir dengedir.
- Bir LSM deposunda memtable, sıralı SSTable'lar, Bloom filtresi, mezar taşı ve birleştirme birlikte çalışır; testle doğrulanmayan bir LSM güvenilmez. Bilerek hatalı bir sürümün 4 377 hata üretmesi, testin gerçekten hata yakaladığını gösterir.
- Bloom filtresi "kesinlikle yok" cevabını kesin, "muhtemelen var" cevabını olasılıksal verir. Yanlış pozitif oranı `(1 - e^(-kn/m))^k` ile hesaplanır; `k = (m/n) ln 2` civarında optimum vardır ve LSM'de okuma yükseltmesini 77 tablodan 1,7 okumaya indirdi.
- Tutarlı hash, düğüm eklenince yalnızca yaklaşık `1/(n+1)` anahtarı taşır; naif `hash % N` ise çoğunu taşır. Sanal düğümler yük dengesini de iyileştirir.
- CAP teoremi, bölünme anında tutarlılık ile erişilebilirlik arasında seçim zorunluluğunu söyler; PACELC bunu bölünme yokken de gecikme ile tutarlılık arasında bir seçim olarak genişletir. Quorum `R + W > N` bayat okumayı engeller, ama sürüm çatışmasını çözmez.
- Belge modelinde gömme okumayı hızlandırır ve tekrar bedeli öder; referans tutarlılığı korur ama birden çok sorgu ister. Şema esnekliği, şemayı uygulama koduna taşır.
- Zaman serisi verisi ekle-yaz ağırlıklıdır; delta-of-delta sıkıştırma düzenli zaman damgalarında nokta başına 1 bite kadar iner, titreme arttıkça bu artar. Downsampling ve saklama politikası uzun vadeli maliyeti sınırlar.
- Önbellek kalıpları (cache-aside, write-through, write-back, TTL, stampede koruması) kaynakla tutarlılık ve gecikme arasındaki dengeyi yönetir.

**Kısım VIII'in kapanışı.** Bu bölümle Kısım VIII, Veritabanı, tamamlandı. Bölüm 33'te verinin **yapısını** (ilişkisel model, normalizasyon, B+ ağacı, ACID teorisi), Bölüm 34'te bu yapıyı **sorgulamayı** (SQL, indeksler, işlemler pratikte) ve Bölüm 35'te verinin **ölçek ve dağıtım** altında nasıl tutulacağını gördün. Üçü birlikte tek bir resmi tamamlar: bir veritabanı, diskteki baytlardan başlayıp birden çok makineye yayılan bir tutarlılık sözleşmesine kadar uzanan bir yığındır. Bölüm 28'deki `fsync` ve yazma sırası kuralı, bu üç bölümde her katmanda yeniden ortaya çıktı.

**Sonraki bölümde:** Bölüm 36 (Formal Diller) ile Kısım IX — Otomata & Derleme başlıyor. Bu bölümde gördüğün "bir kuralı kesin olarak tanımlama" fikri, sorgu dillerinden bir programlama dilinin söz dizimine kadar uzanan biçimsel dillerin temelini oluşturacak. Bir LSM'nin okuma sırasını tanımlayan kuralın ardında, düzenli ifadeler ve sonlu otomatlar gibi bir dil tanımının sezgisi var.

::: mulakat
Aşağıdaki sorular cevapsız bırakılmıştır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. Bir LSM deposunda silinmiş bir anahtar hâlâ diskte duruyorsa, okuma neden yine de doğru sonuç döner? Mezar taşı olmasaydı hangi tutarsızlık ortaya çıkardı?
2. Bloom filtresinde yanlış pozitif oranı neden eleman sayısı arttıkça yükselir? Bit sayısını sabit tutup `n` iki katına çıkarsan oranın yaklaşık ne olacağını tahmin edebilir misin?
3. Tutarlı hash halkasına tek bir sanal düğüm (`v = 1`) koymak neden yük dengesini bozar? Sanal düğüm sayısını artırmanın bir bedeli var mı?
4. Bir sistem `R = 1, W = 1, N = 3` ile çalışıyor. Bayat okumayı azaltmak için hangi tek değişikliği yaparsın ve bu değişikliğin gecikmeye etkisi ne olur?
5. CAP teoreminde "bölünme" ne demektir? Bir veri merkezi içindeki ağ kesintisi ile iki bölge arasındaki bağlantı kesintisi aynı sonuçları mı doğurur?
6. Bir belge veritabanına sipariş ve müşteri verisini tek belgede mi, ayrı belgelerde mi koyarsın? Hangi okuma ve yazma desenleri bu kararı değiştirir?
7. Zaman serisi verisinde tek bir büyük boşluk (ör. bir saatlik kesinti) delta-of-delta sıkıştırmasını nasıl etkiler? Sonraki noktalar neden hemen düzelmez?
8. Bir önbellekte TTL kullanıyorsun ama veri değiştiğinde önbelleği hemen silmek istiyorsun. Cache-aside ile bunu nasıl tasarlarsın ve hangi yarış koşulu ortaya çıkabilir?
:::
