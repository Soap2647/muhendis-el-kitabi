%% kisim_no: V
%% kisim_ad: OOP & Yazılım Tasarımı
%% bolum_no: 23
%% baslik: Clean Code

## Giriş: Kodu bir kez yazarsın, çok kez okursun

Bir programı yazarken en çok kendi zihninle konuşursun. Hangi değişkenin ne tuttuğunu, hangi koşulun neden orada olduğunu aklında taşırsın. Bir hafta sonra aynı dosyaya döndüğünde bu bilginin büyük kısmı yoktur. Yazılım mühendisliğinde kodun büyük bölümü yazıldıktan sonra okunarak geçer: bir hatayı bulmak için, bir özelliği eklemek için, bir inceleme (code review) sırasında. "Kodu bir kez yazar, onlarca kez okuruz" cümlesi yaygın bir gözlemdir; kesin bir oran olarak almıyoruz, genel bilgi olarak geçiyor. Ama yönü açıktır: yazmak tek seferlik bir iştir, okumak tekrarlanan bir iştir.

Bu bölümde "temiz kod" (clean code) terimini tek bir çalışma tanımıyla kullanacağız: **okuyan birinin yanlış anlamasını en aza indiren, değiştirmesi güvenli kod.** Bu tanım estetik bir tercih değil; her maddesi ölçülebilir bir sonuca bağlanabilir. Ad kötüyse okur bir şeyi yanlış anlar. Fonksiyon uzunsa okur hangi satırın neyi bozabileceğini kestiremez. Yorum eskiyse okur, kodun söylediğine değil yorumun söylediğine güvenir.

Bölüm 6'da hata ayıklamayı ve savunmacı programlamayı gördük: erken patla, varsayımlarını `assert` ile yaz, uyarıları aç. Burada aynı zihniyeti kodun kendisine uyguluyoruz. SOLID ilkelerini (tek sorumluluk gibi) Bölüm 21'de, tasarım kalıplarını Bölüm 22'de anlattık; burada onları tekrar etmeyeceğiz, kod düzeyindeki zanaata odaklanacağız. Test yazmanın kendisi Bölüm 39'un konusu; biz burada testi yalnızca bir refactoring güvenlik ağı olarak kullanacağız. Git iş akışı Bölüm 38'de.

Savunma sanayiinde okunabilirlik bir lüks değil, gereksinimdir. Bir uçuş kontrol yazılımı yıllarca bakımdan geçer, farklı ekiplerce değiştirilir ve bir sertifikasyon denetçisi kodu satır satır okur. Bu yüzden MISRA C, CERT C ve JSF AV C++ gibi kodlama standartları hataya yol açan kalıpları yasaklamaya çalışır. Bölüm 23.10'da bu standartların neyi istediğini ve kod incelemesinin nasıl yapıldığını göreceğiz.

Mert'in projeleri bu bölüm için doğal bir laboratuvar. MertOS'un çekirdek kodunda hata yolları ve kaynak temizliği her yerde; EV Dashboard'daki sensör ayrıştırıcısı büyüdükçe okunamaz hale gelme riski taşır. Bölümün sonunda gerçek bir C modülünü bu araçlarla temizleyeceksin.

::: not
Bu bölümdeki her programı çalıştırdık. Python kodları Python 3.12.10 ile çalıştı; rastgele girdiler `random.Random(42)` tohumuyla üretildi, bu yüzden aynı kodu çalıştırdığında aynı sayıları görürsün. C kodları WSL içinde gcc 13.3 ile `-std=c11 -Wall -Wextra` uyarılarıyla derlendi; bellek hataları için `-fsanitize=address,undefined` kullanıldı. Windows tarafında clang-format 23.1.3, clang-tidy 23, ruff 0.17.1, black 26.10.1, mypy 2.4.0 ve radon 6.0.1 kullanıldı. cppcheck ve valgrind bu makinede kurulu değildi; WSL'de `sudo` şifre istediği için kuramadık. Bu yüzden statik analizde cppcheck yerine gcc'nin `-fanalyzer` modunu, bellek hatalarında valgrind yerine ASan ve LeakSanitizer'ı kullandık. Burada ölçtüğümüz şey kodun yapısal karmaşıklığıdır; çalışma süresi ölçmedik.
:::

## 23.1 Okunabilirlik neden bir mühendislik sorunu?

Kod okumak, yazmaktan daha zor bir zihinsel iştir. Okur kodu baştan sona çalıştırıp görmez; her satırda birkaç şeyi aklında tutar: hangi değişken ne, hangi koşul hangi dalda, hangi fonksiyon yan etki yapıyor. Aynı anda akılda tutulması gereken bu şeyler bilişsel yükün (cognitive load) parçasıdır. İnsan kısa süreli belleği aynı anda yalnızca birkaç öğeyi taşıyabilir. Linux çekirdeğinin kodlama belgesi de buna dikkat çeker: bir fonksiyonun yerel değişken sayısının 5-10'u geçmemesini, aksi halde fonksiyonun bölünmesini önerir. Bu sayının kesin olduğunu iddia etmiyoruz; ilke ise tartışmasızdır: aynı anda takip edilen şey azaldıkça hata yapma olasılığı düşer.

Bu bölümde "okunabilirliği" ölçülebilir parçalara ayıracağız:

- **Adlar:** değişken, fonksiyon ve tip adları bir niyet taşıyor mu?
- **Fonksiyon yapısı:** uzunluk, parametre sayısı, iç içe dallanma, yan etki.
- **Yorumlar:** yorumlar kodun söyleyemediği NEDEN'i mi anlatıyor, yoksa kodun tekrarını mı yapıyor?
- **Biçim ve araçlar:** tutarlı biçim, derleyici ve statik analiz uyarıları.
- **Hata yolları:** hatalar nerede yakalanıyor, kaynaklar nerede serbest bırakılıyor?

Her başlıkta aynı yolu izleyeceğiz: önce kötü bir örnek, sonra iyi bir örnek, mümkünse de aracımızla ölçüm. Ölçüm, "bu daha temiz" iddiasını "bu fonksiyonun döngüsel karmaşıklığı 11'den 5'e düştü" gibi denetlenebilir bir cümleye çevirmeyi sağlar. Bölüm 23.9'da bu ölçümü kendi yazdığımız küçük bir araçla yapacağız.

Okuma ile yazma oranına dair "kod on kez okunur" gibi sayısal iddialar da yaygındır. Bunları genel bilgi olarak işaretliyoruz; bu bölümde ölçülmüş bir değer olarak kullanmıyoruz.

## 23.2 Adlandırma: ad niyeti taşımalı

Bir adın iki işi vardır: değişkense neyi tuttuğunu, fonksiyonsa ne yaptığını söylemek; ayrıca neden orada olduğunu ima etmek. Aşağıdaki şekil aynı işlevi iki farklı adla gösteriyor. Kötü adda okur üç soruyu kendisi çözmek zorunda kalır; iyi adda sorular zaten cevaplanmıştır.

![Şekil 23.1: f(k, e, m) adının okura bıraktığı iş ile kritik_ozet(...) adının bıraktığı iş arasındaki fark.](gorseller/b23_adlandirma_zihin.png)

Dört kural bu farkı üretir.

**Kural 1: Ad niyeti söylesin.** `d` yerine `gecikme_ms`, `flag` yerine `alarm_aktif_mi` yaz. Linux çekirdeğinin kodlama belgesi bu konuda açık: yerel değişkenler kısa olabilir (bir döngü sayacı `i` olabilir), ama global değişkenler ve fonksiyonlar açıklayıcı olmalıdır. Belge, aktif kullanıcıları sayan bir fonksiyona `cntusr()` değil, `count_active_users()` adının verilmesini örnek gösterir. Kısa adın meşru olduğu yer, kapsamın küçük olduğu yerdir.

**Kural 2: Ad büyüklüğü kapsamla orantılı olsun.** Üç satırlık bir döngüde `i` ya da `j` sorun değildir; herkes ne olduğunu bilir. Modül düzeyinde yaşayan bir sabit ya da yüzlerce satır boyunca görünen bir değişken için aynı kısalık, okuru her kullanımda tanımı aramaya zorlar. Kural şudur: kapsam büyüdükçe ad uzar.

**Kural 3: Boolean adları bir soru gibi okunsun.** `aktif`, `hazir`, `gecerli_mi`, `bos_mu` gibi adlar bir koşulda doğal okunur. `durum` ya da `kontrol` gibi adlar boolean mı, enum mı, hata kodu mu olduğunu söylemez. Bu belirsizlik gerçek hatalara yol açar. Linux belgesi bunu bir kuralla çözer: eylem adı taşıyan fonksiyon hata kodu döndürür (`add_work()` gibi; başarıda 0, hatada negatif bir kod), yüklem adı taşıyan fonksiyon ise "başarılı mı" boolean'ı döndürür (`pci_dev_present()` gibi; bulunursa 1, bulunamazsa 0). Bu kuralı Bölüm 23.6'da hata yönetimiyle birlikte kullanacağız.

**Kural 4: Kısaltma tuzağına düşme.** `tmp`, `ptr`, `cnt`, `buf` gibi kısaltmalar yazarken kısa ve tanıdık gelir, ama ekipteki herkes aynı şeyi kastetmeyebilir. `tmp` bir geçici tampon mu, geçici dosya mı, geçici bir sayı mı? Kısaltmayı yalnızca ekipçe yerleşmiş olanlarda kullan (`i`, `n`, `len`, `buf`); yeni kısaltmalar icat etme.

### Dil kararı: Türkçe mi, İngilizce mi?

Bu sorunun cevabı bir zevk meselesi değil, bir ekip kararıdır. Bu bölümün örneklerinde Türkçe adları **ASCII** biçiminde kullandık (ç, ğ, ı, ş, ö, ü olmadan): `kayit`, `esik`, `alarm_karari`. İki nedeni var. Birincisi, C standardı taşınabilirlik açısından yalnızca ASCII tanımlayıcıları güvenli kabul eder; `ı` ya da `ş` içeren bir tanımlayıcı derleyiciye, editöre ve araçlara bağımlılık yaratır. İkincisi, grep, komut satırı ve yapılandırma dosyaları ASCII adlarla daha rahat çalışır. Python 3 Türkçe harfleri tanımlayıcı olarak kabul eder (PEP 3131), ama bu kabul kodu taşınabilir kılmaz.

Asıl kural tutarlılıktır. Türkçe ve İngilizce adları aynı kod tabanında karıştırmak en kötü seçenektir: yanında `kayitListesi` duran bir `user_list` gören okur, iki farklı kavram olup olmadığını merak eder ve boşuna arama yapar. Savunma sanayiinde ekipler genellikle İngilizce ad kullanır; nedeni, tek bir terim setinin, dışarıdan gelen kütüphanelerin ve standartların zaten İngilizce olmasıdır. Türkçe kullanmaya karar verirsen bunu yazılı bir ekip kuralı yap ve her yerde uygula. Bu bölümdeki örnekler Türkçe-ASCII'dir; bu bir tercih, zorunluluk değil.

## 23.3 Fonksiyonlar: küçük, tek iş, az yan etki

Fonksiyon, kodun birimidir. İyi bir fonksiyonu bir kez okuyup ne yaptığını anlayabiliyorsan, onu çağıran kişi içine bakmadan güvenle kullanabilir. Linux belgesi bunu tek cümleyle özetler: fonksiyonlar kısa olmalı ve tek bir şey yapmalıdır. "Kısa" ve "tek iş" soyut kalmasın diye dört somut ölçüt kullanacağız.

