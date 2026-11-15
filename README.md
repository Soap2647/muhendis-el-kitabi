<div align="center">

# 📘 Mühendis El Kitabı

**Bilgisayar mühendisliğinin temelinden makine öğrenmesi araştırmasına, 16 kısım ve 80 bölümlük Türkçe bir el kitabı.**

*A Turkish handbook for computer engineers in 80 chapters: from bits and C to compilers, operating systems, embedded systems, ML and deep learning. Written by directing a team of AI agents.*

[İçindekiler](#icindekiler) · [PDF indir](https://github.com/Soap2647/muhendis-el-kitabi/releases/latest) · [Nasıl yazıldı](#nasil-yazildi)

</div>

---

## 🎯 Amaç

Kitabın tek bir başarı ölçütü var: baştan sona okuyup alıştırmalarını yapan biri **hiçbir yapay zekâ aracı olmadan**

- whiteboard mülakatında bir problemi sıfırdan çözebilmeli,
- boş bir IDE'de çalışan kod yazabilmeli,
- gerçek bir projede hatayı kendi bulabilmeli,
- konuyu başkasına anlatabilmeli.

O yüzden her kavram "neden?" sorusuyla anlatılır. Çözümlü örnekler düşünme sürecini adım adım ve iz tablolarıyla gösterir, her bölümün sonunda alıştırmalar var. Kitaptaki kodlar, ölçümler ve grafikler gerçekten çalıştırılıp üretildi; ilgili dosyalar [`arsiv/kod/`](arsiv/kod/) ve [`engine/veri/`](engine/veri/) altında.

<a id="nasil-yazildi"></a>

## 🤖 Nasıl yazıldı

Bu kitap, yapay zekâ ajanlarını yöneterek yazıldı. Yazarlığın büyük kısmı ajanlara verilecek sözleşmeyi kurmak, çıktıyı denetlemek ve doğrulanmamış hiçbir şeyi içeri almamaktı.

| Adım | Kim | Ne |
|---|---|---|
| Sözleşme | İnsan + Opus | [`docs/MASTER_PROMPT.md`](docs/MASTER_PROMPT.md): kitabı sıfırdan yazdırabilecek, kendi kendine yeten yazar sözleşmesi |
| Yazım | Haiku yazar ajanları | Her bölüm, sözleşme ve [`docs/YAZAR_ORTAK.md`](docs/YAZAR_ORTAK.md) kurallarıyla |
| Denetim | Bölüm başına bir Haiku ajanı | 10 puanlık ölçüt: doğruluk, yapay zekâsız uygulanabilirlik, örnek kalitesi, alıştırma hacmi, kaynak dürüstlüğü, dizgi |
| Doğrulama | Opus | Bildirilen her hatayı kaynakla karşılaştırıp yanlış alarmları eledi |
| Onarım | Haiku düzelticiler | Doğrulanmış hatalar ve yeni zorunlu yapılar |
| Dizgi | ReportLab motoru | [`engine/`](engine/) ve [`build/`](build/): Markdown → PDF, otomatik yerleşim ve kod genişliği denetçileri ([`docs/PDF_DIZGI_KURALLARI.md`](docs/PDF_DIZGI_KURALLARI.md)) |

Sürecin dürüst bir ara raporu: [`docs/RAPOR_DENETIM_2026-10-18.md`](docs/RAPOR_DENETIM_2026-10-18.md).

## 🛠️ PDF'i kendin üret

```bash
pip install reportlab matplotlib numpy scipy pymupdf
# DejaVu fontlarını (DejaVuSans*, DejaVuSerif*, DejaVuSansMono*) fonts/ klasörüne koy
python build/make_bolum.py 1        # bolumler/bolum_01.md → pdf/
```

Diyagramlar `engine/diagrams_bNN.py` ile `gorseller/` altına üretilir.

## 📄 Lisans

MIT, bkz. [LICENSE](LICENSE). Kod Okuma bölümlerinde incelenen üçüncü taraf kaynak dosyalar (Linux, CPython, zlib, Go, CMSIS, STM32 HAL vb.) kendi lisanslarına tabi olduğu için bu repoya konmadı; metinde sürüm ve kaynağıyla anılırlar.

<a id="icindekiler"></a>

## 📑 İçindekiler

**Kısım I · Programlama Temelleri**

1. [Bilgisayar Nasıl Düşünür](bolumler/bolum_01.md)
2. [C Dili](bolumler/bolum_02.md)
3. [Python — C Bilenler İçin](bolumler/bolum_03.md)
4. [Terminal & Araçlar](bolumler/bolum_04.md)

**Kısım II · Problemi Çözmeyi Öğrenmek**

5. [Problemi Parçala](bolumler/bolum_05.md)
6. [Debugging Sanatı](bolumler/bolum_06.md)

**Kısım III · Veri Yapıları**

7. [Array & Linked List](bolumler/bolum_07.md)
8. [Stack & Queue](bolumler/bolum_08.md)
9. [Hash Table](bolumler/bolum_09.md)
10. [Tree](bolumler/bolum_10.md)
11. [Graph](bolumler/bolum_11.md)

**Kısım IV · Algoritmalar**

12. [Algoritma Analizi](bolumler/bolum_12.md)
13. [Sıralama](bolumler/bolum_13.md)
14. [Arama](bolumler/bolum_14.md)
15. [Recursion & Backtracking](bolumler/bolum_15.md)
16. [Dynamic Programming](bolumler/bolum_16.md)
17. [Graph Algoritmaları](bolumler/bolum_17.md)
18. [Greedy](bolumler/bolum_18.md)
19. [Divide & Conquer](bolumler/bolum_19.md)

**Kısım V · OOP & Yazılım Tasarımı**

20. [OOP Temelleri](bolumler/bolum_20.md)
21. [SOLID](bolumler/bolum_21.md)
22. [Design Patterns](bolumler/bolum_22.md)
23. [Clean Code](bolumler/bolum_23.md)

**Kısım VI · İşletim Sistemi & Mimari**

24. [CPU Mimarisi](bolumler/bolum_24.md)
25. [Bellek Hiyerarşisi](bolumler/bolum_25.md)
26. [Process & Thread](bolumler/bolum_26.md)
27. [Senkronizasyon](bolumler/bolum_27.md)
28. [File System & I/O](bolumler/bolum_28.md)

**Kısım VII · Ağ**

29. [OSI & TCP/IP](bolumler/bolum_29.md)
30. [HTTP, DNS, DHCP](bolumler/bolum_30.md)
31. [Socket Programming](bolumler/bolum_31.md)
32. [Güvenlik](bolumler/bolum_32.md)

**Kısım VIII · Veritabanı**

33. [İlişkisel Model](bolumler/bolum_33.md)
34. [SQL Derinlemesine](bolumler/bolum_34.md)
35. [NoSQL](bolumler/bolum_35.md)

**Kısım IX · Otomata & Derleme**

36. [Formal Diller](bolumler/bolum_36.md)
37. [Derleyici Nasıl Çalışır](bolumler/bolum_37.md)

**Kısım X · Yazılım Mühendisliği Pratiği**

38. [Git Derinlemesine](bolumler/bolum_38.md)
39. [Test Yazma](bolumler/bolum_39.md)
40. [API Tasarımı](bolumler/bolum_40.md)
41. [System Design](bolumler/bolum_41.md)
42. [Docker & Deployment](bolumler/bolum_42.md)

**Kısım XI · Gömülü Sistem**

43. [Bare-Metal C](bolumler/bolum_43.md)
44. [Kesme & Zamanlayıcı](bolumler/bolum_44.md)
45. [İletişim Protokolleri](bolumler/bolum_45.md)
46. [Edge AI & TinyML](bolumler/bolum_46.md)

**Kısım XII · Matematik**

47. [Ayrık Matematik](bolumler/bolum_47.md)
48. [Lineer Cebir](bolumler/bolum_48.md)
49. [Olasılık & İstatistik](bolumler/bolum_49.md)
50. [Optimizasyon](bolumler/bolum_50.md)
51. [Bilgi Teorisi](bolumler/bolum_51.md)

**Kısım XIII · Sinyal & Paralel**

52. [DSP Temelleri](bolumler/bolum_52.md)
53. [Paralel & Eşzamanlı Programlama](bolumler/bolum_53.md)

**Kısım XIV · Makine Öğrenmesi**

54. [ML'e Giriş & Pipeline](bolumler/bolum_54.md)
55. [ML için Kalkülüs & Otomatik Türev](bolumler/bolum_55.md)
56. [Veriyle Çalışmak](bolumler/bolum_56.md)
57. [Değerlendirme & Deney Tasarımı](bolumler/bolum_57.md)
58. [Doğrusal Modeller](bolumler/bolum_58.md)
59. [Ağaçlar & Ensemble](bolumler/bolum_59.md)
60. [SVM & Kernel Yöntemleri](bolumler/bolum_60.md)
61. [Denetimsiz Öğrenme](bolumler/bolum_61.md)
62. [Olasılıksal Modeller & Bayesçi ML](bolumler/bolum_62.md)

**Kısım XV · Derin Öğrenme**

63. [Sinir Ağı Sıfırdan](bolumler/bolum_63.md)
64. [Eğitimin Sanatı](bolumler/bolum_64.md)
65. [PyTorch Derinlemesine](bolumler/bolum_65.md)
66. [CNN & Bilgisayarlı Görü](bolumler/bolum_66.md)
67. [Nesne Tespiti, Segmentasyon & Takip](bolumler/bolum_67.md)
68. [Dizi Modelleri & Zaman Serisi](bolumler/bolum_68.md)
69. [Attention & Transformer](bolumler/bolum_69.md)
70. [NLP & Dil Modelleri](bolumler/bolum_70.md)
71. [LLM Sistemleri](bolumler/bolum_71.md)
72. [Üretken Modeller](bolumler/bolum_72.md)
73. [Temsil Öğrenme & Self-Supervised](bolumler/bolum_73.md)
74. [Pekiştirmeli Öğrenme](bolumler/bolum_74.md)

**Kısım XVI · ML Mühendisliği & Araştırma**

75. [Verimli Çıkarım & Edge](bolumler/bolum_75.md)
76. [GPU Programlama & Dağıtık Eğitim](bolumler/bolum_76.md)
77. [MLOps](bolumler/bolum_77.md)
78. [Güvenilir & Güvenli AI](bolumler/bolum_78.md)
79. [Makale Okuma & Araştırma Yöntemi](bolumler/bolum_79.md)
80. [Bitirme: Uçtan Uca Sistem](bolumler/bolum_80.md)
