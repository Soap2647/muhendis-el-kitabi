%% kisim_no: XVI
%% kisim_ad: ML Mühendisliği & Araştırma
%% bolum_no: 77
%% baslik: MLOps

## Giriş: Model bir kez eğitilir, sistem her gün çalışır

Bölüm 54'te ML iş akışını kurduk, Bölüm 57'de modelin iyi olup olmadığını ölçmeyi öğrendik, Bölüm 65'te eğitimi tekrarlanabilir hâle getirdik. Bunların hepsi modelin laboratuvarda doğru çalışmasıyla ilgiliydi. Asıl zorluk model bir kullanıcıya servis edildikten sonra başlar. Veri değişir, sensör yaşlanır, yeni eğitilen model eskisinden kötü çıkar ve bunu kimse fark etmez, çünkü hata mesajı yoktur. Model sessizce bozulur.

MLOps, bu sessiz bozulmayı önlemek için geliştirilmiş mühendislik disiplinidir. Adı DevOps'tan gelir: kodu sürümlemek, otomatik test etmek, otomatik dağıtmak ve çalışan sistemi izlemek. ML'de bu zincire iki şey daha girer: veri ve model. Kod bir kez yazılır ve kendiliğinden değişmez; veri ise dünya değiştikçe değişir. Bu fark, yazılım mühendisliğinde işe yarayan alışkanlıkların ML'de neden yetmediğini açıklar.

Bölüm 42'de "bende çalışıyor" sorununu Docker ile çözmeyi, Bölüm 38'de değişikliklerin izini Git ile sürmeyi, Bölüm 39'da testle doğruluğu denetlemeyi gördük. Bu bölümde aynı disiplini veriye, deneylere ve modellere taşıyacağız. Kendi küçük araçlarımızı sıfırdan yazacağız: içerik-adresli bir veri deposu, SQLite tabanlı bir deney takipçisi, bir model kayıt defteri, bir kalite kapısı, bir kayma izleyicisi ve yeniden eğitim politikalarını karşılaştıran bir simülatör. Gerçek araçlar (DVC, MLflow, Weights & Biases, Kubeflow, Feast) kavram olarak anlatılacak ve çalıştırılmadı diye işaretlenecek.

Savunma sanayiinde bu konu doğrudan önemlidir. Bir İHA'nın görüntü tespit modeli, bir yıl sonra bir kaza incelemesinde hangi veriyle, hangi kod sürümüyle ve hangi eşikle üretildiğini gösterebilmelidir. Bu izlenebilirlik olmadan model bir kara kutudur. Bölüm 78'de sertifikasyon ve güvenilirlik konusunu açacağız; bu bölüm o konunun altyapısıdır.

::: not
Bu bölümün tüm kodu Windows 11 üzerinde Python 3.12.10 ile çalıştırıldı; scikit-learn 1.8.0, pandas 2.3.3, scipy 1.17.1 ve pytest 9.0.3 kullanıldı. GPU kullanılmadı, her deney tek bir işlemci üzerinde çalışır ve en uzun betik bir dakikanın altında biter. Stokastik deneylerin her biri üç tohumla (11, 22, 33) tekrarlandı ve sonuçların yanında dağılım verildi. Bu makinede MLflow 3.12 kurulu, DVC ise kurulu değil. Bölümün ruhu gereği araçları sıfırdan yazdık; gerçek araçların hiçbiri bu bölümde çalıştırılmadı.
:::

## 77.1 ML sistemleri yazılımdan neden farklı

Yazılım sistemini kod olarak düşünebiliriz: kaynak dosyalar derlenir, testler geçer, sistem çalışır. ML sisteminde en az üç bileşen vardır: kod, veri ve model. Model, eğitim verisi ve kodun birlikte ürettiği bir çıktıdır. Üçünden biri değiştiğinde sistemin davranışı değişir, kod hiç değişmemiş olsa bile.

Sculley ve arkadaşları 2015'te yayımladıkları "Hidden Technical Debt in Machine Learning Systems" başlıklı makalede bu durumu "gizli teknik borç" diye adlandırdı (genel bilgi; makaleyi bu bölüm için yeniden okumadık, fikri aktarıyoruz). Makalenin ana fikri şudur: bir ML sisteminde modelin kodu tüm sistemin çok küçük bir parçasıdır. Geri kalanı veri toplama, veri doğrulama, özellik çıkarma, süreç yönetimi, altyapı, izleme ve servistir. Şekil 77.1 bu oranı çizer.

![Şekil 77.1: ML sisteminde küçük bir model kodu ve çevresindeki altyapı](gorseller/b77_teknik_borc.png)

Bu borcun tipik biçimleri birbirine bağlıdır. Birincisi **sınır erozyonudur**: girdi özelliklerinden biri değiştiğinde diğer tüm ağırlıklar da etkilenir, çünkü model özellikleri birlikte öğrenir. Makale buna "değişiklik her şeyi değiştirir" (CACE) der (genel bilgi). İkincisi **veri bağımlılığıdır**: bir sensörün ölçü birimi değişirse hiçbir hata alınmaz, model yalnızca yanlış sayılarla çalışır. Üçüncüsü **geri besleme döngüsüdür**: modelin kendi tahminleri bir sonraki eğitim verisine girerse model kendi önyargısını büyütür. Dördüncüsü **boru hattı karmaşasıdır**: onlarca betik, bir sonraki betiğin hangi dosyayı beklediğini bilmeden çalışır.

Bunların pratik sonucu şudur: model kodunun ne kadar temiz olduğu sistemin sağlığını belirlemez. Bir İHA görüntü modelinin eğitim betiği 200 satır olabilir. Ama o betiği çevreleyen etiketleme, veri sürümleme, doğrulama ve izleme sistemi binlerce satır ve çok daha fazla iş demektir. Bölüm 54.12'de dağılım kaymasını bir uyarı olarak gördük; bu bölümde o uyarıyı çalışan bir sisteme dönüştüreceğiz.

## 77.2 Yaşam döngüsü ve olgunluk düzeyleri

ML bir kez yapılıp bırakılan bir iş değildir; bir döngüdür. Problem tanımlanır (Bölüm 54.4), veri toplanır ve temizlenir (Bölüm 56), model eğitilir (Bölüm 65), değerlendirilir (Bölüm 57), dağıtılır (Bölüm 71 ve 75) ve izlenir. İzleme sonucu, veriyi ya da problem tanımını yeniden gözden geçirmeye geri döner. Şekil 77.2 bu döngüyü gösterir.

![Şekil 77.2: ML yaşam döngüsü; izleme, yeni veri ve yeniden eğitimle başa döner](gorseller/b77_yasam_dongusu.png)

Döngünün her adımı otomasyon gerektirmez, ama her adımın kaydının tutulması gerekir. Olgunluk düzeyleri, bir ekibin bu kayıtları ve otomasyonu ne kadar ileri taşıdığını anlatır. Aşağıdaki sınıflandırma Google'ın MLOps dokümanlarında geçen düzeylerin sade bir özetidir (genel bilgi; kaynağı bu makinede doğrulamadık, yalnızca fikri aktarıyoruz).

| Düzey | Ne yapılır | Tipik sorun |
|---|---|---|
| 0 | Eğitim ve dağıtım elle yapılır; kod bir defter dosyasında durur | Sonuç yeniden üretilemez |
| 1 | Eğitim betiklenir; deneyler kaydedilmez | Üretimdeki modelin hangi deneyden geldiği bilinmez |
| 2 | Kod ve model için CI/CD vardır; kalite kapısı çalışır | Veri ve kayma hâlâ elle izlenir |
| 3 | Yeniden eğitim tetiklenir; kayıt defteri, izleme ve geri alma vardır | Maliyet, sorumluluk ve uyum yönetilmesi gerekir |

Bu bölümde düzey 1'den düzey 3'e giden araçların her birini küçük bir biçimde kuracağız. Hiçbiri endüstriyel ölçekte değildir; amaç her aracın hangi sorunu çözdüğünü kodla görmektir.

## 77.3 Tekrarlanabilirlik: kod, veri, ortam ve tohum

