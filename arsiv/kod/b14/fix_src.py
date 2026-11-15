import os, glob
SRC = r"C:\Users\merty\AppData\Local\Temp\b14\src"

PAIRS = {
 "dogrusal.c": [
  (r"/* Nöbetçili arama: a[n] hücresi x'i tutar, döngüde sınır denetimi yok. */",
   "/* Nöbetçili arama: a[n] hücresi x'i tutar; döngüde sınır\n   denetimi yok. */"),
  (r'        printf("x=%5d klasik: konum=%4ld cmp=%5ld\n", hedef[k], r1, c1);',
   '        printf("x=%5d klasik: konum=%4ld cmp=%5ld\\n",\n               hedef[k], r1, c1);'),
 ],
 "dondurulmus.c": [
  (r"   her turda yalnızca bir eleman eler; bu en kötü durumu O(n) yapar. */",
   r"   her turda bir eleman eler; bu en kötü durumu O(n) yapar. */"),
  (r"            hi--;                /* a[orta] == a[hi]: karar verilemez */",
   r"            hi--;                /* a[orta] == a[hi]: karar yok */"),
  (r'        printf("x=%d -> %ld\n", sorgu[i], dondurulmus_ara(a, n, sorgu[i]));',
   '        printf("x=%d -> %ld\\n", sorgu[i],\n               dondurulmus_ara(a, n, sorgu[i]));'),
 ],
 "hatalar.c": [
  (r"/* Hata 1: hi = n - 1 ile lo < hi. Döngü son aralığı denemeden çıkar. */",
   r"/* Hata 1: hi = n - 1 ve lo < hi. Son aralık hiç denenmez. */"),
  (r"/* Hata 2: lo = orta (orta + 1 yerine). lo ve hi komşuyken ilerlemez. */",
   r"/* Hata 2: lo = orta (orta + 1 yerine). Komşuyken ilerlemez. */"),
 ],
 "ilk_true.py": [
  (r'    print("p(0..9):", "".join("T" if p(i) else "F" for i in range(10)))',
   '    dizi = "".join("T" if p(i) else "F" for i in range(10))\n'
   '    print("p(0..9):", dizi)'),
 ],
 "matris.c": [
  (r"   her adımda bir satır ya da bir sütun elenir, en fazla sat+sut adım. */",
   r"   her adımda bir satır ya da sütun elenir: en fazla sat+sut adım. */"),
  (r"int matris_ara1(const int *m, size_t sat, size_t sut, int x, long *adim) {",
   "int matris_ara1(const int *m, size_t sat, size_t sut, int x,\n                long *adim) {"),
  (r"int matris_ara2(const int *m, size_t sat, size_t sut, int x, long *adim) {",
   "int matris_ara2(const int *m, size_t sat, size_t sut, int x,\n                long *adim) {"),
  (r'        printf("sirali  x=%2d bulundu=%d adim=%ld\n", sorgu[k], s, adim);',
   '        printf("sirali x=%2d bulundu=%d adim=%ld\\n",\n               sorgu[k], s, adim);'),
  (r'        printf("duz     x=%2d bulundu=%d adim=%ld\n", sorgu2[k], s, adim);',
   '        printf("duz    x=%2d bulundu=%d adim=%ld\\n",\n               sorgu2[k], s, adim);'),
 ],
 "medyan.py": [
  (r"        a = sorted(random.randint(-50, 50) for _ in range(random.randint(0, 12)))",
   "        a = sorted(random.randint(-50, 50)\n"
   "                   for _ in range(random.randint(0, 12)))"),
  (r"        b = sorted(random.randint(-50, 50) for _ in range(random.randint(0, 12)))",
   "        b = sorted(random.randint(-50, 50)\n"
   "                   for _ in range(random.randint(0, 12)))"),
  (r"        beklenen = c[k // 2] if k % 2 else (c[k // 2 - 1] + c[k // 2]) / 2",
   "        if k % 2:\n            beklenen = c[k // 2]\n"
   "        else:\n            beklenen = (c[k // 2 - 1] + c[k // 2]) / 2"),
 ],
 "ustel.py": [
  (r'    """oku(i): sonsuz artan dizinin i. elemanı; x\'in ilk konumunu döndürür."""',
   r'    """oku(i): sonsuz artan dizinin i. elemanı. x\'in ilk konumu."""'),
  (r'    """0, 3, 6, ... sonsuz dizisinin i. elemanı; her erişim sayılır."""',
   r'    """0, 3, 6, ... dizisinin i. elemanı; erişimler sayılır."""'),
 ],
}

for fn, pairs in PAIRS.items():
    p = os.path.join(SRC, fn)
    s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        n = s.count(old)
        if n != 1:
            print("MISS", fn, n, old[:60])
            continue
        s = s.replace(old, new)
    open(p, "w", encoding="utf-8", newline="\n").write(s)
    print("done", fn)

bad = 0
for p in glob.glob(os.path.join(SRC, "*.c")) + glob.glob(os.path.join(SRC, "*.py")):
    for i, l in enumerate(open(p, encoding="utf-8"), 1):
        if len(l.rstrip("\n")) > 70:
            print("LONG", os.path.basename(p), i, len(l.rstrip("\n")))
            bad += 1
print("long lines:", bad)
