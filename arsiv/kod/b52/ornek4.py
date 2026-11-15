# ornek4.py - Cozumlu Ornek 4: 5 tap Q15 FIR ve doygunluk izi
q = [8192, 16384, 16384, 16384, 8192]         # Q15, kazanc 2,0
xs = [8192, 16384, 32767, 32767, -32768, -32768]
print("q =", q, " sum q =", sum(q))
buf = [0] * 5                                 # buf[0] en yeni ornek
for n, xv in enumerate(xs):
    buf = [xv] + buf[:4]
    acc = sum(q[k] * buf[k] for k in range(5))
    yq = (acc + (1 << 14)) >> 15         # yuvarla, 15 saga kaydir
    y = min(max(yq, -32768), 32767)           # doyur
    print(f"n={n} x={xv:6d} acc={acc:11d}"
          f" yuvarlanmis={yq:6d} y={y:6d}")
