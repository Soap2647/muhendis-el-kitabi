# -*- coding: utf-8 -*-
import re

p = "C:/Users/merty/AppData/Local/Temp/b58/taslak.md"
s = open(p, encoding="utf-8").read()
R = [
    ("matrisinde `i`. satır `[1, xᵢᵀ]`dir.",
     "matrisinde i'inci satır `[1, xᵢᵀ]`'dir."),
    ("Scikit-learn'ün `LinearRegression` nesnesi, düşük rank durumunda bu yolu kullanır.",
     "Scikit-learn'ün `LinearRegression` nesnesi, SVD tabanlı `scipy.linalg.lstsq` çözücüsünü kullanır."),
    ("Bölüm 48.11'deki polinom uydurma örneğinin matrisini (Vandermonde)",
     "Bölüm 48'deki polinom uydurma örneğinin matrisini (Vandermonde)"),
    ("Sonuç çarpıcıdır. OLS katsayılarının",
     "Sonuç Şekil 58.3'te çarpıcıdır. OLS katsayılarının"),
    ("Yüz kere tekrarlanmış deneyde",
     "300 farklı tohumla tekrarlanmış deneyde"),
    ("Diyabet verisinin öznitelikleri makul ölçüde bağımsızdır (aşağıda VIF'lerde göreceğiz, `s1` hariç).",
     "Diyabet verisinde bazı öznitelikler birbirine bağlıdır (aşağıdaki VIF tablosu), ama bu bağlılık test tahminini çok bozmadığı için Ridge'in faydası sınırlı kalır."),
    ("Bu tablo, diyabet verisinin neden Ridge'den fazla yararlanmadığını da açıklar: en çok korelasyonlu öznitelikler (`s1`, `s2`) zaten katsayı sıralamasını bozmaktadır, ama test tahminini çok etkilemezler.",
     "Diyabet verisinde `s1` ve `s2` birbirine bağlıdır; ama bu bağlılık test tahminini ciddi biçimde bozmadığı için Ridge'in test kümesinde kazandırmaması şaşırtıcı değildir."),
    ("Bu değerler, genellikle 10 üzerinin problemli kabul edildiği eşiğin üstündedir.",
     "Genel bir pratik kurala göre 10'un üzerindeki VIF değerleri sorunlu sayılır (genel bilgi)."),
    ("Şekil 58.4 sol tarafta bu eşiği göstermek için L2 ve L1 kısıtlarını yan yana koyuyor; Şekil 58.5 ise Ridge ve Lasso yollarını çiziyor.",
     "Şekil 58.4 kısıt geometrisini, Şekil 58.5 ise Ridge ve Lasso yollarını gösteriyor."),
    ("Kendi koordinat inişimiz sklearn ile `10⁻¹⁰`'dan küçük farkla uyuşur. Elastic Net için fark `10⁻¹¹` mertebesindedir.",
     "Kendi Lasso koordinat inişimiz sklearn ile `10⁻⁹`'dan küçük farkla uyuşur; Elastic Net için fark `10⁻¹¹` mertebesindedir."),
    ("Bu kuralın seçimi nasıl etkilediğini Bölüm 57'de deneyeceğiz.",
     "Bu kuralın ayrıntıları Bölüm 57'de ele alınır."),
    ("Odds oranı bir olasılık oranı değildir. `p` 0,01'den 0,02'ye çıkarken odds 2 katından fazla artmaz; ama odds oranı 2 olabilir. Bu fark, nadir olaylarda sık yapılan bir hatadır.",
     "Odds oranı bir olasılık oranı değildir. Olasılık 0,50'den 0,60'a çıktığında odds 1'den 1,5'e çıkar: olasılık 1,2 kat, odds 1,5 kat artmıştır. Olasılık 0,01'den 0,02'ye çıktığında ise odds yaklaşık 2 kat artar. Bu fark sık yapılan bir hatadır."),
    ("Noktalar, Örnek 58.3'teki w = 0,8 ve b = −1,2 modeli için olasılıkları gösterir.",
     "Noktalar, Çözümlü Örnek 3'teki w = 0,8 ve b = −1,2 modeli için olasılıkları gösterir."),
    ("Sklearn ile katsayı farkı `1,1·10⁻⁶`dır; bu sklearn'ün kendi çıkış toleransının (1e-12 yerine 1e-6 mertebesinde) sonucudur.",
     "Sklearn ile katsayı farkı `1,1·10⁻⁶`dır. Bu fark, sklearn'ün L-BFGS çözücüsünün kendi durma ölçütünden kaynaklanabilir; iki yöntem aynı amaç fonksiyonunu çözer."),
    ("örnek başına kaybın `wᵢ` ile çarpılmasıdır; gradyanda `Aᵀ(w ∘ (p − y))/n` olur.",
     "örnek başına kaybın `sᵢ` ağırlığı ile çarpılmasıdır; gradyanda `Aᵀ(s ∘ (p − y))/n` olur."),
    ("Sklearn'ün `balanced` formülü `wₖ = n/(K·nₖ)` ile ağırlıklandırılmış model",
     "Sklearn'ün `balanced` formülü `s = n/(K·n_sınıf)` ile ağırlıklandırılmış model"),
    ("Ondokuz kuş biçimli dijital rakam için, 64 piksel ve 10 sınıf ile bu `650` parametre demektir.",
     "Dijital rakam veri kümesinde (64 piksel, 10 sınıf) bu `650` parametre demektir."),
    ("(oran oranı, rate ratio)", "(hız oranı, rate ratio)"),
    ("kesikli çizgi gerçek doğrudur.", "noktalı çizgi gerçek doğrudur."),
    ("RBF ailesinde en iyi doğrulama değeri `rbf4` (`0,0312`) ile `poly3` (`0,0308`) arasında kalır; yani bu tek bölmede iki aile benzer sonuç verir.",
     "RBF ailesinde en iyi doğrulama değeri `rbf4`'te (`0,0312`) çıktı; `poly3` (`0,0308`) ile birlikte bu tek bölmede iki aile benzer sonuç verir."),
    ("Bölüm 55'te aynı yarım ay veri kümesinde gizli katmanlı",
     "Bölüm 55'te benzer bir iki yarım ay kümesinde gizli katmanlı"),
    ("Bu bölümdeki her başarı iddiası ayrı bir test kümesinde ölçülmüştür. Her deneyde bir baseline vardır ve eğitim skoru, test skorundan ayrı etiketlenmiştir.",
     "Bu bölümdeki başarı iddialarının çoğu ayrı bir test kümesinde ve bir baseline ile karşılaştırılarak ölçülmüştür; eğitim skorları test skorundan ayrı etiketlenmiştir."),
    ("neden \"tank\" dediğini", "bir tespiti neden yaptığını"),
    ("Bu, Bölüm 49'da hatırlatılan MLE–MAP bağlantısının doğrusal regresyondaki karşılığıdır.",
     "Bu, Bölüm 49.8'deki en büyük olabilirlik ilkesinin doğrusal regresyondaki karşılığıdır."),
    ("(Bölüm 50.3'teki sonlu fark ilkesiyle uyumlu olarak burada yalnızca sıfır kontrolü yapıyoruz)",
     "(Gradyanın doğruluğunu burada yalnızca OLS noktasında sıfıra yakınlık ile denetliyoruz)"),
    ("Bu bölümde iki gerçek kaynak kesiti okuyacağız.",
     "Bu bölümde üç gerçek kaynak kesiti okuyacağız."),
    ("Kesit birebir kopyadır; satır 228 sayfa genişliğine sığması için `return` ifadesi değiştirilmeden tek satırda tutulmuştur.",
     "Kesit birebir kopyadır."),
    ("(`sklearn/linear_model/_cd_fast.pyx`, satır 332–343)",
     "(`sklearn/linear_model/_cd_fast.pyx`, satır 330–343)"),
    ("Dikkat: bir adım yalnızca `0,35` olasılığı `0,33`e yakın bir yere kaydırdı; yani gerçek öğrenme için birçok adım gerekir (Bölüm 50.10).",
     "Dikkat: bir adım, doğru sınıfın olasılığını `0,33`ten yalnızca `0,35`e çıkardı; gerçek öğrenme için birçok adım gerekir (Bölüm 50.10)."),
    ("Bu bölümdeki altı modeli (OLS, Ridge, Lasso, Elastic Net, lojistik regresyon, softmax regresyonu ve Poisson regresyonu)",
     "Bu bölümdeki yedi modeli (OLS, Ridge, Lasso, Elastic Net, lojistik regresyon, softmax regresyonu ve Poisson regresyonu)"),
]
hatalar = 0
for a, b in R:
    n = s.count(a)
    if n != 1:
        hatalar += 1
        print("UYARI count=%d: %s" % (n, a[:80]))
    s = s.replace(a, b)

s = re.sub(r'Bu, Bölüm 56\'daki "çok sınıflı kodlama" kararlarıyla birlikte düşünülmelidir\.',
           "Bu sayı, Bölüm 56'daki kategorik kodlama kararlarıyla birlikte düşünülmelidir.", s)

marker = "@@CIKTI|b58_06_coklu.py@@\n"
assert s.count(marker) == 1, s.count(marker)
s = s.replace(marker, marker + "\n@@SEKIL|b58_coklu_dogrusallik.png|Çoklu doğrusallık: 300 veri kümesinde OLS katsayıları (sol) ile Ridge katsayıları (sağ).@@\n")

ek = open("C:/Users/merty/AppData/Local/Temp/b58/ek.md", encoding="utf-8").read()
anchor = "## Kod Okuma Egzersizi"
assert s.count(anchor) == 1
s = s.replace(anchor, ek + anchor)
open(p, "w", encoding="utf-8").write(s)
print("uyari sayisi:", hatalar, "| satir:", s.count("\n"))
