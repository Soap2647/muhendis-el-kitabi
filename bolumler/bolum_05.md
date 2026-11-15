%% kisim_no: II
%% kisim_ad: Problemi Çözmeyi Öğrenmek
%% kisim_ayrac: evet
%% bolum_no: 5
%% baslik: Problemi Parçala

## Giriş: Boş ekran korkusu

Kısım I'i bitirdin. İki dil biliyorsun, belleğin nasıl çalıştığını görüyorsun, derleyiciyi ve hata ayıklayıcıyı kullanabiliyorsun. Şimdi seni bir odaya alıp beyaz tahtanın önüne dikiyorum ve şunu diyorum: *"Bir dizi verilmiş; içinde toplamı belirli bir hedefe eşit olan iki sayının indekslerini bul."*

Eğer bu anda içinden "hangi fonksiyonu çağırsam?" geçtiyse, bu bölüm tam olarak senin için yazıldı. Çünkü sorun bilgi eksikliği değil. Sözdizimini biliyorsun, `for` döngüsünü de biliyorsun, sözlüğün ne olduğunu da. Eksik olan şey **bilgiyi harekete çeviren süreç**.

Bu ayrımı net görmen lazım: **bilgi** ile **beceri** aynı şey değildir. Yüzme kitabını ezberleyen biri suya atıldığında batar. Programlamada da böyle: dilin tüm anahtar kelimelerini bilmek, boş bir dosyanın karşısında ne yazacağını bilmek anlamına gelmiyor. AI araçlarıyla çalışırken bu fark görünmez, çünkü "ne yazacağım" sorusunu senin yerine başkası cevaplıyor. Sen kodu *okuyor*, *onaylıyor*, *yapıştırıyorsun*. Bu, yüzme videosu izlemeye benziyor — faydalı ama havuzda işe yaramıyor.

Bu bölümün vaadi şu: sana **her problemde uygulanabilen, tekrarlanabilir bir süreç** vereceğim. Beyaz tahtada donduğun anda sığınabileceğin bir çerçeve. Bu çerçeve sihirli değil — zeki insanların yıllarca yaparak edindiği alışkanlıkların adı konmuş hâli. Ama adı konduğu an öğretilebilir hâle geliyor, ve öğrenilebilir olan her şey pratikle reflekse dönüşüyor.

Bir uyarı da baştan: bu bölümde çok az yeni *bilgi* var. Buradaki her şey zaten yapabileceğin şeyler. Zor olan, onları **doğru sırayla** ve **disiplinle** yapmak. Bu yüzden bölümün değeri okumakta değil, uygulamakta. Sonundaki projeleri atlarsan bölümü boşa okumuş olursun.

::: not
Savunma sanayii mülakatlarının teknik ayağı neredeyse her zaman böyle geçer: sana bir problem verilir ve *düşünme sürecini* izlerler. Doğru cevaba ulaşman tek başına yetmez; nasıl ulaştığın, hangi soruları sorduğun, kısıtları nasıl kullandığın değerlendirilir. Sessizce oturup mükemmel kodu bir anda yazan aday, yüksek sesle düşünüp kaba çözümden optimuma yürüyen adaydan daha az puan alır. Bu bölüm, o yürüyüşün haritasıdır.
:::

## 5.1 Neden tıkanıyoruz? Üç yaygın tuzak

Tıkanmanın kaynağını bilmek, çözümün yarısıdır. Öğrencilerin (ve mühendislerin) problem karşısında donmasının üç tipik sebebi var; muhtemelen üçünü de tanıyacaksın.

**Birinci tuzak: doğrudan kodu düşünmek.** Problemi okur okumaz zihnin `for` döngüleri kurmaya başlar. Henüz problemi anlamadan çözüm aramaya girişirsin. Bu, haritaya bakmadan araba sürmek gibidir — hareket ediyorsun ama nereye gittiğin belirsiz. Kod, düşüncenin *son* adımıdır; ilk adımı olduğunda ortaya karmakarışık bir şey çıkar.

**İkinci tuzak: mükemmel çözümü ilk seferde arama.** "O(n) bir çözüm olmalı" diye düşünüp kaba kuvvetle başlamayı reddedersin. Sonuç: hiçbir şey yazamazsın. Oysa çalışan yavaş bir çözüm, hiç çözüm olmamasından *sonsuz kat* iyidir; üstelik optimizasyonun çıkış noktası odur. Mükemmeliyetçilik burada verimsizliğin kılık değiştirmiş hâlidir.

**Üçüncü tuzak: örüntü dağarcığının boş olması.** Bir problemi çözebilmek için önce onun *neye benzediğini* görmen gerekir. Usta bir mühendisin "bu bir kayan pencere problemi" demesi dehâ değil, **tanımadır** — daha önce yirmi benzerini görmüştür. Bu dağarcık okumakla değil, çözmekle dolar. Kısım III ve IV bu dağarcığı sistemli olarak inşa edecek; bu bölüm sana onu *kullanmayı* öğretiyor.

Bu üç tuzağın da panzehiri aynı: yapılandırılmış bir süreç. Şimdi onu kuralım.

## 5.2 Altı adımlı döngü

İşte çerçeve. Altı adım, ve önemli olan sırası:

![Şekil 5.1: Problem çözme döngüsü. Altı adım sırayla ilerler ama tek yönlü değildir: örüntü tutmazsa kaba çözüme, test patlarsa en başa dönülür. Her geri dönüş bir başarısızlık değil, problem hakkında yeni bilgiyle donanmış ikinci bir denemedir.](gorseller/b05_cycle.png)

Adımların özeti şöyle:

1. **Anla** — Girdi nedir, çıktı nedir, kısıtlar neler? Problemi kendi cümlelerinle yeniden ifade edebiliyor musun?
2. **Örnekle** — Küçük bir örneği elle çöz. Kenar durumları yaz. Çözümü *görmeden* önce problemi *gör*.
3. **Kaba çöz** — Aklına gelen en aptal çalışan çözümü yaz. Yavaş olsun, çirkin olsun, ama *çalışsın*.
4. **Örüntü bul** — Bu problem neye benziyor? Hangi tanıdık desen buraya oturur?
5. **İyileştir** — Darboğazı bul, kaldır. Genelde bir takas (bellek ↔ zaman) yaparak.
6. **Doğrula** — Kenar durumlarla test et, karmaşıklığı hesapla, kodu elle iz sür.

Bu altı adımı ezberlemene gerek yok; anlaman yeterli. Ama uygularken **atlamamalısın**. En sık atlanan adım ikincisidir (örnekleme) ve en pahalıya patlayan da odur: elle bir örnek çözmeden yazılan kodun doğru olma ihtimali düşüktür, çünkü ne yapması gerektiğini kendin de tam bilmiyorsundur.

Şimdi her adımı tek tek, derinlemesine açalım.

## 5.3 Adım 1: Anla — problemi kazımak

Bu adımın çıktısı üç şeydir: **girdi imzası**, **çıktı imzası**, **kısıtlar**. Bu üçünü net yazamıyorsan, problemi anlamamışsın demektir.

### Girdi ve çıktıyı imzaya dökmek

Problemi bir fonksiyon imzasına çevirmek, belirsizliği öldürmenin en hızlı yoludur. "Toplamı hedefe eşit iki sayı bul" cümlesi bulanıktır; şu değildir:

```python
def iki_toplam(sayilar: list[int],
               hedef: int) -> tuple[int, int] | None:
    """toplamı hedef olan iki elemanın İNDEKSLERİNİ döndürür."""
```

İmzayı yazar yazmaz onlarca soru netleşir: Girdi liste mi, sıralı mı? Elemanlar tam sayı mı, negatif olabilir mi? Çıktı indeks mi, değerin kendisi mi? Bulunamazsa ne dönüyor — `None` mı, boş liste mi, istisna mı? Birden fazla çözüm varsa hangisi?

Bu soruların cevabı problemde yoksa **sormalısın**. Mülakatta soru sormak zayıflık değil, en güçlü sinyaldir: gerçek işte de gereksinimler hep eksik gelir, iyi mühendis eksiği fark edip sorandır. Sorulacak soruların standart bir listesi vardır:

