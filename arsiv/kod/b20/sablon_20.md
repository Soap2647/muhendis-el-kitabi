%% kisim_no: V
%% kisim_ad: OOP & Yazılım Tasarımı
%% kisim_ayrac: evet
%% bolum_no: 20
%% baslik: OOP Temelleri

## Giriş: Veriyi ve davranışı birlikte taşımak

Bölüm 2'de bir `struct` tanımladık ve onu değiştiren fonksiyonları yanına yazdık. Bölüm 3'te Python'da sınıfla tanıştık. Bu bölümde iki fikri birleştiriyoruz: verinin yanında onu değiştiren kodu tutmak ve bunu yaparken nesnenin geçersiz bir duruma düşmesini engellemek. Buna nesne yönelimli programlama (OOP) diyoruz. Ama OOP bir sözcük oyunu değil; bellek düzeninin ve fonksiyon çağrısının belirli bir biçimidir. Bu bölümde o biçimi hem C'de elle kurarak hem de C++ ve Python'da derleyiciye ya da çalışma zamanına bıraktığımız hâlleriyle göreceğiz.

Neden önemli? Mülakatta "class ile struct arasındaki fark nedir", "virtual ne işe yarar", "yıkıcı neden sanal olmalı", "Rule of 5 nedir" gibi sorular neredeyse her yazılım pozisyonunda gelir. Bu soruların cevabı ezber değildir; her biri bir bellek ya da çağrı olayına dayanır. Bu olayı kendi elinle kurup, sızıntıyı bir sanitizer'ın raporunda gördüğünde cevabı kendin üretirsin.

Savunma sanayiinde ve gömülü tarafta OOP'nin hem değeri hem maliyeti daha görünür hâle gelir. Bir sensör sürücüsünü soyut bir arayüzle yazmak, yeni bir donanımı eklemeyi kolaylaştırır. Ama her nesnenin sakladığı tablo adresi, her sanal çağrının dolaylı atlaması ve her dinamik bellek ayırması zamanlamayı ve belleği etkiler. Bölüm 20.10'da bu maliyetleri ölçeceğiz.

Bu bölümde C++ ve Python'u yan yana kullanıyoruz. Her kavramda iki soruyu soracağız: iki dil bunu nasıl gerçekleştiriyor ve nerede ayrılıyorlar? Bu ayrımı görmek, kavramı tek bir dile bağlı kalmadan anlamanın en kısa yoludur.

::: not
Bu bölümdeki C ve C++ programları WSL içinde Ubuntu 24.04 üzerinde gcc/g++ 13.3.0 ile derlendi; `-std=c11`, `-std=c++17` ve `-Wall -Wextra` uyarıları açıktı. Hata ayıklama denetimleri için `-fsanitize=address,undefined` ile de çalıştırdık. Python programları Windows 11 üzerinde CPython 3.12.10 ile çalıştı. Süre ölçümleri AMD Ryzen 7 6800H üzerinde alındı; değerler makineye ve o andaki yüke bağlıdır. Rastgele girdiler sabit tohumla (`random.Random(42)` ve `std::mt19937(42)`) üretildi. Terminal çıktılarında sayfa genişliği için uzun satırlar kelime sınırından kaydırıldı; uzun komutlar `\` ile devam ettirildi. Kaydırma yalnızca düzenle ilgilidir, çıktının içeriği değişmemiştir. Kesir örneğinde `long` kullandık; Linux'ta 8 bayt, Windows'ta 4 bayttır. Taşınabilir kodda bunun yerine `<cstdint>` içindeki `int64_t` tercih edilir.
:::

## 20.1 Neden nesne yönelimli? Durum, davranış ve değişmezler

Bir kesir düşün: pay ve payda. Bu iki sayı tek başına bir anlam taşımaz; anlamı, birlikte belirli kurallara uymalarından gelir. Payda sıfır olamaz. Kesir sadeleştirilmiş olmalıdır, yani payla paydanın en büyük ortak böleni 1 olmalıdır. Ayrıca `2/4` ile `1/2` aynı sayıdır ve bunları ayırt etmek istemeyiz. Bu kurallara **değişmez (invariant)** diyoruz: nesnenin hayatı boyunca, her fonksiyon çağrısının başında ve sonunda doğru kalması gereken özellik.

Burada asıl soru şudur: bu kuralı kim koruyacak? Bir yaklaşım, her kullanıcının her işlemden önce kontrol yapmasıdır. Bu yaklaşım bir gün unutulur. Diğer yaklaşım, kuralı veri yapısının kendisine gömmektir: kurucu kuralı kurar, her işlem kuralı bozmadan sonuç üretir, ve dış dünya payı ile paydayı doğrudan değiştiremez. Birincisi disiplin ister; ikincisi tasarım ister. OOP'nin özü, ikinci yaklaşıma verdiği destektir: **durum (pay, payda) ile davranış (toplama, sadeleştirme) aynı yerde, dışarıdan korunmuş biçimde durur.** Bu korumaya kapsülleme diyoruz (20.4).

C'de aynı kuralı yazmak mümkündür, ama dil bunu sana zorlamaz. Aşağıdaki kesir C'de tanımlı bir `struct` olsun. Derleyici `payda = 0` olan bir kesirin oluşturulmasına hiçbir engel koymaz.

```c
typedef struct { long pay; long payda; } Kesir;