**Tek soyutlama seviyesi.** Bir fonksiyonun içindeki satırlar aynı soyutlama düzeyinde olmalıdır. Bir sensör okuma fonksiyonunda "veriyi oku, sonra doğrula" adımları ile "şu register'ın şu bitine yaz" ayrıntısı yan yana durmamalıdır. İlki bir kavramdır, ikincisi donanımın ayrıntısıdır. Ayrıntıyı ayrı bir fonksiyona taşıyınca üst fonksiyon kavramı anlatır ve okunur.

**Parametre sayısı.** Parametre sayısı, okurun aklında tutması gereken şeyi gösterir. Üç parametre çoğu zaman rahat okunur. Dört ve üzeri, özellikle aynı tipte olanlar (`int, int, int, int`) yanlış sırayla çağırmaya davetiye çıkarır. Çözüm, ilgili parametreleri bir yapıda toplamaktır; bunu Bölüm 23.8'de "Introduce Parameter Object" adıyla göreceğiz.

**Yan etki.** Ad, fonksiyonun ne değiştirdiğini de söylemelidir. `kuyruk.pop(0)` hem değer döndürür hem kuyruğu değiştirir. Bu yan etki, adından anlaşılmayan bir değişikliktir: okur `ilk = kuyruk.pop(0)` yazdığında kuyruğun değiştiğini bilir, ama bir `kontrol(kuyruk)` çağrısının içinde neyin değiştiğini kestiremez.

**Komut–sorgu ayrımı.** Bir fonksiyon ya bir şeyi **sorgular** (değer döndürür, durumu değiştirmez) ya da bir **komut** verir (durumu değiştirir, ya hiç değer döndürmez ya da yalnızca hata kodu döndürür). İkisini aynı fonksiyonda karıştırmak, çağıranın sorgu yaptığını sanıp yan etkiyi kaçırmasına yol açar. Aşağıdaki küçük program aynı kuyruk işlemini karışık ve ayrık biçimde yazıyor.

```python
# kavram.py: karisik ve ayrik komut-sorgu
def al_kotu(kuyruk):
    return kuyruk.pop(0)  # hem doner hem degistirir


def ilk(kuyruk):
    return kuyruk[0]  # sorgu: degistirmez


def cikar(kuyruk):
    del kuyruk[0]  # komut: degistirir, deger dondurmez


if __name__ == "__main__":
    k1 = [5, 7]
    print("kotu:", al_kotu(k1), k1)
    k2 = [5, 7]
    print("iyi :", ilk(k2), end=" ")
    cikar(k2)
    print(k2)
```

Programı çalıştırdığında şunu görürsün:

```term
$ python kavram.py
kotu: 5 [7]
iyi : 5 [7]
```

İki yazım da aynı sonucu verir; fark, ikinci yazımda her işlemin ne yaptığının adından okunmasıdır. Yan etkileri ayırmak, eşzamanlı kodda da işe yarar: bir değeri okuyup sonra ayrı bir adımda değiştirmek, iki iş parçacığının aynı anda aynı şeyi değiştirme riskini daha görünür hale getirir. Bunu Kısım XIII'te paralel programlamada ayrıntılı göreceksin.

**Koruma cümleleri (guard clauses).** İç içe `if` yapıları okurun zihninde bir yığın oluşturur: her açılan dalı kapatana kadar önceki koşulu da hatırlamak zorundadır. Koruma cümlesi, geçersiz durumu fonksiyonun başında yakalayıp hemen döndürür; geri kalan kod ana akışı düz bir biçimde izler. Aşağıdaki şekil bu dönüşümü gösteriyor; sayılar Örnek 2'de ölçtüğümüz koddan.

![Şekil 23.2: İç içe if yapısı (derinlik 6) ile koruma cümleleriyle düzleşmiş akış. Koşulların sayısı aynı, sırası korunmuş.](gorseller/b23_koruma_duzlestirme.png)

Dönüşümün tam kodunu ve doğrulamasını Örnek 2'de yapacağız. Burada tek bir kural bırakıyoruz: **koruma cümlelerini yazarken koşulların sırası davranışın parçasıdır.** Örnek 2'de bu sırayı bilerek değiştirdiğimizde test 20000 denemede 125 farklı sonuç buldu. Sıra, "hangi geçersizlik önce bildirilir" sorusunu belirler; bunu sadece okunabilirlik meselesi sanmak hatalıdır.

## 23.4 Yorumlar: NEDEN'i anlat, NE'yi kod anlatsın

Yorum, kodun söyleyemediğini söylemek için vardır. Kodun ne yaptığını zaten söyleyen yorum gereksizdir; kodla çelişen yorum ise zararlıdır. Kötü yorumların en tehlikelisi eskimiş yorumdur: kod değişmiş, yorum eski hâliyle kalmıştır ve okur yoruma güvenir.

Aşağıdaki örnekte yorum, gerilim alt sınırını 300 V olarak söylüyor; sabit ise 250 V. Hangisinin doğru olduğu koddan anlaşılamaz, ama okur yoruma güvenirse yanlış bir varsayım taşır.

```python
# Gerilim 300 V'un altina duserse kayit gecersiz sayilir.
GERILIM_ALT = 250.0
```

Bu tür uyumsuzluğu derleyici yakalamaz. Bu yüzden kural basittir: **kod değiştiğinde yorum da aynı değişiklikte güncellenmeli.** Mümkünse yorumun yerine adı kullan. `GERILIM_ALT_V = 250.0` gibi bir ad, bir yorumdan daha az yalan söyler; çünkü ad, sabitin kullanıldığı her yerde okunur.

Yorumun asıl değeri NEDEN sorusunu cevaplamasıdır: bu sabit neden bu değerde, bu sıra neden seçildi, hangi kısıt bu kararı zorladı. Örneğin "sıcaklık sensörü yüksek frekanslı gürültü üretiyor; bu yüzden alarm için tek ölçüm değil ardışık ölçümler kullanılıyor" gibi bir yorum, kodun bilmediği bir bağlamı taşır. Bu tür yorumlar en değerli yorumlardır, çünkü bağlam başka hiçbir yerde yazılı değildir.

Fonksiyonların belgelenmesi için standart biçimler vardır. Python'da docstring, C'de Doxygen tarzı yorumlar kullanılır. Docstring, fonksiyonun sözleşmesini (girdiler, dönüş değeri, hata durumları) anlatır:

```python
def kritik_ozet(ham_kayitlar, esik, mod):
    """Eşik üstü kritik kayıtlardan özet üretir.

    mod "ortalama" ise skorların ortalamasını, "liste" ise
    (zaman, skor) çiftlerini döndürür. Kritik kayıt yoksa None.
    Bilinmeyen mod için ValueError fırlatır.
    """
```

C tarafında Doxygen etiketleri (`@param`, `@return`) aynı işi görür; bu etiketlerden HTML belgesi üretmek için `doxygen` aracı kullanılır. Bu bölümde doxygen'i çalıştırmadık; burada amaç biçimi tanımaktır.
## 23.5 Araçlar: biçimlendirme ve statik analiz

İnsanlar biçim konusunda uzun uzun tartışabilir; tartışılacak bir şey kalmamalıdır. Biçimlendirme aracı boşluk, girinti ve parantez yerleşimini tek bir kurala bağlar. Statik analiz aracı ise kodu çalıştırmadan hatalı kalıpları bulur. İkisi de küçük bir kurulum bedeli karşılığında gelir ve kod incelemesinde insanın yapması gereken işi azaltır. Bu alt bölümde ikisini de gerçek dosyalar üzerinde çalıştırıyoruz.

### Biçimlendirme: clang-format ve black

Aşağıdaki C dosyası bilerek dağınık yazıldı: tek satırda birden çok ifade, tutarsız boşluklar, bazı yerlerde süslü parantez yok.

```c
#include <stdio.h>
#include <stdlib.h>
int olc(int *a,int n){int s=0;
for(int i=0;i<n;i++){ if(a[i]>0){s+=a[i];}else{ s-=a[i] ;} }
if(s>100){printf("buyuk %d\n",s);return 1;}
return 0;}
```

clang-format, ayarlarını bir `.clang-format` dosyasından okur. Bu bölümde Linux çekirdeği stiline yakın bir ayar kullandık: girinti 8 ve sekme, açılış parantezi kontrol satırının sonunda, fonksiyon parantezi kendi satırında.

```term
$ cat .clang-format
BasedOnStyle: LLVM
IndentWidth: 8
UseTab: Always
BreakBeforeBraces: Linux
ColumnLimit: 80
$ clang-format kotu_bicim.c
```

Çıktı aşağıda. Sekmeler okunabilirlik için 4 boşlukla gösterildi; gerçek dosyada sekmedir.

```c
#include <stdio.h>
#include <stdlib.h>
int olc(int *a, int n)
{
    int s = 0;
    for (int i = 0; i < n; i++) {
        if (a[i] > 0) {
            s += a[i];
        } else {
            s -= a[i];
        }
    }
    if (s > 100) {
        printf("buyuk %d\n", s);
        return 1;
    }
    return 0;
}
```

Dikkat edilecek nokta, aracın yalnızca biçimi değiştirdiği, mantığa dokunmadığıdır. Biçim aracı bir "temizlik" değil, bir "eşitleme"dir: her geliştirici aynı kuralla yazmış gibi görünür ve incelemede tartışılacak biçim sorusu kalmaz. Python tarafında aynı işi `black` ya da `ruff format` yapar. Aynı dağınıklığın Python karşılığını `black` ile biçimlendirdik (`black dosya.py` komutu dosyayı yerinde değiştirir):

```python
def ort( xs ,ilk = 0 ):
    return sum(xs)/len(xs)  if xs  else ilk
AD=  {"a":1,
  "b":2}
```

Sonuç:

```python
def ort(xs, ilk=0):
    return sum(xs) / len(xs) if xs else ilk


AD = {"a": 1, "b": 2}
```

Biçim araçlarında bir uyarı: aracın biçimi değiştirmesi, dosyanın anlamını değiştirmez ama diff'i büyütür. Bu yüzden biçimlendirmeyi tek bir ayrı commit'te yap; mantık değişikliğiyle karıştırma. Bu, Bölüm 38'de git iş akışında yeniden karşımıza çıkacak.

### Derleyici uyarıları: bedava hata avcısı

Derleyicinin uyarıları, bir hata ayıklayıcının bulacağı şeyleri çalıştırmadan söyler. Aşağıdaki C dosyasında dört ayrı kalıp var. Her biri gerçek bir hataya yol açabilir.

```c
#include <stdio.h>
#include <stddef.h>
#include <stdint.h>

int toplam_say(const int *dizi, size_t n)
{
    int toplam = 0;
    for (int i = 0; i < n; i++)
        toplam += dizi[i];
    return toplam;
}

void yuzde_yaz(double oran)
{
    int yuzde = oran * 100;
    printf("%d\n", yuzde);
}

int dogrula(int deger)
{
    int sonuc = 0;
    if (deger > 0) {
        int sonuc = deger * 2;   /* golgeleme */
        (void)sonuc;
    }
    return sonuc;
}

int main(void)
{
    uint8_t sayac = 300;          /* tasma */
    int ilk;
    if (sayac > 10)
        ilk = 1;
    printf("%d %d\n", ilk, dogrula(3));
    yuzde_yaz(0.256);
    return toplam_say(NULL, 0) + sayac;
}
```