| Soru | Neden önemli |
|---|---|
| Girdi boş olabilir mi? | En sık atlanan kenar durum |
| Tekrarlı eleman olabilir mi? | Küme/sözlük seçimini değiştirir |
| Negatif sayı / sıfır var mı? | Birçok "hızlı" numarayı bozar |
| Girdi sıralı mı? | Sıralıysa ikili arama ve iki işaretçi açılır |
| Çözüm yoksa ne dönmeli? | Sözleşmenin parçası |
| Birden çok çözüm varsa? | Herhangi biri mi, en küçüğü mü? |
| Girdiyi değiştirebilir miyim? | Yerinde çalışma iznin var mı? |
| n en fazla kaç? | **Algoritmayı doğrudan belirler** |

### Kısıtlar sana algoritmayı söyler

Bu listenin son maddesi, bölümün belki de en pratik bilgisidir. Bir problemde `n ≤ 100000` yazıyorsa bu bir süs değil, **açık bir talimattır**. Modern bir işlemci saniyede kabaca 10⁸ basit işlem yapar. Buradan geriye doğru çalışırsan hangi karmaşıklığın kabul edilebilir olduğunu daha kod yazmadan bulursun:

![Şekil 5.2: Kısıt-karmaşıklık haritası. Problemin verdiği n üst sınırına bakıp hangi karmaşıklık sınıfının zaman limitine sığacağını okursun. Bu tablo, "hangi yaklaşımı deneyeyim?" sorusunu daha başlamadan daraltır.](gorseller/b05_bands.png)

Bu tabloyu tersten okumayı öğren, çünkü asıl gücü orada. `n = 10⁵` gördüğün an, O(n²) çözümün 10¹⁰ işlem demek olduğunu (yani ~100 saniye) hesaplar ve o yolu **daha yazmadan elersin**. Aynı şekilde `n ≤ 20` gördüğünde "burada üstel çözüm bekleniyor, muhtemelen tüm alt kümeleri denemem isteniyor" dersin — kısıt sana çözümün *türünü* fısıldar.

Bu refleks yalnız mülakatta değil, gerçek işte de hayat kurtarır. `ÖZCE`'de bir kodek denemesi tasarlarken "kaç örnek üzerinde çalışacak?" sorusunun cevabı, seçebileceğin algoritmaları baştan sınırlar. 10 bin örnekle çalışan bir prototip, 10 milyon örnekte kullanılamaz hâle gelir — ve bunu tasarım aşamasında görmek, üç hafta kod yazdıktan sonra görmekten çok ucuzdur.

::: ipucu
Kısıt verilmemişse tahmin et ve varsayımını yüksek sesle söyle: "n'in 10⁵ mertebesinde olduğunu varsayıyorum, bu yüzden O(n log n) hedefliyorum." Mülakatçı yanlış varsayımını düzeltir — bu da bilgi kazanmandır. Sessiz kalıp yanlış varsayımla ilerlemek ise en pahalı seçenektir.
:::

## 5.4 Adım 2: Örnekle — elle çalıştır

Problemi anladığını sandığın an, seni yalanlayacak en iyi araç küçük bir örnektir. Bu adımın kuralı basit: **bilgisayarı açmadan, kâğıt üstünde bir örneği baştan sona çöz.**

Neden? Çünkü bir problemi elle çözerken beynin farkında olmadan bir *algoritma* uygular. Sonra yapman gereken tek şey, o algoritmayı adımlara dökmektir. Örneğin "sıralı bir dizide iki sayının toplamı hedefe eşit mi?" sorusunu kâğıtta çözerken parmağını muhtemelen iki uçtan ortaya doğru yürütürsün — işte iki işaretçi tekniğini kendin keşfetmiş olursun.

Örneklerin üç tür olmalı:

**Tipik örnek.** Problemin ruhunu gösteren, ne çok küçük ne çok büyük bir vaka. `[2, 7, 11, 15]`, hedef `9` gibi.

**Kenar durumlar.** Programların çoğu burada kırılır. Standart kontrol listesi:

