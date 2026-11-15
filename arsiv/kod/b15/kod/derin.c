#include <stdio.h>
#include <stdlib.h>

/* Her çerçeve ~100 bayt yerel veri taşır. */
long derin(long n) {
    volatile char tampon[100];
    tampon[0] = (char)n;
    if (n == 0)
        return 0;
    return 1 + derin(n - 1) + tampon[0] * 0;
}

int main(int argc, char **argv) {
    if (argc != 2)
        return 1;
    long n = atol(argv[1]);
    printf("derin(%ld) = %ld\n", n, derin(n));
    return 0;
}
