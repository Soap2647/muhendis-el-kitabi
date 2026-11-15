## Bölüm Özeti

- Bitirme sistemi, bir İHA gözetleme videosunda hava hedeflerini algılayan, izleyen, güvence işareti koyan ve kendi kaymasını izleyen bir zincirdir. Her halka ölçülebilir bir kabul ölçütüne bağlıdır; bu bölümde on dört ölçüt tanımladık.
- Veri üretimi ve küme ayrımı sonucu belirler. Kareden çıkmış nesnelerin yanlış etiketlenmesi, takip MOTA'sını 0,60 gibi yanlış bir değere indirdi. Düzeltmeden sonra aynı model 0,77'ye çıktı. Değerlendirme hataları modelde değil ölçüm aracındadır.
- Dedektör, klasik temel çizgiyi nominal veride belirgin biçimde geçti (0,94'e karşı 0,60). Operasyonel kaymada da kullanılabilir kaldı (0,87), ama sert kaymada çöktü (0,07). Bu, izleme ve güvencenin neden gerektiğinin kanıtıdır.
- Takip, SORT'a dayanan Macar eşleştirmesi ve kare dışı filtresiyle test MOTA'sında 0,81'e ulaştı. R3 (0,90) ve R4 (IDSW <= %1) geçilemedi. Kaçırmalar, OOD kaynaklı yanlış izler ve kesişmedeki kimlik değişimi nedenlerdir.
- BatchNorm katlama, ONNX dışa aktarma ve PyTorch eşleşmesi kanıtlandı (kutu farkı 8e-6). int8 boyutu 3,6 kat küçülttü, ama lokalizasyon kaybı (9,5 puan) R6'yı geçmedi. CPU'da int8, bu küçük ağda hız kazandırmadı; zaman, son işleme ve takipte harcandı.
- Çözünürlük ve donanım birbirini belirler. 96 piksel bir mikrodenetleyiciye sığar ama tespit için yetersizdir; 640 piksel ise ara tamponuyla (1,6 MB) mikrodenetleyici sınıfı belleğe sığmaz.
- Tohum uyumu güvencesi OOD'de yanlış alarmı yüzde 96 azaltır, ama test kapsamasını 7,7 puan düşürür. Tek skor kuralı daha dengelidir (yüzde 79 azalma, 3,2 puan kayıp). Hangisinin seçileceği operasyonel bir karardır.
- İzleme, girdi kaymasını (PSI) skor ve performans sinyallerinden önce yakaladı; yeniden eğitim tetiği iki ardışık alarmla çalıştı. Yeniden eğitimin kazancı iyimserdir, çünkü simülasyonda kaymanın üretici tanımı biliniyor.

**Bundan sonrası:** Kitabın sonu bir sonun değil, bir yolun başlangıcıdır. Bu bölümdeki sistem, gerçek bir sensör ve gerçek veri olmadan tamamlanmış sayılmaz. Bir sonraki adım, kendi kayıtlarınızla (Kendin Yap Proje 1) ve bir gömülü kartla (Ek Alıştırmalar) sistemin ilk gerçek ölçümünü yapmaktır. Bölüm 39'daki simülatör-gerçek donanım farkı sözü, orada tamamlanacaktır. Sonrasında makale okuma ve yeniden üretme becerisi (Bölüm 79), sistemin bir araştırma sorusuna dönüşmesini sağlar: hangi güvence yöntemi gerçek kaymada daha iyi çalışır, hangi kuantizasyon kafa katmanında kayıp üretmez? Bu soruların cevabı, bu kitabın en başında sorulan sorudur: bir sistemin doğru olduğunu nasıl bilirsin? Cevap, bu bölümün her tablosunda aynıdır: ölçersin, koşulu yazarsın, belirsizliğini söylersin.

::: mulakat
1. Bir gözetleme sisteminde takip kimlikleri sık sık değişiyor. Hangi üç veriye bakar ve sırayla ne yaparsın?
2. Kare bütçen 33 ms, sistemin p95 değeri 40 ms. Ölçümün tekrarlanabilir olduğunu nasıl kanıtlarsın?
3. int8 modelin mAP@0,5 kaybı küçük, mAP@[0,5:0,95] kaybı büyük. Bu, hangi kararı değiştirir?
4. Bir izleme sisteminde PSI yükseldi, ama mAP düşmedi. Bunu nasıl yorumlar ve ne yaparsın?
5. Güvence katmanı yanlış alarmı azalttı, ama kapsamayı düşürdü. Bu bir mühendislik kararı mı, bir ölçüm sorunu mu? Açıkla.
6. Bir model kartında "bilinen sınırlar" bölümü neden zorunludur ve bu bölümü yazmamanın bedeli nedir?
7. Bir ekip "modeli her gün yeniden eğitelim, en güncel hâli olsun" diyor. Yanıtın ne olur?
8. Bu bölümde hangi gereksinim en çok belirsizdi ve onu ölçülebilir hâle getirmek için ne yaptın?
:::
