/* b28_8_mmap_olcum.c: read() ile mmap() karşılaştırması ve
 * MAP_SHARED. Çıktı: yontem,sure_ms,minflt (en iyi 3 tur) */
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <time.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/resource.h>

#define TUR 3
#define TAMPON (64 * 1024)

static double simdi_ms(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e3 + t.tv_nsec / 1e6;
}

/* Bu süreçteki küçük sayfa hatası (minor fault) sayısı */
static long minflt(void)
{
    struct rusage ru;
    getrusage(RUSAGE_SELF, &ru);
    return ru.ru_minflt;
}

static unsigned toplam_read(const char *yol)
{
    static char t[TAMPON];
    unsigned s = 0;
    int fd = open(yol, O_RDONLY);
    ssize_t r;
    while ((r = read(fd, t, TAMPON)) > 0)
        for (ssize_t i = 0; i < r; i += 4096)
            s += (unsigned char)t[i];
    close(fd);
    return s;
}

static unsigned toplam_mmap(const char *yol)
{
    int fd = open(yol, O_RDONLY);
    struct stat st;
    fstat(fd, &st);
    const unsigned char *p = mmap(NULL, st.st_size, PROT_READ,
                                  MAP_PRIVATE, fd, 0);
    unsigned s = 0;
    for (off_t i = 0; i < st.st_size; i += 4096)
        s += p[i];
    munmap((void *)p, st.st_size);
    close(fd);
    return s;
}

static void olc(const char *ad, unsigned (*f)(const char *),
                const char *yol)
{
    double en_iyi = 1e18;
    long hata = 0;
    unsigned s = 0;
    for (int t = 0; t < TUR; t++) {
        long f0 = minflt();
        double t0 = simdi_ms();
        s = f(yol);
        double dt = simdi_ms() - t0;
        long df = minflt() - f0;
        if (dt < en_iyi) { en_iyi = dt; hata = df; }
    }
    printf("%s,%.2f,%ld\n", ad, en_iyi, hata);
    fprintf(stderr, "# %s sağ=%u\n", ad, s);
}

/* MAP_SHARED: sayfa, dosyanın önbellek kopyasıdır; yazılan bayt
 * msync'ten sonra read() ile görülür. */
static void paylasimli_demo(void)
{
    const char *yol = "paylasim.bin";
    int fd = open(yol, O_RDWR | O_CREAT | O_TRUNC, 0644);
    if (ftruncate(fd, 4096) < 0) return;
    char *p = mmap(NULL, 4096, PROT_READ | PROT_WRITE,
                   MAP_SHARED, fd, 0);
    memcpy(p, "merhaba", 7);
    p[0] = 'Z';
    msync(p, 4096, MS_SYNC);
    munmap(p, 4096);
    lseek(fd, 0, SEEK_SET);
    char b[8] = {0};
    if (read(fd, b, 7) != 7) return;
    printf("MAP_SHARED: read() görünümü = \"%s\"\n", b);
    close(fd);
}

int main(int argc, char **argv)
{
    const char *yol = argc > 1 ? argv[1] : "veri.bin";
    printf("yontem,sure_ms,minflt\n");
    olc("read_64K", toplam_read, yol);
    olc("mmap", toplam_mmap, yol);
    paylasimli_demo();
    return 0;
}
