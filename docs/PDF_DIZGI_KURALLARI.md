# PDF dizgi kuralları (yeniden kullanılabilir prompt)

Aşağıdaki metni başka bir PDF işinde yapay zekâya olduğu gibi verebilirsin.
Araçtan bağımsızdır (ReportLab, LaTeX, Typst, Word, HTML→PDF).

---

Bu belgeyi profesyonel bir yayınevi dizgisi kalitesinde bir PDF olarak hazırla.
Dizgi kusurlarını tek tek sayfalarda yamalama; her kuralı dizgi motoruna/şablona
genel kural olarak yaz ki bütün belgeye aynı anda uygulansın. Bitirdiğinde
aşağıdaki "Denetim" bölümündeki kontrolleri çalıştır ve sonuçlarını raporla.

## 1. Sayfa ve yazı
- A4, aynalı kenar boşlukları (iç kenar dış kenardan geniş). Üst bilgi ve sayfa
  numarası metin alanının dışında kalır; hiçbir metin, şekil ya da tablo kenar
  boşluğuna veya üst/alt bilgi bandına taşmaz.
- Gövde metni 11–12 pt serif, satır aralığı ~1,35; başlıklar sans. Sayfa doldurmak
  için punto küçültme yok.
- Tek vurgu rengi (ör. koyu bordo); renkli zemin, gölge, yuvarlak köşe yok.
- Gövde metni iki yana yaslı ve dile uygun hecelemeli (Türkçe heceleme). Başlıklar,
  tablo hücreleri ve şekil açıklamaları hecelenmez.

## 2. Başlıklar asla yalnız kalmaz
- Her başlık, ardından gelen ilk içerik bloğuyla (paragraf, liste, tablo, şekil,
  kod) aynı sayfada başlar. Sayfa dibinde tek başına kalan başlık yasaktır.
- Başlıktan önce sayfada asgari boş alan şartı koy; yer yoksa başlık yeni sayfada
  başlasın. Örnek değerler: ana bölüm başlığı ~9,5 cm, alt başlık ~6,8 cm,
  üçüncü düzey ~5 cm, kalın etiket satırı ("Çözüm:" gibi) ~4 cm.
- Art arda gelen başlıklar (bölüm başlığı + hemen altındaki alt başlık) zincir
  gibi birlikte tutulur.

## 3. Tanıtım cümlesi işaret ettiği şeyden ayrılmaz
- "Aşağıdaki tablo…", "Şekil 3.2…", "Şu kod…" gibi bir bloğu tanıtan paragraf, o
  bloğun en azından başlangıcıyla aynı sayfada durur.
- Ama bu kural sayfayı boşaltmamalı: blok uzunsa bütün halinde ileri itilmez;
  tanıtım paragrafı + bloğun ilk ~6 satırı sığıyorsa orada başlar, devamı sonraki
  sayfaya geçer (bkz. 4–6).

## 4. Kod ve terminal çıktısı blokları
- 12 satıra kadar olan bloklar bölünmez.
- Daha uzun bloklar sayfa sonunda bölünebilir, fakat her parçada en az 6 satır
  kalır (tek satırlık "yetim" kod parçası olmaz).
- Kod satırı en fazla ~70 karakter (terminal çıktısında ~74); uzun satır kenardan
  taşmaz, kaynakta anlamlı yerden bölünür.
- Satır içi kısa kod ifadeleri (`x = 1` gibi, ≤18 karakter) satır sonunda ikiye
  bölünmez.

## 5. Tablolar
- Sütun genişliği, o sütundaki EN UZUN KELİMENİN tek satıra sığacağı kadar olur;
  hiçbir kelime harf ortasından ("Sınıflan/dırma", "Doğrulu/k") bölünmez.
  Kalan genişlik, içerik uzunluğuna göre sütunlara dağıtılır.
- Tablo yine de sığmazsa sırasıyla: yazıyı %90, sonra %80'e küçült; uzun dosya
  yollarını yalnız "/" noktalarından böl; heceleme (tire ile) yalnızca son çare
  ve bu durumda uyarı ver.
- 10 satıra kadar tablolar bölünmez; daha uzunlar sayfa sonunda bölünür ve başlık
  satırı yeni sayfada tekrarlanır.
- Sade stil: dikey çizgi ve zebra yok; üstte ve altta kalın, başlık altında ince
  çizgi.

## 6. Şekiller
- Şekil ve açıklaması ("Şekil N.M: …") her zaman aynı sayfada; açıklama sayfa
  başında yetim kalmaz.
- Şekil (tanıtım paragrafıyla birlikte) sayfaya sığmıyorsa önce şekli en fazla
  %35 küçültmeyi dene (en az %65 boyut); sığarsa bu sayfada bırak. Ancak o da
  yetmezse yeni sayfaya geç.
- Şekil numaraları metindeki görünme sırasına göre 1..n gider; metinde atfı
  olmayan şekil olmaz. Şekil içi yazılar belgenin dilinde ve doğru karakterlerle
  (Türkçe için ç, ğ, ı, ş… ASCII'ye çevrilmez).

## 7. Boş sayfa ve dağınık görünüm yasak
- Bölüm sonu dışında hiçbir sayfanın yarısından fazlası boş kalmaz. Boşluk
  oluşuyorsa sebebi bir bloğun bütün halinde ileri itilmesidir; çözüm, o bloğu
  bölünebilir yapmak ya da şekli küçültmektir (4–6), sayfaya dolgu eklemek değil.
- Paragraflar sayfa sonunda tek satır bırakarak bölünmez (en az 2 satır altta,
  2 satır üstte: widow/orphan kontrolü).
- Ardışık boşluklar birikmez: blok sonu boşlukları sayfa başında yutulur, boş
  bir "aralık" yüzünden yeni sayfa açılmaz.

## 8. Matematik ve semboller
- Düz metindeki alt/üst indisler gerçek alt/üst indis olarak basılır: x_{t−1},
  g_k, e^{z}, 2^10 ham karakterlerle görünmez. LaTeX/markdown işareti (**, ##,
  `, _{, ^{, \frac, &amp;) basılı metne sızmaz.
- Yazı tipinde olmayan semboller (⊙, ≤, ∑ …) için yedek yazı tipi kullan; PDF'te
  boş kutu (□) ya da � olmaz.

## 9. Denetim (bitince mutlaka çalıştır ve raporla)
PDF'i bir PDF kütüphanesiyle (ör. PyMuPDF) sayfa sayfa tara ve şunları say:
1. Kenar/üst bilgi/alt bilgi bandına taşan metin veya görsel.
2. Sayfa dibinde tek başına kalan başlık.
3. Yarısından fazlası boş sayfa (bölüm sonu hariç) ve her biri için sebebi.
4. Kelime ortasından kırılmış satırlar (satır harfle bitiyor, sonraki küçük harfle
   başlıyor ve birleşimleri sözlükte bir kelime).
5. Basılı metne sızan biçim işaretleri (**, ##, `, _{, ^{, &amp;, \frac…).
6. Sayfa başında yetim kalmış şekil açıklaması.
7. Uzun kod satırı (>70) ve sığmayıp hecelenen tablo sayısı.
8. Şekil sırası/atıf tutarlılığı.
Ardından en az 5 sayfayı (tablo, şekil, kod ve uzun liste içerenlerden) görüntü
olarak render edip gözle kontrol et. Her kusur türünün sayısını, kalanların
sebebini ve neden kabul edilebilir olduğunu yaz. Sorun bulursan sayfayı tek tek
düzeltme; ilgili kuralı motorda düzelt ve belgeyi baştan yeniden bas.
