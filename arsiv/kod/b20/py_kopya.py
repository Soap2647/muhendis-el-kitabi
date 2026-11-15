# Referans semantigi: ayni liste iki etiket, sig ve derin kopya
import copy

satir = [1, 2]
ic = [satir, satir]          # ayni listenin iki etiketi
ic[0].append(3)
print("ic:", ic)

s = [[1], [2]]
sig = s.copy()               # kabuk kopya: ic listeler paylasilir
sig[0].append(9)
print("s:", s)

derin = copy.deepcopy(s)     # tum ic ice nesneler kopyalanir
derin[0].append(7)
print("s (derin sonrasi):", s, " derin:", derin)