Önce yalnızca `-Wall -Wextra` ile derleyelim. Komutu WSL içinde çalıştırıyoruz; bu bölümdeki C komutlarının hepsi aynı ortamda:

```term
$ gcc -std=c11 -O2 -Wall -Wextra -c uyari.c
uyari.c:8:23: warning: comparison of integer expressions
  of different signedness: 'int' and 'size_t' [-Wsign-compare]
uyari.c:31:21: warning: unsigned conversion from 'int' to
  'uint8_t' changes value from '300' to '44' [-Woverflow]
```

İki uyarı görünüyor. Şimdi katı bayrakları ekleyelim: `-Wshadow` iç içe tanımlanan aynı isimli değişkenleri, `-Wconversion` sessiz tip dönüşümlerini yakalar:

```term
$ gcc -std=c11 -O2 -Wall -Wextra -Wshadow \
    -Wconversion -c uyari.c
uyari.c:8:23: warning: comparison of integer expressions
  of different signedness: 'int' and 'size_t' [-Wsign-compare]
uyari.c:15:17: warning: conversion from 'double' to 'int'
  may change value [-Wfloat-conversion]
uyari.c:23:13: warning: declaration of 'sonuc' shadows
  a previous local [-Wshadow]
uyari.c:31:21: warning: unsigned conversion from 'int' to
  'uint8_t' changes value from '300' to '44' [-Woverflow]
```

Uyarı metinleri terminalde çok uzun olduğu için satır sonlarından bölündü; içerikleri değiştirilmedi.

Dört uyarının her biri bir hataya işaret eder. Şimdi programı çalıştırıp bu hataların sonucunu görelim:

```term
$ gcc -std=c11 -O0 -g -fsanitize=address,undefined \
    -w -o uyari_asan uyari.c && ./uyari_asan
1 0
25
```

Üç gözlem:

- `dogrula(3)` 6 döndürmesi gerekirken 0 döndürdü. İç bloktaki `int sonuc` dış `sonuc`'u gölgeledi; `return sonuc` dış değişkeni okudu. Bu, `-Wshadow` uyarısının tam olarak yakaladığı türden bir hatadır ve test edilmesi kolay değildir, çünkü çoğu zaman sonuç "makul görünür".
- `yuzde_yaz(0.256)` 26 değil 25 yazdırdı. `0.256 * 100` değeri 25.6'dır ve `int`'e atanırken kesildi (yuvarlanmadı). Bu bir sessiz kesmedir; `-Wfloat-conversion` bunu gösterir.
- `uint8_t sayac = 300;` değeri 44'e indi (300 mod 256). Derleyici bunu sabit değerde bildiği için uyardı; değer dışarıdan gelseydi uyarı çıkmayabilirdi.

Ayrıca `-Wsign-compare` uyarısının arkasında gerçek bir risk var. `int i` ile `size_t n` karşılaştırıldığında `i` işaretsiz tipe çevrilir. Bu bellek bloğu büyüdüğünde, `n` `INT_MAX`'ı aşarsa `i` de taşar; işaretli tamsayıda taşma tanımsız davranıştır (UB). Tanımsız davranış, tipik olarak "yanlış sonuç" ya da "çökme" ile sonuçlanabilir, ama bunu garanti etmez: derleyici optimizasyonda döngüyü beklenmedik biçimlerde yeniden yazabilir. Doğru çözüm `i`'yi de `size_t` yapmak ya da `n`'yi uygun bir tipte almaktır.

::: ipucu
Derleyici uyarılarını `-Werror` ile hataya çevirmek, ekip olarak uyarı toleransını sıfırlamanın en basit yoludur. Ama önce uyarıların neden çıktığını anla; yoksa `-Wno-...` ile susturmaya başlarsın ve asıl hatayı kaçırırsın.
:::

### clang-tidy: kalıp tanıyan ikinci göz

Derleyici uyarıları tip ve sözdizimi odaklıdır. clang-tidy daha çok kalıp ve okunabilirlik kurallarını uygular; ayrıca clang'in statik analizörünün bellek kontrollerini çalıştırabilir. Aynı `uyari.c` üzerinde yalnızca `bugprone` ve `readability` kontrol gruplarını çalıştırdık ve çıktıdan ilgili satırları aldık:

```term
$ clang-tidy uyari.c -checks='bugprone-*,readability-*' -- -std=c11
uyari.c:15:17: warning: narrowing conversion from 'double' to
  'int' [bugprone-narrowing-conversions]
uyari.c:31:21: warning: implicit conversion from 'int' to
  'uint8_t' changes value from 300 to 44
  [clang-diagnostic-constant-conversion]
uyari.c:15:24: warning: 100 is a magic number; consider
  replacing it with a named constant [readability-magic-numbers]
```

Sihirli sayı uyarısına Bölüm 23.7'de geri döneceğiz. Bellek sızıntısı için clang-tidy'nin analizör kontrolleri gerçekten işe yarar. Bölüm 23.6'daki `kayit_oku` örneğini `clang-analyzer-*` kontrolleriyle çalıştırdığımızda şu uyarıları aldık (yol kırpılmıştır):

```term
ex3_eski.c:14:17: warning: Opened stream never closed.
  Potential resource leak [clang-analyzer-unix.Stream]
ex3_eski.c:21:17: warning: Potential leak of memory pointed
  to by 'tampon' [clang-analyzer-unix.Malloc]
```

Windows'ta çalıştırdığımız için clang-tidy, MSVC'ye özgü `fopen_s` önerisi gibi CRT uyarıları da üretti. Taşınabilir kod yazıyorsan bu uyarıları bilinçli olarak yok sayabilirsin; ama bunların kaynağını bilmek, uyarıyı gerçek sorundan ayırmanı sağlar.

### Python: ruff ve mypy

Python'da aynı işi `ruff` (hızlı linter) ve `mypy` (tip denetleyicisi) yapar. Aşağıdaki dosya bilerek kötü yazıldı: kullanılmayan importlar, değiştirilebilir varsayılan argüman, çıplak `except`, Python'da olmayan adlandırma.

```python
import os
import sys


def getUser(id, list=[]):
    for u in list:
        if u["id"] == id:
            return u
    return None


def ort(xs):
    try:
        return sum(xs) / len(xs)
    except:
        pass


def is_ok(x):
    if x == None:
        return False
    return True
```

`ruff` kurallarını (E, F, B, N, SIM) seçip çalıştırdığımızda:

```term
$ ruff check --select E,F,B,N,SIM --output-format concise kotu_py.py
kotu_py.py:1:8: F401 `os` imported but unused
kotu_py.py:2:8: F401 `sys` imported but unused
kotu_py.py:5:5: N802 Function name `getUser` should be lowercase
kotu_py.py:5:22: B006 Do not use mutable data structures
  for argument defaults
kotu_py.py:15:5: E722 Do not use bare `except`
kotu_py.py:20:5: SIM103 Return the condition `x != None` directly
kotu_py.py:20:13: E711 Comparison to `None` should be `cond is None`
Found 7 errors.
```

Bu çıktıda en tehlikeli olan `E722`'dir: çıplak `except:` her hatayı, klavye kesmesini (Ctrl+C) bile yakalar ve `pass` ile sessizce yutar. Bölüm 23.6'da bunun neden kötü olduğunu ayrıntılı göreceğiz. `B006`'daki değiştirilebilir varsayılan (`list=[]`) ise aynı listenin tüm çağrılar arasında paylaşılmasına yol açar; bu bir yan etki kaynağıdır.

Tip denetimi ise çalıştırmadan bir hatayı yakalar. Aşağıdaki dosyada `kullanici_bul` bir kullanıcı bulamazsa `None` döndürebilir; `selam` fonksiyonu bunu unutmuş:

```python
from typing import Optional


def kullanici_bul(kimlik: int) -> Optional[str]:
    isimler = {1: "Ayse", 2: "Mert"}
    return isimler.get(kimlik)


def selam(kimlik: int) -> str:
    isim = kullanici_bul(kimlik)
    return "Merhaba " + isim.upper()


def selam_guvenli(kimlik: int) -> str:
    isim = kullanici_bul(kimlik)
    if isim is None:
        return "Merhaba misafir"
    return "Merhaba " + isim.upper()
```

`mypy --strict` bu dosyayı şöyle raporlar:

```term
$ mypy --strict tip_ornek.py
tip_ornek.py:11: error: Item "None" of "str | None" has no
  attribute "upper"  [union-attr]
Found 1 error in 1 file (checked 1 source file)
```

Hata `selam` içinde, `isim.upper()` satırındadır; `selam_guvenli` ise `None` durumunu açıkça ele aldığı için temizdir. Bu, çalışma zamanında `AttributeError` olarak ortaya çıkacak bir hatanın, daha kodu çalıştırmadan yakalanmasıdır. Birçok ekip bu denetimi derleme aşamasının bir parçası yapar. Aynı disiplin, Kısım XIV ve XV'teki büyük ML kod tabanlarında tensör ve veri şekilleri için de geçerli olacak.

## 23.6 Hata yönetimi: yutma, kaynağı unutma, bağlam ver

Hata yönetimi, kodun en çok ihmal edilen kısmıdır. Mutlu yol (happy path) genellikle düzgün yazılır; hatalı yol ise son dakikada, bir şey patladıktan sonra eklenir. Oysa gerçek sistemlerde hata yolu, kodun önemli bir kısmıdır: dosya bulunamaz, bellek biter, sensör veri göndermez, ağ kopar. Bu alt bölümde dört dile özgü kalıbı ele alıyoruz ve sonunda ortak bir kural çıkarıyoruz.

### C: dönüş kodları ve sözleşme

C'de istisna (exception) yoktur; hata, dönüş değeriyle bildirilir. Bunun en yaygın biçimi, başarıda 0 ve hatada negatif bir hata kodu döndürmektir. Bu, Bölüm 23.2'deki adlandırma kuralıyla birlikte düşünülmelidir: eylem adlı fonksiyon hata kodu, yüklem adlı fonksiyon boolean döndürür.

Dönüş değerini yok saymak en sık görülen hatadır. `fclose(f)` çağrısının sonucunu kontrol etmemek, yazma sırasındaki bir hatayı (disk doldu gibi) gizler. Bölüm 6'daki "erken patla" ilkesi burada da geçerlidir: hata, oluştuğu yerde bildirilmeli ya da çağırana iletilmelidir; sessizce yutulmamalıdır.

### C: goto ile tek çıkış noktası

Bir fonksiyon birden çok yerden çıkıyorsa ve bu çıkışların her biri farklı kaynakları serbest bırakması gerekiyorsa, her çıkış yolunda temizlik kodunu tekrarlamak hata üretir. Bir yolda `free` unutulur, bir başkasında iki kez çağrılır. Linux çekirdeğinin kodlama belgesi, birden çok çıkışı olan ve ortak temizlik gerektiren fonksiyonlarda `goto` kullanmanın işe yaradığını söyler: çıkışlar tek bir etikette toplanır, temizlik orada bir kez yazılır. Belge etiket adları için de bir kural koyar: etiket, `goto`'nun ne yaptığını söylemelidir.

![Şekil 23.3: goto ile merkezi çıkış. Hata yolları, açık kalan kaynakları ters sırada kapatan etiketlere atlar.](gorseller/b23_goto_cikis.png)

