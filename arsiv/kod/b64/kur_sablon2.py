# -*- coding: utf-8 -*-
"""Eski bolum_64.md'den birlestirici sablonunu (sablon64.md) uretir."""
SRC = r"C:\Users\merty\AppData\Local\Temp\b64\bolum_64_eski.md"
DST = r"C:\Users\merty\AppData\Local\Temp\b64\sablon64.md"
L = open(SRC, encoding="utf-8").read().split("\n")

FENCE = {
    1: "{{KOD|egitim_np.py|def adam_adim|return theta, m, v, t}}",
    2: "{{KOD|adam_iz.py|^|$}}",
    3: "{{CIKTI|adam_iz.py|out_adam_iz.txt}}",
    4: "{{KOD|egitim_np.py|def adamw_adim|"
       "return adam_adim(theta, g, m, v, t, lr, b1, b2, eps)#2}}",
    5: "{{KOD|egitim_np.py|def lr_adim_kurali|"
       "return lr_kosinus(t - W, T - W, lr_max, lr_min)}}",
    6: "{{KOD|egitim_np.py|def bn_ileri|return dx, dgamma, dbeta}}",
    7: "{{KOD|bn_ornek.py|^|$}}",
    8: "{{CIKTI|bn_ornek.py|out_bn_ornek.txt}}",
    9: "{{KOD|egitim_np.py|def dropout_ileri|return x * maske, maske}}",
    10: "{{KOD|egitim_np.py|def norm_kirp|return gradlar, toplam}}",
    11: "{{KOD|t09b_nan.py|^|$}}",
    12: "{{CIKTI|t09b_nan.py|out_t09b_nan.txt}}",
    13: "{{KOD|bozuk_egitim.py|^|$}}",
    14: "{{CIKTI|bozuk_egitim.py|out_bozuk_egitim.txt}}",
    15: "{{KOD|takvim_ornek.py|^|$}}",
    16: "{{CIKTI|takvim_ornek.py|out_takvim_ornek.txt}}",
}
out, k, inb, buf = [], 0, False, []
for l in L:
    if l.startswith("```") and not inb:
        inb = True
        k += 1
        buf = [l]
        if k in FENCE:
            out.append(FENCE[k])
        continue
    if inb:
        if k in FENCE:
            if l.startswith("```"):
                inb = False
            continue
        buf.append(l)
        if l.startswith("```"):
            inb = False
            out.extend(buf)
        continue
    out.append(l)
assert k == 17, k
L = out


def rep_satir(anahtar, yeni):
    global L
    idx = [i for i, l in enumerate(L) if anahtar in l]
    assert len(idx) == 1, (anahtar, len(idx))
    L[idx[0]] = yeni


def ekle_once(anahtar, tanitim, isaretler):
    global L
    idx = [i for i, l in enumerate(L) if anahtar in l]
    assert len(idx) == 1, (anahtar, len(idx))
    i = idx[0]
    L[i:i] = [tanitim, ""] + isaretler + [""]


def ekle_once_sonra(anahtar, tanitim, isaretler):
    global L
    idx = [i for i, l in enumerate(L) if anahtar in l]
    assert len(idx) == 1, (anahtar, len(idx))
    i = idx[0] + 1
    L[i:i] = [""] + [tanitim, ""] + isaretler + [""]


T = {}
T["ortak"] = (
    "Bölümdeki tüm deneyler, veri ve eğitim döngüsü için aynı küçük "
    "altyapıyı kullanır. Bu dosya ilk deneyden önce verilir: veri "
    "bölmesi, MLP kurucu, eğitim döngüsü ve kayıt yardımcıları. "
    "Dosyanın başındaki `VERI` yolu, deney çıktılarının yazıldığı "
    "klasördür; okur kendi bilgisayarında bu yolu değiştirebilir.")
T["t01"] = (
    "Aşağıdaki betik iki ölçümü birlikte yapar. Birinci bölümde "
    "başlangıç ağırlıklarında tek bir ağın gradyanını hesaplar ve "
    "300 rastgele batch için tam gradyandan sapmayı ölçer. İkinci "
    "bölümde 30 epoch boyunca sabit ve doğrusal ölçekli öğrenme "
    "oranlarıyla beş tohumlu eğitimleri tekrarlar. Sonuçlar aşağıdaki "
    "tablolarda ve Şekil 64.1'de özetlenir.")
T["mom"] = (
    "Sıfırdan yazdığımız optimizasyon güncellemeleri `egitim_np.py` "
    "dosyasındadır. Dosyanın başı ile momentum ve Nesterov güncellemeleri "
    "aşağıdadır:")
