/* fork_temel.c: fork sonrası değişken bağımsızlığı.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11
 *          -D_POSIX_C_SOURCE=200809L */
#include <stdio.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

int main(void)
{
    int sayac = 10;
    setvbuf(stdout, NULL, _IONBF, 0); /* tampon karışıklığını önle */

    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");
        return 1;
    }

    if (pid == 0) {                   /* çocuk: fork 0 döndürdü */
        sayac += 5;
        printf("çocuk : pid=%d ppid=%d sayac=%d\n",
               (int)getpid(), (int)getppid(), sayac);
        return 0;
    }

    int durum = 0;
    /* çocuğu bekle: zombi bırakma */
    waitpid(pid, &durum, 0);
    printf("ebeveyn: pid=%d çocuk=%d sayac=%d\n",
           (int)getpid(), (int)pid, sayac);
    return 0;
}
