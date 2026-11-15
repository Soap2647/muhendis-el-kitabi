/* b53_toplam.c - kayan nokta toplamasi: parca sayisi, birlesme sirasi
 * ve Kahan (telafili) toplam.
 * Derleme: gcc -O2 -std=c11 b53_toplam.c -o toplam
 * (-ffast-math KULLANMA: Kahan'i derleyici silerdi.)
 * Veri: xorshift32 tohum 53; N = 10^7 float, degerler [0,1).
 * Parcalar ayri ayri toplanir, sonra SIRAYLA birlestirilir: bu,
 * p is parcaciginin ayni islemi matematiksel olarak yapmasidir.
 */
#include <stdio.h>
#include <stdlib.h>

#define N 10000000

static float veri[N];
static unsigned int xs = 53u;

static float rastgele(void) {
    xs ^= xs << 13;
    xs ^= xs >> 17;
    xs ^= xs << 5;
    return (float)(xs / 4294967296.0);
}

/* Duz float toplam. */
static float duz(const float *x, long n) {
    float s = 0.0f;
    for (long i = 0; i < n; i++) s += x[i];
    return s;
}

/* Kahan: c, kaybedilen dusuk bitleri geri besler. */
static float kahan(const float *x, long n) {
    float s = 0.0f, c = 0.0f;
    for (long i = 0; i < n; i++) {
        float y = x[i] - c;
        float t = s + y;
        c = (t - s) - y;
        s = t;
    }
    return s;
}

int main(void) {
    for (long i = 0; i < N; i++) veri[i] = rastgele();
    /* Referans: long double ile seri toplam (yakl. dogru). */
    long double acc = 0.0L;
    for (long i = 0; i < N; i++) acc += veri[i];
    double ref = (double)acc;
    printf("referans (long double) = %.3f\n", ref);
    printf("p,duz_float,hata_duz,kahan_parca,hata_kahan\n");
    int pler[] = {1, 2, 3, 4, 6, 8, 12, 16};
    for (int k = 0; k < 8; k++) {
        int p = pler[k];
        float dt = 0.0f, kt = 0.0f;
        long pay = N / p;
        for (int j = 0; j < p; j++) {
            long lo = j * pay;
            long hi = (j == p - 1) ? N : lo + pay;
            /* Parca toplamlari sirayla birlestirilir. */
            dt += duz(veri + lo, hi - lo);
            kt += kahan(veri + lo, hi - lo);
        }
        printf("%d,%.3f,%.3e,%.3f,%.3e\n", p, dt,
               (dt - ref) / ref, kt, (kt - ref) / ref);
    }
    return 0;
}
