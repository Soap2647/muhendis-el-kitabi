# ornek1_ders.py - Ders on kosullari: gecerli sira, dongu (Kahn).
from collections import deque


def ders_sirasi(dersler, onkosul):
    """onkosul: [(once, sonra)]. Donus: (sira, kalan). Dongu varsa
    sira kisadir ve kalan, siraya giremeyen dersleri listeler."""
    idx = {ad: i for i, ad in enumerate(dersler)}
    n = len(dersler)
    adj = [[] for _ in range(n)]
    derece = [0] * n
    for a, b in onkosul:
        adj[idx[a]].append(idx[b])
        derece[idx[b]] += 1
    kuyruk = deque(i for i in range(n) if derece[i] == 0)
    sira = []
    print("  baslangic kuyruk:", [dersler[i] for i in kuyruk])
    while kuyruk:
        u = kuyruk.popleft()
        sira.append(dersler[u])
        for v in adj[u]:
            derece[v] -= 1
            if derece[v] == 0:
                kuyruk.append(v)
        print(f"  {dersler[u]:<14} alindi; kuyruk:",
              [dersler[i] for i in kuyruk])
    kalan = [dersler[i] for i in range(n) if derece[i] > 0]
    return (sira if not kalan else None), kalan


if __name__ == "__main__":
    dersler = ["Programlama", "Matematik", "Veri Yapilari",
               "Algoritmalar",
               "Isletim", "Ag", "Derleyici", "Bitirme"]
    onkosul = [("Programlama", "Veri Yapilari"),
               ("Programlama", "Isletim"),
               ("Veri Yapilari", "Algoritmalar"),
               ("Matematik", "Algoritmalar"),
               ("Isletim", "Ag"), ("Veri Yapilari", "Derleyici"),
               ("Algoritmalar", "Derleyici"),
               ("Algoritmalar", "Bitirme"),
               ("Ag", "Bitirme"), ("Derleyici", "Bitirme")]
    sira, kalan = ders_sirasi(dersler, onkosul)
    print("Sira:", sira, "kalan:", kalan)
    print("--- ters kenar eklenirse ---")
    onkosul.append(("Derleyici", "Programlama"))
    sira, kalan = ders_sirasi(dersler, onkosul)
    print("Sira:", sira, "kalan:", kalan)