Şekil iki kuralı gösterir. Birincisi, etiketler adlarıyla yapılacak işi söyler (`cik_tampon`, `cik_dosya`); `err1`, `err2` gibi numaralı adlar, çıkış yolları değiştiğinde yeniden numaralandırmayı gerektirir ve doğruluğu kontrol etmeyi zorlaştırır. İkincisi, kaynaklar edinildikleri sırayla ters sırada serbest bırakılır: önce tampon (sonra alındı), sonra dosya (önce alındı). Tam kod ve doğrulama Örnek 3'te; buradaki iskelet yalnızca mantığı gösterir.

Belge ayrıca tipik bir hatayı da tarif eder: tek bir hata etiketinin, bazı çıkış yollarında henüz ayrılmamış bir işaretçiyi serbest bırakmaya çalıştığı durum. Çözüm, etiketi iki parçaya bölmektir; her etiket yalnızca o noktaya kadar gerçekten ayrılmış kaynakları serbest bırakır. Bu tam olarak Örnek 3'te yaptığımız şeydir.

### C++: RAII ile kaynağı nesneye bağlamak

C++'ta aynı sorunun çözümü `goto` değil, RAII (Resource Acquisition Is Initialization, kaynak edinimi başlatmadır) kalıbıdır. Kuralı şudur: kaynak bir nesnenin kurucusunda alınır, yıkıcısında serbest bırakılır. Kapsam (scope) bittiğinde, normal dönüşte de istisnada da yıkıcı çalışır. Standart kütüphanedeki `std::unique_ptr` bu kalıbın hazır bir uygulamasıdır:

```cpp
#include <cstdio>
#include <memory>
#include <stdexcept>

void kullan(bool hata) {
    auto veri = std::make_unique<double[]>(10);
    veri[0] = 1.0;
    if (hata) throw std::runtime_error("bozuk girdi");
    std::printf("tamam\n");
}

int main() {
    try {
        kullan(false);
        kullan(true);
    } catch (const std::exception& e) {
        std::printf("yakalandi: %s\n", e.what());
    }
    return 0;
}
```

`kullan(true)` çağrısında fonksiyon istisna fırlatır, ama `veri` dizisi yığından çıkarken serbest kalır. Programı ASan ve LeakSanitizer ile çalıştırdığımızda hiçbir sızıntı raporu çıkmadı:

```term
$ g++ -std=c++17 -Wall -Wextra -g -fsanitize=address,undefined \
    -o raii raii.cpp && ./raii
tamam
yakalandi: bozuk girdi
```

C'deki `goto cleanup` ile C++'taki RAII aynı sorunu çözer; fark, doğruluğu nerede garantilediğindir. `goto`'da doğruluk, programcının her yolu elle doğru sıraya koymasına dayanır. RAII'de doğruluk, derleyicinin kapsam sonunda yıkıcıyı çağırmasına dayanır. Bu yüzden C++ kodunda ham `new`/`delete` ya da `malloc`/`free` yazmak, bugün çoğu ekipte bir kod kokusu sayılır.

### Python: istisnalar ve bağlam

Python'da hatalar istisnadır ve kodun akışını doğal olarak keser. Asıl risk, istisnayı yakalayıp anlamını kaybettirmektir. Yukarıdaki `ruff` çıktısındaki `E722` ve `pass` kalıbı bunun en kötü biçimidir. Doğru yaklaşım üç şeydir: yalnızca beklediğin istisnayı yakala, istisnayı anlamlı bir yeni istisnaya çevirirken nedenini koru, ve mesajda bağlamı (hangi kimlik, hangi dosya) yaz.

```python
def kullanici_bul(kimlik):
    if kimlik != 1:
        raise KeyError(kimlik)
    return "Ayse"


def ad_getir(kimlik):
    try:
        return kullanici_bul(kimlik).upper()
    except KeyError as hata:
        raise ValueError("kimlik %d yok" % kimlik) from hata


print(ad_getir(1))
try:
    ad_getir(7)
except ValueError as e:
    print("hata:", e, "| neden:", repr(e.__cause__))
```

Çıktı:

```term
$ python ustu.py
AYSE
hata: kimlik 7 yok | neden: KeyError(7)
```

`raise ... from hata` ifadesi, orijinal `KeyError`'ı `__cause__` olarak saklar. Üst katmanda hata ayıklarken iki bilgi birlikte görünür: "kimlik 7 yok" (ne olduğu) ve `KeyError(7)` (nereden geldiği). `from` olmadan yeni bir istisna fırlatsaydın, zincirin ilk halkası kaybolurdu.

### Ortak kural: hatayı yutma, bağlamla bildir

Dört dilde de aynı iki kural geçerlidir. Birincisi: **hatayı yutma.** Dönüş kodunu yok saymak, `except: pass` yazmak, boş bir `catch` bloğu bırakmak, hatanın yerini gizler ve yanlış durumda programın devam etmesine yol açar. İkincisi: **hatayı bağlamla bildir.** "Hata oluştu" mesajı işe yaramaz; "kayit.bin açılamadı (errno 2: No such file or directory)" ya da "kimlik 7 yok" gibi mesajlar, hatanın nerede ve neden olduğunu söyler. C'de `strerror(errno)`, Python'da `repr` ve `__cause__` bu bağlamı taşımanın araçlarıdır.

::: dikkat
Bölüm 6'da `assert`'ü programcı hatası için, dönüş kodunu ya da istisnayı dış dünyadaki beklenen hatalar için kullanmayı öğrendik. Burada aynı ayrım yeniden önemli: bir dosyanın olmaması beklenen bir durumdur ve normal hata yolundan geçer; bir indeksin negatif olmaması ise bir programcı varsayımıdır ve `assert` ile yakalanır.
:::
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

- **Uzun fonksiyon:** Birden çok soyutlama seviyesi aynı gövdede. Örnek 4'teki `rapor_uret` 43 satırlık bir gövdeydi ve beş ayrı iş yapıyordu. Giderme: Extract Function.
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
    """Ic ice yapiyi cezalandiran sayim (bilissel benzeri)."""
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
                          derinlik(d), cc_hesapla(d),
                          bilissel_hesapla(d)))
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
## Çözümlü Örnekler

Dört örnek, Bölüm 5'in altı adımını izler. Her birinde elle izlenebilir bir girdi var; sonuçları kendi kafanda ya da bir kâğıtta önce tahmin et, sonra çalıştır. Tahmin ile sonuç arasındaki fark, asıl öğrenme anıdır.

### Örnek 1 (★): Kötü adları ve tek fonksiyonu düzeltmek

Aşağıdaki fonksiyon, bir batarya kayıt listesinden kritik skorlu kayıtları seçer ve özetler. Adları kötü, ama davranışı açık.

```python
def f(k, e, m):
    r = []
    t = 0.0
    for i in k:
        if i[0] is None or i[1] is None or i[2] is None:
            continue
        if i[3] != 1:
            continue
        if i[1] < e:
            continue
        v = i[1] * 0.92 + i[2] * 0.08
        if v <= 85.0:
            continue
        r.append((i[0], v))
        t = t + v
    if len(r) == 0:
        return None
    if m == "ortalama":
        return t / len(r)
    if m == "liste":
        return r
    raise ValueError(m)
```

**Adım 1 — Anla.** Fonksiyon üç işi birden yapıyor: (1) aktif olan ve gerilimi eşiğin üstünde olan kayıtları seçmek, (2) her kayıt için ağırlıklı bir skor hesaplamak (gerilim ağırlığı 0.92, sıcaklık ağırlığı 0.08), (3) skoru 85'i aşanları ya liste olarak ya da ortalama olarak döndürmek. Girdi `k`, dört elemanlı tuple'lardan oluşuyor: (zaman, gerilim, sıcaklık, aktif). `m` ise çıktı modu.

**Adım 2 — Örnekle.** Beş kayıt, eşik 80, mod "liste" ve "ortalama":

```text
(0.0, 90.0, 80.0, 1)   aktif, gerilim >= 80, skor 89.2   -> kritik
(1.0, 95.0, 30.0, 0)   aktif degil                       -> atla
(2.0, 70.0, 60.0, 1)   gerilim 70 < 80                   -> atla
(3.0, 88.0, 50.0, 1)   skor 84.96 <= 85                  -> atla
(4.0, 100.0, 20.0, 1)  aktif, gerilim >= 80, skor 93.6   -> kritik
```

Elle hesap: 90 × 0.92 + 80 × 0.08 = 82.8 + 6.4 = 89.2. Beklenen liste `[(0.0, 89.2), (4.0, 93.6)]`, ortalama `(89.2 + 93.6) / 2 = 91.4`.

**Adım 3 — Kaba çöz.** Fonksiyonu çalıştırıp elle bulduğumuz sonuçla karşılaştırmak en kısa yol. Eski kod bu örnekte beklenen sonucu verir; ama sorun, sonucun doğru olup olmadığını değil, kodu okumanın ne kadar zor olduğudur. 22 satırı okurken üç harfli adı, dört sayıyı ve dört indeksi aynı anda akılda tutmak zorundasın.

**Adım 4 — Örüntü.** Fonksiyonun gövdesi üç bölümden oluşuyor: filtre (`continue` ile elenen dört durum), skor hesabı ve özet. Sabitler (0.92, 0.08, 85.0) adsız, tuple elemanları (`i[1]`, `i[3]`) ise "ilkel takıntısı" kokusu taşıyor. Her bölüm ayrı bir fonksiyon adı hak ediyor.

**Adım 5 — İyileştir.** Önce adları düzelt (davranışa dokunmadan), sonra sabitleri ve bir `NamedTuple`'ı tanıt, sonra filtreyi, skor hesabını ve özeti ayrı fonksiyonlara çıkar. Yeni sürümün tamamı:

```python
from typing import NamedTuple, Optional

GERILIM_AGIRLIGI = 0.92
SICAKLIK_AGIRLIGI = 0.08
KRITIK_SKOR = 85.0


class Kayit(NamedTuple):
    zaman: float
    gerilim: float
    sicaklik: float
    aktif: int


def kayit_oku(ham) -> Optional[Kayit]:
    zaman, gerilim, sicaklik, aktif = ham
    if zaman is None or gerilim is None or sicaklik is None:
        return None
    return Kayit(zaman, gerilim, sicaklik, aktif)
```

```python
def kayit_uygun_mu(kayit: Kayit, esik: float) -> bool:
    return kayit.aktif == 1 and kayit.gerilim >= esik


def skor_hesapla(kayit: Kayit) -> float:
    return (kayit.gerilim * GERILIM_AGIRLIGI
            + kayit.sicaklik * SICAKLIK_AGIRLIGI)


def kritik_skorlar(ham_kayitlar, esik):
    sonuc = []
    for ham in ham_kayitlar:
        kayit = kayit_oku(ham)
        if kayit is None or not kayit_uygun_mu(kayit, esik):
            continue
        skor = skor_hesapla(kayit)
        if skor > KRITIK_SKOR:
            sonuc.append((kayit.zaman, skor))
    return sonuc


def kritik_ozet(ham_kayitlar, esik, mod):
    kritikler = kritik_skorlar(ham_kayitlar, esik)
    if not kritikler:
        return None
    if mod == "ortalama":
        toplam = 0.0
        for _, skor in kritikler:
            toplam = toplam + skor
        return toplam / len(kritikler)
    if mod == "liste":
        return kritikler
    raise ValueError(mod)
```

Yeni yapıda en karmaşık fonksiyonun CC'si 5; eskisinde 11'di. Ama bu sayıya bakıp "bitti" demek yanlış olur: asıl kazanım, her parçanın tek bir soruya cevap vermesi.

