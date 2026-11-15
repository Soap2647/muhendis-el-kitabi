## Çözümlü Örnekler

Bu dört örnek Bölüm 5'teki altı adımı izler. Her birinde adımlar açıkça etiketlenmiştir ve doğrulama bir iz tablosuyla yapılır. Sayıları önce elle hesaplayın; kod yalnızca sonucu teyit etsin.

### Örnek 1 (★): İki histogram arasında PSI'nin elle hesabı

**Adım 1 — Anla.** Referans dağılım dört kutuya eşit bölünmüş: her kutuda referansın yüzde 25'i var. Yeni pencerede oranlar sırasıyla 0,40, 0,30, 0,20 ve 0,10. PSI'yi hesapla ve 0,2 eşiğiyle karşılaştır.

**Adım 2 — Örnekle.** İlk kutu normalden dolu, son kutu neredeyse boş. Bu bir kayma gibi duruyor. Ama hangi kutu sonucu en çok etkiliyor, bunu görmek için her kutunun katkısını ayrı hesaplamak gerekir.

**Adım 3 — Kaba çöz.** Her kutu için `(a − e) · ln(a / e)` hesapla ve dört sonucu topla. Kutu 1: `(0,40 − 0,25) · ln(0,40 / 0,25)`. Kutu 4: `(0,10 − 0,25) · ln(0,10 / 0,25)`. Diğerleri aynı biçimde.

**Adım 4 — Örüntü.** `a − e` ile `ln(a / e)` her zaman aynı işarete sahiptir: `a > e` ise ikisi de pozitif, `a < e` ise ikisi de negatiftir. Çarpımları bu yüzden her zaman sıfırdan büyük ya da sıfırdır; PSI negatif olamaz. Katkı, oranın hem referanstan uzaklaşıp hem de logaritmanın büyüdüğü kutularda en büyüktür. Kutu 4, oranı 0,25'ten 0,10'a düştüğü için en çok katkıyı verir. Bir başka sonuç da şudur: `a` ile `e` yer değiştirse terim aynı kalır, yani PSI simetriktir. Bu, PSI'nin iki yönlü KL ıraksamasının toplamı olduğunu gösterir (Bölüm 51'deki bilgi teorisi kavramlarıyla bağlantılı).

**Adım 5 — İyileştir.** Dört kutu için tabloyla hesap kolaydır, ama gerçek bir izleme sisteminde yüz kutu ve yüzlerce özellik vardır. Bu yüzden hesabı kod ile yap. Dikkat edilecek nokta sıfır oranıdır: bir kutu boşsa logaritma tanımsızdır. Bu nedenle kodda oranlara bir alt sınır (0,0001) uygulanır. Bu sınır, boş kutuların katkısını büyük ama sonlu tutar.

**Adım 6 — Doğrula.** Elle hesabın iz tablosu:

| Kutu | e | a | a − e | ln(a / e) | Terim |
|---|---|---|---|---|---|
| 1 | 0,25 | 0,40 | +0,15 | ln 1,6 = 0,4700 | +0,0705 |
| 2 | 0,25 | 0,30 | +0,05 | ln 1,2 = 0,1823 | +0,0091 |
| 3 | 0,25 | 0,20 | −0,05 | ln 0,8 = −0,2231 | +0,0112 |
| 4 | 0,25 | 0,10 | −0,15 | ln 0,4 = −0,9163 | +0,1374 |
| Toplam | | | | | 0,2282 |

Toplam 0,2282, 0,2 eşiğinin üstünde; kayma belirgin sayılır. Aşağıdaki betik aynı hesabı yapar:

{{KOD b77_ornek1.py}}

{{CIKTI b77_ornek1.txt python b77_ornek1.py}}

Kod çıktısı elle hesabın dört terimini ve toplamı birebir verir. Bu, iz tablosunun doğru olduğunu gösterir.

**Bunu AI'sız yazabilir misin?** Referans dağılımı üç kutuya eşit bölünmüş (her biri 0,333) ve yeni pencerenin oranları 0,20, 0,30 ve 0,50 olsun. PSI'yi elle hesapla; sonucu 0,1 ve 0,25 eşikleriyle karşılaştır ve hangi eşiği aştığını söyle.

### Örnek 2 (★★): Veri hash'i değişince hangi deneyler geçersiz olur?

