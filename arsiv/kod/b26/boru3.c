/* boru3.c: cat /etc/passwd | grep -E "^root" | wc -l
 * Süreç 1: cat   stdout -> p1 yazma
 * Süreç 2: grep  stdin <- p1 okuma, stdout -> p2 yazma
 * Süreç 3: wc    stdin <- p2 okuma
 * Derleme: gcc -O2 -Wall -Wextra -std=c11
 *          -D_POSIX_C_SOURCE=200809L boru3.c
 * -DHATA_ACIK: ebeveyn boruların uçlarını kapatmaz. */
#include <stdio.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void)
{
    int p1[2], p2[2];
    if (pipe(p1) < 0 || pipe(p2) < 0) {
        perror("pipe");
        return 1;
    }

    pid_t c1 = fork();
    if (c1 == 0) {                   /* cat */
        dup2(p1[1], STDOUT_FILENO);
        close(p1[0]); close(p1[1]);
        close(p2[0]); close(p2[1]);
        execlp("cat", "cat", "/etc/passwd", (char *)NULL);
        _exit(127);
    }

    pid_t c2 = fork();
    if (c2 == 0) {                   /* grep */
        dup2(p1[0], STDIN_FILENO);
        dup2(p2[1], STDOUT_FILENO);
        close(p1[0]); close(p1[1]);
        close(p2[0]); close(p2[1]);
        execlp("grep", "grep", "-E", "^root", (char *)NULL);
        _exit(127);
    }

    pid_t c3 = fork();
    if (c3 == 0) {                   /* wc */
        dup2(p2[0], STDIN_FILENO);
        close(p1[0]); close(p1[1]);
        close(p2[0]); close(p2[1]);
        execlp("wc", "wc", "-l", (char *)NULL);
        _exit(127);
    }

#ifndef HATA_ACIK
    /* ebeveyn kopyaları da kapatır */
    close(p1[0]); close(p1[1]);
    close(p2[0]); close(p2[1]);
#endif
    waitpid(c1, NULL, 0);
    waitpid(c2, NULL, 0);
    waitpid(c3, NULL, 0);
    return 0;
}
