# -*- coding: utf-8 -*-
import glob

R = {
"b67_01_iou_nms.py": [
('    bolgesine kaydirir (torchvision batched_nms ayni fikri kullanir)."""',
 '    bolgesine kaydirir (torchvision batched_nms da ayni fikri)."""'),
],
"b67_03_anchor.py": [
('    """Gercek kutu ve anchor (ikisi de cx,cy,w,h): ofset, log-olcek."""',
 '    """Gercek kutu ve anchor (cx,cy,w,h): ofset ve log-olcek."""'),
],
"b67_04_yolo_mini.py": [
('    """(N,G,G,A,8) ham cikti -> gorsel basina (kutular, skor, sinif)."""',
 '    """(N,G,G,A,8) ham cikti -> gorsel basina (kutu, skor, sinif)."""'),
],
"b67_05_taban_hata.py": [
('                        % (ad, anahtar, k, b, fp if anahtar == "bulundu"\n                           else 0))',
 '                        % (ad, anahtar, k, b,\n                           fp if anahtar == "bulundu" else 0))'),
],
"b67_08_takip.py": [
('    (linear_sum_assignment). Gecersiz ciftler buyuk cezayla dislanir."""',
 '    (linear_sum_assignment). Gecersiz ciftler cezalandirilir."""'),
('    print("\\n== Iz ilişkilendirme karsilastirmasi (20 video, 120 kare) ==")',
 '    print("\\n== Iz ilişkilendirme karsılaştırması (20 video) ==")'),
],
}
for f, reps in R.items():
    s = open(f, encoding="utf-8").read()
    for old, new in reps:
        if old not in s:
            print("MISSING", f, old[:60])
        s = s.replace(old, new)
    open(f, "w", encoding="utf-8").write(s)
for f in sorted(glob.glob("b67_*.py")):
    for i, l in enumerate(open(f, encoding="utf-8"), 1):
        if len(l.rstrip("\n")) > 70:
            print("UZUN", f, i, len(l.rstrip("\n")))
print("bitti")
