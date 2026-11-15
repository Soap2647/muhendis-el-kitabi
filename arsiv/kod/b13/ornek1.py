def hollanda_bayragi(a):
    """0, 1, 2 iceren diziyi tek gecisle, yerinde sirala."""
    lo, orta, hi = 0, 0, len(a) - 1
    while orta <= hi:
        if a[orta] == 0:
            a[lo], a[orta] = a[orta], a[lo]
            lo += 1
            orta += 1
        elif a[orta] == 1:
            orta += 1
        else:
            a[orta], a[hi] = a[hi], a[orta]
            hi -= 1
    return a


if __name__ == "__main__":
    print(hollanda_bayragi([2, 0, 2, 1, 0, 1]))
    print(hollanda_bayragi([1, 0]))
    print(hollanda_bayragi([]))