T["t03a"] = (
    "Yörüngeleri üreten betik aşağıdadır. Aynı başlangıç noktasından "
    "üç optimizer 60 adım yürütülür; her adımın konumu ve kaybı CSV "
    "dosyasına yazılır. Şekil 64.2 bu dosyadan çizilmiştir.")
T["t02"] = (
    "Optimizer karşılaştırmasını yapan betik aşağıdadır. Önce her "
    "optimizer için yedi öğrenme oranı yalnızca doğrulama kümesinde "
    "(tohum 10–12) denenir; sonra seçilen lr ile test kümesi beş "
    "tohumda (0–4) ölçülür.")
T["t03b"] = (
    "LR aralık testini yapan betik aşağıdadır. Öğrenme oranı her "
    "adımda çarpanla artırılır ve kayıp izlenir.")
T["t04"] = (
    "Takvim şekillerini, takvim karşılaştırmasını ve derin ağ deneyini "
    "üreten betik aşağıdadır. İlk bölüm 300 adımlık takvim dizilerini "
    "yazar ve kosinüs takvimini PyTorch ile karşılaştırır; ikinci "
    "bölüm MLP üzerinde üç takvimi beş tohumla eğitir; üçüncü bölüm "
    "12 katmanlı ağda ısınmanın etkisini ölçer.")
T["t05"] = (
    "Başlatma deneyini yapan betik aşağıdadır. İlk bölüm, her katmanın "
    "aktivasyon standart sapmasını ve ağırlık gradyan normunu ölçer; "
    "ikinci bölüm dört başlatma yöntemini 20 epoch eğitir.")
T["t06"] = (
    "BatchNorm'un el örneğini, batch deneyini ve eğitim–çıkarım "
    "farkını ölçen betik aşağıdadır.")
T["bncik"] = (
    "Çıkarım modu için BatchNorm fonksiyonu, eğitimde biriken "
    "hareketli ortalamaları kullanır:")
T["t07"] = (
    "Düzenlileştirme deneyini yapan betik aşağıdadır. Her varyant için "
    "MLP, Adam ile 60 epoch eğitilir; eğitim doğruluğu eğitim "
    "kümesinde çıkarım modunda, test doğruluğu ve ECE test kümesinde "
    "ölçülür.")
T["t08"] = (
    "Gradyan deneylerini yapan betik aşağıdadır: (a) patlayan gradyan "
    "ve kırpma, (b) ilk katmanın gradyanı, artık bloğu ve sıfır "
    "başlatma.")
T["t09"] = (
    "Kayıp kataloğunu üreten betik aşağıdadır. Önce başlangıç kaybı "
    "kontrolü yapılır; ardından yedi vakanın her biri 40 epoch "
    "boyunca eğitilir ve kayıp eğrileri CSV dosyasına yazılır.")
T["t10"] = (
    "Tek batch testini ve eval modu kontrollerini yapan betik "
    "aşağıdadır. Dört varyant aynı 32 örnek üzerinde 500 adım çalışır; "
    "ardından dropout ve BatchNorm için eval modu farkı ölçülür.")
T["t11"] = (
    "Arama deneyini yapan betik aşağıdadır. Önce 42 yapılandırma iki "
    "tohumla eğitilip bir tablo oluşturulur; sonra ızgara ve rastgele "
    "arama bu tablo üzerinde 300 kez simüle edilir.")
T["bozuk"] = (
    "Düzeltilmiş betik aşağıdadır; üç hatanın düzeltilmiş hâlini "
    "içerir. Çıktı, bozuk betikle aynı ölçümleri verir:")
T["t12"] = (
    "Sıfırdan yazdığımız her parçanın doğru olduğunu PyTorch ile "
    "sınadık. Aşağıdaki betik 19 kontrol yapar: Adam, AdamW, L2 ile "
    "azaltma, momentum ve Nesterov güncellemeleri; BatchNorm'un ileri "
    "ve geri geçişi (PyTorch ve sayısal gradyan ile), running "
    "istatistikleri ve çıkarım modu; dropout'un ters ölçeklemesi; "
    "kosinüs, basamaklı ve üstel takvimler; gradyan kırpma. Her "
    "kontrol mutlak farkı yazar ve eşiği aşarsa HATA der. Genel eşik "
    "10⁻⁶'dır; takvimler için 10⁻⁹ ve 10⁻¹² kullanılmıştır.")


def KOD(d, a, b):
    return "{{KOD|%s|%s|%s}}" % (d, a, b)


def CIK(s, o):
    return "{{CIKTI|%s|%s}}" % (s, o)