Kesir k = {1, 0};   /* payda sifir: invariant kirildi */
```

Bu iki satırı `gcc -Wall -Wextra -std=c11` ile derlediğimizde uyarı çıkmadı; program `1/0` yazdırdı. Dil kuralı bilmez, sadece bellek düzenini bilir. Dolayısıyla C'de değişmezi koruma sorumluluğu tamamen geliştiricinin omuzlarındadır. Bunu bir kural olarak değil, bir ilke olarak anla: kuralı tek bir yerde (kurucu ve işlem fonksiyonlarında) tutarsan, hatalar tek bir yerde aranır.

OOP'yi tek bir cümleyle tanımlamak zordur, çünkü farklı diller farklı üçlüler öne çıkarır. Yaygın üçlü şudur: **kapsülleme** (durumu korumak), **kalıtım** (ortak davranışı paylaşmak) ve **çok biçimlilik** (aynı çağrının türe göre farklı davranması). Bu üç kavram tek başına "OOP" değildir; bir tasarımın bu ilkelere uyup uymadığı önemlidir. Tasarım ilkelerinin hangi ölçütlerle değerlendirileceğini Bölüm 21 (SOLID) anlatacak. Bu bölüm ise bu üç kavramın dilde nasıl gerçekleştiğini öğretir.

## 20.2 C'de OOP'yi elle kurmak: struct ve fonksiyon işaretçisi

Bölüm 2.10'da fonksiyon işaretçilerini gördün. Bir `struct` içine fonksiyon işaretçileri koyarsan, o yapının her örneği kendi davranışını taşıyabilir. Bu, OOP'nin C'deki ilk ve en yalın hâlidir. Nesnenin davranışını belirleyen işaretçi tablosuna **sanal tablo (vtable)** diyoruz. Nesnenin tablo adresini tutan küçük işaretçiye ise **vptr** (sanal tablo işaretçisi) adını veriyoruz. C++ bu iki parçayı derleyicinin içinde kurar; biz burada onları elle kuracağız.

Aşağıdaki program bir `Sekil` arayüzünü ve iki somut şekli, yani daireyi ve dikdörtgeni, yalnızca C ile tanımlar. Dikkat et: `Daire` ve `Dikdortgen` aynı `Sekil` türünün ilk üyesine sahip. Bu, C'de "kalıtım" benzeri bir yerleşimdir: taban yapının adresi, türetilmiş yapının adresiyle aynıdır.

Aşağıdaki kodun ilk bölümü tip tanımlarını içerir. `SekilVT` tablosu iki işaretçi taşır; her `Sekil` nesnesi `vt` alanıyla bu tabloya bağlanır.

[[KOD c_vtable.c 1 25 c]]

Aşağıdaki ikinci bölüm, her şekil için davranışları yazar ve nesneleri kurar. `daire_alan` ve `dik_alan` fonksiyonları, kendilerine verilen `Sekil*` işaretçisini kendi türlerine dönüştürerek çalışır. Bu dönüşüm, C standardının yapı yerleşimi kuralına dayanır: bir yapının ilk üyesine işaretçi, o yapıya işaretçiyle birbirine dönüştürülebilir (C11, 6.7.2.1). Bu yüzden `taban` üyesini ilk sıraya koyduk.

[[KOD c_vtable.c 26 59 c]]

Son bölüm, bir `Sekil*` dizisini dolaşır ve her elemanın tablosu üzerinden `yazdir` ile `alan` fonksiyonlarını çağırır. Döngü, elemanların gerçek türünü bilmez; bu, çok biçimliliğin özüdür.

[[KOD c_vtable.c 60 72 c]]

Bu programı derleyip çalıştırdığımızda şu çıktıyı aldık:

[[TERM c_vtable]]

Çıktı, iki şeyi gösteriyor. Birincisi, aynı `Sekil*` türü üzerinden çağrılan `yazdir` ve `alan` farklı fonksiyonlara gitti: çağrının hedefi nesnenin gerçek türüne göre belirlendi. İkincisi, `sizeof(Sekil)` değeri 8 bayt; yani bir `Sekil` yalnızca tablo işaretçisinden ibaret. `Daire` ise 16 bayt: tablo işaretçisi ve yarıçap. Bu düzen, Şekil 20.1'de görünen bellek ve tablo ilişkisinin tam karşılığıdır.

![Şekil 20.1: Elle kurulmuş vtable (solda) ve C++ derleyicisinin kurduğu vtable (sağda). Her nesne bir tablo işaretçisi taşır; çağrı bu tablo üzerinden dolaylı yapılır.](gorseller/b20_elle_vtable.png)

Şekil 20.1'in sağ tarafı, aynı düzenin C++'taki karşılığıdır. Orada tablo işaretçisini (vptr) derleyici yazar, tabloyu derleyici üretir ve `virtual` anahtar sözcüğü, hangi çağrıların bu tablo üzerinden yapılacağını belirler. Tablodaki ilk iki girdi yıkıcılar için ayrılmıştır; bunu 20.6'da sanal yıkıcının neden gerektiğini gösterirken göreceğiz. Derleyici tablo düzenini Itanium C++ ABI'ye göre üretir; Linux ve GCC'de bu düzen gözlenen gerçektir, ama dilin standardı bu düzeni zorunlu kılmaz. Taşınabilir kodda tablo düzenine bağımlı olmamalısın.

Elle vtable'ın C dünyasında gerçek bir karşılığı vardır. Linux çekirdeğindeki dosya ve sürücü arayüzleri, bir `struct` içinde fonksiyon işaretçileri tutan işlem tablolarıyla (`file_operations` gibi) çalışır. Bölüm 2.10'da gördüğün geri çağırma (callback) desenini düşün: o desen, tek bir işaretçi yerine bir tablo koyulduğunda vtable'a dönüşür. MertOS'taki klavye sürücüsünün kaydı da bu kalıbın küçük bir örneğidir.

Bu noktada iki şey net olmalı. C'de bu düzeni kurmak tamamen elle ve tamamen geliştiricinin sorumluluğunda yapılır: tabloyu yanlış atarsan, hata derleme zamanında değil çalışma zamanında, muhtemelen dolaylı bir atlamada ortaya çıkar. C++ ise aynı düzeni derleyiciye yaptırır ve tip sistemiyle bu hataların bir kısmını derleme zamanında yakalar. Sonraki bölümlerde her C++ özelliğini bu elle kurulmuş modelle karşılaştıracağız.
## 20.3 Sınıf, nesne, kurucu, yıkıcı ve RAII

Az önceki C programını C++ ile yazdığımızda neler değişiyor? Önce söz dizimi: `struct` yerine `class` kullanıyoruz, tablo işaretçisini ve fonksiyon işaretçilerini elle yazmıyoruz, sanal fonksiyonları `virtual` ile işaretliyoruz. Aşağıdaki program aynı işi yapar. `Daire` kurucusu (constructor) yarıçapı alır ve `r_` üyesine yazar. `Sekil` yıkıcısı (destructor) sanaldır; bunun neden gerektiğini 20.6'da göreceğiz.

Burada bir ayrımı açıkça yapmak gerekir. Sınıf (class) bir şablondur; nesne (object) ondan yaratılan, kendi belleğine sahip örnektir. C'de bu ayrım yoktur, çünkü `struct` hem şablon hem de değişken gibi kullanılır. C++'ta `Daire d(2.0);` satırı bellekte bir `Daire` nesnesi kurar ve kurucuyu çağırır. Yıkıcı ise nesne yaşam süresi bittiğinde, yani bulunduğu kapsam kapandığında otomatik çağrılır.

[[KOD cpp_vtable.cpp 1 33 cpp]]

Programın ikinci yarısı, nesneleri bir dizide tutup sanal çağrıyla dolaşır. Çıktı, C sürümüyle aynıdır; bu bilerek seçilmiş bir karşılaştırmadır.

[[KOD cpp_vtable.cpp 34 47 cpp]]

[[TERM cpp_vtable]]

`nm -C` çıktısındaki `vtable for Daire` satırı, derleyicinin bu sınıf için gerçekten bir tablo ürettiğini gösteriyor. Dikkat et: `nm` yalnızca somut sınıfların tablolarını listeledi; soyut `Sekil` için tablo sembolü çıkmadı, çünkü ondan hiç nesne yaratılmıyor. `sizeof(Daire)` değeri 16 bayttır; bunun 8'i tablo işaretçisi, 8'i ise `double r_` üyesidir.

### RAII: kaynak edinimi başlatmadır

C++'ın en önemli fikirlerinden biri, bir kaynağın yaşam süresini nesnenin yaşam süresine bağlamaktır. Buna RAII (Resource Acquisition Is Initialization, kaynak edinimi başlatmadır) diyoruz. Kaynak, yani dosya, kilit ya da bellek bloğu, kurucuda alınır; yıkıcıda bırakılır. Kapsam hangi yoldan olursa olsun, normal çıkışta ya da bir istisna fırlatıldığında, yıkıcı çağrılır. Bu sayede serbest bırakmayı unutmak, yapısal olarak zorlaştırılmış olur.

Aşağıdaki program bir kilit ve bir dosya sarmalayıcısı yazar. `islem` fonksiyonu iki kaynak alır, birinin arasına bir dosya yazma işlemi koyar ve isteğe bağlı olarak bir istisna fırlatır. Kaynakların bırakılma sırasını gözlemleyebilmek için her kurucu ve yıkıcı ekrana yazar.

[[KOD raii.cpp 1 24 cpp]]

Dosya sarmalayıcısında kopya yasağı önemlidir. İki `Dosya` nesnesi aynı `FILE*` işaretçisini paylaşırsa, iki kez `fclose` çağrılır; bu, Bölüm 2'de gördüğümüz çift serbest bırakma hatasının dosya karşılığıdır. Bu yüzden kopya kurucu ve kopya atama `= delete` ile devre dışı bırakıldı. Taşıma (move) ise nesneyi dosya sahipliğinin el değiştirmesi olarak tanımlar; bunu 20.5'te ayrıntılı göreceğiz.

[[KOD raii.cpp 25 50 cpp]]

[[KOD raii.cpp 51 62 cpp]]

Bu program, AddressSanitizer ve UBSan ile derlenip çalıştırıldı ve hiçbir hata raporlanmadı:

[[TERM raii]]

Çıktı, bırakma sırasını açıkça gösteriyor. İstisnalı yolda `kilit-B` önce, sonra dosya, en son `kilit-A` bırakıldı. Yani yıkıcılar, kuruluşun tersi sırayla çağrıldı. Bu son giren ilk çıkar (LIFO) düzeni, bir yığın gibi çalışır; Şekil 20.2 bunu gösteriyor. Son satırdaki `acik kilit = 0` ise istisnaya rağmen hiçbir kilidin açık kalmadığını doğruluyor.

![Şekil 20.2: RAII'de kaynaklar kuruluş sırasıyla edinilir, yıkımda ters sırayla bırakılır. İstisna, yığını ters yönde açar.](gorseller/b20_raii_yigin.png)

Python'da aynı sözleşme `with` ifadesiyle kurulur. Bölüm 3.8'de context manager'ı gördün; burada onu RAII'nin karşılığı olarak okuyoruz. `__enter__` edinimi, `__exit__` bırakmayı yapar, ve `__exit__` her çıkışta, istisna olsun ya da olmasın, çağrılır. Aşağıdaki programda `__exit__` False döndürür; bu, istisnayı yutmadığımız, yani dışarıya ilettiğimiz anlamına gelir. Aynı programda `__del__` yıkıcısının neden güvenilmez olduğunu da gösteriyoruz.

[[KOD py_kaynak.py 1 28 python]]

Programın ikinci kısmı iki durumu karşılaştırır: döngüsüz bir nesne ve kendine dönen bir referans döngüsü. `gc.disable()` çağrısı, çöp toplayıcının (garbage collector) döngüyü temizlemesini engeller; böylece gecikmenin etkisini görebiliriz.

[[KOD py_kaynak.py 29 41 python]]

[[TERM py_kaynak]]

İlk durumda `__del__`, `del d` satırında hemen çalıştı, çünkü nesnenin referans sayısı sıfıra düştü. İkinci durumda, `del a, b` sonrasında iki nesne hâlâ birbirine referans verdiği için bellekte kaldı; `__del__` yalnızca `gc.collect()` çağrıldığında çalıştı. CPython'un bu davranışı bir uygulama ayrıntısıdır; Python referans kılavuzu `__del__`'in ne zaman çağrılacağını garanti etmez (genel bilgi). Bu yüzden dosya ya da kilit gibi kaynakları `__del__`'e bırakma; `with` kullan. Kaynağı kapatmak için yıkıcıya değil, açık bir sözleşmeye güven.

## 20.4 Kapsülleme ve değişmezleri korumak

Kapsülleme, bir nesnenin iç durumuna dışarıdan doğrudan dokunulmasını engelleme ilkesidir. C++'ta bunu erişim belirleyicileriyle (`private`, `protected`, `public`) yaparsın. Python'da ise bir erişim denetimi yoktur; bunun yerine bir kurallar sistemi vardır: tek alt çizgi (`_x`) "bunu dışarıdan kullanma" anlamına gelir, çift alt çizgi (`__x`) ise derleyici değil yorumlayıcı tarafından sınıf adıyla değiştirilir (ad bozma, name mangling). Aşağıdaki küçük programda bu farkı görüyoruz.

[[KOD py_ad.py 1 10 python]]

Bu programın çıktısı şöyle:

[[TERM py_ad]]

`__gizli` özniteliği `_Hesap__gizli` adına dönüştü; yani ad bozma, kaçış yolu sağlamaz ama gizlemeyi de tam yapmaz. Python'da "özel" bir şey yoktur, yalnızca bir anlaşma vardır. Bu, Python'un bir tasarım felsefesidir: sorumluluk kullanıcıdadır. Buna karşılık C++ derleyicisi `private` üyeye erişimi derleme zamanında reddeder.

Asıl önemli nokta, kapsüllemenin amacının erişimi kısıtlamak değil, değişmezi korumak olmasıdır. Kesir örneğimize dönelim. Kurucu, payda sıfır mı diye kontrol eder, işareti paydaya taşır ve sadeleştirir. Bu kuralların hepsi kurucuda ve işlemlerde tutulur; dış dünya `pay_` ve `payda_` üyelerini doğrudan değiştiremez. Aşağıdaki başlık dosyası bu sınıfı içerir.

[[KOD kesir.hpp 1 26 cpp]]

Sınıfın geri kalanı, toplama, çarpma ve karşılaştırma işlemlerini içerir. Her işlem yeni bir `Kesir` döndürür; sonuç kurucudan geçtiği için sadeleştirme her zaman uygulanır.

[[KOD kesir.hpp 27 41 cpp]]

Bu sınıfı rastgele işlemlerle sınamak için bir test yazdık. Test, her sonucun değişmezi koruyup korumadığını kontrol eder; ayrıca bozuk bir girdiyi (payda sıfır) yakalayıp yakalamadığını görür. Tohum 42 ile 100000 işlem yapıldı.

[[KOD kesir_test.cpp 1 40 cpp]]

[[TERM kesir_test]]

Çıktıda `IHLAL` satırının yer almaması, 100000 rastgele işlemde sonuçların hepsinin değişmezi koruduğu anlamına gelir. `6/-4` girdisinin `-3/2`'ye dönüşmesi, işaretin paya taşındığını ve sadeleştirmenin uygulandığını gösterir. Bu sonuç, Örnek 1'de adım adım izleyeceğimiz şeydir.

Python tarafında aynı sınıfı `__slots__` ile yazmak mümkün; bunun bellek etkisini 20.10'da ölçeceğiz. Burada yalnızca değişmezin aynı fikirle korunduğunu görelim. Test, Python'un kendi `Fraction` sınıfını bir referans olarak kullanır: iki sınıf aynı işlemleri yapıyorsa aynı sonucu vermelidir.

[[KOD py_kesir.py 1 39 python]]

[[KOD py_kesir.py 40 60 python]]

[[TERM py_kesir]]

Python sürümünde `__eq__` ile `__hash__`'i birlikte tanımladık. Bunun neden gerektiğini 20.9'da göreceğiz. Şimdilik şu noktayı not et: Python `Kesir` sınıfımız, aynı rastgele girdilerle `Fraction` sonuçlarına karşı sınandığında 100000 işlemde tek bir uyuşmazlık çıkarmadı.

## 20.5 Kopyalama semantiği: Rule of 5, sığ ve derin kopya

Bir nesneyi kopyalamak göründüğünden daha karmaşıktır. Kopyalama, nesnenin hangi kısmının çoğaltılacağına karar vermek demektir. Üyeler yalnızca sayıysa bir bit kopyası yeterlidir. Ama üye bir işaretçiyse, yani başka bir belleğe bakıyorsa, bit kopyası iki nesnenin aynı belleği paylaşmasına yol açar. Buna **sığ kopya (shallow copy)** diyoruz. İkisinden biri belleği serbest bıraktığında diğeri sarkan bir işaretçi tutar; ikisi de serbest bırakırsa çift serbest bırakma olur.

Bu sorunu, küçük bir dizgi sınıfı üzerinde görelim. Sınıf, Bölüm 2.6'da yazdığın string kavramını C++ nesnesine taşır ve MertOS'taki `kstring.hpp` tasarımına benzer bir yapı kullanır. Sınıf, kendi belleğini `new char[]` ile alır ve yıkıcıda `delete[]` ile bırakır. Bu yapıyı beş özel üyeyle tamamlıyoruz: yıkıcı, kopya kurucu, kopya atama, taşıma kurucu ve taşıma atama. Bu beşliye Rule of 5 diyoruz.

Dizgi sınıfını iki parçada veriyoruz. Önce veri üyesi, kurucu ve kopya işlemleri gelir.

[[KOD dizgi.hpp 1 34 cpp]]

Kopya atama `copy-and-swap` deseniyle yazıldı: önce yeni bir kopya oluşturulur, sonra iki nesnenin içerikleri takas edilir; geçici nesne yıkıcıda eski belleği serbest bırakır. Böylece kopya sırasında bir istisna olursa nesne tutarlı kalır ve `a = a` gibi bir oz-atama da güvenli çalışır.

[[KOD dizgi.hpp 35 67 cpp]]

Bu sınıfı rastgele bir işlem dizisiyle sınadık: dört dizgi üzerinde ekleme, kopya atama ve taşıma atama, 20000 kez yapıldı ve her adımda `std::string` ile karşılaştırıldı. Test ASan ve UBSan ile derlendi.

[[KOD dizgi_test.cpp 1 23 cpp]]

[[KOD dizgi_test.cpp 24 42 cpp]]

[[TERM dizgi_test]]

Çıktı, 20000 işlemin tamamında dizgilerin `std::string` karşılıklarıyla birebir aynı olduğunu gösteriyor. Sanitizer hiçbir bellek hatası raporlamadı. Şimdi kopya kurucuyu yazmadığımızda ne olduğuna bakalım. Aşağıdaki program aynı sınıfın bozuk bir sürümüdür: kopya kurucu tanımlanmadı, derleyici sığ kopya üretir.

[[KOD dizgi_hata.cpp 1 20 cpp]]

[[TERM dizgi_hata]]

AddressSanitizer, ikinci yıkıcının aynı bloğu ikinci kez serbest bıraktığını yakaladı (`attempting double-free`). Raporun iz kısmı hatayı `Dizgi::~Dizgi()` yıkıcısına, yani `delete[]` çağrısına bağlıyor. Normal derlemede glibc bazı çift serbest bırakmaları fark edip programı durdurabilir, bazılarında ise bellek bozulması fark edilmeden ilerleyebilir. Sanitizer ise hatayı her durumda, tam kaynak satırıyla raporlar; bu yüzden bu bölümdeki her bellek kodunu ASan ile sınadık.

Sığ kopyanın bellek görünümü Şekil 20.3'te var. Kural şudur: kaynak sahibi bir sınıf ya beşliyi eksiksiz yazar ya da kopyayı tamamen kapatır. Yarım bırakılan beşli, en çok hatayı üreten yerdir.

![Şekil 20.3: Sığ kopyada iki nesne aynı belleğe bakar ve çift serbest bırakma oluşur (solda). Derin kopyada her nesne kendi belleğine sahiptir (sağda).](gorseller/b20_sig_derin.png)

Taşıma (move) semantiğini kısaca not edelim. Taşıma kurucu, kaynağın belleğini "çalar": işaretçiyi yeni nesneye verir, kaynağı boş bırakır. Bu, geçici nesneler için kopyadan çok daha ucuzdur. `std::move` yalnızca bir dönüşümdür; taşımayı yapan, taşıma kurucusu ya da taşıma atamasıdır. Taşınmış nesne, dilin garantisi gereği "geçerli ama belirtilmemiş" bir durumda kalır; yıkıcısı çağrılabilir, yeniden atanabilir, ama değerine güvenilmez. Taşıma davranışını Örnek 3'te adım adım izleyeceğiz.

Kural seçimi için bir karar akışı yeterlidir. Kaynak sahibi olmayan sınıflarda hiçbir özel üye yazma (Rule of 0). Kaynak sahibi sınıflarda beşliyi eksiksiz yaz. Kaynağı bir sınıfa (`std::unique_ptr`, `std::vector`, `Dizgi`) devredersen, sınıfın kendisi yıkıcı yazmaz; bu da Rule of 0'a geri döner.

![Şekil 20.4: Rule of 0 ve Rule of 5 arasındaki karar. Kaynak sahipliğini bir sınıfa devretmek çoğu zaman en iyi çözümdür.](gorseller/b20_kural_secimi.png)

Python'da bu sorunun yapısı farklıdır. Python'da değişkenler nesnelerin etiketleridir (Bölüm 3.2); atama, değeri kopyalamaz, aynı nesneye yeni bir etiket yapıştırır. Kopya gerekirse açıkça istemelisin. `list.copy()` yalnızca üst düzey kabuğu kopyalar (sığ kopya); iç içe listeler paylaşılır. `copy.deepcopy` ise bütün iç içe nesneleri yeniden yaratır. Aşağıdaki program bu üç durumu gösterir.

[[KOD py_kopya.py 1 16 python]]

[[TERM py_kopya]]

İlk satırda `ic` içindeki iki eleman aynı listeye işaret ettiği için `append` iki kez görünür. `sig` ile `s` arasındaki ilişki de aynıdır: `sig[0]` ile `s[0]` aynı iç listedir; `9` her ikisine de düştü. `deepcopy` ise `derin[0]`'ı tamamen yeni bir liste yaptığı için, `derin` üzerindeki `7` değeri `s` içinde görünmez. Python'da kopya sorusu, bir C++ sınıfındaki kadar tehlikeli değildir, çünkü bellek sahipliği çöp toplayıcıya devredilmiştir. Ama aynı nesne üzerinde iki farklı sorumluluk varsa, sığ kopya yine beklenmedik paylaşımlara yol açar.
## 20.6 Kalıtım: is-a, sanal yıkıcı, dilimleme ve MRO

Kalıtım, bir sınıfın başka bir sınıfın davranışını devralmasıdır. Mantıksal test "is-a", yani "bir Tureyen bir Taban'dır" cümlesinin doğru olup olmadığıdır. Bu test başarılıysa kalıtım mantıklı olabilir; değilse yanlış bir soyutlama kurmuş olursun. Kalıtımın ilk dersi budur: bir ilişkiyi yalnızca ortak kod için kurma; is-a ilişkisi doğru değilse kalıtım yanlıştır (Bölüm 20.8'de bunun alternatifi olan bileşimi göreceğiz).

C++'ta kalıtım `class Tureyen : public Taban` söz dizimiyle kurulur. Bir alt sınıf, bir taban sınıfa ait işaretçiyle kullanıldığında, sanal fonksiyonlar gerçek türe göre çağrılır. Bu davranışı açıklamak için bir yıkıcı sorusu önemlidir. Aşağıdaki programda taban sınıfın yıkıcısı sanal değildir ve alt sınıf kendi kaynağını ayırır.

[[KOD yikici.cpp 1 30 cpp]]

Programı dört farklı komutla derleyip çalıştırdık; çıktının tamamı aşağıda. İlk komut sanal olmayan yıkıcıyla `-Wall -Wextra` altında derlendi; derleyicinin uyarısı çıktının başında görünüyor.

[[TERM yikici]]

Uyarının metni, durumu doğru tarif ediyor: çok biçimli bir sınıf nesnesi, sanal olmayan yıkıcıya sahip bir işaretçiyle silinirse tanımsız davranış (UB) oluşur. Standart bu durumda ne olacağını garanti etmez. Çıktının ikinci bölümü sanal olmayan sürümün çalışma zamanı davranışını gösteriyor: yalnızca `~Taban` çalıştı, `~Tureyen` çalışmadı ve `tampon_` için ayrılan 4000 baytlık bellek sızdı. LeakSanitizer bu sızıntıyı kaynak satırıyla raporladı. Not: ASan varsayılan olarak bu durumu önce "tür uyuşmazlığı" (new-delete-type-mismatch) olarak yakalar; sızıntı raporunu görmek için bu denetimi `ASAN_OPTIONS` ile kapatmak gerekti. İki hata da aynı kök nedenden doğar.

Sanal yıkıcı çözümü tek bir kelimedir: `virtual`. Yıkıcıyı sanal yaptığımızda, `delete p` çağrısı önce `~Tureyen`'i, sonra `~Taban`'ı çalıştırır. Son komutun çıktısında bunu görüyorsun: önce `Tureyen yikici` (kaynağı serbest bırakır), sonra `Taban yikici` yazdı ve ASan sızıntı bildirmedi. Kuralı akılda tutmak yeter: taban sınıf çok biçimli kullanılacaksa, yıkıcısı sanal olmalıdır. Pratikte bir kural olarak uygula: bir sınıfta en az bir sanal fonksiyon varsa ya da başka sınıflar ondan türetilecekse, yıkıcısı sanal olmalıdır.

Nesne dilimleme (object slicing) ikinci büyük tuzaktır. Bir alt sınıf nesnesi, taban sınıf türünde bir değişkene değerle kopyalanırsa, fazla üyeler kaybolur ve sanal çağrı artık alt sınıfın davranışını göstermez.

[[KOD dilimleme.cpp 1 33 cpp]]

[[TERM dilimleme]]

Çıktıdaki ilk satır beklenmedik değildir: değerle geçirilen `Taban` kopyasında `ad()` taban sürümünü döndürdü. İkinci satır, referansla geçirildiğinde gerçek türün (`Tureyen`) korunduğunu gösteriyor. Üçüncü satır, atamanın da aynı kaybı yaptığını gösterir. `sizeof(Tureyen)` değeri 16 bayttır; `ek` üyesi bu yapıda vardır ama `Taban` kopyasında yoktur. Şekil 20.5 bu kaybın bellek resmini gösteriyor.

![Şekil 20.5: Nesne dilimleme. Değerle kopyalanan Taban yalnızca kendi üyelerini taşır; ek üyesi ve türetilmiş davranış kaybolur.](gorseller/b20_dilimleme.png)

Kuralı yalnızca bu kadar özetleyelim: çok biçimli nesneleri her zaman referansla ya da işaretçiyle taşı. Değerle geçirmek, yalnızca türü kaybetmek değil, nesnenin bir kısmını sessizce yok etmek demektir.

### Python'da kalıtım ve MRO

Python'da kalıtım sözdizimi benzerdir, ama kavramsal yapısı farklıdır. Python'da her metot çağrısı çalışma zamanında aranır; yani `obj.metot()` her zaman "sanal" çağrıdır. Çoklu kalıtım desteklenir. Bir sınıf birden çok tabandan türediğinde, hangi tabanın metodunun çağrılacağı bir sıraya göre belirlenir: çözüm sırası (Method Resolution Order, MRO). CPython, bu sırayı C3 doğrusallaştırma algoritmasıyla hesaplar. Elmas biçimli kalıtım, MRO'nun en çok öğretici olduğu durumdur: `D`, hem `B`'den hem `C`'den türer ve ikisi de `A`'dan türer.

[[KOD py_mro.py 1 39 python]]

[[TERM py_mro]]

`D.__mro__` çıktısı, arama sırasını açıkça veriyor: `[D, B, C, A, object]`. `super()` çağrısı, sınıfın kendi adına değil, nesnenin MRO'sundaki bir sonraki sınıfa gider; bu yüzden `D.hazirla` çağrıldığında zincir `B`'ye, oradan `C`'ye ve sonra `A`'ya gitti. `A`'nın `super()` çağrısı yoktur; zincir orada biter. İkinci deneme, `class E(A, B)` tanımının bir `TypeError` ile reddedildiğini gösteriyor: `A`, `B`'nin atasıyken `B`'yi tabanı olarak yazmak, tutarlı bir sıra oluşturamaz. Şekil 20.6 bu sırayı çizer.

![Şekil 20.6: Elmas kalıtımı ve MRO sırası. super(), çağrıyı MRO'da bir sonraki sınıfa iletir.](gorseller/b20_elmas_mro.png)

## 20.7 Çok biçimlilik: sanal fonksiyon, arayüz ve duck typing

Çok biçimlilik, aynı çağrının farklı türlerde farklı davranması demektir. Üç ayrı biçimini görmek gerekir. Birincisi, çalışma zamanında çözülen dinamik çok biçimlilik, yani sanal fonksiyonlardır; bunu 20.1–20.2'de vtable üzerinden gördük. İkincisi, derleme zamanında çözülen statik çok biçimlilik, yani aşırı yükleme (overloading) ve şablonlardır; bu bölümde ayrıntıya girmiyoruz, ama Bölüm 22'deki Strategy kalıbında şablonlarla birlikte geri döneceğiz. Üçüncüsü, Python'un duck typing yaklaşımıdır: bir nesnenin hangi sınıftan geldiği değil, sahip olduğu metotlar önemlidir.

C++'ta yalnızca saf sanal fonksiyonlardan (`= 0`) oluşan bir sınıf arayüz (interface) olur. Arayüzden türetilen her sınıf, tüm saf sanal fonksiyonları uygulamak zorundadır; aksi hâlde kendisi de soyut kalır. Bu, MertOS'taki sürücü kavramının dildeki karşılığıdır: çekirdek, her sürücünün aynı arayüzü uyguladığını bilir, ama sürücünün ayrıntısını bilmez.

Python'da bu fikir iki yoldan kurulabilir. `abc.ABC` ve `@abstractmethod` ile nominal bir arayüz tanımlarsın; alt sınıf o arayüzden türemek zorundadır. `typing.Protocol` ile yapısal bir arayüz tanımlarsın; bir sınıf o arayüzden türemeden de, metotları uygunsa kabul edilir. Aşağıdaki program üçünü birlikte gösterir.

[[KOD py_cokbicim.py 1 21 python]]

[[KOD py_cokbicim.py 22 43 python]]

[[TERM py_cokbicim]]

`Surucu()` çağrısı, soyut metot uygulanmadığı için reddedildi; hata mesajı eksik metodun adını söylüyor. `EskiSensor`, `Surucu`'den türemediği hâlde `olc` fonksiyonuna verilebildi, çünkü `oku` metoduna sahip. Bu, Protocol'ün yapısal tipleme gücüdür ve duck typing'in tip denetimli biçimidir. `dataclass(order=True)` ise karşılaştırma metotlarını da üretti; `etiketler` alanı `compare=False` ile eşitlik ve sıralamanın dışında tutuldu.

Hangi aracı seçmelisin? Kendi kontrolünde olan, ortak davranışı ve durumu paylaşan hiyerarşiler için `ABC` uygun. Dışarıdan gelen, senin yazmadığın nesneleri kabul edeceğin yerlerde `Protocol` daha esnektir. Bu seçimin tasarım tarafı Bölüm 21'de (SOLID'deki arayüz ayrımı) ve Bölüm 22'de (Strategy, Adapter) ayrıntılı olarak tartışılacak.

## 20.8 Bileşim, kalıtımdan önce: kırılgan taban sınıf

Kalıtımın en tehlikeli kullanımı, yalnızca koda sahip olmak için kalıtım yapmaktır. Bu, taban sınıfın iç davranışına bağımlılık yaratır. Taban sınıf bir gün kendi içinde bir metodu başka bir metodu çağıracak şekilde değiştirirse, alt sınıfın davranışı beklenmedik biçimde değişir. Buna kırılgan taban sınıf (fragile base class) problemi denir.

Aşağıdaki örnekte `set`'ten türeyen bir sınıf, eleman sayısını tutmak istiyor. `add` metodunu geçersiz kılıyor ve her eklemede sayacı artırıyor. Sonra toplu ekleme için `update` çağırıyor.

[[KOD py_kirilgan.py 1 19 python]]

[[KOD py_kirilgan.py 20 38 python]]

[[TERM py_kirilgan]]

`update` yoluyla eklenen üç eleman sayaca yansımadı: beklenen 4, gerçek 1. CPython'da `set.update` C düzeyinde çalışır ve geçersiz kılınmış `add`'i çağırmaz. Bu bir uygulama ayrıntısıdır; dilin garantisi değildir (genel bilgi). Ama asıl ders şudur: taban sınıfın iç yapısına güvenen her alt sınıf, bu ayrıntı değiştiğinde kırılır. İkinci sınıf, aynı işi bileşimle yapar: içinde bir `set` tutar ve tüm ekleme yollarını tek bir metottan geçirir. Sonuç doğru: 4.

![Şekil 20.7: Kalıtımla kırılgan sayaç (solda) ve bileşimle tek giriş noktası (sağda).](gorseller/b20_bilesim_kalitim.png)

Bileşim (composition) ilişkisi "has-a", yani "bir SayanBilesik bir kümeye sahiptir" cümlesidir. Kalıtım "is-a" ile kullanıldığında kod paylaşımı, bileşim "has-a" ile kullanıldığında sorumluluk ayrımı sağlar. Genel bir yönerge olarak: önce bileşimi dene; kalıtım yalnızca is-a ilişkisi açıkça varsa ve taban sınıfın davranışına sözleşme olarak güvenebiliyorsan kullan. Liskov yerine koyma ilkesi ve arayüz ayrımı gibi tasarım kuralları Bölüm 21'in konusu.

## 20.9 Özel metotlar, eşitlik ve hash sözleşmesi; dataclass

Python'da `__eq__`, `__hash__`, `__repr__` gibi özel metotlar (dunder metotları), dilin operatörleri ve yerleşik fonksiyonlarıyla sınıfın nasıl etkileşeceğini belirler. C++'ta karşılığı operatör aşırı yüklemesidir: `operator==`, `operator<` gibi operatörleri sınıfın kendi anlamıyla tanımlarsın. Kesir sınıfımızda bunu yaptık: `operator==` ve `operator<` tanımladık.

Eşitlik ve karma (hash) arasında bir sözleşme vardır ve bunu bozmak sessiz hatalar üretir. Sözleşme şudur: iki nesne eşitse, aynı hash değerine sahip olmalıdır. Bölüm 9'da hash tablosunun, anahtarın hash değerine göre bir kovaya yerleştiğini gördün. Eşit iki nesne farklı kovalara düşerse, tablo onları bulamaz.

[[KOD py_hash.py 1 38 python]]

[[TERM py_hash]]

İlk durum, `__eq__` tanımlayıp `__hash__` tanımlamadığımızda ne olduğunu gösteriyor. Python, `__eq__` tanımlandığında `__hash__`'i otomatik olarak `None` yapar; bu sınıfın nesneleri kümeye konamaz. İkinci durumda hash tanımladık ve küme davranışı doğru. Sonra ilginç bir şey yaptık: kümeye koyduğumuz nesnenin `x` değerini değiştirdik. Nesne artık eski hash değerinde değil; bu yüzden hem eski değerle hem yeni değerle aradığımızda bulunamadı. Kural açık: karma yapısında kullanılan bir nesne, hash'ini belirleyen alanlar değişmez olmalıdır. Bu yüzden `dataclass(frozen=True)` karma için güvenli bir seçimdir.

`dataclass`, bu sınıfların kurucusunu, `__repr__`'ini, `__eq__`'ini ve gerekirse karşılaştırma metotlarını senin yerine üretir. Üretilen kodun gerçekte nasıl göründüğünü görmek için, `dataclasses._create_fn` fonksiyonunu çalışma anında izleyen bir program yazdık. Bu teknik, Kod Okuma bölümünde kaynağa bakmadan önce üretilen kodu doğrulamak için iyi bir yoldur.

[[KOD py_uretim.py 1 30 python]]

[[TERM py_uretim]]

İzleme çıktısı `__init__` gövdesinin gerçekte `self.zaman=zaman` ve `self.deger=deger` satırlarından oluştuğunu gösteriyor. `frozen=True` olan sınıfta ise atama `object.__setattr__` üzerinden yapılıyor; bu yüzden dondurulmuş bir nesnede doğrudan atama `FrozenInstanceError` fırlatıyor. Bu tasarım, C++'taki `const` nesne kavramına benzer: derleyici `const` nesnede üye değişikliğine izin vermez, Python ise çalışma zamanında reddeder.

C++'ta aynı işe karşılık gelen dil özelliği, toplama türü (aggregate) ve `struct` kullanımıdır. Üyeleri herkese açık ve sanal fonksiyonu olmayan bir `struct`, basit bir veri kaydı olarak kullanılabilir. Bu tür nesneler kurucu tanımlamadan `{}` ile başlatılır. Ama değişmezi korumanın gerektiği her yerde, Bölüm 20.4'teki gibi bir `class` ve kapsülleme tercih edilir.

## 20.10 Bellek düzeni ve maliyet: vptr, __slots__ ve sanal çağrı

Bu bölümde şimdiye kadar yalnızca mantıksal yapıyla ilgilendik. Şimdi nesnenin bellekte nasıl durduğuna ve sanal çağrının ne kadara mal olduğuna bakacağız. Gömülü sistemde ya da yüksek hızlı bir döngüde bu iki soru, tasarım kararlarının sınırını belirler.

C++'ta bir sınıfın bellek düzenini `sizeof` ve üye adresleriyle ölçebilirsin. Aşağıdaki program bir taban sınıf ile onu türeten bir sınıfın üyelerinin ofsetlerini ölçer.

[[KOD offs.cpp 1 22 cpp]]

[[TERM offs]]

`kimlik` ofseti 8: yani ilk 8 bayt tablo işaretçisine (vptr) ayrılmış. `ek` ofseti ise 12. Taban sınıfın `sizeof` değeri 16 olmasına rağmen, `kimlik` 4 bayt olduğu için 12–15 arası boşluktur; GCC ve Itanium ABI, türetilmiş sınıfın üyesini bu kuyruk dolgusunun (tail padding) içine yerleştirdi. Bu bir ABI ayrıntısıdır; taşınabilir kodda varsayılmamalıdır. Ama bellek düzenini okumayı öğrenmek için iyi bir örnektir. Şekil 20.8, tüm sınıfların bellek görünümünü özetliyor.

![Şekil 20.8: Sınıfların bellek düzeni. Her sanal sınıf nesnesi başta 8 baytlık bir tablo işaretçisi taşır; Tureyen'in ek üyesi Taban'ın kuyruk dolgusuna yerleşir.](gorseller/b20_nesne_duzeni.png)

Python'da nesnelerin bellek maliyeti farklı bir yapıdadır. Varsayılan olarak her nesnenin özniteliklerini bir sözlükte (`__dict__`) tutmak esnekliği sağlar: yeni bir öznitelik her zaman eklenebilir. `__slots__` tanımlandığında ise nesne, sabit bir öznitelik listesi için yuva ayırır ve sözlük oluşturmaz. Bu, bellek tasarrufu sağlar ama yeni öznitelik eklemeyi engeller. Aşağıdaki program iki yaklaşımı birebir bellek ölçümüyle karşılaştırır.

[[KOD py_bellek.py 1 23 python]]

[[KOD py_bellek.py 24 45 python]]

[[TERM py_bellek]]

Ölçüm `tracemalloc` ile yapıldı; 100000 nesnenin listesi için nesne başına ortalama bellek: `__dict__` sürümünde yaklaşık 120 bayt, `__slots__` sürümünde yaklaşık 88 bayt. Bu değerler, nesnenin kendisinin yanında listeye ait işaretçileri ve her nesnenin tamsayı değerlerini de içerir; ama iki sürümde bu öğeler aynı olduğu için fark sınıfın kendisinden gelir. `sys.getsizeof` ise yalnızca nesnenin kendi başlığını gösterir; bu yüzden bu fark, `getsizeof` çıktısında doğrudan görünmez. Ayrıca CPython 3.12'de öznitelik değerleri çoğu durumda sınıfın paylaşılan anahtar düzeniyle nesnenin içinde tutulur; bu ayrıntı sürüme bağlıdır (genel bilgi). Farkı büyüklük sırası olarak düşünmek ve kendi sürümünde ölçmek daha güvenlidir.

Farkın büyüklüğünü görmek için aynı ölçümü farklı `n` değerleri için tekrarladık. CSV dosyası, `bellek_csv.py` betiğiyle üretildi; betik yalnızca standart kütüphaneyi kullanır.

[[KOD bellek_csv.py 1 36 python]]

[[TABLO bellek]]

Tablo, farkın `n` büyüdükçe kararlı kaldığını gösteriyor. Şekil 20.9 aynı veriyi grafikle gösterir.

![Şekil 20.9: Python'da nesne başına bellek, __dict__ ve __slots__ için. Veri engine/veri/b20_bellek_olcum.csv dosyasından okunmuştur.](gorseller/b20_bellek_olcum.png)

Sanal çağrının maliyeti, bellek düzeninden farklı bir sorudur: "bu çağrı ne kadar zaman alır?" Sanal çağrı, normal bir çağrıdan daha fazla iş yapar: nesnenin tablo işaretçisini okur, tablodan adresi alır ve dolaylı atlama yapar. Bu işin büyüklüğünü tahmin etmek yerine ölçmek gerekir. Bölüm 12.11'de öğrendiğimiz ölçüm disiplinini burada uyguluyoruz: sabit tohum, aynı iş miktarı, tekrar ve medyan.

Aşağıdaki program aynı diziyi iki yolla işler. Birincisi, her elemanın tür etiketini (`tur`) bir `switch` ile dallandıran sanal olmayan yöntemdir. İkincisi, `Sekil*` işaretçilerini sanal `alan()` ile çağıran yöntemdir. İki dağılım ölçülür: tek tür (her eleman daire) ve karışık (her eleman rastgele daire ya da kare, tohum 42). Her iki yöntem aynı sonucu üretmek zorundadır; program bu farkı da `sonuc_farki` olarak yazar.

[[KOD sanal_olcum.cpp 1 31 cpp]]

[[KOD sanal_olcum.cpp 32 52 cpp]]

[[KOD sanal_olcum.cpp 53 86 cpp]]

Programı tek bir girdi boyutuyla çalıştırdığımızda şu çıktıyı aldık. Bu, bir çalıştırmanın ham sonucudur; makinedeki o andaki yük sonucu değiştirir, bu yüzden aşağıdaki tabloda medyanları kullanacağız.

[[TERM sanal_olcum]]

Medyan için aynı programı beş kez çalıştıran ve her `n` için medyanı CSV'ye yazan betik aşağıdadır. Bu betik, WSL içinde `sanal_olcum` derlendikten sonra çalıştırılır.

[[KOD medyan.py 1 28 python]]

[[TABLO sanal]]

Tablo, iki sonucu açıkça ortaya koyuyor. Birincisi, tek türde (tahmin edilebilir dal ve hedef) sanal çağrı etiketli dallı sürümden yaklaşık üç kat yavaş: `n = 2^20` için eleman başına yaklaşık 2,7 ns'ye karşı 0,9 ns. İkincisi, karışık dağılımda fark küçülür (yaklaşık 4,7 ns'ye karşı 3,0 ns). Bu, bizim yorumumuzdur ve ölçmedik; karışık dağılımda hem dal hem dolaylı hedef tahmini bozulduğu için iki yöntemin de ek yükü artar, dolayısıyla oran küçülür (genel mimari bilgi; `perf` ile doğrulamadık). Ayrıca bu bir mikro kıyastır: her elemanın işi yalnızca bir çarpmadan ibarettir. Gerçek bir programda çağrının gövdesi ağırlaştıkça, çağrı ek yükünün toplam süredeki payı düşer. Derleyici, tür kesin biliniyorsa sanal çağrıyı doğrudan çağrıya çevirebilir (devirtualization); bu yüzden burada gördüğün maliyet, her durumda geçerli bir üst sınır değildir.

![Şekil 20.10: Sanal çağrı maliyeti. Log-log eksende, n arttıkça iki yöntemin süresi de doğrusal büyüyor; sabit fark, eleman başına ek yüktür.](gorseller/b20_sanal_olcum.png)

### Gömülü dünyada OOP: ne alıyorsun, ne ödüyorsun?

Gömülü sistemde bu maliyetler sonuçlarıyla birlikte düşünülmelidir. Her nesne bir tablo işaretçisi taşır; sanal fonksiyonu olan her sınıf için derleyici bir tablo üretir. Her sanal çağrı dolaylı bir atlamadır ve önbellek davranışını etkileyebilir. Dinamik bellek ayırma (`new`) ise zamanlaması belirsiz bir işlemdir ve bellek parçalanması riski taşır. Bu yüzden birçok gerçek zamanlı ve yüksek güvenilirlikli kodlama standardı bu öğeleri kısıtlar.

Örnek olarak JSF AV C++ kodlama standardını (uçuş yazılımı için bir kural seti) anabiliriz. Bu standardın dinamik bellek ayırmayı başlatmadan sonra yasakladığını ve sanal fonksiyon kullanımını kısıtladığını genel bilgi olarak biliyoruz. Ancak kural numaralarını ve metnini bu yazıda doğrulayamadık; bu nedenle ayrıntıya girmiyoruz, sadece yönü not ediyoruz.

Mert'in MertOS'taki klavye sürücüsü, bu dengenin küçük bir örneğidir. Sürücü kaydı bir işlev işaretçisi tablosuyla yapılır (Bölüm 2.10'daki callback deseni). Bu tasarım sanal fonksiyon kullanmadan, C'de de C++'ta da aynı maliyetle çalışır. Aynı arayüzü sınıf hiyerarşisi olarak yazmak ise daha güzel görünür ama vptr ve dolaylı çağrı maliyetini getirir. Hangi tercihin doğru olduğu, çalıştığın sistemin kısıtlarına bağlıdır; bunu tahmin etme, ölç.
## Çözümlü Örnekler

Bu bölümdeki dört örnek ★'dan ★★★'e doğru ilerler. Her örnekte Bölüm 5'teki altı adımı izleyeceğiz. Doğrulama adımında bir elle iz tablosu kullanacağız ve yazdığımız programın çıktısıyla karşılaştıracağız.

### Örnek 1 (★): Kesir'de değişmezi koruyan kurucu

**Problem:** `Kesir(6, -4)` kurucusunun ürettiği nesnenin `pay` ve `payda` değerlerini bul. Sonra `Kesir(0, 5)` nesnesinin ve `Kesir(1, 2) + Kesir(1, 3)` toplamının değerlerini belirle. Değişmez hangi noktada korunuyor?

**Adım 1 — Anla.** Girdi iki tamsayıdır: pay `6`, payda `-4`. Çıktı, nesnenin iç durumudur. Değişmez iki kuraldır: payda sıfırdan büyük olmalı ve pay ile paydanın en büyük ortak böleni 1 olmalı. Kenar durum: payda `0` ise kurucu istisna fırlatır.

**Adım 2 — Örnekle.** `6/-4` sayısı `-6/4` ile aynıdır, o da `-3/2` ile aynıdır. Yani beklenen son durum `pay = -3`, `payda = 2`'dir. `Kesir(0, 5)` ise `0/1` olmalıdır, çünkü `0/5 = 0`.

**Adım 3 — Kaba çöz.** Her kurucu çağrısında şunları yapabiliriz: önce işareti paydaya taşımak, sonra ortak böleni bulup iki değeri de bölmek. Kaba yöntem bu adımları her işlemde ayrı ayrı tekrarlar; sonuç doğru olur, ama kural her yerde yeniden yazılır.

**Adım 4 — Örüntü.** Sadeleştirme iki bağımsız adımdır: işaret düzeltme ve ortak bölen. Ortak bölen fonksiyonu `gcd(0, q) = q` özelliğiyle sıfır payı da kapsar: `0/5`, `5/5 = 1` ile bölündüğünde `0/1`'e iner. Bu iki adım tek bir `normalize` fonksiyonunda toplanır ve yalnızca kurucuda çağrılır.

**Adım 5 — İyileştir.** Kurucu `normalize()` çağırdığı için, her `Kesir` nesnesi kuruluşunda değişmezi sağlar. `+` ve `*` operatörleri yeni bir `Kesir` döndürür ve bu döndürme aynı kurucudan geçer; bu yüzden işlemler de değişmezi bozamaz. Bir uyarı: payda çarpımları büyüyebilir ve `long` taşabilir. Taşma `long` için işaretli tamsayı taşması, yani tanımsız davranıştır (Bölüm 2). Bu sorunu Ek Alıştırma 10'da ele alacağız.

**Adım 6 — Doğrula.** `6/-4` girdisinin iz tablosu:

| Adım | pay | payda | Ne yapıldı |
|---|---|---|---|
| Başlangıç | 6 | -4 | Kurucu girdisi |
| 1 | 6 | -4 | payda < 0: işaretler çevrildi |
| 2 | -6 | 4 | gcd(\|-6\|, 4) = 2 hesaplandı |
| 3 | -3 | 2 | İkisi de 2'ye bölündü |
| Son | -3 | 2 | payda > 0, gcd = 1: değişmez sağlandı |

Yazdığımız program `6/-4 -> -3/2` çıktısını verdi ve tabloyla birebir eşleşti. `Kesir(0, 5)` için Python sürümü `Kesir(0, 1)` döndürdü; bu da `gcd(0, 5) = 5` ile sıfır payın `0/1`'e indiğini doğruluyor. 100000 rastgele işlemde değişmez hiçbir kez bozulmadı.

**Bunu AI'sız yazabilir misin?** `Kesir` sınıfına çıkarma (`-`) ve bölme (`/`) ekle. Bölme işleminde payda sıfır kontrolünü nerede yapacağını, işaret düzeltmesinin hangi adımda gerektiğini gerekçelendir.

### Örnek 2 (★★): Şekil hiyerarşisinde alan toplamı

**Problem:** Yarıçapı 2 olan bir daire ile 3 × 4 bir dikdörtgenin alanlarını topla. Döngüdeki her çağrı hangi fonksiyona gider? Bu işlemi elle vtable'da ve C++ sanal fonksiyonlarında izle.

**Adım 1 — Anla.** Girdi, iki şeklin bir `Sekil*` dizisidir. Çıktı, toplam alan ve her şeklin `yazdir` çıktısıdır. Kural: çağrının hedefi, dizinin elemanının gerçek türüne göre seçilir; dizinin türüne göre değil.

**Adım 2 — Örnekle.** Daire için alan `pi · r² = 3,14159 · 4 = 12,566`'dır. Dikdörtgen için `3 · 4 = 12`. Toplam `24,566` olmalıdır; çıktıda da `toplam alan = 24.566` görüldü.

**Adım 3 — Kaba çöz.** Her elemanı dolaşır, yazdırır ve alanı toplarız. Hangi fonksiyonun çağrılacağını bilmek için bir `if` zinciri yazabilirdik: `if (tur == DAIRE)`. Bu zincir, yeni bir şekil eklendiğinde her yerde değiştirilmesi gerektiği anlamına gelir.

**Adım 4 — Örüntü.** Çağrı, elemanın tablo işaretçisinden (vptr ya da C'deki `vt`) fonksiyon adresini okuyarak yapılır. Tablo türe özgüdür; bu nedenle dizinin tipi `Sekil*` olsa bile doğru fonksiyon seçilir.

**Adım 5 — İyileştir.** Döngü, alanı her elemanda yalnızca bir kez hesaplar. Alan hesabı pahalıysa sonucu bir kez hesaplayıp saklamak daha iyidir; ama bu, sınıf tasarımını bozmadan yapılmalıdır, yani arayüze yeni bir önbellek alanı eklemek yerine, türetilmiş sınıfta bir üye tutmak gibi.

**Adım 6 — Doğrula.** İz tablosu:

| i | Gerçek tür | `yazdir` çıktısı | Alan (hesap) | Toplam (sonra) |
|---|---|---|---|---|
| 0 | Daire (r = 2) | `Daire r=2.0` | 3,14159 · 2 · 2 = 12,566 | 12,566 |
| 1 | Dikdörtgen (3 × 4) | `Dikdortgen 3.0x4.0` | 3 · 4 = 12 | 24,566 |

Tablo, programın çıktısıyla birebir uyuşuyor: önce daire, sonra dikdörtgen yazdırıldı ve toplam `24.566` oldu. C sürümünde `sizeof(Sekil)` 8, `sizeof(Daire)` 16 bayt çıktı; C++ sürümünde aynı boyutlar bulundu.

**Bunu AI'sız yazabilir misin?** Bir üçgen sınıfı ekle (alan: taban × yükseklik / 2). Önce C sürümünde vtable'a yeni bir girdi eklemeyi dene; sonra C++ sürümüne yeni bir sınıf olarak ekle. Hangisinde hangi dosyaların değişmesi gerektiğini karşılaştır.

### Örnek 3 (★★): Dizgi'de Rule of 5 ve sahiplik

**Problem:** `Dizgi` üzerinde `a("Mert")`, `b = a`, `a.ekle("OS")`, `c = std::move(a)` ve `c = b` işlemlerini yap. Her adımda `a`, `b` ve `c`'nin değerini ve hangi belleğin hangi nesneye ait olduğunu bul. Sızıntı ya da çift serbest bırakma olacak mı?

**Adım 1 — Anla.** Her `Dizgi` nesnesi tek bir `char` bloğunun sahibidir ve yıkıcısında o bloğu serbest bırakır. Girdi, yukarıdaki beş işlem; çıktı, her adımdan sonraki durum. Kural: her blok tam bir kez serbest bırakılmalı; taşınmış nesne boş bir blok göstermelidir.

**Adım 2 — Örnekle.** `a("Mert")` bir blok ayırır. `b = a` derin kopya yapar: `b` yeni bir blok alır ve `"Mert"` içeriğini kopyalar. `a.ekle("OS")` `a`'ya yeni bir blok ayırır (`MertOS`), eski blok serbest kalır. Beklenen son hâl: `a` boş, `b = "Mert"`, `c = "Mert"`.

**Adım 3 — Kaba çöz.** Her işlemi tek tek izleyip bellek bloklarını bir listede takip edebiliriz. Bu, çift serbest bırakmayı elle yakalamaya yarar, ama her adımda listeyi güncellemek hataya açıktır. ASan bu işi çalışma zamanında yapar; biz bunu doğrulama için kullanacağız.

**Adım 4 — Örüntü.** Kaynağı her el değiştirdiğinde, eski sahip ya kendi bloğunu serbest bırakır (kopya atama, `swap` sonrası geçici nesne) ya da bloğu devreder ve kendini boşaltır (taşıma). Taşınmış `a`nın `veri_` işaretçisi `nullptr`dir; `delete[] nullptr` güvenlidir.

**Adım 5 — İyileştir.** Kopya atama `copy-and-swap` ile yazıldığı için, bir istisna olsa bile nesne tutarlı kalır. Taşıma atama da `noexcept`tir; böylece `std::vector` gibi kapsayıcılar yeniden boyutlandırmada taşımayı tercih eder.

**Adım 6 — Doğrula.** Bu izi doğrulamak için her adımdan sonra durumu yazdıran küçük bir program yazdık. Program, Örnek 3'ün beş işlemini aynen uygular:

[[KOD dizgi_iz.cpp 1 22 cpp]]

[[TERM dizgi_iz]]

İz tablosu (program çıktısıyla karşılaştırıldı):

| Adım | İşlem | a | b | c | Bellek notu |
|---|---|---|---|---|---|
| 1 | `a("Mert")` | Mert | — | — | a bir blok sahibi |
| 2 | `b = a` (derin kopya) | Mert | Mert | — | İki ayrı blok |
| 3 | `a.ekle("OS")` | MertOS | Mert | — | a yeni blok aldı, eskisi serbest |
| 4 | `c = std::move(a)` | (boş) | Mert | MertOS | c bloğu çaldı, a `nullptr` |
| 5 | `c = b` (kopya atama) | (boş) | Mert | Mert | c'nin eski bloğu serbest, yeni blok |

Programın çıktısı: `a = "MertOS" (uzunluk 6)`, `b = "Mert" (uzunluk 4)`, `a = "" (uzunluk 0)`, `c = "MertOS" (uzunluk 6)`, `c = "Mert" (uzunluk 4)`. Tabloyla birebir uyuşuyor. Program `-fsanitize=address,undefined` ile çalıştırıldığında hiçbir hata raporlanmadı; yani sızıntı ve çift serbest bırakma yoktu.

**Bunu AI'sız yazabilir misin?** `Dizgi`'ye `operator+` ekle: iki dizgiyi birleştirip yeni bir `Dizgi` döndürsün. Bu operatörün kendi bloğunu nasıl ayırdığını ve sonucun taşınarak nasıl döndürüldüğünü ASan ile sınayarak doğrula.

### Örnek 4 (★★★): İstisna ve kaynak: el ile bırakma mı, RAII mi?

**Problem:** `islem_el(true)` çağrısı bir istisna fırlattığında `acik_kilit` sayacı kaç olur? Aynı işi RAII ile yazdığında sonuç nasıl değişir? İki sürüm arasındaki fark, yazılımda neyi değiştirir?

**Adım 1 — Anla.** Girdi `hatali = true`. Çıktı, sayaç ve istisnanın yakalandığı yer. Kural: her `al` işlemi için tam bir `birak` yapılmalı; istisna, kontrol akışını değiştirir ama bu kuralı ortadan kaldırmamalıdır.

**Adım 2 — Örnekle.** El ile sürümde `acik_kilit++` çalışır (`1`), sonra `throw` oradan çıkar. `acik_kilit--` satırı hiç çalışmaz. Beklenen sonuç: sayaç `1` kalır; bu bir sızıntıdır.

**Adım 3 — Kaba çöz.** Her çıkış yolunda elle `acik_kilit--` yazabilirdik. İki kaynak için ve iki çıkış noktası için bu, dört yerde tekrar eden bir koddur; birini unutmak kolaydır.

**Adım 4 — Örüntü.** Hata, çıkış yolu sayısıyla orantılıdır. Bırakma işini tek bir yere koyduğumuzda (yıkıcı), çıkış yolu ne olursa olsun bırakma çalışır. Bu, RAII'nin yapısal garantisidir.

**Adım 5 — İyileştir.** Kilidi bir `Kilit` sınıfına koyduk; kurucu alır, yıkıcı bırakır. Kopyalamayı yasakladık ki iki kez bırakma olmasın. Artık `islem` fonksiyonunda bırakma satırı yok.

**Adım 6 — Doğrula.** Her iki sürümü de çalıştırıp sayacı yazdırdık. El ile sürüm için:

[[KOD el_ile.cpp 1 21 cpp]]

[[TERM el_ile]]

El ile sürümün iz tablosu:

| Adım | Kod | `acik_kilit` | Olay |
|---|---|---|---|
| 1 | `acik_kilit++` | 1 | Kilit alındı |
| 2 | `if (hatali) throw` | 1 | İstisna, fonksiyondan çıkış |
| 3 | `acik_kilit--` | 1 | Çalışmadı: bırakma atlandı |
| 4 | `catch` | 1 | `yakalandi: hata` |
| Son | | 1 | `acik kilit = 1`: sızıntı |

RAII sürümünün iz tablosu (istisnalı yol):

| Adım | Olay | Açık kilit |
|---|---|---|
| 1 | `Kilit a` kuruldu: `al kilit-A` | 1 |
| 2 | `Dosya d` açıldı | 1 |
| 3 | `Kilit b` kuruldu: `al kilit-B` | 2 |
| 4 | `throw` | 2 |
| 5 | `~Kilit b`: `birak kilit-B` | 1 |
| 6 | `~Dosya`: `kapat` | 1 |
| 7 | `~Kilit a`: `birak kilit-A` | 0 |
| Son | `catch`: `yakalandi: islem basarisiz` | 0 |

El ile sürüm `acik kilit = 1` yazdı; RAII sürümü `acik kilit = 0`. İki sonuç da tabloyla uyuşuyor. Yıkım sırası, kuruluşun tersidir: `kilit-B`, dosya, `kilit-A`.

**Bunu AI'sız yazabilir misin?** `el_ile.cpp` dosyasına ikinci bir kaynak ve bir `return` ekle; sonra sızıntıyı ASan ile göster. Ardından aynı işi RAII ile yeniden yaz ve çıktılar arasındaki farkı açıkla.

::: dikkat
Aşağıdaki iki projede AI yardımı kullanma. Kod tamamlama, sohbet tabanlı kod üretimi ve "hatayı düzelt" istekleri bu projelerin amacını boşa çıkarır. Yalnızca bu bölümün kodlarını, derleyici uyarılarını ve sanitizer raporlarını kullan. Her sonucu kendi testinle doğrula.
:::

## Kendin Yap Projeleri

### Proje 1 (★★): Elle vtable ile sürücü tablosu: C ve C++ karşılaştırması

**Amaç:** Bir işletim sistemi çekirdeğinde sürücü kaydının nasıl çalıştığını hem C'de elle vtable ile hem de C++'ta sanal fonksiyonlarla yazarak karşılaştırmak. Amaç, MertOS'taki klavye sürücüsü gibi bir yapının tabloyla ve sanal fonksiyonla nasıl çalıştığını kendin görmek.

**Yapılacak / Beklenen davranış:**

1. Bir `Surucu` arayüzü tanımla: `ac()`, `oku()` ve `kapat()` işlemleri olsun. C'de bu işlemler bir `SurucuVT` tablosunda, C++'ta saf sanal fonksiyonlarda olacak.
2. İki somut sürücü yaz: bir `KlavyeSurucusu` (sahte tuş kodları üretsin) ve bir `SeriSurucu` (sahte bayt akışı üretsin). İkisi de aynı arayüzü uygulasın.
3. Bir kayıt tablosu oluştur: sürücüleri bir dizide tut ve her birini `ac()`, sonra `oku()` ile dolaş, en sonunda `kapat()` çağır.
4. Her iki sürümde (C ve C++) aynı çıktıyı üret. `sizeof` ile nesne boyutlarını ve `size` komutu ile ikili dosya boyutlarını karşılaştır.
5. Kasıtlı bir hata ekle: C sürümünde bir tablo girdisini `NULL` bırak; C++ sürümünde bunun karşılığı nedir? Hangi sürüm bu hatayı derleme zamanında yakalar, hangisi çalışma zamanında?

**Önerilen yaklaşım (ipucu):** Tabloyu `static const` olarak tanımla. Her sürücü için bir kurucu fonksiyonu yaz; C sürümünde bu fonksiyon `vt` alanını ayarlar. C++ sürümünde, sınıfın kendi kurucusu yeterlidir. Derleyici uyarılarını `-Wall -Wextra` ile açık tut.

**Başarı kriterleri:**

- Her iki sürüm aynı çıktıyı üretir ve ASan + UBSan altında hata raporlamaz.
- Karşılaştırma tablosunda `sizeof(Surucu)`, `sizeof(KlavyeSurucusu)` ve ikili dosya boyutları yer alır; her farkın nedeni bir cümleyle açıklanmıştır.
- Kasıtlı hata için iki sürümün davranışı yazılmış ve hangi aşamada yakalandığı belirtilmiştir.

### Proje 2 (★★★): MertOS tarzı sürücü çerçevesi (C++)

**Amaç:** Bir çekirdek içi sürücü çerçevesini C++'ta yazmak. Soyut arayüz, birden çok somut sürücü, kayıt tablosu, kaynak yönetimi (RAII) ve sahiplik (`unique_ptr`) bu projede birlikte kullanılmalı.

**Yapılacak / Beklenen davranış:**

1. Sanal yıkıcılı bir `Surucu` soyut sınıfı yaz. Saf sanal `ac`, `oku`, `kapat` metotları olsun.
2. Bir RAII kaynak sarmalayıcısı yaz (ör. bir sahte donanım kanalı). Kurucuda "kanal açıldı", yıkıcıda "kanal kapatıldı" yazsın.
3. Üç somut sürücü yaz: `KlavyeSurucusu`, `SeriSurucu` ve `ZamanlayiciSurucu`. Her biri kendi kaynağını RAII sarmalayıcısıyla yönetsin.
4. Sürücüleri `std::vector<std::unique_ptr<Surucu>>` içinde kaydet. Kayıt sırasında aynı ada sahip iki sürücüyü reddet; ad için bölüm 20.6'daki `Dizgi` sınıfını kullan.
5. Bir sürücünün `ac()` sırasında istisna fırlatmasını simüle et; diğer sürücülerin doğru sırayla kapatıldığını ve kaynakların sızmadığını doğrula.
6. Python tarafında, aynı arayüzü `typing.Protocol` ile tanımlayıp bir sahte sürücüyle uyumluluğu sına.

**Önerilen yaklaşım (ipucu):** Kayıt tablosunu bir `std::vector` ile tut. Sürücüler boşaltılırken `vector`'ün yıkım sırasını (ilk eklenen ilk yıkılır) düşün; RAII sırası ile eşleşiyor mu? Kopyalamayı yasakla, sahipliği `unique_ptr` ile taşı.

**Başarı kriterleri:**

- Tüm kaynaklar kapatılır; `-fsanitize=address,undefined` ile çalıştırıldığında hiçbir hata raporlanmaz.
- Üç sürücünün de yıkım sırası, kuruluşun tersidir ve bu, çıktıda görülebilir.
- İstisna senaryosunda sızıntı yoktur ve kayıt tablosu tutarlı kalır.
- Python `Protocol` testi, eksik bir metot verildiğinde bunu açıkça raporlar.

## Ek Alıştırmalar

Aşağıdaki problemlerin cevapları verilmemiştir. Önce kâğıtta düşün, sonra kodla doğrula.

1. ★ Bir `Sayac` sınıfı yaz: `artir()` ve `deger()` metotları olsun. Kopya kurucuyu ve kopya atamayı `= delete` ile kapat. Bu sınıfta kopyanın neden anlamsız olduğunu cümleyle açıkla.
2. ★ C'de bir `struct Yigin` ile `push` ve `pop` yaz. Sonra `struct` içine fonksiyon işaretçileri koyarak elemanın türünü (`int` ya da `char`) seçilebilir yap. Bu yaklaşımın C++ şablonlarına göre sınırlarını yaz.
3. ★ Python'da `Kare` ve `Daire` sınıfları yaz; her biri `alan()` döndürsün. Alanlara göre `sorted` ile sırala. `__lt__` tanımlamadan bu neden hata verir? (Mülakat)
4. ★★ `Kare`'nin `Dikdortgen`'den türemesi mantıklı mı? `genislik_ayarla` metodu ekleyince kareyi bozan bir kullanım yaz. Bu durumu Liskov yerine koyma ilkesi açısından yorumla. (Mülakat)
5. ★★ Aynı sınıfın sanal ve sanal olmayan iki sürümünün `sizeof` değerlerini karşılaştır. Fark hangi durumda görünür, hangi durumda görünmez?
6. ★★ Python'da `__slots__` tanımlı bir sınıftan kalıtım aldığında alt sınıf `__dict__` ekler mi? Deneyle doğrula ve sonucu açıkla.
7. ★★ Bölüm 20.6'daki `Dizgi` sınıfının Rule of 0 sürümünü `std::unique_ptr<char[]>` ile yaz. Kopya kurucuyu nasıl sağlayacağını ve bu sürümün neden tek bir yıkıcı içermediğini açıkla. ASan ile sına.
8. ★★ Python'da bir sınıfın `__hash__` metodunu `return 0` yaparsan bir `set` ne yapar? Bölüm 9'daki çarpışma zinciri ile açıkla ve sürenin nasıl değişeceğini ölç. (Mülakat)
9. ★★ `friend` anahtar sözcüğü kapsüllemeyi nasıl zayıflatır? Bir örnekle göster ve bunu tasarım kokusu olarak ne zaman görmen gerektiğini yaz. (Mülakat)
10. ★★★ Kesir'de `operator+` çağrısında payda çarpımının `long` sınırını aşabileceğini göster. İşaretli taşmanın tanımsız davranış olduğunu (Bölüm 2) göz önüne alarak, sadeleştirmeyi toplamadan önce yapan bir sürüm yaz ve iki sürümü büyük değerlerle karşılaştır.
11. ★★★ Python'da `dataclass(frozen=True)` ile bir sınıf yaz ve `__post_init__` kullanarak değişmezi kurucuda sına. Bir alan geçersiz olduğunda hangi istisnanın fırlatıldığını test et.
12. ★★★ Sanal yıkıcısı olmayan bir `Taban` hiyerarşisinde `std::unique_ptr<Taban>` kullan. LeakSanitizer ne bildirir? `unique_ptr`'nin neden bu durumu kurtarmadığını açıkla. (Mülakat)

## Kod Okuma Egzersizi

Bu egzersizde gerçek bir açık kaynak kodu okuyacaksın: CPython 3.12.10'un `Lib/dataclasses.py` dosyası. Kaynağı `https://raw.githubusercontent.com/python/cpython/v3.12.10/Lib/dataclasses.py` adresinden indirdik. Dosya 1588 satır; SHA-256 özetinin ilk 16 hanesi `d242aea5fcf6408b`. Aşağıdaki kesitler `_create_fn` fonksiyonunu (satır 449–474) içerir; bu fonksiyon, `dataclass` tarafından üretilen `__init__` ve diğer metotların kaynak metnini oluşturur ve `exec` ile çalıştırır.

