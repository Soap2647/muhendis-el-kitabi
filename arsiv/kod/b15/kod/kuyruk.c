#include <stdio.h>
#include <stdlib.h>

/* Kuyruk özyinelemesi: çağrı, fonksiyonun son işi. */
long topla_kuyruk(long n, long birikim) {
    if (n == 0)
        return birikim;
    return topla_kuyruk(n - 1, birikim + n);
}

/* Kuyruk değil: 1 + ... sonucu çağrıdan sonra eklenir. */
long topla_derin(long n) {
    if (n == 0)
        return 0;
    return n + topla_derin(n - 1);
}

int main(int argc, char **argv) {
    if (argc != 3)
        return 1;
    long n = atol(argv[2]);
    if (argv[1][0] == 'k')
        printf("kuyruk(%ld) = %ld\n", n, topla_kuyruk(n, 0));
    else
        printf("derin(%ld) = %ld\n", n, topla_derin(n));
    return 0;
}
