%% kisim_no: XVI
%% kisim_ad: ML Mühendisliği & Araştırma
%% bolum_no: 76
%% baslik: GPU Programlama & Dağıtık Eğitim

## Giriş: GPU'yu bilmeden GPU'da eğitmek

Bölüm 65'te PyTorch'ta bir modeli GPU'ya taşımayı, tensörleri kopyalamayı ve eğitim döngüsünü kurmayı gördük. Orada GPU'yu bir kara kutu gibi kullandık: `.to("cuda")` yazdık, süre kısaldı, ama neden kısaldığını tam olarak anlatamadık. Bu bölüm o kara kutuyu açıyor. Bir GPU'nun neden yüzlerce iş parçacığını aynı anda çalıştırdığını, belleğin neden hesaptan daha pahalı olabildiğini ve birden çok GPU'nun aynı modeli nasıl eğittiğini ölçerek göreceğiz.

Bu konu mülakatta ve iş hayatında sık çıkar. "GPU'da eğitim neden yavaş kaldı?" sorusunun cevabı çoğu zaman GPU'nun hesap gücü değil, veri yolu, bellek erişimi ya da iletişimdir. "Bir modeli 6 GB'lık karta sığdırabilir misin?" sorusu ise bir hesap sorusudur: parametre, gradyan ve optimizasyon durumlarının bayt sayısını bilmeyen biri bunu yanıtlayamaz. Savunma sanayiinde bu ayrım doğrudan önemlidir. Bir İHA'nın görüntü işleme modelini kendi altyapında, dışarıya veri çıkarmadan eğitmek istediğinde, elindeki birkaç GPU'nun gerçek kapasitesini bilmen gerekir.

Bölüm 53'te GPU'yu kavramsal olarak tanıttık ve SIMT ile bellek hiyerarşisinin farkını anlattık (Bölüm 53.11). Bölüm 25'te önbellek satırlarını ve blok matris çarpımını gördük (Bölüm 25.2 ve 25.7). Bu bölümde o kavramları GPU'da ölçeceğiz. Kullanacağımız araçlar Python tarafında numba (`numba.cuda`) ve PyTorch'tur. Çekirdekleri CUDA C olarak yazıp derlemek istedik, ama bu makinede CUDA Toolkit ve `nvcc` yoktu; bu yüzden çekirdekleri Python içinde yazdık.

::: not
Bu bölümdeki tüm ölçümler tek bir makinede alındı: Windows 11, NVIDIA GeForce RTX 3060 Laptop GPU (6 GB, hesaplama yeteneği 8.6, sürücü 616.64), Python 3.12.10, PyTorch 2.6.0+cu124 ve numba 0.65.1. Sayılar bu makineye özgüdür. Her deneyde 3 ısınma koşusu ve 7 ile 15 arasında ölçüm yaptık; tabloda medyan değerleri verdik. Aynı betiği iki kez çalıştırınca sonuçlar birkaç yüzde on kadar değişti; bunun nedeni masaüstü uygulamalarının aynı GPU'yu kullanmasıdır.
:::

## 76.1 CPU ve GPU: iki farklı tasarım felsefesi

CPU'nun işi, tek bir iş parçacığının tek bir işi mümkün olan en kısa sürede bitirmesidir. Bu yüzden CPU'da büyük önbellekler, dal tahmini ve sıra dışı yürütme gibi donanımlar bulunur (Bölüm 24.6 ve 24.7). Bunların hepsi tek bir akışın gecikmesini (latency) düşürmek için vardır. GPU'nun işi ise çok büyük miktarda işi birim zamanda bitirmektir; buna verim (throughput) diyoruz. GPU birkaç büyük çekirdek yerine çok sayıda basit hesap birimi kullanır ve bellek gecikmesini, başka iş parçacıklarını çalıştırarak gizler.

Şekil 76.1 bu iki tasarımı yan yana koyuyor. Soldaki CPU'da birkaç güçlü çekirdek ve büyük önbellek vardır. Sağdaki GPU'da çok sayıda küçük birim bir arada çalışır. NVIDIA bu modele SIMT (single instruction, multiple threads) der: bir komut, bir grup iş parçacığı tarafından aynı anda yürütülür. Bu, Bölüm 24.8'deki SIMD'nin iş parçacığı düzeyindeki karşılığıdır.

![Şekil 76.1: CPU, gecikmeyi düşürmek için az sayıda güçlü çekirdek kullanır; GPU, verimi artırmak için çok sayıda basit birim ve yüksek bant genişlikli bellek kullanır.](gorseller/b76_cpu_gpu.png)

Donanımın temel değerlerini (SM sayısı, warp boyutu, blok başına en fazla iş parçacığı) 76.3'teki ilk betik yazdırıyor; bölümün geri kalanındaki ölçümlerde bu değerlere atıf yapacağız.

Windows'ta GPU'ya kod göndermek için önce bir çalışma ortamı kurmak gerekir. Bu makinede CUDA Toolkit kurulu değildi. Numba'nın CUDA derleyicisi olan libNVVM ve CUDA çalışma zamanı (cudart) için pip paketlerini kullandık: `nvidia-cuda-nvcc-cu12` ve `nvidia-cuda-runtime-cu12`. Numba `cudart.dll` adını aradığı için pip paketindeki `cudart64_12.dll` dosyasının adı değiştirilmiş bir kopyasını kullanıyoruz. Bu iş aşağıdaki küçük yardımcı dosyada yapılıyor.

```python
# -*- coding: utf-8 -*-
"""Windows'ta numba CUDA icin DLL yollarini ayarlar.

CUDA Toolkit yoksa pip ile gelen nvidia-* paketleri kullanilir:
  nvidia-cuda-nvcc-cu12 (libNVVM), nvidia-cuda-runtime-cu12 (cudart).
numba 'cudart.dll' arar; pip paketi 'cudart64_12.dll' getirir,
bu yuzden adi degistirilmis bir kopya cudashim/ altina konur.
"""

import os
import shutil
import nvidia

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = list(nvidia.__path__)[0]
os.environ["CUDA_PATH"] = os.path.join(BASE, "cuda_nvcc")
os.add_dll_directory(os.path.join(BASE, "cuda_nvcc", "nvvm", "bin"))

SHIM = os.path.join(HERE, "cudashim")
os.makedirs(SHIM, exist_ok=True)
_hedef = os.path.join(SHIM, "cudart.dll")
if not os.path.exists(_hedef):
    shutil.copy(
        os.path.join(BASE, "cuda_runtime", "bin", "cudart64_12.dll"),
        _hedef,
    )
os.add_dll_directory(SHIM)
```

Zamanlama için ortak bir yardımcı yazdık. GPU işlerinin süresini duvar saatiyle ölçmek yanıltıcıdır, çünkü çekirdek başlatma asenkrondur. Bu yüzden CUDA olaylarını (event) kullanıyoruz; ısınma koşularından sonra süreleri toplayıp medyanını alıyoruz. Numba için aynı işi `cuda.event` ile yapan bir sürüm de var.

```python
# -*- coding: utf-8 -*-
"""Ortak zamanlama yardimcilari: CUDA olaylariyla medyan sure (ms)."""

import statistics
import torch

def medyan_ms_torch(fn, tekrar=15, isinma=3):
    """fn() calisma suresinin medyani; CUDA olaylariyla olculur."""
    for _ in range(isinma):
        fn()
    torch.cuda.synchronize()
    sure = []
    for _ in range(tekrar):
        a = torch.cuda.Event(enable_timing=True)
        b = torch.cuda.Event(enable_timing=True)
        a.record()
        fn()
        b.record()
        b.synchronize()
        sure.append(a.elapsed_time(b))
    return statistics.median(sure), min(sure), max(sure)

def medyan_ms_numba(cuda, fn, tekrar=15, isinma=3):
    """Numba cekirdekleri icin ayni olcum (cuda.event)."""
    for _ in range(isinma):
        fn()
    cuda.synchronize()
    sure = []
    for _ in range(tekrar):
        a = cuda.event(timing=True)
        b = cuda.event(timing=True)
        a.record()
        fn()
        b.record()
        b.synchronize()
        sure.append(cuda.event_elapsed_time(a, b))
    return statistics.median(sure), min(sure), max(sure)
```

Şimdi ilk çekirdeği yazıyoruz. Vektör toplama, GPU'nun en basit programıdır: her iş parçacığı tek bir eleman toplar. Kod iki kısımdan oluşur: çekirdek (`topla`) ve ana akış. Çekirdek, numba'nın `@cuda.jit` süslemesiyle derleniyor.

```python
# -*- coding: utf-8 -*-
"""Bolum 76 - Deney 0: ortam ve ilk cekirdek (vektor toplama)."""
import _cudaenv  # noqa: F401  (Windows DLL yollari)
import numpy as np
import torch
from numba import cuda

@cuda.jit
def topla(x, y, out):
    i = cuda.grid(1)
    if i < out.size:
        out[i] = x[i] + y[i]

def main():
    print("torch:", torch.__version__)
    print("torch CUDA:", torch.cuda.is_available())
    dev = cuda.get_current_device()
    print("numba GPU:", dev.name.decode())
    print("compute capability:", dev.compute_capability)
    n = 1 << 20
    x = cuda.to_device(np.arange(n, dtype=np.float32))
    y = cuda.to_device(np.ones(n, dtype=np.float32))
    out = cuda.device_array(n, dtype=np.float32)
    topla[(n + 255) // 256, 256](x, y, out)
    sonuc = out.copy_to_host()
    dogru = np.allclose(sonuc, np.arange(n, dtype=np.float32) + 1)
    print("n =", n, "dogru:", dogru)
    print("ilk 4 deger:", sonuc[:4])

if __name__ == "__main__":
    main()
```

Betiği çalıştırdığımızda GPU'nun görüldüğünü, numba'nın çekirdeği derlediğini ve sonucun doğru olduğunu görürüz. Bu adım, sonraki bütün ölçümlerin temelidir.

```term
$ python b76_00_ortam.py
torch: 2.6.0+cu124
torch CUDA: True
numba GPU: NVIDIA GeForce RTX 3060 Laptop GPU
compute capability: (8, 6)
n = 1048576 dogru: True
ilk 4 deger: [1. 2. 3. 4.]
```

Bu bölümde CUDA C kodu derleyemedik, çünkü `nvcc` ve `cl.exe` bu makinede bulunamadı; `torch.utils.cpp_extension.load_inline` da bu yüzden denenmedi. Triton Windows'ta kurulamadığı için `torch.compile` ile ilgili bölüm 65.15'te gösterildiği gibi çalışmıyor. Bu nedenle çekirdekleri numba ile yazıyoruz. CUDA C'ye alışkınsan, numba'daki her satırın bir C karşılığı olduğunu bil: `cuda.grid(1)` ifadesi C'deki `blockIdx.x * blockDim.x + threadIdx.x` ile aynıdır. Aşağıdaki parça derlenmiş değildir; yalnızca karşılığı göstermek içindir.

```c
/* derlenmedi: bu makinede nvcc yok; yalnizca kavram icin */
__global__ void topla(const float *x, const float *y,
                      float *out, int n) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < n) out[i] = x[i] + y[i];
}
/* baslatma: topla<<<(n + 255) / 256, 256>>>(x, y, out, n); */
```

## 76.2 CUDA programlama modeli: ızgara, blok, warp

Bir GPU çekirdeği (kernel) her iş parçacığı için aynı fonksiyonu çalıştırır. Hangi iş parçacığının hangi veriyi işleyeceğini kimliğinden anlar. İş parçacıkları üç düzeyde örgütlenir. En alt düzeyde iş parçacığı (thread) vardır. Bunlar 32'li gruplar hâlinde warp adı verilen birimlerde çalışır; NVIDIA'da warp boyutu 32'dir ve bu değer ölçümle de doğrulandı (cihaz bilgisi betiğinde `Warp boyutu: 32`). Warp'lar bloklarda (block) toplanır; bu makinede bir blok en fazla 1024 iş parçacığı alabiliyor. Bloklar da ızgarada (grid) düzenlenir. Şekil 76.2 bu hiyerarşiyi gösteriyor.

![Şekil 76.2: Izgara bloklardan, bloklar warp'lardan, warp'lar 32 iş parçacığından oluşur. Bir warp içinde iş parçacıkları aynı komutu aynı anda yürütür.](gorseller/b76_izgara_blok_warp.png)

Bir çekirdeği başlatırken ızgara ve blok boyutunu verirsin. Numba'da bu `cekirdek[blok_sayisi, iş_parçacığı_sayısı](argümanlar)` biçimindedir. Global indeks, `cuda.grid(1)` ile hesaplanır ve bu, C'deki `blockIdx.x * blockDim.x + threadIdx.x` ile aynıdır. Örneğin 1000 elemanlı bir diziyi 256'lık bloklarla işlemek için `ceil(1000 / 256) = 4` blok başlatılır; 4 blok 1024 iş parçacığı eder ve fazla olan 24 iş parçacığı `if i < n` korumasıyla atlanır. Bu hesap Çözümlü Örnek 1'de adım adım yapılıyor.

Warp'un önemi, dallanmada (branch) ortaya çıkar. Bir warp içindeki 32 iş parçacığı aynı anda aynı komutu çalıştırdığı için, bir `if` farklı iş parçacıklarını farklı yollara gönderirse donanım iki yolu da sırayla çalıştırır ve her iş parçacığı kendi yolunda olmadığı zaman bekler. Buna dallanma ayrışması (branch divergence) denir. Warp'un tamamı aynı yolu izlediyse maliyet yoktur. Bu bölümün ilk deneyinde bu etkiyi ölçtük (kod 76.3'te, sonuçları 76.3'ün sonunda).

Ölçüm sırasında bir tuzakla karşılaştık ve bunu burada anlatmak isteriz. İlk denememizde iki dal da yalnızca bir satır aritmetik içeriyordu ve dallanma ayrışmalı ile warp-uniform sürümler arasında fark çıkmadı. Derleyici bu kısa dalları koşulsuz hesaplayıp sonucu seçen koda (predikasyon) çevirmişti; yani dallanma yoktu. Dalları döngü içeren hâle getirince, derleyici bu dönüşümü yapamadı ve ölçülebilir fark ortaya çıktı. Ders şudur: bir dallanmanın maliyetini tahmin etmeden önce, derleyicinin ne ürettiğine bakmak ya da ölçmek gerekir.

Warp düzeyinde bir başka araç da kaydırma (shuffle) komutlarıdır. Bir warp içindeki iş parçacıkları, paylaşılan belleğe yazmadan birbirlerinin yazmaçlarından veri okuyabilir. Bu, 76.4'teki indirgeme çekirdeğinde kullanılıyor.

Çekirdek başlatmanın bir maliyeti de var. Her başlatma, Python'dan sürücüye ve oradan GPU'ya bir komut yolculuğu gerektirir. Bölüm 65.4'te küçük tensörlerde GPU'nun CPU'dan neden yavaş kaldığını görmüştük; bu bölümde aynı konuyu çekirdek sayısı ve CUDA graph üzerinden 76.7'de yeniden ele alacağız.

## 76.3 Bellek hiyerarşisi: birleşik erişim ve bant genişliği

