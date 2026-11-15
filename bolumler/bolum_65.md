%% kisim_no: XV
%% kisim_ad: Derin Öğrenme
%% bolum_no: 65
%% baslik: PyTorch Derinlemesine

## Giriş: Bir kütüphane değil, bir hesaplama modeli

Bölüm 63'te bir sinir ağını sıfırdan, yalnızca NumPy ile yazdık. Her katmanın ileri ve geri adımını elle türetip kodladık. Bölüm 55'te ise kendi otomatik türev motorumuzu, yani `Deger` sınıfını kurduk. O iki bölüm bize bir şey kazandırdı: PyTorch'a baktığımızda "bu sihirli kutu ne yapıyor?" diye sormak yerine, "bu satır hangi kuralı uyguluyor?" diye sorabiliyoruz.

PyTorch, derin öğrenme alanında en yaygın kullanılan çatılardan biridir. Araştırma makalelerinin büyük kısmı, savunma sanayiinde ve endüstride ML ekiplerinin ürettiği modellerin çoğu bunun üstünde yazılır. Bir mülakatta "bir modeli eğitirken GPU neden boşta bekliyor?", "`model.eval()` ne yapar?" ya da "bu hatanın nedeni gradyan birikimi mi?" gibi sorular geldiğinde, cevap PyTorch'un içindeki somut mekanizmalara dayanır. Bu bölüm o mekanizmaları gösterir.

Bir İHA görüntü işleme hattında modelin eğitimi bir gün sürebilir. Eğitim kesilirse, bu bir gün başa dönmemelidir; checkpoint bunun için vardır (Bölüm 65.10). Eğitim sürerken GPU'nun yüzde 30'da çalışması, veri yükleyicinin yavaş olduğunu gösterebilir (Bölüm 65.8). Ya da iki farklı çalıştırma farklı sonuç veriyorsa, bu bir tekrarlanabilirlik sorunudur (Bölüm 65.14). Savunma sanayiinde bu üç soru, bir modelin sahada güvenilir olup olmadığını belirler.

Bölümün ana fikri şudur: PyTorch'ta her şey üç kavramın etrafında döner. Birincisi **tensör**, yani bellekte düz bir dizi üzerine kurulu çok boyutlu bir görünümdür. İkincisi **autograd**, yani işlemleri kaydeden ve gradyanları geri yayan dinamik bir hesap grafiğidir. Üçüncüsü **nn.Module**, yani parametreleri, alt modülleri ve durumu bir arada tutan bir kaptır. Bu üçü anlaşıldığında, veri hattı, karışık hassasiyet, bellek ve dağıtım gibi konular birer uygulama ayrıntısına dönüşür.

Bölümdeki her deney, RTX 3060 Laptop GPU (6 GB) üzerinde PyTorch 2.6.0+cu124 ile çalıştırıldı. GPU süreleri ısınma koşusundan sonra ve `torch.cuda.synchronize` ile ölçüldü. Ölçümler makineye bağlıdır; kitaptaki sayıları birebir tutturmak zorunda değilsin, ama her ölçümü kendi makinende yeniden yapabilirsin. Çıktıların ve kodların tamamı arşivdedir.

::: not
Bu bölümde gösterilen her deney sabit tohumla çalışır ve çıktısı kitapta birebir verilmiştir. Hız ölçümleri hariç hiçbir sayı makineye bağlı değildir. Hız ölçümlerinde bir uyarı var: bölüm yazılırken aynı GPU'yu başka bir süreç kullandı ve bu sırada alınan tekrar koşular süreleri yaklaşık iki kat artırdı (kart 86 °C'ye kadar ısındı). Bu tekrar koşuların süreleri kitapta kullanılmadı; kitaptaki hız sayıları, GPU'nun boşken alınan ilk ölçümlerden gelir.
:::

## 65.1 Tensör: şekil, veri türü ve aygıt

Tensör, çok boyutlu bir sayı dizisidir. Skaler bir sayı sıfır boyutlu, bir vektör bir boyutlu, bir matris iki boyutlu bir tensördür. Bir görüntü batch'i `(batch, kanal, yükseklik, genişlik)` şeklinde dört boyutludur. Bölüm 48'de matrisleri ve şekil kavramını gördük; PyTorch'un tensörü o matrisin genellemesidir. Aynı şekil kuralları burada da geçerlidir: iki tensörü toplayabilmek için şekillerinin uyumlu olması gerekir.

Her tensörün üç temel özelliği vardır. **Şekil** (`shape`) her boyutun uzunluğunu verir. **Veri türü** (`dtype`) her elemanın bellekte kaç bit tuttuğunu ve nasıl yorumlandığını belirler: `float32`, `float16`, `int64` gibi. **Aygıt** (`device`) tensörün CPU belleğinde mi yoksa GPU belleğinde mi durduğunu söyler. Bu üç özellik, bir tensörle yapılan her işlemin hem doğruluğunu hem de hızını belirler.

Aşağıdaki kod bir tensörün bu üç özelliğini gösterir ve bellek düzeninin bir sonraki bölümde ayrıntılı açıklanacak kısmını ilk kez ortaya koyar.

```python
# t01_tensor.py: dtype, cihaz, şekil, stride, view ve yayınlama.
import torch

x = torch.arange(12, dtype=torch.float32).reshape(3, 4)
print("shape:", tuple(x.shape), "dtype:", x.dtype)
print("device:", x.device, "stride:", x.stride())
print("offset:", x.storage_offset())
print("storage bayt:", x.untyped_storage().nbytes())

ptr = x.untyped_storage().data_ptr()
y = x.t()                      # transpose: veri kopyalanmaz
print("\ny = x.t()  shape:", tuple(y.shape), "stride:", y.stride())
print("aynı storage:", y.untyped_storage().data_ptr() == ptr)
print("y.is_contiguous():", y.is_contiguous())
try:
    y.view(-1)
except RuntimeError as e:
    print("view hatası:", str(e)[:44], "...")
r = y.reshape(-1)              # reshape: gerekirse kopyalar
print("reshape(-1) aynı storage:",
      r.untyped_storage().data_ptr() == ptr)
c = y.contiguous()
print("contiguous stride:", c.stride(),
      "aynı storage:", c.untyped_storage().data_ptr() == ptr)

z = x[1:, ::2]                 # dilimleme: offset ve stride değişir
print("\nx[1:, ::2] shape:", tuple(z.shape), "stride:", z.stride(),
      "offset:", z.storage_offset())

a = torch.zeros(3, 1)
b = torch.arange(4.0)
print("\nyayın (3,1)+(4,) ->", tuple((a + b).shape))
print(a + b)

print("\nfinfo:")
for dt in (torch.float16, torch.bfloat16, torch.float32):
    f = torch.finfo(dt)
    print(f"{str(dt):15s} max={f.max:.4e} eps={f.eps:.4e} "
          f"bit={f.bits}")
```

Bu programın çıktısı şöyledir:

```term
$ python t01_tensor.py
shape: (3, 4) dtype: torch.float32
device: cpu stride: (4, 1)
offset: 0
storage bayt: 48

y = x.t()  shape: (4, 3) stride: (1, 4)
aynı storage: True
y.is_contiguous(): False
view hatası: view size is not compatible with input tenso ...
reshape(-1) aynı storage: False
contiguous stride: (3, 1) aynı storage: False

x[1:, ::2] shape: (2, 2) stride: (4, 2) offset: 4

yayın (3,1)+(4,) -> (3, 4)
tensor([[0., 1., 2., 3.],
        [0., 1., 2., 3.],
        [0., 1., 2., 3.]])

finfo:
torch.float16   max=6.5504e+04 eps=9.7656e-04 bit=16
torch.bfloat16  max=3.3895e+38 eps=7.8125e-03 bit=16
torch.float32   max=3.4028e+38 eps=1.1921e-07 bit=32
```

Çıktıdaki `device: cpu` satırı, tensörün CPU'da olduğunu söyler. Aynı tensörü GPU'ya taşımak için `x.to("cuda")` yazarsın; bunun maliyetini Bölüm 65.4'te ölçeceğiz. Önce bellek düzenini anlamamız gerekiyor, çünkü `view` ile `reshape` arasındaki fark ancak orada anlaşılır.

## 65.2 Bellek düzeni: storage, stride, offset ve view

Bir tensör iki parçadan oluşur: **storage** ve **görünüm** (view). Storage, bellekte düz, tek boyutlu bir bayt dizisidir. Görünüm ise o diziye bakan bir pencerenin tarifidir: şekil, stride (adım) ve offset (başlangıç ofseti). Şekil 65.1 bu ayrımı gösterir.

Stride, bir boyutta bir sonraki elemana geçmek için storage'da kaç adım atlanması gerektiğini söyler. `x = arange(12).reshape(3, 4)` için `stride = (4, 1)`dir: satır değiştirmek için 4 adım, sütun değiştirmek için 1 adım atlanır. Bu, C dilindeki satır-öncelikli (row-major) düzenin ta kendisidir; Bölüm 25'te bellek hiyerarşisi bağlamında gördüğümüz "yan yana duran veriyi okumak ucuzdur" sezgisi burada da geçerlidir.

![Şekil 65.1: Aynı 12 hücrelik storage, x ve x.t() için farklı stride ve adreslerle okunur](gorseller/b65_depolama.png)

Elemanın adresi formülle bulunur: `adres = offset + i·stride0 + j·stride1`. `x` için bu `i·4 + j·1`dir. Transpose (`x.t()`) yeni bir veri kopyalamaz; yalnızca stride'ları değiştirir. `y = x.t()` için stride `(1, 4)` olur ve `y[1, 2]` elemanı `1·1 + 2·4 = 9` adresindedir. Bu adres, `x[2, 1]`in de adresidir; ikisi aynı hücreye bakar. Çıktıdaki `aynı storage: True` satırı bunu doğrular.

Burada önemli bir sonuç çıkar: `y` artık **bitişik (contiguous) değildir**. Bitişik olmak, elemanların storage'da satır-öncelikli sırada, boşluksuz durması demektir. `y`nin elemanları arasında 4 adım, 1 adım, 4 adım gibi boşluklar vardır. Bu yüzden `y.view(-1)` hata verir: `view` yalnızca mevcut stride'larla ifade edilebilen yeni şekillere izin verir ve düzleştirme bu durumda mümkün değildir.

Üç işlem birbiriyle karıştırılır, o yüzden tablo olarak koyuyoruz:

| İşlem | Veriyi kopyalar mı? | Ne yapar |
|---|---|---|
| `view(...)` | Hayır, kesinlikle | Mevcut stride'larla ifade edilebilirse yeni görünüm verir; değilse hata verir |
| `reshape(...)` | Gerekirse | `view` mümkünse onu kullanır, değilse kopyalar |
| `contiguous()` | Bitişik değilse | Elemanları yeni bir storage'a bitişik sırada yazar |
| `x.t()`, `permute` | Hayır | Yalnızca stride ve şekli değiştirir |
| `x[1:, ::2]` | Hayır | Offset ve stride'ları değiştirir, yeni bir pencere açar |

Çıktıdaki `reshape(-1) aynı storage: False` satırı, `reshape`in bu durumda kopya ürettiğini gösterir. Bu bir performans tuzağıdır: `reshape` sessizce bellek ayırır ve kopyalar. Bir sonraki satırdaki `contiguous` de yeni bir storage ayırır (`aynı storage: False`). Şekil değişikliğinden sonra yazılan bir `view` hatası görürsen, çözümün `reshape` ya da `contiguous()` olduğunu ama bunun bir kopya maliyeti taşıdığını bil.

Dilimleme de bir pencere açar. `x[1:, ::2]` için şekil `(2, 2)`, stride `(4, 2)` ve offset `4`tür. Offset, pencerenin storage'da başladığı yerdir: ilk satır atlanmıştır ve `1·4 = 4` adım ileridir. Bu, Bölüm 7'deki dizi indekslemesinin bellek düzeyindeki karşılığıdır.

::: dikkat
`view` ile `reshape` farkını mülakatta sık sorarlar. Doğru cevap "biri her zaman kopyasız, öteki gerekirse kopyalıyor" biçimindedir. Bunu, bir `transpose` sonrasında `view` hatası alarak ve stride'ları yazdırarak kendin göster; ezberlemek yetmez.
:::

## 65.3 Yayın kuralları, yerinde işlemler ve veri türleri

**Yayın (broadcasting)**, farklı şekillerdeki tensörlerin bir işlemde birlikte kullanılabilmesini sağlayan kuraldır. Kuralı NumPy'dan (Bölüm 48 ve Bölüm 56) zaten biliyorsun: sondan başlayarak boyutlar ya eşit olmalı ya da biri 1 olmalıdır. Eksik boyutlar 1 kabul edilir. Çıktıdaki `(3,1) + (4,) -> (3, 4)` satırı bunun örneğidir: `a` her satırda aynı sütunu, `b` her satırda aynı satırı kullanarak 3×4 bir sonuç üretir.

Yayın bellek açısından da önemlidir. Yayınlanan tensör gerçekte kopyalanmaz; stride'ı 0 yapılarak aynı değer tekrar tekrar okunur. Bu yüzden `a.expand(3, 4)` ucuzdur. Ama yayınlanmış bir sonucu yeni bir tensör olarak yazmak, tam boyutlu bir bellek ayırır.

**Yerinde (in-place) işlemler**, sonu adında `_` taşıyan işlemlerdir: `add_`, `relu_`, `mul_` gibi. Bunlar yeni bir tensör ayırmak yerine girdinin üstüne yazar. Bellek tasarrufu sağlarlar, ama autograd ile çatışabilirler. Bunun nedeni şudur: geri yayılım sırasında, ileri geçişte kaydedilen bazı ara değerlere ihtiyaç duyulur. Bir yerinde işlem bu değeri değiştirirse, geri geçiş yanlış bir değerle çalışır. PyTorch bu durumu tespit eder ve hata verir.

Bu hatayı Bölüm 65.5'te autograd bağlamında yeniden göreceğiz. Şimdilik kural şudur: yerinde işlemi yalnızca geri geçişin o değere ihtiyaç duymadığından emin olduğunda kullan.

**Veri türleri** arasındaki fark, neyin temsil edilebildiğini belirler. Bir sayı `float32` olarak yazıldığında yaklaşık yedi ondalık basamak doğrulukla tutulur; `float16`da yaklaşık üç basamaktır. Aralık da farklıdır: `float16`nın en büyük değeri 65504'tür, bu sayıyı aşan bir değer sonsuza (`inf`) taşar. `bfloat16` ise `float32` ile aynı üssü (aralığı) taşır ama yalnızca daha az hassasiyet verir.

`torch.finfo` her veri türünün sınırlarını verir. Çıktıdaki sütunlar şunları söyler: `max` en büyük sonlu değer, `eps` 1'in hemen üstündeki en küçük adımdır (makine epsilonu). `float16`nın `eps` değeri `9,77·10⁻⁴`, `bfloat16`nınki `7,81·10⁻³`tür: `bfloat16` aralıkta `float32` kadar geniş, hassasiyette ise on kat kabadır. Bu fark, karışık hassasiyet eğitiminde (Bölüm 65.12) neden `bfloat16`nın bazı durumlarda `float16`dan güvenli olduğunu açıklar.

Bir uyarı: `float16`nın küçük değerleri de sıfıra yuvarlanabilir. Gradyanlar genellikle küçüktür ve bu alt taşma (underflow) riski taşır; Bölüm 65.12'de bunu gördüğümüzde `GradScaler`ın neden var olduğunu anlayacağız.

::: ipucu
Bir modelde sayısal bir sorun şüphelendiğinde `torch.finfo(dtype)` ile ilk bakacağın yer, o veri türünün sınırlarıdır. Bir `inf` ya da `nan` değeri çoğu zaman aralık dışına taşmadan kaynaklanır.
:::

## 65.4 GPU: kopya maliyeti, çekirdek yükü ve asenkron çalışma

GPU, binlerce küçük çekirdeği aynı anda çalıştırabilen bir işlemcidir. Bu güç, yalnızca iki koşul sağlandığında işe yarar. Birincisi, verinin zaten GPU belleğinde olması ya da kopyanın ucuz olmasıdır. İkincisi, işin yeterince büyük olmasıdır, çünkü her çekirdeği başlatmanın kendi sabit maliyeti vardır. Bu bölümde iki koşulu da ölçeceğiz.

Önce ölçü aracını anlamamız gerekir. Bir PyTorch işlemi, GPU'ya bir çekirdek başlatma komutu gönderip hemen döner. İş GPU'da bitmeden Python devam eder. Bu asenkron çalışma verimlidir, ama zamanlama için tuzaktır: `time.perf_counter()` ile ölçtüğün süre, GPU'nun işini değil, komutun gönderilmesini ölçer. Doğru süre için GPU'nun işinin bittiğini `torch.cuda.synchronize()` ile beklemek gerekir.

Aşağıdaki fonksiyon bu kuralı uygular. Isınma koşusunu çağırır, sonra ölçüm öncesi ve sonrası senkronize eder (senk = True ise).

```python
# g01_matmul.py: CPU ve GPU matris çarpım süresi, boyuta göre.
# Çıktı: engine/veri/b65_matmul.csv. Isınma koşusu ve senkronizasyon.
import csv, os, time
import torch

KOK = "D:/Mevcut Projeler/Kitap/engine/veri"
torch.manual_seed(0)
torch.set_num_threads(os.cpu_count())
dev = torch.device("cuda")

def olc(fn, tekrar, senk):
    # Zamanlama: GPU işi asenkron olduğundan senkronize etmeden
    # süre ölçülmez. Ortalama tekrar üzerinden.
    fn()
    if senk:
        torch.cuda.synchronize()
    t0 = time.perf_counter()
    for _ in range(tekrar):
        fn()
    if senk:
        torch.cuda.synchronize()
    return (time.perf_counter() - t0) / tekrar

satirlar = []
for n in [32, 64, 128, 256, 512, 1024, 2048, 3072]:
    a = torch.randn(n, n)
    b = torch.randn(n, n)
    ag, bg = a.to(dev), b.to(dev)
    tekrar_cpu = max(2, int(2e8 // (2 * n ** 3)) + 1)
    tekrar_gpu = max(5, int(2e9 // (2 * n ** 3)) + 1)
    tcpu = olc(lambda: a @ b, min(tekrar_cpu, 50), False)
    tgpu = olc(lambda: ag @ bg, tekrar_gpu, True)
    # Gerçek hesap: CPU'dan GPU'ya kopya dahil süre.
    tkop = olc(lambda: (a.to(dev) @ bg), tekrar_gpu, True)
    satirlar.append((n, tcpu, tgpu, tkop))
    print("n=%5d  cpu=%10.6f s  gpu=%10.6f s  gpu+kopya=%10.6f s"
          % (n, tcpu, tgpu, tkop))

```

Programın devamı (satır 41–47):

```python
with open(os.path.join(KOK, "b65_matmul.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["n", "cpu_s", "gpu_s", "gpu_kopya_s"])
    for r in satirlar:
        w.writerow([r[0], "%.8f" % r[1], "%.8f" % r[2],
                    "%.8f" % r[3]])
```

Aynı tehlikeyi bir deneyle de görebiliriz. 3072×3072 bir matris çarpımını 20 kez çalıştırıp süreyi iki farklı yöntemle ölçüyoruz: önce senkronizasyon olmadan, sonra bekleyerek. Üçüncü olarak CUDA olayları (event) ile GPU'nun kendi süresine bakıyoruz.

```python
# g02_senkron.py: GPU zamanlaması, senkronizasyon ve kopya maliyeti.
# Çıktı: engine/veri/b65_senkron.csv, engine/veri/b65_kopya.csv
import csv, os, time
import torch

KOK = "D:/Mevcut Projeler/Kitap/engine/veri"
dev = torch.device("cuda")
x = torch.randn(3072, 3072, device=dev)
for _ in range(5):
    y = x @ x
torch.cuda.synchronize()

# 1) Yanlış ölçüm: senkronizasyon yok, çağrı süresi ölçülür.
t0 = time.perf_counter()
for _ in range(20):
    y = x @ x
t_yanlis = (time.perf_counter() - t0) / 20
torch.cuda.synchronize()
t_bitis = (time.perf_counter() - t0) / 20

# 2) Doğru ölçüm: önce ve sonra senkronize et.
torch.cuda.synchronize()
t0 = time.perf_counter()
for _ in range(20):
    y = x @ x
torch.cuda.synchronize()
t_dogru = (time.perf_counter() - t0) / 20

# 3) CUDA event ile GPU'nun kendi süresi.
e1 = torch.cuda.Event(enable_timing=True)
e2 = torch.cuda.Event(enable_timing=True)
e1.record()
for _ in range(20):
    y = x @ x
e2.record()
torch.cuda.synchronize()
t_event = e1.elapsed_time(e2) / 1000 / 20

```

Programın devamı (satır 39–59):

```python
print("yanlış (senkronsuz çağrı):  %.6f s" % t_yanlis)
print("senkron sonrası toplam:     %.6f s" % t_bitis)
print("doğru (synchronize ile):    %.6f s" % t_dogru)
print("CUDA event (GPU süresi):    %.6f s" % t_event)

# 4) Küçük işlemler: her adımda .item() senkronizasyonu.
s = torch.zeros(1, device=dev)
t0 = time.perf_counter()
for _ in range(2000):
    s += 1
torch.cuda.synchronize()
t_toplu = (time.perf_counter() - t0) / 2000
t0 = time.perf_counter()
for _ in range(2000):
    s += 1
    _ = s.item()
t_item = (time.perf_counter() - t0) / 2000
print("\n2000 küçük işlem, adım başına:")
print("  senkronsuz:            %.2f us" % (t_toplu * 1e6))
print("  her adımda .item():    %.2f us" % (t_item * 1e6))

```

Programın devamı (satır 60–99):

