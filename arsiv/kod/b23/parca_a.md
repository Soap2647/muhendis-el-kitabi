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
