%% kisim_no: I
%% kisim_ad: Programlama Temelleri
%% bolum_no: 3
%% baslik: Python — C Bilenler İçin

## Giriş: Turist değil, göçmen

Python'u muhtemelen benden önce tanıdın: `ÖZCE`'nin kodek deneyleri, derste yazdığın betikler, belki bir iki not defteri (notebook). Ama bir dili *kullanmak* ile *bilmek* arasında dağlar var. Bu bölümün iddiası şu: iki bölümdür C ile kurduğun bellek modeli, Python'u yüzeysel kullanan birinden seni kalıcı olarak ayıracak. Çünkü Python'un bütün "tuhaf" davranışları — listenin kopyalanmayıp paylaşılması, fonksiyondaki varsayılan değerin birikmesi — bellek modelini bilmeyene kara büyü, bilene apaçık sonuçtur.

Neden Python? Kariyer hedefin cevabı kendisi veriyor: makine öğrenmesinin ana dili Python. PyTorch, TensorFlow, pandas, numpy — Kısım XIV'te yaşayacağın her şey Python konuşuyor. Baykar'ın ML mülakatında beyaz tahtaya Python yazacaksın. Ama işin güzel ironisi şu: bu araçların *hepsinin altında C var*. Python yavaş dediğimiz işleri C'ye devreder; numpy bir C kütüphanesinin cilalı yüzüdür, CPython yorumlayıcısının kendisi C ile yazılmıştır. Yani C'den Python'a geçerken katman *değiştirmiyorsun*, katman *ekliyorsun*.

Bu yüzden bu bölüm bir "Python'a giriş" değil; bir **fark haritası**. Her başlıkta aynı soruyu soracağız: *C'de böyleydi — Python'da ne değişti ve neden?* Sözdizimini geçerken öğreneceksin; asıl odağımız zihinsel modelin kendisi: isimler, nesneler, referanslar, çöp toplayıcı. Sonra da Python'u Python yapan dört aleti — comprehension, generator, decorator, context manager — C'deki karşılıksızlıklarıyla birlikte kuracağız.

::: not
Sürüm notu: bu kitap boyunca Python 3.10 ve üzeri varsayılır. Python 2 öldü; internette hâlâ dolaşan `print x` yazımlı örnekler tarihî belgedir, kod değil.
:::

## 3.1 Derleyici gitti, yorumlayıcı geldi — ama tam değil

C'de akış netti: `gcc` kaynak kodu makine koduna çevirir, işletim sistemi o dosyayı çalıştırır. Python'da elle derleme adımı yok; dosyayı doğrudan çalıştırırsın:

```term
$ python3 merhaba.py
Merhaba!
$ python3
>>> 2 ** 10
1024
>>> exit()
```

İkinci kullanım C'de hiç olmayan bir şey: **REPL** (Read-Eval-Print Loop) — yaz, anında çalışsın. Küçük fikirleri denemek için derle-bağla-çalıştır turuna gerek yok; bu, Python'un "deney hızı"nın kaynağı ve ML'de bu kadar sevilmesinin sebeplerinden biri.

Peki "derleme yok" ne kadar doğru? Aslında yarım: CPython, kaynak kodunu önce **bytecode** denen ara dile çevirir, sonra bu bytecode'u bir sanal makinede yorumlar. Bölüm 1'deki fetch-decode-execute döngüsünü hatırla — CPython'un kalbinde de aynısı var, ama komutları donanım değil, C ile yazılmış dev bir `switch` işler. Her `import` ettiğin modülün yanında beliren `__pycache__/` klasörü, işte bu bytecode'un önbelleğidir.

Bunun iki pratik sonucu var. **Birincisi hız:** her toplama işlemi, C'deki tek makine komutuna karşılık Python'da onlarca yorumlayıcı adımıdır; saf Python döngüsü, işe göre değişmekle birlikte genellikle C'den onlarca kat yavaştır. **İkincisi hata zamanı:** C derleyicisi tür hatalarını *derlemede* yakalar; Python ise çoğu hatayı ancak o satır *çalışınca* fark eder. Yazım hatası yaptığın dal, test edilmediyse üretimde patlar — Bölüm 39'daki test disiplininin Python dünyasında bu kadar hayati olmasının kökü budur.

## 3.2 En büyük fark: isim, kutu değil etikettir

C'de değişken bir *kutuydu*: `int x = 42` dediğinde derleyici 4 baytlık yer ayırır, `x` o kutunun adıdır, `y = x` değeri yeni kutuya *kopyalar*. Python'da bu modeli kafandan silmen gerekiyor. Python'da `x = 42` şu demek: bellekte bir **int nesnesi** yaratılır ve `x` adında bir **etiket** ona iliştirilir. `y = x` ise yeni kutu açmaz; *aynı nesneye ikinci bir etiket* yapıştırır:

![Şekil 3.1: İki zihinsel model. C'de isim kutunun adıdır, atama kopyalar. Python'da isim nesneye yapıştırılmış bir etikettir; atama etiket ekler, nesneyi kopyalamaz.](gorseller/b03_name_object.png)

