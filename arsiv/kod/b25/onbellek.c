/* onbellek.c - kume iliskili, LRU'lu bir onbellek simulatoru.
 * Varsayilan: 32 KB, 8 yol, 64 bayt satir -> 64 kume.
 * YOL ve KUME derleme aninda degistirilebilir:
 *   -DYOL=1 -DKUME=512   dogrudan eslemeli (ayni 32 KB)
 *   -DYOL=512 -DKUME=1   tam iliskili (ayni 32 KB)
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 onbellek.c -o onbellek
 * Kullanim:
 *   ./onbellek adres 0x1234 0xabcd ...
 *   ./onbellek matris N satir|sutun
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define SATIR 64
#ifndef YOL
#define YOL 8
#endif
#ifndef KUME
#define KUME 64
#endif

typedef struct {
    int gecerli;
    uint64_t etiket;
    uint64_t son;               /* son kullanim zamani (LRU) */
} Girdi;

static Girdi onb[KUME][YOL];
static uint64_t saat;
static long isabet, kacirma;

/* Tek bir erisim. Donus: 1 isabet, 0 kacirma. */
static int erisim(uint64_t adr)
{
    uint64_t kume = (adr / SATIR) % KUME;
    uint64_t etiket = adr / SATIR / KUME;
    saat++;
    for (int y = 0; y < YOL; y++) {
        Girdi *g = &onb[kume][y];
        if (g->gecerli && g->etiket == etiket) {
            g->son = saat;
            isabet++;
            return 1;
        }
    }
    kacirma++;
    int sec = 0;                /* bos yer ya da en eski girdi */
    for (int y = 0; y < YOL; y++) {
        if (!onb[kume][y].gecerli) { sec = y; break; }
        if (onb[kume][y].son < onb[kume][sec].son) sec = y;
    }
    onb[kume][sec].gecerli = 1;
    onb[kume][sec].etiket = etiket;
    onb[kume][sec].son = saat;
    return 0;
}

static void adres_modu(int n, char **arg)
{
    printf("yol=%d kume=%d satir=%d\n", YOL, KUME, SATIR);
    printf("adres        etiket    kume ofset sonuc\n");
    for (int i = 0; i < n; i++) {
        uint64_t adr = strtoull(arg[i], NULL, 0);
        uint64_t ofs = adr % SATIR;
        uint64_t kume = (adr / SATIR) % KUME;
        uint64_t etiket = adr / SATIR / KUME;
        int s = erisim(adr);
        printf("0x%08llx 0x%06llx %5llu %4llu %s\n",
               (unsigned long long)adr, (unsigned long long)etiket,
               (unsigned long long)kume, (unsigned long long)ofs,
               s ? "ISABET" : "KACIRMA");
    }
}

/* N x N int matrisinin tek gecisi; taban 0x10000, eleman 4 bayt. */
static void matris_modu(long n, int satir_once)
{
    uint64_t taban = 0x10000;
    for (long a = 0; a < n; a++)
        for (long b = 0; b < n; b++) {
            long i = satir_once ? a : b;
            long j = satir_once ? b : a;
            erisim(taban + (uint64_t)(i * n + j) * 4);
        }
    long toplam = isabet + kacirma;
    printf("N=%ld %-5s erisim=%ld isabet=%ld kacirma=%ld oran=%.3f\n",
           n, satir_once ? "satir" : "sutun", toplam, isabet, kacirma,
           (double)kacirma / (double)toplam);
}

int main(int argc, char **argv)
{
    if (argc >= 3 && strcmp(argv[1], "adres") == 0) {
        adres_modu(argc - 2, argv + 2);
        return 0;
    }
    if (argc == 4 && strcmp(argv[1], "matris") == 0 &&
        (strcmp(argv[3], "satir") == 0 ||
         strcmp(argv[3], "sutun") == 0)) {
        matris_modu(atol(argv[2]), strcmp(argv[3], "satir") == 0);
        return 0;
    }
    fprintf(stderr,
            "kullanim: %s adres <hex>... | matris N satir|sutun\n",
            argv[0]);
    return 1;
}