**Adım 1 — Anla.** Ham bir sensör dosyası var ve bundan türetilmiş bir özellik dosyası üretiliyor: sıcaklık sütunu 22 ile 38 arasına kırpılıyor. Üç deney türev dosyanın ilk sürümüyle çalıştırıldı. Ham dosyaya tek bir satır eklendi. Hangi deneyler artık güncel veriyle eşleşmiyor?

**Adım 2 — Örnekle.** Ham dosya değiştiğinde türev dosya yeniden üretilir ve özeti değişir. Her deneyin kaydında hangi türev özetiyle çalıştığı yazılıdır (`veri` sütunu). Önce küçük bir zinciri düşünelim: ham `h1`, türev `o1`, deneyler `o1` ile çalıştı. Ham `h2` olduğunda türev `o2` olur. Deneyler hâlâ `o1`'e bağlı.

**Adım 3 — Kaba çöz.** Her deneyin `veri` alanını güncel türev özetiyle karşılaştır. Eşit değilse deney geçersizdir. Ayrıca türevin kaynağını kontrol et: `o1`'in kaydettiği kaynak özeti `h1`'dir; güncel ham `h2` ise türev eskimiştir.

**Adım 4 — Örüntü.** Bir veri dosyası değiştiğinde özeti de değişir; aynı özeti taşıyan deneyler aynı veriyi görmüştür. Bu yüzden geçersizlik bir deneyin ayrı bir özelliği değil, verinin özetine bağlı bir ilişkidir. Türev dosyanın kaynak bağı da aynı mantıkla çalışır: kaynak özeti değişmişse türev de değişmiş olmalıdır. Zincirin bir halkası kırıldığında bütün alt halkalar şüphelidir.

**Adım 5 — İyileştir.** Bu kontrolü elle yapmak unutulur. Eğitim betiğinin başına otomatik bir denetim eklenmelidir: betik, kullandığı veri özetini güncel dosyanın özetiyle karşılaştırsın, uyuşmazsa çalışmayı reddetsin. Kaynak bağı da veri deposunun kendi kaydında tutulmalıdır. Bu, Bölüm 77.4'teki işaretçi dosyasının genişletilmiş hâlidir.

**Adım 6 — Doğrula.** İz tablosu:

| Adım | Dosya | Özet (ilk 8) | Açıklama |
|---|---|---|---|
| Başlangıç | ham `h1` | e648480f | 1500 satır |
| Başlangıç | türev `o1` | 2b89f8a9 | `h1`'den üretildi, üç deney bu özetle çalıştı |
| Değişiklik | ham `h2` | 8314eb06 | Bir satır eklendi, özet değişti |
| Yeniden üretim | türev `o2` | 3c79b170 | Güncel türev |
| Kontrol | `o1`'in kaynağı = `h2`? | Hayır | Türev `o1` eskidi |
| Kontrol | `veri != o2` olan deneyler | 3 deney | Üçü de geçersiz |

Aşağıdaki betik bu zinciri kurar. İlk bölümü kurulum ve türetme, ikinci bölümü değişiklik ve kontrol içerir.

{{KOD b77_ornek2.py 1 15}}

{{KOD b77_ornek2.py 16 48}}

{{CIKTI b77_ornek2.txt python b77_ornek2.py}}

Çıktı iz tablosuyla birebir uyuşur: üç deney `2b89f8a9` ile kaydedildi, türevin kaynağı artık güncel değil ve üç deney de geçersiz olarak listelendi.

**Bunu AI'sız yazabilir misin?** Türev dosyası bir yerine iki ham dosyadan (`ham_a.csv` ve `ham_b.csv`) birleştirilerek üretiliyor. `ham_b.csv` değiştiğinde hangi kayıtlar tutarsız olur ve bunu tek bir sorguyla nasıl bulursun? Kaynak bağını iki özetle nasıl saklarsın?

### Örnek 3 (★★): Kanarya için gereken örnek sayısı ve süresi

**Adım 1 — Anla.** Taban modelin hata oranı yüzde 5 (p₀ = 0,05). Aday modelin hata oranının yüzde 6'ya (p₁ = 0,06) çıkmış olabileceğinden şüpheleniyoruz. Bu bir puanlık farkı yüzde 80 güçle ve yüzde 5 anlamlılıkla tespit etmek için her koldan kaç istek gerekir? Günlük 100.000 istek var ve her kola günün yüzde 2'si gidiyor. Kaç gün sürer?

