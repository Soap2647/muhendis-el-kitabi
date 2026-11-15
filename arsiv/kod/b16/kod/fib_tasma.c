/* fib_tasma.c: Fibonacci tablosu ve tamsayi tasmasi */
#include <stdio.h>

int main(void) {
    unsigned long long f[95];
    f[0] = 0;
    f[1] = 1;
    for (int i = 2; i < 95; i++)
        f[i] = f[i - 1] + f[i - 2];  /* unsigned: sarma (tanimli) */
    for (int i = 92; i <= 94; i++)
        printf("F(%d) = %llu\n", i, f[i]);
    printf("unsigned long long maksimum: %llu\n", ~0ULL);
    return 0;
}