GPU'nun belleği tek bir katman değildir. En hızlısı iş parçacığına özel yazmaçlardır (register). Blok içinde paylaşılan bellek (shared memory) aynı bloktaki iş parçacıklarının ortak kullandığı, programcının yönettiği küçük ve hızlı bir alandır. L1 ve L2 önbellekler donanım tarafından yönetilir. En alttaki, kartın asıl belleği olan global bellek (VRAM) ise büyük ama görece yavaştır. Bu makinede global bellek 6 GB'tır. Şekil 76.3 bu katmanları ve kabaca konumlarını gösterir. Şekilde yalnızca global bellek için bir sayı var (ölçülen yaklaşık 280 GB/s). Yazmaç, paylaşılan bellek ve önbellek bant genişliklerini ölçmedik, bu yüzden onlar için sayı vermiyoruz.

![Şekil 76.3: GPU bellek hiyerarşisi. Üst katmanlar küçük ve hızlıdır, alt katmanlar büyük ve yavaştır. Global bellek için ölçülen değer 280 GB/s civarıdır.](gorseller/b76_bellek_hiyerarsisi.png)

Global bellekten veri okumanın verimliliği erişim düzenine bağlıdır. Bir warp'taki 32 iş parçacığı ardışık adreslere (örneğin `x[i]`, i = 0..31) eriştiğinde, donanım bu erişimleri birkaç bellek işleminde birleştirir. Buna birleşik erişim (coalesced access) denir. Erişim adımlıysa (`x[i*s]`), her iş parçacığı farklı bir bellek sektörüne düşer ve donanım, yararlı bir baytı geri almak için bütün sektörü getirmek zorunda kalır. Genel bilgi olarak, NVIDIA GPU'larında bellek işlemleri 32 baytlık sektörler hâlinde yapılır.

Bu etkiyi ölçen betik aynı zamanda dallanma ayrışmasını ve cihaz-cihaz kopya bant genişliğini de ölçüyor. Dört parçaya bölerek veriyoruz. İlk parça cihaz bilgisi, adımlı erişim ve ölçüm fonksiyonlarını içerir.

```python
# -*- coding: utf-8 -*-
"""Bolum 76 - Deney 1: bellek erisimi, dallanma, bant genisligi."""

import _cudaenv  # noqa: F401
import csv
import os
import numpy as np
import torch
from numba import cuda, float32, int64
from olcum import medyan_ms_numba, medyan_ms_torch

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"
TPB = 256  # blok basina is parcacigi

@cuda.jit
def okuma_adimli(x, out, s):
    # i. parcacik x[i*s] okur: s=1 birlesik, s>1 adimli erisim
    i = cuda.grid(1)
    if i < out.size:
        out[i] = x[i * s] * 2.0

@cuda.jit
def dallanma_ayrismali(out, n_it):
    # Ayni warp'ta parcaciklar farkli dallara gider (tek/cift).
    # Dallar dongu icerdigi icin derleyici kosulsuz koda cevirmez.
    i = cuda.grid(1)
    v = float32(i & 7)
    if (cuda.threadIdx.x & 1) == 0:
        for _ in range(n_it):
            v = v * 1.0001 + 0.5
    else:
        for _ in range(n_it):
            v = v * 0.9999 - 0.5
    out[i] = v

@cuda.jit
def dallanma_uniform(out, n_it):
```

İkinci parçada iki dallanma çekirdeği var. Dalların her birinde bir döngü bulunuyor; böylece derleyici dalları koşulsuz hesaplayıp seçmek yerine gerçek dallanma üretiyor.

```python
    # Dal warp'a gore sabit: warp'larin yarisi A, yarisi B yapar
    i = cuda.grid(1)
    v = float32(i & 7)
    if ((cuda.threadIdx.x >> 5) & 1) == 0:
        for _ in range(n_it):
            v = v * 1.0001 + 0.5
    else:
        for _ in range(n_it):
            v = v * 0.9999 - 0.5
    out[i] = v

def main():
    props = cuda.get_current_device()
    print("GPU:", props.name.decode())
    print("Compute capability:", props.compute_capability)
    print("SM sayisi:", props.MULTIPROCESSOR_COUNT)
    print("Warp boyutu:", props.WARP_SIZE)
    print(
        "Blok basina en fazla is parcacigi:",
        props.MAX_THREADS_PER_BLOCK,
    )
    print(
        "Bellek veri yolu (genel bilgi): 192 bit, 7001 MHz, ~336 GB/s"
    )
    print()

    # --- 1) Birlesik vs adimli erisim ---
    n = 1 << 22  # 4 M eleman, 16 MB faydali veri
    filo = []
    rows = []
    print("s   ms(medyan)   faydali GB/s   cekilen GB/s")
    for s in [1, 2, 4, 8, 16, 32]:
        x = cuda.to_device(
            np.random.default_rng(76).random(n * s, dtype=np.float32)
        )
        out = cuda.device_array(n, dtype=np.float32)
        blok = (n + TPB - 1) // TPB
        ms, _, _ = medyan_ms_numba(
            cuda, lambda: okuma_adimli[blok, TPB](x, out, s)
```

Üçüncü parça adımlı erişim deneyini yürütür. Her adım `s` için 4 milyon elemanlı bir okuma yapılır; dizi `s` kat büyütülür, böylece okunan elemanlar aynı sayıda olur ama sektör kullanımı değişir.

```python
        )
        # Faydali: n okuma + n yazma (4 B'lik elemanlar)
        faydali = 8 * n / (ms * 1e-3) / 1e9
        # Cekilen: GPU her okumada en az 32 B'lik sektor getirir; bir
        # sektorde 32/(4s) faydali eleman varsa okumalar birlesir.
        sektor_bayt = n * min(32, 4 * s) + 4 * n
        sektor = sektor_bayt / (ms * 1e-3) / 1e9
        rows.append(
            (s, round(ms, 4), round(faydali, 2), round(sektor, 2))
        )
        print(
            f"{s:<3} {ms:10.4f}   {faydali:10.2f}     {sektor:10.2f}"
        )
        del x, out
    with open(
        os.path.join(VERI, "b76_bellek_adimli.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["adim", "ms", "faydali_gbps", "cekilen_gbps"])
        w.writerows(rows)

    # --- 2) Kopya bant genisligi (cihaz-cihaz) ---
    m = 1 << 25  # 128 MB
    a = torch.rand(m, device="cuda")
    ms, _, _ = medyan_ms_torch(lambda: a.clone())
    # clone: bir okuma + bir yazma = 2 * 4m bayt
    kopya = 2 * 4 * m / (ms * 1e-3) / 1e9
    print(f"\nCihaz-cihaz kopya: {ms:.3f} ms, {kopya:.1f} GB/s")
    with open(
        os.path.join(VERI, "b76_kopya_bant.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["islem", "gbps"])
        w.writerow(["cihaz_kopya", round(kopya, 2)])
```

Son parça kopya bant genişliğini ve dallanma oranını hesaplar, sonuçları CSV'ye yazar.

```python

    # --- 3) Dallanma ayrismasi ---
    thr = 256
    blok = (1 << 20) // thr
    out = cuda.device_array(blok * thr, dtype=np.float32)
    t_ayris, _, _ = medyan_ms_numba(
        cuda, lambda: dallanma_ayrismali[blok, thr](out, 2000)
    )
    t_uni, _, _ = medyan_ms_numba(
        cuda, lambda: dallanma_uniform[blok, thr](out, 2000)
    )
    print(f"Dallanma ayrismali: {t_ayris:.3f} ms")
    print(f"Warp-uniform dal  : {t_uni:.3f} ms")
    print(f"Oran (ayrismali/uniform): {t_ayris / t_uni:.2f}")
    with open(
        os.path.join(VERI, "b76_dallanma.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["varyant", "ms"])
        w.writerow(["ayrismali", round(t_ayris, 4)])
        w.writerow(["warp_uniform", round(t_uni, 4)])

if __name__ == "__main__":
    main()
```

Betiğin çıktısı şöyle:

```term
$ python b76_01_bellek.py
GPU: NVIDIA GeForce RTX 3060 Laptop GPU
Compute capability: (8, 6)
SM sayisi: 30
Warp boyutu: 32
Blok basina en fazla is parcacigi: 1024
Bellek veri yolu (genel bilgi): 192 bit, 7001 MHz, ~336 GB/s

s   ms(medyan)   faydali GB/s   cekilen GB/s
1       0.2181       153.84         153.84
2       0.2673       125.55         188.32
4       0.3441        97.52         243.81
8       0.5652        59.37         267.16
16      0.5581        60.12         270.56
32      0.5550        60.46         272.06

Cihaz-cihaz kopya: 0.905 ms, 296.5 GB/s
Dallanma ayrismali: 41.110 ms
Warp-uniform dal  : 20.957 ms
Oran (ayrismali/uniform): 1.96
```

Adımlı erişim tablosunda iki sayıyı ayırmak gerekir. "Faydalı GB/s" sadece programın gerçekten ihtiyaç duyduğu baytları sayar: n okuma ve n yazma. "Çekilen GB/s" ise GPU'nun sektörler yüzünden fiilen hareket ettirdiği baytları sayar. `s = 1` için ikisi aynıdır. `s` büyüdükçe faydalı bant genişliği yaklaşık 154 GB/s'den 60 GB/s'e düşüyor, çekilen bant genişliği ise 270 GB/s civarında kalıyor. Yani bellek yolu tıkanmamış, sadece her 4 baytlık faydalı veri için 32 baytlık sektör taşınıyor. Şekil 76.4 bu iki eğriyi ve ölçülen kopya değerini gösteriyor.

Bu bölümde teorik tepe değeri olarak 336 GB/s kullandık. Bu değer, kartın bellek saatinden (`nvidia-smi` ile 7001 MHz) ve 192 bitlik veri yolundan hesaplanır; bu iki değer de genel bilgi olarak alındı ve bu makinede üretici tablosuyla ayrıca doğrulanmadı. Cihaz-cihaz kopyada ölçtüğümüz 296,5 GB/s, bu tepe değerinin yaklaşık yüzde 88'idir. Kopyada hem okuma hem yazma yapıldığı için toplam trafik 2 × 128 MB'tır.

![Şekil 76.4: Adımlı erişimde faydalı bant genişliği düşer, çekilen bant genişliği ölçülen kopya değerine yakın kalır. Yatay çizgiler ölçülen kopya ve teorik tepe değeridir.](gorseller/b76_adimli_bant.png)

Dallanma deneyi ise 1,96 kat fark gösterdi. İki dalda da eşit iş yapılıyor; ayrışmalı sürümde aynı warp'ın her iki yolu sırayla çalıştırması gerekiyor, uniform sürümde ise warp'ların yarısı bir yolu, diğer yarısı öbür yolu çalıştırıyor. Teorik oran 2'dir ve ölçüm buna yakın çıktı.

Bu bölümün en önemli bellek dersi şudur: bant genişliği tıkanmış görünse de, faydalı işin oranı çok düşük olabilir. Bu yüzden bir çekirdeği optimize etmeden önce, hangi baytların gerçekten gerektiğini ve hangilerinin yalnızca sektör taşıdığını ayırt etmelisin. Bölüm 25.2'de önbellek satırının blok blok geldiğini anlatmıştık; GPU'da bu, sektör düzeyinde aynı etkidir.

## 76.4 Çekirdekler: indirgeme ve işgal sezgisi

Indirgeme (reduction), bir diziyi tek bir değere indirgemektir: toplam, maksimum, ortalama. Eğitimde kayıp toplamı, batch normalizasyonu istatistikleri ve softmax'in paydası bu işlemlere dayanır. GPU'da indirgemeyi üç aşamada yazdık. İlk sürümde paylaşılan bellek vardır ama adresleme ayrışmalıdır: `tid % (2s) == 0` olan iş parçacıkları toplama yapar, böylece bir warp içinde yalnızca birkaç iş parçacığı aktif kalır. İkinci sürümde adresleme sıralıdır: ilk `s` iş parçacığı çalışır. Üçüncü sürümde son beş adım warp içinde kaydırma komutlarıyla yapılır; paylaşılan bellek ve senkronizasyon yalnızca warp toplamlarını birleştirmek için gerekir.

Üç çekirdek ve bir kütüphane fonksiyonu aynı diziyi toplar. Dizi 2^24 eleman (64 MB) ve rastgele değerlerden oluşur; sonuçlar bir float64 referansla karşılaştırılır. Kod üç parçadan oluşur: çekirdekler, bloklar halinde çağıran `indirge` fonksiyonu ve ana akış.

```python
# -*- coding: utf-8 -*-
"""Bolum 76 - Deney 2: indirgeme (toplama) cekirdekleri."""

import _cudaenv  # noqa: F401
import csv
import os
import numpy as np
import torch
from numba import cuda, float32
from olcum import medyan_ms_numba, medyan_ms_torch

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"
TPB = 256

@cuda.jit
def naif(x, out, n):
    # v1: paylasilan bellek, ama ayrismali adresleme (tid % (2s) == 0)
    sd = cuda.shared.array(TPB, float32)
    tid = cuda.threadIdx.x
    i = cuda.blockIdx.x * TPB + tid
    if i < n:
        sd[tid] = x[i]
    else:
        sd[tid] = float32(0)
    cuda.syncthreads()
    s = 1
    while s < TPB:
        if tid % (2 * s) == 0:
            sd[tid] += sd[tid + s]
        cuda.syncthreads()
        s *= 2
    if tid == 0:
        out[cuda.blockIdx.x] = sd[0]

@cuda.jit
def sirali(x, out, n):
    # v2: sirali adresleme (tid < s): aktif iş parçacıkları bitisik
    sd = cuda.shared.array(TPB, float32)
```

Çekirdek kodunun devamı: sıralı adresleme ve warp kaydırma sürümü. Warp kaydırmasında `shfl_down_sync` her iş parçacığına bir üst lane'in değerini getirir ve tam maske (`0xFFFFFFFF`) kullanılır, çünkü warp'ın tüm iş parçacıkları katılmalıdır.

```python
    tid = cuda.threadIdx.x
    i = cuda.blockIdx.x * TPB + tid
    if i < n:
        sd[tid] = x[i]
    else:
        sd[tid] = float32(0)
    cuda.syncthreads()
    s = TPB // 2
    while s > 0:
        if tid < s:
            sd[tid] += sd[tid + s]
        cuda.syncthreads()
        s //= 2
    if tid == 0:
        out[cuda.blockIdx.x] = sd[0]

@cuda.jit
def warp(x, out, n):
    # v3: son adimlar warp icinde shuffle (senkron yok)
    ws = cuda.shared.array(8, float32)  # TPB // 32 = 8 warp
    tid = cuda.threadIdx.x
    i = cuda.blockIdx.x * TPB + tid
    v = float32(0)
    if i < n:
        v = x[i]
    off = 16
    while off > 0:
        v += cuda.shfl_down_sync(0xFFFFFFFF, v, off)
        off //= 2
    lane = tid & 31
    wid = tid >> 5
    if lane == 0:
        ws[wid] = v
    cuda.syncthreads()
    if wid == 0:
        v = float32(0)
        if lane < 8:
            v = ws[lane]
        off = 16
```

Yardımcı fonksiyon bir çekirdeği kalan değer tek olana dek tekrar başlatır. Bu, ızgara boyutunu her turda `ceil(n / 256)` ile küçültmek demektir.

