#include <stdio.h>
#include <stdlib.h>

static int cmp(const void *k, const void *e) {
    int x = *(const int *)k, y = *(const int *)e;
    return (x > y) - (x < y);
}

int main(void) {
    int a[] = {1, 2, 2, 2, 3};
    int key = 2;
    int *p = bsearch(&key, a, 5, sizeof a[0], cmp);
    printf("bsearch key=2 -> index %ld\n", p ? (long)(p - a) : -1L);
    int k2 = 9;
    int *q = bsearch(&k2, a, 5, sizeof a[0], cmp);
    printf("bsearch key=9 -> %s\n", q ? "bulundu" : "NULL");
    return 0;
}
