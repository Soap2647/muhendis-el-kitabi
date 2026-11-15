/* Bolum 24 - assembly okuma ornekleri */
int toplam(const int *a, int n)
{
    int s = 0;
    for (int i = 0; i < n; i++)
        s += a[i];
    return s;
}

long kare_arti(long x, long y)
{
    return x * x + y;
}

int maks(int a, int b)
{
    return a > b ? a : b;
}

int cagiran(int x)
{
    return kare_arti(x, 7) + toplam(&x, 1);
}

int yaprak(int x, int y)
{
    int t = x * 3 + y;
    return t - 2;
}

int g(int x, int y)
{
    return x > y ? 3 * x + y : x - 2 * y;
}