Aşağıda ilk kesit, fonksiyonun imzası ile yorum satırlarını ve metin oluşturma adımlarını gösterir.

[[KOD kaynak_cpython/dataclasses.py 449 466 python]]

Kesitte, kaynağın 467 ve 468. satırları (iki yorum satırı, sırasıyla 78 ve 76 karakter) sayfa genişliği nedeniyle çıkarıldı. Bunların dışında kalan hiçbir satırda değişiklik yapılmadı. Kesitin devamı şöyledir:

[[KOD kaynak_cpython/dataclasses.py 469 474 python]]

Bu fonksiyonun bir kardeşi olan `_field_assign` (satır 477–487) ise `frozen` alanlar için `object.__setattr__` ile atama üretir. Satırı kısa tutmak için kesitini burada vermedik; yalnızca `frozen` dalının yaptığını bu bölümdeki `py_uretim` çıktısında gördün.

**Sorular — cevaplamadan geçme:**

1. `_create_fn` gövdeyi `exec` ile çalıştırıyor, ama metni önce `def __create_fn__(...)` içine sarıyor. Bu sarmalayıcı neden gerekli? Yorum satırlarındaki "serbest değişkenler" (free variables) açıklamasını kendi kelimelerinle anlat.
2. `locals` sözlüğü `__create_fn__`'in parametreleri olarak geçiriliyor. Bu yöntemle `globals` sözlüğü değiştirilmeden hangi değerlere erişiliyor?
3. `return_type` parametresi `None` ya da `MISSING` olabiliyor. `return_annotation` değişkeninin hangi durumda `->__dataclass_return_type__` olduğunu kodda izleyerek yaz.
4. `frozen` dalı neden `object.__setattr__` kullanıyor? Bu dal olmasaydı `frozen=True` sınıfın `__init__`'i nasıl davranırdı? Bu bölümdeki `py_uretim` çıktısıyla karşılaştır.
5. `exec` ile kod üretmenin esnekliği ve sakıncası nedir? Hata ayıklama, hata mesajları ve performans açısından üretilmiş koda bakmadan bir sınıfın doğru olduğunu nasıl doğrularsın?
6. (Mülakat) Sınıfın alan sayısı çok arttığında `__init__` gövdesi hangi sorunları yaratabilir? Üretilmiş kodun doğruluğunu bir test yazarak nasıl sınarsın?

