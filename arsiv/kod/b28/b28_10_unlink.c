/* b28_10_unlink.c: açık dosya silinince ne olur? */
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <sys/stat.h>

static void goster(const char *etiket, int fd)
{
    struct stat st;
    if (fstat(fd, &st) < 0) { perror("fstat"); return; }
    printf("%-18s ino=%lu nlink=%lu boyut=%ld\n", etiket,
           (unsigned long)st.st_ino, (unsigned long)st.st_nlink,
           (long)st.st_size);
}

int main(void)
{
    const char *yol = "gecici.txt";
    char tampon[64] = {0};

    int fd = open(yol, O_RDWR | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); return 1; }
    if (write(fd, "silinecek veri\n", 15) != 15) return 1;
    goster("silmeden önce:", fd);

    if (unlink(yol) < 0) { perror("unlink"); return 1; }
    printf("ad var mı?        %s\n",
           access(yol, F_OK) == 0 ? "evet" : "hayır");
    goster("unlink sonrası:", fd);

    if (lseek(fd, 0, SEEK_SET) < 0) return 1;
    ssize_t r = read(fd, tampon, sizeof tampon - 1);
    printf("fd hâlâ okuyor:   %zd bayt -> \"%.14s\"\n", r, tampon);

    if (write(fd, "yeni\n", 5) != 5) return 1;
    goster("yazdıktan sonra:", fd);

    close(fd);
    int acilamadi = open(yol, O_RDONLY) < 0 && errno == ENOENT;
    printf("close sonrası ad yok: %s\n",
           acilamadi ? "evet" : "hayır");
    return 0;
}
