/* b28_7_tampon_olcum.c: read() tampon boyutunun etkisi.
 * Kullanım: ./b28_7_tampon_olcum veri.bin
 * Çıktı: tur,boyut,syscall,sure_ms (en iyi 3 tur) */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>

#define TUR 3

static double simdi_ms(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e3 + t.tv_nsec / 1e6;
}

/* Dosyayı 'boyut' parçalar hâlinde okur; çağrı sayısını döner. */
static long oku_parcali(const char *yol, size_t boyut,
                        unsigned *sag)
{
    char *tampon = malloc(boyut);
    int fd = open(yol, O_RDONLY);
    long cagri = 0;
    unsigned toplam = 0;
    ssize_t r;
    while ((r = read(fd, tampon, boyut)) > 0) {
        cagri++;
        /* optimizasyon engeli: her sayfadan bir bayt al */
        for (ssize_t i = 0; i < r; i += 4096)
            toplam += (unsigned char)tampon[i];
    }
    close(fd);
    free(tampon);
    *sag = toplam;
    return cagri;
}

/* stdio: fgetc ile bayt bayt; glibc kendi tamponunu kullanır. */
static void oku_fgetc(const char *yol, unsigned *sag)
{
    FILE *f = fopen(yol, "rb");
    unsigned toplam = 0;
    int c;
    while ((c = fgetc(f)) != EOF)
        toplam += (unsigned char)c;
    fclose(f);
    *sag = toplam;
}

int main(int argc, char **argv)
{
    const char *yol = argc > 1 ? argv[1] : "veri.bin";
    size_t boyutlar[] = {1, 16, 64, 256, 1024, 4096, 16384,
                         65536, 262144, 1048576};
    int m = sizeof boyutlar / sizeof boyutlar[0];
    unsigned sag = 0;

    printf("tur,boyut,syscall,sure_ms\n");
    for (int k = 0; k < m; k++) {
        double en_iyi = 1e18;
        long cagri = 0;
        for (int t = 0; t < TUR; t++) {
            double t0 = simdi_ms();
            cagri = oku_parcali(yol, boyutlar[k], &sag);
            double dt = simdi_ms() - t0;
            if (dt < en_iyi) en_iyi = dt;
        }
        printf("read,%zu,%ld,%.2f\n", boyutlar[k], cagri, en_iyi);
    }

    double en_iyi = 1e18;
    for (int t = 0; t < TUR; t++) {
        double t0 = simdi_ms();
        oku_fgetc(yol, &sag);
        double dt = simdi_ms() - t0;
        if (dt < en_iyi) en_iyi = dt;
    }
    printf("stdio_fgetc,1,-1,%.2f\n", en_iyi);
    fprintf(stderr, "# sağ=%u\n", sag);
    return 0;
}
