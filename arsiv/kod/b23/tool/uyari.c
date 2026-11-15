#include <stdio.h>
#include <stddef.h>
#include <stdint.h>

int toplam_say(const int *dizi, size_t n)
{
    int toplam = 0;
    for (int i = 0; i < n; i++)
        toplam += dizi[i];
    return toplam;
}

void yuzde_yaz(double oran)
{
    int yuzde = oran * 100;
    printf("%d\n", yuzde);
}

int dogrula(int deger)
{
    int sonuc = 0;
    if (deger > 0) {
        int sonuc = deger * 2;   /* golgeleme */
        (void)sonuc;
    }
    return sonuc;
}

int main(void)
{
    uint8_t sayac = 300;          /* tasma */
    int ilk;
    if (sayac > 10)
        ilk = 1;
    printf("%d %d\n", ilk, dogrula(3));
    yuzde_yaz(0.256);
    return toplam_say(NULL, 0) + sayac;
}
