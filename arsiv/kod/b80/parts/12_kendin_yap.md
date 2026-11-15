## Kendin Yap Projeleri

::: dikkat
Bu projelerde bir yapay zekâ aracına kod yazdırmayın, hata ayıklatmayın ya da cevap sormayın. Kitabı kapatıp boş bir dosyayla başlayın. Her projenin sonunda, kodunuzun ne yaptığını bir sayfada anlatabiliyor olmalısınız. Yardım gerekirse, önce ilgili bölüme dönün; ipuçları çözüm değildir, yalnızca yönü gösterir.
:::

### Proje 1 (★★): Sistemi kendi kameranıza taşıma

**Amaç.** Bu bölümün sistemini, kendi kameranızla kendi çektiğiniz kısa bir videoda çalıştırmak. Kayıt, kendi bahçenizde ya da kendi odanızda, sizin mülkünüzde olmalı. Başkalarını ya da mülkiyeti belirsiz alanları kaydetmeyin; kayıtları yalnızca bu projede kullanın ve paylaşmayın. Hedef, sistemin gerçek bir sensörde nasıl davrandığını görmek ve kaymayı ölçmektir.

**Yapılacak ve beklenen davranış.** Üç ila beş dakikalık bir video kaydedin. Videonun bir bölümünü etiketleyin (en az 100 kare, ayrı bir küme olarak). Videonun kare ortalama parlaklığını eğitim referansıyla karşılaştırın ve PSI değerini hesaplayın. Videoyu 96 x 96 gri tonlamaya indirin ve modeli bu girdiyle çalıştırın. Sonucu, eğitim ve nominal test sonuçlarıyla karşılaştıran bir tablo yazın.

**Önerilen yaklaşım (ipucu).** Önce PSI'yı hesaplayın; bu, sorunun ne kadar büyük olduğunu gösterir. Bölüm 77.10'daki PSI formülünü ve 80.8'deki izleme betiğini inceleyin, ama kodu kopyalamayın; kendi referansınızla yeniden yazın. Ön işleme (gri dönüşüm, boyutlandırma, normalizasyon) eğitimle birebir aynı olmalı; Bölüm 77.8'deki çarpıklık sorununu hatırlayın. Kamera ışığı değiştiğinde ne olduğunu gözlemleyin.

**Başarı kriterleri.**
- Kendi videonuz için PSI (parlaklık) değerini ve referansla karşılaştırmasını bir tabloda verin.
- Etiketlediğiniz 100 kare üzerinde mAP@0,5 değerini ölçün ve sonucu sayısal olarak raporlayın; hedef eşik yoktur, ama düşük çıkarsa nedenini açıklayın.
- Aynı videoda kare başına gecikmeyi p50 ve p95 olarak ölçün; ölçüm koşullarını (işlemci, iş parçacığı, pil durumu) yazın.
- Bir sayfalık bir rapor: kaymanın hangi özellikten (parlaklık, kontrast, bulanıklık, ölçek) geldiğini kanıtla birlikte söyleyin.

### Proje 2 (★★★): İkinci sensör ekleyip Kalman ile füzyon

**Amaç.** Sisteme sentetik bir radar ekleyip kamera tespitleriyle birleştirmek. Hedef, tek kamerada kaybolan ya da kesişmede kimliği karışan nesnelerde, radar bilgisinin takibi ne kadar iyileştirdiğini ölçmektir. Bölüm 62.9'daki sensör füzyonu fikrini uygulamış olacaksınız.

**Yapılacak ve beklenen davranış.** Radar simülatörü yazın: her karede gerçek nesnelerin (x, y) konumunu gürültüyle ölçsün, bazı karelerde ölçümü olasılıkla düşürsün (örneğin yüzde 20). Kamera tespitleriyle birlikte Kalman filtresinin güncelleme adımını iki ölçümle (kamera kutusunun merkezi ve radar konumu) sırayla çalıştırın. Sadece kamera ile füzyonu aynı test videolarında karşılaştırın.