- Boş girdi (`[]`, `""`, sıfır eleman)
- Tek elemanlı girdi
- Tüm elemanlar aynı
- Zaten sıralı / ters sıralı
- Negatif sayılar, sıfır
- En küçük ve en büyük olası değerler (taşma! Bölüm 1'i hatırla)
- Cevabın var olmadığı durum
- Cevabın birden fazla olduğu durum

**Karşı örnek.** Bu en değerlisidir: aklına gelen basit bir fikri *çürüten* örnek. "En büyük iki sayıyı alsam?" diye düşündüysen, `[3, 3]` hedef `6` örneği bunu doğrular ama `[1, 5, 5]` hedef `6` çürütür. Fikrini erkenden çürütmek, saatlerce yanlış yolda yürümekten iyidir.

::: dikkat
"Elle çözdüm, anladım" ile "elle çözdüğüm adımları yazdım" arasında büyük fark var. İkincisini yap. Zihninde akıp giden sezgi, yazıya dökülünce eksikleri ortaya çıkar — "burada nasıl karar verdim?" diye takıldığın yer, kodunda da hata çıkacak yerdir.
:::

## 5.5 Adım 3: Kaba çöz — utanma, yaz

Şimdi en çok direnç göreceğin adım. Kaba kuvvet (brute force) çözüm, aklına gelen en dolaysız, en aptal, tüm ihtimalleri deneyen yaklaşımdır. Ve **yazılması gerekir.**

Neden bu kadar önemli? Dört sebep:

**1. Doğruluk zemini verir.** Kaba kuvvet çözümü neredeyse her zaman açıkça doğrudur. Sonra yazacağın hızlı çözümü onunla karşılaştırabilirsin — rastgele girdilerde ikisinin aynı sonucu verdiğini test etmek, hata avlamanın en güçlü yöntemlerinden biridir.

**2. Problemin yapısını gösterir.** Kaba çözümü yazarken "burada aynı hesabı tekrar yapıyorum" ya da "bu döngü gereksiz yere baştan tarıyor" dersin. İşte optimizasyon fikri tam olarak oradan doğar.

**3. Tavan belirler.** O(n²) bir çözümün varsa, en kötü ihtimalle o kadar. Bu psikolojik olarak da rahatlatır: elinde bir şey vardır.

**4. Mülakatta puan getirir.** "Aklıma önce şu O(n²) çözüm geliyor, önce onu yazayım sonra iyileştirelim" cümlesi, olumlu bir sinyaldir. Hiçbir şey yazmadan on dakika düşünmek ise değildir.

İki Toplam probleminin kaba kuvvet çözümü, tam olarak "her çifti dene"dir:

```python
def iki_toplam_kaba(sayilar, hedef):
    n = len(sayilar)
    for i in range(n):                 # her i için...
        for j in range(i + 1, n):      # ...sonraki her j'yi dene
            if sayilar[i] + sayilar[j] == hedef:
                return (i, j)
    return None
```

Bu kod on saniyede yazılır ve doğrudur. Kaç çift denedik? `n(n-1)/2` — yani O(n²). `n = 1000` için yarım milyon işlem: kabul edilebilir. `n = 100000` için beş milyar: kabul edilemez. Şimdi elimizde hem çalışan bir çözüm hem de somut bir problem var: **beş milyarı nasıl düşürürüm?**

## 5.6 Adım 4: Örüntü bul — bu neye benziyor?

Bu, ustalığın yattığı adım. Deneyimli bir mühendisin problemleri hızlı çözmesinin sebebi daha hızlı düşünmesi değil, **daha az düşünmesidir** — problemi tanır ve hazır kalıbı uygular. Senin hedefin de bu dağarcığı inşa etmek.

İşte en sık karşılaşacağın örüntüler ve onları ele veren ipuçları. Bu tabloyu duvarına asabilirsin; Kısım III ve IV boyunca her birini tek tek derinleştireceğiz:

| Problemde şunu görürsen | Şu deseni düşün | Nerede işlenecek |
|---|---|---|
| "gördüm mü?", sayma, eşleştirme | Hash tablosu (sözlük/küme) | Bölüm 9 |
| Sıralı dizi + çift arama | İki işaretçi | Bölüm 7 |
| Sıralı dizi + tek eleman arama | İkili arama | Bölüm 14 |
| "ardışık alt dizi/dizgi" + en uzun/kısa | Kayan pencere | Bölüm 8 |
| Aralık toplamı, sık sorgulama | Ön toplam (prefix sum) | Bölüm 7 |
| "sonraki büyük eleman" | Monotonik yığın | Bölüm 8 |
| "en büyük/küçük k eleman" | Yığın (heap) | Bölüm 10 |
| "en kısa yol", "en az adım" | BFS | Bölüm 17 |
| "tüm yolları/kombinasyonları bul" | Geri izleme (backtracking) | Bölüm 15 |
| Alt problemler tekrar ediyor | Dinamik programlama | Bölüm 16 |
| Her adımda "en iyi"yi seçmek yeterli | Açgözlü (greedy) | Bölüm 18 |
| Problemi ikiye bölebiliyorum | Böl ve yönet | Bölüm 19 |
| Nesneler arası ilişki/bağlantı | Çizge modelleme | Bölüm 11 |
| Sıralama işi kolaylaştırıyor | Ön işlem olarak sırala | Bölüm 13 |

Şu an bu isimlerin çoğu sana yabancı; olması gereken de bu. Amaç ezberlemek değil, **böyle bir haritanın var olduğunu bilmek**. İlerleyen bölümlerde her satır dolduğunda bu tabloya geri döneceksin.

Şimdi en sık kullanılan üçünü, bugünden kullanabileceğin kadar açalım.

### Örüntü A: Hash ile "gördüm mü?"

Kaba kuvvette neyi tekrar tekrar yapıyorduk? Her `i` için, `hedef - sayilar[i]` değerini dizide **aramak**. Aramayı O(n)'den O(1)'e indirebilirsek toplam maliyet O(n)'e düşer. Bunu yapan yapı: hash tablosu.

![Şekil 5.3: Aynı problem, iki yaklaşım. Solda her çifti deneyen O(n²) kaba kuvvet. Sağda "ihtiyacım olan eşi daha önce gördüm mü?" diye soran tek geçişli O(n) çözüm — geçtiği her elemanı sözlüğe not eder, böylece arama sabit zamana iner.](gorseller/b05_twosum.png)

Fikir şu: diziyi bir kez gez, gördüğün her sayıyı sözlüğe yaz. Her yeni sayıda "eşim (hedef − ben) daha önce geçti mi?" diye sor. Geçtiyse cevap bulundu.

```python
def iki_toplam_hizli(sayilar, hedef):
    gorulen = {}                          # değer -> indeks
    for i, x in enumerate(sayilar):
        es = hedef - x                    # bana lazım olan eş
        if es in gorulen:              # daha önce gördüm mü? O(1)
            return (gorulen[es], i)
        gorulen[x] = i                    # görülenlere ekle
    return None
```

O(n²) → O(n). Bedeli ne? O(n) ek bellek. Bu bir **takastır** ve optimizasyonun büyük kısmı böyle takaslardan oluşur: bellek vererek zaman almak. Bu deseni tanı, çünkü sürekli karşına çıkacak.

### Örüntü B: İki işaretçi

Girdi *sıralıysa* elinde bedava bir bilgi var demektir ve onu kullanmamak israftır. Sıralı dizide iki sayının toplamını ararken uçlardan başlarsın:

![Şekil 5.4: İki işaretçi. Sıralı dizide sol baştan, sağ sondan başlar. Toplam hedeften büyükse sağ işaretçi sola çekilir (toplam küçülür), küçükse sol sağa itilir. Her adımda bir olasılık kesin olarak elenir — bu yüzden tek geçişte, O(n) sürede biter.](gorseller/b05_pointers.png)

```python
def iki_toplam_sirali(sirali, hedef):
    sol, sag = 0, len(sirali) - 1
    while sol < sag:
        toplam = sirali[sol] + sirali[sag]
        if toplam == hedef:
            return (sol, sag)
        elif toplam > hedef:
            sag -= 1              # küçültmem lazım: sağdan kıs
        else:
            sol += 1              # büyütmem lazım: soldan aç
    return None
```

Bu çözüm O(n) zaman ve **O(1) bellek** kullanır — hash çözümünden bile iyidir. Ama bir şartı vardır: dizi sıralı olmalı. Sıralı değilse önce sıralamak O(n log n) maliyetlidir ve indeksler karışır. İşte bu yüzden "hangi çözüm daha iyi?" sorusunun cevabı hep aynıdır: **duruma bağlı** — ve o durumu belirleyen şey, Adım 1'de topladığın kısıtlardır.

### Örüntü C: Kayan pencere

"Ardışık" kelimesini gördüğün an alarma geç. Bir dizide/dizgide *ardışık* bir parçanın en uzununu, en kısasını ya da toplamı belli bir şeyi sağlayanını arıyorsan, kayan pencere neredeyse her zaman doğru cevaptır.

![Şekil 5.5: Kayan pencere. Sağ kenar diziyi tarayarak pencereyi büyütür; kural bozulunca sol kenar ilerleyerek pencereyi daraltır. İki kenar da hiç geri gitmediği için toplam iş, dizinin uzunluğu mertebesinde kalır: O(n).](gorseller/b05_window.png)

Kritik sezgi şu: iki kenar da **yalnızca sağa** gider. Her eleman pencereye en fazla bir kez girer, en fazla bir kez çıkar. Bu yüzden içeride `while` görsen bile toplam maliyet O(n²) değil, O(n)'dir. Bu "amortize" akıl yürütmeyi Bölüm 12'de resmîleştireceğiz; şimdilik deseni tanı.

Örnek 2'de bu deseni baştan sona uygulayacağız.

## 5.7 Adım 5: İyileştir — darboğazı bul

Optimizasyon rastgele kurcalamak değildir. Sistematik bir sorgudur ve üç sorudan oluşur:

**Soru 1: Gereksiz iş yapıyor muyum?** Kaba kuvvette tüm çiftleri deniyorduk ama cevabı bulunca durmak dışında bir eleme yapmıyorduk. Sıralı bir dizide "toplam zaten çok büyük" bilgisiyle koca bir bölgeyi eleyebiliyorsak, o işi hiç yapmamalıyız. İki işaretçinin yaptığı budur.

**Soru 2: Aynı şeyi tekrar mı hesaplıyorum?** Bu, dinamik programlamanın (Bölüm 16) tohumudur. Fibonacci'yi özyinelemeyle hesaplarken aynı `fib(5)` onlarca kez hesaplanır. Bir kez hesaplayıp saklamak (memoization), üstel maliyeti doğrusala indirir. Genel ilke: **hesabı sakla, tekrar etme.**

**Soru 3: Veriyi daha iyi düzenleyebilir miyim?** Aramayı hızlandırmak için sözlük, sürekli en küçüğü almak için yığın, sıralı erişim için sıralama... Doğru veri yapısı, algoritmayı sadeleştirir. Bu yüzden bir sonraki başlık bu kadar önemli.

Bu üç sorunun cevabı genelde bir **takas** önerir. Takasların bilinmesi gereken temel eksenleri şunlar:

| Takas | Ne verirsin | Ne alırsın | Tipik örnek |
|---|---|---|---|
| Bellek ↔ Zaman | Ek bellek | Hız | Hash tablosu, memoization |
| Ön işlem ↔ Sorgu | Bir kerelik hazırlık | Hızlı tekrar sorgu | Sıralama, ön toplam, indeks |
| Kesinlik ↔ Hız | Kesin sonuç | Yaklaşık ama hızlı | Bloom filtresi, örnekleme |
| Basitlik ↔ Performans | Okunabilirlik | Hız | Elle optimize edilmiş kod |

Son satır özellikle önemli ve genç mühendislerin en sık kaçırdığı yerdir: **her optimizasyon değerli değildir.** Kodun bir kez çalışacaksa ve girdi küçükse, O(n²) çözüm gayet iyidir. "Erken optimizasyon tüm kötülüklerin anasıdır" sözü tam olarak bunu anlatır. Önce doğru ve okunabilir yaz; ölç; gerçekten yavaşsa optimize et. Ölçmeden yapılan optimizasyon, tahmine dayalı bir kumardır — ve programcılar darboğazın nerede olduğunu tahmin etmekte ünlü şekilde kötüdür (bunu Bölüm 6'da ve Kendin Yap 2'de bizzat göreceksin).

### Alt probleme indirgeme

"Parçala" demenin en somut hâli, büyük problemi daha küçük bir kopyasına bağlamaktır. Kendine üç soru sor: (1) Problemin n-1 elemanlık sürümünü çözebiliyor muyum? (2) Bu çözümü n elemanlığa genişletmek için ne eklemem gerekir? (3) Problemi iki yarıya bölüp sonuçları birleştirebilir miyim?

Somut bir örnek: bir dizinin *tüm alt kümelerini* üretmek istiyoruz. `[1, 2]` için bunlar `[]`, `[1]`, `[2]`, `[1, 2]`. `[1]`'in alt kümeleri bilindiğinde `[1, 2]`'yi kurmak için ne gerekir? Her eski alt küme iki yeni alt küme doğurur: kendisi ve kendisine yeni elemanın eklenmiş hâli. Kodu:

```python
def altkumeler(a):
    sonuc = [[]]                         # boş dizinin tek altkümesi
    for x in a:                          # her yeni eleman için...
        sonuc += [k + [x] for k in sonuc]  # ...her eskiye ekle
    return sonuc
```

Burada yaptığımız şey "n-1'den n'e genişletme"dir. Problem yine de zor görünüyorsa daha basit bir ara hedefe in: "tüm alt kümeler" yerine önce "tek elemanlı alt kümeler"i ya da "boş olmayan alt küme sayısını" çöz. Bu kalıp, Bölüm 15'teki geri izleme (backtracking) ve Bölüm 16'daki dinamik programlamanın da temelidir.

## 5.8 Adım 6: Doğrula — kendi kodunun düşmanı ol

Kod yazıldı, çalışıyor gibi görünüyor. Bitmedi. Bu adımda üç iş yaparsın.

**Elle iz sürme (dry run).** Yazdığın kodu, kâğıt üstünde küçük bir girdiyle satır satır çalıştır. Değişkenlerin değerlerini bir tablo hâlinde yaz. Bu, hata ayıklayıcıdan bile hızlı bir hata bulma yöntemidir ve mülakatta zorunludur: kodunu yazdıktan sonra "şimdi bunu `[2,7,11,15]` ile deneyelim" deyip elle çalıştırmak, güçlü bir profesyonellik sinyalidir.

**Kenar durum turu.** Adım 2'de listelediğin kenar durumları tek tek koddan geçir. Özellikle şu üçlü, hataların çoğunu yakalar: boş girdi, tek elemanlı girdi, cevabın olmadığı durum. Bir de klasik **birim hatası (off-by-one)** kontrolü: döngü `<` mi `<=` mi olmalı, `n-1`'e kadar mı `n`'e kadar mı? Bu hata o kadar yaygındır ki, bilgisayar bilimlerinin ünlü şakalarından biridir: *"Bilgisayar bilimlerinde iki zor problem vardır: önbellek geçersizleştirme, isimlendirme ve birim hataları."* Bu bilinçli bir espridir: şakanın kendisi bir birim hatasıdır, çünkü "iki" diyor ama listede üç madde var.

**Karmaşıklık hesabı.** Kaç işlem yapıyorsun, ne kadar bellek kullanıyorsun? Bu, Adım 1'deki kısıtla uyuşuyor mu? Uyuşmuyorsa döngüye geri dön. Bu hesabın nasıl yapıldığını Bölüm 12'de tam kurallarıyla göreceğiz; şimdilik "kaç kez döngüye giriyorum?" sorusu yeterli.

::: baglanti
Doğrulamanın sistemli hâli **testtir** ve testin kendisi bir mühendislik disiplinidir: birim testleri, kenar durum tasarımı, TDD döngüsü **Bölüm 39**'un konusu. Kod çalışmıyorsa devreye giren sistematik hata ayıklama süreci ise hemen sıradaki bölümde, **Bölüm 6**'da.
:::

## 5.9 Veri yapısı karar ağacı

Adım 5'in üçüncü sorusu — "veriyi daha iyi düzenleyebilir miyim?" — genelde bir veri yapısı seçimine dayanır. Ve doğru veri yapısı seçildiğinde problem çoğu zaman kendiliğinden çözülür. Ünlü söz boşuna değildir: *"Kötü programcılar kodu düşünür, iyi programcılar veri yapılarını ve ilişkilerini düşünür."* (Linus Torvalds)

Seçim, ihtiyacını doğru sorulara dökmekle yapılır:

![Şekil 5.6: Veri yapısı seçim ağacı. Soru, "hangi yapı daha iyi?" değil, "verime nasıl erişeceğim?"dir. Erişim biçimin, yapıyı belirler. Birden fazla ihtiyacın varsa yapıları birleştirirsin.](gorseller/b05_dstree.png)

Kararı sağlamlaştırmak için maliyetleri de bilmen gerekir. Bu tablo, Kısım III boyunca tek tek kanıtlayacağımız sonuçların özetidir — şimdilik referans olarak kullan:

| Yapı | Erişim | Arama | Ekleme | Silme | Not |
|---|---|---|---|---|---|
| Dizi (array) | O(1) | O(n) | O(n) | O(n) | Bitişik bellek, cache dostu |
| Dinamik dizi (list) | O(1) | O(n) | O(1)* sona | O(n) | *amortize |
| Bağlı liste | O(n) | O(n) | O(1) | O(1) | Düğüm elindeyse |
| Yığın / Kuyruk | — | — | O(1) | O(1) | Yalnız uçlar |
| Hash tablosu | — | O(1)* | O(1)* | O(1)* | *ortalama; sıra yok |
| Dengeli arama ağacı (AVL vb.) | — | O(log n) | O(log n) | O(log n) | Sıralı kalır |
| Yığın (heap) | O(1) tepe | O(n) | O(log n) | O(log n) | Yalnız uç eleman hızlı |
| Trie | — | O(k) | O(k) | O(k) | k = kelime uzunluğu |

Tablodaki en kritik satır hash tablosudur, çünkü en çok yanlış anlaşılandır: O(1) *ortalama* maliyettir ve **sıra bilgisi yoktur**. "En küçük elemanı bul" gibi bir ihtiyacın varsa hash yanlış seçimdir; onun için yığın ya da sıralı ağaç gerekir.

Son olarak, karar ağacının altındaki not: gerçek problemler genelde **birden fazla yapının birleşimini** ister. "Kelimeleri say ve en sık 3 tanesini ver" problemi, sayma için sözlük *ve* en sıkları seçmek için yığın ister. Örnek 4'te bu birleştirmeyi yapacağız.

## 5.10 Beyaz tahta protokolü

Bu bölümün bilgisini mülakatta puana çevirmenin bir usulü var. Değerlendiren kişi senin kodunu değil, **düşünme sürecini** izliyor; o yüzden süreci görünür kıl.

**1. Problemi geri anlat.** "Anladığım kadarıyla bana bir tam sayı dizisi ve bir hedef veriliyor; toplamı hedefe eşit iki elemanın indekslerini istiyorsun. Doğru mu?" Bu tek cümle, yanlış problemi çözme riskini sıfırlar.

**2. Soru sor.** 5.3'teki listeden en az üçünü sor: boş olabilir mi, tekrar var mı, n ne kadar büyük?

**3. Örnek üret ve elle çöz.** Tahtaya küçük bir örnek yaz, elle çöz. Mülakatçı bu sırada senin problemi gerçekten kavradığını görür.

**4. Kaba çözümü söyle ve karmaşıklığını ver.** "Her çifti deneyebilirim, bu O(n²). Önce bunu yazayım mı, yoksa doğrudan optimize mi edelim?" — bu soru, seni yönlendirmesini sağlar.

**5. İyileştirmeyi sesli düşün.** "Buradaki darboğaz arama. Aramayı hash ile O(1)'e indirirsem toplam O(n) olur, karşılığında O(n) bellek harcarım." Takası açıkça telaffuz et.

**6. Şimdi kod yaz.** Yaklaşım onaylandıktan sonra. Değişken isimlerine özen göster; okunabilir kod da değerlendirilir.

**7. Kendi kodunu test et.** Elle bir örnek çalıştır, kenar durumları söyle. "Boş dizi gelirse döngüye hiç girmez, `None` döner — doğru davranış."

Bu protokolün bir yan faydası daha var: tıkandığında sana yapacak bir şey verir. Fikrin yoksa Adım 1'e dön, kısıtları yüksek sesle oku. Çoğu zaman çözüm oradan çıkar — ve çıkmasa bile sessizce donmuş olmazsın.

### Tıkanma merdiveni ve zaman kutusu

Mülakat genelde kabaca 45 dakika sürer ve süreyi bilinçli bölüşmek, tıkanma riskini düşürür. Aşağıdaki dağılım bir başlangıç noktasıdır:

| Dakika | Ne yapılır |
|---|---|
| 5 | Anla: imza, kısıtlar, üç soru |
| 5 | Örnekle: tipik örnek ve iki kenar durum |
| 10 | Kaba çöz ve örüntü bul |
| 15 | İyileştirilmiş kodu yaz |
| 10 | Doğrula: elle iz, kenar durumlar, karmaşıklık |

Tıkanırsan panik yapma; sırayla şunları dene:

1. Kısıtı yeniden oku. Hangi n, hangi limit? Çözümün türü çoğu zaman oradan çıkar.
2. n = 3-5 ile elle dene. Küçük çıktıları yazıp bir örüntü ara.
3. Problemi alt probleme indir: girdiyi küçült, bir kısıtı geçici olarak kaldır ya da yalnızca bir parçayı çöz.
4. Kaba çözümü yaz. Çalışan yavaş bir çözüm, hiç çözümden iyidir.
5. Bir sonraki somut adımı yüksek sesle söyle: "Şimdi sözlük yapısını kurayım." Sessizlik mülakatçıya hiçbir şey anlatmaz.

::: mulakat
Sık yapılan bir hata: mülakatçı ipucu verdiğinde savunmaya geçmek. İpucu bir eleştiri değil, işbirliğidir; gerçek işte de takım arkadaşın sana fikir verecek. Doğru tepki: "Haklısın, sıralı olduğunu kullanmıyordum — o zaman iki işaretçiyle O(1) belleğe inebilirim." İpucunu alıp üstüne inşa etmek, en güçlü sinyallerden biridir.
:::

## Çözümlü Örnekler

### Örnek 1 (★): İki Toplam — altı adımın tamamı

**Problem:** Bir tam sayı dizisi ve bir hedef sayı veriliyor. Toplamları hedefe eşit olan iki elemanın indekslerini döndür. Tam olarak bir çözüm olduğu garanti ediliyor ve aynı elemanı iki kez kullanamazsın.

Bu örneği, altı adımı eksiksiz uygulayarak çözeceğiz. Amacım problemi çözmek değil, **süreci göstermek**.

**Adım 1 — Anla.** İmzayı yazıyorum: girdi `list[int]` ve `int`, çıktı `tuple[int, int]`. Sorularım: Dizi sıralı mı? (Hayır, belirtilmemiş — sıralı varsayamam.) Negatif olabilir mi? (Evet, "tam sayı" denmiş.) Tekrar var mı? (Olabilir.) n ne kadar? (Diyelim 10⁵ — o zaman O(n²) elenir, O(n) ya da O(n log n) hedeflemeliyim.) Çözüm garanti, yani "bulunamadı" durumunu düşünmeme gerek yok ama yine de sağlam kod için ele alacağım.

**Adım 2 — Örnekle.** Tipik: `[2, 7, 11, 15]`, hedef `9` → cevap `(0, 1)` çünkü 2+7=9. Kenar durumlar: `[3, 3]` hedef `6` → `(0, 1)`; aynı *değer* iki kez var ama farklı indeksler, bu geçerli. `[3]` hedef `6` → cevap yok (tek eleman, kendisiyle toplanamaz). Negatifli: `[-1, 4, 5]` hedef `3` → `(0, 1)`.

Elle nasıl çözerim? `2`'ye bakarım, "bana 7 lazım" derim, listede ararım. Sonra `7`'ye bakarım, "bana 2 lazım" derim... Dikkat: burada zaten bir algoritma uyguladım — her eleman için *eşini arıyorum*.

**Adım 3 — Kaba çöz.** 5.5'te yazdığımız çift döngü: O(n²). n=10⁵ için 5×10⁹ işlem, yani kabul edilemez. Ama elimizde doğru bir referans var.

**Adım 4 — Örüntü bul.** Adım 2'deki elle çözümüme dönüyorum: "eşini ara". Yaptığım iş bir **arama** ve pahalı olan da bu. "Bu değeri daha önce gördüm mü?" sorusu, örüntü tablosundaki ilk satır: **hash tablosu**.

**Adım 5 — İyileştir.** Diziyi tek geçişte gezerim; her elemanda önce "eşim daha önce geçti mi?" diye sorarım, sonra kendimi sözlüğe eklerim. İşlem sırasının önemi burada: önce sorup sonra eklemek, elemanın kendisiyle eşleşmesini kendiliğinden engeller.

```python
def iki_toplam(sayilar, hedef):
    gorulen = {}                        # değer -> indeks
    for i, x in enumerate(sayilar):
        es = hedef - x
        if es in gorulen:               # ÖNCE sor
            return (gorulen[es], i)
        gorulen[x] = i                  # SONRA ekle
    return None
```

**Adım 6 — Doğrula.** Elle iz sürelim, `[2, 7, 11, 15]`, hedef `9`:

| i | x | es = 9−x | es sözlükte? | sözlük (sonrası) |
|---|---|---|---|---|
| 0 | 2 | 7 | hayır | `{2: 0}` |
| 1 | 7 | 2 | **evet (0)** | → `(0, 1)` döner |

Kenar durumlar: `[3, 3]` hedef `6` → i=0'da `es=3` sözlükte yok, `{3: 0}`; i=1'de `es=3` var → `(0, 1)`. Doğru. `[3]` hedef `6` → döngü biter, `None`. Doğru. Karmaşıklık: tek döngü, her adımda O(1) sözlük işlemi → **O(n) zaman, O(n) bellek.** Kısıtla uyumlu.

**Bunu AI'sız, boş IDE'de yazabilir misin?** Asıl sınav kod değil, süreç: kâğıda altı adımı başlıklar hâlinde yazıp her birinin altını doldurabiliyor musun? Ve şu soruya cevabın hazır mı: *"önce sor, sonra ekle" sırasını değiştirsem ne bozulurdu?*

### Örnek 2 (★★): En uzun tekrarsız alt dizgi

**Problem:** Bir dizgi verildiğinde, içindeki tekrar eden karakter içermeyen en uzun *ardışık* parçanın uzunluğunu bul. `"abcabcbb"` → `3` (`"abc"`).

**Adım 1 — Anla.** Girdi `str`, çıktı `int`. Kritik kelime: **ardışık**. Yani `"abcabcbb"` içinde `"abcb"` bir aday değil (ardışık değil, atlayarak seçilmiş). Karakter kümesi ne? (Diyelim ASCII.) Boş dizgi gelebilir mi? (Evet → 0 dönmeli.)

**Adım 2 — Örnekle.** `"abcabcbb"` → 3. `"bbbbb"` → 1. `""` → 0. `"pwwkew"` → 3 (`"wke"`). Bu son örnek önemli: cevap dizginin başında değil ortasında; ayrıca `"pwke"` ardışık olmadığı için 4 *değil*.

**Adım 3 — Kaba çöz.** Tüm alt dizgileri üret, her birinin tekrarsız olup olmadığını kontrol et:

```python
def en_uzun_kaba(s):
    n, en_iyi = len(s), 0
    for i in range(n):
        for j in range(i, n):
            parca = s[i:j+1]
            if len(set(parca)) == len(parca):      # tekrarsız mı?
                en_iyi = max(en_iyi, len(parca))
    return en_iyi
```

Alt dizgi sayısı O(n²), her birinin kontrolü O(n) → **O(n³)**. Çalışır ama n=10⁵ için imkânsız.

**Adım 4 — Örüntü bul.** "Ardışık" + "en uzun" → **kayan pencere** (örüntü tablosu, dördüncü satır). Ayrıca "tekrar var mı?" sorusu → **küme**. İki desen birleşecek.

**Adım 5 — İyileştir.** Pencerenin içindeki karakterleri bir kümede tutarım. Sağ kenarı ilerletirim; gelen karakter kümede varsa, o tekrar ortadan kalkana kadar sol kenarı ilerletip çıkanları kümeden atarım. Her adımda pencere boyunu kaydederim.

```python
def en_uzun(s):
    pencere = set()          # penceredeki karakterler
    sol = 0
    en_iyi = 0
    for sag, ch in enumerate(s):
        while ch in pencere:              # tekrar varsa daralt
            pencere.remove(s[sol])
            sol += 1
        pencere.add(ch)                   # şimdi güvenle ekle
        en_iyi = max(en_iyi, sag - sol + 1)
    return en_iyi
```

**Adım 6 — Doğrula.** `"abcabcbb"` üzerinde iz sürelim:

| sağ | ch | while çalıştı mı | pencere | sol | uzunluk | en iyi |
|---|---|---|---|---|---|---|
| 0 | a | hayır | {a} | 0 | 1 | 1 |
| 1 | b | hayır | {a,b} | 0 | 2 | 2 |
| 2 | c | hayır | {a,b,c} | 0 | 3 | **3** |
| 3 | a | evet (a çıktı) | {b,c,a} | 1 | 3 | 3 |
| 4 | b | evet (b çıktı) | {c,a,b} | 2 | 3 | 3 |

Doğru ilerliyor. Kenar durum: `""` → döngüye hiç girmez, `0` döner. `"bbbbb"` → her adımda pencere daralır, cevap 1. 

Karmaşıklık: içeride `while` var, O(n²) gibi *görünüyor*. Ama `sol` hiçbir zaman geri gitmez ve en fazla n kez artabilir. Yani iki döngünün **toplam** iş yükü 2n adımdır → **O(n)**. Bellek: pencere en fazla alfabe boyu → O(min(n, alfabe)).

**Bunu AI'sız yazabilir misin?** Şu iki soruyu cevaplayabiliyorsan evet: (1) İç içe iki döngü varken karmaşıklık neden O(n²) değil? (2) `pencere.add(ch)` satırını `while`'dan *önceye* alsam ne olurdu?

### Örnek 3 (★★): Anagram gruplama — anahtar tasarlamak

**Problem:** Kelime listesi verildiğinde, birbirinin anagramı olanları grupla. `["eti", "iet", "kar", "rak", "tie"]` → `[["eti","iet","tie"], ["kar","rak"]]`.

**Adım 1 — Anla.** Girdi `list[str]`, çıktı `list[list[str]]`. Anagram: aynı harflerden farklı sırayla oluşan kelimeler. Büyük/küçük harf duyarlı mı? (Diyelim hayır, hepsi küçük.) Grupların sırası önemli mi? (Hayır.)

**Adım 2 — Örnekle.** Elle nasıl gruplarım? `"eti"` ve `"iet"`in aynı gruba girdiğini nasıl anlarım? Harflerini sıralarsam ikisi de `"eit"` olur. İşte bu — elle yaptığım şey bir **normalleştirme**.

**Adım 3 — Kaba çöz.** Her kelime çiftini karşılaştır, anagramsa aynı gruba koy: O(n² · k). Çalışır ama hantal.

**Adım 4 — Örüntü bul.** Adım 2'deki keşif kritik: her kelimeyi *aynı gruptakilerle aynı olan* bir anahtara çevirebiliyorum. "Aynı anahtara sahip olanları topla" → **hash tablosu ile gruplama**. Bu örüntünün adı: *anahtar tasarımı*. Problemin zorluğu algoritmada değil, **doğru anahtarı bulmakta**.

**Adım 5 — İyileştir.** Anahtar: kelimenin harflerinin sıralı hâli. Sözlükte anahtar → kelime listesi tut.

```python
from collections import defaultdict

def anagram_grupla(kelimeler):
    gruplar = defaultdict(list)          # anahtar -> kelimeler
    for kelime in kelimeler:
        anahtar = "".join(sorted(kelime))    # "eti" ve "iet" -> "eit"
        gruplar[anahtar].append(kelime)
    return list(gruplar.values())
```

`defaultdict(list)`, "bu anahtar yoksa boş listeyle başlat" demenin kısa yoludur; `if anahtar not in gruplar: gruplar[anahtar] = []` satırını gereksiz kılar.

**Adım 6 — Doğrula.** `["eti","iet","kar","rak","tie"]`: anahtarlar sırasıyla `eit, eit, akr, akr, eit`.

Elle iz (her adımdan sonra sözlüğün durumu):

| kelime | anahtar | gruplar (sonrası) |
|---|---|---|
| eti | eit | eit: [eti] |
| iet | eit | eit: [eti, iet] |
| kar | akr | eit: [eti, iet], akr: [kar] |
| rak | akr | eit: [eti, iet], akr: [kar, rak] |
| tie | eit | eit: [eti, iet, tie], akr: [kar, rak] |

Sonuçta sözlük: `{"eit": ["eti","iet","tie"], "akr": ["kar","rak"]}`. Doğru. Karmaşıklık: n kelime, her biri k uzunluğunda; sıralama O(k log k) → **O(n · k log k)**. Kaba kuvvetin O(n²·k)'sinden çok daha iyi.

**Alternatif anahtar:** Harf sayımı da kullanılabilir — `"eti"` için `(1,0,...,1,...,1)` gibi 29 elemanlı bir sayaç demeti. Bu O(k) sürede üretilir, sıralamaya göre biraz daha hızlıdır ama daha çok kod ister. İki tasarımı karşılaştırıp gerekçeli seçim yapabilmek, mühendisliğin ta kendisidir.

**Bunu AI'sız yazabilir misin?** Türkçe için bir tuzak var: `"İ"`, `"ı"` gibi harfler ve Unicode normalizasyonu. `sorted("İSTANBUL".lower())` beklediğin sonucu verir mi? Bölüm 1'deki UTF-8 tartışmasını hatırla ve dene.

### Örnek 4 (★★★): En sık k eleman — üç çözüm, bir karar

**Problem:** Bir sayı dizisinde en sık geçen `k` elemanı bul. `[1,1,1,2,2,3]`, `k=2` → `[1,2]`.

Bu örnek, tek bir "doğru cevabı" olmayan gerçekçi bir durumdur: üç meşru çözüm var ve seçim kısıtlara bağlı. Mühendisliğin özü de budur.

**Adım 1 — Anla.** Girdi `list[int]`, `int`. Çıktı: k eleman. Beraberlik olursa? (Herhangi biri kabul.) n ve k'nin ilişkisi? (k ≤ farklı eleman sayısı.) Kritik soru: **k, n'e göre küçük mü?** Çünkü cevap buna göre değişecek.

**Adım 2 — Örnekle.** `[1,1,1,2,2,3]`, k=2: frekanslar `{1:3, 2:2, 3:1}` → en sık ikisi `[1,2]`. Elle nasıl yaptım? Önce **saydım**, sonra **en büyükleri seçtim**. İki ayrı alt problem!

**Adım 3 — Kaba çöz.** Her elemanın frekansını tüm diziyi tarayarak bul, sonra k kez maksimumu ara: O(n²). Elenir.

**Adım 4 — Örüntü bul.** İki alt problem, iki örüntü: sayma → **hash tablosu**; "en büyük k" → örüntü tablosunda **yığın (heap)**. Karar ağacının altındaki not iş başında: yapıları birleştireceğiz.

**Adım 5 — İyileştir.** Sayma kısmı tartışmasız O(n) sözlükle yapılır. Asıl karar, "en sık k'yı seçme" kısmında. Üç yol var:

```python
from collections import Counter
import heapq

def en_sik_k_sirala(sayilar, k):
    """(A) Sırala: basit, her durumda O(m log m)."""
    sayac = Counter(sayilar)                       # O(n)
    sirali = sorted(sayac.items(), key=lambda c: c[1], reverse=True)
    return [deger for deger, _ in sirali[:k]]

def en_sik_k_heap(sayilar, k):
    """(B) Yığın: k küçükken en iyisi, O(m log k)."""
    sayac = Counter(sayilar)                       # O(n)
    en_sik = heapq.nlargest(k, sayac.items(), key=lambda c: c[1])
    return [d for d, _ in en_sik]

def en_sik_k_kova(sayilar, k):
    """(C) Kova sayımı: frekans <= n olduğu için O(n)."""
    sayac = Counter(sayilar)
    n = len(sayilar)
    kovalar = [[] for _ in range(n + 1)]   # kova[f]: frekans f
    for deger, frekans in sayac.items():
        kovalar[frekans].append(deger)
    sonuc = []
    for f in range(n, 0, -1):              # yüksek frekanstan aşağı
        for deger in kovalar[f]:
            sonuc.append(deger)
            if len(sonuc) == k:
                return sonuc
    return sonuc
```

**Adım 6 — Doğrula ve karar ver.** `m` farklı eleman sayısı olsun. Önce (C) yolunu elle izleyelim: `[1,1,1,2,2,3]` için sayaç `{1:3, 2:2, 3:1}`, dolayısıyla `kova[3]=[1]`, `kova[2]=[2]`, `kova[1]=[3]`; burada `n=6`, `k=2`.

| f | kova[f] | sonuç (sonrası) | len = k? |
|---|---|---|---|
| 6 | [] | [] | hayır |
| 5 | [] | [] | hayır |
| 4 | [] | [] | hayır |
| 3 | [1] | [1] | hayır |
| 2 | [2] | [1, 2] | **evet, döndür** |

Üç çözümün karşılaştırması:

| Çözüm | Zaman | Bellek | Ne zaman tercih edilir |
|---|---|---|---|
| (A) Sırala | O(n + m log m) | O(m) | m küçük; kod sadeliği önemli |
| (B) Yığın | O(n + m log k) | O(m + k) | **k ≪ m** olduğunda (klasik "top-10") |
| (C) Kova | O(n) | O(n + m) | En hızlısı; frekanslar sınırlı olduğu için işe yarar |

Üçü de doğru. Seçim, Adım 1'de sorduğun soruya bağlı: k küçükse (B), teorik en iyiyi istiyorsan (C), kod basitliği yeterliyse (A). Mülakatta üçünü de söyleyip gerekçeli seçim yapmak, tek bir çözümü mükemmel yazmaktan daha değerlidir.

(C)'nin neden O(n) olduğu ilk bakışta şaşırtıcıdır: "sıralama en az O(m log m) değil miydi?" Sırrı şu: sıralamıyoruz. Frekansların 1 ile n arasında *tam sayı* olması, onları doğrudan indeks olarak kullanmamıza izin veriyor. Karşılaştırma yapmadan sıralama fikri budur ve Bölüm 13'te sayma/kova sıralamasını işlerken geri döneceğiz.

**Bunu AI'sız yazabilir misin?** `ÖZCE`'de bir metin gövdesindeki en sık 100 token'ı bulman gerekiyor; n = 10 milyon, m = 50 bin, k = 100. Hangi çözümü seçerdin ve neden? Sayıları tabloya koyup hesapla — sezgiyle değil, hesapla karar ver.

## Kendin Yap Projeleri

::: dikkat
Bu iki proje bu bölümün *asıl içeriğidir*. Buradaki teori, uygulanmadığı sürece bilgi olarak kalır ve beceriye dönüşmez. Yapay zekâ kullanımı yasak — özellikle burada, çünkü amacın tam olarak AI'ın senin yerine yaptığı şeyi kendin yapabilmek.
:::

### Proje 1 (★★): Çözüm defteri

**Amaç:** Altı adımlı süreci reflekse dönüştürmek için bir çalışma sistemi kur ve iki hafta uygula.

**Yapılacak:** Bir defter (fiziksel ya da markdown dosyası) aç. Her problem için tek sayfalık şu şablonu doldur:

```term
PROBLEM: <bir cümleyle>
1. ANLA     girdi: ...  çıktı: ...  kısıtlar: ...  sorularım: ...
2. ÖRNEKLE  tipik: ...  kenar: ...  karşı örnek: ...
3. KABA ÇÖZ fikir: ...  karmaşıklık: ...
4. ÖRÜNTÜ   bu şuna benziyor: ...  çünkü: ...
5. İYİLEŞTİR darboğaz: ...  takas: ...  yeni karmaşıklık: ...
6. DOĞRULA  elle iz: ...  kenar testleri: ...
SONRADAN:   ne öğrendim / neyi kaçırdım: ...
```

Sonra 10 problem çöz — kolaydan başla, giderek zorlaş. Başlangıç için önerilen problem türleri: bir dizide en büyük iki eleman; bir dizginin palindrom olup olmadığı; iki dizinin kesişimi; bir dizideki eksik sayıyı bulma (1..n aralığında); parantez dengesi kontrolü; bir dizide çoğunluk elemanı; sıralı dizide belirli bir değeri arama; bir metindeki kelime frekansları; iki sıralı diziyi birleştirme; bir dizinin tüm alt kümelerini üretme.

**Kritik kural:** Şablonun ilk beş adımını doldurmadan kod yazmak yasak. Tıkanırsan 20 dakika dene, sonra çözüme bak — ama baktıktan sonra **defteri kapat, ertesi gün sıfırdan kendin yaz**. Bakarak yazmak öğrenme değil, kopyalamadır.

**Önerilen yaklaşım:** İlk üç problemde şablonu sesli doldur: her satırı yüksek sesle söyle, sonra yaz. Problemler ilerledikçe "ÖRÜNTÜ" satırına bakmadan önce "kısıt ne?" sorusunu sor. Bir problemin "SONRADAN" satırını kapatmadan bir sonrakine geçme. Haftada bir, dolu sayfaları baştan oku ve tekrar eden zayıflığın üzerine bir çalışma planı yaz. Bu bir ipucudur, çözüm değildir; kararları sen vereceksin.

**Başarı kriterleri:** 10 problemin şablonu dolu; en az 3 problemde kaba çözümden optimuma geçmişsin; "SONRADAN" bölümlerinde tekrar eden bir zayıflığını tespit edip adını koymuşsun (örneğin "kenar durumları hep atlıyorum").

### Proje 2 (★★★): Optimizasyonu ölçerek kanıtla

**Amaç:** "Şu çözüm daha hızlı" cümlesini tahminden çıkarıp ölçüme dayandırmak — ve Adım 5'in "önce ölç" ilkesini bizzat yaşamak.

**Problem:** Bir log dosyasında her satır bir zaman damgası içeriyor (saniye cinsinden tam sayı, sıralı). "Herhangi bir 60 saniyelik pencerede en fazla kaç olay gerçekleşmiş?" sorusunu üç farklı yöntemle çöz:

- **(A) Kaba kuvvet:** Her olay için, ondan sonraki 60 saniyeye kaç olay düştüğünü say. O(n²).
- **(B) İkili arama:** Her olay için, pencere sonunu sıralı dizide ikili aramayla bul. O(n log n).
- **(C) Kayan pencere:** İki işaretçiyle tek geçiş. O(n).

**Yapılacak:** Üçünü de yaz; aynı sonucu verdiklerini rastgele girdilerle doğrula (kaba kuvvet senin referansın). Sonra n = 1 000, 10 000, 100 000, 1 000 000 için sürelerini ölç (`time.perf_counter`; Bölüm 3'teki `@zamanla` dekoratörünü buraya taşıyabilirsin). Ölçümleri bir tabloya dök.

**Önerilen yaklaşım:** Test verisini rastgele üret ama sıralamayı unutma. Kaba kuvveti büyük n'lerde çalıştırma — süresini küçük n'lerden tahmin et (n on kat artınca süre kaç kat arttı?). Bu tahmin alıştırması, karmaşıklık sezgisini oturtur.

**Başarı kriterleri:** Üç çözüm de aynı cevabı veriyor; ölçüm tablosu var; n on kat büyüdüğünde her çözümün süresinin kaç kat arttığını *önceden tahmin edip* ölçümle karşılaştırmışsın; hangi n'den itibaren (C)'nin farkının anlamlı hâle geldiğini söyleyebiliyorsun. Bonus: n = 1000'de hangisi daha hızlı ve neden? (Cevap seni şaşırtabilir — sabit çarpanlar küçük n'de büyük O'dan önemlidir.)

### Ek Alıştırmalar

Aşağıdaki on iki problem cevapsız. Her birini altı adımla, kâğıt üstünde çöz; kodu yazmadan önce ilk beş adımı tamamla. Koyu etiket, problemin klasik ailesini gösterir.

1. ★ **Hash.** Bir dizgide tekrar etmeyen ilk karakterin indeksini döndür; yoksa `-1`.
2. ★ **İki işaretçi.** Sıralı bir dizide farkı tam `k` olan iki elemanın indekslerini bul.
3. ★ **Kayan pencere.** Uzunluğu `k` olan her pencerenin toplamını hesapla; en büyük toplamı döndür.
4. ★ **Hash.** Bir cümlede ilk tekrar eden kelimeyi bul.
5. ★★ **Ön toplam.** Bir dizi ve çok sayıda `[l, r]` sorgusu veriliyor; her sorguya aralık toplamını hızlı yanıtla.
6. ★★ **Hash ve ön toplam.** Toplamı `k` olan ardışık alt dizilerin sayısını bul. Elemanlar negatif olabilir.
7. ★★ **Kayan pencere.** En fazla `k` farklı karakter içeren en uzun ardışık alt dizgiyi bul.
8. ★★ **İki işaretçi.** Sıralı bir dizide tekrar eden elemanları ek bellek kullanmadan sil; kalan eleman sayısını döndür.
9. ★★ **Hash.** İki dizinin kesişimini bul; her değer, iki dizide geçtiği kadar sayılsın.
10. ★★★ **Kayan pencere.** Uzunluğu `k` olan her pencerenin maksimumunu bul; her pencere için baştan tarama yapmadan çöz.
11. ★★★ **Ön toplam ve iki işaretçi.** Yalnız pozitif tam sayılardan oluşan bir dizide, toplamı en az `S` olan en kısa ardışık alt dizinin uzunluğunu bul; yoksa `0`.
12. ★★★ **Hash ve iki işaretçi.** Bir dizide toplamı sıfır olan, birbirinden farklı üçlüleri bul.

## Kod Okuma Egzersizi

Bu bölümün kesiti, Python'un standart kütüphanesindeki `bisect` modülünden — sıralı bir listede bir değerin gireceği yeri bulan `bisect_left`. Kısacık bir fonksiyon, ama içinde bu bölümün her fikri var: kısıt (sıralılık) kullanımı, değişmez (invariant) tasarımı ve ünlü bir tarihî hata.

Aşağıdaki kod, CPython 3.12'nin `Lib/bisect.py` dosyasındaki `bisect_left` fonksiyonunun sadeleştirilmiş hâlidir (`key` parametresi ve ayrıntılı belgeler çıkarıldı, döngü mantığı aynıdır).

```python
def bisect_left(a, x, lo=0, hi=None):
    """a sıralı; x'in ekleneceği EN SOL konumu döndürür."""
    if lo < 0:
        raise ValueError('lo must be non-negative')
    if hi is None:
        hi = len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid
    return lo
```

Aynı işin C dünyasındaki klasik yazımı ise şöyleydi ve yıllarca kullanıldı:

```c
/* Java'da ~9 yıl fark edilmeyen hata
   (Bloch, 2006): taşabilir (bkz. aşağıda). */
int mid = (lo + hi) / 2;
```

**Sorular — cevaplamadan geçme:**

- Fonksiyonun **değişmezi (invariant)** nedir? Yani döngünün her turunda `lo` ve `hi` hakkında hep doğru kalan ifade nedir? (İpucu: `a[:lo]` içindeki her eleman `< x`, `a[hi:]` içindeki her eleman `>= x`. Bu iki şart cevabın hangi aralıkta olduğunu nasıl belirliyor? Neden `[lo, hi)` değil de `[lo, hi]` kapalı aralık? Hangi durumda sonuç tam `hi` olur?)
- Döngü neden `lo < hi` ile kontrol ediliyor da `lo <= hi` değil? `hi = mid` yazılırken neden `mid - 1` değil?
- Eşitlik durumunda (`a[mid] == x`) kod `else` dalına düşüp `hi = mid` yapıyor. Bu tercih fonksiyonun "en sol konum" sözleşmesini nasıl sağlıyor? `bisect_right` bu satırda ne yapardı?
- **Tarihî hata:** C'deki `(lo + hi) / 2` satırı, çok büyük dizilerde `lo + hi` toplamı `int` sınırını aşabiliyordu. C'de işaretli tamsayı taşması **tanımsız davranıştır (UB)**: tipik olarak negatif bir değere sarar, ama bu garanti değildir. Java'da ise taşma tanımlıdır; değer iki'ye tümleyenle negatife sarar (Bölüm 1). Aynı hata Java'nın `Arrays.binarySearch` gerçeklemesinde de yaklaşık dokuz yıl fark edilmeden kaldı; Joshua Bloch bunu 2006'da duyurdu. Taşmayan doğru yazım nedir? (İpucu: `lo + (hi - lo) / 2` neden güvenli?)
- Python'da bu hata neden *hiç* oluşmaz? (Bölüm 3'ü hatırla: Python'un `int` türünün C'den farkı ne?)
- Son olarak süreç sorusu: bu fonksiyonu sıfırdan yazman istenseydi, altı adımın hangisinde en çok zorlanırdın? Kenar durumların neler olurdu — boş liste, tek eleman, x'in tüm elemanlardan büyük olması?

## Bölüm Özeti

Bu bölümde bir *bilgi* değil, bir *süreç* öğrendik:

- **Bilgi ile beceri farklıdır.** Sözdizimi bilmek, boş dosyanın karşısında ne yazacağını bilmek demek değildir. Tıkanmanın üç sebebi: doğrudan kodu düşünmek, ilk seferde mükemmeli aramak, örüntü dağarcığının boş olması.
- **Altı adımlı döngü:** Anla → Örnekle → Kaba çöz → Örüntü bul → İyileştir → Doğrula. Tek yönlü değil; tıkandığın yerde geri dön.
- **Anla:** Girdi/çıktı imzasını yaz, soru sor. **Kısıt sana algoritmayı söyler** — n ≤ 10⁵ ise O(n²) daha yazmadan elenir; ~10⁸ işlem ≈ 1 saniye.
- **Örnekle:** Kâğıt üstünde çöz. Tipik örnek, kenar durumlar (boş, tek, tekrarlı, negatif, sınır değerler) ve fikrini çürüten karşı örnek.
- **Kaba çöz:** Yavaş çözüm utanç değil zemindir — doğruluk referansı, yapı sezgisi ve tavan verir.
- **Örüntü bul:** Sinyal → desen eşlemesi (hash, iki işaretçi, kayan pencere, ikili arama, yığın, BFS, DP…). Bu dağarcık okumakla değil çözmekle dolar.
- **İyileştir:** Üç soru — gereksiz iş var mı, tekrar hesap var mı, veri düzeni iyileştirilebilir mi? Cevap genelde bir **takas**: bellek ↔ zaman, ön işlem ↔ sorgu. Ölçmeden optimize etme.
- **Doğrula:** Elle iz sür, kenar durumları geçir, karmaşıklığı hesapla; birim hatalarına dikkat.
- **Veri yapısı seçimi**, "hangisi iyi?" değil "verime nasıl erişeceğim?" sorusuyla yapılır. Gerçek problemler genelde yapıların birleşimini ister.
- **Beyaz tahta protokolü:** Problemi geri anlat, soru sor, örnek çöz, kaba çözümü söyle, takası sesli düşün, sonra kod yaz, sonra kendi kodunu test et.

**Sonraki bölümde:** Süreci uyguladın, kodu yazdın — ve çalışmadı. Şimdi ne olacak? **Bölüm 6 — Debugging Sanatı**'nda hatayı sistematik olarak avlamayı öğreneceğiz: yeniden üretme, izole etme, teşhis, düzeltme, doğrulama döngüsü; ikili aramayla hata daraltma; ve `printf`'ten `gdb`'ye geçişin doğru zamanı.

::: mulakat
Klasik sorular — hemen cevaplamaya çalışma, her birini birkaç dakika düşün:

1. Bir problemde `n ≤ 20` kısıtını gördüğünde aklına ilk hangi çözüm türü gelmeli, neden?
2. Kaba kuvvet çözümü yazmanın, doğrudan optimum çözüme atlamaya göre üç avantajını sırala.
3. `O(n)` bir çözüm, `O(n log n)` bir çözümden her zaman daha mı hızlıdır? Karşı örnek verebilir misin?
4. "Sıralı dizi" bilgisi sana hangi iki tekniği açar? Bu bilgi bedava mıdır — dizi sıralı değilse ne yaparsın?
5. Elinde hem hızlı arama hem "her an en küçüğü al" ihtiyacı varsa hangi yapıları nasıl birleştirirsin?
6. Bir mülakatta problemi çözemedin. Puanını en çok artıracak üç davranış nedir?
:::
