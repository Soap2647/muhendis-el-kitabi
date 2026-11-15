# -*- coding: utf-8 -*-
# Kod satirlarini 70 karakter altina indirir (kitap kurali).
import glob

BS = chr(92)  # ters egik cizgi
R = {
"b67_01_iou_nms.py": [
("    return np.where(birlik > 0, inter / np.maximum(birlik, 1e-12), 0.0)",
 "    return np.where(birlik > 0,\n                    inter / np.maximum(birlik, 1e-12), 0.0)"),
("    return np.where(c > 0, iou - (c - birlik) / np.maximum(c, 1e-12), iou)",
 "    return np.where(c > 0,\n                    iou - (c - birlik) / np.maximum(c, 1e-12), iou)"),
("    bolgesine kaydirir (torchvision batched_nms da ayni fikri kullanir).\"\"\"",
 "    bolgesine kaydirir (torchvision batched_nms ayni fikri kullanir).\"\"\""),
],
"b67_02_ap.py": [
("    (IoU >= esik). Eslesme yoksa FP. Her gercek kutu en fazla bir kez.\"\"\"",
 "    (IoU >= esik). Eslesme yoksa FP. Her gercek kutu en fazla bir\n    kez eslesir.\"\"\""),
("    \"\"\"AP. yontem: '11' (VOC2007), '101' (COCO tarzi), 'tum' (VOC2010+).\"\"\"",
 "    \"\"\"AP. yontem: '11' (VOC2007), '101' (COCO tarzi), 'tum'\n    (VOC2010+).\"\"\""),
("    # tum noktalar: precision zarfi (yalnizca artan kisim) x recall adimi",
 "    # tum noktalar: precision zarfi (artan kisim) x recall adimi"),
("    \"\"\"tahminler/gtler: gorsel listesi; her biri (kutular, skorlar, sinif)\n    ve (kutular, sinif). Donus: (sinif basina AP listesi, ortalama).\"\"\"",
 "    \"\"\"tahminler/gtler: gorsel listesi; her biri (kutular, skorlar,\n    sinif) ve (kutular, sinif). Donus: (sinif basina AP, ortalama).\"\"\""),
("    # Zarfsiz, basamakli toplam (envelope olmadan): sadece karsilastirma",
 "    # Zarfsiz, basamakli toplam (zarf yok): sadece karsilastirma"),
("    print(\"\\n== Kutu gurultusu arttikca mAP (300 gorsel, tohum 2024) ==\")",
 "    print(\"\\n== Kutu gurultusu arttikca mAP (300 gorsel) ==\")"),
("            gk = np.array([o[\"box\"] for o in objs], float).reshape(-1, 4)",
 "            gk = np.array([o[\"box\"] for o in objs],\n                          float).reshape(-1, 4)"),
],
"b67_03_anchor.py": [
("    \"\"\"Gercek kutu ve anchor (ikisi de cx,cy,w,h): ofset ve log-olcek.\"\"\"",
 "    \"\"\"Gercek kutu ve anchor (ikisi de cx,cy,w,h): ofset, log-olcek.\"\"\""),
("        a = int(np.argmax(sekil_iou(w, h, ANCHORS[:, 0], ANCHORS[:, 1])))",
 "        a = int(np.argmax(sekil_iou(w, h, ANCHORS[:, 0],\n                                    ANCHORS[:, 1])))"),
("    print(\"ort. pozitif/gorsel = %.2f, toplam nesne = %d, cakisma = %d\"",
 "    print(\"ort. pozitif/gorsel = %.2f, nesne = %d, cakisma = %d\""),
],
"b67_04_yolo_mini.py": [
("    \"\"\"(N,G,G,A,8) ham cikti -> her gorsel icin (kutular, skor, sinif).\"\"\"",
 "    \"\"\"(N,G,G,A,8) ham cikti -> gorsel basina (kutular, skor, sinif).\"\"\""),
("            with open(os.path.join(KLASOR, \"cnn_pred.pkl\"), \"wb\") as f:",
 "            yol = os.path.join(KLASOR, \"cnn_pred.pkl\")\n            with open(yol, \"wb\") as f:"),
],
"b67_05_taban_hata.py": [
("DOLGU = {0: np.pi / 4, 1: 1.0, 2: 0.5}  # daire, kare, ucgen dolgu orani",
 "DOLGU = {0: np.pi / 4, 1: 1.0, 2: 0.5}  # daire, kare, ucgen"),
("        iou = iou_matris(gk, tk) if len(tk) else np.zeros((len(gk), 0))",
 "        iou = iou_matris(gk, tk) if len(tk) else \\\n            np.zeros((len(gk), 0))"),
("            kucuk = (gk[i, 2] - gk[i, 0]) * (gk[i, 3] - gk[i, 1]) < 200",
 "            alan_i = (gk[i, 2] - gk[i, 0]) * (gk[i, 3] - gk[i, 1])\n            kucuk = alan_i < 200"),
],
"b67_06_pr_ornek.py": [
("                satirlar.append(\"%s,%s,%.4f,%.4f\" % (ad, isim, ri, pi))",
 "                satirlar.append(\"%s,%s,%.4f,%.4f\"\n                                % (ad, isim, ri, pi))"),
("    print(\"kaydedildi: engine/veri/b67_pr_egri.csv, b67_tespit_ornek.csv\")",
 "    print(\"kaydedildi: engine/veri/b67_pr_egri.csv,\")\n    print(\"            engine/veri/b67_tespit_ornek.csv\")"),
],
"b67_07_unet.py": [
("            miou_tr, _, _, _ = olcu(tahmin(model, Xtr[:300]), Str[:300])",
 "            miou_tr, _, _, _ = olcu(tahmin(model, Xtr[:300]),\n                                    Str[:300])"),
("            print(\"%-10s tohum %d: test mIoU=%.4f  Dice(on plan)=%.4f  \"",
 "            print(\"%-10s tohum %d: test mIoU=%.4f  Dice(on)=%.4f  \""),
],
"b67_08_takip.py": [
("    \"\"\"Toplam maliyeti en az olan tam eslestirme (linear_sum_assignment).\n    Gecerli olmayan ciftler buyuk bir cezayla dislanir, sonra elenir.\"\"\"",
 "    \"\"\"Toplam maliyeti en az olan tam eslestirme\n    (linear_sum_assignment). Gecersiz ciftler buyuk cezayla dislanir.\"\"\""),
("            cd = kutular[:, :2] + (kutular[:, 2:] - kutular[:, :2]) / 2",
 "            cd = kutular[:, :2] + \\\n                (kutular[:, 2:] - kutular[:, :2]) / 2"),
("            or (t.hits >= self.min_hits and t.kacirma <= self.max_age)]",
 "            or (t.hits >= self.min_hits\n                and t.kacirma <= self.max_age)]"),
("                if t.hits >= self.min_hits and t.kacirma <= self.max_age]",
 "                if t.hits >= self.min_hits\n                and t.kacirma <= self.max_age]"),
("    m = np.array([[0.9, 0.8], [0.85, 0.1]])  # satir: iz, sutun: tespit",
 "    # satir: iz, sutun: tespit\n    m = np.array([[0.9, 0.8], [0.85, 0.1]])"),
("MODLAR = [\"acgozlu_iou\", \"macar_iou\", \"macar_mesafe\", \"macar_tum\", \"byte\"]",
 "MODLAR = [\"acgozlu_iou\", \"macar_iou\", \"macar_mesafe\", \"macar_tum\",\n          \"byte\"]"),
],
"b67_08b_kesisim.py": [
("            cikti = [izci.guncelle(k[\"det\"], k[\"skor\"]) for k in kareler]",
 "            cikti = [izci.guncelle(k[\"det\"], k[\"skor\"])\n                     for k in kareler]"),
("            toplam[m][2] += sum(v for k, v in s.items() if k not in (0, 1))",
 "            toplam[m][2] += sum(v for k, v in s.items()\n                                if k not in (0, 1))"),
("    print(\"20 video, kesisen cift (GT 0, GT 1) ve diger IDSW toplami:\")",
 "    print(\"20 video: kesisen cift (GT 0, 1) ve diger IDSW toplami:\")"),
("    print(\"kaydedildi: b67_kesisim_ozet.csv, b67_kesisim.csv (tohum 107)\")",
 "    print(\"kaydedildi: b67_kesisim_ozet.csv, b67_kesisim.csv\")"),
],
"b67_09_gecikme.py": [
("    \"\"\"Yalnizca ag ileri gecisi; her olcum CUDA senkronizasyonu ile.\"\"\"",
 "    \"\"\"Yalnizca ag ileri gecisi; her olcum CUDA senkronizasyonlu.\"\"\""),
("        f.write(\"# son_isleme_ms=%.3f, takipci_ms=%.3f\\n\" % (son, tak))",
 "        f.write(\"# son_isleme_ms=%.3f, takipci_ms=%.3f\\n\"\n                % (son, tak))"),
],
"b67_veri.py": [
("# hedefleri\"dir; gercek bir ucus veri kumesi DEGILDIR. Etiket, nesnenin",
 "# hedefleri\"dir; gercek bir ucus veri kumesi DEGILDIR. Etiket,"),
("    \"\"\"Tam (ortusmemis) sekil maskesi. Piksel merkezi x+0.5 kullanilir.\"\"\"",
 "    \"\"\"Tam (ortusmemis) sekil maskesi. Piksel merkezi x+0.5 alinir.\"\"\""),
("    # Cizim sirasi = katman sirasi: sonra cizilen onceki nesneyi ortusturur.",
 "    # Cizim sirasi = katman sirasi: sonra cizilen onceki nesneyi\n    # ortusturur."),
("            det.append([cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2])",
 "            det.append([cx - s / 2, cy - s / 2,\n                        cx + s / 2, cy + s / 2])"),
],
}

for f, reps in R.items():
    s = open(f, encoding="utf-8").read()
    for old, new in reps:
        if old not in s:
            print("MISSING in", f, ":", old[:70])
        s = s.replace(old, new)
    open(f, "w", encoding="utf-8").write(s)

for f in sorted(glob.glob("b67_*.py")):
    for i, l in enumerate(open(f, encoding="utf-8"), 1):
        if len(l.rstrip("\n")) > 70:
            print("UZUN", f, i, len(l.rstrip("\n")))
        if "�" in l:
            print("BOZUK", f, i, l.rstrip())
print("bitti")
