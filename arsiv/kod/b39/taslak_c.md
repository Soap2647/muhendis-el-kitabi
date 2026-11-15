## Kendin Yap Projeleri

::: dikkat
Yapay zekâ kullanımı yasak. Bu bölümün projeleri test yazma kasını geliştirmek için var; testi bir araca ürettirirsen sınadığın şey aracın kararıdır, senin değil. Testleri kendin yaz, kırmızıyı kendin gör.
:::

### Proje 1 (★★): Mini test çatısı

**Amaç:** pytest'in arkasındaki üç mekanizmayı (keşif, fixture ve parametrize) kendi elinle kurmak. Amaç pytest'in tamamını yazmak değil; keşif, parametrize ve hata raporunun nasıl çalıştığını görmek.

**Yapılacak:** Yalnızca standart kütüphane (`importlib`, `inspect`, `traceback`) ile küçük bir çatı yaz. Çatı şunları yapsın:

- Verilen bir `.py` dosyasında `test_` ile başlayan fonksiyonları bulup çalıştırsın (keşif).
- `@parametrize(parametre_adi, [degerler])` süsleyicisi ile bir testi çok girdiyle koştursun; her satır ayrı raporlansın.
- Parametre adı bir `@fixture` fonksiyonunun adıyla eşleşirse fixture'ı çağırıp değerini versin.
- Sonunda geçen ve kalan sayısını, her başarısız testin adını ve hata metnini yazdırsın; başarısızlık varsa çıkış kodu 1 olsun.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** Keşif için modül nesnesinde `dir()` ve `callable` kullan. Parametrize'ı bir fonksiyon özniteliği olarak sakla (`f.parametreler = ...`), koşturucu o özniteliği okusun. Fixture çözümlemesinde `inspect.signature(f).parameters` ile parametre adlarını al. Hata metni için `traceback.format_exc()` yeterlidir.

**Başarı kriterleri:**

- Bölüm 39.4'teki `test_tarih.py` dosyasının parametrik kısmını (`test_sinir_degerler`) kendi çatında koşturabiliyorsun ve 13 satırın her biri ayrı raporlanıyor.
- Kasıtlı olarak bir girdiyi bozduğunda çatın hangi satırın kırıldığını ve beklenen/gerçek değeri söylüyor.
- Bir fixture'ı iki farklı test paylaşıyor ama her test kendi kopyasını alıyor (çatında fixture her testte yeniden çağrılıyor).

### Proje 2 (★★★): Çerçeve okuyucuyu test paketiyle sarmak ve mutasyon skoru hedeflemek

**Amaç:** Bölüm 31.4'teki uzunluk önekli çerçeve okuyucuyu bir test paketiyle sarıp bu paketin kalitesini mutasyon skoruyla ölçmek. Bu proje, Bölüm 39'un tüm araçlarını (birim, sınır, özellik, entegrasyon, mutasyon) bir arada kullanır.

**Yapılacak:** Bölüm 39.10'daki `cerceve.py` dosyasını temel al. Şu davranışları sınayan bir paket yaz:

- **Birim:** uzunluk 0 olan çerçeve; uzunluk tam olarak `MAKS` olan çerçeve (kabul edilmeli); `MAKS + 1` (`ValueError` fırlatmalı).
- **Özellik:** rastgele bir yük (`hypothesis` ile) bir çerçeveye konduktan sonra, gönderici onu rastgele parçalara bölerek yazsın; alıcı yükü aynen geri okusun.
- **Entegrasyon:** `socketpair` üzerinden iki yönlü, art arda birkaç çerçeve.
- **Mutasyon:** 39.7'deki `mutasyon.py` aracını bu dosyaya uygula ve skoru ölç.

**Önerilen yaklaşım (ipucu, tam çözüm değil):** `tam_oku` içindeki döngünün kapanış koşulunu ve `recv` boş dönüş durumunu ayrı birer test olarak düşün. Mutasyon skorunda hayatta kalan mutantları tek tek incele: birçoğu `MAKS` sınırıyla ilgili olacaktır (`>` ile `>=` farkı gibi). Eşdeğer bir mutant çıkarsa bunu bir cümleyle gerekçelendir.

**Başarı kriterleri:**

- Paket, `cerceve.py` üzerindeki mutasyon skorunun en az %90 olduğunu gösteriyor. Skoru ve hayatta kalan mutantların listesini raporla.
- Hayatta kalan her mutant için ya bir test eklenmiş ya da eşdeğer olduğu gerekçelendirilmiş.
- Paket, her çalıştırmada aynı sonucu veriyor (tohum sabit, sıra bağımsız).

### Ek Alıştırmalar

**Zorluk etiketleri:** ★ kolay, ★★ orta, ★★★ zor. Mülakat etiketli sorular klasik mülakat problemleridir; önce yalnızca test listesini yaz, sonra kodu yaz.