C gözlüğüyle bakarsan Python'daki her isim aslında bir işaretçidir — ama aritmetiği olmayan, `*`'sız, `&`'siz, dilin senin yerine yönettiği bir işaretçi. Bu benzetme sana iki soruyu bedavaya cevaplatır: "İki isim aynı nesneyi mi gösteriyor?" sorusunun operatörü `is`'tir (C'deki adres karşılaştırması gibi); "İçerikleri eşit mi?" sorusununki `==`'dir:

```python
a = [1, 2, 3]
b = a          # ikinci etiket, aynı nesne
c = [1, 2, 3]  # AYRI nesne, içeriği aynı

print(a == c)  # True  — içerik eşit
print(a is c)  # False — farklı nesneler
print(a is b)  # True  — aynı nesnenin iki adı
```

Her nesnenin bir kimliği vardır; `id(nesne)` sana CPython'da nesnenin *bellek adresini* verir — C'deki `&x`'in torunu. `is`, iki ismin `id`'lerini karşılaştırmanın kısaltmasıdır.

::: not
CPython, -5 ile 256 arasındaki küçük tam sayıları her seferinde yeni nesne yaratmak yerine önceden hazırlar ve paylaşır. Bu yüzden `x = 100` ve `y = 100` için `x is y` genelde True, `x = 1000` ve `y = 1000` için ise çoğu zaman False çıkar. Bu bir uygulama ayrıntısıdır, dilin garantisi değildir; sayıları `is` ile karşılaştırmak bu yüzden tuzaktır. Değer karşılaştırması için `==` kullan.
:::

### Değişmez ve değişebilir: nesnenin karakteri

Etiket modelinin üstüne Python ikinci bir ayrım koyar: nesne **değişmez (immutable)** mi, **değişebilir (mutable)** mi? Sayılar, stringler ve tuple'lar değişmezdir — "değerini değiştirmek" aslında *yeni nesne yaratıp etiketi taşımaktır*. Listeler, sözlükler, kümeler değişebilirdir — nesnenin *içi* yerinde değişir, tüm etiketler değişikliği görür.

| Tür | Değişebilir mi? | C'deki en yakın akraba |
|---|---|---|
| `int`, `float`, `bool` | Hayır | değer türleri |
| `str` | Hayır | `const char*` (salt-okunur string) |
| `tuple` | Hayır | `const` struct/dizi |
| `list` | Evet | dinamik dizi (Örnek 2.3'teki gibi) |
| `dict` | Evet | hash tablosu (Bölüm 9'da kuracağız) |
| `set` | Evet | üyelik odaklı hash tablosu |

`x = x + 1` bile artık farklı okunuyor: int değişmez olduğundan bu satır 43 değerli *yeni* bir nesne yaratır ve `x` etiketini oraya taşır. C'deki "kutunun içini güncelle" değil, "etiketi başka kutuya as."

## 3.3 Aliasing: kopya sandığın etiket

Şimdi bu modelin ısırdığı yere gelelim — Python'a C'den geçen herkesin bir kez düştüğü çukur. Bir listeyi "yedeklediğini" sanıp aynı nesneye ikinci etiket verirsin:

```python
notlar = [70, 85, 90]
yedek = notlar          # kopya DEĞİL: takma ad (alias)

notlar.append(55)
print(yedek)            # [70, 85, 90, 55] — "yedek" de değişti!
```

![Şekil 3.2: Takma ad tuzağı. `b = a` aynı liste nesnesine ikinci etikettir; `b.append(4)`'ü `a` da görür. Gerçek yedek istiyorsan yeni nesne yaratmalısın: `c = a.copy()`.](gorseller/b03_aliasing.png)

Gerçek kopya istiyorsan bunu *açıkça* söylersin: `yedek = notlar.copy()` (ya da eşdeğeri `notlar[:]`). İç içe listelerde bir katman daha var: `copy()` **sığ (shallow)** kopyadır, içteki listelerin kendisini değil etiketlerini kopyalar; tamamen bağımsız kopya için `copy.deepcopy()` gerekir. Kural şu: *"kopyaladım" diyorsan hangi derinlikte kopyaladığını söyleyebiliyor olmalısın.*

Aynı mekanizma fonksiyon çağrılarını da yönetir. Python'da parametre geçişi, C'deki gibi "değer mi adres mi?" diye ikiye ayrılmaz; **her zaman etiket kopyalanır** (nesne değil). Sonuç, C sezgisiyle şaşırtıcı derecede tanıdık: değişebilir nesneyi fonksiyon içinde değiştirirsen çağıran görür (işaretçi geçirmiş gibi), değişmez nesneye yeni değer atarsan görmez (yerel etiketi taşımış olursun):

```python
def ekle(liste):
    liste.append(99)     # nesnenin İÇİNİ değiştirir → dışarısı görür

def sifirla(sayi):
    sayi = 0            # etiketi YENİ nesneye taşır → dışarısı görmez

veriler = [1, 2]
x = 42
ekle(veriler)            # veriler: [1, 2, 99]
sifirla(x)               # x: hâlâ 42
```

::: ipucu
Kafan karıştığında tek soru sor: *"Bu satır nesnenin içini mi değiştiriyor, yoksa bir etiketi mi taşıyor?"* `liste[0] = 5`, `liste.append(...)`, `sozluk["k"] = v` içi değiştirir; `isim = baska_sey` daima etiket taşır. Bu tek ayrım, Python'daki "gizemli" davranışların yüzde doksanını çözer.
:::

## 3.4 free() nerede? Bellek yönetiminin devri

Bölüm 2'de `malloc` sözleşmesinin üç ihlalini ezberledin: sızıntı, sarkan işaretçi, çifte serbest bırakma. Python'da bu üçlünün adı bile geçmez, çünkü `free()` senin işin değil artık. Peki kim yapıyor? **Referans sayacı.**

CPython'da her nesne, kendisine kaç etiketin (referansın) bağlı olduğunu sayar. Etiket eklenince sayaç artar, etiket kopunca (`del`, kapsamdan çıkma, yeniden atama) azalır. Sayaç sıfıra düştüğü an nesne *anında* yok edilir ve belleği geri verilir:

![Şekil 3.3: Referans sayacının yaşam döngüsü. Nesneye bağlı her isim sayacı artırır; isimler koptukça azalır; sıfırda bellek anında geri verilir. C'deki `free` çağrısının yerini bu mekanizma alır.](gorseller/b03_refcount.png)

Bir de yedek mekanizma var: iki nesne birbirini gösterirse (döngüsel referans) sayaçlar hiç sıfıra inmez; bu tür adaları arada bir tarayıp temizleyen **çöp toplayıcı (garbage collector)** devrededir. İkisinin toplamı sana şu konforu verir: Python'da bellek sızıntısı *istisna*, C'de *varsayılan tehlikedir*.

Bedava değil elbette. Her nesnenin yanında sayaç taşımak bellek ister; sayacı her atamada güncellemek zaman ister; çöp toplayıcının araya girmesi gecikme yaratabilir. `MertOS` çekirdeği ya da bir füzenin uçuş kontrol döngüsü gibi *deterministik* zamanlama isteyen yerlerde bu belirsizlik kabul edilemez — gömülü dünyanın C'de kalmasının bir sebebi de budur. Ayrıca bu sayaç, Bölüm 53'te tanışacağın meşhur GIL kısıtının da perde arkasındaki oyuncusudur.

## 3.5 Koleksiyonlar: C'deki emeklerin hazır hâli

Bölüm 2'de dinamik büyüyen diziyi elle kurdun (Örnek 3: `realloc`, kapasite katlama). Python'un `list`'i tam olarak o yapının fabrikadan çıkmış hâlidir — arkada C ile yazılmış, kapasitesini kendi büyüten bir dizi. `append` çağırdığında senin `realloc` mantığın çalışıyor; bu bölümün Kod Okuma egzersizinde bunu CPython kaynağında bizzat göreceksin.

Bir farkla: C dizisi *değerleri* bitişik tutar, Python listesi *referansları* bitişik tutar; elemanların kendileri dağınık nesnelerdir:

![Şekil 3.4: Aynı dört sayı, iki düzen. C dizisinde değerler yan yanadır (16 bayt, cache dostu). Python listesinde yan yana olan şey referanslardır; her `int` ayrı bir nesnedir. Esneklik bundan gelir, sayısal yavaşlık da — numpy'ın var olma sebebi (Bölüm 48).](gorseller/b03_list_internals.png)

Bu yüzden liste her türden eleman karıştırabilir (`[1, "iki", 3.0]`) ama bir milyon float üstünde aritmetik yaparken berbat bir tercihtir — her eleman için ayrı nesne, ayrı dolaylılık. ML dünyasının `numpy` dizileri, işte bu resmi yeniden C düzenine (bitişik ham değerler) çevirir; Bölüm 48 ve 64'te sürekli elinin altında olacak.

Gündelik kullanımda dört koleksiyonun iş bölümü net:

```python
kuyruk   = [3, 1, 4]                  # list : sıralı, değişebilir
nokta    = (4.0, 2.5)                 # tuple: sıralı, DEĞİŞMEZ
ogrenci  = {"ad": "Mert", "no": 361}  # dict : anahtar → değer
harfler  = {"a", "b", "a"}        # set  : tekrarsız ({'a','b'})

print(ogrenci["ad"])              # dict: anahtarla, indeksle değil
```

İkisi özel ilgiyi hak ediyor. **`tuple`**, "bu veri paketi değişmeyecek" sözleşmesidir — koordinat, RGB üçlüsü, fonksiyondan çoklu dönüş (`return x, y` aslında tuple döndürür). **`dict`** ise Python'un gizli kahramanı: arka planda bir hash tablosudur, aramayı-eklemeyi ortalama O(1)'de yapar. C'de bir sayaç tablosu için düşünmen gereken her şeyi — dizi mi, arama mı, çakışma mı — tek satıra indirir. Bu sihrin içini Bölüm 9'da açacağız; şimdilik güçlü bir kullanıcı ol.

String'ler de C günlerine göre lükse kavuştu ama bir huyunu unutma: **değişmezler**. `s[0] = 'X'` yok; her "değişiklik" yeni string üretir. Biçimleme işinin modern aracı f-string'dir:

```python
ad, ort = "Mert", 3.42
print(f"{ad} ortalama: {ort:.2f}")   # Mert ortalama: 3.42
```

C'nin `printf("%s ortalama: %.2f", ...)` biçimlendirmesinin torunudur — `%.2f`'teki hassasiyet sözdiziminin f-string'de `:.2f` olarak yaşadığına dikkat.

## 3.6 Akış ve fonksiyonlar: küçük ama keskin farklar

Kontrol yapıları tanıdık gelecek; farklar ayrıntıda. **Süslü parantez yok, girinti bloktur** — C'de stil olan şey Python'da sözdizimidir, yanlış girinti yanlış program demektir. **`for` bir sayaç döngüsü değil, gezinme döngüsüdür**: C'deki `for (i = 0; i < n; i++)` kalıbının Python'daki dengi, koleksiyonun *kendisi* üstünde yürümektir; indeks de lazımsa `enumerate` verir:

```python
adlar = ["Ada", "Turing", "Hopper"]

for ad in adlar:                    # eleman üstünde gez
    print(ad)

for i, ad in enumerate(adlar):      # indeks + eleman
    print(i, ad)

for i in range(5):                  # klasik 0..4 sayacı gerekirse
    print(i)
```

Koşullarda da bir Python geleneği var: **doğruluk değeri (truthiness)**. Boş koleksiyon, boş string, `0` ve `None` koşulda "yanlış" sayılır; `if liste:` yazımı "liste boş değilse" okunur. `NULL` kontrolünün Python'daki akrabası `if x is None:` kalıbıdır — `None` tektir, `is` ile sorulur.

Fonksiyon tarafında `def` ile tanım, isteğe bağlı parametreler ve isimle çağırma C'ye göre ciddi konfor:

```python
def selamla(ad, unvan="Müh."):      # varsayılan değer
    return f"Merhaba, {unvan} {ad}"

selamla("Mert")                     # Merhaba, Müh. Mert
selamla("Mert", unvan="Dr.")        # isimli argüman
```

Ama varsayılan değerlerin bir tuzağı var ve bu, klasik mülakat sorusudur: **varsayılan değer, fonksiyon her çağrıldığında değil, tanımlandığında BİR KEZ yaratılır.** Değişebilir bir varsayılan koyarsan, tüm çağrılar aynı nesneyi paylaşır:

```python
def ekle_hatali(eleman, liste=[]):   # [] SADECE BİR KEZ yaratılır!
    liste.append(eleman)
    return liste

ekle_hatali(1)    # [1]
ekle_hatali(2)    # [1, 2]  — sürpriz: önceki çağrının izi duruyor

def ekle_dogru(eleman, liste=None):  # doğru kalıp
    if liste is None:
        liste = []                   # her çağrıda taze nesne
    liste.append(eleman)
    return liste
```

Şekil 3.2'nin diliyle: tüm çağrılar aynı liste nesnesine etiket alıyor. Aliasing'i anlayan için sürpriz değil, kaçınılmaz sonuç.

::: dikkat
Python değişken *tanımlamaz*, ilk atamada yaratır. `toplam += 1` yazıp `toplam`'ı hiç başlatmadıysan `NameError` alırsın; ama daha sinsisi, yazım hatasıdır: `topalm = 5` yeni bir değişken yaratır, derleyici yok ki uyarsın. Bu dilin bedeli budur; panzehiri Bölüm 39'daki testler ve modern editörlerin statik denetimidir.
:::

## 3.7 Comprehension ve generator: veriyi akıtmak

Şimdi Python'u Python yapan aletlere geldik. C'de "bir diziden yeni dizi türet" işi dört satır döngüdür; Python bunu tek satırlık bir ifadeye sıkıştırır — **liste comprehension**:

```python
notlar = [70, 85, 90, 55, 100]

gecenler = [n for n in notlar if n >= 60]        # süz
dortluk  = [n / 25 for n in notlar]              # 100'lük → 4'lük
ciftler  = [(i, n) for i, n in enumerate(notlar)]
```

Okunuşu matematikteki küme gösterimidir: "*notlardaki her n için, n ≥ 60 ise, n'lerden liste*". Sözlük ve küme sürümleri de aynı kalıptır: `{ad: len(ad) for ad in adlar}`. Kural: tek bir süz/dönüştür fikri → comprehension; iç içe koşullu karmaşa → klasik döngü. Tek satıra üç fikir sıkıştıran comprehension, zekâ değil borç göstergesidir.

Comprehension'ın bir sınırı var: sonucun *tamamını* bellekte kurar. Beş eleman için dert değil; ama `ÖZCE`'nin eğitim verisi gibi milyonlarca satırlık bir kaynağı işlerken "önce hepsini belleğe koy" stratejisi seni duvara toslatır. Çözüm, Python'un en zarif fikirlerinden biri: **generator** — değerleri *istendikçe* üreten, duraklatılabilir fonksiyon:

```python
def kareler(n):
    for x in range(n):
        yield x * x          # değeri teslim et ve BURADA DURAKLA

uretec = kareler(1_000_000)  # hiçbir şey hesaplanmadı henüz!
print(next(uretec))          # 0  — ilk değere kadar çalıştı, durdu
print(next(uretec))          # 1  — kaldığı yerden devam etti

for k in kareler(5):         # for, next()'i senin yerine çağırır
    print(k)                 # 0 1 4 9 16
```

`yield`, `return`'ün duraklamalı kardeşidir: değeri verir ama çerçeveyi yıkmaz; fonksiyonun tüm yerel durumu dondurulur, bir sonraki `next()` kaldığı satırdan devam eder. Bölüm 1'in stack çerçevesi modeliyle düşünürsen: `return` çerçeveyi atar, `yield` buzdolabına kaldırır.

![Şekil 3.5: Aynı hesap, iki bellek profili. Liste comprehension tüm değerleri aynı anda bellekte kurar; generator (parantezli sürüm ya da `yield`'li fonksiyon) her `next()` çağrısında TEK değer üretir. Milyonlarca elemanda fark GB'larla ölçülür.](gorseller/b03_generator.png)

Köşeli parantezi normal paranteze çevirmek bile yeter: `(x*x for x in ...)` bir generator ifadesidir. `sum`, `max`, `any` gibi tüketiciler generator'la doğrudan çalışır: `sum(x*x for x in range(10**7))` koca listeyi hiç kurmadan toplar. Bu "akıtarak işleme" zihniyeti, Bölüm 54'te veri hattı (pipeline) kurarken ekmek kapın olacak.

## 3.8 Decorator ve context manager: sarmak ve garantilemek

Son iki alet, Python'da fonksiyonların da birer *nesne* olduğu gerçeğinin meyveleri. Fonksiyonu değişkene atayabilir, parametre olarak geçirebilir, fonksiyondan fonksiyon döndürebilirsin. Bu kapıdan giren ilk kalıp: bir fonksiyonu, davranışına ek yapan başka bir fonksiyonla **sarmak**.

Diyelim `ÖZCE`'de hangi fonksiyonun ne kadar sürdüğünü merak ediyorsun. Her fonksiyonun içine saat koymak yerine, saati bir kez yazıp istediğin fonksiyona yapıştırırsın — **decorator** tam olarak budur:

```python
import time
import functools

def zamanla(fonk):                        # fonksiyon ALIR
    @functools.wraps(fonk)                # ismini/dokümanını koru
    def sarici(*args, **kwargs):          # her türlü argümanı geçir
        t0 = time.perf_counter()
        sonuc = fonk(*args, **kwargs)     # asıl işi yap
        sure = time.perf_counter() - t0
        print(f"{fonk.__name__}: {sure:.4f} sn")
        return sonuc
    return sarici                         # sarılmış fonksiyon DÖNER

@zamanla                                  # kodla = zamanla(kodla)
def kodla(veri):
    return [b ^ 0x5A for b in veri]

kodla(bytes(range(256)))                  # kodla: 0.0001 sn
```

`@zamanla` satırı sözdizimsel şekerdir; `kodla = zamanla(kodla)` demenin kibar yolu. `*args, **kwargs` ikilisi "gelen bütün argümanları olduğu gibi taşı" kalıbıdır — sarıcının her imzaya uymasını sağlar. Bu deseni framework'lerde sürekli göreceksin: Flask'ın `@app.route`'u, pytest'in `@fixture`'ı, PyTorch'ta `@torch.no_grad()` hep aynı fikir. (Bölüm 22'de bunun nesne yönelimli akrabası Decorator Pattern ile tanışacaksın.)

İkinci alet bir C yarasına merhem. Bölüm 2'de her `malloc`'a `free`, her `fopen`'a `fclose` borcun vardı ve erken `return` bu borcu unutturuyordu. Python'un **context manager**'ı bu garantiyi dilin içine gömer:

```python
with open("veri.txt", encoding="utf-8") as dosya:
    icerik = dosya.read()
    # blok biterken dosya KAPANIR — hata fırlasa bile

print(dosya.closed)   # True
```

`with` bloğu bir sözleşmedir: girerken kurulum (`__enter__`), çıkarken — normal bitişte de, istisna fırlarken de — temizlik (`__exit__`) *garantiyle* çalışır. C++'çıların RAII dediği fikrin Python hâlidir. Dosyalar, kilitler, ağ bağlantıları, veritabanı oturumları: "aç-kullan-kapat" gördüğün her yerde `with` kullan. Kendin de yazabilirsin; Kendin Yap 2'de `Zamanlayici` context manager'ını kuracaksın.

## 3.9 Hatalar: istisna mekanizması

C'de hata yönetimi bir *görgü kuralıydı*: fonksiyon `-1` ya da `NULL` döndürür, çağıran kontrol eder — etmezse sessiz felaket. Python bu sözleşmeyi dilin çekirdeğine gömer: bir şey ters gittiğinde fonksiyon dönüş değerine hata sıkıştırmaz, **istisna (exception) fırlatır** ve normal akış o an durur.

İstisnanın yolculuğunu Bölüm 1-2'nin stack çerçeveleriyle düşün — çünkü mekanizma tam olarak orada işler:

![Şekil 3.6: İstisnanın çağrı yığınında tırmanışı. `int("abc")` ValueError doğurur; ara fonksiyon yakalamıyorsa kontrol çerçeve çerçeve yukarı sarar; ilk uygun `except` bloğunda yakalanır. Hiç yakalanmazsa program traceback basarak düşer.](gorseller/b03_exception.png)

Yakalama sözdizimi dört parçalıdır ve her parçanın net bir görevi vardır:

```python
def yas_oku():
    try:
        metin = input("Yaş: ")
        yas = int(metin)              # ValueError fırlatabilir
    except ValueError:
        print(f"'{metin}' bir sayı değil")
        return None
    else:
        return yas                    # yalnız HATASIZ yolda çalışır
    finally:
        print("(deneme kaydedildi)")  # HER durumda çalışır
```

`try` şüpheli bölgeyi işaretler; `except TürAdı` yalnız o hata türünü yakalar (birden çok `except` yazılabilir); `else` "hata çıkmadıysa" dalıdır; `finally` ne olursa olsun çalışır — 3.8'deki `with`'in temizlik garantisi, aslında bu bloğun kurumsallaşmış hâlidir. Kendi hatanı fırlatmak da tek kelime: `raise ValueError("oran 0-1 arasında olmalı")` — kütüphane yazarken sözleşme ihlallerini böyle duyurursun.

Bu mekanizma iki felsefe doğurur ve Python'un tercihi nettir. **LBYL** (Look Before You Leap — atlamadan önce bak): her şeyi önceden kontrol et; C'nin tarzı. **EAFP** (Easier to Ask Forgiveness than Permission — izin yerine af dile): dene, olmazsa yakala; Python'un tarzı. Sözlükte anahtar ararken `if "k" in d: v = d["k"]` yerine `try: v = d["k"] except KeyError:` yazmak, anahtar çoğunlukla varsa Python'da hem hızlı hem kısadır. Ama anahtar sık yoksa her eksik anahtar bir istisna fırlatıp yakalamak demektir ve bu maliyetlidir; o durumda `d.get("k")` ya da `if "k" in d` daha uygundur. İkisini de tanı; hangi dilde hangisinin *deyim* olduğunu bil.

::: dikkat
Çıplak `except:` (tür belirtmeden) yazma — `Ctrl+C`'yi, yazım hatası `NameError`'ını, her şeyi yutar ve hatayı *gizler*. Yakalayacağın türü bil, bilmiyorsan en azından `except Exception as e:` deyip `e`'yi logla. "Sessizce yut ve devam et", hata yönetiminin en pahalı anti-desenidir; Bölüm 6'da bunun enkaz kaldırma maliyetini göreceğiz.
:::

## 3.10 Dilimleme ve string atölyesi

Python'da diziliş türlerinin (str, list, tuple) ortak süper gücü **dilimleme (slicing)**: `s[başla:bitir:adım]` sözdizimiyle alt parça almak. Kuralları iki görselle mühürlenir:

![Şekil 3.7: Dilimleme cetveli. İndeksler 0'dan başlar; negatif indeks sondan sayar. `s[1:4]` başlangıcı dahil eder, bitişi HARİÇ tutar — bu yüzden `s[:k] + s[k:]` her zaman bütünü verir. Adım parametresi atlayarak (`::2`) ya da tersten (`::-1`) gezdirir.](gorseller/b03_slicing.png)

"Bitiş hariç" kuralı ilk gün tuhaf gelir, sonra vazgeçilmez olur: `s[:3]` ilk üç eleman, `s[3:]` gerisi, uzunluklar çıkarma ile hesaplanır (`4-1=3` eleman), kesişme-birleşme hatasız olur. Listede dilimleme *yeni liste* üretir — 3.3'teki `notlar[:]` kopyasının açıklaması bu. `ters = s[::-1]` tersten kopyadır; Bölüm 2'de C'yle elle yazdığın `ters_cevir`'in tek karakterlik Python karşılığı.

String tarafında, C'de `<string.h>` ile didiklediğin işlerin gündelik takımı şudur — hepsi *yeni string döndürür* (string değişmezdi, hatırla):

| Metot | İş | Örnek → sonuç |
|---|---|---|
| `split(ayraç)` | parçala → liste | `"a,b,c".split(",")` → `['a','b','c']` |
| `join(liste)` | listeyi birleştir | `"-".join(['a','b'])` → `"a-b"` |
| `strip()` | uçlardaki boşluğu at | `"  x \n".strip()` → `"x"` |
| `replace(e, y)` | değiştir | `"kodek".replace("k","K")` → `"KodeK"` |
| `startswith(p)` | önek testi | `"HATA: x".startswith("HATA")` → `True` |
| `find(p)` | ilk konum (yoksa −1) | `"merhaba".find("ha")` → `3` |

`split`/`join` ikilisi log işleme, CSV ayrıştırma, yol birleştirme gibi işlerin atıdır; Örnek 3'te ikisini istisnalarla birlikte koşturacağız. Bir de sınır bilgisi: metin (`str`) ile ham bayt (`bytes`) ayrı türlerdir. Dosyadan `"rb"` ile okunan şey `bytes`'tır; `veri.decode("utf-8")` metne, `metin.encode("utf-8")` bayta çevirir. Bölüm 1'deki UTF-8 gerçeği burada pratiğe döner — `ÖZCE`'nin kodeği baytlarla, arayüzü metinle konuşur ve ikisinin sınırında hep `encode`/`decode` durur.

## 3.11 Modüller, paketler ve JSON

Kod büyüyünce tek dosya yetmez. Python'da her `.py` dosyası bir **modüldür** ve `import` ile başka dosyadan kullanılır — C'nin başlık+bağlayıcı ikilisinin dertsiz karşılığı:

```python
# arac.py — kendi modülün
def temizle(satir):
    return satir.strip().lower()

if __name__ == "__main__":       # dosya DOĞRUDAN çalıştırılınca
    print(temizle("  DENEME "))  # hızlı el testi buraya

# ana.py — kullanan taraf
import arac
print(arac.temizle(" VeRi "))    # modül_adı.fonksiyon
```

`if __name__ == "__main__":` kalıbı her Python dosyasının altına yazacağın imzadır: dosya `import` edildiğinde bu blok *çalışmaz*, doğrudan `python arac.py` denince çalışır — modül hem kütüphane hem küçük araç olur. `from arac import temizle` yazımı ismi doğrudan getirir; `from arac import *` ise yasak bölgedir (nereden geldiği belirsiz isimlerle dosyayı doldurur).

Kalıcı veri için C'de format icat ediyordun; Python dünyasının ortak dili hazır: **JSON**. Sözlük/liste yapıları JSON'a birebir eşlenir ve `json` modülü çeviriyi tek satır yapar:

```python
import json

kayit = {"ad": "Mert", "no": 361, "notlar": [78, 85, 91]}

with open("kayit.json", "w", encoding="utf-8") as f:
    json.dump(kayit, f, ensure_ascii=False, indent=2)   # yaz

with open("kayit.json", encoding="utf-8") as f:
    geri = json.load(f)                                 # oku
print(geri["notlar"][0])    # 78 — yapı olduğu gibi geri geldi
```

`ensure_ascii=False`, Türkçe karakterlerin `ç` kaçışları yerine okunur yazılmasını sağlar; `indent=2` insan gözü içindir. Bu dört satır, Bölüm 40'ta API'lerin, Bölüm 54'te deney konfigürasyonlarının konuşacağı formatın tamamıdır — `EV Dashboard`'un ayar dosyası da, `ÖZCE`'nin deney çıktısı da JSON'dan şaşmaz.

## 3.12 Sınıflar, dataclass ve tip ipuçları

Şimdiye kadar veriyi sözlüklerde ve listelerde, işi fonksiyonlarda tuttuk. Proje büyüyünce bu ayrım yetmez: bir sensörün ayarları, bir eğitim döngüsünün durumu, bir ağın ağırlıkları, bunları işleyen kodla birlikte taşınmalı. Bu paketleme işini **sınıf (class)** yapar. C'deki en yakın karşılığı `struct`'tır; fark şu: C struct'ı yalnızca veri taşır, Python sınıfı veriyi ve onu değiştiren metotları aynı yerde tutar. Bunun ML'deki karşılığı, Kısım XIV'te göreceğin her model sınıfıdır. Sınıflara bu bölümde kısa bir giriş yapıyoruz; derinlemesine OOP Bölüm 20'de.

Sınıf bir *şablondur*; ondan üretilen her nesne (instance) kendi verisini taşır. `class Sayac:` yazıp `s = Sayac()` dediğinde, Bölüm 3.2'deki modelde bellekte bir nesne yaratılır ve `s` etiketi ona yapışır:

```python
class Sayac:
    def __init__(self, baslangic=0):   # kurucu: nesne doğarken
        self.deger = baslangic         # veriyi nesneye bağla

    def artir(self):                   # metot: self ilk parametre
        self.deger += 1
        return self.deger

s = Sayac()
print(s.artir(), s.artir())            # 1 2
t = Sayac(10)                          # ayrı nesne, ayrı deger
print(t.artir())                       # 11
```

İki kavramı netleştirelim. `self`, C'de gizli bir parametre değildir ama aynı işi görür: `s.artir()` çağrısı arka planda `Sayac.artir(s)` demektir. Yani `self`, metodun üzerinde çalıştığı nesnenin etiketidir; C'de `struct Sayac *self` alıp `self->deger++` yazmanın Python'daki karşılığı. `__init__` ise nesneyi *başlatır*; nesneyi yaratan aslında `__new__`'dur, ama günlük kodda onunla işin olmaz. `__` ile başlayıp biten metotlara (dunder metot) Python'un kendisi kanca atar: `print` `__str__`'i, `for` `__iter__`'i, `==` `__eq__`'yu çağırır.

Veri taşıyan sınıfların çoğu aynı üç şeyi elle yazar: kurucu, yazdırma (`__repr__`) ve karşılaştırma (`__eq__`). `@dataclass` süsleyicisi bunları senin yerine üretir:

```python
from dataclasses import dataclass

@dataclass
class Ogrenci:
    ad: str                  # tip ipucu: alan adı ve türü
    no: int
    ort: float = 0.0         # varsayılan değer

o = Ogrenci("Mert", 361)
print(o)                     # Ogrenci(ad='Mert', no=361, ort=0.0)
print(o == Ogrenci("Mert", 361))   # True: içerik eşit
```

Yukarıdaki `ad: str` yazımı bir **tip ipucudur (type hint)**. Python dinamik tipli bir dildir; Bölüm 3.6'daki gibi yanlış tipli bir değer ancak çalışırken patlar. İpuçları bunu önlemez, ama kodu okunur kılar ve araçların kontrol etmesini sağlar (mypy gibi statik denetleyiciler ve editörün kendi denetimi):

```python
def selamla(ad: str, yas: int = 0) -> str:
    return f"{ad} ({yas})"

print(selamla("Mert", 22))   # Mert (22)
print(selamla(5))            # hata yok: ipuçları zorlamaz
```

İkinci satır çalışır; bu yüzden ipuçlarını bir güvence değil, bir belge ve kontrol kancası olarak düşün. ML kodunda `torch.Tensor` gibi ipuçlarını sık göreceksin; C'deki tip sistemi kadar sert değildir, ama nedenini bilmek okunabilirliği ciddi artırır.

Kütüphane kurmadan önce **sanal ortam (virtual environment)** kurmak alışkanlık olmalı. Her proje kendi paketlerini ayrı bir klasörde tutar; böylece iki projenin farklı sürümlü `numpy`'si birbirini ezmez. Windows PowerShell'de sıra şöyle:

```term
$ python -m venv .venv
$ .venv\Scripts\Activate.ps1
$ pip install numpy
```

Linux ve WSL'de aktivasyon `source .venv/bin/activate` ile yapılır; ortamdan çıkmak için `deactivate` yazarsın. `pip install` yalnızca aktif ortamın içine kurar; prompt'un başında ortam adını görmeden kurulum yapma.

Şimdi `for` döngüsünün altındaki sözleşmeye bakalım. Bir `for` koleksiyonu nasıl gezer? İki metot işin içindedir. `iter(nesne)` bir **iterator** ister ve nesnenin `__iter__` metodunu çağırır. Sonra her turda `__next__` çağrılarak bir sonraki değer alınır; değer kalmayınca `StopIteration` fırlatılır ve döngü sessizce biter. Bunu elle yazınca mekanizma görünür hâle gelir:

```python
class GeriSay:
    def __init__(self, n):
        self.n = n

    def __iter__(self):              # kendisi iterator: kendini döner
        return self

    def __next__(self):
        if self.n == 0:
            raise StopIteration      # "daha değer yok" sinyali
        self.n -= 1
        return self.n + 1

for k in GeriSay(3):
    print(k)                         # 3 2 1
```

Bölüm 3.7'deki generator bu sözleşmeyi senin yerine otomatik yazar: içinde `yield` olan bir fonksiyon, `__iter__` ve `__next__`'li bir iterator döndürür. Dosya nesnesi de aynı sözleşmeye uyar; `for satir in dosya` dediğinde her tur bir satır istenir.

ML'de bu sınıf düşüncesini her gün kullanacaksın. PyTorch'ta bir sinir ağı, `torch.nn.Module`'den miras alan bir sınıftır: ağırlıklar `__init__` içinde nesnenin verisi olarak tutulur, ileri geçiş `forward` metodunda yazılır. Ağı `ag(x)` diye çağırdığında Python'un çağrılabilir-nesne sözleşmesi (`__call__`) devreye girer ve `forward`'ı çağırır:

```python
import torch
import torch.nn as nn

class KucukAg(nn.Module):             # miras: nn.Module'den
    def __init__(self):
        super().__init__()            # ata sınıfı kur
        self.dogrusal = nn.Linear(4, 1)

    def forward(self, x):             # ileri geçiş
        return self.dogrusal(x)

ag = KucukAg()
cikti = ag(torch.randn(2, 4))         # 2 örnek, 4 özellik
```

Gördüğün gibi: veri (ağırlıklar) nesnenin içinde, davranış (`forward`) sınıfın metodunda. Bölüm 57'de bu iskeleti sıfırdan kuracağız; o zaman `forward`'ı kendi elinle yazacaksın.

## Çözümlü Örnekler

### Örnek 1 (★): Takas ve kopya — iki dilin aynası

**Adım 1 — Anla.** (a) C'de üç satır + işaretçi isteyen takası Python'da yaz. (b) Şu kodun çıktısını *çalıştırmadan* söyle:

```python
a = [1, 2]
b = a
b = b + [3]        # dikkat: append DEĞİL
print(a, b)
```

**Adım 2 — Örnekle.** (a) için somut bir çift al: `x = 3`, `y = 7`. Takastan sonra `x` 7, `y` 3 olmalı. (b) için bir kâğıda iki etiket (`a`, `b`) ve bunların gösterdiği nesneleri çiz; her satırda hangi etiketin nereye baktığını izle.

**Adım 3 — Kaba çöz.** (a) için C'deki yöntem: `gecici = x; x = y; y = gecici`. Doğru, ama Python'da gereksiz. (b) için ilk sezgi "`b` değişti, demek `a` de değişti" olabilir; bu sezgi kontrol edilmeden kabul edilmez.

**Adım 4 — Örüntü.** Çoklu atamada sağ taraf önce tek bir değer olarak kurulur, sonra sol tarafa açılır; geçici değişkene gerek kalmaz. (b)'de sorulacak tek soru 3.3'ün sorusudur: *bu satır nesnenin içini mi değiştiriyor, yoksa bir etiketi mi taşıyor?* `+` yeni bir nesne üretir; `b = ...` yalnız etiketi taşır.

**Adım 5 — İyileştir.** Takas tek satırdır; sağdaki `(y, x)` tuple'ı kurulur ve sola açılır:

```python
x, y = 3, 7
x, y = y, x        # sağdaki (y, x) tuple'ı kurulur, sola açılır
print(x, y)        # 7 3
```

**Adım 6 — Doğrula.** Takas için elle iz sürmek:

| Satır | x | y |
|---|---|---|
| `x, y = 3, 7` | 3 | 7 |
| sağ taraf `(y, x)` kurulur: `(7, 3)` | 3 | 7 |
| sola açılır | 7 | 3 |
| `print(x, y)` | 7 | 3 |

(b) için aynı izi, her satırda etiketlerin gösterdiği nesneyle tut:

| Satır | `a` gösterir | `b` gösterir | Nesneler |
|---|---|---|---|
| `a = [1, 2]` | O1 | — | O1 = [1, 2] |
| `b = a` | O1 | O1 | O1 iki etiketle paylaşılır |
| `b + [3]` | O1 | O1 | O2 = [1, 2, 3] yaratılır |
| `b = b + [3]` etiketi O2'ye taşır | O1 | O2 | O1 değişmedi |
| `print(a, b)` | [1, 2] | [1, 2, 3] | — |

(b)'nin çıktısı: `[1, 2] [1, 2, 3]`. Eğer `b = b + [3]` yerine `b.append(3)` yazılsaydı çıktı `[1, 2, 3] [1, 2, 3]` olurdu — `append` içi değiştirir, `+` yeni nesne kurar.

**Bunu AI'sız yazabilir misin?** Aynı soruyu `b += [3]` için cevapla, sonra REPL'de doğrula. (İpucu: `+=` listelerde `append` ailesindendir — sürpriz tam da burada.)

### Örnek 2 (★★): Kelime frekansı — dict'in gücü

**Adım 1 — Anla.** Bir metindeki kelimelerin kaçar kez geçtiğini say ve en sık üçünü yazdır. (Bölüm 2'nin gözüyle bak: C'de bu iş struct dizisi + arama + elle büyütme demekti.)

**Adım 2 — Örnekle.** Elle küçük bir metin al: `ozce kodek kodek` içinde `kodek` 2, `ozce` 1 kez geçer. Doğru program çıktıda önce `kodek`'i, adının yanında 2 sayısıyla yazmalı. Sayaç tablosunu kâğıda yazarak ilerle.

**Adım 3 — Kaba çöz.** Her kelime için tüm listeyi baştan taramak: `kelimeler.count(k)`. Bu çalışır, ama her kelime için listeyi yeniden okur; metin uzadıkça iş hızla büyür.

**Adım 4 — Örüntü.** "Varsa artır, yoksa 1 ile başlat" kalıbı her sayma probleminde aynıdır; anahtardan değere eşleme, tam da `dict`'in işidir. `dict.get(anahtar, varsayilan)` bu kalıbı tek satır yapar. Sıralama için `sorted`'a "neye göre?" sorusunun cevabını `key` fonksiyonuyla veririm: değere (sayıya) göre, büyükten küçüğe.

**Adım 5 — İyileştir.** Tek geçişli sayaç ve `key` ile sıralama:

```python
metin = ("ozce kodek veriyi sıkıştırır kodek veriyi "
         "kanala verir kanal veriyi tasir")

sayac = {}
for kelime in metin.split():             # boşluklardan böl
    sayac[kelime] = sayac.get(kelime, 0) + 1

siralamali = sorted(sayac.items(),       # (kelime, adet) çiftleri
                    key=lambda cift: cift[1],
                    reverse=True)

for kelime, adet in siralamali[:3]:
    print(f"{kelime:10} {adet}")
```

**Adım 6 — Doğrula.** Metni kelimelere böl ve her adımda sayacın o anki değerini yaz:

| Sıra | kelime | sayacın o andaki değeri |
|---|---|---|
| 1 | ozce | 1 |
| 2 | kodek | 1 |
| 3 | veriyi | 1 |
| 4 | sıkıştırır | 1 |
| 5 | kodek | 2 |
| 6 | veriyi | 2 |
| 7 | kanala | 1 |
| 8 | verir | 1 |
| 9 | kanal | 1 |
| 10 | veriyi | 3 |
| 11 | tasir | 1 |

Sonuç: `veriyi` 3, `kodek` 2, `ozce` 1 ve kalan 1'likler. `sorted(..., reverse=True)` eşit anahtarların göreli sırasını korur, bu yüzden 1'lik kelimeler arasında ilk eklenen `ozce` üçüncü olur. Beklenen çıktı programın çıktısıyla birebir aynıdır:

```term
$ python3 frekans.py
veriyi     3
kodek      2
ozce       1
```

**Açıklama:** Programın kalbi iki satır: `split` metni kelime listesine çevirir, `get(kelime, 0) + 1` sayacı günceller. `lambda cift: cift[1]`, "çiftin ikinci elemanına bak" diyen isimsiz mini fonksiyondur — `sorted`'ın `key` parametresi 3.8'deki "fonksiyon da bir değerdir" fikrinin gündelik hâli. C'deki emeği hatırla: burada üç kavram (dict, sorted, lambda) elli satırlık işi dokuza indirdi. Konfor katmanı tam olarak bu; altında hâlâ Bölüm 9'un hash tablosu dönüyor.

**Bunu AI'sız yazabilir misin?** Boş dosyada, noktalama işaretlerini de temizleyerek (`"kodek,"` ile `"kodek"` aynı sayılsın) yeniden yaz. Hangi string metodunu seçtin, neden?

### Örnek 3 (★★): Sağlam CSV → JSON dönüştürücü

**Adım 1 — Anla.** `ogrenciler.csv` dosyasında `ad,no,ort` satırları var ama dosya kirli: boş satırlar, eksik alanlı satırlar, sayı olmayan notlar. Programı düşürmeden geçerli kayıtları `ogrenciler.json`'a yaz; bozuk satırları satır numarasıyla raporla.

**Adım 2 — Örnekle.** Önce kirli bir dosyayı gözünde canlandır. Örnek `ogrenciler.csv` şöyle olsun:

```term
$ cat ogrenciler.csv
Ali,101,72.5
Ayse,abc,80

Mert,361,88
Deniz,102
Zeynep,103,91.0
```

Altı satırın üçü geçerli (1, 4, 6). Satır 2'de not sayı değil, satır 5'te alan eksik; satır 3 boş. Boş satır bozukluk sayılmaz, normal bir durumdur.

**Adım 3 — Kaba çöz.** Her satırı `split` et, alan sayısını `if len(...) != 3` ile kontrol et, sonra `int` ve `float` çevrimlerini `if` ile tek tek doğrula. Çalışır; ama her hatayı ayrı bir `if` ile önceden tahmin etmek zorundasın ve bir kontrolü unuttuğunda program çöker.

**Adım 4 — Örüntü.** Alan sayısı yanlışsa ve sayı çevrilemiyorsa, ikisi de `ValueError` olarak ortaya çıkar. Yani "hatayı önceden kontrol et" yerine "çevir, olmazsa yakala" (EAFP) kalıbıyla tek bir `try` bloğu iki kontrolü birden görür. Satır numarası için `enumerate(f, start=1)`: dosya nesnesi zaten satır satır gezilir (Bölüm 3.10'daki `split`, 3.9'daki `try`, 3.11'deki `json` burada buluşur).

**Adım 5 — İyileştir.** Geçerli kayıtları sözlük listesine koy, bozuk satırların numarasını ayrı tut ve sonunda JSON'a dök:

```python
import json

kayitlar, bozuk = [], []

with open("ogrenciler.csv", encoding="utf-8") as f:
    for no, satir in enumerate(f, start=1):
        satir = satir.strip()
        if not satir:                      # boş satır: sessizce geç
            continue
        parcalar = satir.split(",")
        try:
            ad, num, ort = parcalar       # 3 alan yoksa ValueError
            kayitlar.append({
                "ad":  ad.strip(),
                "no":  int(num),          # sayı değilse ValueError
                "ort": float(ort),
            })
        except ValueError:
            bozuk.append(no)          # tek yakalama, iki hata türü

with open("ogrenciler.json", "w", encoding="utf-8") as f:
    json.dump(kayitlar, f, ensure_ascii=False, indent=2)

print(f"{len(kayitlar)} kayıt yazıldı; bozuk satırlar: {bozuk}")
```

**Adım 6 — Doğrula.** Örnek dosyanın her satırını kodun nasıl işlediğini elle izle:

| Satır | Ham içerik | Sonuç | `kayitlar` adedi | `bozuk` |
|---|---|---|---|---|
| 1 | `Ali,101,72.5` | 3 alan, sayılar çevrilir: kayıt | 1 | [] |
| 2 | `Ayse,abc,80` | `int("abc")` ValueError: bozuk | 1 | [2] |
| 3 | (boş) | `strip` sonrası boş: geçilir | 1 | [2] |
| 4 | `Mert,361,88` | kayıt | 2 | [2] |
| 5 | `Deniz,102` | 2 alan, paketi açarken ValueError: bozuk | 2 | [2, 5] |
| 6 | `Zeynep,103,91.0` | kayıt | 3 | [2, 5] |

İz, programın çıktısını birebir verir:

```term
$ python3 donustur.py
3 kayıt yazıldı; bozuk satırlar: [2, 5]
```

**Açıklama:** Kodun zarafeti `ad, num, ort = parcalar` satırında: liste 3 elemanlı değilse Python kendiliğinden `ValueError` fırlatır — uzunluk kontrolünü `if len(...) != 3` ile yazmak yerine istisnaya devrettik (EAFP). Aynı `except`, `int("abc")` çevrim hatasını da yakalar: iki ayrı hata kaynağı, tek toparlanma noktası. `continue` ile boş satırı *hata saymadığımıza* dikkat — neyin hata, neyin normal olduğu tasarım kararıdır ve raporda dürüstçe ayrılır.

**Bunu AI'sız yazabilir misin?** Aynı aracı ters yönde yaz: JSON'u okuyup CSV'ye dök. Hangi adımda istisna beklersin, hangi adımda beklemezsin — ve neden?

### Örnek 4 (★★★): Generator hattı — sabit bellekle akış işleme

**Adım 1 — Anla.** `EV Dashboard`'un hız sensöründen milyonlarca satırlık kayıt aktığını düşün (`zaman,hiz` biçiminde). Tüm kaydı belleğe almadan: geçersiz satırları ele, hızları çıkar, 100 km/s üstü ihlallerin sayısını ve en yükseğini bul.

**Adım 2 — Örnekle.** Akan verinin küçük bir kesiti `hiz_kaydi.csv` olsun:

```term
$ cat hiz_kaydi.csv
08:00:00,72.5
08:00:01,104.0
08:00:02,abc
08:00:03,130.5

08:00:05
08:00:06,99.9
```

Yedi satırın dördü hız taşıyan geçerli satırlar (1, 2, 4, 7). Satır 3'te hız sayı değil, satır 5 boş, satır 6'da tek alan var. İhlal olanlar 100'ün üstündeki 104.0 ve 130.5'tir.

**Adım 3 — Kaba çöz.** Dosyayı `readlines()` ile tek seferde listeye al, sonra iki döngüyle işle: önce hızları bir listeye çevir, sonra ihlalleri say. Doğru sonucu verir; ama milyonlarca satırda tüm veri bellekte iki kez durur ve akış sensörü için en kötü seçimdir.

**Adım 4 — Örüntü.** Her aşama bir öncekinden bir değer ister ve kendi değerini teslim eder. Bu, Unix boru hattına (`cat | grep | wc`) benzeyen bir akış desenidir ve generator ile birebir kurulur: kaynak → ayrıştır → süz → tüket. Kimse ara liste kurmaz; bellekte her an tek satır vardır.

**Adım 5 — İyileştir.** Üç generator'ü zincirleyen hat:

```python
def hizlar(satirlar):
    """'zaman,hiz' satırlarından hız üretir; bozukları atlar."""
    for satir in satirlar:
        parcalar = satir.strip().split(",")
        if len(parcalar) != 2:
            continue                     # bozuk satır: sessizce atla
        try:
            yield float(parcalar[1])     # tek tek teslim et
        except ValueError:
            continue                     # sayı değilse atla

def ihlaller(hiz_akisi, limit=100.0):
    for h in hiz_akisi:
        if h > limit:
            yield h

with open("hiz_kaydi.csv", encoding="utf-8") as dosya:
    adet, en_yuksek = 0, 0.0
    for h in ihlaller(hizlar(dosya)):    # zincir: dosya → hız → ihlal
        adet += 1
        en_yuksek = max(en_yuksek, h)

print(f"{adet} ihlal, en yüksek {en_yuksek:.1f} km/s")
```

**Adım 6 — Doğrula.** Örnek dosyanın her satırını zincirden elle geçir. Sütunlar: `hizlar` ne üretti, `ihlaller` neyi geçirdi, sayaçların durumu:

| Satır | `hizlar` üretti | `ihlaller` geçirdi | `adet` | `en_yuksek` |
|---|---|---|---|---|
| 1 `72.5` | 72.5 | hayır (100'ün altında) | 0 | 0.0 |
| 2 `104.0` | 104.0 | evet | 1 | 104.0 |
| 3 `abc` | yok (float hatası, atlanır) | — | 1 | 104.0 |
| 4 `130.5` | 130.5 | evet | 2 | 130.5 |
| 5 (boş) | yok (tek parça, atlanır) | — | 2 | 130.5 |
| 6 `08:00:05` | yok (tek parça, atlanır) | — | 2 | 130.5 |
| 7 `99.9` | 99.9 | hayır | 2 | 130.5 |

İz, programın çıktısını verir:

```term
$ python3 ihlal.py
2 ihlal, en yüksek 130.5 km/s
```

**Açıklama:** Bu programın bellek kullanımı dosya 1 GB da olsa değişmez: her an uçuşta olan şey *tek satır ve tek float*. `for h in ihlaller(hizlar(dosya))` satırı üç generator'ü zincirler; en dıştaki `for` her turda `next` ister, istek zincirde geriye doğru dalgalanır. Dosya nesnesinin kendisi de zaten satır satır gezilen bir iterator'dür; zincirin başını o oluşturur. Hata yönetimi de akışın içinde: bozuk satır tüm işi çökertmek yerine atlanıyor (hangi durumda hangisinin doğru olduğu Bölüm 6'nın konusu). `with` bloğu sayesinde dosya, işin sonunda garanti kapanıyor.

**Bunu AI'sız yazabilir misin?** Zincire "hareketli ortalama" halkası ekle: son 5 hızın ortalamasını üreten bir generator. Hangi durumu (state) tutman gerekiyor ve nerede?

## Kendin Yap Projeleri

::: dikkat
Kural aynı: yapay zekâ araçları **yasak**. Bu iki proje, C'den Python'a taşındığını kendi ellerinle kanıtlaman için.
:::

### Proje 1 (★★): Kayıt sistemini Python'a taşı

**Amaç:** Bölüm 2 Proje 2'deki öğrenci kayıt sistemini (ekle / listele / ara / çık) Python'la yeniden yaz ve iki deneyimi karşılaştır.

**Beklenen davranış:** Aynı menü, aynı işlevler. Kayıt `dict` olarak (`{"ad": ..., "no": ..., "ort": ...}`), kayıtlar listede. Kapasite, `realloc`, `free` — hiçbiri yok; onların yerini ne aldığını *fark etmen* projenin asıl çıktısı.

**Önerilen yaklaşım:** Menü döngüsü `while True` + `match` ya da if zinciri. Numarayla aramayı önce döngüyle yaz, sonra tek satır comprehension/`next` ile. Bitirince 10 satırlık bir "göç raporu" yaz: C sürümünde olup burada kaybolan üç dert, Python sürümünde dikkat etmen gereken iki yeni tuzak (ipucu: aliasing, yazım hatası değişkeni).

**Başarı kriterleri:** 1000 kayıt sorunsuz; olmayan numara aranınca çökme yok; isimde boşluk destekleniyor; kod 80 satırın altında ve `input` dışında global durum yok.

### Proje 2 (★★★): Kendi @zamanla ve Zamanlayici'ni yaz

**Amaç:** 3.8'deki iki aleti sıfırdan, bakmadan kur: fonksiyonları ölçen bir `@zamanla` decorator'ü ve `with Zamanlayici("etiket"):` biçiminde kullanılan bir context manager sınıfı.

**Beklenen davranış:** Decorator, sarılan fonksiyonun adını ve süresini basmalı; dönüş değerini bozmamalı; her imzayla çalışmalı. Context manager, bloğun süresini ölçmeli ve blok içinde istisna fırlasa bile süreyi raporlamalı.

**Önerilen yaklaşım:** Decorator için Örnek yapısını hatırla ama kopyalama: önce `*args, **kwargs`'sız naif sürümü yaz, tek argümanlı fonksiyonda çalıştır, sonra genelleştir. Context manager için `__enter__` ve `__exit__(self, tur, deger, iz)` metotlu bir sınıf kur; `__exit__`'in dönüş değerinin istisnayı yutup yutmadığını deneyerek keşfet.

**Başarı kriterleri:** `@zamanla` üç farklı imzalı fonksiyonda doğru; `functools.wraps` kullanılmış (`__name__` korunuyor); `with Zamanlayici(...)` içinde `1/0` yazınca süre yine raporlanıyor ve istisna kaybolmuyor; ikisini iç içe kullanınca çıktılar tutarlı.

### Ek Alıştırmalar

Aşağıdaki problemler cevapsız. Önce çözümünü kâğıda yaz, sonra bilgisayara geç. Zorluk etiketi kabaca sıralıdır; sırayla gitmek zorunda değilsin.

1. **★** (aliasing) `m = [[0] * 3] * 3` yazıp `m[0][1] = 5` dersen hangi satırlar değişir ve neden? Aynı ölçüde kısa ama istediğin kurulumu nasıl yaparsın?
2. **★** (dict) Bir dizide uzunluğunun yarısından fazla geçen eleman varsa onu bul, yoksa `None` döndür. Dizi yalnız bir kez taransın. (Klasik mülakat: Majority Element.)
3. **★★** (dict) `iki_toplam(sayilar, hedef)` fonksiyonu, toplamı `hedef` eden iki farklı indeks döndürsün. Beklenen zaman karmaşıklığı O(n). (Klasik mülakat: Two Sum.)
4. **★** (comprehension) Bir matrisin (liste listesi) satırlarını sütun yapan transpozu tek bir liste comprehension ile yaz. Satır uzunlukları eşit değilse ne olur?
5. **★★** (comprehension) Bir cümledeki tekrarlanan kelimeleri ilk görüldükleri sırayla ayıkla. Bunu yalnız liste comprehension ile yapmak mümkün mü, yoksa yardımcı bir yapıya ihtiyaç var mı? Neden?
6. **★★** (generator) Sonsuz Fibonacci üreten bir generator yaz; `itertools` kullanmadan ilk `n` terimi alan bir fonksiyon da yaz. Bellek kullanımı `n`'den bağımsız olmalı.
7. **★★** (generator) Keyfi derinlikte iç içe listeyi (`[1, [2, [3, 4]], 5]`) düzleştiren bir generator yaz. `yield from` kullan. (Klasik mülakat: Flatten Nested List.)
8. **★★** (decorator) Argümanlarına göre sonucu önbelleğe alan bir `@onbellek` decorator'ü yaz. Naif özyinelemeli `fib(50)` pratikte bitmez; önbellekli sürüm anında dönmeli. (Klasik mülakat: Memoization.)
9. **★★★** (decorator) `@yeniden_dene(n=3)` gibi parametre alan bir decorator yaz: istisna fırlatan fonksiyonu en fazla `n` kez yeniden denesin; hepsi başarısız olursa son istisnayı yeniden fırlatsın. Neden üç katmanlı iç içe fonksiyon gerektiğini açıkla.
10. **★★** (context manager) `with cd("/yol"):` biçiminde çalışan, çalışma dizinini blok boyunca değiştirip çıkışta eski dizine dönen bir context manager yaz. Hem sınıf (`__enter__`/`__exit__`) hem `@contextmanager` sürümünü dene; bloğun içinde istisna fırlatınca ne olduğunu kontrol et.
11. **★★★** (sınıf) Kapasiteli bir LRU önbelleği sınıfı yaz: `get(anahtar)` ve `put(anahtar, deger)` ikisi de O(1) olsun; kapasite dolunca en uzun süredir kullanılmayan kayıt atılsın. (Klasik mülakat: LRU Cache.)
12. **★★** (sınıf) `Nokta` sınıfında `__eq__` tanımlayıp `__hash__`'i tanımlamazsan `{Nokta(1, 2)}` yazınca ne olur? Sebebini açıkla ve Bölüm 3.5'teki tuple gerekçesiyle karşılaştırarak bu sınıfı dict anahtarı yapmanın yolunu anlat.

## Kod Okuma Egzersizi

Bu bölümün kapanışı, iki dünyayı tek karede birleştiriyor. Aşağıdaki kesit, CPython 3.12.10'un `Objects/listobject.c` dosyasındaki `list_resize` fonksiyonundan alınmıştır; Python `list`'inin gerçek implementasyonudur ve `append` yer kalmayınca bu fonksiyon çağrılır. Kesit sadeleştirilmiştir: hızlı yol (`allocated >= newsize` kontrolü, ona bağlı `allocated` değişkeni) ile taşma korumasının satırları çıkarılmıştır. Boyut güncellemesi ve büyüme hesabı aynen korunmuştur:

```c
static int
list_resize(PyListObject *self, Py_ssize_t newsize)
{
    PyObject **items;
    size_t new_allocated, num_allocated_bytes;

    /* hızlı yol atlandı: allocated >= newsize ise realloc yok */

    new_allocated = ((size_t)newsize + (newsize >> 3) + 6)
                    & ~(size_t)3;
    if (newsize - Py_SIZE(self)
        > (Py_ssize_t)(new_allocated - newsize))
        new_allocated = ((size_t)newsize + 3) & ~(size_t)3;
    if (newsize == 0)
        new_allocated = 0;

    num_allocated_bytes = new_allocated * sizeof(PyObject *);
    items = (PyObject **)PyMem_Realloc(self->ob_item,
                                       num_allocated_bytes);
    if (items == NULL) {
        PyErr_NoMemory();
        return -1;
    }
    Py_SET_SIZE(self, newsize);
    self->ob_item = items;
    self->allocated = new_allocated;
    return 0;
}
```

Bölüm 2'de `realloc`'la kapasite katlayan sen, bu kodu okuyabilecek tek şeye sahipsin: bağlam. `PyObject **` dizisi Şekil 3.4'teki "referanslar bitişik" resminin ta kendisi; `PyMem_Realloc` senin `realloc`'unun kurumsal ağabeyi.

**Sorular — cevaplamadan geçme:**

- `newsize >> 3` ne hesaplar (Bölüm 1'deki kaydırmaları hatırla) ve bu, "kapasiteyi ikiye katla" stratejinden nasıl farklı? Yüzde kaç büyüme demek?
- `& ~(size_t)3` maskesi sonucu neye yuvarlar? `~3`'ün bit deseni ne? (Bölüm 1'in Kod Okuma'sındaki `CLR` makrosuyla aynı aile.)
- `+ 6` sabiti olmasaydı `newsize = 1` için `(1 + 0) & ~3` ne verirdi? Küçük listelerde bu sabitin rolü ne?
- `PyMem_Realloc` `NULL` dönerse eski blok ne oluyor ve bu kod Bölüm 2 Örnek 4'teki hangi kurala harfiyen uyuyor?
- Python %12,5 büyürken senin C örneğin %100 büyüyordu. İki tercihenin bellek/zaman ödünleşimini bir cümleyle karşılaştır.

## Bölüm Özeti

Bu bölümde Python'u C'nin üstüne, fark fark inşa ettik:

- **CPython bir C programıdır**: kodun bytecode'a çevrilir, sanal makinede yorumlanır. REPL deney hızı verir; bedeli çalışma-zamanı hataları ve saf döngü yavaşlığıdır.
- **İsim = etiket, nesne = kutu.** Atama kopyalamaz, etiket taşır. `==` içeriği, `is` kimliği sorar. Nesneler değişmez (int, str, tuple) ya da değişebilir (list, dict, set) karakterdedir.
- **Aliasing**, kopya sanılan paylaşımdır; gerçek kopya `copy()`/`deepcopy()` ile *açıkça* istenir. Fonksiyona geçen şey daima etiket kopyasıdır: içi değiştiren görünür, etiketi taşıyan görünmez.
- **`free` yok**: referans sayacı sıfırlanan nesne anında, döngüsel adalar çöp toplayıcıyla temizlenir. Konforun bedeli bellek/zaman yükü ve deterministik olmayan gecikmedir — gömülünün C'de kalma sebebi.
- **`list` = senin yazdığın dinamik dizinin hazır hâli** (ama referans dizisi); `dict` = O(1) hash tablosu; `tuple` = değişmezlik sözleşmesi. Sayısal yoğun iş numpy'ın bitişik dünyasına gider.
- **Varsayılan argüman tanımda bir kez yaratılır** — değişebilir varsayılan koyma; `None` kalıbını kullan.
- **Comprehension** süz/dönüştürü tek ifadeye indirir; **generator** (`yield`) değerleri istendikçe üretir, GB'lık akışı KB'lık bellekle işler.
- **Decorator** fonksiyonu fonksiyonla sarar (`@`), **context manager** (`with`) kurulum-temizlik garantisi verir — `fclose` borcunun dildeki çözümü.
- **İstisnalar** hata yönetimini dönüş kodundan mekanizmaya çevirir: `try/except/else/finally`, `raise`, çağrı yığınında tırmanış. Python'un deyimi EAFP'dir; çıplak `except:` yasaktır.
- **Dilimleme** `[başla:bitir:adım]` — bitiş hariç; listede yeni nesne (kopya), `[::-1]` tersten. String atölyesi: `split/join/strip/replace`; `str` ↔ `bytes` sınırında `encode/decode` (UTF-8).
- **Her `.py` bir modüldür**: `import`, `__name__ == "__main__"` kalıbı; kalıcı yapısal veri için `json.dump/load`.

**Sonraki bölümde:** Diller tamam; şimdi tezgâhı kuruyoruz. Terminalde yaşamayı, `gcc`'nin dört aşamasını, `gdb` ile hata avlamayı, Makefile ve git'i — yani bir mühendisin günlük aletlerini öğreneceksin: **Bölüm 4 — Terminal & Araçlar**.

::: mulakat
Klasik sorular — hemen cevaplamaya çalışma, her birini birkaç dakika düşün:

1. `a == b` doğruyken `a is b` yanlış olabilir mi? Tersi? Birer örnek ver.
2. `def f(x, liste=[])` imzası neden hatalıdır ve doğru kalıp nedir?
3. `list` ile `tuple` arasında seçim yaparken hangi soruları sorarsın? `tuple` neden dict anahtarı olabilirken `list` olamaz? (İpucu: değişmezlik + Bölüm 9.)
4. Generator ile liste döndüren fonksiyon arasındaki farkı bellek ve "yeniden gezilebilirlik" açısından anlat.
5. `with open(...)` bloğu, `try/finally` ile elle yazılmış eşdeğerinden neden daha güvenlidir? `__exit__` ne zaman çalışır?
6. EAFP ile LBYL'yi bir örnekle karşılaştır. `try/except KeyError` ile `if key in d` arasında hangi durumda gerçek bir davranış farkı doğar?
7. `s[:3] + s[3:]` neden her zaman `s`'ye eşittir? Dilimlemenin "bitiş hariç" kuralı bunu nasıl garanti eder?
:::