```python
        while off > 0:
            v += cuda.shfl_down_sync(0xFFFFFFFF, v, off)
            off //= 2
        if lane == 0:
            out[cuda.blockIdx.x] = v

def indirge(cekirdek, x):
    """Bloklar halinde kismi toplam; kalan 1 olana dek tekrarla."""
    n = x.size
    buf = x
    while n > 1:
        blok = (n + TPB - 1) // TPB
        cikis = cuda.device_array(blok, dtype=np.float32)
        cekirdek[blok, TPB](buf, cikis, n)
        buf, n = cikis, blok
    return buf

def main():
    n = 1 << 24  # 16 M eleman, 64 MB
    rng = np.random.default_rng(76)
    host = rng.random(n, dtype=np.float32)
    ref = float(host.astype(np.float64).sum())
    print(f"n = {n}, referans (float64) = {ref:.3f}")
    x = cuda.to_device(host)
    tx = torch.from_numpy(host).cuda()

    rows = []
    print("varyant              ms(medyan)   bagil hata")
    for ad, k in [
        ("naif (ayrismali)", naif),
        ("sirali adresleme", sirali),
        ("warp shuffle", warp),
    ]:
        sonuc = indirge(k, x).copy_to_host()[0]
        bagil = abs(float(sonuc) - ref) / ref
        ms, _, _ = medyan_ms_numba(cuda, lambda: indirge(k, x))
        rows.append((ad, round(ms, 4), f"{bagil:.2e}"))
        print(f"{ad:<20} {ms:10.4f}   {bagil:.2e}")
```

Ana akış dört sürümü çalıştırır, her birinin süresini ve bağıl hatasını yazdırır.

```python
    ms, _, _ = medyan_ms_torch(lambda: tx.sum())
    bagil = abs(float(tx.sum().item()) - ref) / ref
    rows.append(
        ("torch.sum (kutuphane)", round(ms, 4), f"{bagil:.2e}")
    )
    print(f"{'torch.sum':<20} {ms:10.4f}   {bagil:.2e}")
    # Karsilastirma: sirali float32 toplam (CPU), hata birikimi.
    seq = float(np.cumsum(host, dtype=np.float32)[-1])
    bagil = abs(seq - ref) / ref
    rows.append(("CPU sirali float32", "", f"{bagil:.2e}"))
    print(f"{'CPU sirali float32':<20} {'-':>10}   {bagil:.2e}")

    with open(
        os.path.join(VERI, "b76_indirgeme.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["varyant", "ms", "bagil_hata"])
        w.writerows(rows)

if __name__ == "__main__":
    main()
```

Çıktı:

```term
$ python b76_02_indirgeme.py
n = 16777216, referans (float64) = 8389075.498
varyant              ms(medyan)   bagil hata
naif (ayrismali)         0.9390   5.98e-08
sirali adresleme         0.9011   5.98e-08
warp shuffle             0.5151   5.98e-08
torch.sum                0.2560   5.98e-08
CPU sirali float32            -   1.45e-05
```

Süreler bir koşudan diğerine yüzde on beş civarında değişti; dört ayrı koşuda naif sürüm 0,86 ile 0,96 ms, sıralı adresleme 0,82 ile 0,90 ms, warp kaydırma 0,45 ile 0,52 ms arasında çıktı. Bu nedenle sıralamayı tek bir koşuya değil, bu aralıklara göre okumalısın. Warp kaydırmalı sürüm, naif sürümün yaklaşık yarısı süre ile çalıştı. Kütüphane fonksiyonu (`torch.sum`) yine daha hızlıdır; onun neden hızlı olduğunu bilmiyoruz, çünkü kaynak kodunu ölçmedik ve bu konuda varsayımda bulunmak istemiyoruz. Şekil 76.5 ortalama süreleri gösteriyor.

![Şekil 76.5: Dört indirgeme sürümünün medyan süreleri (2^24 float32). Warp kaydırma, paylaşılan bellekli sıralı sürümün yaklaşık yarısı süre ile çalışır.](gorseller/b76_indirgeme.png)

Doğruluk konusunda bir gözlem önemli. Üç GPU sürümünün bağıl hatası aynı (5,98e-08) çıktı. Bu, sonucun float32'ye yuvarlanmasından kaynaklanıyor: 8,39 milyon civarındaki bir float32 sayının iki komşu değeri arasındaki aralık 1'dir, yani sonucu en yakın değere yuvarlamak en fazla 0,5 hata yapar. Bağıl hata olarak bu, 6e-08 civarıdır. Buna karşılık aynı diziyi CPU'da sıralı bir float32 toplamla (`np.cumsum`) topladığımızda hata 1,45e-05 oldu; bu, GPU'nun ağaç biçimli toplamının hatasından yaklaşık 240 kat büyüktür. Bölüm 53.10'da kayan noktada birleşme sırasının sonucu değiştirdiğini görmüştük; burada aynı ilkeyi GPU'da gözlemledik.