**Önerilen yaklaşım (ipucu).** Durum vektörünü Bölüm 67.15'teki gibi (cx, cy, w, h, vx, vy) tutun. Radar ölçümü yalnızca (cx, cy) bileşenlerini ölçer; bu durumda gözlem matrisi H'nin yalnızca ilk iki satırı birdir. Radar ölçüm gürültüsü R_radar'ı ayrı bir köşegen matrisle verin. Kameranın ve radarın koordinatları aynı olmadığı için bir dönüşüm varsayımı yazın ve bunu bir ipucu olarak değil, bir varsayım olarak raporlayın. Kayıp kareleri, Kalman tahmin adımının tek başına çalıştığı durumlar olarak ele alın.

**Başarı kriterleri.**
- Üç tohumla (her tohum için ayrı radar gürültüsü) test videolarında MOTA ve IDSW değerlerini kamera-only ile karşılaştırın; ortalama ve standart sapma yazın.
- Füzyonun MOTA'yı en az 0,03 artırdığını ya da bunun olmadığını, tohumlar arası farkın gürültüden büyük olup olmadığını (Bölüm 57) belirterek söyleyin.
- Radar kaybı senaryosunda takibin max_age süresince kopmadığını gösteren bir iz şekli üretin.
- Radarın gerçekçi olmadığını, bu bir varsayım olduğunu rapora yazın; gerçek sensör hatasıyla ilgili hiçbir iddiada bulunmayın.

### Ek Alıştırmalar

Aşağıdaki on iki problem, zorluk etiketiyle sıralanmıştır. Her biri bir ya da üç cümledir; cevapları kendiniz yazın. (Mülakat) etiketli olanlar klasik mülakat sorularıdır.

1. ★ 96 x 96 bir görüntüde iki kutunun IoU değerini, (a) hiç kesişmediklerinde, (b) birinin diğerinin içinde olduğunda, (c) tam çakıştıklarında elle hesaplayın.
2. ★ (Mülakat) NMS'de eşik 0,3 ve 0,5 olsun. Hangisi daha çok tespit bastırır ve bu, kaçırmayı mı yanlış alarmı mı artırır?
3. ★★ (Mülakat) Bir sınıflandırıcının eşiğini değiştirmek mAP'i değiştirir mi? Cevabınızı bir örnekle gerekçelendirin.
4. ★★ (Mülakat) Bir dedektörün mAP@0,5 değeri yüksek, mAP@[0,5:0,95] değeri düşük. Bu ne anlatır ve nasıl iyileştirilebilir?
5. ★★ Bir 3 x 4 maliyet matrisi verildiğinde, Macar algoritmasının hangi tespiti eşleştirmeden bırakacağını ve nedenini elle bulun.
6. ★★★ (Mülakat) Kaybolan bir nesnenin izi max_age boyunca FP üretiyor. Üç farklı önlem önerin ve her birinin maliyetini yazın.
7. ★★ 8-bit simetrik kuantizasyonda bir tensörün en büyük mutlak değeri 3,2 ise ölçeği hesaplayın ve 1,7 değerinin kuantize edilmiş karşılığını yazın.
8. ★★ Bir Conv katmanının bir çıkış kanalı için ağırlıklar, BN gamma, beta, ortalama ve varyans verildiğinde, katlanmış ağırlık ve sapmayı el ile hesaplayın.
9. ★★★ (Mülakat) İki modelin test mAP'i 0,92 ve 0,93, test kümesi 200 nesne. Hangi kararı verirsiniz ve hangi istatistiği kullanırsınız (Bölüm 49 ve 57)?
10. ★★ (Mülakat) PSI 0,25 ve KS p değeri 0,5 olsun. Hangi sinyale güvenirsiniz ve neden?
11. ★★★ (Mülakat) Bir gözetleme sisteminin kare bütçesi 33 ms; ağ 20 ms, takip 8 ms. Bütçe aşılmış mı, hangi ölçüme bakarsınız ve hangi iyileştirmeyi önce denersiniz?
12. ★ (Mülakat) "Modelim test kümesinde yüzde 99 doğru" diyen birine ilk soru ne olmalı?
