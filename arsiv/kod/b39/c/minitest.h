/* minitest.h: birkaç satırlık birim test çatısı (Bölüm 39). */
#ifndef MINITEST_H
#define MINITEST_H
#include <stdio.h>

static int mt_gecen = 0;
static int mt_kalan = 0;

#define CHECK(kosul) do { \
    if (kosul) { mt_gecen++; } \
    else { mt_kalan++; \
        printf("  BAŞARISIZ %s:%d: %s\n", \
               __FILE__, __LINE__, #kosul); } \
} while (0)

#define CHECK_EQ(a, b) do { \
    long long mt_a = (long long)(a); \
    long long mt_b = (long long)(b); \
    if (mt_a == mt_b) { mt_gecen++; } \
    else { mt_kalan++; \
        printf("  BAŞARISIZ %s:%d: %s == %s (%lld != %lld)\n", \
               __FILE__, __LINE__, #a, #b, mt_a, mt_b); } \
} while (0)

#define MT_SONUC() do { \
    printf("%d geçti, %d başarısız\n", mt_gecen, mt_kalan); \
    return mt_kalan == 0 ? 0 : 1; \
} while (0)

#endif
