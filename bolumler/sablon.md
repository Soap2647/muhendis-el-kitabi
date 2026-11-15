%% kisim_no: I
%% kisim_ad: Programlama Temelleri
%% bolum_no: 0
%% baslik: Şablon — Dizgi ve Bileşen Örneği

Bu sayfa gerçek bir bölüm değildir; kitabın **dizgi düzenini** ve tüm görsel bileşenlerini tek yerde göstermek için hazırlandı. Amaç: yazı tipi, başlık hiyerarşisi, kod blokları, çağrı kutuları, şekiller ve tabloların nasıl göründüğünü onaylaman. Gövde metni *serif* bir yazı tipiyle, iki yana yaslı dizilir; satır aralığı uzun okumalar için rahat tutulmuştur. Değişken adları ve komutlar satır içinde `malloc()` ya da `git rebase` gibi tek aralıklı (monospace) gösterilir.

Aşağıda bir konunun neden önemli olduğunu anlatan tipik bir paragraf var. Cümleler kısa ve net. Akademik jargon minimumda. Her soyut kavram somut bir şeye bağlanır — tıpkı bu cümlenin bir örnekle bitmesi gibi: bir programın çalışırken belleği nasıl kullandığını bilmezsen, `segmentation fault` hatasını yalnızca ezberden tanırsın, anlamazsın.

## İkinci Düzey Başlık (H2)

Her kısım yeni bir sağ sayfada, her bölüm yeni bir sayfada başlar. İkinci düzey başlıklar konuyu ana bloklara böler. Sayfa dibinde yalnız kalmamaları için otomatik olarak bir sonraki sayfaya taşınabilirler.

### Üçüncü Düzey Başlık (H3)

Üçüncü düzey başlıklar bir H2 bloğunun içindeki alt konulardır. Aşağıda kod blokları, kutular ve tablolar geliyor.

#### Dördüncü Düzey Başlık (H4)

En ince kırılım. Genelde bir prosedürün adımlarını ya da küçük bir alt notu ayırmak için.

## Kod Blokları

Aşağıdaki kod, bir tam sayı dizisinin toplamını klasik bir döngüyle hesaplıyor. Her satır numaralı ve söz dizimi renklendirmeli:

```c
#include <stdio.h>

// bir dizinin elemanlarını toplar
int topla(int *dizi, int n) {
    int toplam = 0;                 // biriktirici
    for (int i = 0; i < n; i++) {
        toplam += dizi[i];          // her elemanı ekle
    }
    return toplam;
}
```

Aynı işin Python karşılığı çok daha kısa; farkı görmek önemli:

```python
def topla(dizi):
    toplam = 0
    for x in dizi:      # doğrudan eleman üzerinde gez
        toplam += x
    return toplam       # tek satırda: return sum(dizi)
```

Bir programı derleyip çalıştırdığında terminalde şunu görürsün:

```term
$ gcc topla.c -o topla
$ ./topla
Dizinin toplamı: 42
```

## Çağrı Kutuları

Kenar kutuları okuru uyarır, ipucu verir ya da başka bölüme bağlar.

::: dikkat
`malloc()` ile ayırdığın her bloğu `free()` ile geri vermezsen bellek sızıntısı (*memory leak*) oluşur. Uzun çalışan programlarda bu, sistemi yavaş yavaş çökertir.
:::

::: ipucu
Bir diziyi fonksiyona geçirdiğinde aslında ilk elemanın adresini geçirirsin. Bu yüzden fonksiyon içinde `sizeof(dizi)` sana dizinin boyutunu **değil**, bir işaretçinin boyutunu verir.
:::

::: baglanti
Bellek düzeni ve işaretçi aritmetiği **Bölüm 2**'de; sürecin bellekteki yerleşimi **Bölüm 25**'te derinlemesine işlenir.
:::

::: mulakat
"Stack ve heap arasındaki fark nedir, hangi değişken nerede saklanır?" — Bu soru neredeyse her whiteboard mülakatında bir biçimde karşına çıkar.
:::

## Şekiller

Diyagramlar içeriğe birebir çizilir. Aşağıda bir sürecin bellek düzeni gösteriliyor:

![Şekil 0.1: Bir sürecin bellekteki yerleşimi — yüksek adresten düşük adrese doğru stack, heap, data ve text segmentleri.](gorseller/_ornek_memory.png)

CPU'nun her komutu işlerken izlediği döngü ise şöyledir:

![Şekil 0.2: Komut döngüsü — getir (fetch), çöz (decode), yürüt (execute), yaz (writeback); ardından döngü başa döner.](gorseller/_ornek_cpu.png)

## Tablolar

Farklı veri yapılarının maliyetlerini karşılaştıran bir tablo, bir bakışta karar vermeni sağlar:

| İşlem | Dizi (Array) | Bağlı Liste | Hash Tablosu |
|---|---|---|---|
| Rastgele erişim | O(1) | O(n) | — |
| Başa ekleme | O(n) | O(1) | — |
| Arama | O(n) | O(n) | O(1)* |
| Bellek düzeni | bitişik | dağınık | dağınık |

Yukarıdaki `O(1)*` amortize edilmiş maliyeti gösterir; en kötü durumda çakışmalar bunu bozabilir.

## Listeler

Bir problemi çözerken izlenen tipik adımlar:

1. Girdi ve çıktıyı net tanımla.
2. Kısıtları (constraint) çıkar: boyut, zaman, bellek.
3. Önce çalışan bir brute-force çözüm yaz.
4. Sonra darboğazı bul ve optimize et.

Bir veri yapısı seçerken sorulacaklar:

- Erişim mi ağırlıklı, ekleme/silme mi?
- Sıra önemli mi, yoksa yalnız üyelik mi?
- Bellek bitişik mi olmalı (cache dostu)?

---

## Zorluk Rozetleri ve Kapanış

Kendin Yap projeleri zorluk derecesiyle işaretlenir: **⭐ basit**, **⭐⭐ orta**, **⭐⭐⭐ ileri**. Bu şablon buraya kadar; onaylarsan gerçek bölümleri bu düzende üretmeye başlıyorum.
