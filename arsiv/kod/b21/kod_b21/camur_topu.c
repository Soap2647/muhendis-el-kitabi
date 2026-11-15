/* camur_topu.c: her sey tek dosyada (big ball of mud).
 * Gomulu telemetri simulasyonu. Donanim sahte: ADC yerine LCG,
 * UART yerine printf, SD karti yerine bellekte bir tampon. */
#include <stddef.h>
#include <stdio.h>
#include <string.h>

#define KANAL_SAYI 4   /* 0 termistor, 1 gerilim, 2 basinc, 3 pil */
#define FILTRE_N 4
#define ALARM_ESIK 80.0
#define LOG_BOYUT 512
#define DONGU_SAYI 6

static unsigned tohum = 42u;
static const int taban[KANAL_SAYI] = {1500, 1000, 1200, 1100};
static int adc_son[KANAL_SAYI];
static double filtre[KANAL_SAYI][FILTRE_N];
static double son[KANAL_SAYI];
static double enk[KANAL_SAYI], enb[KANAL_SAYI];
static int dongu_no;
static int alarm_sayisi;
static int pil_uyari_sayisi;
static int watchdog;
static int reset_sayisi;
static char sd_log[LOG_BOYUT];
static size_t sd_uzun;

/* UART'tan gelen komutlar (sahte): dongu numarasina gore */
static const char *gelen[DONGU_SAYI] = {"", "", "", "R", "", "S"};

static int hal_adc_oku(int kanal)
{
    tohum = tohum * 1103515245u + 12345u;
    return taban[kanal] + (int)((tohum >> 16) % 50u);
}

static void sensorleri_oku(void)
{
    for (int k = 0; k < KANAL_SAYI; k++)
        adc_son[k] = hal_adc_oku(k);
    watchdog++;
}

static double kalibre(int kanal, int ham)
{
    switch (kanal) {
    case 0: return ham * 0.1 - 40.0;          /* termistor, C */
    case 1: return ham * 3.3 / 4095.0;        /* gerilim, V */
    case 2: return ham * 0.05;                /* basinc, kPa */
    default: return ham * 3.3 * 2.0 / 4095.0; /* pil, V (bolucu 2) */
    }
}

static void uart_gonder(const char *metin)
{
    printf("UART> %s\n", metin);
}

static void sd_yaz(const char *satir)
{
    size_t n = strlen(satir);
    if (sd_uzun + n + 2 <= sizeof sd_log) {   /* tasma sigortasi */
        memcpy(sd_log + sd_uzun, satir, n);
        sd_uzun += n;
        sd_log[sd_uzun++] = '\n';
        sd_log[sd_uzun] = '\0';
    }
}

static void filtrele(int kanal)
{
    double v = kalibre(kanal, adc_son[kanal]);
    int n = dongu_no < FILTRE_N ? dongu_no + 1 : FILTRE_N;
    double toplam = 0.0;
    filtre[kanal][dongu_no % FILTRE_N] = v;
    for (int i = 0; i < n; i++)
        toplam += filtre[kanal][i];
    son[kanal] = toplam / n;
    if (dongu_no == 0 || son[kanal] > enb[kanal])
        enb[kanal] = son[kanal];
    if (dongu_no == 0 || son[kanal] < enk[kanal])
        enk[kanal] = son[kanal];
}

static void komut_isle(int no)
{
    if (gelen[no][0] == 'R') {
        reset_sayisi++;
        memset(filtre, 0, sizeof filtre);
        dongu_no = 0;
        uart_gonder("RESET OK");
    } else if (gelen[no][0] == 'S') {
        printf("durum: dongu=%d alarm=%d\n", no, alarm_sayisi);
    }
}

static void alarm_kontrol(void)
{
    if (son[0] > ALARM_ESIK) {
        alarm_sayisi++;
        printf("ALARM termistor %.2f\n", son[0]);
    }
    if (son[3] < 0.85) {
        pil_uyari_sayisi++;
        printf("UYARI pil %.3f\n", son[3]);
    }
}

static void telemetri_satiri(void)
{
    char satir[96];
    snprintf(satir, sizeof satir, "T=%.2f V=%.3f P=%.2f B=%.3f",
             son[0], son[1], son[2], son[3]);
    uart_gonder(satir);
    sd_yaz(satir);
}

static void dongu(int no)
{
    sensorleri_oku();
    komut_isle(no);
    for (int k = 0; k < KANAL_SAYI; k++)
        filtrele(k);
    alarm_kontrol();
    telemetri_satiri();
    dongu_no++;
}

int main(void)
{
    for (int t = 0; t < DONGU_SAYI; t++)
        dongu(t);
    for (int k = 0; k < KANAL_SAYI; k++)
        printf("kanal %d min=%.3f maks=%.3f\n", k, enk[k], enb[k]);
    printf("alarm=%d pil=%d reset=%d watchdog=%d sd=%zu\n",
           alarm_sayisi, pil_uyari_sayisi, reset_sayisi,
           watchdog, sd_uzun);
    fputs(sd_log, stdout);
    return 0;
}
