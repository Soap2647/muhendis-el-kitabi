#include <stdint.h>
#include <stdio.h>

static uintptr_t taban = 0;

long faktoriyel(int n) {
    volatile int yerel = n;
    uintptr_t adres = (uintptr_t)&yerel;
    if (taban == 0)
        taban = adres;
    printf("n=%d  taban'dan uzaklik=%ld bayt\n", n,
           (long)(taban - adres));
    if (n <= 1)
        return 1;
    return n * faktoriyel(n - 1);
}

int main(void) {
    printf("faktoriyel(4) = %ld\n", faktoriyel(4));
    return 0;
}
