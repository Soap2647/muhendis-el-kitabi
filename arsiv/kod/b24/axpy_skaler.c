/* SIMD deneyi: skaler referans (vektörleşme kapalı derlenir) */
void axpy_skaler(float *y, const float *x, float a, int n)
{
    for (int i = 0; i < n; i++)
        y[i] = a * x[i] + y[i];
}
