# Haiku yazarları için ortak çalışma kuralları

Bu dosya, `docs/MASTER_PROMPT.md`'ye EK olarak, önceki bölümlerin Opus denetiminden
çıkan dersleri toplar. İkisi çelişirse MASTER_PROMPT kazanır.

## Süreç
1. Önce `docs/MASTER_PROMPT.md`'yi (tamamı), sonra görevde adı geçen önceki bölümleri oku.
   Önceki bölümlerde anlatılanı TEKRAR ANLATMA: kısa hatırlat, "Bölüm N'de" diye atıf yap, üstüne kur.
   Önceki bölümlerin "Bölüm X'te" diye verdiği sözleri `grep "Bölüm X"` ile bul ve tut.
2. Kodları `C:\Users\merty\AppData\Local\Temp\bNN\` altında dosya olarak yaz, çalıştır,
   md'ye dosyadan otomatik göm (birleştirici betik). Kitapta çıktısı gösterilen HER programın
   tam kodu kitapta olmalı.
3. Kanonik kaynak `bolumler/bolum_NN.md`'dir. Birleştirici kullanıyorsan, son md'yi kontrol et:
   terminal bloklarına sahte boş satır girmesin (programın gerçek çıktısıyla birebir olmalı;
   Windows'ta `\r\n` → çift satır sonu tuzağı).
4. Bağlamın daralırsa md'yi parça parça yaz. İşi yarıda bırakma; md yazılmadan rapor verme.

## İçerik
- Uzunluk sınırı YOK; ölçüt öğretim değeri ve okuru sağlam bir mühendis yapmak. Dolgu/tekrar yok.
- Her araç/kütüphane/derleyici/protokol davranışı iddiasını çalıştırarak ya da gerçek kaynaktan
  doğrula; doğrulayamadığını metinde "genel bilgi"/"bilinen sonuç" diye işaretle.
- Algoritma/kodu küçük rastgele girdilerde kaba kuvvete/kütüphaneye/başka gerçeklemeye karşı
  test et (sabit tohum) ve testi metinde göster. Sınır durumlarını gerçekten dene.
- Kodun yanlış sonuç verdiği bir durum varsa metinde açıkça söyle (iyi bir öğretim fırsatıdır).
- Teoride tanımlamadığın sembol/kavramı örnekte kullanma.
- **ML bölümleri (54+):** Her başarı/doğruluk iddiası AYRI TUTULMUŞ veride (test/doğrulama) ölçülür; eğitim skoru
  verilirse açıkça "eğitim doğruluğu" diye etiketlenir ve yanında test skoru da verilir. Baseline'ı da göster.
  Tek koşu yerine mümkünse birden çok tohum + ortalama ± sapma. (Bölüm 54/57 disiplini.)
- TAM KOD: tablo/şekil/çıktısı verilen HER deney betiği kitapta TAM hâliyle (kesit + "tamamı arşivde" YASAK). Uzunluk sorun değil.
- Kod Okuma: kaynağı GERÇEKTEN indir (curl ile raw.githubusercontent.com, belirli etiket/sürüm),
  birebir kopyala; kısalttıysan/böldüysen metinde belirt. Uydurma alıntı YASAK.
- `::: mulakat` kutusunda her soru ayrı satırda `1. ...` biçiminde.

## Şekiller
- `engine/diagrams_bNN.py`, dosya başında `# -*- coding: utf-8 -*-`.
- Şekil yazıları TÜRKÇE KARAKTERLİ ("düğüm", "aşama", "ölçüm"); ASCII'leştirilmiş Türkçe YASAK.
- Ölçüm verisi okuyan şekil veriyi `engine/veri/bNN_*.csv`'den okur; Temp'e bağımlı şekil YASAK.
- Çok panelli şekillerde 1×3 yerine 2×2 tercih et (sayfada okunur kalsın); kenar etiketleri
  çakışmasın, kenarlar alakasız düğümlerin üstünden geçmesin.
- Her PNG'yi Read ile aç ve gözle kontrol et.
- Şekil numaraları METİNDEKİ GÖRÜNÜŞ SIRASIYLA 1..n olmalı; her üretilen şekil metne eklenmeli (check_figures.py).

## Teknik
- C: `wsl gcc -O2 -Wall -Wextra -std=c11` + ayrıca `-fsanitize=address,undefined`.
  C++: `wsl g++ -O2 -Wall -Wextra -std=c++17` (+ sanitizer). Python: `python` (3.12.10).
- Git Bash'ten WSL çağrısında yol dönüşümü sorunu: `MSYS_NO_PATHCONV=1`. Konsol: `PYTHONIOENCODING=utf-8`.
- **GPU:** NVIDIA GeForce RTX 3060 Laptop (6 GB, compute 8.6, sürücü 616.64); Windows Python'da PyTorch 2.6.0+cu124,
  `torch.cuda.is_available() == True`. Derin öğrenme bölümlerinde GPU ölçümleri gerçekten yapılır; 6 GB bellek sınırına
  uygun model/batch seç. GPU paylaşımlıdır (paralel yazarlar): SÜRE ölçümünden önce `nvidia-smi --query-gpu=utilization.gpu --format=csv`
  ile kartın boşta olduğunu doğrula; değilse birkaç dakika sonra tekrar dene; ölçüm koşullarını metinde yaz. ARM araç zinciri: C:\ST\STM32CubeIDE_1.19.0\STM32CubeIDE\plugins\com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.13.3.rel1.win32_1.0.0.202411081344\tools\bin\arm-none-eabi-gcc.exe (13.3); Unicorn kurulu.
- Kod satırı ≤70, terminal satırı ≤74 karakter. Kod/terminal/tablo/şekilden hemen önce tanıtım paragrafı.

## Derle ve denetle
```
python build\make_bolum.py NN
python build\check_layout.py        (TEMİZ)
python build\check_code_width.py    (0)
python build\contact.py NN          (build\bNN_contact.png — Read ile aç)
python build\check_figures.py       (şekil sırası/atıf/dosya — TEMİZ olmalı)
```
Şekilli sayfalardan en az 5'ini ayrıca aç.

## Rapor
Türkçe: satır/sayfa, şekiller, örnekler ve zorlukları, Kod Okuma kaynağı (yol+sürüm, doğrulama),
testler ve ölçümler, kontrol çıktıları, emin olmadığın iddiaların DÜRÜST listesi.
