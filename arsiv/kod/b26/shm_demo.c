/* shm_demo.c: POSIX paylaşılan bellek. Çocuk yazar, ebeveyn okur.
 * Derleme: gcc -O2 -Wall -Wextra -std=c11 -D_DEFAULT_SOURCE */
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#define AD "/b26_demo"
#define BOY 4096

int main(void)
{
    int fd = shm_open(AD, O_CREAT | O_RDWR, 0600);
    if (fd < 0) { perror("shm_open"); return 1; }
    if (ftruncate(fd, BOY) < 0) { perror("ftruncate"); return 1; }

    char *p = mmap(NULL, BOY, PROT_READ | PROT_WRITE,
                   MAP_SHARED, fd, 0);
    if (p == MAP_FAILED) { perror("mmap"); return 1; }

    pid_t pid = fork();     /* çocuk aynı fiziksel sayfayı görür */
    if (pid == 0) {
        strcpy(p, "çocuk yazdı");
        _exit(0);
    }
    waitpid(pid, NULL, 0);
    printf("ebeveyn okudu: \"%s\"\n", p);

    munmap(p, BOY);
    close(fd);
    shm_unlink(AD);         /* ad sistemden kaldırılır */
    return 0;
}