Bir sonucu yeniden üretmek için dört şeyi bilmen gerekir. Birincisi **kod sürümüdür**: hangi commit çalıştırıldı (Bölüm 4.7 ve 38'deki Git bilgisi). İkincisi **veri sürümüdür**: hangi dosya, hangi içerik. Üçüncüsü **ortamdır**: Python sürümü, kütüphanelerin sürümleri, işletim sistemi. Dördüncüsü **rastgeleliktir**: bölme, başlangıç ağırlıkları ve artırma gibi adımların tohumu. Bölüm 65.14'te tohumun tek başına yetmediğini, GPU'da bazı işlemlerin deterministik olmadığını görmüştük. Bu dört bilginin üçü kaydedilmemişse sonuç yeniden üretilemez; dördü de kaydedilmemişse sonuç sadece bir söylentidir.

Ortamı kaydetmenin en basit yolu, kullandığın her paketin sürümünü bir dosyaya yazmaktır. Gerçek projelerde bu iş `pip freeze` ve hash'li bir kilit dosyasıyla yapılır (genel bilgi). Aşağıdaki betik, bu bölümde kullanılan paketlerin sürümlerini `requirements.lock` dosyasına yazar ve tüm satırların SHA-256 özetini parmak izi olarak basar. İki makinede parmak izi aynıysa paket sürümleri de aynıdır.

```python
# -*- coding: utf-8 -*-
"""Ortam kaydi: tekrarlanabilirlik icin surumleri dondur."""
import hashlib
import platform
import sys
from importlib import metadata

PAKETLER = ["numpy", "pandas", "scikit-learn", "scipy", "pytest"]


def ortam_satirlari():
    satirlar = ["python==" + platform.python_version()]
    for paket in PAKETLER:
        satirlar.append("%s==%s" % (paket, metadata.version(paket)))
    return satirlar


if __name__ == "__main__":
    metin = "\n".join(ortam_satirlari()) + "\n"
    with open("requirements.lock", "w", encoding="utf-8") as f:
        f.write(metin)
    print(metin, end="")
    ozet = hashlib.sha256(metin.encode()).hexdigest()
    print("ortam parmak izi:", ozet[:16])
    print("platform:", platform.system(), "|", sys.platform)
```

Betiği çalıştırdığında şu çıktıyı alırsın:

```term
$ python b77_ortam.py
python==3.12.10
numpy==2.3.5
pandas==2.3.3
scikit-learn==1.8.0
scipy==1.17.1
pytest==9.0.3
ortam parmak izi: 5b7316389d17d2de
platform: Windows | win32
```

Parmak izi `5b7316389d17d2de` bu makinedeki ortama özgüdür. Bir arkadaşının makinesinde farklı bir değer çıkarsa sonuçların birebir tutmayacağını baştan biliriz; bu bir hata değil, bir bilgidir. Tohum ve kod sürümü ile birlikte bu parmak izi, bir deneyin "ortam bilgisini" oluşturur ve deney takipçisine yazılır (77.5).

## 77.4 Veri versiyonlama: içerik-adresli depolama

Veriyi sürümlemek Git'i büyük dosyalara uygulamak gibi görünür, ama işe yaramaz. Git dosyaların her sürümünü tam olarak saklar; birkaç gigabaytlık bir görüntü kümesi her değişiklikte depoyu şişirir. Daha önemli sorun, dosya adının içeriği göstermemesidir. "telemetri.csv" dün ve bugün tamamen farklı içerik olabilir ve isim aynı kalır.

Çözüm **içerik-adresli depolamadır**. Dosyanın adı yerine içeriğinin özetini (SHA-256) adres olarak kullanırsın. Bölüm 9'da hash fonksiyonunun bir anahtarı sabit uzunlukta bir sayıya dönüştürdüğünü gördük; burada anahtar dosyanın kendisidir. Aynı içerik iki kez gelirse aynı adrese düşer ve bir kez saklanır. İçerik bir bayt değişirse özet tamamen değişir ve yeni bir nesne oluşur. Git'in kendi nesne deposu da bu fikre dayanır: her blob, tree ve commit içeriğinin özetiyle adreslenir (Bölüm 38.1).

Şekil 77.3 akışı gösterir. Dosya depoya kopyalanır; Git'e yalnızca küçük bir işaretçi dosyası (`.veri`) girer. İşaretçi dosyanın yolunu, özetini ve boyutunu tutar. Gerçek DVC aynı mantığı kullanır (kavram olarak; DVC bu makinede kurulu değil ve çalıştırılmadı).

![Şekil 77.3: İçerik-adresli depoda dosya özetle adreslenir, Git'e yalnızca işaretçi girer](gorseller/b77_icerik_adresli.png)

Aşağıdaki küçük depo üç işlemi yapar: dosyayı ekler, özetini hesaplar ve işaretçi yazar; dosyayı geri yüklerken özeti yeniden hesaplar; depodaki nesne bozulmuşsa bunu fark eder. Önce özet ve kopya kısmını okuyalım.

```python
# -*- coding: utf-8 -*-
"""Icerik-adresli veri deposu: DVC'nin kucuk bir benzeri.

Dosya adina degil icerigin SHA-256 ozetine gore saklanir.
Git'e buyuk veri yerine yalnizca kucuk bir isaretci (.veri) girer.
"""
import glob
import hashlib
import json
import os
import shutil

DEPO = "calisma/depo_veri"


def ozet(yol):
    """Dosyanin SHA-256 ozetini parca parca hesaplar."""
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


def nesne_yolu(d, depo=DEPO):
    return os.path.join(depo, d[:2], d[2:])
```

Akış hesabı, büyük dosyaları tek seferde belleğe almadan 1 MB'lık parçalarla yapılır. `nesne_yolu` özetin ilk iki karakterini klasör adı yapar; bu, tek bir klasörde on binlerce dosya birikmesini önler. Git de aynı numaralandırmayı kullanır.

```python
def ekle(yol, depo=DEPO):
    """Dosyayi depoya koyar ve yanina isaretci (.veri) yazar."""
    d = ozet(yol)
    hedef = nesne_yolu(d, depo)
    if not os.path.exists(hedef):          # ayni icerik tek kez
        os.makedirs(os.path.dirname(hedef), exist_ok=True)
        shutil.copyfile(yol, hedef)
    isaret = {"yol": os.path.basename(yol), "sha256": d,
              "boyut": os.path.getsize(yol)}
    with open(yol + ".veri", "w", encoding="utf-8") as f:
        json.dump(isaret, f, indent=2, ensure_ascii=False)
    return d


def dogrula(isaret_yolu, depo=DEPO):
    """Depodaki nesne, isaretcideki ozetle hala eslesiyor mu?"""
    with open(isaret_yolu, encoding="utf-8") as f:
        d = json.load(f)["sha256"]
    yol = nesne_yolu(d, depo)
    return os.path.exists(yol) and ozet(yol) == d


def getir(isaret_yolu, hedef, depo=DEPO):
    """Isaretciye karsilik gelen nesneyi hedef yola geri koyar."""
    with open(isaret_yolu, encoding="utf-8") as f:
        d = json.load(f)["sha256"]
    kaynak = nesne_yolu(d, depo)
    if ozet(kaynak) != d:
        raise IOError("nesne bozulmus: " + d[:12])
    shutil.copyfile(kaynak, hedef)
    return d
```

`ekle` fonksiyonu nesneyi yalnızca depoda yoksa kopyalar ve yanına işaretçiyi yazar. `dogrula` ve `getir` fonksiyonları ise işaretçideki özeti okur ve depodaki nesnenin özetini yeniden hesaplar. İki değer tutmazsa nesne bozulmuştur ve `getir` bir hata verir. Bu kontrol, sessiz veri bozulmasının en ucuz tespitidir. Bölüm 6'daki hata ayıklama disipliniyle düşünürsek: sorunu kullanıcıya bırakmadan, yanlış veriyle model eğitilmeden durdurur.

Demo bölümü aynı içerikle kopya, değişen içerik ve bozulma senaryosunu çalıştırır:

```python
if __name__ == "__main__":
    shutil.rmtree(DEPO, ignore_errors=True)       # temiz baslangic
    os.makedirs("calisma", exist_ok=True)
    yol = "calisma/telemetri.csv"
    with open(yol, "w", encoding="utf-8") as f:
        f.write("sicaklik,akim\n31.2,9.8\n28.7,10.4\n")
    d1 = ekle(yol)
    shutil.copyfile(yol + ".veri", "calisma/v1.veri")
    print("v1 ozeti      :", d1[:16])
    shutil.copyfile(yol, "calisma/kopya.csv")
    d2 = ekle("calisma/kopya.csv")
    print("kopya ayni mi :", d1 == d2)
    print("depoda nesne  :", len(glob.glob(DEPO + "/*/*")))
    with open(yol, "a", encoding="utf-8") as f:
        f.write("30.1,10.0\n")
    d3 = ekle(yol)
    print("v2 ozeti      :", d3[:16])
    print("depoda nesne  :", len(glob.glob(DEPO + "/*/*")))
    with open("calisma/v1.veri", encoding="utf-8") as f:
        isaret = json.load(f)
    print("isaretci      :", isaret["yol"], isaret["boyut"],
          isaret["sha256"][:16] + "...")
    with open(nesne_yolu(d1), "ab") as f:      # depoyu elle boz
        f.write(b"x")
    print("v1 dogrula    :", dogrula("calisma/v1.veri"))
    try:
        getir("calisma/v1.veri", "calisma/geri.csv")
    except IOError as e:
        print("getir hatasi  :", e)
```

Betiğin çıktısı aşağıdadır.

```term
$ python b77_veri.py
v1 ozeti      : 8d7116f4039ba281
kopya ayni mi : True
depoda nesne  : 1
v2 ozeti      : ce70d463373fa119
depoda nesne  : 2
isaretci      : telemetri.csv 36 8d7116f4039ba281...
v1 dogrula    : False
getir hatasi  : nesne bozulmus: 8d7116f4039b
```

İlk iki satır temel fikri gösterir: aynı içerikli iki dosya aynı özeti üretir ve depoda tek nesne vardır. Dosyaya tek bir satır eklendiğinde özet değişir ve depoda ikinci nesne oluşur. Eski sürümün işaretçisiyle yapılan denetim, depodaki nesne elle bozulduğunda `False` döner ve `getir` hatayı yakalar.

Bu küçük araç bilinçli olarak eksik bırakılmıştır. Uzak depo, paylaşım, yetkilendirme, kopya ve birden çok sürüm arasında geçiş yoktur. Bunlar gerçek araçların (DVC, Git LFS, S3 benzeri nesne depoları) işidir ve bu bölümde çalıştırılmadı. Ama temel fikir aynıdır ve bir sonraki adım, veri ile model arasındaki bağı kurmaktır: bir türev veri hangi ham verinin özetine dayanıyorsa, bu bağ kaydedilmelidir. Buna **veri kökeni (lineage)** denir ve Örnek 2'de kullanılacak.

## 77.5 Deney takibi: SQLite ile sıfırdan

Bir ekip haftada onlarca eğitim koşusu yapar. Üç hafta sonra biri "geçen ayki en iyi model hangisiydi?" diye sorar. Cevap bir notebook hücresinde, bir yorum satırında ya da kimsenin hatırlamadığı bir dosya adında kalmışsa, o sonuç yeniden üretilemez ve güvenilmez hâle gelir. Deney takipçisinin işi bu soruya tek bir sorguyla cevap verebilmektir.

Takipçinin veri modeli dört tablodur (Şekil 77.4). `deney` tablosu her koşuyu bir satır olarak tutar ve koşunun kod sürümünü (git commit), veri özetini ve ortam parmak izini bağlar. `parametre` ve `metrik` tabloları koşuya bağlı anahtar-değer çiftleridir; böylece her koşunun hiperparametreleri ve sonuçları ayrı satırlarda durur. `artefakt` tablosu koşunun ürettiği dosyaları, yani model dosyasını, özetiyle birlikte tutar. Eğitim ve test metriklerini ayrı anahtarlarla kaydetmek bilinçli bir karardır: Bölüm 54 ve 57'de gördüğümüz gibi eğitim skoru tek başına başarı sayılmaz.

![Şekil 77.4: Deney takibi veri modeli; koşu merkezde, diğer tablolar koşuya bağlanır](gorseller/b77_deney_modeli.png)

Takipçinin bağlandığı veri kaynağı için küçük bir telemetri üreticisi yazdık. Bölüm 68'deki batarya ve İHA telemetrisi fikrini sadeleştirdik: dört özellik (sıcaklık, akım, gerilim, döngü sayısı) ve arıza etiketi. Gerçek kural bilindiği için kaymanın etkisini kontrollü ölçebiliriz. Taban arıza oranı yaklaşık %11'dir. Ortamın kayması (`ortam_kaymasi`) yalnızca girdi dağılımını, kuralın katsayısının kayması (`katsayi_kaymasi`) ise girdi ile etiket arasındaki ilişkiyi değiştirir.

```python
# -*- coding: utf-8 -*-
"""Sentetik batarya telemetrisi (kisa, kontrollu bir veri kaynagi).

Her satir bir olcum penceresi: sicaklik, akim, gerilim, dongu sayisi.
Etiket: pencerede ariza var (1) ya da yok (0). Gercek kural bilindigi
icin kaymanin etkisini kontrollu olarak olcebiliriz.
"""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

OZELLIKLER = ["sicaklik", "akim", "gerilim", "dongu"]
ESIK = 2.6   # risk bu degeri asarsa ariza; oran yaklasik %10
```

```python
def uret(n, rng, ortam_kaymasi=0.0, katsayi_kaymasi=0.0):
    """n ornek uretir. Doner: X (n x 4), y (n,)

    ortam_kaymasi:  sicaklik dagiliminin otelenmesi (kovaryat).
                     Kural degismez, yalnizca girdi dagilimi kayar.
    katsayi_kaymasi: sicakligin arizaya etkisinin degismesi
                     (kavram kaymasi). p(y|x) degisir.
    """
    sicaklik = rng.normal(30.0, 4.0, n) + ortam_kaymasi
    akim = rng.normal(10.0, 3.0, n)
    gerilim = rng.normal(3.7, 0.05, n)
    dongu = rng.uniform(0, 1000, n)
    risk = ((0.25 + katsayi_kaymasi) * (sicaklik - 30.0)
            + 0.12 * (akim - 10.0)
            - 30.0 * (gerilim - 3.7)
            + 0.0015 * (dongu - 500.0)
            + rng.normal(0.0, 1.0, n))
    y = (risk > ESIK).astype(int)
    X = np.column_stack([sicaklik, akim, gerilim, dongu])
    return X, y


def model_kur(C=1.0):
    """Olcekleme + lojistik regresyon. Tek bir boru hatti."""
    return make_pipeline(StandardScaler(),
                         LogisticRegression(C=C, max_iter=1000))
```

Takip kodu SQL şemasıyla başlar. Şemanın tüm tabloları `CREATE TABLE IF NOT EXISTS` ile oluşturulur; böylece betik tekrar çalıştırıldığında veri kaybetmez.

```python
# -*- coding: utf-8 -*-
"""SQLite tabanli deney takipcisi (MLflow'un kucuk bir benzeri).

Her deney icin: kod surumu (git commit), veri ozeti, parametreler,
metrikler ve artefakt ozetleri tek bir veritabaninda tutulur.
"""
import datetime
import os
import sqlite3
import subprocess

import joblib
import numpy as np
from sklearn.metrics import roc_auc_score

from b77_veri import ozet
from b77_telemetri import model_kur

SEMA = """
CREATE TABLE IF NOT EXISTS deney (
  id INTEGER PRIMARY KEY, ad TEXT, zaman TEXT,
  git TEXT, veri TEXT, ortam TEXT);
CREATE TABLE IF NOT EXISTS parametre (
  deney INTEGER, anahtar TEXT, deger TEXT);
CREATE TABLE IF NOT EXISTS metrik (
  deney INTEGER, anahtar TEXT, deger REAL);
CREATE TABLE IF NOT EXISTS artefakt (
  deney INTEGER, yol TEXT, sha256 TEXT);
"""
```

Aşağıdaki kesit `git_commit` fonksiyonunu ve `Takip` sınıfının başlangıç metotlarını içerir. Git komutu bir kod deposu yoksa hata vermek yerine `yok` döndürür; deney yine kaydedilir ama kod sürümü boş kalır. Bu, takipçinin bir kod bilgisi olmadan çalışmayı reddetmediği, ama bunu gizlemediği anlamına gelir.

```python
def git_commit(kod="."):
    """Kod deposunun HEAD commit'ini okur; depo yoksa 'yok' doner."""
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=kod,
                           capture_output=True, text=True, check=True)
        return r.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "yok"


class Takip:
    def __init__(self, dosya):
        self.db = sqlite3.connect(dosya)
        self.db.executescript(SEMA)

    def baslat(self, ad, veri_ozeti, kod, ortam=""):
        zaman = datetime.datetime.now().isoformat(timespec="seconds")
        cur = self.db.execute(
            "INSERT INTO deney (ad, zaman, git, veri, ortam) "
            "VALUES (?, ?, ?, ?, ?)",
            (ad, zaman, git_commit(kod), veri_ozeti, ortam))
        self.db.commit()
        return cur.lastrowid

    def parametre(self, deney, d):
        self.db.executemany("INSERT INTO parametre VALUES (?, ?, ?)",
                            [(deney, k, str(v))
                            for k, v in d.items()])
        self.db.commit()

    def metrik(self, deney, anahtar, deger):
        self.db.execute("INSERT INTO metrik VALUES (?, ?, ?)",
                        (deney, anahtar, float(deger)))
        self.db.commit()
```

Sonraki kesit, metrik ve artefakt kayıtlarını ve asıl sorguyu verir. `sirala` fonksiyonu tek bir SQL sorgusuyla her deneyin `C` parametresini ve istenen metriği bir satırda birleştirir. `gecersiz` ise bir verinin özeti değiştiğinde hangi deneylerin artık güncel veriyle eşleşmediğini bulur; Örnek 2'de bunu kullanacağız.

```python
    def artefakt(self, deney, yol):
        self.db.execute("INSERT INTO artefakt VALUES (?, ?, ?)",
                        (deney, yol, ozet(yol)))
        self.db.commit()

    def sirala(self, metrik):
        """Deneyleri metriğe göre azalan sırada listeler."""
        sorgu = """
        SELECT d.id, d.ad, d.git, d.veri,
          (SELECT deger FROM parametre p
            WHERE p.deney = d.id AND p.anahtar = 'C') AS C,
          (SELECT deger FROM metrik m
            WHERE m.deney = d.id AND m.anahtar = ?) AS skor
        FROM deney d ORDER BY skor DESC"""
        return self.db.execute(sorgu, (metrik,)).fetchall()

    def gecersiz(self, guncel_veri):
        """Veri ozeti degismis (artik gecersiz) deneyleri listeler."""
        return self.db.execute(
            "SELECT id, ad FROM deney WHERE veri != ?",
            (guncel_veri,)).fetchall()
```

Aşağıdaki kesit CSV yardımcılarını ve kod deposunu hazırlayan fonksiyonu içerir. `kod_deposu`, deneyin kod sürümünü gerçekten bir git commit'ine bağlamak için yerelde küçük bir depo oluşturur. Commit'in kimliği zamana bağlı olduğu için her makinede farklıdır; tablodaki `git` sütununu bu yüzden karşılaştırırken dikkatli ol.

```python

def csv_yaz(yol, X, y):
    with open(yol, "w", encoding="utf-8") as f:
        f.write("sicaklik,akim,gerilim,dongu,etiket\n")
        for satir, e in zip(X, y):
            f.write(",".join("%.4f" % v for v in satir) + ",%d\n" % e)


def csv_oku(yol):
    d = np.loadtxt(yol, delimiter=",", skiprows=1)
    return d[:, :4], d[:, 4].astype(int)


def kod_deposu(yol="calisma/kod"):
    """Egitim betigini iceren gecici bir git deposu hazirlar."""
    if os.path.exists(os.path.join(yol, ".git")):
        return yol
    os.makedirs(yol, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=yol, check=True)
    ep = os.path.join(yol, "egitim.py")
    with open(ep, "w", encoding="utf-8") as f:
        f.write("# egitim betigi (surum 1)\n")
    subprocess.run(["git", "add", "."], cwd=yol, check=True)
    subprocess.run(["git", "-c", "user.name=b77",
                    "-c", "user.email=b77@example.com",
                    "commit", "-q", "-m", "egitim betigi"],
                   cwd=yol, check=True)
    return yol
```

Demo bölümü dört farklı `C` değeri için lojistik regresyon eğitir. Her koşu için eğitim ve test AUC'sini kaydeder, modeli `joblib` ile diske yazar ve dosyanın özetini `artefakt` tablosuna ekler.

```python
if __name__ == "__main__":
    from b77_veri import ekle
    from b77_telemetri import uret
    if os.path.exists("calisma/takip.db"):
        os.remove("calisma/takip.db")
    kod = kod_deposu()
    rng = np.random.default_rng(42)
    csv_yaz("calisma/egitim.csv", *uret(3000, rng))
    csv_yaz("calisma/test.csv", *uret(2000, np.random.default_rng(7)))
    v_egitim = ekle("calisma/egitim.csv")
    Xe, ye = csv_oku("calisma/egitim.csv")
    Xt, yt = csv_oku("calisma/test.csv")

    takip = Takip("calisma/takip.db")
    for C in [0.01, 0.1, 1.0, 10.0]:
        d = takip.baslat("lojistik", v_egitim, kod)
        takip.parametre(d, {"C": C, "tohum": 42, "model": "lojistik"})
        m = model_kur(C).fit(Xe, ye)
        takip.metrik(d, "egitim_auc",
                     roc_auc_score(ye, m.predict_proba(Xe)[:, 1]))
        takip.metrik(d, "test_auc",
                     roc_auc_score(yt, m.predict_proba(Xt)[:, 1]))
        yol = "calisma/model_%d.joblib" % d
        joblib.dump(m, yol)
        takip.artefakt(d, yol)

    print("%-3s %-8s %-8s %-8s %-9s %-9s" %
          ("id", "C", "git", "veri", "egitim", "test"))
    for satir in takip.sirala("test_auc"):
        did, ad, git, veri, C, skor = satir
        egitim = takip.db.execute(
            "SELECT deger FROM metrik WHERE deney=? AND "
            "anahtar='egitim_auc'", (did,)).fetchone()[0]
        print("%-3d %-8s %-8s %-8s %-9.4f %-9.4f" %
              (did, C, git[:7], veri[:8], egitim, skor))
```

Betiği çalıştırdığında sıralanmış tablo aşağıdaki gibi çıkar:

```term
$ python b77_takip.py
id  C        git      veri     egitim    test     
4   10.0     c8b0d4c  23397e5e 0.9496    0.9585   
3   1.0      c8b0d4c  23397e5e 0.9496    0.9585   
2   0.1      c8b0d4c  23397e5e 0.9496    0.9584   
1   0.01     c8b0d4c  23397e5e 0.9495    0.9581   
```

Tablo üç şeyi gösterir. Birincisi, dört koşunun da aynı veri özetine (`23397e5e`) bağlı olmasıdır; bu, hepsinin aynı eğitim dosyasını gördüğünü garanti eder. İkincisi, test AUC'lerinin 0,9581 ile 0,9585 arasında olmasıdır. `C` değeri 0,01'den 10'a çıkarken sonuç neredeyse hiç değişmiyor. Bu bir hata değil: 3000 satır ve dört özellik için düzenlileştirme belirleyici değil. Üçüncüsü ve en önemlisi, sıralamanın üst sıradaki iki koşu arasında bir fark olmamasıdır. Bu tür küçük farklar tohum değişince kaybolur; tek koşuya bakıp "en iyi C budur" demek Bölüm 57.11'de gördüğümüz hatanın ta kendisidir.

MLflow bu makinede kurulu (sürüm 3.12) ve aynı tabloyu `mlflow.log_param` ile `mlflow.log_metric` çağrılarıyla tutar. Bu bölümde MLflow çalıştırılmadı; yukarıdaki kod yalnızca aynı fikri gösterir. Gerçek bir ekipte araç seçimi, kullanıcı arayüzü, dosya depolama ve kullanıcı yetkilendirmesi gibi konulara bağlıdır.

## 77.6 Model kayıt defteri: sürüm, aşama ve geri alma

Deney takipçisi "hangi koşu" sorusunu yanıtlar. Üretimde çalışan modelin hangi koşudan geldiğini ve o an hangi aşamada olduğunu ise **model kayıt defteri** tutar. Bir model sürümü önce kayıtlıdır, sonra staging (test ortamında) aşamasına alınır, onaylanırsa production'a geçer. Yeni model production'a geçtiğinde eski üretim sürümü arşive gider; böylece gerektiğinde geri alınabilir.

Kayıt defterinde iki kural önemlidir. Birincisi, her sürümün dosya özeti saklanır ve model yüklenirken bu özet yeniden hesaplanır. Dosya değiştiyse model yüklenmez. İkincisi, model dosyası `pickle` tabanlı bir biçimde saklanır, bu da güvenlik açısından kritiktir: `pickle` ile kaydedilmiş bir dosyayı yüklemek içindeki kodu çalıştırmak demektir. Bu yüzden model dosyasını yalnızca kendi ürettiğin ve özetini doğruladığın dosyalardan yükle. Savunma yazılımında bu kural bir politika olmalıdır (Bölüm 78'de tekrar döneceğiz).

Kayıt defteri, JSON tabanlı bir indeks dosyası ve sürüm dosyalarından oluşur. Kodun tamamı aşağıda.

```python
# -*- coding: utf-8 -*-
"""Model kayit defteri: surum, asama, ozet ve geri alma.

Her surum bir dosyadir; kayit defteri dosyanin SHA-256 ozetini saklar.
Yukleme sirasinda ozet yeniden hesaplanir; eslesmezse model yuklenmez.
"""
import json
import os

import joblib

from b77_veri import ozet
```

`KayitDefteri` sınıfı, kayıt defterinin indeksini başlatır ve her değişiklikten sonra diske yazar. `kaydet` yeni bir sürüm oluşturur ve sürümün özetini hemen hesaplar.

```python
class KayitDefteri:
    def __init__(self, kok="calisma/kayit"):
        self.kok = kok
        self.dosya = os.path.join(kok, "index.json")
        os.makedirs(kok, exist_ok=True)
        self.idx = {}
        if os.path.exists(self.dosya):
            with open(self.dosya, encoding="utf-8") as f:
                self.idx = json.load(f)

    def _kaydet(self):
        with open(self.dosya, "w", encoding="utf-8") as f:
            json.dump(self.idx, f, indent=2, ensure_ascii=False)

    def kaydet(self, ad, model, deney, veri):
        """Yeni surum yazar; asamasi 'kayitli' olarak baslar."""
        surumler = self.idx.setdefault(ad, [])
        n = len(surumler) + 1
        yol = os.path.join(self.kok, ad, "v%d.joblib" % n)
        os.makedirs(os.path.dirname(yol), exist_ok=True)
        joblib.dump(model, yol)
        surumler.append({"surum": n, "dosya": yol,
                         "sha256": ozet(yol),
                         "deney": deney, "veri": veri,
                         "asama": "kayitli"})
        self._kaydet()
        return n
```

`asama_ata` yeni bir sürümü production'a alırken eski production sürümünü arşive taşır. `yukle` ise aşamadaki sürümü yüklemeden önce özeti doğrular. Özet tutmazsa `ValueError` fırlatır; bu, bozulmuş ya da değiştirilmiş bir modelin üretime sızmasını engeller.

```python
    def asama_ata(self, ad, n, asama):
        """Asama atar. 'production' ise eski surum arsive gider."""
        for s in self.idx[ad]:
            if asama == "production" and s["asama"] == "production":
                s["asama"] = "arsiv"
            if s["surum"] == n:
                s["asama"] = asama
        self._kaydet()

    def yukle(self, ad, asama):
        """Asamadaki surumu yukler; once ozeti dogrular."""
        for s in self.idx[ad]:
            if s["asama"] == asama:
                if ozet(s["dosya"]) != s["sha256"]:
                    raise ValueError(
                        "%s v%d bozulmus" % (ad, s["surum"]))
                # yalniz kendi dosyani yukle
                return joblib.load(s["dosya"])
        raise KeyError("%s icin %s surumu yok" % (ad, asama))
```

`geri_al` fonksiyonu production sürümünü "geri alındı" olarak işaretler ve en son arşivlenmiş sürümü yeniden production'a alır. Bu bir `git revert` gibi çalışır: geçmiş silinmez, yalnızca aktif sürüm değişir. `goster` ise tüm sürümleri aşamalarıyla birlikte basar.

```python
    def geri_al(self, ad):
        """Uretimdeki surumu, son arsiv surumuyle degistirir."""
        surumler = self.idx[ad]
        uretim = [s for s in surumler if s["asama"] == "production"]
        arsiv = [s for s in surumler if s["asama"] == "arsiv"]
        if not uretim or not arsiv:
            raise KeyError("geri alinacak surum yok")
        hedef = max(arsiv, key=lambda s: s["surum"])
        uretim[0]["asama"] = "geri_alindi"
        hedef["asama"] = "production"
        self._kaydet()
        return hedef["surum"]

    def goster(self, ad):
        for s in self.idx[ad]:
            print("  v%d  %-12s deney=%s veri=%s" %
                  (s["surum"], s["asama"], s["deney"], s["veri"][:8]))
```

Demo üç model sürümü üretir, her birini production'a alır, sonra geri alma yapar ve bozulmuş bir sürümü yüklemeye çalışır. Demo'da üçüncü sürümün kötü olduğunu varsayıyoruz. Gerçek hayatta bu kararı izleme sistemi (77.9) ve kalite kapısı (77.7) verir.

```python
if __name__ == "__main__":
    import shutil

    import numpy as np

    from b77_telemetri import model_kur, uret
    shutil.rmtree("calisma/kayit", ignore_errors=True)
    kd = KayitDefteri()
    veri = ozet("calisma/egitim.csv")
    X, y = uret(2000, np.random.default_rng(3))
    for i, C in enumerate([1.0, 0.1, 10.0], 1):
        n = kd.kaydet("batarya", model_kur(C).fit(X, y), i, veri)
        kd.asama_ata("batarya", n, "production")
        print("v%d kaydedildi ve uretime alindi (C=%s)" % (n, C))
    print("--- durum (geri alma oncesi)")
    kd.goster("batarya")
    print("geri alinan surum:", kd.geri_al("batarya"))
    print("--- durum (geri alma sonrasi)")
    kd.goster("batarya")
    m = kd.yukle("batarya", "production")
    print("uretim modeli yuklendi:", type(m).__name__)
    with open(kd.idx["batarya"][1]["dosya"], "ab") as f:
        f.write(b"!")                          # v2 dosyasini bozalim
    try:
        kd.yukle("batarya", "production")
    except ValueError as e:
        print("yukleme reddedildi:", e)
```

Betiğin çıktısı şöyledir:

```term
$ python b77_kayit.py
v1 kaydedildi ve uretime alindi (C=1.0)
v2 kaydedildi ve uretime alindi (C=0.1)
v3 kaydedildi ve uretime alindi (C=10.0)
--- durum (geri alma oncesi)
  v1  arsiv        deney=1 veri=23397e5e
  v2  arsiv        deney=2 veri=23397e5e
  v3  production   deney=3 veri=23397e5e
geri alinan surum: 2
--- durum (geri alma sonrasi)
  v1  arsiv        deney=1 veri=23397e5e
  v2  production   deney=2 veri=23397e5e
  v3  geri_alindi  deney=3 veri=23397e5e
uretim modeli yuklendi: Pipeline
yukleme reddedildi: batarya v2 bozulmus
```

Çıktıdaki üç satır, bir sürümün yaşam döngüsünü gösterir. Geri alma öncesinde v3 production'dadır. Geri almadan sonra v2 yeniden production'a geçer ve v3 "geri_alindi" olarak kalır; kayıt silinmemiştir, tarih boyunca izi durur. Son satır bozulma kontrolünün çalıştığını gösterir: v2 dosyasına bir bayt eklendiğinde yükleme reddedilir.

Bu tasarımın sınırı da açıktır. Kayıt defteri, bir sürümün "neden" production'a alındığını bilmez; bu bilgi onay sürecinde tutulmalıdır. Ayrıca iki ekip aynı anda aşama değiştirirse çakışma çözümü yoktur. Gerçek MLflow Model Registry ve benzeri araçlar bu sorunları eşzamanlılık denetimi ve kullanıcı yetkileriyle çözer (çalıştırılmadı).

## 77.7 CI/CD for ML: veri doğrulama, kalite kapısı ve testler

Yazılımda sürekli entegrasyon (CI) her değişiklikte testleri çalıştırır ve kırılan bir değişikliği birleştirmeyi engeller (Bölüm 42.10 ve 39.4). ML'de aynı mantık üç ek kontrol gerektirir. Birincisi **veri doğrulamadır**: gelen verinin şeması, değer aralıkları ve eksik oranı beklenen gibi mi? İkincisi **model kalite kapısıdır**: yeni model, üretimdeki modelden istatistiksel olarak anlamlı biçimde kötü mü? Üçüncüsü **birim testleridir**: ön işleme, metrik ve kayıt fonksiyonları doğru mu? Bölüm 71.8'de LLM değerlendirmesini CI'a koymanın gerekliliğini gördük; burada bu fikri sayısal modeller için sıfırdan kuruyoruz.

Veri doğrulama üç denetimi yapar. Sütunlar var mı ve sayısal mı? Her değer beklenen aralıkta mı? Eksik değerlerin oranı eşiğin altında mı? Hepsi geçerse parti eğitime alınır; biri başarısız olursa eğitim başlamaz. Bu, Bölüm 56'da gördüğümüz veri sözleşmesinin çalıştırılabilir hâlidir.

Kalite kapısının kriteri bir **eşleştirilmiş önyükleme (bootstrap)** ile kurulur. Aynı test örnekleri hem üretimdeki modele (taban) hem adaya verilir. Her önyükleme örneğinde iki modelin AUC'leri hesaplanır ve farkları toplanır. Farkın %2,5 alt sınırı, önceden belirlenmiş marjın (0,01) altına düşerse aday reddedilir. Bu bir **non-inferiority** (kötü değil) testidir: adayın daha iyi olmasını aramıyoruz, yalnızca belirgin biçimde kötü olmadığını kanıtlamasını istiyoruz. Önyüklemenin mantığı Bölüm 49.9'da, modelleri anlamlı biçimde karşılaştırmanın nasıl yapılacağı Bölüm 57.11'de anlatıldı.

Şekil 77.5 hattın sırasını gösterir: kod commit'i, veri doğrulama, eğitim, ölçütler, kalite kapısı. Kapı reddederse yayın olmaz; geçerse kayıt defterine staging olarak girer.

![Şekil 77.5: CI/CD kalite kapısı hattı; reddedilen model yayınlanmaz](gorseller/b77_kalite_kapisi.png)

Aşağıdaki kod hem veri doğrulamayı hem kalite kapısını içerir. Önce doğrulama ve kapının fonksiyonlarını, ardından deneyi kuran yardımcıyı okuyalım.

```python
# -*- coding: utf-8 -*-
"""Veri dogrulama ve model kalite kapisi (sifirdan)."""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from b77_telemetri import OZELLIKLER, model_kur, uret

ARALIK = {"sicaklik": (-20, 80), "akim": (-5, 40),
          "gerilim": (3.0, 4.3), "dongu": (0, 5000)}
EKSIK_ESIK = 0.01
SEEDS = [11, 22, 33]
```

```python
def veri_denetle(df):
    """Hata listesi doner; bos liste, parti gecti demektir."""
    hatalar = []
    for c in OZELLIKLER:
        if c not in df.columns:
            hatalar.append("eksik sutun: " + c)
        elif not pd.api.types.is_numeric_dtype(df[c]):
            hatalar.append("sayisal degil: " + c)
    for c, (lo, hi) in ARALIK.items():
        if c in df.columns:
            d = int(((df[c] < lo) | (df[c] > hi)).sum())
            if d:
                hatalar.append("%s aralik disi: %d" % (c, d))
    eksik = float(df.isna().mean().max())
    if eksik > EKSIK_ESIK:
        hatalar.append("eksik orani %.1f%%" % (100 * eksik))
    return hatalar
```

`veri_denetle` boş bir liste döndürürse parti geçmiştir. Eksik sütun, sayısal olmayan sütun, aralık dışı değer ve eksik oran için ayrı mesajlar üretir; böylece hata neden durdurdu sorusunun cevabı hemen görünür.

```python
def fark_dagilimi(y, p_yeni, p_eski, B, rng):
    """Eslestirilmis onyukleme: AUC farkinin B ornekli dagilimi."""
    n = len(y)
    farklar = []
    while len(farklar) < B:
        i = rng.integers(0, n, n)
        if len(np.unique(y[i])) < 2:
            continue
        farklar.append(roc_auc_score(y[i], p_yeni[i])
                       - roc_auc_score(y[i], p_eski[i]))
    return np.array(farklar)


def kapi(y, p_yeni, p_eski, marj=0.01, B=1000, rng=None):
    """Yeni model, eskisinden marjdan fazla kotuyse reddedilir.

    Doner: (gecti, fark ortalamasi, %2,5 alt sinir)
    """
    rng = rng or np.random.default_rng(0)
    f = fark_dagilimi(y, p_yeni, p_eski, B, rng)
    alt = float(np.percentile(f, 2.5))
    return alt > -marj, float(f.mean()), alt
```

`fark_dagilimi` önyükleme yapar. Bir örnekte yalnızca bir sınıf varsa AUC tanımsızdır; bu yüzden o örnek atlanır. `kapi` ise farkın %2,5 alt sınırını alır ve kabul kararını verir. Rastgelelik `rng` ile dışarıdan verilir; bu sayede aynı tohumla aynı karar çıkar.

```python
def aday_kur(ad, rng):
    """Dort adaydan birini egitir. Doner: (model, sutun dilimi)."""
    tum = slice(None)
    if ad == "daha_fazla_veri":
        X, y = uret(6000, rng)
    elif ad == "etiket_gurultulu":          # etiketlerin %30'u ters
        X, y = uret(2000, rng)
        ters = rng.random(len(y)) < 0.3
        y = np.where(ters, 1 - y, y)
    elif ad == "ozellik_eksik":             # sicaklik sutunu yok
        X, y = uret(2000, rng)
        X, tum = X[:, 1:], slice(1, None)
    else:                                   # yeni_tohum
        X, y = uret(2000, rng)
    return model_kur().fit(X, y), tum
```

`aday_kur` dört aday üretir: aynı dağılımdan yeni bir örnekle eğitilmiş model (`yeni_tohum`), daha büyük veriyle eğitilmiş model (`daha_fazla_veri`), etiketlerinin %30'u ters çevrilmiş model (`etiket_gurultulu`) ve bir özelliği (sıcaklığı) eksik model (`ozellik_eksik`). Bunların birincisi ve ikincisi iyi, sonuncu ikisi kötü aday olarak tasarlandı. Kapının bu ayrımı yapıp yapmadığını ölçeceğiz.

```python
if __name__ == "__main__":
    print("--- veri denetimi")
    df = pd.DataFrame(uret(500, np.random.default_rng(5))[0],
                      columns=OZELLIKLER)
    print("temiz parti     :", veri_denetle(df) or "gecti")
    print("gerilim yok     :",
          veri_denetle(df.drop(columns="gerilim")))
    b = df.copy()
    b.loc[:9, "akim"] = 999.0
    print("akim bozuk      :", veri_denetle(b))
    b = df.copy()
    b.loc[:19, "sicaklik"] = np.nan
    print("eksik deger     :", veri_denetle(b))
    print("--- kalite kapisi (3 tohum, B=1000)")
    print("tohum aday            fark     alt    karar")
    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        Xt, yt = uret(2000, rng)
        taban = model_kur().fit(Xt, yt)
        Xs, ys = uret(2000, rng)            # tutulmus test kumesi
        p_eski = taban.predict_proba(Xs)[:, 1]
        for ad in ["yeni_tohum", "daha_fazla_veri",
                   "etiket_gurultulu", "ozellik_eksik"]:
            m, dil = aday_kur(ad, rng)
            p_yeni = m.predict_proba(Xs[:, dil])[:, 1]
            gecti, ort, alt = kapi(ys, p_yeni, p_eski,
                                   rng=np.random.default_rng(seed))
            print("%-5d %-17s %+.4f %+.4f  %s" %
                  (seed, ad, ort, alt, "KABUL" if gecti else "RED"))
```

Betik önce dört veri denetimi senaryosunu, sonra üç tohum için dört adayın kapı sonucunu basar. Çalışma süresi yaklaşık bir dakikadır, çünkü her karşılaştırma bin önyükleme örneği kullanır.

```term
$ python b77_kapi.py
--- veri denetimi
temiz parti     : gecti
gerilim yok     : ['eksik sutun: gerilim']
akim bozuk      : ['akim aralik disi: 10']
eksik deger     : ['eksik orani 4.0%']
--- kalite kapisi (3 tohum, B=1000)
tohum aday            fark     alt    karar
11    yeni_tohum        -0.0005 -0.0019  KABUL
11    daha_fazla_veri   -0.0002 -0.0018  KABUL
11    etiket_gurultulu  -0.0020 -0.0040  KABUL
11    ozellik_eksik     -0.0653 -0.0819  RED
22    yeni_tohum        +0.0001 -0.0037  KABUL
22    daha_fazla_veri   +0.0009 -0.0012  KABUL
22    etiket_gurultulu  -0.0225 -0.0325  RED
22    ozellik_eksik     -0.0738 -0.0920  RED
33    yeni_tohum        -0.0004 -0.0018  KABUL
33    daha_fazla_veri   +0.0005 -0.0004  KABUL
33    etiket_gurultulu  -0.0274 -0.0371  RED
33    ozellik_eksik     -0.0551 -0.0700  RED
```

Veri denetimi kısmı beklenen hataları yakalar: `gerilim` sütunu yoksa "eksik sütun", `akim` değerlerinin on tanesi 999 yapılmışsa "aralık dışı", sıcaklığın yüzde dördü boşsa "eksik oranı" mesajı çıkar. Üretim hattında bu mesajlar eğitimi durdurmalıdır.

Kalite kapısı kısmı daha öğreticidir. Üç tohum için sonuçları özetlersek:

| Aday | Tohum 11 | Tohum 22 | Tohum 33 |
|---|---|---|---|
| yeni_tohum | KABUL (alt sınır -0,0019) | KABUL (-0,0037) | KABUL (-0,0018) |
| daha_fazla_veri | KABUL (-0,0018) | KABUL (-0,0012) | KABUL (-0,0004) |
| etiket_gurultulu | KABUL (-0,0040) | RED (-0,0325) | RED (-0,0371) |
| ozellik_eksik | RED (-0,0819) | RED (-0,0920) | RED (-0,0700) |

Ozellik eksik modeli üç tohumda da reddedildi. Bu üreteçte en güçlü özellik gerilimdir, sıcaklık ikincidir; sıcaklık sütununu çıkarmak tahmin gücünü belirgin biçimde düşürür ve kapı bunu kolayca görür. Yeni tohumlu ve daha büyük veriyle eğitilmiş adaylar üç tohumda da kabul edildi; bu beklenen davranıştır, çünkü onlar iyi bir modeldir.

Etiket gürültülü aday ise bir sorun gösteriyor. Üç tohumun ikisinde reddedildi, birinde (tohum 11) kabul edildi, çünkü o tohumdaki fark yalnızca -0,0020 ve alt sınır marj içinde kaldı. Bu, kapının gerçek ama küçük bozulmaları her zaman yakalamadığını gösterir. Çözüm marjı keyfi bırakmamak, test kümesini büyütmek ve kararı tek bir tohuma değil birden çok tohuma dayandırmaktır. Bu sonuç bilinçli olarak bu bölümde bırakılmıştır, çünkü bir kapının sınırını göstermek, sınırını gizlemekten daha değerlidir.

Birim testleri aynı mantıkla yazıldı. Her fonksiyonun bir davranışını ayrı bir test doğrular ve pytest bunları tek komutla çalıştırır. Testler de kodun parçasıdır ve aynı kalite denetiminden geçer.

```python
# -*- coding: utf-8 -*-
"""Birim testleri. Calistirma: python -m pytest -q test_b77.py"""
import os

import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import StandardScaler

from b77_ab import gerekli_n, guc_sim
from b77_drift import psi
from b77_kapi import kapi, veri_denetle
from b77_kayit import KayitDefteri
from b77_servis import ozellik_donustur, servis_donusumu
from b77_telemetri import model_kur, uret
from b77_veri import dogrula, ekle, getir, ozet

OZ = ["sicaklik", "akim", "gerilim", "dongu"]
```

```python
def test_ozet_ayni_icerik_ayni_ozet(tmp_path):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    a.write_text("1,2\n")
    b.write_text("1,2\n")
    assert ozet(str(a)) == ozet(str(b))


def test_ayni_icerik_tek_nesne(tmp_path):
    depo = str(tmp_path / "depo")
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    a.write_text("x\n")
    b.write_text("x\n")
    assert ekle(str(a), depo) == ekle(str(b), depo)
    assert len(list((tmp_path / "depo").glob("*/*"))) == 1


def test_bozulma_yakalanir(tmp_path):
    depo = str(tmp_path / "depo")
    a = tmp_path / "a.csv"
    a.write_text("x\n")
    d = ekle(str(a), depo)
    with open(os.path.join(depo, d[:2], d[2:]), "ab") as f:
        f.write(b"y")
    assert dogrula(str(a) + ".veri", depo) is False
    with pytest.raises(IOError):
        getir(str(a) + ".veri", str(tmp_path / "geri.csv"), depo)
```

```python
def test_psi_ayni_dagilim_kucuk():
    rng = np.random.default_rng(0)
    assert psi(rng.normal(size=5000), rng.normal(size=5000)) < 0.02


def test_psi_kayma_esigi_asar():
    rng = np.random.default_rng(0)
    assert psi(rng.normal(size=5000),
               rng.normal(1.0, size=5000)) > 0.2


def test_veri_denetle_sutun_ve_aralik():
    X, _ = uret(200, np.random.default_rng(1))
    df = pd.DataFrame(X, columns=OZ)
    assert veri_denetle(df) == []
    assert any("eksik sutun" in h
               for h in veri_denetle(df.drop(columns="akim")))
    df.loc[0, "akim"] = 999.0
    assert any("aralik disi" in h for h in veri_denetle(df))
```

```python
def test_kapi_ayni_model_gecer():
    rng = np.random.default_rng(2)
    X, y = uret(1500, rng)
    Xs, ys = uret(1000, rng)
    p = model_kur().fit(X, y).predict_proba(Xs)[:, 1]
    gecti, _, _ = kapi(ys, p, p, B=200, rng=np.random.default_rng(0))
    assert gecti


def test_kapi_ozellik_eksik_adayi_reddeder():
    rng = np.random.default_rng(3)
    X, y = uret(2000, rng)
    Xs, ys = uret(2000, rng)
    eski = model_kur().fit(X, y).predict_proba(Xs)[:, 1]
    yeni = model_kur().fit(X[:, 1:], y).predict_proba(Xs[:, 1:])[:, 1]
    gecti, _, _ = kapi(ys, yeni, eski, B=300,
                       rng=np.random.default_rng(0))
    assert not gecti
```

```python
def test_kayit_geri_al(tmp_path):
    kd = KayitDefteri(str(tmp_path / "kayit"))
    X, y = uret(300, np.random.default_rng(4))
    for i in range(3):
        n = kd.kaydet("m", model_kur(1.0).fit(X, y), i, "v")
        kd.asama_ata("m", n, "production")
    assert kd.geri_al("m") == 2
    assert [s["asama"] for s in kd.idx["m"]] == \
        ["arsiv", "production", "geri_alindi"]


def test_servis_olcek_yok_farkli():
    X, _ = uret(100, np.random.default_rng(5))
    sc = StandardScaler().fit(X)
    assert np.allclose(ozellik_donustur(X, sc), sc.transform(X))
    assert not np.allclose(servis_donusumu(X, sc, "olcek_yok"),
                           sc.transform(X))


def test_ab_formul_ve_simulasyon():
    n = gerekli_n(0.05, 0.06)
    assert 8100 <= n <= 8200
    assert abs(guc_sim(0.05, 0.06, n, deneme=4000) - 0.8) < 0.03
```

Testler şu çıktıyı verir:

```term
$ COLUMNS=70 python -m pytest -q -p no:cacheprovider test_b77.py
...........                                                    [100%]
11 passed in 8.34s
```

On bir testin tamamı geçti. Bu sayı bir kalite güvencesi değildir; yalnızca testlerin çalıştığını gösterir. Önemli olan, her testin bir hatayı yakalayabileceğini bilmektir. Örneğin `test_bozulma_yakalanir` depodaki bir baytı değiştirir ve hatanın fark edildiğini doğrular; `test_kapi_ozellik_eksik_adayi_reddeder` kapının gerçekten çalıştığını kanıtlar. Bu test bir kapının her zaman "kabul" dediğini de yakalar.

Bu testlerin GitHub Actions üzerinde her değişiklikte çalışması için aşağıdaki iş akışı yazılabilir. Bu dosya bu makinede çalıştırılmadı ve yalnızca bir örnek olarak verilmiştir.

```yaml
name: ml-kalite-kapisi
on:
  pull_request:
    paths: ["**/*.py", "**/*.veri", "requirements.lock"]
jobs:
  dogrula:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Kilitli ortam
        run: pip install -r requirements.lock
      - name: Birim testleri
        run: python -m pytest -q test_b77.py
      - name: Veri ve kalite kapisi
        run: python b77_kapi.py
```

Bu iş akışının önemli bir ayrıntısı, `requirements.lock` dosyasını kurmasıdır. Ortam kilitlenmezse CI makinesi farklı bir scikit-learn sürümü kurabilir ve kapının sonucu değişebilir. Yani CI'ın da tekrarlanabilir olması gerekir; bu, 77.3'te anlattığımız kuralın aynısıdır.

Gerçek bir kalite kapısında ek olarak "aday modeli eğit" adımı ve "eşik değerleri değiştiyse ekibe bildir" gibi onay adımları da bulunur. Bunları bu bölümde kodlamadık; amaç kararın mantığını göstermekti.

## 77.8 Dağıtım kalıpları ve eğitim/servis çarpıklığı

Model iki ana biçimde servis edilir. **Toplu çıkarımda (batch)** model belirli aralıklarla tüm veriyi işler ve sonuçları bir tabloya yazar; örneğin her gece bir bakım raporu üretilir. Hatalı bir sonuç düzeltilip yeniden hesaplanabilir. **Çevrimiçi çıkarımda (online)** her istek için bir tahmin üretilir ve gecikme kritik olur (Bölüm 41.5 ve 71.12). Hangi biçimin seçileceği problemin gereksinimlerine bağlıdır; gömülü cihazda çalışan model (Bölüm 75.7) çevrimiçi servisin en uç hâlidir.

Yeni bir modeli üretime almanın üç yaygın kalıbı vardır (Şekil 77.6). **Gölge (shadow)** dağıtımda aday model canlı trafiği alır ama yanıtı kullanıcıya gitmez; gecikme, hata ve tahmin dağılımı karşılaştırılır. Riski, adayın gerçek etkisinin hiç görülmemesidir. **Kanarya (canary)** dağıtımda trafiğin küçük bir yüzdesi adaya gider ve bu yanıtlar kullanıcıya döner. Sorun görülürse yüzde sıfıra çekilir. Örnek 3'te, kanaryanın ne kadar süre çalışması gerektiğini hesaplayacağız. **A/B testinde** kullanıcılar rastgele iki kola ayrılır ve bir ölçütün farkı hipotez testiyle değerlendirilir (Bölüm 49.10 ve 57.13). Kanaryanın amacı riski sınırlamaktır; A/B'nin amacı bir karar için kanıt üretmektir.

![Şekil 77.6: Gölge, kanarya ve A/B dağıtım kalıpları; yanıtın kullanıcıya gidip gitmediği farklıdır](gorseller/b77_dagitim.png)

Dağıtımda en sinsi hatalardan biri **eğitim/servis çarpıklığıdır** (training-serving skew). Model eğitimde bir ön işlemeyle (örneğin standardizasyon) öğrenir, ama servisteki kod aynı ön işlemeyi farklı uygular. Hiçbir istisna fırlatılmaz, model çalışmaya devam eder, yalnızca doğruluğu sessizce düşer. Bu, 77.1'deki gizli borcun en pahalı biçimidir.

Bu sorunun çözümü **tek kaynak** ilkesidir: dönüşümü bir kez tanımla ve hem eğitim hem servis aynı fonksiyonu çağırsın. Özellik deposu (feature store) kavramı bunu kurumsal ölçekte yapar; Feast gibi araçlar bu fikri uygular (çalıştırılmadı). Aşağıdaki deneyde bu fonksiyonu bilerek bozuyoruz ve etkisini ölçüyoruz.

Betik bir ön işleme tablosu tanımlar. `ozellik_donustur` tek kaynaktır; `servis_donusumu` ise dört farklı servis hatasını taklit eder: sıcaklığın ölçeklenmemesi (`olcek_yok`), akımın amper yerine miliamper gelmesi (`birim`), gerilimin bir ondalığa yuvarlanması (`yuvarlama`) ve hiçbir hatanın olmadığı doğru yol (`dogru`).

```python
# -*- coding: utf-8 -*-
"""Egitim/servis carpikligi: ayni model, farkli on isleme.

Model egitimde dogru olceklenmis veriyle egitilir. Servis tarafinda
ayni boru hatti her varyantta biraz farkli calisir. Test kumesinde
AUC'nin ne kadar dustugunu olcuyoruz (3 tohum).
"""
import os

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

from b77_telemetri import uret

SEEDS = [11, 22, 33]
VARYANTLAR = ["dogru", "olcek_yok", "birim", "yuvarlama"]
```

```python
def ozellik_donustur(ham, scaler):
    """Tek kaynak: egitim ve servis bu fonksiyonu cagirmali."""
    return scaler.transform(ham)


def servis_donusumu(ham, scaler, varyant):
    """Servis tarafindaki (bozuk olabilen) on isleme."""
    if varyant == "dogru":
        return ozellik_donustur(ham, scaler)
    if varyant == "olcek_yok":          # sicaklik olceklenmeden gecer
        x = scaler.transform(ham)
        x[:, 0] = ham[:, 0]
        return x
    if varyant == "birim":              # akim A yerine mA gider
        h = ham.copy()
        h[:, 1] *= 1000.0
        return ozellik_donustur(h, scaler)
    if varyant == "yuvarlama":  # gerilim 1 ondalik
        h = ham.copy()
        h[:, 2] = np.round(h[:, 2], 1)
        return ozellik_donustur(h, scaler)
    raise ValueError(varyant)


def deney(seed):
    rng = np.random.default_rng(seed)
    Xe, ye = uret(3000, rng)
    Xt, yt = uret(3000, rng)
    scaler = StandardScaler().fit(Xe)
    clf = LogisticRegression(max_iter=500).fit(
        ozellik_donustur(Xe, scaler), ye)
    sonuc = {}
    ref = clf.predict(ozellik_donustur(Xt, scaler))
    for v in VARYANTLAR:
        p = clf.predict_proba(servis_donusumu(Xt, scaler, v))[:, 1]
        sonuc[v] = (roc_auc_score(yt, p),
                    float(np.mean((p >= 0.5) != ref)))
    return sonuc
```

Deney her tohum için modeli eğitir, test kümesini dört farklı servis yolundan geçirir ve AUC ile tahmin değişimini ölçer. Tahmin değişimi, doğru yoldaki sınıfla servisteki sınıfın kaç örnekte farklı olduğunun oranıdır.

```python
if __name__ == "__main__":
    sonuclar = {seed: deney(seed) for seed in SEEDS}
    os.makedirs("calisma/veri", exist_ok=True)
    with open("calisma/veri/b77_servis_auc.csv", "w",
              encoding="utf-8") as f:
        f.write("varyant,tohum,auc,tahmin_degisimi\n")
        for seed in SEEDS:
            for v in VARYANTLAR:
                a, dg = sonuclar[seed][v]
                f.write("%s,%d,%.6f,%.6f\n" % (v, seed, a, dg))
    print("varyant      AUC(11)  AUC(22)  AUC(33)  ort.   tahmin")
    for v in VARYANTLAR:
        aucs = [sonuclar[s][v][0] for s in SEEDS]
        dg = np.mean([sonuclar[s][v][1] for s in SEEDS])
        print("%-12s %.4f   %.4f   %.4f   %.4f  %6.1f%%" %
              (v, aucs[0], aucs[1], aucs[2], np.mean(aucs), 100 * dg))
```

```term
$ python b77_servis.py
varyant      AUC(11)  AUC(22)  AUC(33)  ort.   tahmin
dogru        0.9600   0.9506   0.9533   0.9546     0.0%
olcek_yok    0.5276   0.5192   0.5534   0.5334    92.2%
birim        0.4990   0.5002   0.5004   0.4998    92.1%
yuvarlama    0.9313   0.9149   0.9159   0.9207     6.4%
```

Aynı sonuçlar Şekil 77.7'de tek bakışta görülür. Çubuklar üç tohumun ortalama AUC'sini, noktalar her tohumun değerini gösterir; kesikli çizgi rastgele tahminin değeridir.

![Şekil 77.7: Dört servis varyantının test AUC'si ve tahmin değişimi; rastgele tahmin 0,5'te gösterilmiştir](gorseller/b77_servis_carpikligi.png)

Sonuçlar dramatiktir. Doğru yolda ortalama AUC 0,955'tir. Sıcaklığı ölçeklemeyi unutmak AUC'yi 0,533'e düşürür, yani model rastgele tahmine yakın çalışır. Akımı miliamper olarak göndermek AUC'yi 0,500'e çeker. Bu rakam rastgele tahminin değeridir; model artık hiçbir bilgi taşımıyor. Gerilimi yuvarlamak ise 0,921'e düşürür, çünkü gerilimin standart sapması 0,05 V'tur ve bir ondalığa yuvarlamak bu özelliğin neredeyse tüm bilgisini siler. Ama diğer üç özellik hâlâ çalıştığı için kayıp sınırlı kalır.

Dikkat edilecek nokta, hiçbir durumda hata fırlatılmamasıdır. Tahmin değişimi, ölçek ve birim hatalarında yüzde 92'ye çıkıyor: servis edilen tahminlerin neredeyse tamamı doğru yoldan farklı. Yuvarlama hatasında bu oran yüzde 6'dır. Bu yüzden eğitim/servis çarpıklığını yakalamanın yolu, hem birim testlerinde aynı dönüşümü iki tarafta çağırmak hem de servisteki tahmin dağılımını izlemektir (77.9 ve 77.10). Bu bölümün test dosyasındaki `test_servis_olcek_yok_farkli`, ölçek bozulduğunda dönüşümün farklı sonuç verdiğini doğrular.

## 77.9 İzleme: model metrikleri ve sistem metrikleri

Bir modeli üretimde izlemek iki katmanlıdır. Birinci katman **sistem metrikleridir**: gecikme (p50, p95, p99 yüzdelikleri), hata oranı, bellek ve işlemci kullanımı. Bunlar bir web servisinin sağlığını gösterir ve Bölüm 41.11'deki gözlemlenebilirlik kavramıyla aynıdır. Yüzdelikleri ortalama yerine kullanmak, Bölüm 71.12'de gördüğümüz kuyruk davranışını yakalamak için gereklidir. İkinci katman **model metrikleridir**: girdi dağılımı, tahmin dağılımı ve performans.

Burada kritik bir ayrım vardır: bazı metrikler etiket gerektirmez, bazıları gerektirir. Bir İHA'nın arıza tahmininde gerçek arızanın ne zaman doğrulandığını bilmeden doğruluk ölçemezsin; belki bakım sonrasında, haftalar sonra öğrenirsin. Bu **etiket gecikmesi** sorunu, izlemeyi iki hıza ayırır: etiket beklemeden erken uyarı veren hızlı göstergeler (girdi ve tahmin dağılımı) ve etiket geldikçe performansı güncelleyen yavaş göstergeler.

| Ölçüt | Ne yakalar | Etiket gerekir mi | Örnek bir alarm |
|---|---|---|---|
| Gecikme p99 | Servis yavaşladı | Hayır | 50 ms'den 400 ms'ye |
| Hata oranı (5xx) | Servis çöktü | Hayır | Hata oranı yüzde 0,1'den yüzde 3'e |
| Girdi dağılımı (PSI) | Sensör ya da veri hattı değişti | Hayır | Sıcaklık ortalaması 2 °C arttı |
| Tahmin dağılımı | Model davranışı değişti | Hayır | Pozitif tahmin oranı yüzde 11'den yüzde 19'a |
| Performans (AUC, kalibrasyon) | Gerçek kalite düştü | Evet, gecikmeli | AUC 0,95'ten 0,92'ye |

Tablodaki son satır, Bölüm 57.7'de anlatılan kalibrasyonun izlemeye taşınmasıdır: tahminin olasılığı gerçek oranla uyuşmuyorsa, AUC hâlâ yüksek olsa bile karar eşiği yanlış çalışır. Tahmin dağılımı izlemesi bu tür sessiz değişimleri erken yakalar; etiketler gelmeden önce bile.

Bu bölümde bu izlemenin ilk iki satırını, yani girdi ve tahmin dağılımı ile gecikmeli performansı, kayma (drift) deneyleriyle uygulayacağız (77.10). Gecikme ve hata oranı için ayrı bir sistem ölçümü gerekir; bunu Bölüm 71.12'deki servis deneylerinde gördük ve burada tekrar etmiyoruz.

## 77.10 Kayma (drift): tanımlar, PSI, KS ve alan sınıflandırıcısı

Dağılım kayması, Bölüm 54.12'de bir uyarı olarak geçti; burada onu ölçmeyi öğreniyoruz. Olasılık dilinde üç tür ayırt edilir. Girdinin dağılımı `p(x)` değişip girdi ile etiket arasındaki ilişki `p(y|x)` aynı kalıyorsa buna **kovaryat kayması** denir. Sensör ısındığında sıcaklık dağılımı kayar, ama sıcaklığın arızaya etkisi değişmez. Etiketin dağılımı `p(y)` değişirse **etiket kayması** vardır; kış aylarında arıza oranı artabilir. İlişkinin kendisi `p(y|x)` değişirse **kavram kayması** vardır: aynı girdi artık başka bir sonuç verir, çünkü arızanın fiziği değişmiştir. Şekil 77.8 üç türü özetler.

![Şekil 77.8: Kayma türleri; kovaryat, etiket ve kavram kaymasının olasılıksal tanımları](gorseller/b77_drift_turleri.png)

Üç tür arasında en önemli fark, hangilerinin etiket olmadan görülebileceğidir. Kovaryat kayması yalnızca girdilere bakarak görülür. Kavram kayması ise girdi dağılımı değişmediği hâlde ortaya çıkabilir ve yalnızca etiketlerle ya da performansla görülür. Bu yüzden kayma izleyicisi tek bir ölçüt olamaz; her biri farklı bir türü yakalar.

Bu bölümde dört yöntem kullanıyoruz. Birincisi **PSI (Population Stability Index)** yani popülasyon kararlılık indeksidir. Referans dağılımı kuantillerine göre `k` kutuya böler, her kutudaki oranı referansta `e_i`, yeni pencerede `a_i` ile gösterir ve şöyle hesaplarız:

PSI = Σ (a_i − e_i) · ln(a_i / e_i)

Bu formülün her terimi iki oranın farkını ve oranlarının logaritmasını çarpar; sonuç her zaman sıfır veya pozitiftir ve iki yönde de aynıdır (a ile e'nin yer değiştirmesi değeri değiştirmez). Kredi skorlamadan gelen bir gösterge olduğu için yaygın eşikler vardır: 0,1 altı hafif, 0,2 üstü belirgin kayma (genel bilgi; eşik seçimi veriye bağlıdır ve aşağıda ölçülecek). PSI'yi elle hesaplamayı Örnek 1'de yapacağız.

İkincisi **KS (Kolmogorov–Smirnov) testidir**. İki örneğin ampirik birikimli dağılım fonksiyonları arasındaki en büyük mutlak farkı ölçer ve bu farkın şansla açıklanıp açıklanamayacağını bir p değeriyle verir. Python'da `scipy.stats.ks_2samp` bunu yapar; Kod Okuma bölümünde bu fonksiyonun içine bakacağız. KS her özellik için ayrı çalışır, bu yüzden dört özellik için dört test yapılır ve çoklu karşılaştırma nedeniyle eşik düşük tutulur.

Üçüncüsü **alan sınıflandırıcısıdır** (domain classifier). Referans örneğini "0", yeni pencereyi "1" olarak etiketleyip bir sınıflandırıcı eğitiriz. İki dağılım aynıysa sınıflandırıcı ayırt edemez ve AUC yaklaşık 0,5 çıkar. Dağılımlar farklıysa AUC yükselir. Bu yöntemin güzelliği, çok değişkenli kaymayı da yakalamasıdır: her özelliğin tek tek dağılımı aynı kalsa bile özellikler arasındaki ilişki değişmişse sınıflandırıcı bunu fark edebilir. Burada lojistik regresyon ve beş katlı çapraz doğrulama kullandık.

Dördüncüsü **performans izlemesidir**: model AUC'sini etiket geldikçe hesaplar ve referans değerin belli bir miktar altına düşüp düşmediğine bakar. Bu, kavram kaymasını yakalayan tek yöntemdir ve etiket gecikmesi (77.9) nedeniyle yavaştır.

Deneyin tasarımı şöyledir. Eğitim dağılımından bir model eğitilir ve donar. Her biri 600 örnekli 120 pencere üretilir. 60. pencereden itibaren sıcaklık dağılımı 2 °C ötelenir (kovaryat kayması). 90. pencereden itibaren sıcaklığın katsayısı 0,25'ten 0,60'a çıkar (kavram kayması); bu durumda girdi dağılımı aynı kalır. Etiketler beş pencere gecikmeli gelir. Kayma büyüklüklerini bilerek ılımlı seçtik: ilk denemede sıcaklık ötelemesi 6 °C'ydi ve PSI eşiğinin hangi değerde olduğunun bir önemi kalmamıştı. Ölçeği küçültünce eşik seçiminin etkisi görünür oldu. Bu bir tasarım seçimidir; gerçek bir sistemde kaymanın büyüklüğü önceden bilinmez.

```python
# -*- coding: utf-8 -*-
"""Kayma (drift) tespiti: PSI, KS ve alan siniflandiricisi.

Sentetik bir akis uzerinde: 60. pencerede ortam kaymasi (kovaryat),
90. pencerede kavram kaymasi (etiket iliskisi) baslar. Etiketler 5
pencere gecikmeli gelir. Her yontem icin yanlis alarm orani ve tespit
gecikmesi 3 tohumla olculur.
"""
import csv
import os

import numpy as np
from scipy.stats import ks_2samp
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from b77_telemetri import model_kur, uret

SEEDS = [11, 22, 33]
PENCERE = 600           # her pencerede ornek sayisi
W = 120                 # toplam pencere
KAYMA_BAS = 60          # ortam kaymasi (kovaryat)
KAYMA_ARTIS = 2.0       # sicaklik dagiliminin otelenmesi (C)
KAVRAM_BAS = 90         # etiket iliskisi kaymasi
KAVRAM_ARTIS = 0.35     # sicaklik katsayisi 0,25 -> 0,60
GECIKME = 5             # etiketler 5 pencere sonra gelir
PSI_ESIK = 0.2
KS_ESIK = 0.01
ALAN_ESIK = 0.6
PERF_DUSUS = 0.05
YONTEMLER = ["a_psi", "a_ks", "a_alan", "a_perf"]
```

```python
def psi(ref, yeni, kutu=10):
    """Populasyon Kararlilik Indeksi: referans kuantillerine gore."""
    kenar = np.quantile(ref, np.linspace(0, 1, kutu + 1))
    kenar[0], kenar[-1] = -np.inf, np.inf
    e = np.histogram(ref, kenar)[0] / len(ref)
    a = np.histogram(yeni, kenar)[0] / len(yeni)
    e, a = np.clip(e, 1e-4, None), np.clip(a, 1e-4, None)
    return float(np.sum((a - e) * np.log(a / e)))


def alan_auc(ref, yeni, rng):
    """Referans mi, yeni pencere mi? Ayirt edilemiyorsa AUC ~ 0,5."""
    X = np.vstack([ref, yeni])
    y = np.r_[np.zeros(len(ref)), np.ones(len(yeni))]
    cv = StratifiedKFold(5, shuffle=True,
                         random_state=int(rng.integers(10**6)))
    m = make_pipeline(StandardScaler(),
                      LogisticRegression(max_iter=500))
    skor = cross_val_predict(m, X, y, cv=cv, method="predict_proba")
    return roc_auc_score(y, skor[:, 1])
```

`psi` fonksiyonu, referans kuantillerinden kutu sınırları çıkarır ve iki histogramın oranlarını karşılaştırır. Sıfır oranları önlemek için 0,0001 alt sınırı kullanılır; bu, logaritmanın tanımsız olmasını engeller. `alan_auc` ise yukarıda anlatılan sınıflandırıcı testidir.

```python
def akis(seed):
    """Bir tohum icin W pencerelik akis; satir listesi doner."""
    rng = np.random.default_rng(seed)
    X0, y0 = uret(4000, rng)
    model = model_kur().fit(X0, y0)           # egitim dagilimi, donuk
    ref, _ = uret(2000, rng)     # referans: egitim dagilimi
    aucs, satirlar = [], []
    ref_auc = None
    for w in range(W):
        ortam = KAYMA_ARTIS if w >= KAYMA_BAS else 0.0
        kat = KAVRAM_ARTIS if w >= KAVRAM_BAS else 0.0
        X, y = uret(PENCERE, rng, ortam, kat)
        p = model.predict_proba(X)[:, 1]
        aucs.append(roc_auc_score(y, p))
        psis = [psi(ref[:, j], X[:, j]) for j in range(4)]
        kss = [ks_2samp(ref[:, j], X[:, j]).pvalue for j in range(4)]
        alan = alan_auc(ref[:PENCERE], X, rng)
        # Gecikmeli performans: pencere t'nin etiketi simdi geldi.
        t = w - GECIKME
        if ref_auc is None and t >= 9:
            ref_auc = float(np.mean(aucs[:10]))
        perf = ref_auc is not None and t >= 10 and \
            aucs[t] < ref_auc - PERF_DUSUS
        satirlar.append({
            "tohum": seed, "pencere": w,
            "psi_max": max(psis), "ks_min_p": min(kss),
            "alan_auc": alan, "auc": aucs[-1],
            "a_psi": max(psis) > PSI_ESIK,
            "a_ks": min(kss) < KS_ESIK,
            "a_alan": alan > ALAN_ESIK, "a_perf": perf})
    return satirlar
```

`akis` fonksiyonu bir tohum için 120 pencereyi üretir ve her pencere için dört yöntemin ölçümünü bir satır olarak kaydeder. Performans alarmı, referans AUC'yi ilk on pencereden hesaplar ve beş pencere gecikmeyle gelen etiketi kullanır. Alarm eşiği 0,05 düşüş olarak seçildi.

```python
def ilk_alarm(satirlar, anahtar, bas, son=W):
    """[bas, son) araligindaki ilk alarm penceresi; yoksa None."""
    for s in satirlar:
        if bas <= s["pencere"] < son and s[anahtar]:
            return s["pencere"]
    return None


def yontem_ozeti(satirlar):
    """Yontem basina: yanlis alarm orani, iki tespit gecikmesi."""
    sonuc = []
    for yontem in YONTEMLER:
        once = [s[yontem] for s in satirlar
                if s["pencere"] < KAYMA_BAS]
        g1 = ilk_alarm(satirlar, yontem, KAYMA_BAS, KAVRAM_BAS)
        g2 = ilk_alarm(satirlar, yontem, KAVRAM_BAS)
        sonuc.append((yontem, float(np.mean(once)),
                      None if g1 is None else g1 - KAYMA_BAS,
                      None if g2 is None else g2 - KAVRAM_BAS))
    return sonuc


def yaz(yol, satirlar):
    with open(yol, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        w.writerows(satirlar)
```

```python
if __name__ == "__main__":
    os.makedirs("calisma/veri", exist_ok=True)
    tum, tohum_satir = [], {}
    for seed in SEEDS:
        tohum_satir[seed] = akis(seed)
        tum.extend(tohum_satir[seed])
    yaz("calisma/veri/b77_drift_seri.csv", tum)

    print("tohum  AUC(0-59)  AUC(90-119)")
    for seed in SEEDS:
        s = tohum_satir[seed]
        a1 = np.mean([r["auc"] for r in s if r["pencere"] < 60])
        a2 = np.mean([r["auc"] for r in s if r["pencere"] >= 90])
        print("%-6d %.4f    %.4f" % (seed, a1, a2))

    print("yontem   yanlis-alarm  kayma-gecikme   kavram-gecikme")
    ozetler = {seed: yontem_ozeti(tohum_satir[seed])
               for seed in SEEDS}
    for k, yontem in enumerate(YONTEMLER):
        fa = np.mean([ozetler[s][k][1] for s in SEEDS])
        g1 = [ozetler[s][k][2] for s in SEEDS]
        g2 = [ozetler[s][k][3] for s in SEEDS]
        print("%-8s %-13.3f %-15s %s" % (yontem, fa, g1, g2))

    print("PSI esigi  yanlis-alarm  kayma-gecikme (3 tohum)")
    for esik in [0.05, 0.1, 0.2, 0.3]:
        fa, gec = [], []
        for seed in SEEDS:
            s = tohum_satir[seed]
            fa.append(np.mean([r["psi_max"] > esik for r in s
                               if r["pencere"] < KAYMA_BAS]))
            ilk = [r["pencere"] for r in s
                   if r["pencere"] >= KAYMA_BAS
                   and r["psi_max"] > esik]
            gec.append(ilk[0] - KAYMA_BAS if ilk else None)
        print("%-10.2f %-13.3f %s" % (esik, np.mean(fa), gec))
```

Betik üç tohumla çalışır. Önce her tohum için iki dönem AUC'sini basar. Sonra dört yöntemin yanlış alarm oranını ve iki tespit gecikmesini özetler. Son olarak PSI eşiğinin etkisini ayrı bir tabloda gösterir.

```term
$ python b77_drift.py
tohum  AUC(0-59)  AUC(90-119)
11     0.9521    0.9259
22     0.9539    0.9160
33     0.9523    0.9229
yontem   yanlis-alarm  kayma-gecikme   kavram-gecikme
a_psi    0.000         [0, 0, 0]       [0, 1, 0]
a_ks     0.067         [0, 0, 0]       [0, 0, 0]
a_alan   0.000         [0, 0, 0]       [0, 0, 0]
a_perf   0.000         [None, None, None] [26, 6, None]
PSI esigi  yanlis-alarm  kayma-gecikme (3 tohum)
0.05       0.044         [0, 0, 0]
0.10       0.000         [0, 0, 0]
0.20       0.000         [0, 0, 0]
0.30       0.000         [12, None, 15]
```

Çıktıyı üç açıdan okumak gerekir. Birincisi, model AUC'si kayma öncesinde 0,952-0,954 ve kavram kayması sonrasında 0,916-0,926 aralığındadır. Düşüş yaklaşık 0,03'tür; küçük, ama gerçek. İkincisi, yanlış alarm oranı PSI, alan sınıflandırıcısı ve performans için sıfırdır; KS için yüzde 6,7'dir. KS'nin daha fazla yanlış alarm vermesinin bir nedeni, referans örneğinin tüm pencerelerde aynı kalmasıdır; böylece pencereler arasında bağımlılık oluşur (bu bir yorumdur, kesin bir kanıt değil). Üçüncüsü, ortam kaymasını üç yöntem de hemen yakalar: PSI, KS ve alan sınıflandırıcısı, 60. pencerede tespit gecikmesi sıfırdır.

Kavram kaymasında tablo farklı konuşur. Performans alarmı üç tohumun ikisinde 90. pencereden sonra 26 ve 6 pencere gecikmeyle ateşledi; üçüncü tohumda hiç ateşlemedi. Üstelik PSI ve alan sınıflandırıcısı, kavram kaymasında "tespit" gibi görünen değerler verdi. Bu değerler, kavram kaymasını değil, 60. pencerede başlayan ortam kaymasının süren etkisini yansıtır; PSI bu süre boyunca eşiğin çevresinde dalgalanır. Yani kavram kaymasının gerçek bir tespiti yalnızca performans alarmından gelir ve bu alarm yavaştır.

PSI eşiğinin tablosu tasarım tercihini gösterir. Eşik 0,05'e indiğinde yanlış alarm yüzde 4,4'e çıkar; 0,1 ve 0,2'de yanlış alarm sıfırdır ve tespit anındadır; 0,3'te ise üç tohumun birinde kayma hiç tespit edilmez, diğerlerinde 12 ve 15 pencere gecikme olur. Bu eğri, eşik seçiminin bir ödünleşim (trade-off) olduğunu gösterir: düşük eşik yanlış alarm, yüksek eşik kaçırma getirir. Bu deneyde 0,2 makul bir seçimdir, ama bu sonuç yalnızca bu veriye ve bu kayma büyüklüğüne aittir.

Şekil 77.9 aynı akışı tohum 11 için çizer: üstte PSI'nin zaman içindeki değeri ve eşikler, altta alan sınıflandırıcısının AUC'si ile model AUC'si. Model AUC'sinin 90. pencereden sonraki hafif düşüşü, gözle bile seçilebilir ama tek bir eşikle yakalanamayacak kadar küçüktür.

![Şekil 77.9: Tohum 11 için PSI, alan sınıflandırıcısı AUC'si ve model AUC'si; kaymaların başlangıcı çizgilerle gösterilmiştir](gorseller/b77_drift_akis.png)

## 77.11 Yeniden eğitim politikaları: zamanlanmış mı, tetiklemeli mi?

Kayma tespit edildiğinde modeli yeniden eğitmek gerekir. Ama ne zaman? İki temel politika vardır. **Zamanlanmış** politikada yeniden eğitim her `n` pencerede bir yapılır, kayma olsun olmasın. **Tetiklemeli** politikada yeniden eğitim yalnızca bir alarm geldiğinde yapılır. Zamanlanmış politika basittir ama gereksiz eğitim maliyeti yaratabilir. Tetiklemeli politika verimlidir ama alarmın kalitesine bağlıdır; kaçırılan bir kayma, bütün maliyeti doğrudan bozulmaya çevirir.

Bu karar bir maliyet modeliyle verilmelidir (Bölüm 57.1'deki hata maliyeti düşüncesi). Simülasyonda yanlış negatif bir hatanın maliyeti 5, yanlış pozitifin maliyeti 1 birim; her yeniden eğitimin maliyeti 60 birim. Kayma kademelidir: ortam 20. pencerede başlar ve 100. pencerede tam +6 °C'ye ulaşır; kavram kayması 40. pencerede başlar ve katsayıyı 120. pencereye doğru +0,30'a kadar artırır. Etiketler beş pencere gecikmeli gelir. Dört politika karşılaştırılır: hiç yeniden eğitim yok, her 10 pencerede bir, her 30 pencerede bir ve performans alarmıyla tetiklemeli (son altı etiketli pencereyle eğitim, 10 pencerelik soğuma süresi).

Modelin kendisi değişmez; sadece kayma ve politika değişir. Bu yüzden çıktı yalnızca politikanın kararlarının sonucunu gösterir.

```python
# -*- coding: utf-8 -*-
"""Yeniden egitim politikalari: maliyet simulasyonu (3 tohum).

Kayma kademeli: ortam 20. pencerede baslar (en fazla +6 C), kavram
kaymasi 40. pencerede baslar (katsayi en fazla +0,30). Etiketler 5
pencere gecikmeli gelir. Maliyet: yanlis negatif 5, yanlis pozitif 1,
her yeniden egitim 60 birim.
"""
import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from b77_telemetri import uret

SEEDS = [11, 22, 33]
PENCERE = 300
W = 120
GECIKME = 5
FN, FP, EGITIM = 5.0, 1.0, 60.0
PERF_DUSUS = 0.05
POLITIKALAR = [("hic", None, False), ("her_10", 10, False),
               ("her_30", 30, False), ("tetikli", None, True)]
```

```python
def ortam(w):
    return 6.0 * min(1.0, max(0.0, (w - 20) / 80))


def katsayi(w):
    return 0.30 * min(1.0, max(0.0, (w - 40) / 80))


def egit(X, y):
    sc = StandardScaler().fit(X)
    lr = LogisticRegression(max_iter=500)
    return sc, lr.fit(sc.transform(X), y)


def tahmin(model, X):
    sc, m = model
    return m.predict_proba(sc.transform(X))[:, 1]
```

```python
def calistir(seed, periyot, tetikli):
    rng = np.random.default_rng(seed)
    model = egit(*uret(PENCERE * 10, rng))
    aucs, gecmis = [], []
    maliyet, yeniden = 0.0, 0
    ref_bas, ref_auc, bekleme = 0, None, -1
    for w in range(W):
        X, y = uret(PENCERE, rng, ortam(w), katsayi(w))
        p = tahmin(model, X)
        pred = p >= 0.5
        maliyet += FN * np.sum(~pred & (y == 1))
        maliyet += FP * np.sum(pred & (y == 0))
        aucs.append(roc_auc_score(y, p))
        gecmis.append((X, y))
        t = w - GECIKME    # etiketi simdi gelen pencere
        if ref_auc is None and t >= ref_bas + 9:
            ref_auc = float(np.mean(aucs[ref_bas:ref_bas + 10]))
        tetik = periyot is not None and w > 0 and w % periyot == 0
        if tetikli and ref_auc is not None and t >= ref_bas + 10 \
                and w >= bekleme and aucs[t] < ref_auc - PERF_DUSUS:
            tetik = True
        if tetik and t >= 5:                 # son 6 etiketli pencere
            Xs = np.vstack([g[0] for g in gecmis[t - 5:t + 1]])
            ys = np.concatenate([g[1] for g in gecmis[t - 5:t + 1]])
            model = egit(Xs, ys)
            maliyet += EGITIM
            yeniden += 1
            ref_bas, ref_auc, bekleme = w + 1, None, w + 10
    return maliyet, float(np.mean(aucs)), yeniden


if __name__ == "__main__":
    print("politika  maliyet (ort +- ss)  AUC (ort)  yeniden")
    for ad, periyot, tetikli in POLITIKALAR:
        s = [calistir(seed, periyot, tetikli) for seed in SEEDS]
        m = np.array([x[0] for x in s])
        print("%-9s %9.0f +- %-7.0f     %.4f      %.1f" %
              (ad, m.mean(), m.std(ddof=1),
               np.mean([x[1] for x in s]),
               np.mean([x[2] for x in s])))
```

Politikanın mantığı `calistir` fonksiyonunda. Her pencerede modelin tahminleri maliyete çevrilir, AUC kaydedilir ve pencere geçmişe eklenir. Tetiklemeli politika, referans AUC'yi kendi son eğitiminden sonraki ilk on pencereden hesaplar; böylece referans her yeniden eğitimde sıfırlanır. Yeniden eğitim, en son altı etiketli pencereyle yapılır ve o andan sonra on pencere boyunca yeni bir eğitim yapılmaz.

```term
$ python b77_yeniden_egitim.py
politika  maliyet (ort +- ss)  AUC (ort)  yeniden
hic           25161 +- 956         0.9417      0.0
her_10        15098 +- 314         0.9500      11.0
her_30        16953 +- 148         0.9483      3.0
tetikli       22172 +- 4342        0.9440      0.7
```

Tablo üç tohumun ortalamasını ve standart sapmasını gösterir. Hiç yeniden eğitmemek en pahalı politikadır: ortalama maliyet 25161, AUC 0,942. Her 10 pencerede bir eğitmek en düşük maliyeti verir (15098), AUC 0,950 ile en yüksek ortalamayı da sağlar ve 11 kez yeniden eğitir. Her 30 pencerede bir ise 16953 maliyetle yakın bir sonuç verir; yalnızca 3 kez eğitir. Tetiklemeli politika ise hem en pahalı ikinci hem de en değişken sonucu verir (22172 ± 4342) ve ortalama yalnızca 0,7 kez yeniden eğitir.

Tetiklemeli politikanın başarısızlığı kayma hızıyla ilgilidir. Kayma yavaş olduğu için AUC her pencerede çok az düşer ve 0,05'lik eşik ancak geç aşılır. Ayrıca bu eşik her tohumda bir kez bile ateşlemeyebilir. Çözüm, eşiği düşürmek ya da bir kayma göstergesini (PSI) yeniden eğitimin ön koşulu yapmaktır; ama her iki seçenek de yanlış alarm riskini artırır. Yani bu simülasyon, en iyi politikanın kaymanın hızına ve maliyet oranına bağlı olduğunu gösterir. Kesin bir "şunu yap" cevabı yoktur. Maliyet birimleri kurgusaldır; gerçek bir ekipte bu değerleri üretim verisinden ve iş kaybından ölçmek gerekir.

## 77.12 Sorumluluk, uyum ve savunma bağlamı

Bir modelin çalıştırılması kadar, neden ve nasıl çalıştığının belgelenmesi de bir mühendislik işidir. **Model kartı** (Mitchell ve arkadaşları, 2019; genel bilgi) bir modelin amacını, eğitim verisinin özetini, performansını alt gruplara göre ve bilinen sınırlarını tek bir belgede toplar. Bölüm 54.12'de yanlılık ve dağılım kaymasının bu belgenin parçaları olduğunu gördük. **Veri sayfası** (datasheet; Gebru ve arkadaşları, 2018; genel bilgi) aynı mantığı veri setine uygular: veri nasıl toplandı, kimleri içerir, hangi amaçla kullanılmamalıdır.

Bu belgeler bir **denetim izi** (audit trail) ile birleştiğinde anlamlı olur. Denetim izi, bir modelin her yaşam döngüsü olayını kaydeder: kim hangi kod sürümünü eğitti, hangi veri özetiyle, hangi tohumla, hangi kalite kapısı sonucuyla, hangi onayla üretime alındı. Bu bölümde yazdığımız deney takipçisi, kayıt defteri ve kapı bu izin çekirdeğidir. Eksik olan şey imza ve kimlik doğrulamasıdır; gerçek bir sistemde bu kayıtlar değiştirilemez bir depoya yazılmalı ve kayıt sahibi doğrulanabilmelidir.

Savunma bağlamında üç kısıt bu tasarımı zorlaştırır. Birincisi **hava boşluklu (air-gapped) ortamdır**: eğitim ve üretim ağı internete bağlı değildir. Paketler yerel bir depodan kurulur ve kilit dosyası, kaynak kodu ve modelle birlikte özetleriyle taşınır. Bölüm 71.13'te yerel ve hava boşluklu LLM kurulumlarının aynı sorunu taşıdığını görmüştük. İkincisi **sürüm izlenebilirliğidir**: bir uçuşta hangi modelin çalıştığı, o modelin hangi veriyle ve hangi kodla üretildiği, bir kaza ya da arıza incelemesinde cevaplanabilmelidir. Üçüncüsü **güvenli yükleme** kuralıdır: model dosyası güvenilmeyen bir kaynaktan geliyorsa yüklenmez; bu bölümde `pickle` tabanlı bir yükleme yaptığımızı ve bunun neden risk olduğunu gördük.

Bu kısıtlar, bir modelin "çalıştığını" göstermenin yetmediğini söyler. Havacılık ve savunma yazılımında doğrulama ve sertifikasyon süreçleri, bir sistemin hangi koşullarda güvenle çalıştığını kanıtlamayı ister (genel bilgi). ML bileşenlerinin bu süreçlere nasıl girdiği, belirsizlik tahmini, dayanıklılık ve açıklanabilirlik ile birlikte Bölüm 78'in konusudur. Bu bölümde kurduğumuz izlenebilirlik zinciri, o sertifikasyon tartışmasının ön koşuludur.

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

```python
# -*- coding: utf-8 -*-
"""Ornek 1: PSI'nin elle hesabi (dort kutu, kagit kalemiyle)."""
import math

e = [0.25, 0.25, 0.25, 0.25]    # referans oranlari
a = [0.40, 0.30, 0.20, 0.10]    # yeni pencerenin oranlari
terimler = [(ai - ei) * math.log(ai / ei) for ai, ei in zip(a, e)]
for k, t in enumerate(terimler, 1):
    print("kutu %d: (a-e) ln(a/e) = %+.4f" % (k, t))
print("PSI = %.4f" % sum(terimler))
```

```term
$ python b77_ornek1.py
kutu 1: (a-e) ln(a/e) = +0.0705
kutu 2: (a-e) ln(a/e) = +0.0091
kutu 3: (a-e) ln(a/e) = +0.0112
kutu 4: (a-e) ln(a/e) = +0.1374
PSI = 0.2282
```

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

```python
# -*- coding: utf-8 -*-
"""Ornek 2: veri hash'i degisince hangi deneyler gecersiz olur?"""
import os
import shutil

import numpy as np

from b77_takip import Takip, csv_oku, csv_yaz
from b77_telemetri import uret
from b77_veri import ekle

K = "calisma/ornek2"
HAM, OZEL = K + "/ham.csv", K + "/ozellik.csv"
```

```python
def turet():
    """Turetilmis veri: sicaklik sensorunun tavanina kirpar."""
    X, y = csv_oku(HAM)
    X[:, 0] = np.clip(X[:, 0], 22, 38)
    csv_yaz(OZEL, X, y)
    return ekle(OZEL)


shutil.rmtree(K, ignore_errors=True)
os.makedirs(K)
csv_yaz(HAM, *uret(1500, np.random.default_rng(1)))
h1 = ekle(HAM)
o1 = turet()
soy = {o1: h1}                        # turev ozeti -> kaynak ozeti

takip = Takip(K + "/takip.db")
for C in [0.1, 1.0, 10.0]:
    d = takip.baslat("lojistik", o1, "calisma/kod")
    takip.parametre(d, {"C": C})
print("deneyler v1 turevi ile kaydedildi:", o1[:8])

# ham veriye bir satir eklenir
with open(HAM, "a", encoding="utf-8") as f:
    f.write("31.0,10.0,3.7,100,0\n")
h2 = ekle(HAM)
o2 = turet()
soy[o2] = h2
print("ham veri: %s -> %s" % (h1[:8], h2[:8]))
print("turev   : %s -> %s" % (o1[:8], o2[:8]))
print("v1 turevinin kaynagi hala guncel mi:", soy[o1] == h2)
print("guncel veriyle gecersiz deneyler:")
for did, ad in takip.gecersiz(o2):
    print("   deney %d (%s) veri=%s" % (did, ad, o1[:8]))
```

```term
$ python b77_ornek2.py
deneyler v1 turevi ile kaydedildi: 2b89f8a9
ham veri: e648480f -> 8314eb06
turev   : 2b89f8a9 -> 3c79b170
v1 turevinin kaynagi hala guncel mi: False
guncel veriyle gecersiz deneyler:
   deney 1 (lojistik) veri=2b89f8a9
   deney 2 (lojistik) veri=2b89f8a9
   deney 3 (lojistik) veri=2b89f8a9
```

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

```python
# -*- coding: utf-8 -*-
"""Kanarya / A-B: gereken ornek sayisi, formul ve simulasyon.

Iki esit kol (taban ve aday), her koldan n istek. Hata oranlari
p0 ve p1. Iki oranli z-testi, iki yonlu alfa = 0,05.
"""
import math

import numpy as np
from scipy.stats import norm


def gerekli_n(p0, p1, alfa=0.05, guc=0.8):
    """Her kol icin ornek sayisi (iki oranli z-testi formulu)."""
    za = norm.ppf(1 - alfa / 2)
    zb = norm.ppf(guc)
    pb = (p0 + p1) / 2
    pay = (za * math.sqrt(2 * pb * (1 - pb))
           + zb * math.sqrt(p0 * (1 - p0) + p1 * (1 - p1)))
    return math.ceil(pay ** 2 / (p1 - p0) ** 2)
```

```python
def guc_sim(p0, p1, n, alfa=0.05, deneme=20000, seed=0):
    """Ayni testi simule ederek tespit olasiligini olcer."""
    rng = np.random.default_rng(seed)
    x0 = rng.binomial(n, p0, deneme) / n
    x1 = rng.binomial(n, p1, deneme) / n
    pb = (x0 + x1) / 2
    se = np.sqrt(pb * (1 - pb) * 2 / n)
    z = np.abs(x1 - x0) / np.where(se > 0, se, np.inf)
    return float(np.mean(z > norm.ppf(1 - alfa / 2)))


if __name__ == "__main__":
    print("senaryo               n (formul)  guc (formul)  guc (sim)")
    for p0, p1 in [(0.05, 0.06), (0.05, 0.055), (0.05, 0.07)]:
        n = gerekli_n(p0, p1)
        print("p0=%.3f p1=%.3f   %-11d 0.800         %.3f" %
              (p0, p1, n, guc_sim(p0, p1, n)))
    n = gerekli_n(0.05, 0.06)
    print("--- n yarisina inerse (p0=0.05, p1=0.06)")
    yari = n // 2
    print("n=%d guc(sim)=%.3f" % (yari, guc_sim(0.05, 0.06, yari)))
    print("--- sahte alarm: p0=p1=0.05 (fark yok)")
    print("alfa(sim)=%.3f" % guc_sim(0.05, 0.05, n))
```

Modülün kendi çıktısı, aşağıdaki sonuçların kaynağıdır:

```term
$ python b77_ab.py
senaryo               n (formul)  guc (formul)  guc (sim)
p0=0.050 p1=0.060   8158        0.800         0.801
p0=0.050 p1=0.055   31234       0.800         0.801
p0=0.050 p1=0.070   2213        0.800         0.802
--- n yarisina inerse (p0=0.05, p1=0.06)
n=4079 guc(sim)=0.508
--- sahte alarm: p0=p1=0.05 (fark yok)
alfa(sim)=0.049
```

Simülasyonun gücü formülle uyuşuyor (0,80). Aşağıdaki betik iki senaryoyu çalıştırır.

```python
# -*- coding: utf-8 -*-
"""Ornek 3: kanarya icin gereken ornek ve gun sayisi."""
import math

from b77_ab import gerekli_n, guc_sim

GUNLUK = 100000       # gunluk toplam istek
KOL_PAYI = 0.02       # her kola gunun yuzde 2'si

for p0, p1 in [(0.05, 0.06), (0.05, 0.055)]:
    n = gerekli_n(p0, p1)
    gun = math.ceil(n / (GUNLUK * KOL_PAYI))
    print("p0=%.3f p1=%.3f: n=%d, gun=%d, sim guc=%.3f" %
          (p0, p1, n, gun, guc_sim(p0, p1, n)))
```

```term
$ python b77_ornek3.py
p0=0.050 p1=0.060: n=8158, gun=5, sim guc=0.801
p0=0.050 p1=0.055: n=31234, gun=16, sim guc=0.801
```

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

```python
# -*- coding: utf-8 -*-
"""Uretim hatasinda kok neden analizi: simule edilmis gunluk kayitlar.

Senaryo: 40. gunde cihazlarin %30'unda (firmware v2) sicaklik sensoru
bazen okunamiyor. Yeni seri hatti eksik degeri 0,0 yaziyor. Model bu
degeri sicaklik = 0 C sanip dusuk risk tahmin ediyor. Kok nedeni
bulmak icin dort kontrol yapiyoruz. Tohum: 7.
"""
import numpy as np
from sklearn.metrics import roc_auc_score

from b77_drift import psi
from b77_telemetri import model_kur, uret

SEED = 7
GUN = 60
KIRILMA = 40
GUNLUK = 300
```

```python
def gunlukler():
    """Her satir bir kayit: gun, cihaz, firmware, ham girdi (4 sutun),
    gercek etiket ve model tahmini. Ham girdi, seri hattindan sonra
    kaydedilen degerdir."""
    rng = np.random.default_rng(SEED)
    egitim = model_kur().fit(*uret(4000, rng))
    satirlar = []
    for gun in range(GUN):
        X, y = uret(GUNLUK, rng)
        cihaz = rng.integers(0, 100, GUNLUK)
        v2 = cihaz >= 70
        bozuk = v2 & (gun >= KIRILMA) & (rng.random(GUNLUK) < 0.5)
        Xk = X.copy()
        Xk[bozuk, 0] = 0.0              # seri hattinin hatasi
        p = egitim.predict_proba(Xk)[:, 1]
        satirlar.append(np.column_stack([
            np.full(GUNLUK, gun), cihaz, v2, Xk, y, p]))
    return egitim, np.vstack(satirlar)
```

```python
if __name__ == "__main__":
    egitim, D = gunlukler()
    gun, v2, sic = D[:, 0], D[:, 2] == 1, D[:, 3]
    y, p = D[:, 7], D[:, 8]
    once, sonra = gun < KIRILMA, gun >= KIRILMA
    ref = sic[once]

    print("1) Genel performans (AUC)")
    print("   40. gune kadar: %.4f" % roc_auc_score(y[once], p[once]))
    print("   40. gunden sonra: %.4f" %
          roc_auc_score(y[sonra], p[sonra]))

    print("2) Ortam kaymasi mi? (PSI, sicaklik, referans 0-39. gun)")
    print("   tum cihazlar : %.3f" % psi(ref, sic[sonra]))
    print("   yalniz v1    : %.3f" % psi(sic[once & ~v2],
                                       sic[sonra & ~v2]))
    print("   yalniz v2    : %.3f" % psi(sic[once & v2],
                                       sic[sonra & v2]))

    print("3) Sicaklik = 0,0 orani (sensor okunamadi isareti)")
    grup = [("v1, 0-39", once & ~v2), ("v2, 0-39", once & v2),
            ("v1, 40-59", sonra & ~v2), ("v2, 40-59", sonra & v2)]
    for ad, kume in grup:
        print("   %-10s : %.3f" % (ad, np.mean(sic[kume] == 0.0)))

    print("4) Cevrimdisi yeniden hesap farki (serving - offline)")
    yeniden = egitim.predict_proba(D[:, 3:7])[:, 1]
    print("   en buyuk fark: %.2e" % np.max(np.abs(yeniden - p)))

    print("5) Hata nerede? (40-59. gunler, gercek pozitifler)")
    poz = sonra & (y == 1)
    sifir = poz & (sic == 0.0)
    print("   sicaklik=0 olan pozitiflerde kacirma: %.3f" %
          np.mean(p[sifir] < 0.5))
    print("   diger pozitiflerde kacirma        : %.3f" %
          np.mean(p[poz & ~(sic == 0.0)] < 0.5))
    print("   referans (0-39. gun) kacirma      : %.3f" %
          np.mean(p[once & (y == 1)] < 0.5))
```

```term
$ python b77_kok_neden.py
1) Genel performans (AUC)
   40. gune kadar: 0.9552
   40. gunden sonra: 0.8189
2) Ortam kaymasi mi? (PSI, sicaklik, referans 0-39. gun)
   tum cihazlar : 0.139
   yalniz v1    : 0.004
   yalniz v2    : 1.078
3) Sicaklik = 0,0 orani (sensor okunamadi isareti)
   v1, 0-39   : 0.000
   v2, 0-39   : 0.000
   v1, 40-59  : 0.000
   v2, 40-59  : 0.495
4) Cevrimdisi yeniden hesap farki (serving - offline)
   en buyuk fark: 0.00e+00
5) Hata nerede? (40-59. gunler, gercek pozitifler)
   sicaklik=0 olan pozitiflerde kacirma: 1.000
   diger pozitiflerde kacirma        : 0.444
   referans (0-39. gun) kacirma      : 0.437
```

**Bunu AI'sız yazabilir misin?** Eksik değerleri `NaN` olarak bırakan bir servis hattı yazdığını düşün. Model `NaN` aldığında ne yapar? Bu davranışı yakalayan tek bir birim testi yaz ve hangi girdiyle başarısız olacağını söyle.

## Kendin Yap Projeleri

::: dikkat
Bu iki projeyi yapay zekâ aracı olmadan yap. Önce kağıt üzerinde tasarımı çiz, veri akışını elle izle, sonra kodla. MLflow ya da DVC gibi hazır araçları kullanma; amacın bu bölümün küçük araçlarını genişletmek ve bunun neden zor olduğunu görmek.
:::

### Proje 1 (★★): Veri kökeni (lineage) izleyicisi

**Amaç.** Türev verilerin hangi ham verilerden üretildiğini kaydeden, ham veri değiştiğinde eskiyen türevleri ve onlara bağlı deneyleri bulan bir araç yazmak.

**Yapılacaklar / beklenen davranış.** Her türev dosya için üst dosyaların özetlerini ve üretim betiğinin commit kimliğini tutan bir `kaynak` tablosu oluştur. Bu bağlardan bir yönlü çevrimsiz graf (DAG) kur. Zincirin herhangi bir düğümü değiştiğinde, o düğümden erişilebilen bütün alt düğümleri "eskidi" olarak işaretle. Deney takipçisindeki `veri` alanının zincirdeki hangi düğüme karşılık geldiğini de gösterebilmelisin. Üç katmanlı bir zincir (ham, temiz, özellik) ile sına.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Düğümleri özetleriyle adresle, kenarları `(ust_ozet, alt_ozet, betik_commit)` üçlüsü olarak tut. Eskime taraması için Bölüm 17'deki DFS ya da topolojik sıralama doğrudan kullanılabilir. Döngü olmadığını varsay ama bir kez kontrol et; kontrol edilmeyen döngü sonsuz taramaya yol açar.

**Başarı kriterleri.** (a) Üç katmanlı zincirde ham dosyanın tek bir baytı değiştiğinde alt iki katman eskidi olarak işaretlenir ve ilgisiz bir dosya işaretlenmez. (b) Türev yeniden üretildiğinde sonucun özeti beklenen özetle eşleşir. (c) En az 20 rastgele zincirde, her biri için beklenen eskime kümesi elle hesaplanmış kümeyle birebir aynıdır. (d) Kod 70 sütunu aşmaz ve testleri vardır.

### Proje 2 (★★★): İHA telemetri modeli için uçtan uca izleme ve yeniden eğitim hattı

**Amaç.** Bu bölümdeki parçaları (77.4'ten 77.11'e kadar) tek bir çalıştırılabilir hatta birleştirmek. Her gün yeni bir telemetri partisi gelir; hat veriyi doğrular, eğitir, kapıdan geçirir, kayıt defterine koyar, kaymayı izler ve tetiklemeli politikaya göre yeniden eğitir. Her karar bir denetim kaydına yazılır.

**Yapılacaklar / beklenen davranış.** Önce 100 günlük bir parti simülatörü yaz: her gün 300 satır, ortam ve katsayı kayması 40. günden itibaren kademeli artsın. Her gün sırasıyla şunları yap: veri denetimi, kayma metrikleri, gecikmeli performans, kalite kapısı, kayıt ve denetim günlüğü. Yeniden eğitim tetiklenirse önceki model korunmalı ve yalnızca kapıdan geçen aday production'a alınmalıdır. Hat tek komutla (`python hat.py`) çalışsın ve aynı tohumla iki kez çalıştığında bayt bayt aynı denetim günlüğünü üretsin. Dört politikayı (hiç, 10, 30 ve tetikli) aynı hatla üç tohumda karşılaştır ve hangi politikanın neden kazandığını yazılı açıkla.

**Önerilen yaklaşım (ipucu, tam çözüm değil).** Her adımı girdi ve çıktısı açık bir fonksiyon yap, sonra hepsini bir `gunluk_dongu(gun, durum)` içinde çağır. Denetim günlüğünü JSON satırları olarak ekle ve yalnızca ekleme yap (append-only); eski satırlar asla değişmez. "Kapı reddederse önceki model korunur" kuralını ayrı bir testle kanıtla. Maliyet birimlerini bir yapılandırma dosyasına taşı, böylece değiştirildiğinde sonucun nasıl değiştiğini görebilirsin.

**Başarı kriterleri.** (a) Üç tohumda da hat hatasız tamamlanır ve her gün için denetim kaydı vardır. (b) Aynı tohumla iki çalıştırma aynı denetim günlüğünü üretir. (c) Kapı reddettiğinde üretim modeli değişmez; bunu bir test kanıtlar. (d) Maliyet ve yeniden eğitim sayısı üç tohumun ortalaması ve standart sapmasıyla raporlanır. (e) Maliyet birimleri değiştirildiğinde kararların değişip değişmediği raporlanır.

### Ek Alıştırmalar

1. ★ PSI'de bir kutunun oranı sıfır olduğunda formül ne olur? Koddaki 0,0001 alt sınırı sonucu nasıl etkiler, bunu iki farklı değerle dene.
2. ★ Deney takipçisinde aynı parametrelerle iki koşu yapılırsa tablo ne gösterir? Bu, tekrarlanabilirlik hakkında ne söyler?
3. ★ Veri özetinde SHA-256 yerine MD5 kullanmanın hangi riski vardır? Bölüm 9'daki çarpışma fikrini kullanarak açıkla.
4. ★★ Kalite kapısında önyükleme sayısı B = 1000 yerine B = 100 kullanılırsa %2,5 alt sınır kararlı kalır mı? Üç tohumla gözlemle.
5. ★ Bir modelin etiketi yalnızca 30 gün sonra geliyorsa, performans alarmı hangi gecikmeyle çalışır? Gecikmenin tespit süresine etkisini yaz.
6. ★★ Kanarya payı yüzde 2'den yüzde 10'a çıkarsa Örnek 3'teki gün sayısı nasıl değişir? Bu artışın bedeli nedir?
7. ★★ (Mülakat) Bir sistemde her gün 200 özellik için PSI hesaplanıyor. Yanlış alarm oranını nasıl yönetirsin? Çoklu karşılaştırma düzeltmesini düşün.
8. ★★ (Mülakat) Eğitim ve servis aynı dönüşüm fonksiyonunu çağırıyor, ama servise gelen veri yeni bir yazılım sürümünde farklı bir birimle kaydediliyor. Bu tür bir çarpıklık nasıl fark edilir?
9. ★★★ (Mülakat) Bir savunma sisteminde bir modelin sürüm izlenebilirliği nasıl kanıtlanır? Bu bölümdeki hangi bileşenler çekirdektir, hangi eksikleri kapatman gerekir?
10. ★ Kayıt defterinde production sürümü arşive taşınırken hata olursa hangi durum oluşur? Bu işlemi atomik yapmak için ne gerekir?
11. ★★ (Mülakat) Gölge dağıtımda adayın gecikmesi taban modelden yüzde 40 yüksek çıkıyor. Gecikme ölçümünde p50 mi p99 mu daha önemlidir ve neden?
12. ★★ Kalite kapısı, veri doğrulama ile birlikte hangi hataları kaçırabilir? Her biri için bir örnek ver.

## Kod Okuma Egzersizi

Aşağıdaki kesit, scipy 1.17.1 kütüphanesinin yerel kurulumundaki `ks_2samp` fonksiyonudur. Dosya `C:\Users\merty\AppData\Local\Programs\Python\Python312\Lib\site-packages\scipy\stats\_stats_py.py` konumundadır ve 7948. satırdan 7969. satıra kadar birebir alınmıştır. Kısaltma ya da sadeleştirme yapılmadı. Bu kesit, KS istatistiğinin nasıl hesaplandığını gösterir; Bölüm 77.10'da kullandığımız p değeri ise bu fonksiyonun devamında hesaplanır.

```python
    data1 = np.sort(data1)
    data2 = np.sort(data2)
    n1 = data1.shape[0]
    n2 = data2.shape[0]
    if min(n1, n2) == 0:
        raise ValueError('Data passed to ks_2samp must not be empty')

    data_all = np.concatenate([data1, data2])
    # using searchsorted solves equal data problem
    cdf1 = np.searchsorted(data1, data_all, side='right') / n1
    cdf2 = np.searchsorted(data2, data_all, side='right') / n2
    cddiffs = cdf1 - cdf2

    # Identify the location of the statistic
    argminS = np.argmin(cddiffs)
    argmaxS = np.argmax(cddiffs)
    loc_minS = data_all[argminS]
    loc_maxS = data_all[argmaxS]

    # Ensure sign of minS is not negative.
    minS = np.clip(-cddiffs[argminS], 0, 1)
    maxS = cddiffs[argmaxS]
```

**Sorular — cevaplamadan geçme:**

1. `data1` ve `data2` neden önce sıralanıyor? Sıralama olmadan `searchsorted` neden yanlış bir ampirik dağılım verir?
2. `searchsorted(..., side='right')` kullanılmasının eşit değerlerdeki etkisi nedir? Kaynaktaki yorumun neden söz ettiği konuyu açıkla.
3. `cddiffs = cdf1 - cdf2` ifadesi KS istatistiğinin hangi tanımına karşılık gelir? İki yönlü test için neden hem `minS` hem `maxS` hesaplanıyor?
4. `np.clip(-cddiffs[argminS], 0, 1)` satırında neden `clip` var? Hangi durumda negatif bir değer üretilebilir?
5. Büyük örneklerde (on milyonlarca eleman) en pahalı adım hangisidir? `np.sort` ile iki `searchsorted` çağrısının maliyetini karşılaştır.
6. Bölüm 77.10'daki KS hesabımız `ks_min_p` için bu fonksiyonun p değerini kullanır. Pencere büyüklüklerimizde (600 ve 2000) `method='auto'` hangi yöntemi seçer, kaynakta bu kuralı bul ve açıkla.

## Bölüm Özeti

- ML sistemi kod, veri ve modelden oluşur. Modelin kodu sistemin küçük bir parçasıdır; geri kalanı teknik borç olarak birikir (Sculley ve ark. 2015, genel bilgi).
- Tekrarlanabilirlik dört bilgiye dayanır: kod sürümü, veri özeti, ortam kilidi ve tohum. Biri eksikse sonuç yeniden üretilemez.
- İçerik-adresli depolama, veriyi SHA-256 özetiyle adresler. Git'e yalnızca küçük işaretçi girer ve bozulma özet kontrolüyle yakalanır.
- Deney takipçisi her koşuyu kod, veri ve ortamla bağlar. Küçük AUC farkları tohum belirsizliğinin içinde kalabilir; tek koşuya bakıp karar verme.
- Kayıt defteri sürümleri ve aşamaları tutar. Yüklemede özet doğrulanır, geri alma eski sürümü production'a döndürür.
- Kalite kapısı ve veri doğrulama bozuk modelin ve partinin yayınlanmasını engeller. Kapı küçük bozulmaları her zaman yakalamaz; bu bir sınırdır ve bilinmelidir.
- Eğitim/servis çarpıklığı hata vermeden doğruluğu düşürür. Tek kaynak dönüşüm ve tahmin dağılımı izlemesi bunu önler.
- Kayma türleri farklı yöntemlerle yakalanır: PSI, KS ve alan sınıflandırıcısı etiketsiz kovaryat kaymasını, performans alarmı kavram kaymasını yakalar. Yeniden eğitim politikası bir maliyet kararıdır.

**Sonraki bölümde:** Bölüm 78'de (Güvenilir ve Güvenli AI) bu bölümde kurduğumuz izlenebilirlik zincirinin neden tek başına yetmediğini göreceğiz. Model, saldırılara karşı dayanıksız olabilir, belirsizliğini bildirmeyebilir ve kararlarını açıklayamayabilir. Savunma sanayiinde bu eksikler, sertifikasyon sürecinin asıl konusudur. Bu bölümdeki sürüm izlenebilirliği, o tartışmanın ön koşuludur.

::: mulakat
1. Üretimdeki bir model %10 daha kötü çalışıyor, ama kayıtlarda hiçbir hata yok. Hangi üç veriye, hangi sırayla bakarsın?
2. Eğitim ve servis aynı dönüşüm fonksiyonunu çağırıyor. Bu yeterli mi? Hangi durumda yine de çarpıklık oluşur?
3. Bir veri dosyasının adı aynı, içeriğinde tek bir bayt değişti. Git bunu nasıl görür ve büyük bir ikili dosya için bu neden yetersizdir?
4. Kalite kapısı yeni modeli reddetti, ama ekip modelin iyi olduğuna inanıyor. Tartışmada kapının hangi parametresine bakarsın ve neden?
5. Kanarya dağıtımı yüzde 1 trafikle başladı ve iki gün sonra hata oranında belirgin bir fark yok. Bu, adayın güvenli olduğu anlamına gelir mi?
6. Yeniden eğitimin maliyeti 60, yanlış negatifin maliyeti 5 birim. Kaç yanlış negatif bir yeniden eğitimi haklı çıkarır? Bu hesabın dayandığı varsayımları say.
7. Bir model dosyasını bir arkadaşından `pickle` ile aldın. Yüklemeden önce hangi üç şeyi kontrol edersin?
:::
