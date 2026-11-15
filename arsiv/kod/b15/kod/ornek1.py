def us(taban, n):
    if n == 0:
        return 1
    yari = us(taban, n // 2)
    if n % 2 == 0:
        return yari * yari
    return yari * yari * taban


if __name__ == "__main__":
    print(us(2, 10))
    print(us(3, 5))
    print(us(7, 0))
