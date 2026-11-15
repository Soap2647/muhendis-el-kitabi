/* b28_1_temel.c: open, write, lseek, read, close ve O_APPEND */
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>

int main(void)
{
    const char *yol = "deneme.txt";
    unlink(yol);                        /* eski dosya varsa sil */

    int fd = open(yol, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd < 0) { perror("open"); return 1; }
    printf("ilk fd = %d\n", fd);

    ssize_t n = write(fd, "merhaba", 7);
    printf("write -> %zd\n", n);

    off_t p = lseek(fd, 0, SEEK_CUR);   /* ofseti sor, değiştirme */
    printf("lseek(SEEK_CUR) -> %ld\n", (long)p);
    close(fd);

    /* O_APPEND: her yazma önce dosya sonuna gider */
    fd = open(yol, O_WRONLY | O_APPEND);
    if (lseek(fd, 0, SEEK_SET) < 0) return 1;
    if (write(fd, " dunya", 6) != 6) return 1;
    close(fd);

    fd = open(yol, O_RDONLY);
    char buf[64] = {0};
    n = read(fd, buf, sizeof buf - 1);
    printf("read -> %zd, içerik=\"%s\"\n", n, buf);
    n = read(fd, buf, sizeof buf - 1);
    printf("EOF'ta read -> %zd\n", n);
    close(fd);

    if (write(fd, "x", 1) < 0)         /* kapalı fd: EBADF */
        printf("kapalı fd: errno=%d (%s)\n", errno, strerror(errno));
    return 0;
}