**Adım 6 — Doğrula.** Eşdeğerliği kanıtlamanın en güvenilir yolu, rastgele girdilerle karşılaştırmaktır. Test, 5000 rastgele kayıt kümesi üretir (tohum 42, bazı gerilim ve sıcaklık değerleri `None`), her küme için üç mod dener (ortalama, liste ve tanınmayan bir mod):

```python
import random
from ex1_eski import f
from ex1_yeni import kritik_ozet


def uret(rng):
    kayitlar = []
    for z in range(rng.randint(0, 30)):
        g = None if rng.random() < 0.08 else rng.uniform(60, 100)
        s = None if rng.random() < 0.08 else rng.uniform(20, 90)
        kayitlar.append((float(z), g, s, rng.choice([0, 1, 1])))
    return kayitlar


def calistir(fn, *a):
    try:
        return ("ok", fn(*a))
    except ValueError as e:
        return ("hata", str(e))


if __name__ == "__main__":
    rng = random.Random(42)
    sayac = {"toplam": 0, "dolu": 0, "uyusmayan": 0}
    for _ in range(5000):
        kay = uret(rng)
        esik = rng.uniform(55, 95)
        for mod in ("ortalama", "liste", "bilinmeyen"):
            sayac["toplam"] += 1
            eski = calistir(f, kay, esik, mod)
            yeni = calistir(kritik_ozet, kay, esik, mod)
            if eski[1] is not None and eski[0] == "ok":
                sayac["dolu"] += 1
            if eski != yeni:
                sayac["uyusmayan"] += 1
    print("toplam:", sayac["toplam"], "dolu:", sayac["dolu"],
          "uyusmayan:", sayac["uyusmayan"])
```

İlk denemede özeti `sum(s for _, s in kritikler) / len(kritikler)` ile yazdık ve test 524 uyuşmazlık buldu. Nedeni, sayıların toplama sırasıyla ilgili değildi; `sum()` ile döngüsel toplam, sonuçların son basamaklarında farklı çıkıyordu. Python 3.12 sürüm notlarında da belirtildiği gibi `sum()`, float toplamında telafili (compensated) bir toplama kullanır ve bu sonuç `math.fsum` ile birebir aynıdır; bizim `t = t + v` döngümüz ise farklı bir sonuç üretir. Refactoring'in kuralı gereği davranışı bit düzeyinde korumak istedik, bu yüzden toplamayı açık döngüye çevirdik. Testin son hali:

| Durum | Eski `f` | Yeni `kritik_ozet` | Not |
|---|---|---|---|
| Elle örnek, liste | `[(0.0, 89.2), (4.0, 93.6)]` | aynı | beklenen |
| Elle örnek, ortalama | `91.4` | `91.4` | beklenen |
| 15000 durum, `sum()` ile | — | 524 uyuşmazlık | telafili toplama farkı |
| 15000 durum, döngü ile | — | 0 uyuşmazlık | davranış korundu |
| `gerilim = nan`, liste | `[(0.0, nan)]` | `None` | NaN ve koşul olumsuzlama |

Son satır, en öğretici olanıdır. Eski kod `if i[1] < e: continue` ile filtreler; NaN için `nan < e` yanlıştır, dolayısıyla kayıt geçer. Yeni kod `kayit.gerilim >= esik` ile geçirir; NaN için bu da yanlıştır, dolayısıyla kayıt elenir. `not (a < b)` ile `a >= b` NaN'da aynı değildir. Test rastgele girdilerde NaN üretmediği için bu farkı yakalayamadı; sen de bir koşulu tersine çevirdiğinde NaN kenar durumunu ayrıca düşünmelisin.

**Bunu AI'sız yazabilir misin?** Aynı kayıtlar için, yalnızca kritik kayıtların en yüksek skorunu döndüren bir `en_yuksek_skor(ham_kayitlar, esik)` fonksiyonu yaz. Önce adını ve parametrelerini düşün, sonra eski kodla eşdeğerlik testini yaz.

### Örnek 2 (★★): İç içe if cehenneminden koruma cümlelerine

Bir sensör ölçümünden alarm kararı çıkaran aşağıdaki fonksiyon, altı farklı sonuç döndürüyor. Girdiler: ölçüm (gerilim, sıcaklık) ya da `None`, son alarm zamanı ve şimdiki zaman.

```python
def alarm_karari(olcum, son_alarm_s, simdi_s):
    if olcum is not None:
        gerilim, sicaklik = olcum
        if gerilim is not None:
            if 300.0 <= gerilim <= 420.0:
                if sicaklik is not None:
                    if sicaklik > 60.0:
                        if simdi_s - son_alarm_s >= 60.0:
                            return "KRITIK"
                        return "SESSIZ"
                    if sicaklik > 45.0:
                        return "UYARI"
                    return "NORMAL"
                return "VERI_EKSIK"
            return "GERILIM_HATASI"
        return "VERI_EKSIK"
    return "VERI_YOK"
```

**Adım 1 — Anla.** Fonksiyon önce veri varlığını kontrol eder (ölçüm, gerilim, sıcaklık), sonra gerilim aralığını, sonra sıcaklık eşiklerini ve son olarak sessizlik süresini değerlendirir. Altı çıkış vardır: `VERI_YOK`, `VERI_EKSIK`, `GERILIM_HATASI`, `KRITIK`, `SESSIZ`, `UYARI`, `NORMAL` (yedi ayrı değer).

**Adım 2 — Örnekle.** Sekiz elle girdi, beklenen sonuçla birlikte:

```text
olcum          son   simdi  beklenen
None            0     0     VERI_YOK
(None, 50.0)    0    10     VERI_EKSIK
(250.0, 50.0)   0    10     GERILIM_HATASI
(350.0, None)   0    10     VERI_EKSIK
(350.0, 70.0)   0    10     SESSIZ    (60 sn dolmadi)
(350.0, 70.0)   0   100     KRITIK
(350.0, 50.0)   0    10     UYARI
(350.0, 30.0)   0    10     NORMAL
```

**Adım 3 — Kaba çöz.** Eski kodu bu sekiz girdide çalıştırıp beklenenlerle karşılaştırdık; hepsi tuttu. Ama kodu okumak için her seviyede bir öncekinin "açık" olduğunu hatırlamak zorundasın: altıncı katmanda beş koşulun da doğru olduğunu bilmen gerekiyor.

**Adım 4 — Örüntü.** Her `if`'in bir `else`'i yok; her iç koşul bir dış koşulun içinde. Bu, koruma cümlesi kalıbına çok uygun bir durum. Dikkat edilmesi gereken tek şey, geçersizlik kontrollerinin **sırası**: gerilim `None` kontrolü, aralık kontrolünden önce gelmeli; ama sıcaklık `None` kontrolü aralık kontrolünden sonra. Sebep, eski kodda gerilim aralık dışıysa sıcaklığın hiç denetlenmemesidir.

**Adım 5 — İyileştir.** Sabitleri adlandır, koruma cümlelerini sırayla yaz:

```python
GERILIM_ALT, GERILIM_UST = 300.0, 420.0
SICAKLIK_KRITIK, SICAKLIK_UYARI = 60.0, 45.0
SESSIZLIK_SURESI_S = 60.0


def alarm_karari(olcum, son_alarm_s, simdi_s):
    if olcum is None:
        return "VERI_YOK"
    gerilim, sicaklik = olcum
    if gerilim is None:
        return "VERI_EKSIK"
    if not GERILIM_ALT <= gerilim <= GERILIM_UST:
        return "GERILIM_HATASI"
    if sicaklik is None:
        return "VERI_EKSIK"
    if sicaklik > SICAKLIK_KRITIK:
        if simdi_s - son_alarm_s >= SESSIZLIK_SURESI_S:
            return "KRITIK"
        return "SESSIZ"
    if sicaklik > SICAKLIK_UYARI:
        return "UYARI"
    return "NORMAL"
```

İlk denememizde sıcaklık `None` kontrolünü gerilim aralık kontrolünün üstüne aldık; yani iki koşulu yer değiştirdik. Bu, "daha düz" görünüyordu ama davranışı bozdu: gerilim aralık dışıyken sıcaklık da boşsa, eski kod `GERILIM_HATASI` dönerken yeni kod `VERI_EKSIK` dönüyordu. Test 20000 girdide 125 uyuşmazlık buldu. Sıra, hangi geçersizliğin önce bildirildiğini belirler; bu bir davranıştır.

**Adım 6 — Doğrula.** 20000 rastgele girdi (tohum 42) üzerinde eski ve yeni sürümü karşılaştıran test:

```python
import random, sys
from ex2_eski import alarm_karari as eski
from ex2_yeni import alarm_karari as yeni


def deger(rng, lo, hi):
    r = rng.random()
    if r < 0.1:
        return None
    if r < 0.2:
        return rng.uniform(lo - 100, hi + 100)  # sinir disi
    return rng.uniform(lo, hi)


if __name__ == "__main__":
    rng = random.Random(42)
    uyusmayan = 0
    toplam = 0
    for _ in range(20000):
        olcum = None if rng.random() < 0.05 else (
            deger(rng, 300.0, 420.0), deger(rng, 20.0, 80.0))
        son = rng.uniform(0.0, 200.0)
        simdi = rng.uniform(0.0, 300.0)
        toplam += 1
        a = eski(olcum, son, simdi)
        b = yeni(olcum, son, simdi)
        if a != b:
            uyusmayan += 1
            if uyusmayan <= 2:
                print("OLCUM", olcum, "eski", a, "yeni", b)
    print("toplam", toplam, "uyusmayan", uyusmayan)
    sys.exit(0)
```

```term
$ python ex2_test.py
toplam 20000 uyusmayan 0
```

Ölçümler, aynı iki fonksiyon için şu şekilde:

| Sürüm | Döngüsel karmaşıklık | Bilişsel puan | Derinlik | Satır |
|---|---|---|---|---|
| Eski | 8 | 26 | 6 | 17 |
| Yeni | 8 | 8 | 2 | 17 |

Döngüsel karmaşıklık değişmedi, çünkü karar noktası sayısı aynı; yalnızca iç içelik kalktı. Bu yüzden CC tek başına "daha iyi" demek için yetersizdir; bilişsel puan ve derinlik bu farkı gösterir.

**Bunu AI'sız yazabilir misin?** Sıcaklık için "80 derecenin üstünde hemen KRITIK, sessizlik süresine bakma" kuralını ekle. Yeni koşulu nereye koyarsın ve hangi girdi ailesi bu değişikliğin doğru olduğunu gösterir?

### Örnek 3 (★★): C'de hata yolunda sızıntı ve goto ile temizlik

Bir sensör kayıt dosyası okuyan `kayit_oku` fonksiyonu C'de yazıldı. Dosya formatı: 4 bayt sihir değeri (`SIHIR`), 4 bayt kayıt sayısı `n` ve ardından `n` adet `double`. Önce başlık kısa bir ortak dosyaya konur:

```c
#ifndef KAYIT_H
#define KAYIT_H
#include <stddef.h>

#define SIHIR 0x4B41u /* "KA" dosya basligi */

/* 0: basarili; negatif: hata kodu.
   Cikista *kayitlar free() edilmeli. */
int kayit_oku(const char *yol, double **kayitlar, size_t *adet);

#endif
```

**Adım 1 — Anla.** `kayit_oku` bir dosyayı açar, başlığı doğrular, kayıt sayısını okur, kayıtlar için bellek ayırır, kayıtları okur ve sonucu çağırana verir. Her adım başarısız olabilir ve her başarısızlık farklı bir kaynağı açık bırakabilir.

