#include <stdio.h>
#include <stdlib.h>

/* HATA: taban durumu yok. Her çağrı kendini çağırır. */
long faktoriyel(int n) {
    return n * faktoriyel(n - 1);
}

int main(int argc, char **argv) {
    if (argc != 2)
        return 1;
    printf("%ld\n", faktoriyel(atoi(argv[1])));
    return 0;
}
