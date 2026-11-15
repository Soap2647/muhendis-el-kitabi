## 80.3 Veri: sentetik sahneden operasyonel akışa

Modelin ne öğrendiğini anlamak için önce ona ne gösterdiğimizi bilmeliyiz. Bu bölümde veri üreticisini Bölüm 67'deki sentetik sahne üreticisinden (67.10) yola çıkarak dört yönde genişlettik: aydınlatma, gürültü, bulanıklık ve ölçek. Ayrıca iki yeni küme ekledik. Birincisi operasyonel kaymayı temsil eder: sis ya da yansımayla parlayan bir arka plan, azalmış kontrast, artmış gürültü, hafif bulanıklık ve uzaklaşan hedefler. İkincisi OOD (out-of-distribution, dağılım dışı) kümesidir: eğitimde hiç görülmemiş, kuşa benzeyen yatay iki kanatlı şekiller içerir ve bunların etiketi yoktur.

Üreticinin ayarları üç sözlükte toplanır. Her sahne, parlaklık, gürültü ve ölçek değerlerini bu aralıklardan rastgele seçer. `EGITIM` eğitim ve nominal test için kullanılır; `DRIFT` operasyonel kaymayı; `DRIFT_AGIR` ise bilerek sert seçilmiş bir kontrol kümesini üretir. Sert kaymanın neden ayrıca tutulduğunu 80.4'te göreceğiz.

Kodun ilk parçası sabitleri ve ayarları verir. Bulanıklık (`bul`) bir olasılık ve sigma aralığıdır; ölçek (`olcek`) hedef boyutunu çarpar.

{{KOD veri 1}}

Kuşa benzeyen OOD şekli, iki yatay elipsin birleşimidir. Hedef sınıflarından (daire, kare, üçgen) farklı bir siluet vermek için seçildi. Şekil maskelerinin geri kalanı Bölüm 67'deki `_sekil` fonksiyonundan gelir; yeniden yazmak yerine kullandık.

{{KOD veri 2}}

Sahne üretimi üç adımda ilerler: arka planı doldur, nesneleri katman sırasıyla çiz ve sonra gürültü ekle. Bir nesnenin etiket kutusu, yalnızca görünen piksellerinden hesaplanır; üst üste binen ve neredeyse tamamen kapanmış nesneler etiketlenmez. OOD nesneleri hiçbir zaman etiketlenmez. Bu kural, OOD'deki tespitlerin neden yanlış sayıldığını açıklar.

{{KOD veri 3}}

Video üretimi, takip için ayrı bir fonksiyondur. Dört nesne doğrusal hareket eder ve ikisi (0 ve 1) aynı bölgede kesişir; bu, kimlik değişimi riskinin en klasik durumudur (Bölüm 67.18). Beşinci nesne, kuş benzeri OOD hedeftir ve kareler boyunca yavaşça yatay gider.

{{KOD veri 4}}

Kodun devamı, her karenin görüntüsünü ve gerçek kutularını üretir. Burada bir kural önemlidir: bir nesne karenin dışına çıkmışsa, görünür alanı yüzde 50'nin altına düştüğünde etiketlenmez. Bu kuralı sonradan ekledik; ilk sürümde kareden çıkmış nesneler de etiketleniyordu ve bu, aşağıda anlatacağımız bir ölçüm hatasına yol açtı.

{{KOD veri 5}}

Bu betiğin `__main__` bölümü, üreticinin çıktı istatistiklerini basar. Sınıf dağılımının dengeli olduğunu ve kayma kümesinin piksel ortalamasının nominalden belirgin biçimde yüksek olduğunu bu çıktıdan görürüz.

{{KOD veri 6}}

{{CIKTI veri.txt python b80_veri.py}}

### Ayrım: sahne düzeyinde, tohumla

Bölüm 54'ün ve Bölüm 57'nin ilk kuralı, eğitim ve test verisinin birbirine karışmamasıdır. Burada her küme ayrı bir tohumdan üretildiği için sahneler bağımsızdır; bir sahne ya da video iki kümede birden yer almaz. Tablo, kümelerin nasıl kurulduğunu gösterir.

| Küme | Tohum | Boyut | Ayar | Kullanım |
|---|---|---|---|---|
| Eğitim | 0 | 3 000 sahne | EGITIM | Model eğitimi |
| Doğrulama | 5 | 300 sahne | EGITIM | Eşik ve takip modu seçimi |
| Test (nominal) | 777 | 500 sahne | NOMINAL | Son ölçüm (R1) |
| Operasyonel kayma | 888 | 500 sahne | DRIFT | R2 ve izleme |
| Sert kayma (kontrol) | 890 | 500 sahne | DRIFT_AGIR | Bilgi amaçlı |
| OOD | 999 | 500 sahne, +1 kuş | NOMINAL | Güvence (80.7) |
| Video doğrulama | 200 ... 204 | 5 video x 120 kare | NOMINAL | Takip modu seçimi |
| Video test | 300 ... 304 | 5 video x 120 kare | NOMINAL | Takip ölçümü |
| Video kayma | 400 ... 404 | 5 video x 120 kare | DRIFT | Takip ölçümü |

Dikkat edilecek nokta, nominal test kümesinin eğitim dağılımıyla aynı olmasıdır. Bu bilerek yapıldı: nominal test "içinde kalan" veriyi ölçer, kayma ise "dışında kalan" veriyi. Nominal test sayısı, eğitimdeki sahnelerin üreticisinin gerçek dağılımını temsil eder; bu bir sınırlılıktır ve 80.9'daki model kartında yazılıdır.

### Etiket hatası: ölçümü bozan şey modelin değil etiketin hatasıydı

İlk video ölçümümüzde doğrulama MOTA'sı 0,60 civarındaydı. Takip modeli kötü görünüyordu, bu yüzden takip parametrelerini ayarlamaya başlamıştık. Sonra kareden çıkmış nesnelerin hâlâ "gerçek" sayıldığını fark ettik. Bu nesneler karede piksel olarak yoktu, ama gerçek kutuları duruyordu. Dedektör bunları bulamıyordu ve her biri bir kaçırma (FN) olarak sayılıyordu.

Kural düzeltildikten sonra aynı model ve aynı takipçi için doğrulama MOTA'sı 0,60'tan 0,77'ye çıktı. Yani ölçümdeki sorunun büyük kısmı etiketteydi, modelde değil. Bu, değerlendirme hatalarının neden bu kadar sinsi olduğunu gösterir: sayı düşük çıktığında ilk şüphe modele gider, ama kendi ölçüm aracınızı da sorgulamalısınız. Bölüm 57'de tartıştığımız değerlendirme disiplini tam olarak bunu koruma amacı taşır.

Şekil 80.3, üç kümeden birer örnek gösterir. Üst satır nominal test, orta satır operasyonel kayma ve alt satır OOD'dir. Kayma satırında arka plan daha açık ve gürültü daha belirgindir; OOD satırındaki kuş benzeri şekiller etiketsizdir ve bir dedektör için tuzak oluşturur.

![Şekil 80.3: Üç kümeden örnek sahneler (yeşil kutu: etiketli nesne)](gorseller/b80_sahneler.png)