**Adım 2 — Örnekle.** Dört girdi dosyası ve beklenen dönüş değerleri: `iyi.bin` (n = 3, üç kayıt) → 0; `sihir.bin` (sihir yanlış) → -2; `kesik.bin` (n = 1000 ama yalnızca üç kayıt var) → -5; `yok.bin` (dosya yok) → -1.

**Adım 3 — Kaba çöz.** Eski kodu, sızıntıları görebilmek için ASan ve LeakSanitizer ile çalıştırdık:

```c
#include <stdio.h>
#include <stdlib.h>
#include "kayit.h"

int kayit_oku(const char *yol, double **kayitlar, size_t *adet)
{
    FILE *f = fopen(yol, "rb");
    unsigned int sihir = 0, n = 0;
    double *tampon;

    if (f == NULL)
        return -1;
    if (fread(&sihir, sizeof sihir, 1, f) != 1 || sihir != SIHIR)
        return -2;                 /* SIZINTI: f kapanmadi */
    if (fread(&n, sizeof n, 1, f) != 1)
        return -3;                 /* SIZINTI: f kapanmadi */
    tampon = malloc(n * sizeof *tampon);
    if (tampon == NULL)
        return -4;                 /* SIZINTI: f kapanmadi */
    if (fread(tampon, sizeof *tampon, n, f) != n)
        return -5;                 /* SIZINTI: f ve tampon */
    fclose(f);
    *kayitlar = tampon;
    *adet = n;
    return 0;
}
```

Bu dosyayı dört girdiyle çalıştıran sürücü:

```c
#include <stdio.h>
#include <stdlib.h>
#include "kayit.h"

static void dosya_yaz(const char *ad, unsigned int sihir,
                      unsigned int n, int adet_gercek)
{
    FILE *f = fopen(ad, "wb");
    double v = 1.5;
    fwrite(&sihir, sizeof sihir, 1, f);
    fwrite(&n, sizeof n, 1, f);
    for (int i = 0; i < adet_gercek; i++)
        fwrite(&v, sizeof v, 1, f);
    fclose(f);
}

int main(void)
{
    double *k = NULL;
    size_t adet = 0;
    int r;

    setvbuf(stdout, NULL, _IONBF, 0);
    dosya_yaz("iyi.bin", SIHIR, 3, 3);
    dosya_yaz("sihir.bin", 0x1234u, 3, 3);
    dosya_yaz("kesik.bin", SIHIR, 1000, 3);

    r = kayit_oku("iyi.bin", &k, &adet);
    printf("iyi.bin    -> %d, adet=%zu\n", r, adet);
    free(k);
    r = kayit_oku("sihir.bin", &k, &adet);
    printf("sihir.bin  -> %d\n", r);
    r = kayit_oku("kesik.bin", &k, &adet);
    printf("kesik.bin  -> %d\n", r);
    r = kayit_oku("yok.bin", &k, &adet);
    printf("yok.bin    -> %d\n", r);
    return 0;
}
```

Derleyip ASan ile çalıştırdığımızda, eski sürüm için şu çıktıyı aldık (LeakSanitizer raporu, yol ve sürüm kırpılmıştır):

```term
$ gcc -std=c11 -Wall -Wextra -g -fsanitize=address,undefined \
    -o eski_asan ex3_main.c ex3_eski.c && ./eski_asan
iyi.bin    -> 0, adet=3
sihir.bin  -> -2
kesik.bin  -> -5
yok.bin    -> -1
=================================================================
==730==ERROR: LeakSanitizer: detected memory leaks

Direct leak of 8000 byte(s) in 1 object(s) allocated from:
    #1 ... in kayit_oku ex3_eski.c:17
SUMMARY: AddressSanitizer: 8000 byte(s) leaked in 1 allocation(s).
```

Sızıntının kaynağı 17. satırdaki `malloc`'tur ve sızan blok, 1000 `double`'lık (8000 bayt) tampondur: `kesik.bin` durumunda `-5` yolu tamponu serbest bırakmadan döner. Ama bu rapor eksiktir, çünkü `-2`, `-3`, `-4` ve `-1` yollarında açık kalan dosya tutucusu (`FILE *f`) bir bellek bloğu değildir; LeakSanitizer onu görmez. Bunu `gcc -fanalyzer` gösterir.

**Adım 4 — Örüntü.** Her hata yolunda hangi kaynakların açık kaldığını yazarsak bir tablo çıkar:

| Dönüş | Açık kalan kaynak (eski kod) |
|---|---|
| -1 | yok (dosya açılamadı) |
| -2 | `f` |
| -3 | `f` |
| -4 | `f` |
| -5 | `f` ve `tampon` |

Her erken dönüş, bir öncekinin kaynaklarını da açık bırakıyor; bu bir "tek temizleme noktası" eksikliğidir. Çözüm, tüm çıkışları tek bir temizleme bloğuna bağlamak ve bu bloğu kaynak sırasının tersine göre yazmaktır.

**Adım 5 — İyileştir.** `goto` ile tek çıkış, ters sıralı temizlik:

```c
#include <stdio.h>
#include <stdlib.h>
#include "kayit.h"

int kayit_oku(const char *yol, double **kayitlar, size_t *adet)
{
    int durum;
    FILE *f;
    unsigned int sihir = 0, n = 0;
    double *tampon = NULL;

    f = fopen(yol, "rb");
    if (f == NULL)
        return -1;

    durum = -2;
    if (fread(&sihir, sizeof sihir, 1, f) != 1 || sihir != SIHIR)
        goto cik_dosya;

    durum = -3;
    if (fread(&n, sizeof n, 1, f) != 1)
        goto cik_dosya;

    durum = -4;
    tampon = malloc(n * sizeof *tampon);
    if (tampon == NULL)
        goto cik_dosya;

    durum = -5;
    if (fread(tampon, sizeof *tampon, n, f) != n)
        goto cik_tampon;

    fclose(f);
    *kayitlar = tampon;
    *adet = n;
    return 0;

cik_tampon:
    free(tampon);
cik_dosya:
    fclose(f);
    return durum;
}
```

Etiketler yaptığı işi söyler: `cik_tampon` önce tamponu serbest bırakır ve `cik_dosya`'ya düşer; `cik_dosya` dosyayı kapatır. Bir `goto` dalı, ayrılmamış kaynağa dokunmaz: `tampon` henüz ayrılmadan `-4` yoluna giden dal yalnızca `cik_dosya`'ya atlar. `durum` değişkeni, her adımın hangi hata kodunu döndüreceğini başta belirler; bu, hata kodlarının iki kez yazılmasını önler ama adımlar arasında unutmaya da açıktır. Daha temiz bir alternatif, her adım için ayrı bir etiket kullanmaktır; bunu okurun denemesi için bırakıyoruz.

**Adım 6 — Doğrula.** Üç kanıt: dönüş değerleri aynı kaldı, ASan temiz, `-fanalyzer` uyarısı yok.

```term
$ gcc -std=c11 -Wall -Wextra -g -fsanitize=address,undefined \
    -o yeni_asan ex3_main.c ex3_yeni.c && ./yeni_asan
iyi.bin    -> 0, adet=3
sihir.bin  -> -2
kesik.bin  -> -5
yok.bin    -> -1
$ gcc -std=c11 -Wall -Wextra -fanalyzer -c ex3_yeni.c
(uyari yok)
```

Eski sürümün `-fanalyzer` çıktısı ise şuydu:

```term
ex3_eski.c:14:16: warning: leak of FILE 'f' [-Wanalyzer-file-leak]
ex3_eski.c:14:16: warning: leak of 'f' [-Wanalyzer-malloc-leak]
ex3_eski.c:21:16: warning: leak of FILE 'f' [-Wanalyzer-file-leak]
ex3_eski.c:21:16: warning: leak of 'tampon' [-Wanalyzer-malloc-leak]
```

| Girdi | Dönüş (eski) | Dönüş (yeni) | ASan (eski) | ASan (yeni) | -fanalyzer (eski) |
|---|---|---|---|---|---|
| iyi.bin | 0 | 0 | temiz | temiz | uyarı yok |
| sihir.bin | -2 | -2 | temiz | temiz | `f` sızıntısı |
| kesik.bin | -5 | -5 | 8000 bayt | temiz | `f` ve `tampon` |
| yok.bin | -1 | -1 | temiz | temiz | uyarı yok |

Tablo, iki aracın birbirini tamamladığını gösteriyor: ASan bellek sızıntısını, `-fanalyzer` dosya tutucusu sızıntısını yakalar. Hangisine güvenirsen, kendi başına eksik kalır. Ayrıca `-fanalyzer` çıktısındaki iki uyarının aynı satırı göstermesi, tek bir hata yolunun birden çok kaynağı sızdırdığını anlatır.

**Bunu AI'sız yazabilir misin?** `fread` ile `n` değeri 0 okunduğunda ne olur? `malloc(0)`'ın standart tarafından nasıl tanımlandığını (genel bilgi: `NULL` dönebilir ya da benzersiz bir işaretçi) düşün ve bu durumda kodun doğru davranıp davranmadığını test ile göster.

### Örnek 4 (★★★): Tanrı fonksiyonunu karakterizasyonla parçalamak

Aşağıdaki `rapor_uret` fonksiyonu, cihaz ölçümlerinden bir metin raporu üretiyor. Girdi satırları `cihaz;zaman;deger;birim` biçiminde; birim `V` ya da `mV`. Yorum satırları (`#`) ve boş satırlar atlanır; bozuk satırlar sayılır. Bu fonksiyon büyük ve değişmesi riskli: sınırda, bir sorumluluğu değiştirmek diğerlerini de bozabilir.

**Adım 1 — Anla.** Fonksiyon beş işi birden yapıyor: satırları ayrıştırmak ve doğrulamak, birimi volta çevirmek, cihaz bazında min, max ve ortalama toplamak, eşiği aşan cihazları `UYARI` olarak işaretlemek ve sonucu hizalı bir metin tablosu olarak biçimlendirmek.

**Adım 2 — Örnekle.** Beş satırlık bir girdi, elle tahmin ettiğimiz sonuç: `ALFA` iki ölçüm (3.9 ve 2.5 V), `BETA` bir ölçüm (3500 mV = 3.5 V), bir bozuk satır (`x;;1;V`, zaman boş) ve bir yorum (`# not`). Beklenen: `ALFA` maksimumu 3.9 olduğu için eşik 3.6'yı aşar ve `UYARI`; `BETA` `TAMAM`; bir hatalı satır. Program bu beklentiyi aynen üretti.

**Adım 3 — Kaba çöz.** Fonksiyonun çıktısını test etmek kolaydır; zor olan, 43 satırlık gövdeyi okuyup her değişkenin hangi aşamada ne olduğunu takip etmektir:

```python
ESIK = 3.6


def rapor_uret(satirlar):
    cihazlar = {}
    hatalar = 0
    for satir in satirlar:
        satir = satir.strip()
        if not satir or satir.startswith("#"):
            continue
        parca = satir.split(";")
        if len(parca) != 4:
            hatalar += 1
            continue
        cihaz, zaman, deger, birim = parca
        if not zaman.isdigit():
            hatalar += 1
            continue
        try:
            deger = float(deger)
        except ValueError:
            hatalar += 1
            continue
        if birim == "mV":
            deger = deger / 1000.0
        elif birim != "V":
            hatalar += 1
            continue
        if cihaz not in cihazlar:
            cihazlar[cihaz] = {"min": deger, "max": deger,
                               "toplam": 0.0, "adet": 0}
        c = cihazlar[cihaz]
        c["min"] = min(c["min"], deger)
        c["max"] = max(c["max"], deger)
        c["toplam"] += deger
        c["adet"] += 1
    cikti = ["CIHAZ       ADET      MIN      MAX    ORT  DURUM"]
    for ad in sorted(cihazlar):
        c = cihazlar[ad]
        ort = c["toplam"] / c["adet"]
        durum = "UYARI" if c["max"] > ESIK else "TAMAM"
        cikti.append("%-10s %5d %8.3f %8.3f %6.3f  %s"
                     % (ad, c["adet"], c["min"], c["max"], ort,
                        durum))
    cikti.append("hatali satir: %d" % hatalar)
    return "\n".join(cikti) + "\n"
```