ekle_once_sonra("## 64.2 Mini-batch", T["ortak"], [
    KOD("ortak64.py", "^", "torch.set_num_threads(1)"),
    KOD("ortak64.py", "def veri", "return (t(Xtr), t(ytr), t(Xva), t(yva), t(Xte), t(yte))"),
    KOD("ortak64.py", "def mlp", "return nn.Sequential(*kat)"),
    KOD("ortak64.py", "@torch.no_grad()", "<def egit("),
    KOD("ortak64.py", "def egit", "<    for ep in range(epochs):"),
    KOD("ortak64.py", "    for ep in range(epochs):", "<    _, h["),
    KOD("ortak64.py", "    _, h[", "return h"),
    KOD("ortak64.py", "def csv_yaz", "return yol"),
    KOD("ortak64.py", "def ortalama_sapma", "return a.mean()"),
])
ekle_once("Bunu ölçmek için ağı başlangıç ağırlıklarında tuttuk", T["t01"], [
    KOD("t01_batch.py", "^", "<def grad_vec"),
    KOD("t01_batch.py", "@", "<# (b)"),
    KOD("t01_batch.py", "@", "$"),
    CIK("t01_batch.py", "out_t01_batch.txt"),
])
ekle_once("**AdaGrad** her parametrenin", T["mom"], [
    KOD("egitim_np.py", "^", "return theta - lr * (g + mu * v), v"),
])
ekle_once("Şekil 64.2, aynı deneyin yörüngelerini", T["t03a"], [
    KOD("t03a_yorunge.py", "^", "<satir = []"),
    KOD("t03a_yorunge.py", "satir = []", "$"),
    CIK("t03a_yorunge.py", "out_t03a_yorunge.txt"),
])
ekle_once("| Optimizer | Seçilen lr", T["t02"], [
    KOD("t02_optim.py", "^", "<for ad in OPT:"),
    KOD("t02_optim.py", "@", "<print(\"\\nAdim 2"),
    KOD("t02_optim.py", "print(\"\\nAdim 2", "$"),
    CIK("t02_optim.py", "out_t02_optim.txt"),
])
ekle_once("Aşağıdaki deney, 0,9 momentumlu SGD ile batch 64", T["t03b"], [
    KOD("t03b_lr_aralik.py", "^", "<# ---- (b)"),
    KOD("t03b_lr_aralik.py", "# ---- (b)", "$"),
    CIK("t03b_lr_aralik.py", "out_t03b_lr_aralik.txt"),
])
ekle_once("Şekil 64.5 sol üstte dört takvimi", T["t04"], [
    KOD("t04_takvim.py", "^", "<# Torch karsilastirmasi"),
    KOD("t04_takvim.py", "# Torch karsilastirmasi", "<# (b) Sig"),
    KOD("t04_takvim.py", "# (b) Sig", "<# (c) Derin"),
    KOD("t04_takvim.py", "@", "<satir = []"),
    KOD("t04_takvim.py", "@", "$"),
    CIK("t04_takvim.py", "out_t04_takvim.txt"),
])
ekle_once("Dört başlatma biçimi karşılaştırıldı", T["t05"], [
    KOD("t05_baslatma.py", "^", "<def ag("),
    KOD("t05_baslatma.py", "@", "<def olc("),
    KOD("t05_baslatma.py", "@", "<satir = []"),
    KOD("t05_baslatma.py", "@", "<print(\"\\nEgitim"),
    KOD("t05_baslatma.py", "print(\"\\nEgitim", "$"),
    CIK("t05_baslatma.py", "out_t05_baslatma.txt"),
])
ekle_once("**Küçük batch sorunu.**", T["t06"], [
    KOD("t06_bn.py", "^", "<# (b) Kucuk"),
    KOD("t06_bn.py", "# (b) Kucuk", "$"),
    CIK("t06_bn.py", "out_t06_bn.txt"),
])
ekle_once("Bu iki fonksiyonun doğruluğunu iki bağımsız", T["bncik"], [
    KOD("egitim_np.py", "def bn_cikarim", "return gamma"),
])
ekle_once("Aşağıdaki deney, 256 gizli birimli", T["t07"], [
    KOD("t07_duzenlilestirme.py", "^", "<D = veri()"),
    KOD("t07_duzenlilestirme.py", "D = veri()", "<satir = []"),
    KOD("t07_duzenlilestirme.py", "satir = []", "<for ad, c in VARYANT"),
    KOD("t07_duzenlilestirme.py", "@", "$"),
    CIK("t07_duzenlilestirme.py", "out_t07_duzenlilestirme.txt"),
])
ekle_once("Bu fonksiyon PyTorch'un `clip_grad_norm_`", T["t08"], [
    KOD("t08_gradyan.py", "^", "<def derin"),
    KOD("t08_gradyan.py", "def derin", "<# (a) patlayan"),
    KOD("t08_gradyan.py", "# (a) patlayan", "<# (b) kaybolan"),
    KOD("t08_gradyan.py", "# (b) kaybolan", "<class Artik"),
    KOD("t08_gradyan.py", "class Artik", "$"),
    CIK("t08_gradyan.py", "out_t08_gradyan.txt"),
])
ekle_once("**Loss eğrisi kataloğu.**", T["t09"], [
    KOD("t09_teshis.py", "^", "<satir = []"),
    KOD("t09_teshis.py", "satir = []", "<EP = 40"),
    KOD("t09_teshis.py", "EP = 40", "<# D. Yetersiz"),
    KOD("t09_teshis.py", "# D. Yetersiz", "<# E. Veri"),
    KOD("t09_teshis.py", "# E. Veri", "<# F. Etiket"),
    KOD("t09_teshis.py", "# F. Etiket", "<# G. Sayisal"),
    KOD("t09_teshis.py", "# G. Sayisal", "$"),
    CIK("t09_teshis.py", "out_t09_teshis.txt"),
])
ekle_once("Aşağıdaki deneyde aynı 32 örnek", T["t10"], [
    KOD("t10_tek_batch.py", "^", "<def kos("),
    KOD("t10_tek_batch.py", "def kos(", "<print(\"Tek batch"),
    KOD("t10_tek_batch.py", "print(\"Tek batch", "<# Eval modu"),
    KOD("t10_tek_batch.py", "# Eval modu", "<Xv = veri()[2]"),
    KOD("t10_tek_batch.py", "@", "$"),
    CIK("t10_tek_batch.py", "out_t10_tek_batch.txt"),
])
ekle_once("Şekil 64.10, 42 yapılandırmanın", T["t11"], [
    KOD("t11_arama.py", "^", "<tablo = {}"),
    KOD("t11_arama.py", "@", "<rng = np.random.default_rng(64)"),
    KOD("t11_arama.py", "@", "$"),
    CIK("t11_arama.py", "out_t11_arama.txt"),
])
ekle_once("## Çözümlü Örnekler", "", [])
idx = [i for i, l in enumerate(L) if l == ""]
# bosluk satirlarindan birini baslik icin kullanmak yerine acikca ekle:
i_coz = [i for i, l in enumerate(L) if l.startswith("## Çözümlü Örnekler")][0]
L[i_coz:i_coz] = [
    "## 64.12 PyTorch ile eşleşme: NumPy kodunun doğrulanması", "",
    T["t12"], "",
    KOD("test_np64.py", "^", "<def kontrol"),
    KOD("test_np64.py", "def kontrol", "<# ---- A."),
    KOD("test_np64.py", "# ---- A.", "<kontrol(ad, en_kotu)"),
    KOD("test_np64.py", "@", "<# ---- B."),
    KOD("test_np64.py", "# ---- B.", "<# ---- C."),
    KOD("test_np64.py", "# ---- C.", "<# sayisal gradyan"),
    KOD("test_np64.py", "@", "<# running istatistikler"),
    KOD("test_np64.py", "@", "<# ---- D."),
    KOD("test_np64.py", "# ---- D.", "<# ---- E."),
    KOD("test_np64.py", "# ---- E.", "<# ---- F."),
    KOD("test_np64.py", "# ---- F.", "$"),
    CIK("test_np64.py", "out_test_np64.txt"), "",
]
ekle_once("**Adım 6 — Doğrula.** Düzeltilmiş betiğin sonucu", T["bozuk"], [
    KOD("bozuk_egitim_duzeltilmis.py", "^", "$"),
    CIK("bozuk_egitim_duzeltilmis.py", "out_bozuk_egitim_duzeltilmis.txt"),
])
rep_satir("Bu bölümde kullandığımız NumPy kodunun tamamı",
    "Bu bölümde kullandığımız NumPy kodunun tamamı (`egitim_np.py`) ve PyTorch ile eşleşme testi (`test_np64.py`, 19 kontrol) 64.12'de verilmiştir. Tüm kontroller geçti: Adam, AdamW, momentum, BatchNorm ileri ve geri geçişi, dropout, zamanlayıcılar ve gradyan kırpma PyTorch ile eşleşti; BatchNorm'un gradyanı sayısal fark ile de doğrulandı (en büyük fark 1,4 × 10⁻⁹).")

open(DST, "w", encoding="utf-8").write("\n".join(L))
print("sablon yazildi:", len(L), "satir")