## Bölüm Özeti

- OOP'nin temel üçlüsü kapsülleme, kalıtım ve çok biçimliliktir; ama bir tasarımın kalitesi, bu araçları hangi ilkelerle kullandığına bağlıdır (Bölüm 21).
- C'de bir `struct` ile fonksiyon işaretçisi tablosu (vtable) kurarak OOP'nin ilk hâlini elle yapabilirsin. C++ bu düzeni derleyiciye yaptırır; Python ise her çağrıyı çalışma zamanında çözer.
- RAII, kaynağı nesnenin ömrüne bağlar: kurucuda edin, yıkıcıda bırak. Python'da bunun karşılığı `with` ifadesidir; `__del__`'e güvenilmez.
- Değişmez (invariant), kapsülleme ile korunur. Kurucu kuralı kurar, işlemler kuralı bozmadan sonuç üretir. Python'da bu bir anlaşmadır; C++'ta derleyici erişimi denetler.
- Bir sınıf kaynak sahibi ise Rule of 5'i eksiksiz uygular; değilse Rule of 0 ile kaynağı bir sınıfa devreder. Sığ kopya, çift serbest bırakmanın en yaygın nedenidir.
- Sanal fonksiyon içeren bir taban sınıfın yıkıcısı sanal olmalıdır; aksi hâlde silme tanımsız davranıştır ve sızıntıya yol açar. Değerle alınan çok biçimli nesne dilimlenir.
- Python'da MRO C3 algoritmasıyla hesaplanır; `super()` çağrıyı MRO'da bir sonraki sınıfa iletir.
- Kalıtım, is-a ilişkisi gerçekten varsa kullanılır; yalnızca kod paylaşmak için yapılan kalıtım, kırılgan taban sınıf problemine yol açar. Bileşim çoğu zaman daha güvenlidir.
- Eşitlik ve hash sözleşmesi birlikte korunmalıdır; karma tablosunda kullanılan nesnelerin hash alanları değişmez olmalıdır.
- Sanal çağrı, nesne başına bir tablo işaretçisi ve çağrı başına dolaylı atlama maliyeti getirir. Bu maliyet, gömülü ve yüksek hızlı sistemlerde ölçülerek değerlendirilmelidir.