```python
# 5) Kopya: sayfalanabilir (pageable) ve pinned bellek.
boyut = [1, 4, 16, 64]
kopya = []
for mb in boyut:
    n = mb * 1024 * 1024 // 4
    h = torch.randn(n)
    hp = h.pin_memory()
    d = torch.empty(n, device=dev)
    def kop(src, nb):
        d.copy_(src, non_blocking=nb)
    for _ in range(3):
        kop(h, False)
    torch.cuda.synchronize()
    r = []
    for src, nb in ((h, False), (hp, True)):
        t0 = time.perf_counter()
        for _ in range(10):
            kop(src, nb)
        torch.cuda.synchronize()
        r.append((time.perf_counter() - t0) / 10)
    kopya.append((mb, r[0], r[1]))
    print("%3d MB  pageable=%.5f s  pinned=%.5f s"
          % (mb, r[0], r[1]))
    print("     GB/s: pageable=%.2f  pinned=%.2f"
          % (mb / 1024 / r[0], mb / 1024 / r[1]))

with open(os.path.join(KOK, "b65_senkron.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["olcum", "sure_s"])
    w.writerow(["yanlis_senkronsuz", "%.8f" % t_yanlis])
    w.writerow(["senkron_sonrasi_toplam", "%.8f" % t_bitis])
    w.writerow(["dogru_synchronize", "%.8f" % t_dogru])
    w.writerow(["cuda_event", "%.8f" % t_event])
with open(os.path.join(KOK, "b65_kopya.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["mb", "pageable_s", "pinned_s"])
    for r in kopya:
        w.writerow([r[0], "%.8f" % r[1], "%.8f" % r[2]])
```

Senkronizasyon olmadan alınan süre, gerçek süreden yaklaşık 157 kat küçüktür. Bu fark, bir GPU kıyaslamasındaki en yaygın hatanın kaynağıdır. Şekil 65.2, aynı deneyi çubuk grafikle gösterir.

