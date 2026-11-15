# uav.py -- sentetik IHA bakim tablosu (sabit tohum)
import numpy as np
import pandas as pd


def uav_veri(n=4000, seed=59, p_dondur=False):
    rng = np.random.default_rng(seed)
    motor = rng.normal(55, 8, n)  # motor sicakligi C
    titresim = 0.3 + rng.gamma(2.0, 0.12, n)  # RMS, g
    akim = rng.normal(15, 2.5, n)  # ortalama akim, A
    gerilim = np.abs(rng.normal(0.25, 0.08, n))  # gerilim dusumu, V
    saat = rng.uniform(0, 600, n)  # toplam ucus saati
    dongu = rng.uniform(0, 800, n)  # batarya dongusu
    gorev = rng.choice(["kesif", "gozetleme", "tasima"], n,
                       p=[0.4, 0.4, 0.2])
    ortam = rng.choice(["ilimli", "sicak", "tozlu"], n,
                       p=[0.5, 0.3, 0.2])
    seri = rng.permutation(100000)[:n]  # tekil kimlik
    # gizli dogru risk: dogrusal olmayan ve etkilesimli
    z = (-2.2 + 0.08 * (motor - 60) + 4.0 * (titresim - 0.5)
         + 3.0 * (titresim > 0.8) * (ortam == "tozlu")
         + 0.004 * np.maximum(saat - 350, 0)
         + 0.8 * (gorev == "tasima") + 0.002 * (dongu - 400) / 4)
    p = 1 / (1 + np.exp(-z))
    ariza = (rng.random(n) < p).astype(int)  # 7 gun ariza
    df = pd.DataFrame({
        "motor_sicaklik": motor, "titresim_rms": titresim,
        "akim_ort": akim, "gerilim_dusum": gerilim,
        "ucus_saati": saat, "batarya_dongu": dongu,
        "gorev": gorev, "ortam": ortam, "seri_no": seri,
    })
    if p_dondur:
        return df, ariza, p
    return df, ariza


if __name__ == "__main__":
    df, y = uav_veri()
    print("satir sayisi:", len(df), " sutun sayisi:", df.shape[1])
    print("ariza orani: %.3f" % y.mean())
