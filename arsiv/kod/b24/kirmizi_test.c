#include <stdio.h>
#include <unistd.h>

int kirmizi(int x);

static inline long sistem_getppid(void)
{
    long r;
    __asm__ volatile("syscall"
                     : "=a"(r)
                     : "a"(110L)
                     : "rcx", "r11", "memory");
    return r;
}

int main(void)
{
    long sc = sistem_getppid();
    printf("kirmizi(4)=%d\n", kirmizi(4));
    printf("syscall_ppid=%ld getppid=%d eslesme=%s\n", sc,
           (int)getppid(), sc == getppid() ? "evet" : "hayir");
    return 0;
}
