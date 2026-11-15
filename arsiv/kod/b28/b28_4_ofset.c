/* b28_4_ofset.c: fork sonrası paylaşılan dosya ofseti */
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/wait.h>

int main(void)
{
    const char *harf = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    char buf[8];

    int w = open("harf.txt", O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (write(w, harf, 26) != 26) return 1;
    close(w);

    int fd = open("harf.txt", O_RDONLY);     /* açık dosya A */
    int fd2 = open("harf.txt", O_RDONLY);    /* ayrı açık dosya B */

    pid_t pid = fork();
    if (pid == 0) {
        if (read(fd, buf, 5) != 5) _exit(1);
        buf[5] = '\0';
        printf("çocuk fd okudu: %s\n", buf);
        fflush(stdout);
        _exit(0);
    }
    wait(NULL);

    if (read(fd, buf, 5) != 5) return 1;
    buf[5] = '\0';
    printf("ana fd okudu:   %s\n", buf);

    if (read(fd2, buf, 5) != 5) return 1;
    buf[5] = '\0';
    printf("fd2 okudu:      %s\n", buf);

    printf("lseek(fd)  = %ld\n", (long)lseek(fd, 0, SEEK_CUR));
    printf("lseek(fd2) = %ld\n", (long)lseek(fd2, 0, SEEK_CUR));
    close(fd);
    close(fd2);
    return 0;
}