![Şekil 65.2: Senkronizasyonsuz ölçüm 0,048 ms gösterir; gerçek GPU süresi 7,5 ms'dir](gorseller/b65_senkron.png)

Çıktı şöyledir:

```term
$ python g02_senkron.py
yanlış (senkronsuz çağrı):  0.000048 s
senkron sonrası toplam:     0.007535 s
doğru (synchronize ile):    0.007569 s
CUDA event (GPU süresi):    0.007573 s

2000 küçük işlem, adım başına:
  senkronsuz:            20.74 us
  her adımda .item():    36.40 us
  1 MB  pageable=0.00013 s  pinned=0.00009 s
     GB/s: pageable=7.58  pinned=11.25
  4 MB  pageable=0.00037 s  pinned=0.00032 s
     GB/s: pageable=10.66  pinned=12.36
 16 MB  pageable=0.00139 s  pinned=0.00125 s
     GB/s: pageable=11.27  pinned=12.49
 64 MB  pageable=0.00561 s  pinned=0.00500 s
     GB/s: pageable=11.14  pinned=12.51
```

Üç doğru ölçüm birbirine yakındır (7,53 – 7,57 ms). Bu, `synchronize` ile beklemenin ve CUDA olaylarının aynı şeyi ölçtüğünü gösterir. Yanlış ölçüm yalnızca Python'un komut gönderme süresini verir.

**Kopya maliyeti.** CPU ile GPU arasındaki veri kopyası PCIe veri yolu üzerinden yapılır. Bu yol, GPU'nun iç bellek bant genişliğinin çok altındadır. Bir tensörü `.to("cuda")` ile taşıdığında bu maliyeti her seferinde ödersin. Kopyanın hızı, kaynak belleğin türüne de bağlıdır. İşletim sistemi sayfalanabilir (pageable) belleği istediği an taşıyabilir, bu yüzden CUDA önce onu kilitli (pinned) bir tampona kopyalar. Kendi belleğinizi `pin_memory()` ile baştan kilitlerseniz bu ara kopya atlanır.

Ölçümümüz bunu doğruluyor. Aşağıdaki tabloda kopya süresi ve bant genişliği (GB/s) boyuta göre verilmiştir.

| Veri (MB) | Sayfalanabilir süre (ms) | Pinned süre (ms) | Sayfalanabilir (GB/s) | Pinned (GB/s) |
|---|---|---|---|---|
| 1 | 0,129 | 0,087 | 7,58 | 11,25 |
| 4 | 0,366 | 0,316 | 10,66 | 12,36 |
| 16 | 1,387 | 1,251 | 11,27 | 12,49 |
| 64 | 5,612 | 4,996 | 11,14 | 12,51 |

Küçük kopyalarda pinned bellek yaklaşık yüzde 30 daha hızlıdır; büyük kopyalarda fark yüzde 10 civarına iner, çünkü her iki yol da PCIe'nin sınırına yaklaşır. Pinned bellek kullanmanın bir bedeli vardır: işletim sistemi bu belleği kilitli tuttuğu için çok fazla ayırmak sistemin genel belleğini daraltır. Bu yüzden yalnızca eğitim veri hattında, sürekli kopyalanan batch tamponları için kullanılır (Bölüm 65.8).

**Matris çarpımı: ne zaman GPU kazanır?** Aşağıdaki ölçüm, kare matrislerin çarpım süresini boyuta göre üç ayrı senaryoda verir: CPU, veri zaten GPU'da olan GPU ve CPU'dan kopya dahil GPU. Matris çarpımı 2n³ işlemdir, yani süre boyutla kübik büyür; bu yüzden grafik log-log ölçeğindedir.

Aşağıdaki çıktı, tablodaki sayıların kaynağıdır (tablo saniyeleri milisaniyeye çevirir).
```term
$ python g01_matmul.py
n=   32  cpu=  0.000017 s  gpu=  0.000026 s  gpu+kopya=  0.000062 s
n=   64  cpu=  0.000018 s  gpu=  0.000032 s  gpu+kopya=  0.000066 s
n=  128  cpu=  0.000038 s  gpu=  0.000031 s  gpu+kopya=  0.000081 s
n=  256  cpu=  0.000099 s  gpu=  0.000034 s  gpu+kopya=  0.000102 s
n=  512  cpu=  0.000569 s  gpu=  0.000062 s  gpu+kopya=  0.000236 s
n= 1024  cpu=  0.003671 s  gpu=  0.000329 s  gpu+kopya=  0.000773 s
n= 2048  cpu=  0.031270 s  gpu=  0.002330 s  gpu+kopya=  0.004097 s
n= 3072  cpu=  0.102774 s  gpu=  0.007494 s  gpu+kopya=  0.010870 s
```

| n | CPU (ms) | GPU (ms) | GPU + kopya (ms) |
|---|---|---|---|
| 32 | 0,017 | 0,026 | 0,062 |
| 128 | 0,038 | 0,031 | 0,081 |
| 512 | 0,569 | 0,062 | 0,236 |
| 1024 | 3,672 | 0,329 | 0,773 |
| 2048 | 31,270 | 2,330 | 4,097 |
| 3072 | 102,774 | 7,494 | 10,870 |

![Şekil 65.3: Matris çarpımı süresi, CPU ve GPU, boyuta göre (log-log)](gorseller/b65_matmul.png)

Tablo üç şey söyler. İlki, `n = 32` gibi küçük boyutta GPU'nun CPU'dan yavaş olmasıdır: 26 µs'lik bir çekirdek başlatma süresi, 17 µs'lik CPU hesabından daha pahalıdır. İkincisi, GPU'nun kendi çalışma süresi `n = 128`de CPU'yu geçer; kopya dahil edildiğinde ise eşitlik `n = 256` civarındadır, `n = 512`de GPU net biçimde kazanır. Üçüncüsü, `n = 3072`de GPU yaklaşık 7,8 TFLOPS (saniyede trilyon işlem) verir, CPU ise 0,57 TFLOPS. Bu oran, veriyi GPU'da tutmanın neden önemli olduğunu gösterir: eğitim sırasında parametreler ve aktivasyonlar zaten GPU'dadır, o yüzden kopya maliyeti tek seferliktir.

**Küçük işlemler.** Matris çarpımında gördüğümüz başlatma yükü, küçük tensörlerde daha belirgindir. Aşağıdaki ölçümde iki tensörü toplayan tek bir işlemin süresini uzunluğa göre veriyoruz (2000 tekrar CPU, 500 tekrar GPU).

Küçük işlem ölçümünün betiği ve çıktısı şöyledir:
```python
# g03_kucuk.py: küçük tensörlerde kernel başlatma yükü (CPU vs GPU).
# Çıktı: engine/veri/b65_kucuk.csv
import csv, os, time
import torch

KOK = "D:/Mevcut Projeler/Kitap/engine/veri"
dev = torch.device("cuda")
satir = []
for n in [1, 64, 1024, 16384, 262144]:
    for ad, d in (("cpu", "cpu"), ("gpu", dev)):
        a = torch.randn(n, device=d)
        b = torch.randn(n, device=d)
        k = 2000 if d == "cpu" else 500
        for _ in range(50):
            c = a + b
        if d != "cpu":
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        for _ in range(k):
            c = a + b
        if d != "cpu":
            torch.cuda.synchronize()
        us = (time.perf_counter() - t0) / k * 1e6
        satir.append((n, ad, us))
        print("n=%7d  %s  %8.2f us/işlem" % (n, ad, us))
with open(os.path.join(KOK, "b65_kucuk.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["n", "aygit", "us_islem"])
    for r in satir:
        w.writerow([r[0], r[1], "%.3f" % r[2]])
```
```term
$ python g03_kucuk.py
n=      1  cpu      1.87 us/işlem
n=      1  gpu     13.83 us/işlem
n=     64  cpu      2.01 us/işlem
n=     64  gpu     14.79 us/işlem
n=   1024  cpu      2.02 us/işlem
n=   1024  gpu     14.73 us/işlem
n=  16384  cpu      4.10 us/işlem
n=  16384  gpu     14.32 us/işlem
n= 262144  cpu     11.84 us/işlem
n= 262144  gpu     16.44 us/işlem
```

| Uzunluk n | CPU (µs/işlem) | GPU (µs/işlem) |
|---|---|---|
| 1 | 1,87 | 13,83 |
| 1024 | 2,02 | 14,73 |
| 16384 | 4,10 | 14,32 |
| 262144 | 11,84 | 16,44 |

Bu tabloda GPU, 262144 uzunluğunda bile CPU'dan yavaştır. Bunun nedeni, bu toplamanın yalnızca birkaç mikro saniyelik gerçek hesap olmasıdır: GPU'ya komut göndermek, Python yorumlayıcısının yükü ve Windows sürücü katmanı, işin kendisinden daha pahalıdır. Küçük işlemlerden oluşan bir döngüyü GPU'ya taşımak, hesabı hızlandırmak yerine yavaşlatabilir. Bu yüzden PyTorch'ta kod yazarken küçük işlemleri birleştirmek (fusion) ve işi büyük tensörler üzerinde toplu yapmak, GPU verimliliğinin temel kuralıdır. Bölüm 65.15'te bu birleştirmeyi `torch.compile` ile nasıl otomatik yaptırabileceğimize bakacağız.

::: dikkat
Bir döngüde her adımda `loss.item()` çağırmak, o adımda GPU'yu bekletir ve asenkron çalışmayı öldürür. Eğitim döngüsünde kaybı yalnızca günlük yazacağın zaman `item()` ile al. Bunun etkisini Çözümlü Örnek 4'te ölçeceğiz.
:::

## 65.5 Autograd: requires_grad, grad_fn ve backward

Bölüm 55'te hesap grafiğini ve geri yayılımı kendi elimizle kurduk. PyTorch'un autograd'ı aynı fikri, çok daha geniş bir tensör dünyasında uygular. Farkı iki yerde görürsün: PyTorch grafiği **her çalıştırmada yeniden** kurar (buna tanımla-çalıştır, define-by-run denir), ve grafiği tensör üzerinde, operatör düzeyinde tutar. Bu yüzden bir `if` ya da döngü içeren normal Python kodu da türevlenebilir.

Bir tensörün gradyan takibi `requires_grad=True` ile başlar. Bu bayrağı taşıyan bir tensörle yapılan her işlem, sonucu bir **grad_fn** düğümüne bağlar. Bu düğüm, o işlemin geri adımını bilir. Aşağıdaki program, `f = tanh((a·b + a)/10)` ifadesinin grafiğini kurar ve düğüm zincirini yazdırır.

```python
# t02_autograd.py: requires_grad, grad_fn, birikim, no_grad, detach.
import torch

a = torch.tensor(2.0, requires_grad=True)
b = torch.tensor(3.0, requires_grad=True)
c = a * b + a
f = torch.tanh(c / 10)
print("f =", round(f.item(), 6))
print("f.grad_fn:", type(f.grad_fn).__name__)
print("f.grad_fn.next_functions:")
print("  ", [type(n).__name__ for n, _ in f.grad_fn.next_functions])
print("c.grad_fn:", type(c.grad_fn).__name__)
print("a.is_leaf:", a.is_leaf, " c.is_leaf:", c.is_leaf)

f.backward()
print("\nbirinci geçiş: a.grad =", round(a.grad.item(), 6),
      " b.grad =", round(b.grad.item(), 6))

# Birikim: zero_grad olmadan ikinci backward gradyanı toplar.
(a * b).sum().backward()
print("ikinci geçiş (sıfırlamadan): a.grad =",
      round(a.grad.item(), 6))
a.grad = None
b.grad = None
(a * b).sum().backward()
print("sıfırlandıktan sonra:        a.grad =", a.grad.item())

# Yaprak olmayan tensör: grad varsayılan olarak doldurulmaz.
u = a * 2
(u ** 2).sum().backward()
print("\nyaprak olmayan u.is_leaf:", u.is_leaf)
u2 = a * 2
u2.retain_grad()
(u2 ** 2).sum().backward()
print("retain_grad sonrası u2.grad:", u2.grad.item())

```

Programın devamı (satır 37–51):

```python
# no_grad ve detach: gradyan izi kesilir.
with torch.no_grad():
    d = a * b
print("\nno_grad içinde requires_grad:", d.requires_grad)
e = (a * b).detach()
print("detach requires_grad:", e.requires_grad)

# In-place çatışması: geri adımın ihtiyaç duyduğu çıktı değişti.
p = torch.tensor([1.0, 2.0], requires_grad=True)
q = p.sigmoid()
q.add_(1.0)
try:
    q.sum().backward()
except RuntimeError as err:
    print("\nin-place hatası:", str(err)[:44], "...")
```

Çıktının ilk kısmı şöyledir:

```term
$ python t02_autograd.py
f = 0.664037
f.grad_fn: TanhBackward0
f.grad_fn.next_functions:
   ['DivBackward0']
c.grad_fn: AddBackward0
a.is_leaf: True  c.is_leaf: False

birinci geçiş: a.grad = 0.223622  b.grad = 0.111811
ikinci geçiş (sıfırlamadan): a.grad = 3.223622
sıfırlandıktan sonra:        a.grad = 3.0

yaprak olmayan u.is_leaf: False
retain_grad sonrası u2.grad: 8.0

no_grad içinde requires_grad: False
detach requires_grad: False

in-place hatası: one of the variables needed for gradient com ...
```

Bu çıktıda üç şey önemlidir. `a` ve `b` **yapraktır** (leaf): onları sen yarattın ve grafik onlardan başlar. `c` ve `f` yaprak değildir; onlar işlemlerin sonucudur. `f.grad_fn` zinciri, `TanhBackward0 → DivBackward0 → AddBackward0 → ...` diye geriye doğru gider. Bu zincir Şekil 65.4'te aynı grafik olarak görülüyor: siyah oklar ileri değer akışını, bordo oklar `backward()` ile gradyanın geri akışını gösterir.

![Şekil 65.4: f = tanh((a·b + a)/10) için hesap grafiği ve grad_fn düğümleri](gorseller/b65_grad_grafi.png)

Gradyanları elle kontrol edelim. `c = 8`, `c/10 = 0,8` ve `tanh(0,8) = 0,664037`. Zincir kuralıyla `df/da = (1 − tanh²(0,8)) · (1/10) · (b + 1) = 0,559055 · 0,1 · 4 = 0,223622`. Çıktıdaki değer tam olarak budur. `df/db = (1 − tanh²) · (1/10) · a = 0,559055 · 0,2 = 0,111811`, o da çıktıyla eşleşiyor. Programın bulduğu değerlerle elle hesabımız aynıdır; bu, grafiğin doğru kurulduğunun ilk kanıtıdır.

**Gradyan birikimi.** Bölüm 55'te `+=` ile birikimin önemini gördük. PyTorch'ta `backward()` her çağrıda gradyanları **üzerine ekler**. Bu, tasarım gereğidir: bir mini-batch'in gradyanını birkaç parça hâlinde toplamak (Bölüm 65.11) ya da RNN'lerde zamanla yayılan gradyanı biriktirmek için gereklidir. Ama her eğitim adımından önce gradyanları sıfırlamazsan, model bir önceki adımın gradyanıyla güncellenir. Çıktıdaki birikim satırları bunu gösterir.

İlk geçişte `a.grad = 0,223622` idi. İkinci geçiş `a·b`nin gradyanı olan `b = 3`ü ekledi: `0,223622 + 3 = 3,223622`. Sıfırladıktan sonra yalnızca `b = 3` kalır. Bu neden `zero_grad()` çağırmak zorunda olduğunu açıklar. Eğitim döngüsünde bunu her adımın başında yaparız (Bölüm 65.9). `optimizer.zero_grad(set_to_none=True)` varsayılan olarak gradyanları `None` yapar; bu da bellek ve hız açısından `0` yazmaktan biraz daha ucuzdur.

**Yaprak olmayan tensörler.** Aşağıdaki kod, bir ara tensörün gradyanına ne olduğunu gösterir.

Yaprak olmayan `u`nun gradyanı, PyTorch tarafından bellek tasarrufu için **saklanmaz**. `u.grad` erişimi bir uyarı üretir: "Bu tensör yaprak değildir; gradyanı doldurulmaz. `retain_grad()` kullanın." Bu yüzden `u.grad`e bakmayı bu bölümde bilerek atladık. `u2.retain_grad()` ile gradyanı saklatabilirsin. Değer `d(u²)/du = 2u = 2·(2a) = 8` ile tutar, çünkü `a = 2` ve `u = 4`. Ara gradyanları görmek hata ayıklamada değerlidir, ama her ara tensör için açmak bellek tüketir.

**no_grad ve detach.** Gradyan takibini kesmenin iki yolu vardır. `torch.no_grad()` bloğu içindeki işlemler grafiğe hiç eklenmez; değerlendirme ve tahmin sırasında kullanılır. `detach()` ise tek bir tensörü grafikten koparır ama aynı bellek üzerinde bir görünüm döndürür. Çıktı `False` değerlerini gösterir: her iki yolda da sonucun `requires_grad` bayrağı kapalıdır.

**In-place hatası.** Bölüm 65.3'te yerinde işlemlerin autograd ile çatışabileceğini söylemiştik. Sigmoid'in geri adımı kendi çıktısını kullanır (`σ'(x) = σ(x)(1 − σ(x))`). Eğer `q = sigmoid(p)` çıktısını `add_` ile değiştirirsen, geri geçiş yanlış bir değer okuyacağı için PyTorch hata verir.

Bu hata, PyTorch'un en iyi tasarım kararlarından biridir: yanlış gradyan üretmek yerine hata verir. Hatayı görünce kodu düzeltmek için iki yol vardır: yerinde işlemi kaldırmak ya da girdiyi `clone()` ile kopyalamak.

::: dikkat
Mülakatta "gradyanlar neden birikiyor?" diye sorarlarsa iki cevap ver: bir, gradyan birikimi mini-batch toplamaya ve paylaşılan parametrelere (RNN'de olduğu gibi) gerekli bir araçtır. İki, bu yüzden her adımda sıfırlamak zorundasın. Cevabın bu ikisini birlikte söylemesi beklenir.
:::

## 65.6 Micrograd ile karşılaştırma ve özel autograd Function

Bölüm 55'teki `Deger` sınıfı, PyTorch'un küçük bir kopyasıdır. İkisinin de cevabı aynı olmalıdır. Bunu test etmek, hem motorumuzun doğruluğunu hem de PyTorch'un ne yaptığını anlamanın en iyi yoludur. Aşağıdaki program, aynı ifadeyi iki motorda da hesaplar.

```python
# t03_micrograd.py: Bölüm 55'teki Deger ile PyTorch gradyanlarını
# karşılaştırır. Aynı ifade, aynı gradyan.
import random, math
import torch
from deger import Deger

# 1) Sabit ifade: f = tanh((a*b + a) / 10)
a = Deger(2.0); b = Deger(3.0)
f = ((a * b + a) / 10).tanh()
f.geri()
print("Deger  : f=%.6f  a.grad=%.6f  b.grad=%.6f"
      % (f.veri, a.grad, b.grad))

ta = torch.tensor(2.0, dtype=torch.float64, requires_grad=True)
tb = torch.tensor(3.0, dtype=torch.float64, requires_grad=True)
tf = torch.tanh((ta * tb + ta) / 10)
tf.backward()
print("torch  : f=%.6f  a.grad=%.6f  b.grad=%.6f"
      % (tf.item(), ta.grad.item(), tb.grad.item()))

# 2) Rastgele ifadeler: 200 tohumlu ağaç, göreli hata ölçümü.
OPS = ["+", "*", "tanh"]

def kur(rng, n_gir, derinlik):
    # Aynı ağacı iki motorda da kurabilmek için bir tarif üretir.
    if derinlik == 0:
        return ("g", rng.randrange(n_gir))
    op = rng.choice(OPS)
    if op == "tanh":
        return (op, kur(rng, n_gir, derinlik - 1))
    return (op, kur(rng, n_gir, derinlik - 1),
            kur(rng, n_gir, derinlik - 1))

```

Programın devamı (satır 36–71):

```python
def degerle(t, gir):
    if t[0] == "g":
        return gir[t[1]]
    if t[0] == "tanh":
        return degerle(t[1], gir).tanh()
    x, y = degerle(t[1], gir), degerle(t[2], gir)
    return x + y if t[0] == "+" else x * y

def tdegerle(t, gir):
    if t[0] == "g":
        return gir[t[1]]
    if t[0] == "tanh":
        return torch.tanh(tdegerle(t[1], gir))
    x, y = tdegerle(t[1], gir), tdegerle(t[2], gir)
    return x + y if t[0] == "+" else x * y

en_kotu = 0.0
for tohum in range(200):
    rng = random.Random(tohum)
    agac = kur(rng, 3, 4)
    vals = [rng.uniform(-1, 1) for _ in range(3)]
    gir = [Deger(v) for v in vals]
    out = degerle(agac, gir)
    out.geri()
    tg = [torch.tensor(v, dtype=torch.float64, requires_grad=True)
          for v in vals]
    to = tdegerle(agac, tg)
    to.backward()
    for dg, tt in zip(gir, tg):
        # Girdi ifadede hiç kullanılmadıysa gradyan 0'dır.
        ref = 0.0 if tt.grad is None else tt.grad.item()
        hata = abs(dg.grad - ref) / max(1.0, abs(ref))
        en_kotu = max(en_kotu, hata)
print("200 rastgele ifade, en kötü göreli hata: %.3e" % en_kotu)
```

İlk iki satır şöyledir:

```term
$ python t03_micrograd.py
Deger  : f=0.664037  a.grad=0.223622  b.grad=0.111811
torch  : f=0.664037  a.grad=0.223622  b.grad=0.111811
200 rastgele ifade, en kötü göreli hata: 4.441e-16
```

Sabit ifade için iki motor aynı sonucu verir. Asıl sınav rastgele ifadelerdir. Betik, 200 farklı tohumla rastgele bir ifade ağacı üretir (`+`, `*`, `tanh` işlemleri, 3 girdi, derinlik 4), her iki motorla gradyanı hesaplar ve en büyük göreli hatayı alır. Aşağıdaki kısım ağacı tarif olarak üretir ve iki motorda da aynı tarifi değerlendirir.

Tarifi değerlendiren iki fonksiyon, biri `Deger` için, diğeri PyTorch tensörleri için yazılmıştır. Ana döngü her tohumda ikisini çalıştırır.

En kötü göreli hata `4,4·10⁻¹⁶`dır, yani makine epsilonunun (`float64` için `2,2·10⁻¹⁶`) iki katı. İki motor ayrı yollardan geçse de sonuç çift duyarlık yuvarlama sınırında aynıdır. Bölüm 55'in motoru doğrudur ve PyTorch'un autograd'ı bu kavramın üretim sürümüdür. Fark, ölçekte ve operatör çeşitliliğindedir: PyTorch yüzlerce operatörü çekirdek düzeyinde, GPU'da, tensör olarak yapar.

**Özel autograd Function.** Bazen bir işlemin türevini PyTorch'un otomatik bulmasına bırakmak yetmez. Örneğin büyük girdilerde taşan bir fonksiyonun gradyanını kararlı biçimde kendin yazman gerekebilir. `torch.autograd.Function` bunun için vardır: ileri geçişi ve geri geçişi sen tanımlarsın. Aşağıdaki örnek **softplus** fonksiyonunu, `log(1 + eˣ)`, kararlı biçimde yazar.

```python
# t04_ozel_fn.py: özel autograd Function ve gradcheck.
import torch

class Softplus(torch.autograd.Function):
    # softplus(x) = log(1 + e^x), sayısal olarak kararlı biçimde.
    @staticmethod
    def forward(ctx, x):
        ctx.save_for_backward(x)
        # max(x,0) + log(1 + e^{-|x|}): e^x hiç hesaplanmaz.
        return x.clamp_min(0) + torch.log1p(torch.exp(-x.abs()))

    @staticmethod
    def backward(ctx, grad_out):
        (x,) = ctx.saved_tensors
        return grad_out * torch.sigmoid(x)

def naif(x):
    return torch.log1p(torch.exp(x))

x = torch.tensor([-100.0, 0.0, 100.0], requires_grad=True)
ileri = Softplus.apply(x).tolist()
print("kararlı ileri :", [f"{v:.6g}" for v in ileri])
print("naif ileri    :", naif(x).detach().tolist())
Softplus.apply(x).sum().backward()
print("kararlı grad  :", x.grad.tolist())
x.grad = None
naif(x).sum().backward()
print("naif grad      :", x.grad.tolist())

xd = torch.linspace(-5, 5, 9, dtype=torch.float64, requires_grad=True)
ok = torch.autograd.gradcheck(Softplus.apply, (xd,))
print("\ngradcheck (float64, 9 nokta):", ok)

```

Programın devamı (satır 37–41):

```python
# İkinci dereceden türev: f = x^3, f' = 3x^2, f'' = 6x (x = 3).
y = torch.tensor(3.0, requires_grad=True)
d1, = torch.autograd.grad(y ** 3, y, create_graph=True)
d2, = torch.autograd.grad(d1, y)
print("f'(3) = %.1f, f''(3) = %.1f" % (d1.item(), d2.item()))
```

Naif formül `log(1 + eˣ)` büyük `x`te `eˣ`i taşırır. Stabil formül `max(x,0) + log(1 + e^(−|x|))` aynı fonksiyonu verir ama üssel terimin negatif değerlerini kullanır, bu yüzden taşmaz. Geri geçişte gradyan `sigmoid(x)`tir. Bu, `softplus'(x) = σ(x)` özdeşliğinden gelir ve ileri geçişte `eˣ` hesaplanmadığı için yeniden kullanılacak bir ara değer tutmaz.

```term
$ python t04_ozel_fn.py
kararlı ileri : ['3.92364e-44', '0.693147', '100']
naif ileri    : [3.923635700109488e-44, 0.6931471824645996, inf]
kararlı grad  : [0.0, 0.5, 1.0]
naif grad      : [3.783505853677006e-44, 0.5, nan]

gradcheck (float64, 9 nokta): True
f'(3) = 27.0, f''(3) = 18.0
```

Sonuç çarpıcıdır. Naif formül `x = 100` için ileri değerde `inf` ve gradyanda `nan` üretir. Stabil sürüm `100` ve `1.0` verir. Bu, sayısal kararlılığın, Bölüm 55.13'te gördüğümüz taşma sorununun PyTorch'taki karşılığı olduğunu gösterir. `nan` bir eğitim sırasında görülürse, sebep çoğu zaman bu tür bir naif formüldür.

**Gradcheck: özel türevi doğrulamak.** Kendi geri adımını yazdıysan, onu sayısal türevle karşılaştırmak zorundasın. `torch.autograd.gradcheck` tam bunu yapar: her girdi için sonlu farkla türevi hesaplar ve geri adımla karşılaştırır. Çift duyarlık (`float64`) gerekir, çünkü sonlu fark `float32`de gürültülüdür.

`gradcheck` `True` döndürdü, yani geri adımımız sayısal türevle uyuşuyor. Son olarak yüksek dereceli türevi göstermek için iki kez `grad` alırız: `f(x) = x³` için `f′(3) = 3·3² = 27` ve `f″(3) = 6·3 = 18`.

`create_graph=True` ilk türevin de bir grafik olarak saklanmasını sağlar; bu sayede türevin türevi alınabilir. Hessian-vektör çarpımları ve bazı fizik-bilgili öğrenme yöntemleri bu tekniğe dayanır.

## 65.7 nn.Module: parametre kaydı, durum ve hook'lar

Bölüm 63'te katmanları sınıf olarak yazdık: her katmanın `ileri` ve `geri` metotları vardı, ağırlıklarını kendimiz tutuyorduk (Bölüm 63.6 ve 63.7'deki `Dogrusal`, `ReLU`, `SoftmaxCE` ve `Ag` sınıfları). PyTorch'un `nn.Module` sınıfı aynı sorumlulukları standartlaştırır. Her modül üç şeyi bilir: kendi **parametrelerini** (öğrenilen ağırlıklar), **buffer'larını** (öğrenilmeyen ama durumun parçası olan değerler, örneğin BatchNorm'un hareketli ortalaması) ve **alt modüllerini**. Bu üçü bir ağacı oluşturur ve tüm ağın durumu bu ağacın yapraklarında durur.

Aşağıdaki program, Bölüm 64'te gördüğümüz BatchNorm ve dropout'u içeren bir modeli kurar. Ağacı, parametreleri, buffer'ları, `state_dict` anahtarlarını, `train()`/`eval()` farkını ve bir aktivasyon kancasını gösterir.

```python
# t05_module.py: nn.Module ağacı, state_dict, buffer ve hook.
import torch
import torch.nn as nn

torch.manual_seed(0)

class Ag(nn.Module):
    def __init__(self):
        super().__init__()
        self.ust = nn.Sequential(
            nn.Linear(64, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Dropout(0.5),
        )
        self.cikis = nn.Linear(32, 10)

    def forward(self, x):
        return self.cikis(self.ust(x))

ag = Ag()
print("modül ağacı (ad, sınıf):")
for ad, m in ag.named_modules():
    print(f"  {ad or '(kök)':12s} {type(m).__name__}")
print("\nparametreler:")
for ad, p in ag.named_parameters():
    print(f"  {ad:22s} {str(tuple(p.shape)):12s}")
print("buffer'lar:")
for ad, _ in ag.named_buffers():
    print("  ", ad)
print("state_dict anahtarları:")
for k in ag.state_dict():
    print("  ", k)
print("toplam parametre:",
      sum(p.numel() for p in ag.parameters()))

```

Programın devamı (satır 39–61):

```python
ag.train()
print("\ntrain modu: dropout =", ag.ust[3].training,
      " bn =", ag.ust[1].training)
ag.eval()
print("eval modu : dropout =", ag.ust[3].training,
      " bn =", ag.ust[1].training)

# Hook: ileri geçişte aktivasyonun ortalama ve std değerini topla.
izler = {}

def ileri_hook(ad):
    def kanca(modul, girdi, cikti):
        izler[ad] = (cikti.mean().item(), cikti.std().item())
    return kanca

kanca = ag.ust[2].register_forward_hook(ileri_hook("relu"))
ag.train()
ag(torch.randn(64, 64))
print("\nrelu aktivasyonu (train):",
      {k: tuple(round(v, 4) for v in t) for k, t in izler.items()})
kanca.remove()
```

Programın çıktısı şöyledir:

```term
$ python t05_module.py
modül ağacı (ad, sınıf):
  (kök)        Ag
  ust          Sequential
  ust.0        Linear
  ust.1        BatchNorm1d
  ust.2        ReLU
  ust.3        Dropout
  cikis        Linear

parametreler:
  ust.0.weight           (32, 64)    
  ust.0.bias             (32,)       
  ust.1.weight           (32,)       
  ust.1.bias             (32,)       
  cikis.weight           (10, 32)    
  cikis.bias             (10,)       
buffer'lar:
   ust.1.running_mean
   ust.1.running_var
   ust.1.num_batches_tracked
state_dict anahtarları:
   ust.0.weight
   ust.0.bias
   ust.1.weight
   ust.1.bias
   ust.1.running_mean
   ust.1.running_var
   ust.1.num_batches_tracked
   cikis.weight
   cikis.bias
toplam parametre: 2474

train modu: dropout = True  bn = True
eval modu : dropout = False  bn = False

relu aktivasyonu (train): {'relu': (0.4, 0.5871)}
```

Ağaçta her düğümün adı (`ust.0`, `ust.1` gibi) `state_dict` anahtarlarını belirler: `ust.0.weight`, "`ust` içindeki 0 numaralı alt modülün `weight`i" demektir.

![Şekil 65.5: nn.Module ağacı; parametreler ve buffer'lar, state_dict anahtarları](gorseller/b65_nn_agac.png)

Toplam parametre sayısı elle de doğrulanabilir: `64·32 + 32 + 32 + 32 + 10·32 + 10 = 2048 + 32 + 64 + 320 + 10 = 2474`. BatchNorm'un `running_mean`, `running_var` ve `num_batches_tracked` alanları **parametre değil buffer**'dır: gradyan almazlar, optimizer onları güncellemez, ama `state_dict` içinde yer alırlar. Bu ayrım önemlidir. Bir modeli kaydedip yeniden yüklediğinde bu buffer'lar kaybolursa, BatchNorm değerlendirme modunda yanlış çalışır.

**Nasıl kaydediliyor?** `self.ust = nn.Sequential(...)` yazdığında, bu atama bir `__setattr__` çağrısına dönüşür ve PyTorch alt modülü bir sözlüğe kaydeder. Bu kaydın mekanizmasını PyTorch 2.6.0 kaynağında okuyalım. Aşağıdaki kesit, `torch/nn/modules/module.py` dosyasının 1933–1945. satırlarından birebir alınmıştır (`def` satırı ve iki uzun hata mesajı yer açmak için atlanmıştır; kalan satırlar aynen).

```python
        def remove_from(*dicts_or_sets):
            for d in dicts_or_sets:
                if name in d:
                    if isinstance(d, dict):
                        del d[name]
                    else:
                        d.discard(name)

        params = self.__dict__.get("_parameters")
        if isinstance(value, Parameter):
            if params is None:
                # (burada AttributeError fırlatılır; satır atlandı)
```

Bu kodda üç şeye dikkat et. Birincisi, `Parameter` örneği atandığında PyTorch onu `_parameters` sözlüğüne koyar; sıradan bir tensör atandığında ise modül onu parametre olarak **kaydetmez**. Bu yüzden ağırlığını `torch.tensor(...)` ile sıradan bir değişkene yazarsan optimizer onu görmez. İkincisi, `remove_from` yardımcısı aynı isimde başka bir kayıt varsa onu temizler; böylece bir isim aynı anda hem parametre hem alt modül olamaz. Üçüncüsü, `__init__` çağrılmadan atama yapılırsa hata verilir, çünkü sözlükler henüz yoktur. Bu, Python'da `super().__init__()` çağrısının neden zorunlu olduğunu açıklar.

**Eğitim ve değerlendirme modu.** `train()` ve `eval()` modülün ve tüm alt modüllerinin `training` bayrağını değiştirir. Dropout eğitimde rastgele nöronları kapatır, değerlendirmede ise kapalı ve etkisizdir. BatchNorm eğitimde mini-batch istatistiklerini kullanır ve hareketli ortalamayı günceller; değerlendirmede ise biriken hareketli ortalamaları kullanır. Çıktıdaki `train modu` ve `eval modu` satırları bu farkı gösterir.

Doğrulama kümesinde `model.eval()` çağırmayı unutmak, en yaygın ve en sinsi eğitim hatalarından biridir. Dropout açık kalır, tahminler rastgele olur ve BatchNorm batch istatistiklerini kullanır; doğrulama kaybı yapay olarak yüksek ya da düşük görünür. Eğitim döngüsünde (Bölüm 65.9) bu yüzden her epoch'un iki yarısını ayrı ayrı işaretleriz.

**Hook'lar.** Hook, bir modül ileri ya da geri geçişi yaptığında çağrılan bir kancadır. Aktivasyon dağılımını izlemek için idealdir: ölü ReLU'lar ya da patlayan aktivasyonlar gibi eğitim hatalarını bu yolla yakalarsın. Programdaki kanca, ReLU çıktısının ortalamasını ve standart sapmasını kaydetti ve `remove()` ile söküldü. Kanca sökülmezse her ileri geçişte kayıt yapılmaya devam eder ve uzun eğitimde bellek ve süre kaybı olur.

**Sayısal eşleşme: NumPy MLP ile PyTorch.** Bölüm 63.6 ve 63.7'de ileri ve geri geçişi elle yazdık; Bölüm 63.15'te aynı ağırlıklarla kurulmuş bir PyTorch modelinin kaybını ve gradyanlarını NumPy çıktısıyla karşılaştırdık (kayıp 8 basamağa kadar, gradyan farkı `10⁻¹⁷`). Bu sayısal eşleşmeyi bu bölümde tekrarlamıyoruz; bu bölümün konusu PyTorch'un kendi yapılarıdır. Önemli bir not: o karşılaştırmada `.double()` çağrısı modeli çift duyarlığa çevirir; bunu yapmasaydık `float32` ile `float64` karışık işlem hatası alırdık. Algoritmik eşleşmeyi float64'te kanıtlayıp sonra float32'ye geçmek, hata ayıklamanın doğru sırasıdır.

::: ipucu
Bir modelin ağırlıklarını kaydedip yüklerken `state_dict()` kullan, tüm modeli `torch.save(model)` ile kaydetme. Birincisi taşınabilir ve sürüme daha az bağlıdır. Ayrıca `load_state_dict` ile eksik ya da fazla anahtarları yakalayabilirsin (`strict=True` varsayılandır).
:::

## 65.8 Dataset ve DataLoader: veri hattı ve GPU'nun beklemesi

Bir modelin eğitimi üç adımdan oluşur: veriyi hazırlamak, modelin ileri ve geri geçişini çalıştırmak, sonra parametreleri güncellemek. PyTorch'ta birinci adım **Dataset** ve **DataLoader** ile yapılır. Dataset tek bir örneğe nasıl erişileceğini bilir. DataLoader ise bu örnekleri batch'lere toplar, karıştırır, gerekirse paralel işçilerle (worker) önceden hazırlar ve GPU'ya gönderir.

Veri hattının neden önemli olduğunu bir örnekle görelim. Bir İHA görüntü hattında her örnek diskten okunur, döndürülür, bulanıklaştırılır ve normalize edilir. Bu işlemler CPU'da yapılır ve GPU'nun hesabından bağımsızdır. Eğer CPU bu işi GPU'nun ihtiyaç duyduğu hızda üretemezse, GPU her adımda veri beklemek zorunda kalır. Bu durumda GPU'nun yüzde 100 kullanımı bir yanılsama olur: GPU, ancak beklediği veri geldiğinde çalışır.

Ölçüm için bir veri kümesi kuruyoruz: `load_digits` rakamlarını 32×32'ye büyütüp her örnek için rastgele döndürme ve bulanıklaştırma uyguluyoruz. Bu dönüşümü bilerek pahalı tuttuk ki işçi etkisi ölçülebilsin.

```python
# g08_veri.py: DataLoader num_workers, pin_memory ve GPU'nun veri
# beklemesi. Çıktı: engine/veri/b65_veri.csv
import csv, os, time
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from scipy import ndimage
from sklearn.datasets import load_digits

KOK = "D:/Mevcut Projeler/Kitap/engine/veri"

class DigitGenis(Dataset):
    # 1797 rakamı 32x32'ye büyütür; her örnek için rastgele döndürme
    # ve bulanıklaştırma yapar. Bu işlem CPU'da çalışır: bilerek
    # pahalı tutuldu ki worker etkisi ölçülebilsin.
    def __init__(self, n):
        X, y = load_digits(return_X_y=True)
        X = X.reshape(-1, 8, 8) / 16.0
        self.X = np.stack([ndimage.zoom(im, 4, order=1) for im in X])
        self.y = y
        self.n = n

    def __len__(self):
        return self.n

    def __getitem__(self, i):
        rng = np.random.default_rng(i)
        k = i % len(self.X)
        im = ndimage.rotate(self.X[k], rng.uniform(-20, 20),
                            reshape=False, order=1)
        im = ndimage.gaussian_filter(im, 0.8)
        im = im + rng.normal(0, 0.02, im.shape)
        return torch.from_numpy(im).float()[None], int(self.y[k])

```

Programın devamı (satır 37–45):

```python
def ag():
    return torch.nn.Sequential(
        torch.nn.Conv2d(1, 16, 3, padding=1), torch.nn.ReLU(),
        torch.nn.MaxPool2d(2),
        torch.nn.Conv2d(16, 32, 3, padding=1), torch.nn.ReLU(),
        torch.nn.MaxPool2d(2),
        torch.nn.Flatten(), torch.nn.Linear(32 * 8 * 8, 10))

```

Programın devamı (satır 46–85):

```python
def turu(workers, pin, dev):
    torch.manual_seed(0)
    ds = DigitGenis(4096)
    dl = DataLoader(ds, batch_size=64, shuffle=True,
                    num_workers=workers, pin_memory=pin,
                    persistent_workers=workers > 0)
    net = ag().to(dev)
    opt = torch.optim.Adam(net.parameters(), 1e-3)
    bekleme = 0.0
    gpu_sure = 0.0
    adim = 0
    for ep in range(2):          # 1. tur ısınma (worker başlatma)
        if ep == 1:
            t_ep = time.perf_counter()
            bekleme = 0.0
            gpu_sure = 0.0
            adim = 0
        t_once = time.perf_counter()
        it = iter(dl)
        while True:
            t0 = time.perf_counter()
            try:
                x, y = next(it)
            except StopIteration:
                break
            bekleme += time.perf_counter() - t0
            t1 = time.perf_counter()
            x = x.to(dev, non_blocking=pin)
            y = y.to(dev, non_blocking=pin)
            loss = torch.nn.functional.cross_entropy(net(x), y)
            opt.zero_grad()
            loss.backward()
            opt.step()
            torch.cuda.synchronize() if dev.type == "cuda" else None
            gpu_sure += time.perf_counter() - t1
            adim += 1
    toplam = time.perf_counter() - t_ep
    return toplam, bekleme, gpu_sure, adim

```

Programın devamı (satır 86–103):

```python
if __name__ == "__main__":
    dev = torch.device("cuda")
    satir = []
    for w, pin in [(0, False), (1, False), (2, False), (4, False),
                   (4, True), (8, True)]:
        toplam, bek, gsu, adim = turu(w, pin, dev)
        satir.append((w, pin, toplam, bek, gsu, adim))
        print("workers=%d pin=%-5s tur=%6.2f s  veri_bekleme=%6.2f s"
              % (w, pin, toplam, bek))
        print("  gpu_adim=%5.2f s  adim=%d" % (gsu, adim))
    with open(os.path.join(KOK, "b65_veri.csv"), "w", newline="",
              encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["workers", "pin", "tur_s", "veri_bekleme_s",
                     "gpu_adim_s", "adim"])
        for r in satir:
            wr.writerow([r[0], r[1], "%.3f" % r[2], "%.3f" % r[3],
                         "%.3f" % r[4], r[5]])
```

Dataset sınıfının üç metodu vardır: `__len__` örnek sayısını, `__getitem__` ise i-inci örneği döndürür. Dikkat et: `__getitem__` her çağrıda yeni bir rastgele dönüşüm üretir ve bunu `default_rng(i)` ile örnek indeksinden türetir. Böylece aynı `i` her zaman aynı görüntüyü verir; bu, tekrarlanabilir veri artırma (augmentation) için gereklidir (Bölüm 65.14).

Ölçüm fonksiyonu, bir epoch'u verilen worker ve `pin_memory` ayarıyla koşturur. Epoch'un iki kısmı ayrı ölçülür: DataLoader'dan batch beklemek (`veri_bekleme`) ve GPU'da ileri, geri ve adım (`gpu_adim`). İlk epoch ısınma içindir: worker'ların başlatılması ve ilk CUDA çağrıları bu epoch'a düşer.

Bu fonksiyonda `persistent_workers=True` önemlidir: worker'lar epoch'lar arasında yaşar ve her epoch'ta yeniden başlatılmaz. `non_blocking=pin` ise pinned bellekten yapılan kopyanın CPU'yu bloke etmeden yapılmasını sağlar (Bölüm 65.4). Ana blok, sekiz konfigürasyonu koşturur. Windows'ta bu blok `if __name__ == "__main__":` içinde olmak zorundadır, çünkü worker'lar Windows'ta `spawn` yöntemiyle başlatılır: her worker modülü baştan içe aktarır. Korumayı atlarsan, her worker kendi başına yeni işçiler başlatmaya çalışır ve program bir hata ile durur.

```term
$ python g08_veri.py
workers=0 pin=False tur=  0.95 s  veri_bekleme=  0.78 s
  gpu_adim= 0.18 s  adim=64
workers=1 pin=False tur=  0.83 s  veri_bekleme=  0.51 s
  gpu_adim= 0.31 s  adim=64
workers=2 pin=False tur=  0.42 s  veri_bekleme=  0.26 s
  gpu_adim= 0.16 s  adim=64
workers=4 pin=False tur=  0.23 s  veri_bekleme=  0.09 s
  gpu_adim= 0.14 s  adim=64
workers=4 pin=True  tur=  0.23 s  veri_bekleme=  0.10 s
  gpu_adim= 0.13 s  adim=64
workers=8 pin=True  tur=  0.15 s  veri_bekleme=  0.02 s
  gpu_adim= 0.13 s  adim=64
```

Tablo, bir epoch'un (64 batch, 4096 örnek) süresini ve bunun ne kadarının veri beklemesine gittiğini gösterir.

| worker | pin | epoch (s) | veri beklemesi (s) | GPU adımı (s) | beklemenin payı |
|---|---|---|---|---|---|
| 0 | hayır | 0,952 | 0,777 | 0,175 | %82 |
| 1 | hayır | 0,829 | 0,515 | 0,314 | %62 |
| 2 | hayır | 0,423 | 0,263 | 0,159 | %62 |
| 4 | hayır | 0,233 | 0,095 | 0,137 | %41 |
| 4 | evet | 0,227 | 0,098 | 0,128 | %43 |
| 8 | evet | 0,151 | 0,022 | 0,128 | %15 |

![Şekil 65.6: Worker sayısına göre epoch süresi; GPU'nun veri beklediği kısım koyu renkle](gorseller/b65_veri_hatti.png)

Tablo iki şeyi açıkça gösterir. Birincisi, `num_workers=0` ile GPU, epoch'un yüzde 82'sinde veri beklemiştir; GPU'nun gerçek hesap süresi yalnızca 0,175 s'dir. Yani bu konfigürasyonda GPU'yu eklemek sana neredeyse hiç kazanç sağlamaz, darboğaz veri hattıdır. İkincisi, worker sayısını 8'e çıkarınca bekleme yüzde 15'e düşer ve epoch 6 kat hızlanır (0,952 s'den 0,151 s'ye). GPU'nun hesap süresi (0,128 s) sabit kalır, çünkü model aynıdır. Pinned bellek bu ölçümde yalnızca marjinal bir fark yaratır (0,233 s'ye karşı 0,227 s); asıl kazanç worker'lardan gelir. Pinned bellek, kopyanın maliyetini azaltır, ama dönüşümün kendisi CPU'da yapılıyorsa darboğaz zaten oradadır.

Bu sonuçların makineye bağlı olduğunu unutma. Worker sayısının faydası, CPU çekirdek sayısına (bu makinede 16 mantıksal çekirdek) ve dönüşümün ağırlığına bağlıdır. Ölçümü kendi veri hattınla tekrar et: `num_workers`u 0'dan başlayıp artır ve veri beklemesinin payına bak. Pay düşmeyi durduğunda, artık bir kazanç yok demektir.

::: dikkat
Veri hattını optimize etmeden önce darboğazın nerede olduğunu ölç. GPU kullanımına bakmak yetmez: `nvidia-smi` yüzde 100 gösterdiğinde bile GPU'nun gerçekte kaç saniye hesap yaptığını, kaç saniye beklediğini, yukarıdaki gibi ayrı ayrı ölçmelisin.
:::

## 65.9 Kanonik eğitim döngüsü: train, validation ve cihaz yönetimi

Her eğitim betiği aynı iskeleti izler. Bir epoch boyunca mini-batch'ler üzerinde ileri, kayıp, geri ve adım yapılır. Epoch sonunda model değerlendirme moduna geçer, doğrulama kümesinde kayıp ve doğruluk ölçülür, öğrenme oranı zamanlayıcısı ilerler ve en iyi model ile checkpoint kaydedilir. Şekil 65.7 bu akışı gösterir.

![Şekil 65.7: Kanonik eğitim döngüsü: batch, ileri geçiş, geri geçiş, adım, değerlendirme ve kayıt](gorseller/b65_egitim_akis.png)

Aşağıdaki kod bu döngüyü bir fonksiyon olarak yazar. Verilerin ve modelin tohumu ve cihaz kararı dışarıda tutulur; her epoch metrik üretir.

```python
# t07_egitim.py: kanonik eğitim döngüsü, checkpoint ile devam,
# gradyan birikimi eşdeğerliği. Çıktı: engine/veri/b65_egitim.csv
import csv, os, random
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

KOK = "D:/Mevcut Projeler/Kitap/engine/veri"
CK = "C:/Users/merty/AppData/Local/Temp/b65/ck.pt"

def tohumla(s):
    random.seed(s); np.random.seed(s); torch.manual_seed(s)

X, y = load_digits(return_X_y=True)
X = torch.tensor(X / 16.0, dtype=torch.float32)
y = torch.tensor(y)
Xtr, Xgec, ytr, ygec = train_test_split(X, y, test_size=0.3,
                                        stratify=y, random_state=0)
Xva, Xte, yva, yte = train_test_split(Xgec, ygec, test_size=0.5,
                                      stratify=ygec, random_state=0)

def model():
    return nn.Sequential(nn.Linear(64, 128), nn.ReLU(),
                         nn.Dropout(0.1), nn.Linear(128, 10))

def dogruluk(net, X_, y_):
    net.eval()
    with torch.no_grad():
        return (net(X_).argmax(1) == y_).float().mean().item()

```

Programın devamı (satır 39–69):

```python
def egit(net, opt, sched, dl, bas, son,
         ck_yolu=None, log=None, gen=None):
    lossf = nn.CrossEntropyLoss()
    for ep in range(bas, son):
        net.train()
        toplam = 0.0
        for xb, yb in dl:
            opt.zero_grad()
            l = lossf(net(xb), yb)
            l.backward()
            opt.step()
            toplam += l.item() * len(xb)
        lr = opt.param_groups[0]["lr"]      # bu epoch'ta kullanılan
        sched.step()
        net.eval()
        with torch.no_grad():
            vl = lossf(net(Xva), yva).item()
        va = dogruluk(net, Xva, yva)
        if log is not None:
            log.append((ep + 1, toplam / len(dl.dataset), vl, va, lr))
        if ck_yolu:
            torch.save({"model": net.state_dict(),
                        "opt": opt.state_dict(),
                        "sched": sched.state_dict(),
                        "epoch": ep + 1,
                        "rng_torch": torch.get_rng_state(),
                        "rng_gen": gen.get_state() if gen else None},
                       ck_yolu)
    return net

```

Programın devamı (satır 70–100):

```python
def kur(seed):
    tohumla(seed)
    net = model()
    opt = torch.optim.Adam(net.parameters(), lr=3e-3)
    sched = torch.optim.lr_scheduler.StepLR(opt, step_size=3,
                                            gamma=0.5)
    gen = torch.Generator().manual_seed(seed)
    dl = DataLoader(TensorDataset(Xtr, ytr), batch_size=64,
                    shuffle=True, generator=gen)
    return net, opt, sched, dl, gen

# 1) Kesintisiz 8 epoch.
net, opt, sched, dl, gen = kur(0)
log = []
egit(net, opt, sched, dl, 0, 8, log=log, gen=gen)
ref = {k: v.clone() for k, v in net.state_dict().items()}
print("epoch  egitim_kayip  val_kayip  val_dogr  lr")
for r in log:
    print("%5d  %12.4f  %9.4f  %8.4f  %.5f" % r)
with open(os.path.join(KOK, "b65_egitim.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["epoch", "egitim_kayip", "val_kayip", "val_dogruluk",
                "lr"])
    for r in log:
        w.writerow([r[0], "%.5f" % r[1], "%.5f" % r[2], "%.4f" % r[3],
                    "%.6f" % r[4]])
print("test doğruluğu (kesintisiz, bir kez):",
      "%.4f" % dogruluk(net, Xte, yte))

```

Programın devamı (satır 101–130):

```python
# 2) 4 epoch + checkpoint, sonra YENİ nesnelerle 4 epoch daha.
net, opt, sched, dl, gen = kur(0)
egit(net, opt, sched, dl, 0, 4, ck_yolu=CK, gen=gen)
net2, opt2, sched2, _, _ = kur(123)         # farklı başlangıç
ck = torch.load(CK, weights_only=True)
net2.load_state_dict(ck["model"])
opt2.load_state_dict(ck["opt"])
sched2.load_state_dict(ck["sched"])
torch.set_rng_state(ck["rng_torch"])
gen2 = torch.Generator()
gen2.set_state(ck["rng_gen"])
dl2 = DataLoader(TensorDataset(Xtr, ytr), batch_size=64, shuffle=True,
                 generator=gen2)
egit(net2, opt2, sched2, dl2, ck["epoch"], 8, gen=gen2)
fark = max((ref[k] - v).abs().max().item()
           for k, v in net2.state_dict().items())
print("\ncheckpoint sonrası en büyük parametre farkı:", fark)

# 3) Yanlış devam: RNG durumu yüklenmezse.
net3, opt3, sched3, _, _ = kur(123)
ck = torch.load(CK, weights_only=True)
net3.load_state_dict(ck["model"]); opt3.load_state_dict(ck["opt"])
sched3.load_state_dict(ck["sched"])
dl3 = DataLoader(TensorDataset(Xtr, ytr), batch_size=64, shuffle=True,
                 generator=torch.Generator().manual_seed(0))
egit(net3, opt3, sched3, dl3, ck["epoch"], 8)
fark3 = max((ref[k] - v).abs().max().item()
            for k, v in net3.state_dict().items())
print("RNG yüklenmeden devam, en büyük fark: %.3e" % fark3)

```

Programın devamı (satır 131–154):

```python
# 4) Gradyan birikimi: 4 x 64 mikro-batch == 256 batch (dropout yok).
torch.set_default_dtype(torch.float64)
tohumla(0)
A = nn.Sequential(nn.Linear(64, 32), nn.Tanh(), nn.Linear(32, 10))
B = nn.Sequential(nn.Linear(64, 32), nn.Tanh(), nn.Linear(32, 10))
B.load_state_dict(A.state_dict())
xb, yb = Xtr[:256].double(), ytr[:256]
lossf = nn.CrossEntropyLoss()
lossf(A(xb), yb).backward()                 # tek büyük batch
for i in range(4):
    mx = xb[i * 64:(i + 1) * 64]
    my = yb[i * 64:(i + 1) * 64]
    (lossf(B(mx), my) / 4).backward()       # 1/4 ölçekleme şart
fk = max((pa.grad - pb.grad).abs().max().item()
         for pa, pb in zip(A.parameters(), B.parameters()))
print("birikim (doğru 1/4): en büyük gradyan farkı: %.3e" % fk)
for p in B.parameters():
    p.grad = None
for i in range(4):
    (lossf(B(xb[i*64:(i+1)*64]), yb[i*64:(i+1)*64])).backward()
fk2 = max((pa.grad - pb.grad).abs().max().item()
          for pa, pb in zip(A.parameters(), B.parameters()))
print("birikim (ölçeksiz):  en büyük gradyan farkı: %.3e" % fk2)
torch.set_default_dtype(torch.float32)
```

Bu döngüdeki sıra önemlidir. `opt.zero_grad()` her adımın başında çağrılır (Bölüm 65.5). `net.train()` ve `net.eval()` epoch içinde doğru moda geçişi garanti eder (Bölüm 65.7). Doğrulama `torch.no_grad()` içinde yapılır: gradyan takibi kapalıdır, bellek ve süre tasarrufu sağlanır. Kayıp ortalaması `toplam / len(dl.dataset)` ile örnek başına hesaplanır, batch başına değil; son batch daha küçük olduğu için bu fark önemlidir.

Veri, model ve optimizer için yardımcı fonksiyonlar:

Veri bölmesi (`train_test_split`) üç parçaya ayrılır: eğitim (%70), doğrulama (%15), test (%15). Doğrulama kümesi hiperparametre seçmek ve epoch'ları izlemek içindir. Test kümesi yalnızca en sonda, bir kez kullanılır. Test kümesini bir kez bile ayarlamak için kullanırsan, o sayı artık tarafsız değildir (Bölüm 57). Bu yüzden `dogruluk(net, Xte, yte)` çağrısı betikte yalnızca bir yerde yer alır.

`tohumla` fonksiyonu Python, NumPy ve PyTorch tohumlarını aynı değere ayarlar. Yalnızca `torch.manual_seed` yetmez; her kütüphanenin kendi rastgele üretecine ihtiyacı vardır.

Kesintisiz 8 epoch'un sonucu aşağıdadır. Ayrıca her epoch'un öğrenme oranını da yazdırıyoruz; `lr` sütunu, bu epoch'ta kullanılan değerdir (zamanlayıcı epoch sonunda ilerler, bu yüzden `sched.step()` çağrısından önce okunur).

```term
$ python t07_egitim.py
epoch  egitim_kayip  val_kayip  val_dogr  lr
    1        1.9532     1.4666    0.8370  0.00300
    2        1.0707     0.7401    0.8296  0.00300
    3        0.5500     0.4628    0.8815  0.00300
    4        0.3886     0.3836    0.9037  0.00150
    5        0.3303     0.3369    0.9111  0.00150
    6        0.2889     0.2993    0.9148  0.00150
    7        0.2669     0.2855    0.9185  0.00075
    8        0.2471     0.2689    0.9259  0.00075
test doğruluğu (kesintisiz, bir kez): 0.9481

checkpoint sonrası en büyük parametre farkı: 0.0
RNG yüklenmeden devam, en büyük fark: 2.187e-02
birikim (doğru 1/4): en büyük gradyan farkı: 3.469e-17
birikim (ölçeksiz):  en büyük gradyan farkı: 8.097e-02
```

Eğitim kaybı her epoch düşmektedir, doğrulama kaybı da eşlik eder; aralarında büyük bir açılma yoktur, yani fazla öğrenme (overfitting) başlamamıştır. Doğrulama doğruluğu epoch 2'de bir kez düşer; bu, öğrenme oranı yüksekken yaşanan olağan bir dalgalanmadır. Öğrenme oranı her üç epoch'ta yarıya iner, bu da son epoch'larda düzenli bir iyileşme sağlar. Test doğruluğu (`0,9481`) tek bir koşudan gelir ve bir tohuma bağlıdır; bir sayı olarak tek başına değil, çoklu tohumla (Bölüm 65.14'te yaptığımız gibi) raporlanmalıdır. Bu bölümün kurulumu bir *öğrenme* kanıtı değil, *döngünün doğru çalıştığının* kanıtıdır.

## 65.10 Checkpoint: eğitime kaldığı yerden devam etmek

Bir eğitim, saatler ya da günler sürebilir. Elektrik kesilebilir, sürücü çökebilir, ya da bir sonraki iyileştirmeyi denemek için koşuyu durdurman gerekebilir. **Checkpoint**, eğitimi durdurup daha sonra aynen devam ettirebilmek için gereken her şeyi diske yazmaktır. Yalnızca model ağırlıklarını kaydetmek yetmez. Optimizer'ın momentum tamponları, zamanlayıcının durumu, epoch sayısı ve rastgele sayı üreteçlerinin durumu da gerekir. Bunların biri eksikse devam eden koşu, kesintisiz koşudan farklı sonuç verir.

Checkpoint'i `egit` içinde her epoch sonunda yazıyoruz (yukarıdaki kodda `ck_yolu` verildiğinde). Kaydedilen sözlük şöyledir: `model`, `opt`, `sched`, `epoch`, `rng_torch` (PyTorch'un global üreteci) ve `rng_gen` (DataLoader'ın karıştırma üreteci). Yüklemeyi ve devam etmeyi şöyle yaparız:

Bu deney, 4 epoch eğitip checkpoint alıyor, ardından **yeni nesneler** (farklı tohumla kurulmuş bir model ve optimizer) yaratıp checkpoint'ten yüklüyor ve kalan 4 epoch'u koşturuyor. Sonucu, kesintisiz 8 epoch'un son ağırlıklarıyla (`ref`) karşılaştırıyoruz.

Fark tam olarak sıfırdır. Kesintili ve kesintisiz koşu, bit düzeyinde aynı sonucu verir. Bu, checkpoint'in içeriğinin eksiksiz olduğunu kanıtlar.

**Bir eksik parça bırakınca ne olur?** Aynı deneyi, RNG durumunu yüklemeden tekrarlayalım. Model, optimizer ve zamanlayıcı yüklenir, ama karıştırma sırası ve dropout maskeleri farklı olur.

Fark `2,2·10⁻²` mertebesindedir. Sonuç bir hata değil, ama bir *ayrı koşu*dur: farklı bir karıştırma sırasıyla eğitilmiş bir model. Bu fark, kötü bir sonuç olarak görünmeyebilir; ama iki çalıştırmanın neden karşılaştırılamayacağını açıklar. Hata ayıklamada iki koşuyu yan yana koyup "bu değişiklik işe yaradı mı?" diye sorduğunda, aslında rastgele sayı üretecindeki farkı görmüş olabilirsin. Kural şudur: checkpoint'e yazılmayan her durum, devam eden koşuda sessizce farklılaşır.

::: not
Checkpoint'i kaydederken dosyayı önce geçici bir adla yazıp sonra yeniden adlandırmak (atomik yazma), elektrik kesintisinde bozuk bir dosya bırakmanı önler. Bu betikte böyle bir koruma yok; üretimde eklemelisin.
:::

## 65.11 Gradyan birikimi: büyük batch'i küçük parçalarla

Büyük bir batch, gradyanı daha kararlı tahmin eder ve GPU'yu daha verimli kullanır. Ama GPU belleği sınırlıysa büyük batch sığmayabilir (Bölüm 65.13). **Gradyan birikimi** (gradient accumulation) bu sorunu çözer: büyük batch'i `k` küçük parçaya böler, her parçanın geri geçişini yapar, gradyanları birikime bırakır ve yalnızca `k` parçadan sonra optimizer adımını atar. Sonuç, büyük batch ile aynı gradyandır; bellek ise küçük parça kadar kullanılır.

Bu eşdeğerliğin doğru olması için iki koşul vardır. Birincisi, her parçanın kaybı **`1/k` ile ölçeklenmelidir**; çünkü `CrossEntropyLoss` varsayılan olarak parça içinde ortalama alır ve bu ortalamaları toplamak büyük batch'in ortalamasını vermez. İkincisi, modelde batch istatistiği kullanan katman (BatchNorm) olmamalıdır: BatchNorm küçük parçada farklı istatistik hesaplar ve eşdeğerlik bozulur. Bu deneyde dropout ve BatchNorm'u dışarıda tuttuk.

Burada `A` tek bir 256 örneklik batch ile geri geçiş yapar; `B` aynı verinin dört 64'lük parçası üzerinde, her biri `1/4` ile ölçeklenmiş kayıpla geri geçiş yapar. Aynı başlangıç ağırlıkları kullanılır (`load_state_dict`) ve gradyanlar karşılaştırılır.

Gradyanlar çift duyarlık yuvarlama sınırında aynıdır. Şimdi 1/4 ölçeklemesini kaldırıp aynı deneyi tekrarlayalım. Bu, en yaygın hatanın ne olduğunu gösterir.

Ölçeklemesiz birikim, gradyanı yaklaşık 4 kat büyük yapar ve fark `8·10⁻²` olur. Bu bir "sessiz" hatadır: kod çalışır, kayıp düşer, ama öğrenme oranı fiilen dört kat yüksek bir değerle çalışır. Bu tür bir hata, eğitim eğrisinde yalnızca belirsiz bir kararsızlık olarak görünür; bu yüzden birikim kodunu yazdığında mutlaka bu tür bir eşdeğerlik testiyle doğrula.

Gerçek bir eğitim döngüsünde birikim şöyle görünür (sadeleştirilmiş, yalnızca ilgili kısım):

```python
ACC = 4
opt.zero_grad()
for i, (xb, yb) in enumerate(dl):
    kayip = lossf(net(xb), yb) / ACC
    kayip.backward()
    if (i + 1) % ACC == 0:
        opt.step()
        opt.zero_grad()
```

Burada `opt.zero_grad()` yalnızca `ACC` parçadan sonra çağrılır. Dikkat: epoch'un toplam batch sayısı `ACC`ye tam bölünmüyorsa, son birikmiş gradyanlar atlanır; bunu döngünün sonunda ayrıca kontrol etmelisin.

::: dikkat
Gradyan birikimi, BatchNorm'un istatistiklerini büyütmez. Efektif batch 256 olsa bile BatchNorm her 64'lük parçada kendi ortalamasını ve varyansını kullanır. Bu nedenle "birikim ile büyük batch" eşdeğerliği BatchNorm'lu modellerde yaklaşıktır ve bu fark, Bölüm 64'teki BatchNorm tartışmasına bağlanır.
:::

## 65.12 Karışık hassasiyet: autocast, GradScaler ve TF32

Bir sinir ağında çoğu işlem, yüksek hassasiyete ihtiyaç duymadan yapılabilir. `float16` bellekte yarısı kadar yer kaplar ve tensör çekirdekleri (tensor core) onu çok hızlı işler. Karışık hassasiyet (mixed precision) eğitiminin fikri şudur: ileri geçişin ağır işlemlerini `float16` ya da `bfloat16`da yap, ama kritik birikimleri ve ağırlıkların ana kopyasını `float32`de tut. PyTorch bunu `torch.autocast` ile yapar; hangi işlemin düşük hassasiyette güvenle çalışacağına kendisi karar verir.

Autocast tek başına yetmez. Bölüm 65.3'te gördüğümüz gibi `float16` küçük sayıları sıfıra yuvarlayabilir. Bunu somut görelim: gradyanlar genellikle `10⁻⁶`–`10⁻⁸` gibi küçük değerler alır ve bunlar `float16`da kaybolabilir.

```python
# g13_alt_tasma.py: fp16'da küçük gradyanın kaybı ve ölçekleme.
import torch
g = torch.tensor([1e-8, 3e-6, 1e-4])      # tipik küçük gradyanlar
print("fp32 :", [f"{v:.4g}" for v in g.tolist()])
print("fp16 :", [f"{v:.4g}" for v in g.half().float().tolist()])
s = 2.0 ** 16                    # GradScaler başlangıç ölçeği
gs = (g * s).half()
geri = (gs.float() / s).tolist()
print("fp16 (x 2^16):", [f"{v:.4g}" for v in geri])
print("fp16 en küçük normal:", torch.finfo(torch.float16).tiny)
print("fp16 en küçük alt normal:",
      torch.tensor(2.0 ** -24, dtype=torch.float16).item())
```

```term
$ python g13_alt_tasma.py
fp32 : ['1e-08', '3e-06', '0.0001']
fp16 : ['0', '2.98e-06', '0.0001']
fp16 (x 2^16): ['9.997e-09', '3.001e-06', '0.0001']
fp16 en küçük normal: 6.103515625e-05
fp16 en küçük alt normal: 5.960464477539063e-08
```

`1e-8` değeri `float16`ya yazıldığında `0,0` olur. Yani o gradyan, geri yayılım sırasında hiç var olmamış gibi davranır. `3e-6` ise yalnızca kısmen korunur: alt normal aralıkta olduğu için hassasiyeti düşmüştür. Çözüm **kayıp ölçekleme**dir (loss scaling). Kayıp `2¹⁶` ile çarpılır; böylece geri yayılan tüm gradyanlar aynı oranda büyür ve `float16`nın alt sınırının üstüne çıkar. Adım atılmadan önce gradyanlar tekrar `2⁻¹⁶` ile bölünür. Ölçekleme sonrası `1e-8` değeri `9,997·10⁻⁹`a geri döner.

`GradScaler`, bu ölçeği otomatik yönetir. Ölçekli gradyanlarda `inf` ya da `nan` görürse adımı atlar ve ölçeği yarıya indirir; uzun süre sorun çıkmazsa ölçeği yavaşça artırır. Bu, ölçeğin ne çok küçük ne çok büyük olmasını sağlar: büyük çarpan gradyanı taşırır, küçük çarpan alt taşmayı geri getirmez.

Aşağıdaki adım fonksiyonu, GPU üzerinde üç kipi (fp32, fp16 ve bf16) aynı kod yapısıyla çalıştırır. `bf16`da `GradScaler` gerekmez, çünkü `bfloat16` `float32`nin üssünü taşır; alt taşma riski çok daha düşüktür.

```python
# g04_amp.py: fp32 / fp16 AMP / bf16 AMP hız ve bellek ölçümü.
# Çıktı: engine/veri/b65_amp.csv
import csv, os, statistics, time
import torch
import torch.nn as nn

KOK = "D:/Mevcut Projeler/Kitap/engine/veri"
dev = torch.device("cuda")
torch.backends.cuda.matmul.allow_tf32 = False
torch.backends.cudnn.allow_tf32 = False
torch.manual_seed(0)

def model():
    return nn.Sequential(
        nn.Linear(4096, 4096), nn.ReLU(),
        nn.Linear(4096, 4096), nn.ReLU(),
        nn.Linear(4096, 10)).to(dev)

def adim(mod_kip, batch):
    net = model()
    opt = torch.optim.SGD(net.parameters(), lr=1e-3)
    x = torch.randn(batch, 4096, device=dev)
    y = torch.randint(0, 10, (batch,), device=dev)
    lossf = nn.CrossEntropyLoss()
    scaler = torch.amp.GradScaler("cuda", enabled=(mod_kip == "fp16"))

```

Programın devamı (satır 29–64):

```python
    def step():
        opt.zero_grad(set_to_none=True)
        kip_dt = torch.float16
        if mod_kip == "bf16":
            kip_dt = torch.bfloat16
        on = mod_kip != "fp32"
        with torch.autocast("cuda", dtype=kip_dt, enabled=on):
            loss = lossf(net(x), y)
        if mod_kip == "fp16":
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
        else:
            loss.backward()
            opt.step()
        return loss

    for _ in range(10):
        step()
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    step()
    torch.cuda.synchronize()
    bellek = torch.cuda.max_memory_allocated() / 2**20
    sureler = []
    for _ in range(3):
        t0 = time.perf_counter()
        for _ in range(20):
            step()
        torch.cuda.synchronize()
        sureler.append((time.perf_counter() - t0) / 20)
    del net, opt
    torch.cuda.empty_cache()
    return statistics.median(sureler) * 1000, bellek

```

Programın devamı (satır 65–78):

```python
sonuc = []
for batch in [256, 1024]:
    for kip in ["fp32", "fp16", "bf16"]:
        ms, mb = adim(kip, batch)
        sonuc.append((batch, kip, ms, mb))
        print("batch=%4d %s  adım=%8.2f ms  tepe bellek=%7.1f MB"
              % (batch, kip, ms, mb))

with open(os.path.join(KOK, "b65_amp.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["batch", "kip", "adim_ms", "tepe_bellek_mb"])
    for r in sonuc:
        w.writerow([r[0], r[1], "%.3f" % r[2], "%.1f" % r[3]])
```
```term
$ python g04_amp.py
batch= 256 fp32  adım=    7.49 ms  tepe bellek=  280.6 MB
batch= 256 fp16  adım=    6.02 ms  tepe bellek=  308.6 MB
batch= 256 bf16  adım=    4.85 ms  tepe bellek=  308.6 MB
batch=1024 fp32  adım=   25.61 ms  tepe bellek=  328.6 MB
batch=1024 fp16  adım=   11.01 ms  tepe bellek=  320.6 MB
batch=1024 bf16  adım=    9.96 ms  tepe bellek=  320.6 MB
```

`with torch.autocast(...)` bloğu yalnızca ileri geçişi ve kaybı kapsar; geri geçiş bloğun dışındadır. Bu bilinçli bir tasarımdır: autocast geri geçişte, ileri geçişte kullanılan düşük hassasiyetli işlemleri otomatik olarak izler.

Ölçüm, iki batch boyutunda (256 ve 1024) üç katmanlı bir MLP'nin (4096 genişlik) adım süresini ve tepe GPU belleğini verir. Süre, 3 tekrarın medyanıdır; her tekrar 20 adımdır ve 10 adım ısınma yapılır.

| Batch | Kip | Adım (ms) | Tepe bellek (MB) |
|---|---|---|---|
| 256 | fp32 | 7,49 | 280,6 |
| 256 | fp16 AMP | 6,02 | 308,6 |
| 256 | bf16 AMP | 4,85 | 308,6 |
| 1024 | fp32 | 25,61 | 328,6 |
| 1024 | fp16 AMP | 11,01 | 320,6 |
| 1024 | bf16 AMP | 9,96 | 320,6 |

![Şekil 65.8: fp32, fp16 AMP ve bf16 AMP için adım süresi ve tepe bellek](gorseller/b65_amp.png)

Batch 1024'te fp16 AMP, fp32'ye göre adımı yaklaşık 2,3 kat hızlandırır. Bu, RTX 3060'ın tensör çekirdeklerinin işe yaradığını gösterir. Ama bellek tablosu bir beklentiyi bozar: AMP, bu modelde tepe belleği **azaltmadı**, hatta artırdı. Nedeni şudur: model 33,6 milyon parametre taşıyor, yani ağırlıkların ve gradyanların (her biri `float32`) toplam ~270 MB'ı tepe belleğin büyük kısmını oluşturuyor. Batch ise yalnızca birkaç megabayt aktivasyon ekliyor. Autocast, ağırlıkların `float16` kopyalarını geçici olarak da tutar; bu da küçük bir ek yük getirir. AMP'nin bellek kazancı, aktivasyonların baskın olduğu derin modellerde görünür (Bölüm 65.13).

**TF32: görünmez bir hassasiyet kararı.** Ampere mimarisi (RTX 3060 dahil), `float32` matris çarpımını **TF32** formatında da yapabilir: 10 bitlik mantis (float16 ile aynı), 8 bitlik üs (float32 ile aynı). Bu, `float32` kodunuzda hiç değişiklik yapmadan çarpımı hızlandırır, ama hassasiyeti düşürür. PyTorch'ta varsayılan olarak matris çarpımı için TF32 kapalıdır; açmak bilinçli bir karardır.

```python
# g06_tf32.py: TF32 hız ve hassasiyet farkı; OOM yakalama.
# Çıktı: engine/veri/b65_tf32.csv
import csv, os, time
import torch

KOK = "D:/Mevcut Projeler/Kitap/engine/veri"
dev = torch.device("cuda")
torch.manual_seed(0)
n = 4096
a = torch.randn(n, n)
b = torch.randn(n, n)
ref = (a.double() @ b.double())            # referans: float64 (CPU)
satir = []
for tf32 in (False, True):
    torch.backends.cuda.matmul.allow_tf32 = tf32
    ag, bg = a.to(dev), b.to(dev)
    # Isınma: GPU saat hızı yükselsin.
    for _ in range(20):
        c = ag @ bg
    torch.cuda.synchronize()
    sureler = []
    for _ in range(5):
        t0 = time.perf_counter()
        for _ in range(10):
            c = ag @ bg
        torch.cuda.synchronize()
        sureler.append((time.perf_counter() - t0) / 10)
    sure = sorted(sureler)[2]              # medyan
    rel = ((c.cpu().double() - ref).norm() / ref.norm()).item()
    ad = "tf32" if tf32 else "fp32"
    satir.append((ad, sure, rel))
    print("%s  süre=%.5f s  göreli hata=%.3e  TFLOPS=%.2f"
          % (ad, sure, rel, 2 * n ** 3 / sure / 1e12))

with open(os.path.join(KOK, "b65_tf32.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["kip", "sure_s", "goreli_hata"])
    for r in satir:
        w.writerow([r[0], "%.6f" % r[1], "%.3e" % r[2]])
```
```term
$ python g06_tf32.py
fp32  süre=0.01821 s  göreli hata=5.741e-07  TFLOPS=7.55
tf32  süre=0.00985 s  göreli hata=2.940e-04  TFLOPS=13.95
```

`n = 4096` matris çarpımında iki kip karşılaştırıldı. Referans olarak çift duyarlıklı (float64) CPU sonucu alındı; hata, bağıl Frobenius normu olarak ölçüldü. Her ölçümde 20 ısınma ve 5 tekrarın medyanı alındı.

| Kip | Süre (ms) | TFLOPS | Bağıl hata |
|---|---|---|---|
| fp32 | 18,21 | 7,6 | 5,7·10⁻⁷ |
| TF32 | 9,85 | 14,0 | 2,9·10⁻⁴ |

TF32, süreyi neredeyse yarıya indirir ama hatayı yaklaşık 500 kat büyütür. Derin öğrenmede bu takas çoğu zaman kabul edilebilir: gradyan gürültüsü zaten vardır ve stokastik gradyan iniş onu tolere eder. Ama bir bilimsel hesaplamada ya da çok hassas bir sayısal yöntemde (örneğin bir Kalman filtresinin kovaryans güncellemesinde) TF32'yi kapatmak doğru olabilir. Karar, hatanın ne kadar tolere edilebilir olduğuna bağlıdır.

**AMP'nin doğruluğa etkisi.** Hız ve bellek iyi görünüyor; peki doğruluk? Üç tohumla (0, 1, 2) bir MLP'yi (64→256→10) digits veri kümesinde 30 epoch eğittik, fp32 ve fp16 AMP ile. Sonuç ortalama ± standart sapma olarak verildi.

| Kip | Eğitim doğruluğu | Test doğruluğu |
|---|---|---|
| fp32 | 0,9928 ± 0,0003 | 0,9685 ± 0,0013 |
| fp16 AMP | 0,9928 ± 0,0003 | 0,9685 ± 0,0013 |

İki satır da aynı görünüyor. Ama bu, ağırlıkların aynı olduğu anlamına gelmez. Aynı tohumla eğitilen iki modelin ağırlıklarını doğrudan karşılaştırdığımızda en büyük fark `0,011` çıkıyor. Yani sayısal yollar gerçekten ayrılmış, ama bu küçük veri kümesinde tahmin doğruluğu tesadüfen aynı kalmış. Ağırlık farkını ölçen betik ve çıktısı:
```python
# g10_amp_kontrol.py: aynı tohum, fp32 ile fp16-AMP ağırlık farkı.
import torch
import torch.nn as nn
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
dev = torch.device("cuda")
X, y = load_digits(return_X_y=True)
X = torch.tensor(X / 16.0, dtype=torch.float32).to(dev)
y = torch.tensor(y).to(dev)

def egit(amp):
    torch.manual_seed(0)
    net = nn.Sequential(nn.Linear(64, 256), nn.ReLU(),
                        nn.Linear(256, 10)).to(dev)
    opt = torch.optim.Adam(net.parameters(), 1e-3)
    sc = torch.amp.GradScaler("cuda", enabled=amp)
    lossf = nn.CrossEntropyLoss()
    for ep in range(3):
        perm = torch.randperm(len(X), device=dev)
        for i in range(0, len(X), 64):
            b = perm[i:i + 64]
            with torch.autocast("cuda", dtype=torch.float16,
                                enabled=amp):
                l = lossf(net(X[b]), y[b])
            opt.zero_grad()
            sc.scale(l).backward()
            sc.step(opt)
            sc.update()
    return net

a = egit(False)
b = egit(True)
print("fp32 vs AMP en büyük ağırlık farkı:",
      max((p - q).abs().max().item()
          for p, q in zip(a.parameters(), b.parameters())))
```
```term
$ python g10_amp_kontrol.py
fp32 vs AMP en büyük ağırlık farkı: 0.011115383356809616
```

Bu bir nüanstır: doğruluk aynı görünse de yollar farklıdır. Daha büyük ve zor veri kümelerinde AMP'nin etkisi doğruluk düzeyinde de görünebilir; bu yüzden AMP'yi açmadan önce kendi görevinde iki kipi de çalıştırıp doğrulamalısın.

::: dikkat
AMP'yi açtığında `loss` değerini ve gradyanların `nan`/`inf` olup olmadığını ilk birkaç yüz adımda izle. `GradScaler` bu adımları atlayıp ölçeği düşürür, ama sürekli atlanan adımlar bir kararsızlık işaretidir. Sessizce adım atlamak, yanlış bir eğitim eğrisinden daha kötüdür.
:::

## 65.13 Bellek: batch, OOM ve checkpointing

Bir modelin eğitim sırasında GPU belleğinde dört şey bulunur: parametreler, gradyanlar, optimizer durumu (Adam'ın iki moment tamponu gibi) ve **aktivasyonlar**. Aktivasyonlar, ileri geçişte hesaplanan ve geri geçişte gradyanı hesaplamak için saklanan ara değerlerdir. Parametre sayısı batch'ten bağımsızdır, ama aktivasyonlar batch ile doğrusal büyür. Derin ağlarda ve büyük batch'lerde belleği yiyen şey budur.

Bu etkiyi, 24 katmanlı, 1024 genişlikli bir ağla ölçtük. Parametreler sabit kalır (yaklaşık 100 MB), batch'i 128'den 4096'ya çıkarıyoruz. Üç kip karşılaştırılır: fp32, fp16 AMP ve **checkpointing**.

Gradient checkpointing, aktivasyonları saklamak yerine yeniden hesaplama takası yapar: ağı bloklara böler, yalnızca blok sınırlarındaki girdileri saklar ve geri geçişte her bloğun iç aktivasyonlarını yeniden hesaplar. Bellek, aktivasyonların tamamı yerine blok sayısına bağlı olur; bedeli ekstra bir ileri geçiş, yani yaklaşık bir ek hesap turudur.

```python
# g05_bellek.py: aktivasyon belleği, OOM, checkpointing ve AMP bellek.
# Çıktı: engine/veri/b65_bellek.csv
import csv, os, time
import torch
import torch.nn as nn
from torch.utils.checkpoint import checkpoint_sequential

KOK = "D:/Mevcut Projeler/Kitap/engine/veri"
dev = torch.device("cuda")
torch.backends.cuda.matmul.allow_tf32 = False
torch.manual_seed(0)
DERIN, GENIS = 24, 1024

def ag():
    katman = []
    for _ in range(DERIN):
        katman += [nn.Linear(GENIS, GENIS), nn.ReLU()]
    return nn.Sequential(*katman, nn.Linear(GENIS, 10)).to(dev)

def olc(batch, kip, dene=True):
    net = ag()
    opt = torch.optim.SGD(net.parameters(), lr=1e-4)
    x = torch.randn(batch, GENIS, device=dev)
    y = torch.randint(0, 10, (batch,), device=dev)
    lossf = nn.CrossEntropyLoss()
    scaler = torch.amp.GradScaler("cuda", enabled=(kip == "fp16"))

```

Programın devamı (satır 30–51):

```python
    def step():
        opt.zero_grad(set_to_none=True)
        if kip == "ckpt":
            # 24 doğrusal+ReLU çifti 6 bloğa bölünür; blok girdileri
            # saklanır, iç aktivasyonlar ileri geçişte silinir.
            out = checkpoint_sequential(net, 6, x,
                                        use_reentrant=False)
            loss = lossf(out, y)
            loss.backward()
            opt.step()
            return
        with torch.autocast("cuda", dtype=torch.float16,
                            enabled=(kip == "fp16")):
            loss = lossf(net(x), y)
        if kip == "fp16":
            scaler.scale(loss).backward()
            scaler.step(opt)
            scaler.update()
        else:
            loss.backward()
            opt.step()

```

Programın devamı (satır 52–86):

```python
    try:
        step()
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        step()
        torch.cuda.synchronize()
        bellek = torch.cuda.max_memory_allocated() / 2**20
        t0 = time.perf_counter()
        for _ in range(5):
            step()
        torch.cuda.synchronize()
        sure = (time.perf_counter() - t0) / 5 * 1000
        sonuc = (bellek, sure, "tamam")
    except torch.cuda.OutOfMemoryError:
        sonuc = (float("nan"), float("nan"), "OOM")
    del net, opt
    torch.cuda.empty_cache()
    return sonuc

satir = []
for batch in [128, 256, 512, 1024, 2048, 4096]:
    for kip in ["fp32", "fp16", "ckpt"]:
        mb, ms, durum = olc(batch, kip)
        satir.append((batch, kip, mb, ms, durum))
        print("batch=%5d %-5s tepe=%8.1f MB  adım=%8.2f ms  %s"
              % (batch, kip, mb, ms, durum))

with open(os.path.join(KOK, "b65_bellek.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["batch", "kip", "tepe_bellek_mb", "adim_ms", "durum"])
    for r in satir:
        w.writerow([r[0], r[1], "%.1f" % r[2] if r[2] == r[2] else "",
                    "%.2f" % r[3] if r[3] == r[3] else "", r[4]])
```
```term
$ python g05_bellek.py
batch=  128 fp32  tepe=   209.5 MB  adım=    6.89 ms  tamam
batch=  128 fp16  tepe=   211.0 MB  adım=   11.21 ms  tamam
batch=  128 ckpt  tepe=   209.5 MB  adım=   12.44 ms  tamam
batch=  256 fp32  tepe=   210.5 MB  adım=    8.84 ms  tamam
batch=  256 fp16  tepe=   211.5 MB  adım=   11.24 ms  tamam
batch=  256 ckpt  tepe=   210.5 MB  adım=   12.76 ms  tamam
batch=  512 fp32  tepe=   212.5 MB  adım=   13.31 ms  tamam
batch=  512 fp16  tepe=   212.5 MB  adım=   11.22 ms  tamam
batch=  512 ckpt  tepe=   212.5 MB  adım=   16.59 ms  tamam
batch= 1024 fp32  tepe=   228.5 MB  adım=   23.95 ms  tamam
batch= 1024 fp16  tepe=   224.5 MB  adım=   13.45 ms  tamam
batch= 1024 ckpt  tepe=   228.6 MB  adım=   30.70 ms  tamam
batch= 2048 fp32  tepe=   340.4 MB  adım=   44.83 ms  tamam
batch= 2048 fp16  tepe=   288.4 MB  adım=   18.15 ms  tamam
batch= 2048 ckpt  tepe=   260.6 MB  adım=   58.12 ms  tamam
batch= 4096 fp32  tepe=   555.0 MB  adım=   88.86 ms  tamam
batch= 4096 fp16  tepe=   407.0 MB  adım=   31.25 ms  tamam
batch= 4096 ckpt  tepe=   315.2 MB  adım=  112.98 ms  tamam
```

`checkpoint_sequential(net, 6, x)` ağı 6 bloğa böler. `use_reentrant=False` yeni, önerilen geri çağırma mekanizmasını seçer. Ölçüm sonuçları aşağıdadır (medyan adım süreleri, ms).

| Batch | fp32 bellek (MB) | fp16 bellek (MB) | checkpoint bellek (MB) | fp32 adım | fp16 adım | checkpoint adım |
|---|---|---|---|---|---|---|
| 128 | 209,5 | 211,0 | 209,5 | 6,89 | 11,21 | 12,44 |
| 512 | 212,5 | 212,5 | 212,5 | 13,31 | 11,22 | 16,59 |
| 1024 | 228,5 | 224,5 | 228,6 | 23,95 | 13,45 | 30,70 |
| 2048 | 340,4 | 288,4 | 260,6 | 44,83 | 18,15 | 58,12 |
| 4096 | 555,0 | 407,0 | 315,2 | 88,86 | 31,25 | 112,98 |

![Şekil 65.9: Batch boyutuna göre tepe bellek ve adım süresi; fp32, fp16 AMP ve checkpoint](gorseller/b65_bellek.png)

Tablo iki gerçeği açıkça gösterir. Birincisi, aktivasyon belleği batch ile büyür: 4096'da fp32 tepe belleği 555 MB'a ulaşır; bunun yaklaşık 355 MB'ı aktivasyondur. İkincisi, checkpointing belleği düşürür (4096'da 555'ten 315'e) ama süreyi artırır (88,9 ms'den 113,0 ms'ye, yani yaklaşık yüzde 27 daha yavaş). Küçük batch'lerde bu ek yük daha da belirgindir: 128'de checkpoint adımı fp32'nin neredeyse iki katıdır, ama bu batch'te bellek zaten sorun değildir. Checkpointing'i yalnızca bellek gerçekten sınırladığında kullanmak akıllıca olur.

Bu tabloda fp16 AMP'nin küçük batch'lerde daha yavaş olduğunu da görüyorsun (128'de 11,21 ms'ye karşı 6,89 ms). Autocast'in her işlemde tip dönüşümü yapması, küçük işlerde bu dönüşümü pahalı kılar. AMP'nin kazancı büyük işlerde ortaya çıkar.

**OOM ve Windows'ta gizlenen sınır.** `CUDA out of memory` (OOM) hatası, kartın belleğinin tükendiğini gösterir. Beklenti şudur: 131072 batch'lik aynı derin ağ 6 GB'lık kartta OOM vermeli. Ama Windows'ta NVIDIA sürücüsünün **sistem belleği yedeği** (system memory fallback) özelliği devrededir. Sürücü, GPU belleği dolduğunda ayırmayı sistem RAM'ine yönlendirir. Sonuç, OOM hatası yerine yavaşlamadır. Aşağıdaki ölçüm bunu gösterir.

```python
# g07_oom.py: (a) Windows sysmem fallback ile sınırsız görünen bellek,
# (b) set_per_process_memory_fraction ile gerçek OOM yakalama.
# Çıktı: engine/veri/b65_oom.csv
import csv, os, time
import torch
KOK = "D:/Mevcut Projeler/Kitap/engine/veri"
dev = torch.device("cuda")

def dene(batch):
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    try:
        net = torch.nn.Sequential(*[torch.nn.Sequential(
            torch.nn.Linear(1024, 1024), torch.nn.ReLU())
            for _ in range(24)]).to(dev)
        x = torch.randn(batch, 1024, device=dev)
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        net(x).sum().backward()
        torch.cuda.synchronize()
        sonuc = (torch.cuda.max_memory_allocated() / 2**20,
                 time.perf_counter() - t0, "sığdı")
    except torch.cuda.OutOfMemoryError:
        sonuc = (float("nan"), float("nan"), "OOM")
    net = x = None
    torch.cuda.empty_cache()
    return sonuc

satir = []
print("(a) sınır yok, kart 6143 MB:")
for batch in [16384, 65536, 131072]:
    mb, s, d = dene(batch)
    satir.append(("sinirsiz", batch, mb, s, d))
    print("  batch=%6d tepe=%8.0f MB süre=%6.2f s %s"
          % (batch, mb, s, d))

```

Programın devamı (satır 39–53):

```python
torch.cuda.set_per_process_memory_fraction(0.25)   # ~1536 MB sınır
print("(b) bellek sınırı %25 (~1536 MB):")
for batch in [4096, 16384]:
    mb, s, d = dene(batch)
    satir.append(("sinir_25yuzde", batch, mb, s, d))
    print("  batch=%6d tepe=%8.0f MB süre=%6.2f s %s"
          % (batch, mb, s, d))

with open(os.path.join(KOK, "b65_oom.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["kosul", "batch", "tepe_mb", "sure_s", "durum"])
    for r in satir:
        w.writerow([r[0], r[1], "" if r[2] != r[2] else "%.0f" % r[2],
                    "" if r[3] != r[3] else "%.3f" % r[3], r[4]])
```
```term
$ python g07_oom.py
(a) sınır yok, kart 6143 MB:
  batch= 16384 tepe=    1803 MB süre=  0.50 s sığdı
  batch= 65536 tepe=    6804 MB süre=  4.01 s sığdı
  batch=131072 tepe=   13492 MB süre= 35.23 s sığdı
(b) bellek sınırı %25 (~1536 MB):
  batch=  4096 tepe=     555 MB süre=  0.10 s sığdı
  batch= 16384 tepe=     nan MB süre=   nan s OOM
```

Tepe bellek, kartın 6143 MB'ını **iki katından fazla** aşıyor ama her batch "sığdı" olarak tamamlandı. Batch 131072'de süre 35,2 saniye: GPU'nun hesap süresi değil, sistem belleğine yapılan gidiş-dönüş trafiğidir. Bir eğitim betiği bu durumda çökmez, sadece yavaşlar; bu da onu fark etmeyi zorlaştırır. Bu yüzden gerçek bir OOM davranışını test etmek istersen sınırı PyTorch'a kendin koymalısın:

Bu sınırda `batch=16384` anında OOM verir. Bu ölçüm, OOM'un nasıl yakalanacağını da gösterir: `torch.cuda.OutOfMemoryError` istisnası, betiğin kendi batch boyutunu küçültüp yeniden denemesi için bir kanca sağlar. Gerçek bir eğitim döngüsünde OOM'a karşı tipik strateji, batch'i yarıya indirip gradyan birikimiyle efektif batch'i korumaktır (Bölüm 65.11).

::: not
Windows'taki sistem belleği yedeği bir kolaylık gibi görünse de bir tuzaktır. Eğitimin "çalıştığını" sanırsın, ama süre beklenenden çok uzun olduğunda sebebi budur. Bunu kontrol etmenin yolu, `torch.cuda.max_memory_allocated()` değerini kartın toplam belleğiyle karşılaştırmaktır.
:::

## 65.14 Tekrarlanabilirlik: aynı tohum, aynı sonuç mu?

Bir deneyi yeniden üretebilmek bilimin ve mühendisliğin temelidir. "Bu modeli iki kez eğittim, biri daha iyi çıktı" demek, bir bulguyu kanıtlamaz. Bu bölümde iki soruyu sorduk: aynı tohumla aynı kod, aynı sonucu verir mi, ve GPU'da bu neden bazen vermez?

Tohum ayarları tek başına yetmez; üç katman vardır. Birincisi Python, NumPy ve PyTorch tohumlarıdır (Bölüm 65.9'daki `tohumla`). İkincisi, DataLoader'ın karıştırma üretecidir (`generator=`). Üçüncüsü, GPU'daki çekirdeklerin kendisinin deterministik olup olmadığıdır. Üçüncüsü en az bilinendir ve en çok sürpriz çıkaran olandır.

GPU'da bazı işlemler **atomik toplama** kullanır: birden fazla iş parçacığı aynı bellek adresine aynı anda yazmaya çalışır ve sonuç, hangi iş parçacığının önce yazdığına bağlı olur. Kayan noktalı sayılarda toplama sırası sonucu değiştirir (kayan noktalı sayılarda `(a + b) + c` ile `a + (b + c)` aynı sonucu vermeyebilir). Aşağıdaki deney, `index_add_` ile çok sayıda çakışan yazımı 6 kez çalıştırır.

```python
# g09_tekrar.py: GPU tekrarlanabilirligi ve AMP'nin dogrulugu.
# Çıktı: engine/veri/b65_tekrar.csv
import csv, os, statistics
import torch
import torch.nn as nn
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

KOK = "D:/Mevcut Projeler/Kitap/engine/veri"
dev = torch.device("cuda")
satir = []

# (a) Atomik toplama: aynı tohum, aynı girdi, 6 tekrar.
def atomik():
    torch.manual_seed(0)
    idx = torch.randint(0, 8, (2_000_000,), device=dev)
    deg = torch.randn(2_000_000, device=dev)
    out = torch.zeros(8, device=dev)
    out.index_add_(0, idx, deg)
    return out.cpu()

sonuc = [atomik() for _ in range(6)]
farkli = len({tuple(s.tolist()) for s in sonuc})
print("index_add_ (GPU), 6 koşu, farklı sonuç sayısı:", farkli)
satir.append(("index_add_ varsayilan", farkli))
torch.use_deterministic_algorithms(True)
sonuc = [atomik() for _ in range(6)]
farkli = len({tuple(s.tolist()) for s in sonuc})
print("index_add_ deterministic=True, farklı sonuç:", farkli)
satir.append(("index_add_ deterministic", farkli))
torch.use_deterministic_algorithms(False)

# (b) Konvolüsyon geri yayılımı: iki koşu bit düzeyinde aynı mı?
def conv_gradyan():
    torch.manual_seed(0)
    c = nn.Conv2d(16, 32, 3, padding=1).to(dev)
    x = torch.randn(64, 16, 32, 32, device=dev)
    c(x).sum().backward()
    return c.weight.grad.clone().cpu()

```

Programın devamı (satır 41–80):

```python
torch.backends.cudnn.benchmark = False
torch.backends.cudnn.deterministic = True
g1, g2 = conv_gradyan(), conv_gradyan()
print("conv (deterministic=True) bit aynı mı:", torch.equal(g1, g2))
satir.append(("conv deterministic bit-aynı",
             int(torch.equal(g1, g2))))

# (c) AMP doğruluğu: 3 tohum, fp32 vs fp16 AMP; test doğruluğu ayrıca.
X, y = load_digits(return_X_y=True)
X = torch.tensor(X / 16.0, dtype=torch.float32)
y = torch.tensor(y)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2,
                                      stratify=y, random_state=0)
Xtr, ytr = Xtr.to(dev), ytr.to(dev)
Xte, yte = Xte.to(dev), yte.to(dev)

def egit(seed, amp):
    torch.manual_seed(seed)
    net = nn.Sequential(nn.Linear(64, 256), nn.ReLU(),
                        nn.Linear(256, 10)).to(dev)
    opt = torch.optim.Adam(net.parameters(), 1e-3)
    sc = torch.amp.GradScaler("cuda", enabled=amp)
    lossf = nn.CrossEntropyLoss()
    for ep in range(30):
        perm = torch.randperm(len(Xtr), device=dev)
        for i in range(0, len(Xtr), 64):
            b = perm[i:i + 64]
            with torch.autocast("cuda", dtype=torch.float16,
                                enabled=amp):
                l = lossf(net(Xtr[b]), ytr[b])
            opt.zero_grad()
            sc.scale(l).backward()
            sc.step(opt)
            sc.update()
    net.eval()
    with torch.no_grad():
        tr = (net(Xtr).argmax(1) == ytr).float().mean().item()
        te = (net(Xte).argmax(1) == yte).float().mean().item()
    return tr, te

```

Programın devamı (satır 81–101):

```python
for amp in (False, True):
    trs, tes = [], []
    for s in range(3):
        tr, te = egit(s, amp)
        trs.append(tr); tes.append(te)
    ad = "fp16-AMP" if amp else "fp32"
    print("%-9s eğitim=%.4f±%.4f  TEST=%.4f±%.4f"
          % (ad, statistics.mean(trs), statistics.pstdev(trs),
             statistics.mean(tes), statistics.pstdev(tes)))
    satir.append((ad + " egitim_dogruluk",
                  "%.4f" % statistics.mean(trs)))
    satir.append((ad + " test_dogruluk",
                  "%.4f+-%.4f" % (statistics.mean(tes),
                                  statistics.pstdev(tes))))

with open(os.path.join(KOK, "b65_tekrar.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["olcum", "deger"])
    for r in satir:
        w.writerow(r)
```
```term
$ python g09_tekrar.py
index_add_ (GPU), 6 koşu, farklı sonuç sayısı: 6
index_add_ deterministic=True, farklı sonuç: 1
conv (deterministic=True) bit aynı mı: True
fp32      eğitim=0.9928±0.0003  TEST=0.9685±0.0013
fp16-AMP  eğitim=0.9928±0.0003  TEST=0.9685±0.0013
```

Varsayılan modda altı koşunun altısı da birbirinden farklı sonuç verdi. Bu, aynı tohum ve aynı girdiyle bile GPU'nun her seferinde farklı bir toplama sırası seçtiğini gösterir. `torch.use_deterministic_algorithms(True)` açıldığında sonuç tek bir değere indi. Bu mod, deterministik olmayan işlemleri ya deterministik bir yoldan çalıştırır ya da onlar için hata verir. Bedeli hızdır, bu yüzden araştırma koşularında açılır, üretim eğitimde kapalı tutulabilir.

Evrişim (konvolüsyon) geri yayılımı, cuDNN'in seçtiği algoritmaya bağlıdır. Aşağıdaki deney, 64×16×32×32 girdili bir konvolüsyonun ağırlık gradyanını iki kez hesaplayıp bit düzeyinde karşılaştırır.

`cudnn.deterministic = True` ve `benchmark = False` ayarı, bu ölçümde iki koşunun bit düzeyinde aynı olmasını sağladı. `benchmark = True` ise cuDNN'in her girdi şekli için en hızlı algoritmayı ölçerek seçmesini sağlar; bu seçim koşudan koşuya değişebilir ve sonuçta küçük farklara yol açabilir. Genel olarak, tekrarlanabilir bir deney için `deterministic = True` ve `benchmark = False`, hızlı bir eğitim için ise tersi tercih edilir. Bu ikisinin takasını bilerek yapman gerekir.

**Hassasiyet ve tekrarlanabilirlik.** Tekrarlanabilirlik, yalnızca bit düzeyinde eşitlik değildir. Üç tohumla yapılan bir değerlendirme, tek bir tohumun şansına bağlı olmadığını gösterir. Yukarıdaki AMP deneyinde (Bölüm 65.12) üç tohumun ortalamasını ve standart sapmasını verdik; bu, tek bir sayıdan daha dürüst bir rapordur.

::: ipucu
Tekrarlanabilirlik için bir kontrol listesi: tüm tohumları ayarla (Python, NumPy, PyTorch, DataLoader üreteci), `use_deterministic_algorithms(True)` dene ve gerekirse cuBLAS için `CUBLAS_WORKSPACE_CONFIG` ortam değişkenini ayarla (bu kısım PyTorch belgelerinde yazılıdır; bu makinede denemedik), `cudnn.deterministic` ile `benchmark` ayarını kaydet, ve her deneyi birden çok tohumla raporla.
:::

## 65.15 Performans: profiler ve torch.compile

Yavaş bir eğitim döngüsünü hızlandırmadan önce neyin yavaş olduğunu bilmek gerekir. PyTorch'un `torch.profiler` aracı, her operatörün CPU ve GPU süresini, çağrı sayısını ve hangi kodun bu operatörü başlattığını gösterir. Aşağıdaki program, küçük bir CNN'in eğitim adımını beş kez profilleyip en pahalı sekiz operatörü listeler.

```python
# g11_profil.py: torch.profiler ile GPU operatör maliyeti.
# Çıktı: engine/veri/b65_profil.csv
import csv, os
import torch
import torch.nn as nn
from torch.profiler import profile, ProfilerActivity
KOK = "D:/Mevcut Projeler/Kitap/engine/veri"
dev = torch.device("cuda")
torch.manual_seed(0)
net = nn.Sequential(
    nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
    nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
    nn.Flatten(), nn.Linear(64 * 8 * 8, 256), nn.ReLU(),
    nn.Linear(256, 10)).to(dev)
opt = torch.optim.Adam(net.parameters(), 1e-3)
x = torch.randn(256, 1, 32, 32, device=dev)
y = torch.randint(0, 10, (256,), device=dev)
lossf = nn.CrossEntropyLoss()

def adim():
    opt.zero_grad()
    lossf(net(x), y).backward()
    opt.step()

```

Programın devamı (satır 27–52):

```python
for _ in range(10):
    adim()
torch.cuda.synchronize()
acts = [ProfilerActivity.CPU, ProfilerActivity.CUDA]
with profile(activities=acts) as p:
    for _ in range(5):
        adim()
    torch.cuda.synchronize()
tablo = p.key_averages()
kaba = sorted(tablo, key=lambda e: e.self_device_time_total,
              reverse=True)[:8]
print("%-34s %10s %10s %6s" % ("operatör", "GPU us/adım",
                                 "CPU us/adım", "çağrı"))
satir = []
for e in kaba:
    ad = e.key[:34]
    us = e.self_device_time_total / 5
    cpu = e.self_cpu_time_total / 5
    print("%-34s %10.1f %10.1f %6d" % (ad, us, cpu, e.count // 5))
    satir.append((ad, "%.1f" % us, "%.1f" % cpu, e.count // 5))
with open(os.path.join(KOK, "b65_profil.csv"), "w", newline="",
          encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["operator", "gpu_us_adim", "cpu_us_adim",
                "cagri_adim"])
    w.writerows(satir)
```
```term
$ python g11_profil.py
operatör                           GPU us/adım CPU us/adım  çağrı
aten::convolution_backward             1558.6      230.8      2
aten::max_pool2d_with_indices_back      761.0       68.6      2
aten::cudnn_convolution                 531.8      246.4      2
aten::threshold_backward                515.6       75.6      3
aten::add_                              376.2       85.7     10
aten::clamp_min                         327.2       73.8      3
aten::mm                                307.4      214.5      4
aten::result_type                       303.4        8.3     40
```

Tablo adım başına ortalama süreyi verir (µs). Sütunlar: GPU süresi, CPU süresi ve çağrı sayısı.

![Şekil 65.10: CNN eğitim adımında en pahalı operatörlerin GPU süresi](gorseller/b65_profil.png)

Tablo iki şey öğretir. Birincisi, GPU zamanının yarısından fazlası evrişim ve havuzlamanın geri geçişine gider; bu, CNN eğitiminin doğal darboğazıdır (Bölüm 66). İkincisi, `aten::result_type` gibi çok küçük işlemlerin 40 çağrısı, toplam 303 µs GPU zamanı üretir. Bu sayı yanıltıcı olabilir: profiler, bir çekirdeği başlatan üst operatöre ait GPU süresini atfeder; `result_type` kendisi hesap yapmaz, ama içinden başlatılan çekirdekler onun adına sayılır. Bu yüzden tabloyu okurken CPU süresi sütununa da bakmak ve bir operatörün gerçek sebebini izlemek gerekir.

Profiler, darboğazın türünü de gösterir. Bir operatörün CPU süresi GPU süresinden büyükse, GPU bekliyor demektir: çekirdek başlatma yükü ya da Python tarafındaki iş baskındır. Tersi durumda, GPU gerçekten çalışıyordur ve iyileştirme için algoritmik ya da veri türü değişikliği gerekir. Bu adımda `convolution_backward` için CPU süresi 230 µs, GPU süresi 1558 µs'dir: GPU baskındır, yani daha hızlı bir evrişim algoritması ya da daha düşük hassasiyet (AMP) işe yarar.

**torch.compile.** Küçük işlemlerin başlatma yükünü (Bölüm 65.4) azaltmanın bir yolu, birden çok işlemi tek bir çekirdekte birleştirmektir. `torch.compile` modeli bir grafik olarak yakalar ve bu birleştirmeyi otomatik yapar. Varsayılan arka uç `inductor`, çekirdekleri üretmek için **Triton** kullanır. Bu makinede Triton kurulu değildi; deneyi denediğimizde şu hatayı aldık:

```python
# g12_derleme.py: torch.compile, torch.export ve torch.jit.trace.
import os

import torch
import torch.nn as nn

torch.manual_seed(0)
net = nn.Sequential(nn.Linear(1024, 1024), nn.GELU(),
                    nn.Linear(1024, 1024), nn.GELU(),
                    nn.Linear(1024, 10)).cuda().eval()
x = torch.randn(64, 1024, device="cuda")

with torch.no_grad():
    try:
        cnet = torch.compile(net)
        cnet(x)
        print("torch.compile (inductor) çalıştı")
    except Exception as e:
        print("torch.compile BAŞARISIZ:", type(e).__name__,
              str(e).splitlines()[0][:60])
    # Grafik yakalama, Triton gerektirmeyen 'eager' arka ucuyla.
    c = torch.compile(net, backend="eager")
    print("eager backend fark:", (c(x) - net(x)).abs().max().item())

# torch.export: grafik yakalama (CPU üzerinde, dışa aktarım için).
cpu = nn.Sequential(nn.Linear(16, 8), nn.ReLU(),
                    nn.Linear(8, 2)).eval()
ex = torch.export.export(cpu, (torch.randn(4, 16),))
print("\ntorch.export grafiği (ilk düğümler):")
for n in list(ex.graph.nodes)[:6]:
    print("  ", n.op, n.target if n.op != "placeholder" else n.name)
print("export/eager fark:",
      (ex.module()(torch.ones(4, 16))
       - cpu(torch.ones(4, 16))).abs().max().item())

```

Programın devamı (satır 36–44):

```python
# TorchScript trace ve kaydet/yükle.
yol = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "model.pt")
tr = torch.jit.trace(cpu, torch.randn(4, 16))
tr.save(yol)
yuk = torch.jit.load(yol)
t = torch.randn(4, 16)
print("jit trace yükle farkı:", (yuk(t) - cpu(t)).abs().max().item())
print("model.pt bayt:", os.path.getsize(yol))
```
```term
$ python g12_derleme.py
torch.compile BAŞARISIZ: BackendCompilerFailed backend='inductor' raised:
eager backend fark: 0.0

torch.export grafiği (ilk düğümler):
   placeholder p_fn_0_weight
   placeholder p_fn_0_bias
   placeholder p_fn_2_weight
   placeholder p_fn_2_bias
   placeholder input
   call_function aten.linear.default
export/eager fark: 0.0
jit trace yükle farkı: 0.0
model.pt bayt: 7755
```

Bu bir kod hatası değil, ortam eksikliğidir: Windows'ta Triton genellikle hazır gelmez. Yani bu bölümde `inductor` ile derleme hızını ölçemedik ve bu konuda bir sayı vermeyeceğiz. Derleme yolunu ayrıca doğrulamak için arka ucu `eager` yaptığımızda grafik yakalama çalıştı ve çıktı farkı sıfır çıktı:

Bu, `torch.compile`'ın grafik yakalama katmanının çalıştığını, eksik olan şeyin yalnızca Triton çekirdek üretici olduğunu gösterir. Triton kurulu bir Linux ortamında ya da WSL2 içinde aynı kodu çalıştırmak, derlemenin gerçek hızını ölçmeye imkân verir.

::: dikkat
`torch.compile` ilk çağrıda derleme yaptığı için ilk çağrının süresi çok uzundur. Derlemenin kazancını ölçerken ilk çağrıyı ısınma olarak say, sonraki çağrıları ölç. Ölçmeden "derleme hızlandırdı" demek, hız iddiasının en yaygın hatasıdır.
:::

## 65.16 Dağıtıma köprü: TorchScript, torch.export ve ONNX

Eğitilmiş bir model, eğitim betiği olmadan, PyTorch'un Python yorumlayıcısı olmadan ya da farklı bir çalışma zamanında çalışmak zorunda kalabilir. Gömülü bir cihazda, bir C++ servisinde ya da bir ONNX çalışma zamanında. Bölüm 46'da (TinyML) mikrodenetleyicilerde çıkarım yapmanın kısıtlarını gördük; Bölüm 75'te (verimli çıkarım ve edge) bu konuyu derinleştireceğiz. Bu bölümde yalnızca dışa aktarımın temel araçlarını gösteriyoruz.

**TorchScript (jit.trace).** `torch.jit.trace`, örnek bir girdiyle modeli çalıştırır ve işlemleri bir grafik olarak kaydeder. Sonuç, Python'dan bağımsız olarak yüklenebilen bir dosyadır.

Bu küçük model (16→8→2) için kaydedilen dosya 7755 bayttır ve yüklenen modelin çıktısı orijinalle fark sıfırdır. `trace` yalnızca izlenen yolu kaydeder: girdiye bağlı bir `if` ya da döngü varsa, `trace` yalnızca o örnek için geçerli olan dalı kaydeder. Bu durumda `torch.jit.script` gerekir.

**torch.export.** Yeni yaklaşım, modeli statik ve tam bir grafik olarak yakalar; PyTorch 2.x'in önerilen dışa aktarım yoludur.

Grafikteki düğümler `placeholder` (girdi ve parametreler) ve `call_function` (işlem) türündedir. `aten.linear.default` gibi ifadeler, PyTorch'un temel işlem kümesine (ATen) indirgenmiş olduğunu gösterir. Bu temel küme, bir derleyicinin ya da bir çıkarım motorunun desteklemesi gereken işlemlerin listesidir.

**ONNX.** Açık standart olan ONNX, farklı çalışma zamanlarına (ONNX Runtime, TensorRT, OpenVINO) model taşımak için kullanılır. `torch.onnx.export` bu dışa aktarımı yapar. Bu makinede `onnx` paketi kurulu değildi ve paket indirmesi bu deneyin kapsamında değildi; bu yüzden ONNX dışa aktarımını burada **ölçmedik**. Dışa aktarılan bir ONNX modelinin çıktısını PyTorch çıktısıyla karşılaştırmak, bu bölümde gösterdiğimiz eşleşme testinin aynısıdır: aynı girdi, aynı çıktı, bir tolerans içinde.

::: not
Dağıtımda en sık yapılan hata, eğitimde kullanılan ve dışa aktarımda desteklenmeyen bir işlemi fark etmemektir. Dışa aktarılmış modeli, hedef çalışma zamanında, gerçek girdilerle, PyTorch çıktısıyla karşılaştırarak doğrula. Bu test, Bölüm 75'teki nicemleme (quantization) ile sayısal sapmayı ölçmenin de temelidir.
:::

## Çözümlü Örnekler

Bu bölümdeki dört örnek, zorluk sırasıyla ★, ★★, ★★ ve ★★★ olarak dizilmiştir. Her örnek Bölüm 5'teki altı adımı izler: anla, örnekle, kaba çöz, örüntüyü bul, iyileştir ve doğrula. Doğrulama adımında elle iz sürme tablosu bulunur. Her örnek bir varyasyon sorusuyla biter; bu soruyu yapay zekâ aracı kullanmadan çözmeni bekliyorum.

Dört örneğin sayısal değerleri aşağıdaki tek programla doğrulandı. Örnek 1, 2 ve 3'ün her sayısı bu programın çıktısındadır; Örnek 4'ün ölçümleri ayrı betiklerle alındı (aşağıda, Örnek 4'ün altında).
```python
# ex_dogrula.py: Çözümlü Örnek 1-3 için sayısal doğrulama.
import torch

# Örnek 1: permute ve dilimleme adresleri.
x = torch.arange(24).reshape(2, 3, 4)
y = x.permute(2, 0, 1)
print("x stride:", x.stride())
print("y = x.permute(2,0,1): shape", tuple(y.shape),
      "stride", y.stride())
print("y[3,1,2] =", y[3, 1, 2].item(),
      " x[1,2,3] =", x[1, 2, 3].item())
z = x[:, 1, ::2]
print("z = x[:,1,::2]: shape", tuple(z.shape),
      "stride", z.stride(), "offset", z.storage_offset())
print("z[1,1] =", z[1, 1].item(),
      " x[1,1,2] =", x[1, 1, 2].item())
print("y.is_contiguous():", y.is_contiguous())

# Örnek 2: f(x,y) = y^2 * ln(x) noktasında (2, 3).
xa = torch.tensor(2.0, dtype=torch.float64, requires_grad=True)
ya = torch.tensor(3.0, dtype=torch.float64, requires_grad=True)
f = torch.log(xa) * ya ** 2
f.backward()
print("\nf =", f.item(), " df/dx =", xa.grad.item(),
      " df/dy =", ya.grad.item())
print("elle: df/dx = y^2/x =", 9 / 2,
      " df/dy = 2y ln x =",
      6 * torch.log(torch.tensor(2.0)).item())
print("grad_fn:", type(f.grad_fn).__name__,
      [type(n).__name__ for n, _ in f.grad_fn.next_functions])

# Örnek 3: eşit olmayan mikro-batch 6 + 4 (N = 10).
torch.manual_seed(0)
lin = torch.nn.Linear(3, 2).double()
X = torch.randn(10, 3, dtype=torch.float64)
Y = torch.randint(0, 2, (10,))
ce_sum = torch.nn.CrossEntropyLoss(reduction="sum")
ce_mean = torch.nn.CrossEntropyLoss()

```

Programın devamı (satır 41–61):

```python
def gradyan(fn):
    lin.zero_grad()
    fn().backward()
    return lin.weight.grad.clone(), lin.bias.grad.clone()

def fark(a, b):
    return max((p - q).abs().max().item() for p, q in zip(a, b))

ref = gradyan(lambda: ce_mean(lin(X), Y))
lin.zero_grad()
for a, b in [(0, 6), (6, 10)]:
    (ce_sum(lin(X[a:b]), Y[a:b]) / 10).backward()
dogru = (lin.weight.grad.clone(), lin.bias.grad.clone())
lin.zero_grad()
for a, b in [(0, 6), (6, 10)]:
    (ce_mean(lin(X[a:b]), Y[a:b]) / 2).backward()
yanlis = (lin.weight.grad.clone(), lin.bias.grad.clone())
print("\neşit olmayan batch doğru:", fark(ref, dogru))
print("eşit olmayan batch yanlış (ortalama/2):", fark(ref, yanlis))
```
```term
$ python ex_dogrula.py
x stride: (12, 4, 1)
y = x.permute(2,0,1): shape (4, 2, 3) stride (1, 12, 4)
y[3,1,2] = 23  x[1,2,3] = 23
z = x[:,1,::2]: shape (2, 2) stride (12, 2) offset 4
z[1,1] = 18  x[1,1,2] = 18
y.is_contiguous(): False

f = 6.238324625039508  df/dx = 4.5  df/dy = 4.1588830833596715
elle: df/dx = y^2/x = 4.5  df/dy = 2y ln x = 4.158883094787598
grad_fn: MulBackward0 ['LogBackward0', 'PowBackward0']

eşit olmayan batch doğru: 5.551115123125783e-17
eşit olmayan batch yanlış (ortalama/2): 0.042203432992340285
```

### Örnek 1 (★): Permute ve dilimleme sonrası adres hesabı

`x = torch.arange(24).reshape(2, 3, 4)` tensörü için iki görünüm var: `y = x.permute(2, 0, 1)` ve `z = x[:, 1, ::2]`. `y[3, 1, 2]` elemanı hangi `x` elemanıdır? `z`nin stride'ı, offset'i ve `z[1, 1]`in storage adresi nedir? Hiçbir görünüm için veri kopyalanıp kopyalanmadığını söyle.

**Adım 1 — Anla.** İstenen üç şey var: `y[3,1,2]`nin `x`teki karşılığı, `z`nin offset ve stride'ları, ve `z[1,1]`in storage adresi. Bu sorular stride'ın tanımından çözülebilir; kopya olup olmadığına da bakılacak.

**Adım 2 — Örnekle.** `x[0,0,0] = 0` ve `x[0,0,1] = 1` biliniyor. `y[k,i,j] = x[i,j,k]` olduğundan `y[1,0,0] = x[0,0,1] = 1` olmalı. Bu, permute'un eksenleri gerçekten yer değiştirdiğini kontrol eder.

**Adım 3 — Kaba çöz.** `x`in stride'ı `(12, 4, 1)`dir. `permute(2, 0, 1)` yalnızca eksen sırasını ve stride'ları değiştirir: `y`nin stride'ı `(1, 12, 4)` olur. Adres formülü `i·1 + j·12 + k·4` olur; `y[3,1,2]` için `3 + 12 + 8 = 23`. `z = x[:, 1, ::2]` için offset `x[0,1,0]`ın adresi olan `4`, stride ise `(12, 2)`dir; `z[1,1]` için adres `4 + 12 + 2 = 18`.

**Adım 4 — Örüntü.** Permute, stride'ların sırasını değiştirir ama bellekteki hiçbir şeye dokunmaz. Dilimleme ise offset'i ilk elemanın adresine kaydırır ve her eksende stride'ı istenen adımla çarpar. İkisi de kopyasız çalışır. Bu, Bölüm 65.2'de gördüğümüz kuralın iki farklı uygulamasıdır.

**Adım 5 — İyileştir.** `y`yi düzleştirmek (`reshape(-1)`) bitişik olmayan bir görünümü tek boyuta indirgeyemez; bu yüzden PyTorch kopya yapar. Bunu önlemek için düzleştirmeden önce bir kez `contiguous()` çağırmak da bir kopya demektir. Yani "kopyasız düzleştirme" bu durumda yoktur; kopya kaçınılmazsa maliyetini bilerek ödemek gerekir.

**Adım 6 — Doğrula.** Kod ile elle hesabı karşılaştır:

| Adım | Değer |
|---|---|
| `y[3,1,2]` adresi: `3·1 + 1·12 + 2·4` | 23 |
| `x[1,2,3]` adresi: `1·12 + 2·4 + 3·1` | 23 |
| `z` offset | 4 |
| `z[1,1]` adresi: `4 + 1·12 + 1·2` | 18 |
| `x[1,1,2]` adresi: `1·12 + 1·4 + 2·1` | 18 |

Kod çıktısı: `y[3,1,2] = 23`, `x[1,2,3] = 23`, `z` şekli `(2, 2)`, stride `(12, 2)`, offset `4`, `z[1,1] = 18`, `x[1,1,2] = 18`. Hepsi elle hesapla eşleşiyor. `y.is_contiguous()` `False` döndü, bu da permute sonrası bitişik olmadığını doğrular.

**Bunu AI'sız yazabilir misin?** `x = torch.arange(60).reshape(3, 4, 5)` için `y = x.transpose(0, 2)` ve `z = x[1:, :, 3]` görünümlerinde `y[4, 2, 1]` ve `z[1, 2]` elemanlarının `x`teki karşılıklarını, `z`nin offset ve stride'ını elle hesapla. Sonra `torch` ile doğrula.

### Örnek 2 (★★): f(x, y) = y²·ln x: grad_fn zinciri ve elle gradyan

`f(x, y) = y² · ln(x)` ifadesi için `(x, y) = (2, 3)` noktasında `f`nin değerini, iki kısmi türevini ve `grad_fn` zincirini bul. Sonucu `backward()` ile doğrula.

**Adım 1 — Anla.** Gerekenler: `f(2, 3)`, `∂f/∂x`, `∂f/∂y` ve autograd'ın kurduğu düğüm zinciri. Üç sonuç da elle hesaplanabilir ve PyTorch ile karşılaştırılabilir.

**Adım 2 — Örnekle.** `y` sabit tutulup `x` değiştirilirse, `ln x` eğrisi yavaş büyür; `x = 2`de eğim `1/x = 0,5` olur. Bu nedenle `∂f/∂x` değeri `y²·0,5 = 9·0,5 = 4,5` civarında olmalı. Benzer şekilde `y` değiştirilince `f` ikinci dereceden büyür; `∂f/∂y` değeri `2y·ln x`tir.

**Adım 3 — Kaba çöz.** Zincir kuralıyla: `∂f/∂x = y² · (1/x) = 9/2 = 4,5`. `∂f/∂y = 2y · ln x = 6 · ln 2 = 6 · 0,693147 = 4,158883`. Değer `f = ln(2) · 9 = 6,238325`.

**Adım 4 — Örüntü.** `f`, bir çarpımdır: `ln x` ile `y²` çarpılır. Çarpım kuralı, her çarpanın türevini diğerinin değeriyle çarpmayı söyler. Autograd bu çarpımı bir `MulBackward0` düğümü olarak kaydeder, girdileri ise `LogBackward0` (ln x) ve `PowBackward0` (y²) düğümleridir. Yani grafik, elle yaptığımız ayrıştırmanın aynısıdır.

**Adım 5 — İyileştir.** Elle türevde hata yapma olasılığını azaltmak için `float64` kullan ve `grad_fn` zincirini yazdır: bu, kurduğun hesabın doğru yapıda olduğunu gösterir. Ayrıca bağımsız bir yol olarak `y`yi sabit tutup `x` üzerinden tek değişkenli türevi ayrıca hesaplayabilirsin.

**Adım 6 — Doğrula.** İz tablosu:

| Büyüklük | Elle | PyTorch (`backward`) | Fark |
|---|---|---|---|
| `f(2, 3) = ln(2)·9` | 6,238325 | 6,238325 | ~0 |
| `∂f/∂x = y²/x` | 4,5 | 4,5 | 0 |
| `∂f/∂y = 2y·ln x` | 4,158883 | 4,158883 | ~10⁻¹⁶ |
| `f.grad_fn` | `MulBackward0` | `MulBackward0` | — |
| Girdi düğümleri | `LogBackward0`, `PowBackward0` | aynı | — |

Üç sayısal değer ve düğüm zinciri eşleşiyor. Bu, grafiğin yapısının ve geri adımın doğru olduğunu gösterir.

**Bunu AI'sız yazabilir misin?** `g(x, y) = sin(x) · e^(xy)` için `(x, y) = (1, 0)` noktasında `∂g/∂x` ve `∂g/∂y` değerlerini elle hesapla, sonra `grad_fn` zincirini çiz ve `backward` ile karşılaştır. Hangi düğümlerin `∂g/∂y` hesabında yer aldığını söyleyebiliyor musun?

### Örnek 3 (★★): Eşit olmayan mikro-batch ile gradyan birikimi

10 örneklik bir batch'i iki parçaya böldün: 6 örnek ve 4 örnek. Her parça için kaybı `CrossEntropyLoss` ile (varsayılan ortalama) hesaplayıp `/2` ile ölçeklersen, gradyan tek bir 10'luk batch ile aynı olur mu? Değilse doğru ağırlık nedir?

**Adım 1 — Anla.** Karşılaştırılacak iki gradyan var: tek 10'luk batch'in gradyanı (referans) ve birikim yoluyla elde edilen gradyan. İstenen, hangi ölçekleme ile ikisinin aynı çıktığını bulmak.

**Adım 2 — Örnekle.** Parçalardan birinin 6 örneği olsun. Parça kaybı `L₁` (6 örneğin ortalaması), tüm batch'in kaybı `L = (6·L₁ + 4·L₂)/10` olmalıdır. Eşit ağırlık (`1/2`) kullanılırsa, 6 örnekli parça 4 örnekli parçayla aynı ağırlığı alır; bu, örneklerin katkısını çarpıtır.

**Adım 3 — Kaba çöz.** Doğru ağırlık, her parçanın örnek sayısıyla orantılıdır: 6 örneklik parça için `6/10`, 4 örneklik parça için `4/10`. Bu, `reduction="sum"` ile parça toplamını alıp toplam örnek sayısına (10) bölmekle aynıdır.

**Adım 4 — Örüntü.** Gradyan birikimi bir toplamdır. Toplamın her terimi, o terimin örnek sayısına göre ağırlıklandırılmış olmalıdır. Eşit boyutlu parçalarda `1/k` bu ağırlığı verir; eşitsiz parçalarda ağırlık boyuta bağlıdır. Bu nedenle `1/k` sabit bir kural değil, eşit boyut varsayımına bağlı bir kısayoldur.

**Adım 5 — İyileştir.** Kodu, parçaların boyutundan bağımsız hâle getir: `reduction="sum"` ile parça kaybını topla, sonra tüm batch'in örnek sayısına böl. Bu yaklaşım bölüm boyutu ne olursa olsun doğru kalır.

**Adım 6 — Doğrula.** İz tablosu (gradyan farkı, en büyük mutlak değer):

| Yöntem | Parça ağırlıkları (6 ve 4) | Referansla fark |
|---|---|---|
| Tek batch (referans) | — | — |
| Doğru: `sum` / 10 | `6/10`, `4/10` | `5,6·10⁻¹⁷` |
| Yanlış: ortalama / 2 | `1/2`, `1/2` | `4,2·10⁻²` |

Doğru yöntem makine epsilonu mertebesinde eşleşir; yanlış yöntem gradyanı `4·10⁻²` kadar sapırır. Bu sapma, eğitim eğrisinde zor fark edilen bir sistematik hatadır.

**Bunu AI'sız yazabilir misin?** Batch 13 örnek ve parçalar 5, 5, 3 ise her parçanın kaybını hangi katsayıyla ölçeklemen gerektiğini hesapla. Bu katsayıların toplamı kaç olmalı ve neden?

### Örnek 4 (★★★): Yavaş bir eğitim döngüsünü profilleyip düzeltmek

Bir CNN eğitim döngüsü GPU'da yavaş çalışıyor. Döngü `num_workers=0` kullanıyor, her adımda `loss.item()` çağırıyor ve her adımda tahminleri CPU'ya kopyalayıp doğruluğu hesaplıyor. Sebebi bul, düzelt ve önce/sonra süreyi ölç.

**Adım 1 — Anla.** Ölçülecek şey bir epoch'un süresidir. Döngüde üç şüpheli var: worker yokluğu (veri hazırlığı ana iş parçacığında), her adımda senkronizasyon (`.item()`), ve her adımda CPU'ya kopya. Hangisinin ne kadar etkili olduğunu ayırmak gerekiyor.

**Adım 2 — Örnekle.** Önce basit bir ölçüm: GPU'nun veri beklediği süre ile hesap süresini ayır. Bölüm 65.8'deki `turu` fonksiyonu tam bunu yapar. Bu makinede, `num_workers=0` ile epoch'un büyük kısmı veri beklemekle geçmişti (%82); bu, darboğazın veri hattında olduğunu gösterir.

**Adım 3 — Kaba çöz.** Üç değişikliği öner: worker sayısını 4'e çıkar, `pin_memory=True` kullan, ve kaybı ile doğruluğu GPU üzerinde biriktirip senkronizasyonu yalnızca epoch sonunda yap.

**Adım 4 — Örüntü.** Darboğaz, GPU'yu bekletmektir. Senkronizasyon bekletir, ama yalnızca GPU'nun işi bittikten sonra bekler; asıl beklenen şey, bir sonraki batch'in hazırlanmasıdır. Bu yüzden worker sayısı, senkronizasyondan daha büyük bir kaldıraçtır. Ölçüm bunu doğrular.

**Adım 5 — İyileştir.** Düzeltilmiş döngüde: `num_workers=4`, `pin_memory=True`, `persistent_workers=True` (worker'lar yeniden başlatılmaz), kayıp ve doğruluk GPU tensörü olarak biriktirilir, senkronizasyon epoch sonunda bir kez yapılır. Ölçüm için DataLoader bir kez kurulur ve bir ısınma epoch'u koşulur; böylece worker başlatma süresi ölçüme girmez.

**Adım 6 — Doğrula.** Örnek 4 iki betikle ölçüldü: `ex4_dongu.py` (yavaş ve düzeltilmiş döngü) ve `ex4_ayrik.py` (worker ve senkronizasyonun ayrı etkisi). İki betik dönüşümlü olarak üç kez çalıştırıldı; her koşuda yavaş ve hızlı döngü aynı koşu içinde ölçüldüğü için oran anlamlıdır. Aşağıda tam çıktısı verilen koşu (koşu 2) ortanca orana sahip olanıdır. Üç koşunun oran aralığı şöyledir:

| Ölçüm | Koşu 1 | Koşu 2 | Koşu 3 | Aralık |
|---|---|---|---|---|
| Yavaş / düzeltilmiş oranı (`ex4_dongu`) | 4,35 | 4,35 | 4,95 | 4,35 – 4,95 |
| Yavaş epoch süresi (s) | 1,865 | 2,000 | 2,521 | 1,87 – 2,52 |
| Düzeltilmiş epoch süresi (s) | 0,428 | 0,460 | 0,510 | 0,43 – 0,51 |

Ölçüm betikleri şunlardır: `ex4_dongu.py` ve `ex4_ayrik.py`.

```python
# ex4_dongu.py: Çözümlü Örnek 4 - yavaş ve düzeltilmiş döngü.
# Worker başlatma süresi ölçüme girmez: DataLoader bir kez kurulur,
# bir ısınma epoch'u koşulur, sonra yalnızca epoch süresi alınır.
import statistics
import time

import torch
from torch.utils.data import DataLoader

from g08_veri import DigitGenis, ag

def epoch_yavas(dl, net, opt, dev):
    lossf = torch.nn.CrossEntropyLoss()
    toplam = 0.0
    for x, y in dl:
        x, y = x.to(dev), y.to(dev)
        out = net(x)
        loss = lossf(out, y)
        opt.zero_grad()
        loss.backward()
        opt.step()
        toplam += loss.item()                # her adımda senkron
        tahmin = out.argmax(1).cpu().numpy()  # her adımda kopya
        _ = (tahmin == y.cpu().numpy()).mean()
    return toplam

```

Programın devamı (satır 29–43):

```python
def epoch_hizli(dl, net, opt, dev):
    lossf = torch.nn.CrossEntropyLoss()
    toplam = torch.zeros((), device=dev)
    for x, y in dl:
        x = x.to(dev, non_blocking=True)
        y = y.to(dev, non_blocking=True)
        out = net(x)
        loss = lossf(out, y)
        opt.zero_grad()
        loss.backward()
        opt.step()
        toplam += loss.detach()              # senkron yok
    return toplam.item()

```

Programın devamı (satır 44–69):

```python
if __name__ == "__main__":
    dev = torch.device("cuda")
    torch.manual_seed(0)
    ds = DigitGenis(4096)
    dl_y = DataLoader(ds, batch_size=64, shuffle=True,
                      num_workers=0)
    dl_h = DataLoader(ds, batch_size=64, shuffle=True, num_workers=4,
                      pin_memory=True, persistent_workers=True)
    sonuc = {}
    for ad, fn, dl in (("yavas", epoch_yavas, dl_y),
                       ("hizli", epoch_hizli, dl_h)):
        net = ag().to(dev)
        opt = torch.optim.Adam(net.parameters(), 1e-3)
        fn(dl, net, opt, dev)                # ısınma
        torch.cuda.synchronize()
        sure = []
        for _ in range(3):
            t0 = time.perf_counter()
            fn(dl, net, opt, dev)
            torch.cuda.synchronize()
            sure.append(time.perf_counter() - t0)
        sonuc[ad] = statistics.median(sure)
        print("%-6s medyan epoch = %.3f s  (tekrarlar: %s)"
              % (ad, sonuc[ad], ", ".join("%.3f" % s for s in sure)))
    print("oran yavas/hizli = %.2f"
          % (sonuc["yavas"] / sonuc["hizli"]))
```

```python
# ex4_ayrik.py: Çözümlü Örnek 4 - worker ve senkron etkisinin ayrımı.
import statistics
import time

import torch
from torch.utils.data import DataLoader

from ex4_dongu import epoch_hizli, epoch_yavas
from g08_veri import DigitGenis, ag

if __name__ == "__main__":
    dev = torch.device("cuda")
    torch.manual_seed(0)
    ds = DigitGenis(4096)
    dl0 = DataLoader(ds, batch_size=64, shuffle=True, num_workers=0)
    dl4 = DataLoader(ds, batch_size=64, shuffle=True, num_workers=4,
                     pin_memory=True, persistent_workers=True)
    vaka = [("worker yok + item (yavas)", epoch_yavas, dl0),
            ("worker=4 + item", epoch_yavas, dl4),
            ("worker yok + senkronsuz", epoch_hizli, dl0),
            ("worker=4 + senkronsuz (hizli)", epoch_hizli, dl4)]
    for ad, fn, dl in vaka:
        net = ag().to(dev)
        opt = torch.optim.Adam(net.parameters(), 1e-3)
        fn(dl, net, opt, dev)
        torch.cuda.synchronize()
        sure = []
        for _ in range(3):
            t0 = time.perf_counter()
            fn(dl, net, opt, dev)
            torch.cuda.synchronize()
            sure.append(time.perf_counter() - t0)
        print("%-32s medyan = %.3f s"
              % (ad, statistics.median(sure)))
```

Tam çıktı, koşu 2 (önce `ex4_dongu`, sonra `ex4_ayrik`):

```term
$ python ex4_dongu.py
yavas  medyan epoch = 2.000 s  (tekrarlar: 1.745, 2.000, 2.239)
hizli  medyan epoch = 0.460 s  (tekrarlar: 0.460, 0.461, 0.457)
oran yavas/hizli = 4.35
```

```term
$ python ex4_ayrik.py
worker yok + item (yavas)        medyan = 2.320 s
worker=4 + item                  medyan = 0.475 s
worker yok + senkronsuz          medyan = 1.829 s
worker=4 + senkronsuz (hizli)    medyan = 0.646 s
```

Ayrıştırma ölçümleri, üç koşunun aralığıyla birlikte:

| Konfigürasyon | Koşu aralığı (s) | Yavaşa göre oran |
|---|---|---|
| Yavaş: worker yok + `item` (her adım) | 2,31 – 2,34 | 1 |
| Yalnız worker=4 | 0,40 – 0,62 | 3,7 – 5,8 kat |
| Yalnız senkronsuz (worker yok) | 1,56 – 1,87 | 1,25 – 1,49 kat |
| Worker=4 + senkronsuz (düzeltilmiş) | 0,40 – 0,65 | 3,6 – 5,8 kat |

Bu tablo iki şey gösterir. Birincisi, bu iş yükünde asıl darboğaz worker yokluğudur: veri dönüşümü ana iş parçacığında yapılırken GPU her adımda beklemektedir. İkincisi, worker yokken her adımda `loss.item()` ve CPU'ya kopyayı kaldırmak da 1,25–1,49 kat kazandırır; worker=4 varken senkronizasyonun etkisi ölçüm gürültüsü içinde kalır, çünkü darboğaz artık veri hattıdır. Yani hangi değişikliğin ne kadar kazandırdığı, darboğazın nerede olduğuna bağlıdır; bu yüzden her değişikliği tek tek ölçmek gerekir.

::: not
Bu ölçümler paylaşımlı, yüklü bir makinede alındı; diğer yazarların CPU işleri aynı anda çalışıyordu. Mutlak süreler değişkendir; bu yüzden tabloda aralıklar verildi. Ders olan orandır ve darboğazın yeri: veri hattı (CPU) bu iş yükünde GPU'dan önce tıkanır.
:::

**Bunu AI'sız yazabilir misin?** Bir eğitim döngüsünde her epoch sonunda doğrulama kaybını yazdırmak istiyorsun, ama her adımda `loss.item()` çağırmak istemiyorsun. Döngünün hangi kısmını değiştirirsin ve neden? Ayrıca döngü sonunda `item()` çağrısının hangi tensörde yapılmasını önerirsin?

## Kendin Yap Projeleri

::: dikkat
Bu projelerde yapay zekâ aracı kullanma. Kodu, testleri ve ölçümleri kendin yaz. Amaç, bu bölümdeki kavramları bir mülakatta ya da boş bir IDE'de yeniden kurabilmektir. Bir hata bulursan, önce hatayı kendin çöz; bu, bu bölümün en değerli kısmıdır.
:::

### Proje 1 (★★): Sıfırdan mini-Trainer

**Amaç.** Bölüm 65.9–65.14'te parça parça gördüğün eğitim döngüsünü tek bir sınıf olarak kurmak: karışık hassasiyet, gradyan birikimi, checkpoint ile devam, en iyi modeli kaydetme, CSV günlüğü ve deterministik mod.

**Yapılacak / Beklenen davranış.** `MiniTrainer` sınıfı şu arayüzü sağlasın: `fit(epochs)`, `save(yol)`, `load(yol)`. Eğitim, `accum` parametresiyle gradyan birikimi yapsın; `amp=True` ile fp16 AMP kullansın; her epoch sonunda doğrulama kaybını izleyip en iyi modeli ayrı bir dosyaya yazsın; her epoch'un eğitim kaybı, doğrulama kaybı, doğruluk ve öğrenme oranını bir CSV dosyasına eklesin. `deterministic=True` ayarında tohumlar ve `use_deterministic_algorithms` açılsın.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Checkpoint'te, Bölüm 65.10'daki altı parçayı (model, optimizer, zamanlayıcı, epoch, torch RNG, DataLoader üreteci) hepsini kaydet. Birikimde kayıp ölçeğini `1/accum` yerine, parçanın örnek sayısına göre `sum` ile hesapla (Örnek 3). AMP için `GradScaler`ı yalnızca fp16 kipinde etkinleştir. Testleri ayrı bir dosyada yaz.

**Başarı kriterleri.** (1) Birikimli eğitimde (`accum=4`, batch 64) ve tek 256'lık batch'te gradyan farkı `10⁻⁶`nın altındadır (BatchNorm yokken). (2) Checkpoint'ten devam eden koşu, kesintisiz koşuyla bit düzeyinde aynı son ağırlıkları verir. (3) `deterministic=True` ile aynı tohumla iki koşu bit düzeyinde aynıdır. (4) AMP açıkken doğrulama doğruluğu fp32'den `0,01`den fazla sapmaz (üç tohumla rapor et). (5) CSV dosyası her epoch için bir satır içerir ve en iyi model yalnızca doğrulama kaybı düştüğünde güncellenir.

### Proje 2 (★★★): Eşleşme test paketi ve özel autograd Function

**Amaç.** Bir NumPy MLP'nin (ileri ve geri geçiş elle yazılmış) PyTorch karşılığıyla katman katman eşleştiğini kanıtlayan bir test paketi yazmak; ardından kendi özel autograd `Function`ını ekleyip sayısal türevle doğrulamak.

**Yapılacak / Beklenen davranış.** Üç katmanlı bir MLP için (64→64→32→10), her katmanın ileri çıktısını, her parametrenin gradyanını ve son kaybı PyTorch ile karşılaştıran testler yaz. Ardından aktivasyon olarak `softplus` yerine kendi seçtiğin, sayısal olarak zor bir fonksiyonu (ör. büyük girdilerde taşan bir üslü ifade ya da `log(σ(x))`) kararlı biçimde yazan bir `Function` ekle. Geri geçişi elle türet, `gradcheck` ile doğrula ve PyTorch modülünde kullan. Son olarak bir forward hook ile her katmanın aktivasyon istatistiğini topla ve bir "ölü nöron" oranı hesapla.

**Önerilen yaklaşım (ipucu).** Testleri çift duyarlıkta (`float64`) yaz; tolerans `10⁻⁹` civarında olsun. Her katmanın gradyanını hem NumPy'da elle, hem PyTorch'ta `backward` ile hesaplayıp karşılaştır. Kararlı fonksiyon için, büyük girdilerde ne olduğunu önce naif formülle göster (inf/nan), sonra kararlı formülü yaz (Bölüm 65.6).

**Başarı kriterleri.** (1) Tüm katman çıktıları ve gradyanları `10⁻⁹` göreli toleransla eşleşir. (2) Özel `Function` için `gradcheck` `True` döner. (3) Naif formül ile kararlı formül, büyük girdide farklı davranışı (inf/nan karşılığı sayı) açıkça gösterilir. (4) Ölü nöron oranı, en az iki tohumla ortalama ve sapmasıyla raporlanır. (5) Test paketi, tek bir komutla hatasız çalışır ve ilk başarısızlıkta hangi katmanın sapmaya başladığını söyler.

### Ek Alıştırmalar

Aşağıdaki problemler cevapsızdır. Her birini önce kendin çöz, sonra kontrol etmek için bu bölümdeki kodları kullan.

1. (★) `x = torch.arange(12).reshape(3, 4)` için `x.t().reshape(-1)` bir kopya mı? `storage` adresini `data_ptr` ile karşılaştırarak göster ve nedenini bitişik olmama kavramıyla açıkla.
2. (★) `x = torch.arange(6.0).reshape(2, 3)` için `x[:, 1:]` görünümünün `offset` ve `stride` değerlerini elle hesapla, sonra kodla doğrula.
3. (★) `a = torch.tensor(1.0, requires_grad=True)` ve `b = a * 3` için `b.backward()` çağrısını iki kez yap. `a.grad` değeri kaç olur ve neden? Üçüncü bir `zero_grad` sonrası ne olur?
4. (★★) Mülakat: `view` ile `reshape` arasındaki farkı, bir `transpose` sonrası hangisinin hata verdiğini ve hangisinin kopya ürettiğini örnekle açıkla.
5. (★★) Mülakat: Bir eğitim döngüsünde `zero_grad()` çağrısını unutursan, model neden her epoch farklı bir yöne gider? Birikim hangi adımda toplanır ve sonuç hangi gradyanla güncellenir?
6. (★★) Mülakat: `model.eval()` ne yapar, ve sadece `model.eval()` çağırıp `torch.no_grad()` çağırmazsan ne olur? İkisinin etkisini ayır.
7. (★★) Mülakat: GPU zamanlamasında `torch.cuda.synchronize()` neden gereklidir? Synchronize olmadan `time.perf_counter()` ile ölçtüğün süre neyi ölçer?
8. (★★) Mülakat: `float16` ile `bfloat16` arasında, bir eğitim için neden `bfloat16` daha güvenlidir? Aralık ve hassasiyet farkını `finfo` değerleriyle açıkla.
9. (★★) `nn.Module` içine bir `torch.tensor` atayıp `nn.Parameter` olarak sarmadığında, optimizer bu tensörü güncellemez. Bunu `named_parameters()` çıktısıyla göster ve `register_buffer` ile farkı açıkla.
10. (★★★) Mülakat: Gradient checkpointing hangi bellek ve hesap takasını yapar? `n` katmanlı bir ağı `k` bloğa bölersen, saklanan aktivasyon sayısı ve ek ileri geçiş sayısı için kabaca bir ifade yaz.
11. (★★★) Mülakat: Karışık hassasiyet eğitiminde ana ağırlık kopyasını neden `float32`de tutarız? Küçük bir güncellemenin (`lr·g`) `float16` ağırlığa eklendiğinde kaybolduğu bir sayısal örnek ver.
12. (★★★) `torch.compile` ile bir döngüyü hızlandırmadan önce neyi ölçmen gerekir? İlk çağrının derleme süresi ile sonraki çağrıların süresini ayıran bir ölçüm protokolü tasarla.

## Kod Okuma Egzersizi

Bu bölümde gördüğümüz `nn.Module` kayıt mekanizmasını, PyTorch 2.6.0'ın kurulu kaynağında (`torch/nn/modules/module.py`, `zero_grad`) izleyeceğiz. Kaynak, PyTorch 2.6.0+cu124 paketinin yerel kurulumundan alınmıştır (`C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\site-packages\torch\nn\modules\module.py`). Aşağıdaki kesit, satır 2904–2913'ten birebir kopyadır. Docstring (2888–2895) ve `_is_replica` için `DataParallel` uyarısı (2896–2902) kısaltıldı; bu kısımların davranışa katkısı yoktur, kesit bu nedenle yalnızca döngüyü içerir.

```python
        for p in self.parameters():
            if p.grad is not None:
                if set_to_none:
                    p.grad = None
                else:
                    if p.grad.grad_fn is not None:
                        p.grad.detach_()
                    else:
                        p.grad.requires_grad_(False)
                    p.grad.zero_()
```

Bu döngü, modüldeki her parametre için gradyanı sıfırlar. `set_to_none=True` varsayılandır ve gradyanı `None` yapar: bellek ayrılmaz, sonraki `backward` yeni bir tensör yazar. `set_to_none=False` ise mevcut gradyan tensörünü yerinde `zero_()` ile sıfırlar.

**Sorular — cevaplamadan geçme:**

1. `zero_grad` neden `self.parameters()` üzerinde döner, `self.state_dict()` üzerinde değil? İki yöntem arasındaki fark nedir ve hangisinin buffer'ları içerdiğini söyle.
2. `p.grad` yalnızca `None` değilse işlem yapılır. Hiç `backward` çağrılmamış bir parametre için `zero_grad` ne yapar, ve bu neden bir hata vermez?
3. `set_to_none=True` ile `set_to_none=False` arasında bellek ve hız açısından fark nedir? Büyük bir modelde hangisi tercih edilir ve neden?
4. `p.grad.grad_fn is not None` kontrolü neden var? Bir gradyan tensörünün kendisi bir hesap grafiğinin parçası olabilir mi, ve bu durumda `detach_()` ne yapar?
5. Bu döngü, Bölüm 65.5'te gördüğümüz gradyan birikimini nasıl tersine çevirir? `zero_grad` çağrılmazsa, `backward` her çağrıda hangi tensöre hangi değeri ekler?
6. Optimizer'ın kendi `zero_grad` metodu da var. Modülün `zero_grad`ı ile optimizer'ınki arasında hangi parametre kümesini etkileme farkı olabilir? Eğitimde hangisini çağırmak yeterlidir ve neden?

## Bölüm Özeti

- **Tensör**, bellekte düz bir storage ile onun üzerindeki bir görünümden (şekil, stride, offset) oluşur. `view` kopyasız çalışır ama bitişik olmayan tensörde hata verir; `reshape` gerekirse kopyalar; `transpose` ve dilimleme yalnızca stride ve offset'i değiştirir.
- **Yayın (broadcasting)** NumPy'daki kurallarla çalışır; stride'ı 0 yapılan boyutlar bellek kopyalamaz. Yerinde işlemler (`_` sonekli), autograd'ın ihtiyaç duyduğu ara değerleri değiştirirse hata verir.
- **GPU zamanlaması** asenkron çalışır: `synchronize` olmadan ölçülen süre yalnızca komut gönderme süresidir (bu makinede yaklaşık 157 kat yanlış). Küçük işlemlerde GPU başlatma yükü CPU'dan pahalıdır.
- **Autograd**, işlemleri `grad_fn` düğümleri olarak kaydeder ve `backward` ile zincir kuralını geriye uygular. Gradyanlar birikir; bu yüzden her adımda `zero_grad` gerekir. Özel `Function` ile geri adımı kendin yazabilir ve `gradcheck` ile doğrulayabilirsin.
- **nn.Module** parametreleri, buffer'ları ve alt modülleri bir ağaçta tutar; `state_dict` bu ağacın durumudur. `train()` ve `eval()` dropout ve BatchNorm'un davranışını değiştirir. Bölüm 63'teki NumPy MLP ile aynı denklemler, float64'te `10⁻¹⁷` düzeyinde eşleşir.
- **Veri hattı** (Dataset ve DataLoader) çoğu zaman darboğazdır: worker sayısını artırmak, bu makinede epoch süresini 0,95 s'den 0,15 s'ye indirdi. Windows'ta `if __name__ == "__main__":` korumasını unutma.
- **Eğitim döngüsü** train ve eval modlarını, metrik kaydını ve checkpoint'i doğru sırada yönetir. Checkpoint'e model, optimizer, zamanlayıcı ve **her RNG üretecinin** durumunu yazmak, devam eden koşuyu bit düzeyinde aynı kılar.
- **Karışık hassasiyet** (AMP) bu RTX 3060'ta batch 1024'te adımı yaklaşık 2,3 kat hızlandırdı. fp16 için `GradScaler` alt taşmayı önler. Bellek kazancı aktivasyonların baskın olduğu derin ağlarda görünür; checkpointing bellek tasarrufu sağlar ama süreyi artırır. Windows'ta sürücünün sistem belleği yedeği OOM'u gizler; sınırı kendin koy.
- **Tekrarlanabilirlik** için tohumlar yetmez: GPU'nun atomik toplamaları ve cuDNN algoritma seçimi de sonucu değiştirir. `use_deterministic_algorithms` ve `cudnn.deterministic` bu farkları kapatır.
- **Performans ve dağıtım**: `torch.profiler` darboğazın CPU mu GPU mu olduğunu gösterir. `torch.compile`, Windows'ta Triton eksikliği nedeniyle derlenemedi; `torch.jit.trace` ve `torch.export` çalıştı. ONNX bu makinede ölçülmedi.

**Sonraki bölümde:** Bölüm 66, CNN ve Bilgisayarlı Görü, bu bölümdeki evrişim katmanlarını ve `nn.Module` yapısını kullanarak evrişimi sıfırdan açıklayacak. Bu bölümün profilinde gördüğümüz `convolution_backward` operatörünün neden GPU zamanının yarısını aldığını, ve ResNet ile transfer öğrenmenin bu araçlarla nasıl kurulduğunu göreceğiz.

::: mulakat
1. `view` ile `reshape` arasındaki fark nedir? Bir `transpose`'tan sonra hangisi hata verir, hangisi kopya üretir ve bunu bellek düzeniyle nasıl açıklarsın?
2. `zero_grad()` neden gereklidir? Gradyanlar neden birikir ve bu tasarım hangi kullanım durumunu mümkün kılar?
3. `model.eval()` ile `torch.no_grad()` arasındaki fark nedir? Doğrulamada ikisini birlikte kullanmak neden gerekir?
4. GPU'da bir işlemin süresini `time.perf_counter()` ile ölçerken `synchronize()` neden gerekir? Ölçüm yanlış olduğunda hangi sayıyı görürsün?
5. Veri yükleyicide `num_workers` artırınca bazen hız kazanılır, bazen kazanılmaz. GPU'nun veri beklemesini ölçen bir protokol nasıl kurarsın?
6. Karışık hassasiyet eğitiminde `GradScaler` neden gerekir? `bfloat16` kullanırsan bu gereksinim neden ortadan kalkar?
7. Checkpoint'ten devam eden bir eğitimin kesintisiz eğitimle aynı sonucu vermesi için hangi durumların kaydedilmesi gerekir? Birini atlarsan ne olur?
8. Gradient checkpointing'in bellek ve hesap takası nedir? Hangi durumda kullanmak mantıklı değildir?
:::