**Sonraki bölümde:** Bölüm 21, SOLID ilkelerini ele alıyor. Bu bölümde gördüğümüz Kare–Dikdörtgen sorusu, kırılgan taban sınıf ve sürücü arayüzü örnekleri, orada tek sorumluluk, açık-kapalı, Liskov, arayüz ayrımı ve bağımlılığın tersine çevrilmesi ilkelerine dönüşecek. Tasarım kalıpları ise Bölüm 22'de (Strategy, Adapter ve Command dahil) işlenecek.

::: mulakat
Aşağıdaki sorular cevapsız bırakılmıştır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. C++'ta `class` ile `struct` arasındaki fark nedir? Python'daki sınıfla C'deki `struct` arasındaki benzerlik nerede biter?
2. Sanal yıkıcı neden gereklidir? Bir taban işaretçisiyle sanal olmayan yıkıcıya sahip bir nesneyi silmek ne üretir ve bunu nasıl tespit edersin?
3. Rule of 3, Rule of 5 ve Rule of 0 nedir? Bir `Dizgi` sınıfında hangi üyeleri ve neden yazarsın?
4. Sığ kopya ile derin kopya arasındaki fark nedir? Hangi durumda sığ kopya bilinçli bir tercih olabilir?
5. Nesne dilimleme neden tehlikelidir? Değerle geçirilen bir türetilmiş nesnenin neyini kaybettiğini bir örnekle anlat.
6. Python'da `__eq__` tanımladığında `__hash__` neden `None` olur? Eşit ama farklı hash değerine sahip iki nesne bir kümede olursa ne olur?
7. Kalıtım yerine bileşimi ne zaman tercih etmelisin? Kırılgan taban sınıf problemini bir örnekle anlat.
8. Bir sanal fonksiyon çağrısının maliyetini nasıl ölçersin? Ölçümde hangi tuzaklar vardır ve Bölüm 12'deki ölçüm disiplini bunlara nasıl karşılık verir?
:::
