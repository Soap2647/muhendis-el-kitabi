#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    if (argc != 3)
        return 1;
    int lo = atoi(argv[1]);      /* çalışma anında okunur */
    int hi = atoi(argv[2]);
    int yanlis = (lo + hi) / 2;          /* işaretli taşma: UB */
    int dogru = lo + (hi - lo) / 2;      /* taşmaz */
    printf("INT_MAX=%d\n", INT_MAX);
    printf("yanlis=%d dogru=%d\n", yanlis, dogru);
    return 0;
}
