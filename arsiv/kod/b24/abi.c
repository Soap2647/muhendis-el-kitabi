/* Çağrı kuralları ve sistem çağrısı (x86-64, GCC) */
#include <stdio.h>
#include <unistd.h>

/* System V AMD64 (Linux, varsayılan) */
long sysv_bes(long a, long b, long c, long d, long e)
{
    return a + 2 * b + 3 * c + 4 * d + 5 * e;
}

/* Windows x64 kuralı: GCC'nin ms_abi uygulaması */
__attribute__((ms_abi))
long ms_bes(long a, long b, long c, long d, long e)
{
    return a + 2 * b + 3 * c + 4 * d + 5 * e;
}

/* yaprak fonksiyon: yığın işaretçisini değiştirmez */
int yaprak_tampon(int x)
{
    volatile int t[2];
    t[0] = x;
    t[1] = x + 1;
    return t[0] + t[1];
}

/* syscall: getppid (x86-64'te numara 110) */
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
    printf("sysv=%ld ms=%ld tampon=%d\n",
           sysv_bes(1, 2, 3, 4, 5), ms_bes(1, 2, 3, 4, 5),
           yaprak_tampon(4));
    printf("ppid_syscall=%ld\n", sistem_getppid());
    return 0;
}
