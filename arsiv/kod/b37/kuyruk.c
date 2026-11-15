long fak(long n, long acc) {
    return n <= 1 ? acc : fak(n - 1, acc * n);
}