**Adım 4 — Örüntü.** Beş iş beş bloğa karşılık geliyor. Bloklar bir değişken kümesini paylaşıyor (`cihazlar`, `hatalar`) ve bu paylaşım, her bloğun ne yaptığını sınırlıyor. Sözlük (`{"min": ..., "max": ...}`) bir ilkel takıntısıdır: anahtar adları yazım hatasına açıktır ve veri yapısının ne olduğu sözlükte yazılı değildir.

**Adım 5 — İyileştir.** Dört adımda, her adımdan sonra testi çalıştırarak ilerledik:

- **a) Ayrıştırmayı çıkar.** `satir_ayristir` tek bir satırı ayrıştırır ve bozuk satır için `ValueError` fırlatır. Döngü, `try/except` ile hatalı satırları sayar.
- **b) Sözlüğü sınıfa çevir.** `CihazOzeti`, `min`, `max`, `toplam`, `adet` alanlarını ve `ekle`, `ortalama`, `durum` davranışlarını tutar. İlk değer için `CihazOzeti(deger, deger)` çağrısı, eski `min` ve `max` başlangıcıyla aynı sonucu verir.
- **c) Toplamayı ayır.** `ozetle` yalnızca veriyi toplar ve `(cihazlar, hatalar)` döndürür.
- **d) Biçimlendirmeyi ayır.** `satir_bicimle` tek bir cihaz satırını üretir; `rapor_uret` artık yalnızca bu parçaları birleştirir.

Son sürüm, dört parçanın birleşimidir:

```python
from dataclasses import dataclass

ESIK = 3.6
BASLIK = "CIHAZ       ADET      MIN      MAX    ORT  DURUM"


@dataclass
class CihazOzeti:
    minimum: float
    maksimum: float
    toplam: float = 0.0
    adet: int = 0

    def ekle(self, volt):
        self.minimum = min(self.minimum, volt)
        self.maksimum = max(self.maksimum, volt)
        self.toplam += volt
        self.adet += 1

    def ortalama(self):
        return self.toplam / self.adet

    def durum(self):
        return "UYARI" if self.maksimum > ESIK else "TAMAM"


def satir_ayristir(satir):
    cihaz, zaman, deger, birim = satir.split(";")
    if not zaman.isdigit():
        raise ValueError("zaman")
    deger = float(deger)
    if birim == "mV":
        deger = deger / 1000.0
    elif birim != "V":
        raise ValueError("birim")
    return cihaz, deger
```

```python
def ozetle(satirlar):
    cihazlar = {}
    hatalar = 0
    for satir in satirlar:
        satir = satir.strip()
        if not satir or satir.startswith("#"):
            continue
        try:
            cihaz, deger = satir_ayristir(satir)
        except ValueError:
            hatalar += 1
            continue
        if cihaz not in cihazlar:
            cihazlar[cihaz] = CihazOzeti(deger, deger)
        cihazlar[cihaz].ekle(deger)
    return cihazlar, hatalar


def satir_bicimle(ad, c):
    return "%-10s %5d %8.3f %8.3f %6.3f  %s" % (
        ad, c.adet, c.minimum, c.maksimum, c.ortalama(), c.durum())


def rapor_uret(satirlar):
    cihazlar, hatalar = ozetle(satirlar)
    cikti = [BASLIK]
    for ad in sorted(cihazlar):
        cikti.append(satir_bicimle(ad, cihazlar[ad]))
    cikti.append("hatali satir: %d" % hatalar)
    return "\n".join(cikti) + "\n"
```

**Adım 6 — Doğrula.** Karakterizasyon testi, Bölüm 23.9'da gösterdiğimiz betikle çalışır: 300 tohumlu girdinin çıktı özetleri, eski sürümden alınan altın kayıtla karşılaştırılır. Her adımda ölçüm de aldık:

| Adım | `rapor_uret` satır | `rapor_uret` CC | En yüksek CC | Bozuk (300 içinden) |
|---|---|---|---|---|
| 0 (eski) | 43 | 12 | 12 (`rapor_uret`) | altın kayıt |
| a) `satir_ayristir` | 29 | 8 | 8 (`rapor_uret`) | 0 |
| b) `CihazOzeti` | 23 | 7 | 7 (`rapor_uret`) | 0 |
| c-d) `ozetle`, `satir_bicimle` | 7 | 2 | 6 (`ozetle`) | 0 |

Her adımda bozuk sayısı sıfır kaldı. Testin gerçekten duyarlı olduğunu kontrol etmek için iki bilinçli hata enjekte ettik: eşiği 3.6'dan 3.5'e çekmek 22 bozuk çıktı, sütun sırasını değiştirmek 244 bozuk çıktı üretti (Bölüm 23.9). Yani test, hem birim dönüşümü hem sıralama gibi ince değişiklikleri yakalar.

Bu örnekte dikkat edilecek bir nokta daha var: toplam CC'ye bakarsan, fonksiyon sayısı arttığı için bir miktar yükselmiş olabilir. Ama hiçbir fonksiyon artık beş ayrı işi birden yapmıyor. Okurun her parçayı ayrı ayrı anlayabilmesi, toplam karmaşıklığın bir miktar artmasından daha değerlidir.

**Bunu AI'sız yazabilir misin?** Birimlere `kV` desteği eklemek gerekiyor. Hangi tek fonksiyon değişir? Karakterizasyon testini bu yeni birimi kapsayacak şekilde nasıl güncellersin, ve eski altın kayıt bu güncellemeyle neden geçersiz olur?

## Kendin Yap Projeleri

::: dikkat
Bu iki projede yapay zekâ aracına kod yazdırma. Bölüm 6'daki kuralın aynısı geçerli: önce kendin dene, takıldığında kavramı sor, cevabı değil. Projeyi bitirdikten sonra kendi kodunu bu bölümün örnekleriyle karşılaştır; farkın nedenini yazmak, öğrenmenin asıl kısmıdır.
:::

### Proje 1 (★★): Kendi mini linter'ın

**Amaç.** Python kaynak dosyalarını `ast` ile tarayan ve dört kod kokusunu satır numarasıyla raporlayan küçük bir araç yaz. Araç, Bölüm 23.9'daki `karmasiklik.py`'nin üzerine kurulabilir, ama sıfırdan yazman daha çok şey öğretir.

**Beklenen davranış.** Komut `python linter.py dosya1.py dosya2.py` biçiminde çalışmalı ve her bulgu şu biçimde yazılmalı: `dosya:satir: KOKU ad (deger)`. Dört kural:

- Uzun fonksiyon: 30 satırdan uzun.
- Uzun parametre listesi: 4 ve üzeri parametre.
- Yüksek döngüsel karmaşıklık: CC 10'dan büyük.
- Sihirli sayı: 0, 1, -1 ve 2 dışında kalan sayısal sabitler; yalnızca atama ya da çağrı argümanı olarak kullanıldıklarında. Büyük harfli sabit atamaları (`ESIK = 3.6`) ve varsayılan argümanlar hariç.

**Önerilen yaklaşım.** İpucu olarak: `ast.walk` ile düğümleri gez; sihirli sayı için `ast.Constant` düğümlerini bul ve üst düğümün türünü (atama mı, çağrı mı) kontrol et. Kuralları bir sözlükte tut, eşikleri komut satırı argümanı olarak al. Tam çözüm değil, yalnızca yön göstermek için: önce dört kuralı ayrı fonksiyonlara böl, sonra tek bir dolaşımda hepsini topla.

**Başarı kriterleri.**

- `ex1_eski.py` için en az iki kural uyarısı üretiyor; `ex1_yeni.py` için sihirli sayı uyarısı yalnızca sabit tanımlamayan satırlarda çıkıyor.
- Kendi kitap motorunun (`engine/` altındaki bir dosya) üzerinde çalışıyor ve kaç fonksiyonun işaretlendiğini raporluyor.
- Eşikler komut satırı argümanıyla değiştirilebiliyor.
- Yanlış pozitif (aracın yanlış alarm verdiği) en az iki durumu listeleyip nedenini yazıyorsun.

### Proje 2 (★★★): Eski bir C modülünü güvenceye al ve temizle

**Amaç.** Kendi yazdığın ya da MertOS ve EV Dashboard'dan seçtiğin 150-300 satırlık bir C modülünü, davranışını bozmadan temizlemek.

**Yapılacak.**

1. Modülün açık API'sini belirle. Her herkese açık fonksiyon için bir karakterizasyon testi yaz: tohumlu girdiler üret, çıktıları kaydet (Bölüm 23.9'daki betik bir başlangıç noktası).
2. `-std=c11 -Wall -Wextra -Wshadow -Wconversion` ile uyarısız derle. ASan ve UBSan ile temiz çalıştır.
3. Hata yollarını `goto` ile tek temizleme noktasına bağla. Her kaynağın serbest bırakıldığını `-fanalyzer` ile doğrula.
4. En uzun üç fonksiyonu Extract Function ile böl; her adımda karakterizasyon testini çalıştır.
5. Önce ve sonra için karmaşıklık tablosu üret (kendi aracınla ya da elle; hangi yöntemi kullandığını yaz).

**Önerilen yaklaşım.** Önce davranışı kaydet, sonra temizle. Her dönüşümü ayrı bir kayıt (commit) olarak tut; Bölüm 38'de git ile bunu nasıl yapacağını göreceksin. Sıra değiştiren her dönüşümü (koruma cümleleri gibi) bilerek test et; sıranın davranış olduğunu kendi testinle kanıtla.

**Başarı kriterleri.**

- Karakterizasyon testi her adımda geçiyor ve en az bir bilinçli mutantı (bozuk kopya) yakalıyor.
- Dört bayrakla (`-Wall -Wextra -Wshadow -Wconversion`) uyarısız derleniyor; ASan ve UBSan temiz; `-fanalyzer` uyarısı yok.
- En uzun fonksiyon 30 satırın altında, en yüksek döngüsel karmaşıklık 10'un altında.
- Yapılan her dönüşümün listesi ve nedeni yazılı; hangi dönüşümün hangi testi değiştirdiği belli.

## Ek Alıştırmalar

Aşağıdaki alıştırmalar cevapsız. Her birini önce kâğıda ya da boş bir dosyaya düşünerek çöz; kodu yazdıktan sonra kontrol et.