1. **(★) Palindrom.** `palindrom_mu(s)` için test listesi yaz: boş metin, tek karakter, büyük-küçük harf, boşluk ve noktalama, Türkçe karakterler (`"Kayak"`, `"İstanbul"`). Hangi girdi için testin hangi durumu sınadığını tek cümlede açıkla.
2. **(★★) İki toplam (Mülakat).** Bir dizide iki elemanın toplamı hedefe eşit olan bir çift bulan fonksiyon için test listesi yaz. Negatif sayılar, aynı elemanın iki kez kullanılması, hedefin hiç bulunmaması ve boş dizi durumlarını ekle. Sonra karma tabloyla `O(n)` çözümünü yaz ve testlerle doğrula.
3. **(★★) Min'li yığın (Mülakat).** `push`, `pop` ve `min` işlemleri olan ve `min` işlemini `O(1)` tutan bir yığın için TDD ile çalış: kırmızı testleri sırayla yaz, her turda yeşil kodu ve yeniden düzenlemeyi göster.
4. **(★) Fizz–Buzz parametrize tablosu.** 1 ile 30 arasındaki sayılar için beklenen çıktıyı bir `parametrize` tablosuna yaz. 3'ün, 5'in ve 15'in katlarını ayrı satırlarda kapsa.
5. **(★★★) LRU önbellek (Mülakat).** Kapasiteli bir LRU önbelleği için test senaryolarını yaz: kapasite dolunca en az kullanılanın atılması, `get` işleminin bir girdiyi "yeni" yapması, aynı anahtara yeniden `put` yapmanın değeri güncellemesi. Testler kodundan önce yazılmalı.
6. **(★★) İkili aramayı sına.** Bölüm 39.8'deki `ikili_arama_hatali` için bir özellik testi yetiyor mu? Hatayı yakalamayan ama yakalayan üç farklı girdi kümesi tasarla ve neden yakalamadığını açıkla. (Bölüm 14.5'teki off-by-one kataloğu bu konuda yardımcı olur.)
7. **(★) Fake mi, mock mu?** `test_siparis.py` içindeki `BellekDeposu` yerine bir `Mock()` kullanan bir test yazsaydın neyi kaybederdin? Bir cümleyle yaz ve kırılganlığın kaynağını göster.
8. **(★★) Üç mutant.** `ortalama` fonksiyonu için (Bölüm 39.6'daki `kapsama_ornek.py`) üç mutant tasarla: biri `//` yerine `/` koyar, biri boş liste kontrolünü kaldırır, biri `len(xs)` yerine `len(xs) + 1` yazar. Bu mutantlardan hangisinin mevcut testlerle hayatta kalacağını tahmin et, sonra çalıştır.
9. **(★★★) Kararsız test istatistiği (Mülakat).** Bir testin yaklaşık %2 olasılıkla kaldığını gözlemledin. Bunu güvenilir biçimde ayırt etmek için kaç koşu gerekir? Bir kalma oranı için güven aralığını nasıl hesaplarsın ve testi "kararlı" ilan etmek için hangi kriteri koyarsın?
10. **(★★) Başka bir MC/DC kümesi.** `(A or B) and C` kararı için dört testlik bir MC/DC kümesi türet. Sonra Örnek 3'teki `mcdc.py` aracının `karar` fonksiyonunu bu yeni karara göre değiştir ve kümeni araçla doğrula.
11. **(★★★) Disk dolu simülasyonu (Mülakat).** Bir dosyaya satır yazan `kaydet(yol, satirlar)` fonksiyonu için test yaz. `tmp_path` kullan. Disk dolu durumunu (yazma sırasında `OSError`) nasıl simüle edersin? Gerçek bir dolu disk olmadan bunu yapabilmek neden önemlidir?
12. **(★★) Halka tamponunun boş kenarı.** Bölüm 39.9'daki `HalkaTampon(0)` çağrısı `ValueError` fırlatmalı. Bu davranışı sınayan testi yaz; önce kırmızı olduğunu göster ya da neden zaten yeşil olduğunu açıkla.

## Kod Okuma Egzersizi

Bugünkü kesit, CPython 3.12.10'un `Lib/bisect.py` dosyasındaki `bisect_right` fonksiyonunun gövdesidir. Kaynak, yerel kurulumdaki `C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\bisect.py` dosyasından birebir alındı; yalnızca belgeleme dizesi (docstring) çıkarıldı ve yorumlar korundu:

```python
def bisect_right(a, x, lo=0, hi=None, *, key=None):
    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    # Note, the comparison uses "<" to match the
    # __lt__() logic in list.sort() and in heapq.
    if key is None:
        while lo < hi:
            mid = (lo + hi) // 2
            if x < a[mid]:
                hi = mid
            else:
                lo = mid + 1
    else:
```

Fonksiyonun geri kalanı (`key` dalı) aynı döngüyü `key(a[mid])` ile yapar; burada gösterilmedi. Bu bir **kısaltılmış kesittir**; kaynağın orijinal satırları değiştirilmedi.

**Sorular — cevaplamadan geçme:**

- Döngü `while lo < hi` ile yazılmış, `<=` ile değil. Bölüm 14.2'deki döngü değişmezine göre `[lo, hi)` yarı açık aralığı burada neyi temsil eder? Dizinin son elemanı (`hi = len(a)`) neden hiçbir zaman karşılaştırılmaz ama yine de doğru sonuç çıkar?
- `mid = (lo + hi) // 2` satırı, Bölüm 14.3'te anlatılan taşma sorununu Python'da yaşatır mı? C'de `lo + (hi - lo) / 2` neden yazılır?
- `if x < a[mid]` karşılaştırmasında yalnızca `<` kullanılıyor. Bu, `bisect_right` ile `bisect_left` arasındaki farkı nasıl belirler? Eşit elemanlar dizide varsa dönüş değeri nerede durur?
- `lo < 0` kontrolü neden fonksiyonun başında yapılıyor? Bu kontrolü sınayan bir test yazsaydın hangi girdi ile yazardın ve bu test hangi mutantı öldürürdü?
- Aynı davranış `sorted` ve `dict` gibi yerleşiklerde de geçerli mi? Hangi test kalıbı (özellik mi, diferansiyel mi) bu fonksiyonun doğruluğunu daha güçlü kanıtlar; neden?
- `key` argümanı eklenince testlerin kapsaması nasıl değişir? Dal kapsaması (39.6) bu iki yolu ayrı ayrı göstermek için hangi testleri ister?

## Bölüm Özeti

Bu bölümde testin neden yazıldığından başlayıp kanıtın sınırlarına kadar gittik:

- **Test üç işe yarar:** hızlı geri bildirim, regresyon koruması ve tasarım baskısı. Ama hiçbir test hataların yokluğunu kanıtlamaz; yalnızca sınadığı durumları doğrular.
- **Test piramidi:** çok birim testi, daha az entegrasyon, en az uçtan uca. Test kupası bu oranın tersidir ve kırılgandır.
- **İyi birim testi:** AAA yapısı, tek davranış, deterministik, hızlı, bağımsız ve açık adlandırılmış.
- **pytest:** keşif, `assert` yeniden yazımı, fixture kapsamları, `parametrize`, `skip` ve `xfail`, `approx` ile kayan nokta toleransı.
- **Test ikizleri:** fake ve spy ile davranışı, mock ile etkileşimi sına. Dış sınırda mock kullan; iç çağrıları mock'lamak uygulamaya bağlı kırılgan testler üretir.
- **Kapsama:** satır ve dal kapsaması farklı şeyler ölçer; %100 kapsama hatasızlık demek değildir (Örnek 1'deki `ortalama` hatası buna örnektir).
- **Mutasyon testi:** küçük hatalar enjekte edip test setinin onları yakalayıp yakalamadığını ölçer; hayatta kalan her mutant ya bir test boşluğu ya da eşdeğer bir mutanttır.
- **Özellik tabanlı test ve küçültme:** Hypothesis özelliği rastgele girdilerle sınar ve karşı örneği en küçük haline indirir. Diferansiyel test (referans gerçeklemeye karşı) Bölüm 13 ve 16'daki çapraz test disiplininin genelleşmiş hâlidir.
- **TDD:** kırmızı, yeşil, yeniden düzenle; kırmızıyı görmeden yazılan test bir şey kanıtlamaz.
- **Kararsız testler:** zamanlama, sıra bağımlılığı, rastgelelik ve paylaşılan durum. Tekrarlı çalıştırma ile bulunur, tohum, fixture ve izolasyon ile düzeltilir.
- **Savunma sanayiinde test:** iz sürülebilirlik, MC/DC (DO-178C DAL A için) ve donanım-döngüde test (HIL).

**Sonraki bölümde:** Bölüm 40 — API Tasarımı. Testlerin sınadığı şey bir arayüzdür; bu bölümde gördüğümüz bağımlılık enjeksiyonu ve sözleşme düşüncesi, bir arayüzü tasarlarken nasıl kararlar aldığımızı belirleyecek. Bölüm 40'ta bu sözleşmeleri, sürümlemeyi ve hata modellerini ayrıntılı göreceğiz.

::: mulakat
Klasik sorular — hemen cevaplamaya çalışma, her birini birkaç dakika düşün:

1. Bir birim testi ile bir entegrasyon testi arasındaki fark nedir? Hangisini ne zaman yazarsın ve neden?
2. Fake ile mock arasındaki farkı bir örnekle açıklar mısın? Hangi durumda mock kullanmak zararlıdır?
3. %100 dal kapsaması olan bir test paketinin hâlâ hata kaçırabileceğini nasıl gösterirsin?
4. Mutasyon testi, kapsamadan neyi fazladan ölçer? Eşdeğer mutant neden skoru bir üst sınır olmaktan çıkarır?
5. Kararsız bir testi nasıl bulur, nasıl düzeltirsin? Tohumu sabitlemek her zaman doğru çözüm müdür?
6. TDD'de kırmızı adımı atlamak neden tehlikelidir? Bir testin hiç kırmızı olmadan geçtiğini görmek ne anlama gelir?
7. MC/DC ile dal kapsaması arasındaki fark nedir? `(A and B) or C` kararında neden en az n + 1 test gerekir?
8. Bir hatayı düzelttikten sonra regresyon testi yazmak neden tek başına yeterli değildir; testi nasıl doğrularsın?
:::
