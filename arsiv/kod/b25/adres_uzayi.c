/* adres_uzayi.c - surecin sanal adres haritasi,
 * 4 seviyeli sayfa tablosu indeksleri.
 * Her bolumden bir adres alir, 48 bitlik adresin sayfa tablosu
 * indekslerine boler ve /proc/self/maps'i (kisaltilmis) yazar.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 adres_uzayi.c -o adr
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

int veri_baslangic = 7;              /* .data */
int veri_bss;                        /* .bss  */
const char *metin = "merhaba";       /* .rodata'daki dize */

static void indeks(const char *ad, uintptr_t va)
{
    printf("%-7s %016llx %3llu %4llu %4llu %4llu\n", ad,
           (unsigned long long)va,
           (unsigned long long)((va >> 39) & 0x1FF),
           (unsigned long long)((va >> 30) & 0x1FF),
           (unsigned long long)((va >> 21) & 0x1FF),
           (unsigned long long)((va >> 12) & 0x1FF));
}

static void harita(void)
{
    FILE *f = fopen("/proc/self/maps", "r");
    char satir[512];
    if (!f) { perror("maps"); return; }
    while (fgets(satir, sizeof satir, f)) {
        unsigned long a, b;
        char izin[8];
        sscanf(satir, "%lx-%lx %7s", &a, &b, izin);
        char *yol = satir;
        for (int k = 0; k < 5; k++) {          /* 5 alan atla */
            yol = strchr(yol, ' ');
            while (yol && *yol == ' ') yol++;
        }
        if (yol) yol[strcspn(yol, "\n")] = '\0';
        char *ad = (yol && *yol) ? strrchr(yol, '/') : NULL;
        printf("%012lx-%012lx %s %s\n", a, b, izin,
               ad ? ad + 1 : (yol && *yol ? yol : "(anonim)"));
    }
    fclose(f);
}

int main(void)
{
    int yerel = 0;
    char *yigin_ayri = malloc(100);
    char *buyuk = malloc(1u << 20);      /* 1 MB: mmap ile gelir */

    printf("bolge    sanal adres      PML4 PDPT   PD   PT\n");
    indeks("kod", (uintptr_t)&harita);
    indeks("rodata", (uintptr_t)metin);
    indeks("data", (uintptr_t)&veri_baslangic);
    indeks("bss", (uintptr_t)&veri_bss);
    indeks("heap", (uintptr_t)yigin_ayri);
    indeks("mmap", (uintptr_t)buyuk);
    indeks("yigin", (uintptr_t)&yerel);

    printf("\n/proc/self/maps:\n");
    harita();
    free(yigin_ayri);
    free(buyuk);
    return 0;
}
