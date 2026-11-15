/* b28_5_atomik.c: yerinde yazma ve atomik yazmanın çökme testi */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/wait.h>

#define YOL   "yapi.conf"
#define ESKI  "surum=1 esik=10 aktif=1\n"
#define YENI  "surum=2 esik=25 aktif=1 yeni=abcdefgh\n"

/* Kırılgan yöntem: dosyayı yerinde aç, sıfırla, yaz. */
static void yerinde_yaz(const char *veri, size_t n, int kir)
{
    int fd = open(YOL, O_WRONLY | O_TRUNC | O_CREAT, 0644);
    size_t yarim = n / 2;
    if (write(fd, veri, yarim) < 0) _exit(2);
    if (kir == 1) _exit(7);            /* yarım yazıldı: çökme */
    if (write(fd, veri + yarim, n - yarim) < 0) _exit(2);
    close(fd);
}

/* Atomik yöntem: geçici dosya, fsync, rename, dizin fsync. */
static void atomik_yaz(const char *veri, size_t n, int kir)
{
    const char *tmp = YOL ".tmp";
    int fd = open(tmp, O_WRONLY | O_TRUNC | O_CREAT, 0644);
    size_t yarim = n / 2;
    if (write(fd, veri, yarim) < 0) _exit(2);
    if (kir == 1) _exit(7);            /* geçici dosya yarım */
    if (write(fd, veri + yarim, n - yarim) < 0) _exit(2);
    if (kir == 2) _exit(7);            /* tam yazıldı, fsync yok */
    if (fsync(fd) < 0) _exit(2);
    close(fd);
    if (kir == 3) _exit(7);            /* rename'den önce */
    if (rename(tmp, YOL) < 0) _exit(2);
    if (kir == 4) _exit(7);            /* rename'den sonra */
    int dfd = open(".", O_RDONLY);
    if (dfd >= 0) { fsync(dfd); close(dfd); }
}

/* 0: ESKI, 1: YENI, -1: ne eski ne yeni (bozuk) */
static int dogrula(void)
{
    char tampon[128] = {0};
    int fd = open(YOL, O_RDONLY);
    if (fd < 0) return -1;
    ssize_t r = read(fd, tampon, sizeof tampon - 1);
    close(fd);
    if (r < 0) return -1;
    if (strcmp(tampon, ESKI) == 0) return 0;
    if (strcmp(tampon, YENI) == 0) return 1;
    return -1;
}

static void sifirla(void)
{
    int fd = open(YOL, O_WRONLY | O_TRUNC | O_CREAT, 0644);
    if (write(fd, ESKI, strlen(ESKI)) < 0) _exit(2);
    close(fd);
}

int main(int argc, char **argv)
{
    int atomik = argc > 1 && strcmp(argv[1], "atomik") == 0;
    int deneme = 500;
    int eski = 0, yeni = 0, bozuk = 0;

    for (int i = 0; i < deneme; i++) {
        sifirla();
        int kir = i % 5;               /* 0..4: çökme noktası */
        /* yerinde yazmada yalnız 0 ve 1 noktaları var */
        if (!atomik && kir > 1) kir = 0;

        pid_t pid = fork();
        if (pid == 0) {
            if (atomik) atomik_yaz(YENI, strlen(YENI), kir);
            else        yerinde_yaz(YENI, strlen(YENI), kir);
            _exit(0);
        }
        int durum;
        waitpid(pid, &durum, 0);

        int s = dogrula();
        if (s == 0) eski++;
        else if (s == 1) yeni++;
        else bozuk++;
    }
    printf("yöntem=%s deneme=%d eski=%d yeni=%d bozuk=%d\n",
           atomik ? "atomik" : "yerinde", deneme, eski, yeni, bozuk);
    return 0;
}
