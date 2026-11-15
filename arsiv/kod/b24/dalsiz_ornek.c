/* Dalsız mutlak değer ve maksimum; dallı sürümle karşılaştırma */
#include <stdio.h>
#include <stdint.h>

/* dallı sürümler */
int mutlak_dalli(int x)
{
    return x < 0 ? -x : x;
}

int maks_dalli(int a, int b)
{
    return a > b ? a : b;
}

/* dalsız sürümler: işaret maskesi ile */
int mutlak_dalsiz(int x)
{
    int m = x >> 31;             /* 0 ya da -1 (işaretli kaydırma) */
    return (x ^ m) - m;
}

int maks_dalsiz(int a, int b)
{
    int m = -(a < b);            /* a<b ise -1, değilse 0 */
    return a ^ ((a ^ b) & m);
}

int main(void)
{
    uint32_t durum = 42;  /* sabit tohum: hep aynı sayılar */
    long hata = 0;
    for (int i = 0; i < 1000000; i++) {
        durum ^= durum << 13;
        durum ^= durum >> 17;
        durum ^= durum << 5;
        int a = (int)(durum % 2001u) - 1000;   /* -1000..1000 */
        durum ^= durum << 13;
        durum ^= durum >> 17;
        durum ^= durum << 5;
        int b = (int)(durum % 2001u) - 1000;
        if (mutlak_dalli(a) != mutlak_dalsiz(a)) hata++;
        if (maks_dalli(a, b) != maks_dalsiz(a, b)) hata++;
    }
    printf("uyusmazlik=%ld\n", hata);
    printf("mutlak(-7)=%d maks(3,9)=%d\n",
           mutlak_dalsiz(-7), maks_dalsiz(3, 9));
    return 0;
}
