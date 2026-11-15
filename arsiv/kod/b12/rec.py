import sys
def derin(n):
    return 0 if n == 0 else 1 + derin(n - 1)
print("getrecursionlimit =", sys.getrecursionlimit())
son = None
for n in range(1, 100000):
    try:
        derin(n)
        son = n
    except RecursionError:
        break
print("en büyük başarılı derinlik (ilk taramada) =", son)
