/* Kırmızı bölge: yaprak fonksiyon rsp'yi değiştirmeden kullanır */
int kirmizi(int x)
{
    volatile int t[2];   /* volatile: bellekte kalmak zorunda */
    t[0] = x;
    t[1] = x + 1;
    return t[0] + t[1];
}