**Adım 2 — Örnekle.** Önce küçük bir örnek düşünelim: her kolda 100 istek. Yüzde 5 ile yüzde 6 arasındaki fark 0,01'dir. Her kolda 100 istek olduğunda oranın standart hatası yaklaşık `√(0,055 · 0,945 · 2 / 100) ≈ 0,032`tir. Fark, standart hatanın üçte birinden bile küçüktür. Bu bir sinyal değil, gürültüdür.

**Adım 3 — Kaba çöz.** İki oranlı z-testi için gereken örnek sayısı şudur:

n = [z_{α/2} · √(2p̄q̄) + z_β · √(p₀q₀ + p₁q₁)]² / (p₁ − p₀)²

Burada p̄ = (p₀ + p₁) / 2 ve q = 1 − p. α = 0,05 için z_{α/2} = 1,96; güç 0,80 için z_β = 0,8416.

**Adım 4 — Örüntü.** Paydadaki `(p₁ − p₀)²` terimi, sonucu en çok etkileyen şeydir. Fark yarıya inerse payda dört kat küçülür ve n yaklaşık dört kat büyür. Bu yüzden küçük iyileştirmeleri bulmak için büyük örneklere ihtiyaç vardır; Bölüm 49.10'daki güç kavramı tam olarak budur. Bir başka örüntü: kanarya payı yüzde 2 olduğunda gün sayısı, gerekli n'nin 2000'e bölümüyle belirlenir.