İşgal (occupancy) sezgisi, bir SM'de aynı anda kaç warp'ın canlı tutulabildiğini anlatır. Bu sayı, blok başına iş parçacığı sayısı, çekirdeğin kullandığı yazmaç sayısı ve blok başına paylaşılan bellek miktarı tarafından sınırlanır. Yüksek işgal, bellek gecikmesini gizlemek için iyidir, ama her zaman en hızlı çekirdek anlamına gelmez. Bu bölümde işgali doğrudan ölçmedik; profiler bu kurulumda GPU çekirdek etkinliklerini kaydetmediği için (76.7'ye bak) bu değer için bir ölçümümüz yok. Sezgi olarak şunu bil: blok boyutunu 256 gibi 32'nin katı bir değerde tutmak, warp'ların yarım kalmasını önler.

## 76.5 Matris çarpımı: naif, döşemeli ve roofline

Matris çarpımı, derin öğrenmenin neredeyse her katmanında yapılır: tam bağlı katmanlar, dikkat (attention) ve konvolüsyonun matris biçimine dönüştürülmüş hâli. Bölüm 48'de BLAS'ın bu işi nasıl hızlandırdığını anlatmıştık (Bölüm 48.14). Burada aynı işin GPU'daki üç sürümünü karşılaştırıyoruz: naif çekirdek, paylaşılan bellekle döşemeli (tiled) çekirdek ve `torch.matmul`, yani NVIDIA'nın cuBLAS kütüphanesi.

Naif sürümde her çıktı elemanını bir iş parçacığı hesaplar ve ona gereken satırı ve sütunu global bellekten okur. Her çarpım-toplama işleminde iki sayı okunur: 8 bayt, 2 flop. Yani aritmetik yoğunluk (arithmetic intensity) 0,25 flop/bayt'tır. Bölüm 53.9'daki roofline modeline göre bu, bellek bant genişliğiyle sınırlı bir çekirdek demektir: performans en fazla `bant × yoğunluk` olabilir.

Döşemeli sürümde her blok T × T boyutunda parçaları (tile) paylaşılan belleğe kopyalar. Bir kopyanın her elemanı T çarpım için kullanılır, böylece global okuma T kat azalır. Ideal durumda yoğunluk T/4 olur; T = 16 için 4 flop/bayt. Bu, Bölüm 25.7'deki önbelleğe dostu blok çarpımın GPU'daki karşılığıdır.

Aşağıdaki betik 2048 × 2048 FP32 matrisleri üç yöntemle çarpar. TF32'yi kapattık; yani Bölüm 65.12'deki hızlandırılmış tensör çekirdekleri kullanılmıyor, sonuçlar saf FP32'dir. Her sürümün sonucu float64 referansla karşılaştırılır.

```python
# -*- coding: utf-8 -*-
"""Bolum 76 - Deney 3: matris carpimi (naif, tiled, cuBLAS)."""

import _cudaenv  # noqa: F401
import csv
import os
import numpy as np
import torch
from numba import cuda, float32
from olcum import medyan_ms_numba, medyan_ms_torch

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"
T = 16  # dongu (tile) boyutu

@cuda.jit
def matmul_naif(A, B, C):
    # Her iş parçacığı C[row,col] için tüm k'yı global bellekten okur
    col, row = cuda.grid(2)
    if row < C.shape[0] and col < C.shape[1]:
        acc = float32(0)
        for k in range(A.shape[1]):
            acc += A[row, k] * B[k, col]
        C[row, col] = acc

@cuda.jit
def matmul_tiled(A, B, C):
    # Her blok T x T döşemeleri paylaşımlı belleğe kopyalar; her
    # global okuma T çarpım için yeniden kullanılır.
    sA = cuda.shared.array((16, 16), float32)
    sB = cuda.shared.array((16, 16), float32)
    tx = cuda.threadIdx.x
    ty = cuda.threadIdx.y
    row = cuda.blockIdx.y * 16 + ty
    col = cuda.blockIdx.x * 16 + tx
    acc = float32(0)
    for t in range(A.shape[1] // 16):
        sA[ty, tx] = A[row, t * 16 + tx]
        sB[ty, tx] = B[t * 16 + ty, col]
```

Çekirdeklerin devamı ve ana akış. Döşemeli sürümde senkronizasyon (`syncthreads`) iki kez yapılır: birincisi parçalar yüklendikten sonra, ikincisi kullanıldıktan sonra. İkincisi olmazsa, bir sonraki döngüde parçanın üzerine yazılabilir.

```python
        cuda.syncthreads()
        for k in range(16):
            acc += sA[ty, k] * sB[k, tx]
        cuda.syncthreads()
    C[row, col] = acc

def main():
    torch.backends.cuda.matmul.allow_tf32 = False  # saf FP32
    n = 2048
    rng = np.random.default_rng(76)
    a = rng.standard_normal((n, n)).astype(np.float32)
    b = rng.standard_normal((n, n)).astype(np.float32)
    ref = a.astype(np.float64) @ b.astype(np.float64)
    ref_norm = np.abs(ref).max()
    flop = 2.0 * n**3
    da, db = cuda.to_device(a), cuda.to_device(b)
    dc = cuda.device_array((n, n), dtype=np.float32)
    ta, tb = torch.from_numpy(a).cuda(), torch.from_numpy(b).cuda()
    blok = (T, T)
    izgara = (n // T, n // T)

    def hata(c):
        return float(np.abs(c - ref).max() / ref_norm)

    rows = []
    print(f"N = {n}, FLOP = {flop / 1e9:.2f} GFLOP")
    print(
        "varyant          ms(medyan)   GFLOP/s   bagil max hata  AI"
    )
    for ad, k, ai in [
        ("naif", matmul_naif, 0.25),
        ("tiled (T=16)", matmul_tiled, T / 4),
    ]:
        matmul_run = lambda kk=k: kk[izgara, blok](da, db, dc)
        matmul_run()
        cuda.synchronize()
        c = dc.copy_to_host()
        ms, _, _ = medyan_ms_numba(cuda, matmul_run, tekrar=7)
        gf = flop / (ms * 1e-3) / 1e9
```

Ana akış her üç sürümün süresini, GFLOP/s değerini ve bağıl hatasını yazdırır.

```python
        e = hata(c)
        rows.append((ad, round(ms, 3), round(gf, 1), f"{e:.2e}", ai))
        print(f"{ad:<16} {ms:10.3f}   {gf:8.1f}   {e:.2e}      {ai}")
    ms, _, _ = medyan_ms_torch(
        lambda: torch.matmul(ta, tb), tekrar=10
    )
    gf = flop / (ms * 1e-3) / 1e9
    e = hata(torch.matmul(ta, tb).cpu().numpy())
    rows.append(
        (
            "torch.matmul (cuBLAS)",
            round(ms, 3),
            round(gf, 1),
            f"{e:.2e}",
            "-",
        )
    )
    print(f"{'torch.matmul':<16} {ms:10.3f}   {gf:8.1f}   {e:.2e}")

    with open(
        os.path.join(VERI, "b76_matmul.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["varyant", "ms", "gflops", "bagil_hata", "ai"])
        w.writerows(rows)

if __name__ == "__main__":
    main()
```

Çıktı:

```term
$ python b76_03_matmul.py
N = 2048, FLOP = 17.18 GFLOP
varyant          ms(medyan)   GFLOP/s   bagil max hata  AI
naif                 63.271      271.5   2.28e-06      0.25
tiled (T=16)         22.653      758.4   2.28e-06      4.0
torch.matmul          2.780     6180.6   2.28e-06
```

Üç sürümün hatası aynı (2,28e-06); yani hızlanma doğruluk pahasına gelmedi. Naif sürüm 271 GFLOP/s, döşemeli sürüm 758 GFLOP/s, cuBLAS 6181 GFLOP/s verdi. Döşemeli sürüm naif sürümden yaklaşık 2,8 kat hızlı, cuBLAS ise döşemeli sürümden yaklaşık 8 kat hızlı.

Roofline ile yorumlayalım. Bölüm 76.3'te ölçülen kopya bant genişliği 296,5 GB/s'dir ve bu, bellek tavanının eğimini verir. Pratik hesap tavanı olarak cuBLAS'ın ölçtüğü 6,18 TFLOP/s'yi kullandık; kartın kâğıt üstü FP32 tepe değeri üretici tablosundan ayrıca kontrol edilmelidir, biz bunu yapmadık.

Naif sürüm için tavan 0,25 × 296,5 ≈ 74 GFLOP/s'dir. Ölçülen 271 GFLOP/s bu tavanın yaklaşık dört katı. Bu bir hata değil: 0,25 yoğunluğu, önbelleklerin hiçbir yeniden kullanım sağlamadığını varsayar. Gerçekte L1 ve L2 önbellekler aynı satır ve sütunu tekrar tekrar okudukları için global bellek trafiği tahmin edilenden küçüktür. Yani roofline'ın yoğunluk hesabı, önbellek etkisi ölçülmeden yapılırsa iyimser ya da kötümser sonuç verebilir.

Döşemeli sürüm için tavan 4 × 296,5 ≈ 1186 GFLOP/s'dir ve ölçülen 758 GFLOP/s bu tavanın yaklaşık yüzde 64'üdür. Aradaki fark T = 16'lık küçük döşemeden, her parça için senkronizasyon maliyetinden ve paylaşılan bellek gecikmesinden gelebilir. Bu ayrıntıyı ölçmedik; profiler GPU çekirdek ayrıntısı vermediği için bu bölümde kesin bir neden söyleyemeyiz.

cuBLAS'ın 6181 GFLOP/s'si ise, döşemeleri çok daha büyük tutan, iş parçacığı başına çok sayıda çarpımı yazmaçlarda tutan ve bellek erişimini vektörleyen bir kütüphanenin sonucudur (genel bilgi). Pratikte matris çarpımını kendi çekirdeğinle yazman gerekmez; ama döşemenin neden işe yaradığını ve kütüphanenin neden hızlı olduğunu anlamak, GPU'da bir performans sorununu teşhis ederken işine yarar.

![Şekil 76.6: Solda üç sürümün GFLOP/s değerleri. Sağda roofline: eğik çizgi bellek tavanı, yatay çizgi ölçülen pratik hesap tavanı; naif ve döşemeli noktalar.](gorseller/b76_matmul_roofline.png)

## 76.6 Çekirdek birleştirme ve akışlar

Derin öğrenmede çoğu işlem küçük ve elemanterdir: çarpma, toplama, aktivasyon. PyTorch bunları ayrı çekirdekler olarak çalıştırır. Her çekirdek girdisini global bellekten okur ve çıktısını geri yazar. Beş işlemlik bir zincir, bellek trafiğini beş kat artırır. Çekirdek birleştirme (kernel fusion), bu zinciri tek bir çekirdekte yapıp ara sonuçları yazmazsın; böylece trafik yalnızca girdi ve çıktıdır.

Bu deneyde y = relu(x·A + B)·C + D işlemini iki yolla hesapladık. Eager sürümde beş ayrı PyTorch işlemi var; her biri N elemanı okur ve N elemanı yazar, toplam 40N bayt. Birleştirilmiş sürümde tek bir numba çekirdeği x'i okur, y'yi yazar: 8N bayt. Teorik oran 5'tir.

```python
# -*- coding: utf-8 -*-
"""Bolum 76 - Deney 4: cekirdek birlestirme (fusion), bellek."""

import _cudaenv  # noqa: F401
import csv
import os
import torch
from numba import cuda, float32
from olcum import medyan_ms_numba, medyan_ms_torch

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"
A, B, C, D = 1.5, -0.25, 0.75, 0.1

@cuda.jit
def fused(x, y, n):
    # y = relu(x*A + B) * C + D tek cekirdekte: bellek trafigi 8N bayt
    i = cuda.grid(1)
    if i < n:
        v = x[i] * float32(A) + float32(B)
        if v < 0.0:
            v = float32(0.0)
        y[i] = v * float32(C) + float32(D)

def eager(x):
    # Bes ayri cekirdek; her biri bellekten okur ve bellege yazar
    t1 = x * A
    t2 = t1 + B
    t3 = torch.relu(t2)
    t4 = t3 * C
    return t4 + D

def main():
    print(
        "n            eager ms   fused ms   hizlanma   eager GB/s  "
        "fused GB/s"
    )
    rows = []
```

Çekirdeğin devamı ve ana akış. Ana akış dört boyutta (2^14'ten 2^25'e) iki sürümü ölçer ve iki sonucun farkını da kontrol eder.

```python
    for k in [14, 18, 22, 25]:
        n = 1 << k
        x = torch.randn(
            n,
            device="cuda",
            generator=torch.Generator(device="cuda").manual_seed(76),
        )
        y = torch.empty_like(x)
        dx = cuda.as_cuda_array(x)
        dy = cuda.as_cuda_array(y)
        blok = (n + 255) // 256
        me, _, _ = medyan_ms_torch(lambda: eager(x))
        mf, _, _ = medyan_ms_numba(
            cuda, lambda: fused[blok, 256](dx, dy, n)
        )
        # Dogruluk: eager ile fused ayni sonucu vermeli
        fused[blok, 256](dx, dy, n)
        cuda.synchronize()
        fark = (eager(x) - y).abs().max().item()
        # Bayt trafigi: eager = 5 islem x (4N okuma + 4N yazma) = 40N
        ge = 40 * n / (me * 1e-3) / 1e9
        gf = 8 * n / (mf * 1e-3) / 1e9
        rows.append(
            (
                n,
                round(me, 4),
                round(mf, 4),
                round(me / mf, 2),
                round(ge, 1),
                round(gf, 1),
                f"{fark:.1e}",
            )
        )
        print(
            f"2^{k:<3} {me:10.4f} {mf:10.4f}   {me / mf:6.2f}x   "
            f"{ge:8.1f}   {gf:8.1f}"
        )
    maks = max(float(r[6]) for r in rows)
    print(f"max fark (tum boyutlar): {maks:.1e}")
    with open(
```

Kalan kısım sonuçları yazar.

```python
        os.path.join(VERI, "b76_fuzyon.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(
            [
                "n",
                "eager_ms",
                "fused_ms",
                "hizlanma",
                "eager_gbps",
                "fused_gbps",
                "max_fark",
            ]
        )
        w.writerows(rows)

```

Çıktı:

```term
$ python b76_04_fuzyon.py
n            eager ms   fused ms   hizlanma   eager GB/s  fused GB/s
2^14      0.3820     0.1219     3.13x        1.7        1.1
2^18      0.1587     0.0698     2.27x       66.1       30.0
2^22      0.5786     0.1710     3.38x      290.0      196.2
2^25      4.3469     0.9155     4.75x      308.8      293.2
max fark (tum boyutlar): 4.8e-07
```

Büyük boyutta sonuç açık: 2^25 eleman için birleştirilmiş çekirdek 4,75 kat hızlı, yani teorik 5 kata yakın. Birleştirilmiş sürümün bellek hızı 293 GB/s ile ölçülen kopya değerine (296 GB/s) çok yakın; bu, çekirdeğin bellek tavanıyla sınırlı olduğunu gösterir. Küçük boyutlarda ise sonuçlar çok oynuyor: 2^14 için dört koşuda 1,02 ile 3,23 kat, 2^18 için dört koşuda 1,45 ile 4,31 kat arasında ölçtük. Küçük işlerde süre, çekirdek başlatma maliyetiyle belirlenir ve bu maliyet koşudan koşuya değişir; bu yüzden küçük boyutlar için kesin bir sayı vermek yanıltıcı olur. İki sürümün en büyük farkı 4,8e-07'dir; birleştirme doğruluğu bozmadı.

Akışlar (stream), GPU'ya gönderilen işlerin ayrı sıralar hâlinde çalışmasını sağlar. Farklı akışlardaki bir kopya ile bir hesap aynı anda ilerleyebilir, çünkü GPU'nun kopya motoru ve hesap birimleri bağımsızdır. Kopyayı etkin kılmak için ana bellekteki verinin sabitlenmiş (pinned) olması gerekir; bunu Bölüm 65.4'te görmüştük. Bu deneyde 8 parça işledik, her parça için bir kopya, bir hesap ve bir geri kopya var. Parçaların tek akışta sırayla mı, yoksa üç akışa dağıtılarak mı işlendiğini karşılaştırdık.

Bir parçanın kopyası ile hesabının süresi birbirine yakın olmalı; yoksa örtüşmenin kazancı sınırlanır. Bu yüzden hesap yoğunluğunu (`ITER`) kopya süresine göre ayarladık. Betik bu iki süreyi kendisi de ölçüp yazdırıyor.

```python
# -*- coding: utf-8 -*-
"""Bolum 76 - Deney 5: akislar ile kopya/hesap ortusmesi."""

import _cudaenv  # noqa: F401
import csv
import os
import time
import torch
from olcum import medyan_ms_torch

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"
ITER = 2  # hesap/kopya sureleri ~esit (olcum)

def isle(v):
    # Hesap yogun is: bellek trafigine kiyasla cok aritmetik
    for _ in range(ITER):
        v = v * 1.0000001 + 0.0000003
        v = torch.sin(v) * 0.5 + v * 0.5
    return v

def seri(gh, gd_out, parca, m):
    # Her parca: kopya -> hesap -> geri kopya, tek akista sirayla
    for i in range(parca):
        s = slice(i * m, (i + 1) * m)
        gd = gh[s].to("cuda", non_blocking=True)
        gd = isle(gd)
        gd_out[s].copy_(gd, non_blocking=True)
    torch.cuda.synchronize()

def ortusen(gh, gd_out, parca, m, akislar):
    # Parcalari farkli akislarda calistir: kopya ve hesap ortusebilir
    for i in range(parca):
        s = slice(i * m, (i + 1) * m)
        ak = akislar[i % len(akislar)]
        with torch.cuda.stream(ak):
            gd = gh[s].to("cuda", non_blocking=True)
            gd = isle(gd)
```

Parça döngüleri ve akış ataması (`ortusen`) bu kısmın devamıdır. Her parça `torch.cuda.stream` bağlamında, kendi akışında yürür.

```python
            gd_out[s].copy_(gd, non_blocking=True)
    torch.cuda.synchronize()

def main():
    torch.manual_seed(76)
    parca, m = 8, 1 << 22  # 8 parca x 4M eleman
    toplam = parca * m
    gh = torch.randn(
        toplam
    ).pin_memory()  # sabitlenmis (pinned) bellek
    gd_out = torch.empty(toplam, device="cuda")
    # Dogruluk: iki yol da ayni sonucu vermeli
    seri(gh, gd_out, parca, m)
    ref = gd_out.clone()
    akislar = [torch.cuda.Stream() for _ in range(3)]
    ortusen(gh, gd_out, parca, m, akislar)
    fark = (ref - gd_out).abs().max().item()
    print(f"toplam eleman = {toplam}, parca = {parca}, akis = 3")
    print(f"max fark (seri - ortusen) = {fark:.1e}")

    t_seri, _, _ = medyan_ms_torch(
        lambda: seri(gh, gd_out, parca, m), tekrar=7, isinma=2
    )
    t_ort, _, _ = medyan_ms_torch(
        lambda: ortusen(gh, gd_out, parca, m, akislar),
        tekrar=7,
        isinma=2,
    )
    # Yalnizca hesabin suresi (kopya yok): ust sinir olcegi
    gd = torch.randn(m, device="cuda")
    t_hesap, _, _ = medyan_ms_torch(
        lambda: isle(gd), tekrar=7, isinma=2
    )
    t_hesap_tum = t_hesap * parca
    # Olcek kontrolu: parca basina H2D kopya ve hesap suresi
    t_kopya, _, _ = medyan_ms_torch(
        lambda: gh[:m].to("cuda", non_blocking=True),
        tekrar=7,
        isinma=2,
```

Ana akış ölçümleri yapar ve sonuçları CSV'ye yazar.

```python
    )
    print(f"parca H2D kopya : {t_kopya:6.3f} ms")
    print(f"parca hesap     : {t_hesap:6.3f} ms")
    print(f"seri            : {t_seri:8.2f} ms")
    print(f"ortusen (3 akis): {t_ort:8.2f} ms")
    print(f"hizlanma        : {t_seri / t_ort:6.2f}x")
    print(f"yalniz hesap    : {t_hesap_tum:8.2f} ms")
    with open(
        os.path.join(VERI, "b76_akis.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["varyant", "ms"])
        w.writerow(["seri", round(t_seri, 3)])
        w.writerow(["ortusen_3_akis", round(t_ort, 3)])
        w.writerow(["yalniz_hesap", round(t_hesap_tum, 3)])

if __name__ == "__main__":
    main()
```

Çıktı:

```term
$ python b76_05_akis.py
toplam eleman = 33554432, parca = 8, akis = 3
max fark (seri - ortusen) = 0.0e+00
parca H2D kopya :  1.353 ms
parca hesap     :  1.475 ms
seri            :    23.97 ms
ortusen (3 akis):    14.08 ms
hizlanma        :   1.70x
yalniz hesap    :    11.80 ms
```

Bir parça için H2D kopya 1,35 ms, hesap 1,48 ms sürdü; yani iki süre dengeli. Seri sürüm 23,97 ms, üç akışlı sürüm 14,08 ms sürdü, hızlanma 1,70 kat. Üç akışlı sürümün süresi hesabın toplam süresine (11,80 ms) yakın kaldı. Bu, hesabın sınırladığı bir noktaya geldiğimizi gösterir: kopya tamamen gizlendiğinde süre, hesabın toplamından kısa olamaz.

Dikkat edilecek nokta, iki sonucun birbirine tam eşit olmasıdır (fark 0,0). Akış değişikliği yalnızca sırayı değiştirdi, işlemin kendisini değiştirmedi. Eğitimde bunu uygulamak, veri yükleyicisinin (Bölüm 65.8) ve GPU'nun örtüşmesini sağlayan `pin_memory=True` ile `non_blocking=True` kombinasyonunun temelidir.

## 76.7 PyTorch'ta GPU performansı: profiler, küçük çekirdekler, CUDA graph

Bir eğitim adımında kaç GPU işi yapıldığını bilmek, performans sorununu teşhis etmenin ilk adımıdır. PyTorch'un profiler aracı (`torch.profiler`) CPU tarafını ayrıntılı gösterir. Bu makinedeki Windows PyTorch kurulumunda ise GPU çekirdek etkinlikleri kaydedilmedi: profiler izinde yalnızca CPU olayları çıktı ve GPU zaman çizelgesi üretilemedi. Bu bir ölçüm kısıtıdır ve bu bölümde GPU tarafını profiler ile değil, CUDA olaylarıyla ve aten işlemi sayımıyla ölçtük.

Aşağıdaki betik, küçük bir MLP'nin eğitim adımında kaç aten işlemi çalıştığını sayar (ileri ve geri geçiş dahil), adım süresini ölçer ve CPU tarafındaki en pahalı işlemleri listeler. Ardından 200 küçük işlemden oluşan bir diziyi, eager olarak ve CUDA graph ile çalıştırıp karşılaştırır.

```python
# -*- coding: utf-8 -*-
"""Bolum 76 - Deney 6: profiler ile cekirdek sayimi ve CUDA graph."""

import _cudaenv  # noqa: F401
import csv
import os
import torch
from torch import nn
from torch.profiler import profile, ProfilerActivity
from torch.utils._python_dispatch import TorchDispatchMode
from olcum import medyan_ms_torch

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"

class IslemSayaci(TorchDispatchMode):
    """Her aten islemini (ileri+geri) sayar."""

    def __init__(self):
        super().__init__()
        self.n = 0

    def __torch_dispatch__(self, func, types, args=(), kwargs=None):
        self.n += 1
        return func(*args, **(kwargs or {}))

def profil_mlp():
    torch.manual_seed(76)
    model = nn.Sequential(
        nn.Linear(64, 64), nn.ReLU(), nn.Linear(64, 10)
    ).cuda()
    x = torch.randn(32, 64, device="cuda")
    y = torch.randint(0, 10, (32,), device="cuda")
    kayip = nn.CrossEntropyLoss()

    def adim():
        model.zero_grad(set_to_none=True)
        kayip(model(x), y).backward()
        with torch.no_grad():
```

Kodun devamı: profiler ve CUDA graph karşılaştırması. `CUDAGraph` bir kez yakalanır (capture); sonrasında `replay` tek bir komutla tüm işlem dizisini yeniden çalıştırır.

```python
            for p in model.parameters():
                p.sub_(0.01 * p.grad)

    for _ in range(5):
        adim()
    torch.cuda.synchronize()
    with IslemSayaci() as sayac:
        adim()
    torch.cuda.synchronize()
    print(f"Bir egitim adiminda {sayac.n} aten islemi")
    t_adim, _, _ = medyan_ms_torch(adim, tekrar=15)
    print(f"Adim suresi (CUDA olaylari, medyan): {t_adim:.3f} ms")
    # Not: bu Windows kurulumunda profiler GPU cekirdek etkinligi
    # kaydetmedi; bu yuzden CPU tarafi tablosu ve olay zamanlamasi
    # kullanilir.
    with profile(activities=[ProfilerActivity.CPU]) as prof:
        for _ in range(20):
            adim()
        torch.cuda.synchronize()
    print("ad                             cagri   kendi CPU ms")
    satir = sorted(
        prof.key_averages(), key=lambda e: -e.self_cpu_time_total
    )[:6]
    for e in satir:
        print(
            f"{e.key[:30]:<30} {e.count:6d} "
            f"{e.self_cpu_time_total / 1000:12.3f}"
        )
    return sayac.n, t_adim

def kucuk_isler(x, adet=200):
    # 200 kucuk elemanter islem: her biri ayri bir cekirdek baslatma
    for _ in range(adet):
        x = x * 1.0001 + 0.0001
    return x

def cuda_graph_karsilastirma():
    x = torch.zeros(1024, device="cuda")
```

Ana akış ve CSV yazımı.

```python
    # Isinma: graph yakalamadan once yan akista calistir
    s = torch.cuda.Stream()
    s.wait_stream(torch.cuda.current_stream())
    with torch.cuda.stream(s):
        for _ in range(3):
            kucuk_isler(x)
    torch.cuda.current_stream().wait_stream(s)
    graf = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graf):
        cikis = kucuk_isler(x)
    t_eager, _, _ = medyan_ms_torch(lambda: kucuk_isler(x), tekrar=15)
    t_graf, _, _ = medyan_ms_torch(lambda: graf.replay(), tekrar=15)
    dogru = torch.allclose(cikis, kucuk_isler(x))
    print(f"\n200 kucuk islem (1024 eleman):")
    print(f"  eager (her islem ayri baslatma): {t_eager:.3f} ms")
    print(f"  CUDA graph replay              : {t_graf:.3f} ms")
    print(f"  hizlanma: {t_eager / t_graf:.2f}x   dogruluk: {dogru}")
    return t_eager, t_graf

def main():
    islem, t_adim = profil_mlp()
    t_e, t_g = cuda_graph_karsilastirma()
    with open(
        os.path.join(VERI, "b76_profil.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["olcum", "deger"])
        w.writerow(["adim_basina_aten_islemi", islem])
        w.writerow(["adim_ms", round(t_adim, 4)])
        w.writerow(["eager_ms", round(t_e, 4)])
        w.writerow(["graph_ms", round(t_g, 4)])

if __name__ == "__main__":
    main()
```

Çıktı:

```term
$ python b76_06_profil.py
Bir egitim adiminda 45 aten islemi
Adim suresi (CUDA olaylari, medyan): 0.955 ms
ad                             cagri   kendi CPU ms
aten::mm                           60        2.691
aten::addmm                        40        2.178
aten::mul                          80        2.116
aten::sub_                         80        1.376
aten::fill_                        40        1.092
aten::sum                          40        0.971

200 kucuk islem (1024 eleman):
  eager (her islem ayri baslatma): 9.461 ms
  CUDA graph replay              : 0.493 ms
  hizlanma: 19.21x   dogruluk: True
```

Bir eğitim adımında 45 aten işlemi çalıştı; adım süresi 0,955 ms. Profilerin CPU tablosunda en çok zaman alan işlemler matris çarpımları (`aten::mm`, `aten::addmm`) ve elemanter işlemlerdir. 20 adımda `aten::mm` 60 kez çağrıldı; yani adım başına 3 kez.

CUDA graph sonucu dikkat çekici: 200 küçük işlem eager olarak 9,46 ms sürdü (işlem başına yaklaşık 47 µs), graph ile 0,49 ms; 19,21 kat hızlanma. Bu rakam her koşuda değişti (17,9 ile 19,4 arasında); yönü her zaman aynıydı. Buradaki asıl maliyet, her işlemin ayrı başlatılmasıdır, hesabın kendisi değil; işlemler 1024 elemanlık küçük diziler üzerinde yapıldığı için hesap neredeyse sıfırdır. Windows'ta çekirdek başlatma maliyetinin Linux'a göre daha yüksek olduğunu düşünüyoruz (genel bilgi); bunu aynı makinede Linux ile karşılaştırmadık.

Bu, Bölüm 65.4'te gördüğümüz küçük tensör sorununun grafik tabanlı çözümüdür. Bölüm 65.15'teki `torch.compile` aynı hedefe farklı bir yoldan gider, ama bu makinede Triton olmadığı için onun üretimi çalışmıyor. CUDA graph ise Triton gerektirmez ve sabit boyutlu, tekrarlayan işler için iyi çalışır. Dinamik şekiller ve Python kontrol akışı ile graph yakalama zorlaşır; bu yüzden graph'ı kullanmadan önce girdi şekillerinin sabit olduğunu doğrulamak gerekir.

## 76.8 Dağıtık eğitim: DDP, all-reduce ve halka algoritması

Tek bir GPU modeli sığdıramıyor ya da eğitimi yetiştiremiyorsa, birden çok süreç kullanırsın. Veri paralelliğinde (data parallelism) her süreç modelin tam bir kopyasını tutar, ama her biri farklı bir mini-batch parçası işler. Her adımın sonunda gradyanlar süreçler arasında toplanıp ortalanır (all-reduce), böylece herkes aynı ağırlık güncellemesini yapar. PyTorch'taki DistributedDataParallel (DDP) bunu yapar: geri yayılım sırasında gradyanları kovalara (bucket) ayırır ve kova hazır olur olmaz all-reduce başlatır. Varsayılan kova boyutu 25 MiB'dir; bu değer kaynak kodda da yazılı (Kod Okuma'ya bak).

Gradyanların ortalanması neden tek süreçli eğitimle aynı sonucu verir? Her süreç kendi yerel batch'inin ortalama kaybının gradyanını hesaplar. Batch'ler eşit büyüklükte ise, bu yerel ortalamaların ortalaması tüm batch'in ortalama kaybının gradyanına eşittir. Kaynakta `allreduce_hook` gradyanları toplamadan önce süreç sayısına böler; kaynak kodundaki gerekçe FP16'da taşmayı önlemektir (Kod Okuma'ya bak). Sonuç toplam ortalamadır. Aşağıdaki deney bunu doğrular: iki süreç, her biri 128 örnek, tek süreç 256 örnek.

Windows'ta PyTorch'un dağıtık paketinde iki sınır var. Birincisi NCCL arka ucu yok; bu makinede `is_nccl_available()` False döndü, bu yüzden GPU'lar arası iletişim için gloo arka ucunu kullandık. Gloo, GPU'ya değil CPU'ya dayalı çalışır, yani bu deney CPU üzerinde bir DDP demonstrasyonudur. İkincisi, PyTorch bu derlemede libuv desteği içermiyor; TCP tabanlı rendezvous çalışmadı. Bu yüzden süreçler dosya tabanlı bir depo (`file://`) üzerinden buluşuyor.

Halka all-reduce (ring all-reduce), N düğümün M elemanlık vektörlerini ağ üzerinde toplamanın yaygın yoludur. Düğümler bir halka oluşturur; her düğüm yalnızca komşusuna gönderir. Algoritma iki fazdan oluşur. Azaltma fazında (reduce-scatter) M/N uzunluğundaki parçalar halka boyunca döner ve her düğüm bir parçanın tam toplamını elde eder. Dağıtma fazında (all-gather) bu tam parçalar yine halkada döner ve herkes tüm sonucu alır. Her fazda N − 1 adım vardır; her adımda her düğüm M/N eleman gönderir. Düğüm başına toplam iletişim hacmi 2(N − 1)/N × M elemandır. Bu formül N büyüdükçe 2M'ye yaklaşır: düğüm sayısı arttıkça düğüm başına iletişim pratikte sabit kalır. Şekil 76.7 bu düzeni gösteriyor.

![Şekil 76.7: Dört düğümlü halka. Her düğüm yalnızca komşusuna gönderir; iki faz, her biri N − 1 adım.](gorseller/b76_halka_allreduce.png)

Aşağıdaki betik iki bölümden oluşur. İlk bölüm, DDP ile tek süreç eğitimi arasında gradyan ve ağırlık eşitliğini test eder. İkinci bölüm, halka all-reduce'un sıfırdan yazılmış simülasyonunu üç düğüm sayısı için çalıştırır ve düğüm başına gönderilen eleman sayısını formülle karşılaştırır. İkinci bölümün kabarcık tablosu 76.9'da kullanılacak.

```python
# -*- coding: utf-8 -*-
"""Bolum 76 - Deney 8: DDP (gloo, 2 surec) esdegerligi."""

import os

os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")
import torch
import torch.distributed as dist
import torch.multiprocessing as mp
from torch import nn
from torch.nn.parallel import DistributedDataParallel as DDP

DUNYA = 2  # surec sayisi (dunya boyutu)
ADIM = 5  # egitim adimi
LR = 0.1

def model_kur():
    torch.manual_seed(76)  # her surec ayni baslangic agirliklari
    return nn.Sequential(
        nn.Linear(16, 32), nn.ReLU(), nn.Linear(32, 1)
    )

def veri():
    g = torch.Generator().manual_seed(76)
    x = torch.randn(256, 16, generator=g)
    y = torch.sin(x[:, :1]) + 0.1 * torch.randn(256, 1, generator=g)
    return x, y

def calistir(rank, depo):
    # Windows'ta libuv yok: TCP yerine dosya deposu (file://)
    dist.init_process_group(
        "gloo", init_method=depo, rank=rank, world_size=DUNYA
    )
    x, y = veri()
    parca = x.shape[0] // DUNYA
    xy = x[rank * parca : (rank + 1) * parca]  # yerel mini-batch
```

DDP deneyinin devamı: gradyan karşılaştırması ve beş adımlık eğitim döngüsü. Tek süreç referansı aynı başlangıç ağırlıklarıyla kurulur ve tam batch üzerinde çalışır.

```python
    yy = y[rank * parca : (rank + 1) * parca]

    ddp = DDP(model_kur())
    ref = model_kur()  # tek surec referansi
    ref.load_state_dict(ddp.module.state_dict())
    kayip = nn.MSELoss()
    opt_d = torch.optim.SGD(ddp.parameters(), lr=LR)
    opt_r = torch.optim.SGD(ref.parameters(), lr=LR)

    # 1) Gradyan karsilastirmasi (tek adim)
    ddp.zero_grad()
    kayip(ddp(xy), yy).backward()  # all-reduce burada
    ref.zero_grad()
    kayip(ref(x), y).backward()  # tum batch
    fark_g = max(
        (a.grad - b.grad).abs().max().item()
        for a, b in zip(ddp.parameters(), ref.parameters())
    )

    # 2) ADIM adim egitim ve agirlik karsilastirmasi
    for _ in range(ADIM):
        opt_d.zero_grad()
        kayip(ddp(xy), yy).backward()
        opt_d.step()
        opt_r.zero_grad()
        kayip(ref(x), y).backward()
        opt_r.step()
    fark_w = max(
        (a - b).abs().max().item()
        for a, b in zip(ddp.parameters(), ref.parameters())
    )
    if rank == 0:
        print(
            f"surec sayisi = {DUNYA}, yerel batch = {parca}, "
            f"toplam = {x.shape[0]}"
        )
        print(f"max |grad_ddp - grad_tek| (1. adim) = {fark_g:.2e}")
        print(
            f"max |w_ddp - w_tek| ({ADIM} adim sonra) = {fark_w:.2e}"
        )
```

Ana akış ve süreçlerin başlatılması. `mp.spawn` iki süreç başlatır ve her birine dosya deposunun yolunu verir.

```python
        print(
            f"son kayip (tek surec) = "
            f"{kayip(ref(x), y).item():.6f}"
        )
    dist.destroy_process_group()

if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    depo_yol = os.path.join(HERE, "ddp_depo.tmp")
    if os.path.exists(depo_yol):
        os.remove(depo_yol)
    depo = "file:///" + depo_yol.replace("\\", "/")
    mp.spawn(calistir, args=(depo,), nprocs=DUNYA, join=True)
```

Çıktı:

```term
$ python b76_08_ddp.py
surec sayisi = 2, yerel batch = 128, toplam = 256
max |grad_ddp - grad_tek| (1. adim) = 2.09e-07
max |w_ddp - w_tek| (5 adim sonra) = 2.98e-08
son kayip (tek surec) = 0.338179
```

Gradyanlar en fazla 2,09e-07 farklı; beş adım sonra ağırlıklar en fazla 2,98e-08 farklı çıktı. Bu fark float32'nin yuvarlama hatasıdır; sürecin toplamasının sırası bile hatayı değiştirebilir (Bölüm 53.10). DDP'nin tek süreçle eşleştiğini bu sonuçlar gösteriyor.

Şimdi halka simülasyonu. Aşağıdaki betik, halka all-reduce'u sıfırdan uygular ve her adımda tüm mesajları önce toplayıp sonra uygular; yani gerçek bir ağ gibi eş zamanlı çalışır. Bu betik GPU kullanmaz; ağın davranışını anlamak için bir simülasyondur.

```python
# -*- coding: utf-8 -*-
"""Bolum 76 - Deney 9: halka all-reduce ve boru hatti kabarcigi."""

import csv
import os
import numpy as np

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"

def halka_allreduce(vekt):
    """vekt: N dugumun vektorleri. Her dugumun sonucu toplamdir.
    Her adimda mesajlar once toplanir, sonra uygulanir.
    """
    n = len(vekt)
    buf = [
        np.array_split(v.astype(np.float64).copy(), n) for v in vekt
    ]
    gonderilen = 0  # dugum basina gonderilen eleman
    # 1) Reduce-scatter: N-1 adim
    for s in range(n - 1):
        mesaj = [buf[i][(i - s) % n].copy() for i in range(n)]
        for i in range(n):
            j = (i - 1) % n
            buf[i][(j - s) % n] = buf[i][(j - s) % n] + mesaj[j]
        gonderilen += mesaj[0].size
    # 2) All-gather: N-1 adim
    for s in range(n - 1):
        mesaj = [buf[i][(i + 1 - s) % n].copy() for i in range(n)]
        for i in range(n):
            j = (i - 1) % n
            buf[i][(j + 1 - s) % n] = mesaj[j]
        gonderilen += mesaj[0].size
    sonuc = [np.concatenate(b) for b in buf]
    return sonuc, gonderilen

def kabarcik(p, m):
    """GPipe ileri gecisi: asama s, batch j'yi t = s + j'de isler.
    Zaman izgarasinda mesgul hucreleri sayar; kabarcik = bos oran."""
```

Simülasyonun devamı: ana akış, üç düğüm sayısı için doğruluk ve iletişim hacmi kontrolü ve GPipe kabarcık tablosu. Kabarcık hesabı 76.9'da açıklanıyor.

```python
    t_son = m + p - 1  # son meşgul zaman dilimi + 1
    mesgul = {(s, s + j) for s in range(p) for j in range(m)}
    return 1 - len(mesgul) / (p * t_son), (p - 1) / (m + p - 1)

def main():
    rng = np.random.default_rng(76)
    m_eleman = 1200  # gradyan vektoru uzunlugu
    rows = []
    print(
        "N   simulasyon-dogru   gonderim/dugum(eleman)  "
        "2(N-1)/N * M"
    )
    for n in [2, 4, 8]:
        vekt = [rng.standard_normal(m_eleman) for _ in range(n)]
        hedef = np.sum(vekt, axis=0)
        sonuc, gon = halka_allreduce(vekt)
        dogru = all(np.allclose(s, hedef) for s in sonuc)
        formul = 2 * (n - 1) / n * m_eleman
        print(f"{n:<3} {str(dogru):<18}  {gon:<22} {formul:.1f}")
        rows.append(("halka", n, dogru, gon, round(formul, 1)))
    print(
        "\np (asama)  m (mikro-batch)  "
          "kabarcik (simulasyon)  (p-1)/(m+p-1)"
    )
    for p in [4]:
        for m in [1, 4, 8, 16, 32]:
            sim, formul = kabarcik(p, m)
            print(f"{p:<10} {m:<16} {sim:<22.4f} {formul:.4f}")
            rows.append(
                ("kabarcik", p, m, round(sim, 4), round(formul, 4))
            )
    with open(
        os.path.join(VERI, "b76_halka_kabarcik.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(["tur", "a", "b", "c", "d"])
        w.writerows(rows)

if __name__ == "__main__":
    main()
```

Çıktı:

```term
$ python b76_09_halka.py
N   simulasyon-dogru   gonderim/dugum(eleman)  2(N-1)/N * M
2   True                1200                   1200.0
4   True                1800                   1800.0
8   True                2100                   2100.0

p (asama)  m (mikro-batch)  kabarcik (simulasyon)  (p-1)/(m+p-1)
4          1                0.7500                 0.7500
4          4                0.4286                 0.4286
4          8                0.2727                 0.2727
4          16               0.1579                 0.1579
4          32               0.0857                 0.0857
```

Üç düğüm sayısı için de her düğüm tam toplamı aldı (`True`). Düğüm başına gönderilen eleman sayısı formüldeki değerle birebir eşleşti: M = 1200 için N = 2, 4, 8 düğümde 1200, 1800 ve 2100. Yani gönderim hacmi, düğüm sayısı 2'den 8'e çıkarken 1200'den 2100'e, yani 2M'ye doğru yaklaşıyor.

Bu simülasyon ağın gecikmesini ya da bant genişliğini modellemez. Gerçek bir all-reduce'un süresi, mesaj boyutu ve gecikme (latency) iki terimli bir toplamla tahmin edilir: adım sayısı çarpı (gecikme artı mesaj/bant genişliği). Düşük gecikmeli çok mesajlı durumlarda ağaç tabanlı algoritmalar, büyük mesajlarda halka tercih edilir (genel bilgi). Bu bölümde zamanlamayı ölçmedik; yalnızca hacmi ve doğruluğu ölçtük.

## 76.9 Model paralelliği, boru hattı ve tensör paralelliği

Model bir GPU'ya sığmıyorsa veri paralelliği yetmez: her süreç tam modeli tutmak zorunda kalır. Bu durumda modeli parçalara bölersin. Model paralelliğinde (model parallelism) farklı katmanlar farklı GPU'lardadır ve veri GPU'dan GPU'ya akar. Basit hâli, bir GPU'nun iş bitirmesini bekleyen diğerleridir: yalnızca bir GPU aynı anda çalışır ve kaynak israf olur.

Boru hattı paralelliği (pipeline parallelism) bu israfı azaltmak için batch'i mikro-batch'lere böler. Her aşama (stage) bir mikro-batch'i işler ve sonucunu bir sonraki aşamaya geçirir; böylece farklı aşamalar farklı mikro-batch'lerle aynı anda çalışır. Ama boru hattının başında ve sonunda bazı aşamalar boş kalır. Bu boşluklara kabarcık (bubble) denir. Basit GPipe zamanlamasında, p aşamalı ve m mikro-batch'li bir boru hattının kabarcık oranı (p − 1) / (m + p − 1)'dir. Bu formül, ileri geçiş için her aşamanın m + p − 1 zaman diliminde çalıştığı varsayımından gelir. Şekil 76.8 p = 4, m = 4 zamanlamasını ve kabarcık oranının m ile düşüşünü gösteriyor.

![Şekil 76.8: Solda p = 4, m = 4 zamanlaması; boş hücreler kabarcıktır. Sağda ızgara sayımı ile (p − 1)/(m + p − 1) eğrisi çakışıyor.](gorseller/b76_boru_hatti.png)

Yukarıdaki Deney 9'un ikinci tablosu bu formülü bir zaman ızgarası üzerinde saydığımızda elde ettiğimiz değerleri verdi. p = 4 için m = 1'de 0,75, m = 4'te 0,4286, m = 8'de 0,2727, m = 16'da 0,1579 ve m = 32'de 0,0857; sayım ile formül her satırda eşleşti. Pratik sonuç açık: kabarcığı küçültmek için mikro-batch sayısını artırmak gerekir, ama mikro-batch çok küçülürse GPU verimi düşer. Bu iki kuvvet arasında bir denge vardır.

Tensör paralelliği (tensor parallelism) ise tek bir matris çarpımını GPU'lara böler. Ağırlık matrisinin sütunları ya da satırları farklı GPU'lardadır; her GPU kendi parçasının sonucunu hesaplar ve katman sonunda sonuçlar all-reduce ile birleşir. Bu yöntem kabarcık üretmez, ama her katmanda iletişim gerektirir; bu yüzden yüksek bant genişlikli bir GPU-GPU bağlantısı ister (genel bilgi). Gerçek büyük dil modellerinde bu üç yöntem genellikle birlikte kullanılır (genel bilgi): veri, tensör ve boru hattı paralelliği aynı kümede bir arada çalışır. Bu bölümde tensör ve boru hattı paralelliğini ölçmedik; yalnızca kavram ve kabarcık hesabı var.

## 76.10 FSDP ve ZeRO: bellek ayak izi

Bir modeli eğitmek yalnızca parametreleri tutmak değildir. Her parametre için gradyan ve optimizasyon durumu da gerekir. Adam optimizasyonu her parametre için iki ek değer (birinci ve ikinci moment) tutar. fp32 eğitimde her parametre için bellek şöyle dağılır: parametre 4 bayt, gradyan 4 bayt, Adam m ve v 8 bayt; toplam 16 bayt. Aktivasyonlar bu hesaba dahil değildir; onlar batch boyutuna ve model derinliğine bağlıdır (Bölüm 65.13'teki bellek ölçümlerine bak).

ZeRO (Zero Redundancy Optimizer), veri paralelliğinde her GPU'nun aynı durumu tekrar tekrar tutmasını önler. Üç aşama vardır. Aşama 1'de optimizasyon durumu süreçler arasında bölünür. Aşama 2'de gradyanlar da bölünür. Aşama 3'te parametreler de bölünür ve her katman çalışmadan önce gerekli parametreler toplanır (genel bilgi). PyTorch'un FSDP (Fully Sharded Data Parallel) bu fikrin uygulamasıdır; kabaca ZeRO aşama 3'e karşılık gelir (genel bilgi). Karışık hassasiyette (2 bayt fp16 parametre, 2 bayt gradyan, 12 bayt fp32 ana kopya ve Adam durumu) toplam yine 16 bayttır; bunun ayrıntısını Bölüm 65.12'de gördük.

Aşağıdaki betik bu hesabı iki yönden doğrular. İlk olarak 67,13 milyon parametreli bir modelde fp32 Adam eğitiminin bellek artışını ölçer. İkinci olarak, 1,3 milyar ve 7 milyar parametreli modeller için ZeRO aşamalarına göre GPU başına bellek tablosunu üretir. Tabloda parametre, gradyan ve optimizasyon sütunları ayrı ayrı yazılmıştır, böylece hangi bileşenin bölündüğü görülebilir.

```python
# -*- coding: utf-8 -*-
"""Bolum 76 - Deney 7: egitimde bellek butcesi (fp32, Adam)."""

import _cudaenv  # noqa: F401
import csv
import os
import torch
from torch import nn

VERI = r"D:\Mevcut Projeler\Kitap\engine\veri"
MB = 1024**2

def bellek():
    return torch.cuda.memory_allocated() / MB

def main():
    torch.manual_seed(76)
    torch.cuda.reset_peak_memory_stats()
    # 4 katman, her biri 4096 x 4096 + sapma: ~67.1 M parametre
    model = nn.Sequential(*[nn.Linear(4096, 4096) for _ in range(4)])
    P = sum(p.numel() for p in model.parameters())
    model = model.cuda()
    opt = torch.optim.Adam(model.parameters(), lr=1e-4)
    x = torch.randn(8, 4096, device="cuda")  # kucuk batch
    print(f"parametre sayisi P = {P / 1e6:.2f} M")
    print(f"beklenen (fp32, Adam): 16 P bayt = {16 * P / MB:.1f} MB")
    print()
    print("asama                         ayrilan MB   P basina bayt")
    satirlar = []
    a0 = bellek()
    satirlar.append(("model parametreleri", a0))
    loss = model(x).pow(2).mean()
    loss.backward()
    a1 = bellek()
    satirlar.append(("+ gradyanlar", a1))
    opt.step()
    a2 = bellek()
    satirlar.append(("+ Adam m ve v (ilk adim)", a2))
```

Bellek ölçümünün devamı. Her aşamada `memory_allocated` okunur; ilk adımdan sonra Adam durumları oluşur, `zero_grad(set_to_none=True)` gradyan belleğini serbest bırakır.

```python
    opt.zero_grad(set_to_none=True)
    a3 = bellek()
    satirlar.append(("zero_grad(None) sonrasi", a3))
    for ad, deger in satirlar:
        print(f"{ad:<29} {deger:10.1f}   {deger * MB / P:8.2f}")
    tepe = torch.cuda.max_memory_allocated() / MB
    print(f"\nTepe (max_memory_allocated): {tepe:.1f} MB")
    print(
        "Aktivasyon ve tamponlar tepe-ayrilan farkina girer."
    )

    # Sinir sinamasi: 6 GB kartta 12 GB'lik dolu tensor.
    # Bu makinede (WDDM) hata vermedi; metinde yorumlanir.
    del model, opt, x, loss
    torch.cuda.empty_cache()
    libre, toplam = torch.cuda.mem_get_info()
    print(
        "\nVRAM bos/toplam: "
        f"{libre / 1024 ** 3:.2f} / {toplam / 1024 ** 3:.2f} GB"
    )
    try:
        t = torch.zeros(
            12 * 1024**3 // 4, dtype=torch.float32, device="cuda"
        )
        print(
            "12 GB dolduruldu; ayrilan: "
            f"{torch.cuda.memory_allocated() / 1024 ** 3:.1f} GB"
        )
        del t
    except torch.OutOfMemoryError as hata:
        print("OOM:", str(hata).split("\n")[0][:100])
    torch.cuda.empty_cache()

    with open(
        os.path.join(VERI, "b76_bellek_butce.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
```

Ölçümün son kısmı: tepe bellek, VRAM durumu ve sınır sınaması. Sınır sınaması, 6 GB'lık kartta 12 GB'lık tek bir tensör ayırmaya çalışır.

```python
        w.writerow(["asama", "mb", "bayt_per_param"])
        for ad, deger in satirlar:
            w.writerow(
                [ad, round(deger, 2), round(deger * MB / P, 3)]
            )
        w.writerow(["tepe", round(tepe, 2), round(tepe * MB / P, 3)])
        w.writerow(["P", P, ""])
    zt = zero_tablo()
    print("\nZeRO: GPU basina bellek (GB), fp32 + Adam")
    print("model  N  asama  parametre  gradyan  optimizer  toplam")
    for r in zt:
        print(
            f"{r[0]:<6}{r[1]:<3}{r[2]:<7}{r[3]:9.3f}{r[4]:9.3f}"
            f"{r[5]:11.3f}{r[6]:8.3f}"
        )
    with open(
        os.path.join(VERI, "b76_zero.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as f:
        w = csv.writer(f)
        w.writerow(
            [
                "model",
                "n",
                "asama",
                "parametre_gb",
                "gradyan_gb",
                "optimizer_gb",
                "toplam_gb",
            ]
        )
        w.writerows(zt)

def zero_tablo():
    """ZeRO asamalarina gore GPU basina bellek (GB, 10^9 bayt).
    fp32+Adam: parametre 4, gradyan 4, Adam (m, v) 8 bayt/param.
    Asama 0: tam kopya. 1: Adam bolunur. 2: + gradyan bolunur.
```

ZeRO tablosunu üreten fonksiyon ve CSV yazımı. Formüller, her aşamada hangi bileşenin GPU sayısına (N) bölündüğünü kodlar.

```python
    3: + parametre. Karisik hassasiyette (2+2+12) yine 16 bayt.
    """
    satirlar = []
    for ad, P in [("1.3B", 1.3e9), ("7B", 7e9)]:
        for n in [1, 4, 8]:
            for asama in [0, 1, 2, 3]:
                w = 4 * P / 1e9
                g = 4 * P / 1e9
                o = 8 * P / 1e9
                if asama == 0:
                    wg, gg, og = w, g, o
                elif asama == 1:
                    wg, gg, og = w, g, o / n
                elif asama == 2:
                    wg, gg, og = w, g / n, o / n
                else:
                    wg, gg, og = w / n, g / n, o / n
                satirlar.append(
                    (
                        ad,
                        n,
                        asama,
                        round(wg, 3),
                        round(gg, 3),
                        round(og, 3),
                        round(wg + gg + og, 3),
                    )
                )
    return satirlar

if __name__ == "__main__":
    main()
```

Çıktı:

```term
$ python b76_07_bellek_butce.py
parametre sayisi P = 67.13 M
beklenen (fp32, Adam): 16 P bayt = 1024.2 MB

asama                         ayrilan MB   P basina bayt
model parametreleri                256.2       4.00
+ gradyanlar                       528.5       8.26
+ Adam m ve v (ilk adim)          1040.6      16.26
zero_grad(None) sonrasi            784.6      12.26

Tepe (max_memory_allocated): 1296.7 MB
Aktivasyon ve tamponlar tepe-ayrilan farkina girer.

VRAM bos/toplam: 4.96 / 6.00 GB
12 GB dolduruldu; ayrilan: 12.0 GB

ZeRO: GPU basina bellek (GB), fp32 + Adam
model  N  asama  parametre  gradyan  optimizer  toplam
1.3B  1  0          5.200    5.200     10.400  20.800
1.3B  1  1          5.200    5.200     10.400  20.800
1.3B  1  2          5.200    5.200     10.400  20.800
1.3B  1  3          5.200    5.200     10.400  20.800
1.3B  4  0          5.200    5.200     10.400  20.800
1.3B  4  1          5.200    5.200      2.600  13.000
1.3B  4  2          5.200    1.300      2.600   9.100
1.3B  4  3          1.300    1.300      2.600   5.200
1.3B  8  0          5.200    5.200     10.400  20.800
1.3B  8  1          5.200    5.200      1.300  11.700
1.3B  8  2          5.200    0.650      1.300   7.150
1.3B  8  3          0.650    0.650      1.300   2.600
7B    1  0         28.000   28.000     56.000 112.000
7B    1  1         28.000   28.000     56.000 112.000
7B    1  2         28.000   28.000     56.000 112.000
7B    1  3         28.000   28.000     56.000 112.000
7B    4  0         28.000   28.000     56.000 112.000
7B    4  1         28.000   28.000     14.000  70.000
7B    4  2         28.000    7.000     14.000  49.000
7B    4  3          7.000    7.000     14.000  28.000
7B    8  0         28.000   28.000     56.000 112.000
7B    8  1         28.000   28.000      7.000  63.000
7B    8  2         28.000    3.500      7.000  38.500
7B    8  3          3.500    3.500      7.000  14.000
```

Ölçülen fp32 Adam değeri parametre başına 16,26 bayttır; formül 16 bayt dediği için aradaki 0,26 bayt Adam'ın geçici tamponlarından ve küçük yardımcı tensörlerden gelir. İlk adımdan sonra gradyanlar serbest bırakılınca bellek 784,6 MB'a düşüyor; tepe değer ise 1296,7 MB. Yani tepe bellek, kalıcı durumdan yaklaşık yarım gigabayt fazla; aradaki fark aktivasyon ve geçici bellektir.

Ölçüm sırasında kartın boş VRAM'i 4,96 GB olarak raporlandı; 6 GB'lık kart kullanılabilir bellek açısından bundan daha küçük. Bu, 5 GB'ı aşan bir model durumunun bu kartta aktivasyonla birlikte sığmayacağı anlamına gelir.

Sınır sınaması beklediğimizden farklı çıktı. 6 GB'lık kartta 12 GB'lık dolu bir tensör hata vermeden ayrıldı. Bu, Windows'taki NVIDIA sürücüsünün bellek taşmasını sistem belleğine yönlendiren bir ayarıyla açıklanabilir (genel bilgi: "CUDA - Sysmem Fallback Policy"). Bu makinede bu ayarı kontrol etmedik. Sonuç olarak bu kartta "bellek bitti" hatasını güvenilir biçimde üretemedik; Bölüm 65.13'te batch 16384 için OOM gözlemlenmişti, bu sınama ise farklıydı. Ders şu: OOM'u tek bir büyük ayırma ile test etmek, gerçek eğitim sırasındaki kullanımı temsil etmez. Eğitimde bellek sorununu ölçmek için tepe bellek ve adım başına bellek değerlerini izle.

ZeRO tablosunda 1,3 milyar parametreli model için N = 4 GPU'da aşama 0 (klasik DDP) GPU başına 20,8 GB ister. Aşama 3'te bu 5,2 GB'a iner; N = 8'de 2,6 GB'a. 7 milyar parametreli model için N = 8 ve aşama 3 bile GPU başına 14 GB ister. Yani bu tablo, 6 GB'lık tek bir kartta 1,3 milyar parametreli modelin bile fp32 Adam ile eğitilemeyeceğini (20,8 GB) gösteriyor. 7 milyar parametreli model için aşama 3 GPU başına 112 / N GB eder; aktivasyon hariç bile 6 GB'a sığması için en az 19 GPU gerekir (112 / 6 ≈ 18,7). Şekil 76.9 bu tabloyu N = 4 için görselleştiriyor.

![Şekil 76.9: N = 4 GPU'da 1,3B ve 7B modeller için GPU başına bellek: DDP ve ZeRO aşama 1, 2, 3. Kesikli çizgi 6 GB'lık kartı gösterir.](gorseller/b76_zero_bellek.png)

Aktivasyon belleği tabloda yoktur. Bunu iki yolla azaltırsın: aktivasyon yeniden hesaplama (activation checkpointing), yani ileri geçişte bazı ara sonuçları atıp geri geçişte yeniden hesaplamak, ya da daha küçük batch ve gradyan birikimi (Bölüm 65.11 ve 65.13). Yeniden hesaplama hesap süresini artırır, bellek kazandırır; bu bir zaman-bellek takasıdır.

## 76.11 Ölçekleme, maliyet ve pratik sorunlar

Birden çok GPU eklemek her zaman hızlandırmaz. Güçlü ölçeklemede (strong scaling) iş sabittir ve GPU sayısı arttıkça süre azalmalıdır; Amdahl yasası burada sınır koyar: seri kesir küçük olsa bile çok sayıda GPU'da verimi düşürür (Bölüm 53.3). Zayıf ölçeklemede (weak scaling) her GPU'ya düşen iş sabittir ve toplam iş büyür; ölçülen verim genelde daha iyidir, ama iletişim arttıkça düşer.

Dağıtık eğitimde iletişim ile hesabın oranı belirleyicidir. Halka all-reduce düğüm başına yaklaşık 2M eleman gönderir; M, model boyutuyla orantılıdır. Hesap ise batch boyutu ve model derinliğiyle büyür. Büyük batch hesabı artırır ve iletişim payını düşürür; ama batch büyüdükçe eğitimin istatistiksel davranışı da değişir (Bölüm 64.2). Bu nedenle ölçekleme kararını yalnızca süreye göre değil, hem süreye hem de doğruluk eğrisine göre vermelisin.

Pratikte GPU eğitiminde karşılaşacağın birkaç sorun var. Bellek yetersizliği hatası (OOM) geldiğinde ilk adım tepe bellek ölçümü yapmaktır; `torch.cuda.max_memory_allocated()` ve `torch.cuda.memory_summary()` bunu gösterir, ama `memory_summary` çıktısı uzundur, bu yüzden tek tek sayılara bakmak daha kullanışlıdır. Bellek parçalanması (fragmentation), toplam boş bellek yeterli olsa bile büyük bir ayırmanın başarısız olması demektir; değişken boyutlu tensörler bunu artırır. Hata yakalama ve batch küçültme için Bölüm 65.13'teki desen geçerlidir.

Birden çok makineli eğitimde süreçleri başlatmak için `torchrun` kullanılır; kümede iş zamanlaması SLURM gibi bir yöneticiyle yapılır (genel bilgi). Makineler arası ağın bant genişliği ve gecikmesi, ölçeklemeyi doğrudan belirler; Ethernet ile InfiniBand arasındaki fark bu nedenle büyüktür (genel bilgi). Bu makinede yalnızca tek GPU ve tek makine vardı; çok makineli bir kurulumu ölçmedik.

Savunma sanayiinde eğitim verisi ve model ağırlıkları çoğu zaman dış bulut ortamına çıkarılamaz. Bu durumda eğitim altyapısı yerel ve hava boşluklu (air-gapped) olmalıdır; bu konuyu Bölüm 71.13'te kurumsal bağlam olarak ele aldık. Burada şunu eklemek yeter: yerel kümede GPU sayısı, bellek ve ağ bant genişliği, model boyutu ve batch planlaması birbirine bağlıdır. Bu bölümdeki bellek formülleri ve ZeRO tablosu, bir teklif hazırlarken hangi donanımın yeterli olduğunu hesaplamak için doğrudan kullanılabilir.

## Çözümlü Örnekler

### Örnek 1 (★): 1000 elemanlı dizi için ızgara ve global indeks

**Adım 1 — Anla.** n = 1000 elemanlı bir dizi var ve her iş parçacığı tek bir elemanı işleyecek. Blok boyutu 256 olsun. Kaç blok başlatmalıyız? Her iş parçacığı hangi elemanı alır? Son bloktaki fazla iş parçacıkları ne yapmalı?

**Adım 2 — Örnekle.** Daha küçük bir durum düşünelim: n = 10, blok boyutu 4. Blok sayısı `ceil(10 / 4) = 3` olur, yani 12 iş parçacığı başlatılır. Son blokta iki iş parçacığı (indeks 10 ve 11) fazladır ve diziye erişmemelidir.

**Adım 3 — Kaba çöz.** Blok sayısı için `(n + 255) // 256` kullanılır: `(1000 + 255) // 256 = 4`. Her iş parçacığı için global indeks `i = blockIdx.x * 256 + threadIdx.x` ile bulunur. Koşul `if i < n` fazla iş parçacıklarını korur.

**Adım 4 — Örüntü.** Dört blok 1024 iş parçacığı eder ve fazla olan 24 tanesi son blokta, yani indeksleri 1000..1023 olanlardır. Genel kural: blok sayısı `(n + T - 1) // T`, fazla iş parçacığı sayısı `blok * T - n`. İlk üç blok tamamen dolu, son blokta 232 iş parçacığı aktiftir.

**Adım 5 — İyileştir.** Blok sayısı çok büyük olduğunda, her iş parçacığının bir elemanla sınırlı kalması yerine bir döngüde birden çok eleman işlemesi (ızgara-adım döngüsü) daha iyi olabilir. 1000 elemanlık bu örnekte gereksiz; ama 10^9 elemanlık bir dizide ızgaranın boyutunu donanıma göre sınırlamak gerekir.

**Adım 6 — Doğrula.** Her bloğun hangi indeksleri işlediğini tabloyla kontrol et:

| blockIdx | threadIdx | i = blockIdx·256 + threadIdx | i < 1000 aktif |
|---|---|---|---|
| 0 | 0..255 | 0..255 | 256 |
| 1 | 0..255 | 256..511 | 256 |
| 2 | 0..255 | 512..767 | 256 |
| 3 | 0..255 | 768..1023 | 232 |

Aktif iş parçacığı toplamı 256 + 256 + 256 + 232 = 1000 = n. Bu hesap, 76.1'deki vektör toplama betiğinde `n = 1 << 20` için de doğru çalıştı (`dogru: True`).

**Bunu AI'sız yazabilir misin?** n = 5000 ve blok boyutu 128 için blok sayısını, son blokta kaç iş parçacığının aktif olduğunu ve `blockIdx = 20` olan bloktaki ilk iş parçacığının global indeksini hesapla.

### Örnek 2 (★★): Paylaşılan bellekte ağaç indirgemesi, sekiz eleman için adım adım

**Adım 1 — Anla.** Sekiz elemanlık bir dizi tek bir blokta paylaşılan bellekte toplanacak. Amaç, toplamı log₂(8) = 3 adımda elde etmek. İki adresleme biçimini karşılaştıracağız: ayrışmalı (tid % 2s == 0) ve sıralı (tid < s).

**Adım 2 — Örnekle.** Dizi a = [3, 1, 4, 1, 5, 9, 2, 6]; toplam 31. Beklenen sonuç 31.

**Adım 3 — Kaba çöz.** Her adımda `s` yarılanır: sıralı adresleme için `s = 4, 2, 1` ve her adımda `sd[i] += sd[i + s]` (i < s). Bu, her adımda aktif iş parçacıklarının bitişik olmasını sağlar.

**Adım 4 — Örüntü.** Sıralı adresleme her adımda ilk `s` iş parçacığını kullanır, yani aktif iş parçacıkları bir warp içinde bitişiktir ve ayrışma yoktur. Ayrışmalı sürümde ise ilk adımda aktifler 0, 2, 4, 6'dır; bu, aynı warp içinde dağınık lane'ler demektir ve her adımda aynı warp'ın farklı yolları sırayla çalışır.

**Adım 5 — İyileştir.** Bir warp 32 iş parçacığı içerir; son beş adım (s = 16..1) warp kaydırmasıyla (shuffle) yapılabilir ve paylaşılan bellek ile senkronizasyon ortadan kalkar. Bu, 76.4'te ölçtüğümüz üçüncü sürümün mantığıdır.

**Adım 6 — Doğrula.** Sıralı adresleme için dizinin durumu:

| adım | s | sd[0] … sd[7] |
|---|---|---|
| başlangıç | - | 3 1 4 1 5 9 2 6 |
| 1 | 4 | 8 10 6 7 5 9 2 6 |
| 2 | 2 | 14 17 6 7 5 9 2 6 |
| 3 | 1 | 31 17 6 7 5 9 2 6 |

Yalnızca `sd[0]` anlamlı son değerdir ve 31'dir. Ayrışmalı sürümde ilk adım `sd[0] = 4`, `sd[2] = 5`, `sd[4] = 14`, `sd[6] = 8` verir; ikinci adım `sd[0] = 9`, `sd[4] = 22`; son adım `sd[0] = 31`. İki yolun sonucu aynıdır, yalnızca hangi iş parçacıklarının çalıştığı farklıdır.

**Bunu AI'sız yazabilir misin?** Aynı sıralı ağacı 16 elemanlı bir dizi için kur: kaç adım var, her adımda kaç iş parçacığı aktif ve son adımda hangi `sd` değeri 0 numaralı yazmacta olur?

### Örnek 3 (★★): Dört düğümde halka all-reduce, adım adım veri akışı

**Adım 1 — Anla.** Dört düğümün her birinin dört elemanlık bir vektörü var. Hedef, her düğümün sonunda dört elemanın toplamını tutmasıdır. İletişim hacmini de bulacağız.

**Adım 2 — Örnekle.** Düğüm vektörleri v0 = [1, 2, 3, 4], v1 = [10, 20, 30, 40], v2 = [100, 200, 300, 400], v3 = [1000, 2000, 3000, 4000]. Toplam [1111, 2222, 3333, 4444]. Her parça M/N = 1 elemandır; yani 4 parça vardır ve parça k, vektörün k. elemanıdır.

**Adım 3 — Kaba çöz.** Azaltma fazında (N − 1 = 3 adım) düğüm i, parça `(i − s) mod 4`'ü komşusu i + 1'e gönderir ve gelen parçayı kendi parçasına ekler. Dağıtma fazında (3 adım) düğüm i, tam toplamı bulunan parçayı `(i + 1 − s) mod 4` komşusuna gönderir ve gelen değeri üzerine yazar.

**Adım 4 — Örüntü.** Azaltma sonunda düğüm i, parça `(i + 1) mod 4`'ün tam toplamını tutar. Dağıtma ise bu tam parçaları halkada dolaştırır. Düğüm başına gönderilen eleman sayısı 2(N − 1) parçadır ve her parça 1 elemandır; yani 6 eleman. Formül 2(N − 1)/N × M = 2 × 3/4 × 4 = 6 ile aynıdır.

**Adım 5 — İyileştir.** Naif yöntemde herkes vektörünü bir merkeze gönderir; merkez (N − 1) × M = 12 eleman alır ve tek bir düğüm darboğaz olur. Halkada ise en fazla yük her düğümde eşit dağılır. Bunun bedeli, toplam adım sayısının 2(N − 1) olmasıdır; yani gecikme düğüm sayısıyla doğrusal artar.

**Adım 6 — Doğrula.** Her adımın sonunda düğümlerin durumu (elle izlenmiştir):

| adım | düğüm 0 | düğüm 1 | düğüm 2 | düğüm 3 |
|---|---|---|---|---|
| başlangıç | [1, 2, 3, 4] | [10, 20, 30, 40] | [100, 200, 300, 400] | [1000, 2000, 3000, 4000] |
| azaltma 1 | [1, 2, 3, 4004] | [11, 20, 30, 40] | [100, 220, 300, 400] | [1000, 2000, 3300, 4000] |
| azaltma 2 | [1, 2, 3303, 4004] | [11, 20, 30, 4044] | [111, 220, 300, 400] | [1000, 2220, 3300, 4000] |
| azaltma 3 | [1, 2222, 3303, 4004] | [11, 20, 3333, 4044] | [111, 220, 300, 4444] | [1111, 2220, 3300, 4000] |
| dağıtma 3 | [1111, 2222, 3333, 4444] | [1111, 2222, 3333, 4444] | [1111, 2222, 3333, 4444] | [1111, 2222, 3333, 4444] |

Son satırda dört düğümün de aynı vektörü tuttuğunu görüyoruz. Elle izlediğimiz sonucu kontrol etmek için 76.8'deki `halka_allreduce` fonksiyonunu aynı girdiyle çalıştırdık: sonuç `[1111. 2222. 3333. 4444.]` ve düğüm başına 6 eleman oldu.

**Bunu AI'sız yazabilir misin?** N = 3 düğüm ve her düğümde M = 6 elemanlık vektörler için düğüm başına gönderilen eleman sayısını ve her fazın adım sayısını hesapla. Sonra formülün N = 3 için verdiği değerle karşılaştır.

### Örnek 4 (★★★): 1,3 milyar parametreli model, 6 GB kart ve ZeRO-3 kararı

**Adım 1 — Anla.** Elimizde 1,3 milyar parametreli bir model var ve eğitimi fp32 Adam ile yapmak istiyoruz. Her GPU'nun kullanılabilir belleği bu makinede ölçüldüğü gibi yaklaşık 4,96 GB (boş VRAM). Kaç GPU'da, hangi ZeRO aşamasıyla eğitimi sığdırabiliriz?

**Adım 2 — Örnekle.** Parametre sayısı P = 1,3 × 10^9. Parametre, gradyan ve Adam durumu toplam 16 bayt/parametre; yani tam model durumu 16 × 1,3 × 10^9 = 20,8 GB. Bu, tek karta sığmaz.

**Adım 3 — Kaba çöz.** ZeRO-3'te her bileşen N'ye bölünür: GPU başına 16P/N. N = 4 için 5,2 GB; N = 8 için 2,6 GB.

**Adım 4 — Örüntü.** Durum belleği yalnızca 1/N ile küçülür. Aktivasyon bu hesapta yoktur; batch boyutu ve sıra uzunluğuna bağlıdır. Dolayısıyla sınır, durum belleğinin 4,96 GB'ın altında kalması ve geriye kalan birkaç gigabaytın aktivasyona yetmesidir.

**Adım 5 — İyileştir.** Seçenekler: (a) N = 8 ile aşama 3; (b) N = 4 ile aşama 3 ve aktivasyon yeniden hesaplama; (c) GPU'ya sığmayan kısmı CPU belleğine taşımak (offload). Üçüncü seçenek bu bölümde ölçülmedi. İkinci seçenek N = 4'te 5,2 GB durum belleğini 4,96 GB'lık boş alana sığdırmaz; yani aktivasyon yeniden hesaplamayla bile yetmez. Birinci seçenek makul görünüyor.

**Adım 6 — Doğrula.** Tablo, `b76_07_bellek_butce.py` çıktısından alındı:

| N | aşama 0 (DDP) | aşama 1 | aşama 2 | aşama 3 (GB/GPU) |
|---|---|---|---|---|
| 4 | 20,8 | 13,0 | 9,1 | 5,2 |
| 8 | 20,8 | 11,7 | 7,15 | 2,6 |

N = 4 aşama 3 (5,2 GB) boş VRAM'i (4,96 GB) aşıyor: sığmaz. N = 8 aşama 3 (2,6 GB) 2,3 GB'lık bir pay bırakıyor; aktivasyon bu paya sığarsa eğitim başlar. Bu yüzden karar: N = 8, aşama 3; aktivasyon boyutunu tek bir ileri-geri adımında ölç ve sonuçlara göre batch'i ayarla. Ölçülmeden "sığar" demek doğru olmaz.

**Bunu AI'sız yazabilir misin?** 7 milyar parametreli bir model için aynı karar: 6 GB'lık kartlarla aşama 3 kaç GPU gerektirir (aktivasyon hariç)? Cevabını 112 / N ≤ 6 eşitsizliğinden çıkar.

## Kendin Yap Projeleri

::: dikkat
Bu iki projeyi yapay zekâ aracı olmadan yap. Önce kağıtta tasarımını çiz, indeks hesabını elle yap, sonra kodla. Ölçümler için bu bölümdeki `olcum.py` yardımcısını ve ısınma koşusu kuralını kullan; kendi zamanlama kodunu yazacaksan CUDA olaylarını kullan, duvar saatini kullanma.
:::

### Proje 1 (★★): 3 × 3 konvolüsyon çekirdeği: naif ve döşemeli

**Amaç.** Tek kanallı bir görüntüye 3 × 3 konvolüsyon uygulayan iki GPU çekirdeği yazmak: naif (her çıktı pikseli global bellekten okur) ve paylaşılan bellekle döşemeli. Sonuçları PyTorch'un `torch.nn.functional.conv2d` fonksiyonuyla karşılaştır. Dikkat: PyTorch'un `conv2d`'si çekirdeği ters çevirmez; yani aslında çapraz korelasyon hesaplar. Senin çekirdeğin de aynı tanımı kullanmalı.

**Yapılacaklar / beklenen davranış.** Girdi 4096 × 4096 float32 bir görüntü ve 3 × 3 bir çekirdek olsun. Kenar pikselleri için çıktı boyutu 4094 × 4094 olabilir (valid mod). Döşemeli sürümde blok, kendi çıktı döşemesinden 1 piksel büyük bir girdi döşemesini (halo) paylaşılan belleğe yüklemelidir.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Blok boyutunu 16 × 16 seç. Paylaşılan bellek dizisini 18 × 18 tanımla. Halo elemanlarını yüklerken sınır kontrolünü unutma. Çekirdek ağırlıklarını her iş parçacığında sabit bir dizi olarak tutabilirsin.

**Başarı kriterleri.** (1) Her iki sürümün en büyük mutlak hatası, PyTorch sonucuna göre 1e-5'ten küçük. (2) Süreler CUDA olaylarıyla, ısınma sonrası 7 tekrarın medyanı olarak ölçülmüş. (3) Döşemeli sürüm naif sürümden en az 1,5 kat hızlı, ya da hızlı değilse neden olduğunu aritmetik yoğunlukla açıkla. (4) Rapor, her sürüm için GFLOP/s ve GB/s değerlerini verir.

### Proje 2 (★★★): Kendi halka all-reduce'un ile DDP'nin gradyanlarını eşleştirmek

**Amaç.** Bu bölümdeki `halka_allreduce` fonksiyonunu PyTorch tensörleri ve gloo arka ucu üzerinde gerçek süreçler arasında çalıştır. Sonra, iki ya da dört süreçte, her süreç yerel batch'inin gradyanını hesaplayıp kendi halka all-reduce'unla ortalasın ve sonucu DDP'nin sonucuyla karşılaştır.

**Yapılacaklar / beklenen davranış.** Her süreç M elemanlık gradyan vektörünü düzleştirir, N − 1 + N − 1 adımda komşularıyla değiş tokuş yapar ve sonunda ortalamayı alır. Bu ortalamayı DDP'nin aynı batch üzerindeki gradyanıyla karşılaştır. Windows'ta TCP rendezvous çalışmadığı için dosya deposu kullan.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** `dist.isend` ve `dist.irecv` kullan; sırayla gönderip almak deadlock'a yol açabilir. Her parça için hangi süreç komşusunun olduğunu `(rank + 1) % N` ve `(rank - 1) % N` ile hesapla. Gönderim sayısını bir sayaçla tut ve formül 2(N − 1)/N × M ile karşılaştır.

**Başarı kriterleri.** (1) İki ve dört süreçte her süreç sonucu aynı ve DDP gradyanına göre en büyük mutlak fark 1e-6'dan küçük. (2) Gönderilen toplam eleman sayısı formülle birebir eşleşiyor. (3) Kodunda deadlock olmadan 20 ardışık adım tamamlanıyor. (4) Ölçülen hacim ile formül arasındaki fark raporda açıklanmış.

### Ek Alıştırmalar

1. ★ Bir warp içinde 32 iş parçacığının hepsi aynı `if` koşulunu sağlıyorsa dallanma ayrışması olur mu? Neden?
2. ★ Bir matris çarpımı için 4096 × 4096 float32 matrisin global bellekten tek okunuşunun baytını hesapla; döşeme boyutu T = 32 için toplam global okuma kaç kat azalır?
3. ★★ Naif matris çarpımında iki girdi matrisinin toplam okuma hacmi nedir? Bu hacim, önbelleklerin hiç yardım etmediği varsayımına göre ölçülen 271 GFLOP/s ile nasıl karşılaştırılır?
4. ★★ Bir modelin GPU başına belleği 16P/N ile tahmin edildi. Gerçek ölçüm bunun yüzde kaç üzerinde çıkabilir ve nedenleri neler olabilir?
5. ★ Halka all-reduce'da N = 16 ve M = 10^6 elemanlık bir gradyan için düğüm başına gönderilen eleman sayısını hesapla.
6. ★★ GPipe'da p = 8 aşama ve kabarcık oranını %10'un altına düşürmek için gereken en küçük mikro-batch sayısını bul.
7. ★★ Bir CUDA graph yakalamak için girdi şeklinin sabit olması neden gerekir? Değişken uzunluklu sıralarla ne olur?
8. ★ `torch.cuda.max_memory_allocated()` ile `torch.cuda.memory_reserved()` farkı neyi gösterir? Biri büyükse ne anlama gelir?
9. ★★★ Mülakat: Bir eğitim işi GPU'da beklenenden yavaş. Gerçek bir ölçüm yapmadan önce hangi üç hipotezi sıralarsın ve her biri için hangi tek ölçümü yaparsın?
10. ★★ Mülakat: Sekiz GPU'ya çıktığında eğitim süresi neden iki katına kadar düşmedi? Amdahl ve iletişim payı açısından açıkla.
11. ★★ Mülakat: Veri paralelliğinde batch boyutunu artırmak ile gradyan birikimi arasındaki fark nedir? İkisi de aynı etkin batch'i verebilir mi?
12. ★★★ Mülakat: Savunma uygulamasında eğitim verisi dışarı çıkamıyorsa, bir ekip hangi donanım ve yazılım kararlarını vermek zorundadır? Bu bölümdeki ölçüm alışkanlıklarından hangisi en çok işine yarar?

## Kod Okuma Egzersizi

Aşağıdaki kesit PyTorch 2.6.0 (`torch 2.6.0+cu124`) kaynağından alındı: `torch/distributed/algorithms/ddp_comm_hooks/default_hooks.py`, 17. satırdan 30. satıra kadar. Dosya yerel kurulumdaki `site-packages` dizininden kopyalandı; kısaltma yok. Yalnızca iki uzun satır 70 sütuna sığsın diye bölündü: docstring bir satır kaydırıldı, bir atama parantez içinde dört satıra ayrıldı. Kelimeler ve kod aynı kaldı.

```python
def _allreduce_fut(
    process_group: dist.ProcessGroup, tensor: torch.Tensor
) -> torch.futures.Future[torch.Tensor]:
    """Average the input gradient tensor by allreduce and returns a
    future."""
    group_to_use = (
        process_group
        if process_group is not None
        else dist.group.WORLD
    )

    # Apply the division first to avoid overflow, especially for FP16.
    tensor.div_(group_to_use.size())

    return (
        dist.all_reduce(tensor, group=group_to_use, async_op=True)
        .get_future()
        .then(lambda fut: fut.value()[0])
    )
```

Kesitte `_allreduce_fut` fonksiyonu, bir gradyan kovasını (bucket) ortalamak için kullanılır. Gradyan, toplamadan önce süreç sayısına bölünür ve toplama asenkron olarak başlatılır; sonuç bir future olarak döner.

**Sorular — cevaplamadan geçme:**

1. `tensor.div_(group_to_use.size())` satırı `all_reduce`'dan önce yapılıyor. Kaynaktaki yorum bunun nedenini FP16 taşması olarak veriyor. Taşma neden toplamadan önce, bölünmüş değerlerle olmaz? Basit bir sayısal örnekle açıkla.
2. `dist.all_reduce(..., async_op=True)` ne döndürür, `.get_future()` ve `.then(...)` zinciri ne zaman çalışır? Bu, geri yayılımın hesap ve iletişimi nasıl örtüştürmesine izin verir?
3. Bu fonksiyon bir kova alır, ama PyTorch'un varsayılan DDP yolunda gradyanlar ayrı ayrı mı yoksa kovalar hâlinde mi toplanır? Kaynak sana neyi söylüyor, neyi söylemiyor?
4. `distributed.py` içinde varsayılan kova boyutu 25 MiB olarak yazılı (`bucket_cap_mb = 25`, `# default case (bucket cap is 25 MiB)`). Kovayı çok küçük seçmenin ve çok büyük seçmenin iki maliyetini yaz.
5. `allreduce_hook` DDP'nin sonucunu değiştirir mi? Kaynaktaki docstring'in bu konuda verdiği garanti nedir?
6. Bu kesit, halka all-reduce'un hangi bölümünü uygular: azaltma mı, dağıtma mı, yoksa ikisi birden? Ağ üzerindeki bir all-reduce'da bu fonksiyonun çağrıldığı yer ile kova toplamanın tamamlandığı yer arasındaki farkı tarif et.

## Bölüm Özeti

- GPU verim için tasarlanmıştır: çok sayıda basit birim ve gecikmeyi gizlemek için çok iş parçacığı kullanır. CPU ise tek bir akışın gecikmesini düşürür.
- CUDA'da iş parçacıkları ızgara, blok ve 32'lik warp düzeninde örgütlenir. Warp içi dallanma ayrışması, dalların gerçekten ayrışması durumunda maliyet yaratır; derleyici kısa dalları predikatlayabilir.
- Bellek erişimi birleşik olmalıdır. Adımlı erişimde faydalı bant genişliği düşer, çünkü GPU her okumada 32 baytlık sektör taşır.
- Paylaşılan bellek ve warp kaydırması, indirgeme ve döşemeli matris çarpımı gibi çekirdeklerin hızının kaynağıdır; roofline, bir çekirdeğin bellek mi hesap mı tavanına bağlı olduğunu gösterir.
- Çekirdek birleştirme, bellek trafiğini azaltır; bu bölümde büyük boyutta yaklaşık 4,7 kat hızlanma ölçtük. Akışlar, kopya ve hesabı örtüştürür; burada 1,7 kat kazanç vardı.
- DDP, gradyanları all-reduce ile ortalar; halka all-reduce düğüm başına yaklaşık 2M eleman gönderir. Windows'ta NCCL yoktur ve gloo ile CPU üzerinde çalışılır.
- Boru hattında kabarcık oranı (p − 1)/(m + p − 1) ile verilir; tensör paralelliği kabarcık üretmez ama her katmanda iletişim ister.
- FP32 Adam eğitiminde durum başına 16 bayt/parametre; ZeRO-3 bunu N'ye böler. Aktivasyon ayrıca hesaplanmalıdır. Ölçülmeden "sığar" demek yanlıştır.

**Sonraki bölümde:** Bölüm 77'de (MLOps) bu bölümde ölçtüğümüz sayıların nasıl sürümlendiğini, deney kayıtlarında nasıl tutulacağını ve bir eğitim işinin hangi metriklerle izleneceğini göreceğiz. Bu bölümde ölçümleri CSV dosyalarına yazdık; ama hangi kod ve hangi sürümle üretildiklerini takip etmek ayrı bir iştir. Bölüm 77'nin ilk motivasyonu budur.

::: mulakat
1. Bir warp içinde iki dal ayrışırsa maliyet neden yalnızca iki kat olmaz da, iki yolun toplam süresi kadar olur?
2. Naif matris çarpımının aritmetik yoğunluğu neden 0,25 flop/bayt'tır ve döşeme bu değeri nasıl değiştirir?
3. Bir modelin tek bir GPU'ya sığıp sığmadığını hangi formülle hesaplarsın? Parametre başına baytları ve hesaba katmadığın kalemleri say.
4. Halka all-reduce'da düğüm başına iletişim hacmi neden N'den neredeyse bağımsızdır, ama adım sayısı N ile artar?
5. İki GPU'da eşit büyüklükte batch ile DDP eğitimi, tek GPU'da iki katı batch ile aynı gradyanı verir mi? Verirse neden, vermezse hangi koşulda?
6. Boru hattında p = 4 ve m = 4 iken kabarcık oranı nedir? Kabarcığı azaltmanın iki yolu hangileri ve bedelleri ne?
7. Bir eğitim adımı GPU'da yavaş görünüyor. Profiler ya da ölçüm olmadan ilk hangi iki şeyi kontrol edersin?
8. ZeRO-3 neyi böler, neyi bölmez? Bellek tahmininde aktivasyonu neden ayrı tutarsın?