1. ★ Şu adları gözden geçir: `d`, `flag`, `tmp2`, `aktif_mi`, `bekle`, `data`. Hangileri niyeti söylüyor, hangileri söylemiyor? Her biri için iyi bir ad öner ve nedenini yaz.
2. ★ `kontrol(x)` adlı bir fonksiyon hem girdiyi doğrulayıp hem de bir sayacı artırıyor. Adını ve yapısını nasıl ayırırsın? Komut–sorgu ayrımını kullan.
3. ★ Dört parametreli bir fonksiyonu iki parametreye indirmek istiyorsun. Hangi bilgiyi bir yapıda toplarsın? Yapının adını ve alanlarını yaz; bu yapının neden tek başına bir anlam taşıdığını açıkla.
4. ★★ Derinliği beş olan bir iç içe `if` bloğunu koruma cümleleriyle düzleştir. Koşulların sırasını değiştirmenin davranışı nasıl etkileyebileceğini iki somut örnekle göster.
5. ★★ İki fonksiyon aynı üç satırı içeriyor, ama biri fiyat hesabında, diğeri raporlamada kullanılıyor. Bu satırları tek bir fonksiyonda birleştirmeli misin? Nedenini değişme sebepleri üzerinden açıkla ve hangi testi yazarsın?
6. ★★ Bir C fonksiyonu dört farklı hata yolunda üç kaynak ayırıyor. `goto` etiketlerini nasıl sıralarsın? Etiketleri ters sırada tasarlamanın neden doğru olduğunu bir tabloyla göster.
7. ★★ `sum()` ile döngüsel toplamın float sonuçlarının farklı çıkabileceğini gösteren üç satırlık bir program yaz. Hangisini seçersin ve neden? (Mülakat)
8. ★★ Bir yorum "bu fonksiyon iş parçacığı güvenlidir" diyor, ama içinde paylaşılan bir global sayaç var. Bunu nasıl kanıtlar ya da düzeltirsin? Yorumu ne zaman yazmalısın?
9. ★★★ Bir enum'a yeni bir değer eklemenin `switch` içindeki `default:` dalı varken ve yokken derleyici uyarılarını nasıl etkilediğini `-Wswitch` ile göster. Kod incelemesinde bu bilgiyi nasıl kullanırsın? (Mülakat)
10. ★★★ Bir Python fonksiyonunun döngüsel karmaşıklığını elle hesapla, sonra bu bölümdeki `karmasiklik.py` ile karşılaştır. Farklı çıkan bir durum bul ve nedenini açıkla. (Mülakat)
11. ★★★ `int i` ile `size_t n` karşılaştırmasındaki `-Wsign-compare` uyarısının gerçek bir hataya dönüştüğü bir girdiyi tarif et. `n` gerçekten `INT_MAX`'ı aşacak kadar büyük bir bellek olmadan bunu nasıl test edersin? (Mülakat)
12. ★★★ Savunma sanayiinde kodlama standardında "dinamik bellek ayırma yasak" kuralı olsaydı, Örnek 3'teki `kayit_oku` fonksiyonunu bu kısıtla nasıl yeniden yazardın? Hangi bilgiyi çağıran tarafa bırakırsın? (Mülakat)

## Kod Okuma Egzersizi

Bu egzersizde gerçek bir açık kaynak belgesini okuyacaksın: Linux çekirdeği v6.6 sürümündeki `Documentation/process/coding-style.rst` dosyası. Dosya, `https://raw.githubusercontent.com/torvalds/linux/v6.6/Documentation/process/coding-style.rst` adresinden indirildi ve 1271 satırdır. Bu bölümde yalnızca üç bölüm kullanıyoruz: 6 (Functions), 7 (Centralized exiting of functions) ve 16 (Function return values and names). Belge GPL-2.0 lisanslıdır; aşağıdaki kesit yalnızca kısa bir alıntıdır.

Bölüm 7, `goto` ile merkezi çıkışı anlatırken şu kesiti verir (kaynakta sekmeler kullanılmış; burada 4 boşlukla gösterildi, başka hiçbir değişiklik yok):

```c
int fun(int a)
{
    int result = 0;
    char *buffer;

    buffer = kmalloc(SIZE, GFP_KERNEL);
    if (!buffer)
        return -ENOMEM;

    if (condition1) {
        while (loop1) {
            ...
        }
        result = 1;
        goto out_free_buffer;
    }
    ...
out_free_buffer:
    kfree(buffer);
    return result;
}
```

Belge, etiket adları için şunu söyler: etiket, `goto`'nun ne yaptığını ya da neden orada olduğunu anlatmalıdır. Bölüm 6 ise fonksiyon boyutu için şunu söyler: fonksiyonlar kısa olmalı ve tek bir şey yapmalıdır. Bölüm 16 ise dönüş değeri kuralını verir: eylem adlı fonksiyon hata kodu, yüklem adlı fonksiyon başarı boolean'ı döndürmelidir.

**Sorular — cevaplamadan geçme:**

1. `fun` içindeki `out_free_buffer` etiketi olmadan, fonksiyonun üç ayrı çıkışı olsaydı, her çıkışta `kfree(buffer)` yazmak zorunda kalırdın. Bu durum hata oranını neden artırır? Bölüm 23.6'daki `kayit_oku` örneğiyle karşılaştır.
2. Belge etiket adlarında `err1:` ve `err2:` gibi numaralı adlardan kaçınmayı öneriyor. Bu adların sakıncasını kendi cümlelerinle yaz; yeni bir çıkış yolu eklendiğinde ne olur?
3. Bölüm 16'daki kurala göre `add_work()` ve `pci_dev_present()` ne döndürmelidir? Bu kuralın hangi tür bir hatayı önlediğini, Bölüm 23.2'deki adlandırma kuralıyla birlikte açıkla.
4. Belgenin bir başka bölümünde tek bir `err:` etiketi, bazı yollarda henüz ayrılmamış bir işaretçiyi serbest bırakabilir. Bu hatayı bir örnekle göster ve çözümünü iki etiketle yaz. Örnek 3'teki etiketlerle karşılaştır.
5. Bölüm 6, bir fonksiyonun 5-10'dan fazla yerel değişken içermemesini öneriyor. Bu sayı neden kesin bir kural değil de bir işaret? Bölüm 23.9'daki karmaşıklık ölçümüyle ilişkisini düşün.
6. (Mülakat) `fun` içinde `result` değişkeni neden 0 ile başlatılmış? `goto` kullanılmayan bir sürümde `result` yerine ne yazardın, ve bu sürümde hangi çıkış yolunda bir temizlik hatası olasılığı artar?

## Bölüm Özeti

Bu bölümde kodun okunabilirliğini ölçülebilir parçalara ayırıp her birini bir araçla ve bir testle destekledik:

- Adlar niyet söyler: kapsamla orantılı uzunlukta, boolean adları bir soru gibi okunur, kısaltmalar yalnızca ekipçe yerleşmişse kullanılır. Türkçe ve İngilizce adlar aynı kod tabanında karıştırılmaz.
- Fonksiyonlar kısa, tek iş yapar ve yan etkisi adından anlaşılır. Komut ve sorgu ayrılır; koruma cümleleri iç içe yapıyı düzleştirir, ama koşulların sırası davranışın parçasıdır.
- Yorumlar NEDEN'i anlatır. Eskimiş yorum, kodla çelişen yorumdan daha tehlikelidir; mümkünse yorumun yerine ad ya da sabit kullanılır.
- Biçim araçları (clang-format, black) tartışmayı bitirir; derleyici uyarıları (`-Wshadow`, `-Wconversion`), clang-tidy ve mypy gibi araçlar hataları çalıştırmadan yakalar. Bu bölümde bunların hepsinin gerçek hataları bulduğunu gördük.
- Hata yolları tek bir yerde temizlenir: C'de `goto` ile ters sıralı temizlik, C++'ta RAII, Python'da istisnayı yutmadan bağlamla zincirlemek.
- Sihirli sayılar adlandırılır, tekrar yalnızca aynı değişme nedenine sahip kopyalar için birleştirilir; tip koşulları ihtiyaç duyulduğunda polimorfizme çevrilir.
- Refactoring davranışı koruyan küçük adımlarla yapılır; her adım karakterizasyon testiyle doğrulanır ve test, bilinçli mutantlarla sınanır.
- Döngüsel karmaşıklık koşul sayısını ölçer; iç içe yapının zihinsel yükünü ise derinlik ve bilişsel bir puan daha iyi yansıtır. Tek bir metriğe güvenmek yanıltıcıdır.
- Savunma sanayiinde MISRA C, CERT C ve JSF AV C++ gibi standartlar kısıtları belirler; araçlarla denetlenebilen kısmı otomatikleşir, kalanı kod incelemesiyle kontrol edilir.

### Kısım V'in kapanışı

Kısım V'te dört ayrı bölümde aynı soruya farklı açılardan baktık: kod, bir sistemi nasıl taşır? Bölüm 20'de sınıflar ve kalıtımla veri ile davranışı birlikte paketledik. Bölüm 21'de SOLID ile her parçanın hangi sorumluluğu taşıdığını ve bağımlılıkların nereye yöneleceğini gördük. Bölüm 22'de tekrar eden tasarım sorunlarına adlandırılmış çözümler, yani kalıplar, ele aldık. Bölüm 23'te ise bu tasarımın kod düzeyinde nasıl okunur ve değiştirilebilir kaldığını inceledik: bir adın, bir fonksiyonun, bir yorumun ve bir hata yolunun ne kadarının okurun kafasında yük olduğunu.

Kısım V'in ortak fikri şudur: iyi tasarım, değişikliğin maliyetini düşürmektir. Kod bugün çalışıyorsa yeterli değildir; yarın bir hata düzeltmesi ya da yeni bir özellik için güvenle değiştirilebiliyorsa iyidir. Bu bölümdeki her araç ve her test, bu güveni bir adım daha sağlamlaştırmak için var.

**Sonraki bölümde:** Bölüm 24 (CPU Mimarisi) ile Kısım VI — İşletim Sistemi & Mimari başlıyor. Şimdiye kadar kodu bir insanın okuyacağı bir metin olarak ele aldık; Kısım VI'da bu kodun donanımda nasıl çalıştığına bakacağız: komutlar, yazmaçlar, önbellekler ve bunların C kodundaki bir atamaya nasıl karşılık geldiği. Bölüm 23'teki hata yolları ve kaynak yönetimi, orada işletim sisteminin bellek ve süreç yönetimiyle birlikte yeniden karşımıza çıkacak.

::: mulakat
Aşağıdaki sorular cevapsız bırakılmıştır. Hemen cevaplamaya çalışma; her birini birkaç dakika düşün, sonra kendi kelimelerinle yaz:

1. İyi bir değişken adı ile kötü bir değişken adı arasındaki farkı, okurun bilişsel yükü üzerinden açıklar mısın? Kısa ad ne zaman doğrudur?
2. Döngüsel karmaşıklık ile bilişsel karmaşıklık neden farklı sonuçlar verebilir? Koruma cümlelerine geçmek CC'yi değiştirmezken okunabilirliği neden değiştirir?
3. C'de hata yönetimi için `goto` kullanmak neden yaygındır, ama bunun tehlikeleri nelerdir? RAII bu tehlikelerin hangilerini ortadan kaldırır?
4. Bir fonksiyonu test etmeden refactor etmek neden tehlikelidir? Karakterizasyon testi ile birim testi arasındaki fark nedir?
5. Bir enum'a yeni bir değer eklendiğinde `default:` dalı olan ve olmayan `switch` bloklarında ne olur? Bu bir tasarım kararı mıdır?
6. Kod kokusu ile hata arasındaki fark nedir? Hata olmayan bir kodu neden yine de değiştirmek isteyebilirsin?
7. Bir ekipte Türkçe ve İngilizce adların karışması hangi somut sorunlara yol açar? Bu kararı kim ve nasıl vermelidir?
8. MISRA C gibi bir standart, tanımsız davranışın bazı türlerini neden yasaklar? Derleyici uyarıları ile standart kuralları arasındaki ilişki nedir?
:::