**Adım 5 — İyileştir.** Süreyi kısaltmanın üç yolu vardır. Kanarya payını artırmak (riski artırır), ölçümün gürültüsünü azaltmak (daha iyi bir metrik seçmek) ya da sıralı bir test kullanmak (Bölüm 57.13'te çevrimiçi deneylerde görülen fikir). Burada ilk yolu kullanmıyoruz, çünkü risk sınırlamak kanaryanın amacıdır.

**Adım 6 — Doğrula.** Formülü 20.000 denemelik bir simülasyonla sınadık. Simülasyonda iki kolun gerçek hata oranlarından binom örnekleri çekilip z-testi uygulandı.

| Senaryo | n (formül) | Gün (kol payı yüzde 2) | Simülasyon gücü |
|---|---|---|---|
| p₀ = 0,05, p₁ = 0,06 | 8158 | 5 | 0,801 |
| p₀ = 0,05, p₁ = 0,055 | 31234 | 16 | 0,801 |

Formülü ve simülasyonu uygulayan modül aşağıda. `gerekli_n` formülü, `guc_sim` ise aynı testi binom örnekleriyle yeniden kurar.

{{KOD b77_ab.py 1 22}}

{{KOD b77_ab.py 23 45}}

Modülün kendi çıktısı, aşağıdaki sonuçların kaynağıdır:

{{CIKTI b77_ab.txt python b77_ab.py}}

Simülasyonun gücü formülle uyuşuyor (0,80). Aşağıdaki betik iki senaryoyu çalıştırır.

{{KOD b77_ornek3.py}}

{{CIKTI b77_ornek3.txt python b77_ornek3.py}}

Eğer yarı örnekle yetinirsek, yani n = 4079 kullanırsak, simülasyon gücü 0,508'e düşer. Yani her iki kolda yarısı kadar istekle, bir puanlık bir kötüleşmeyi bulma şansı neredeyse yazı tura gibi olur. Bu tablo, kanaryanın süresini bütçeye göre değil, tespit etmek istediğin farka göre planlaman gerektiğini gösterir.

**Bunu AI'sız yazabilir misin?** p₀ = 0,03 ve p₁ = 0,035 için n'yi hesapla. Günlük 50.000 istek var ve her kola günün yüzde 5'i gidiyorsa kaç gün gerekir? Farkı yarıya indirirsen gün sayısı kaç kat artar?

### Örnek 4 (★★★): Üretimde doğruluk düştü: kök neden hangisi?

**Adım 1 — Anla.** Telemetri modeli 40. günden sonra yüzde 14 kadar AUC kaybetti (0,955'ten 0,819'a). Üç aday açıklama var. (a) Ortam değişti ve model artık eski dağılımda çalışmıyor (kayma). (b) Eğitim ve servis farklı dönüşüm kullanıyor (çarpıklık). (c) Veri hattında bir hata var (boru hattı hatası). Her birini ayırt edecek bir ölçüm bulmalıyız.

**Adım 2 — Örnekle.** Kayıtlardan bir satıra bak. Cihaz 84, firmware v2, 45. gün. Sıcaklık kaydı 0,0. Gerçek etiket 1, yani arıza var. Model bu satırda ne diyor? Sıcaklık katsayısı 0,25 olduğu için 0,25 · (0 − 30) = −7,5 katkısı oluşur. Bu, arıza eşiği 2,6'nın çok altındadır. Model bu arızayı kaçırır.

**Adım 3 — Kaba çöz.** Her açıklamaya bir ölçüm ata. Kayma için: referans dönemle yeni dönemin PSI'si, tüm cihazlarda ve cihaz grubu başına. Çarpıklık için: servisteki tahminlerin çevrimdışı yeniden hesabıyla farkı. Hat hatası için: eksik ya da sıfır değerlerin oranı ve bu değerlerin hatalarla ilişkisi.

**Adım 4 — Örüntü.** Tüm cihazlarda PSI 0,139 çıkıyor; bu sınırda bir değer ve tek başına karar verdirmiyor. Ama cihaz grubuna bölünce tablo değişiyor: v1 cihazlarında 0,004 (çevre sabit), v2 cihazlarında 1,078 (sorun burada). Sıfır oranı yalnızca 40. günden sonra v2 cihazlarında 0,495 olarak ortaya çıkıyor. Kaçırma oranı, sıcaklığı sıfır olan gerçek pozitiflerde 1,000, diğer pozitiflerde 0,444. Referans dönemdeki kaçırma 0,437; yani model genel olarak değişmemiş, yalnızca sıfır değerli kayıtlarda çöküyor.

**Adım 5 — İyileştir.** Kök neden seri hattındaki eksik değer dönüşümüdür: eksik sıcaklık 0,0 olarak yazılıyor. Düzeltme hem veri hattında hem modelde yapılmalıdır. Hattın eksik değeri sıfır olarak değil, açıkça eksik olarak işaretlemesi ve modelin bu durumu eğitimde de aynı kuralla ele alması gerekir (tek kaynak). Veri doğrulama kuralına da eksik oranı için bir eşik eklenmelidir; Bölüm 77.7'deki `veri_denetle` bunu yapar.

**Adım 6 — Doğrula.** İz tablosu, her kontrolün ne gösterdiğini ve hangi açıklamayı desteklediğini özetler.

| Kontrol | Ölçüm | Ne söylüyor |
|---|---|---|
| PSI, tüm cihazlar | 0,139 | Sınırda; tek başına karar vermez |
| PSI, yalnız v1 | 0,004 | Çevre sabit; kayma yok |
| PSI, yalnız v2 | 1,078 | Sorun yalnızca v2 cihazlarında |
| Sıfır oranı, v2, 40–59. gün | 0,495 | Eksik değer 0,0 olarak yazılıyor |
| Çevrimdışı yeniden hesap farkı | 0,00 | Servis ve çevrimdışı kod aynı; çarpıklık yok |
| Kaçırma, sıcaklık = 0 | 1,000 | Hatanın kaynağı bu kayıtlar |
| Kaçırma, diğer pozitifler | 0,444 | Referansla (0,437) aynı |

Sonuç: kök neden **veri hattı hatasıdır**. Ortam kayması değildir, çünkü v1 cihazlarında değişim yok. Çarpıklık değildir, çünkü aynı girdiyle servis ve çevrimdışı hesap aynı sonucu verir. Hata seri hattında, eksik değerin sıfıra dönüşmesindedir. Kodun tamamı aşağıda. Simülasyon tohum 7 ile çalışır ve gerçek bir veri değildir; amaç analizin adımlarını göstermektir.

{{KOD b77_kok_neden.py 1 20}}

{{KOD b77_kok_neden.py 21 40}}

{{KOD b77_kok_neden.py 41 78}}

{{CIKTI b77_kok_neden.txt python b77_kok_neden.py}}

**Bunu AI'sız yazabilir misin?** Eksik değerleri `NaN` olarak bırakan bir servis hattı yazdığını düşün. Model `NaN` aldığında ne yapar? Bu davranışı yakalayan tek bir birim testi yaz ve hangi girdiyle başarısız olacağını söyle.
