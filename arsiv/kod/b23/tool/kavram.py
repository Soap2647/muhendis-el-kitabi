# Komut-sorgu ayrimi: kotu ve iyi
kuyruk_kotu = [5, 7]


def al_kotu(kuyruk):
    return kuyruk.pop(0)  # hem doner hem degistirir


kuyruk_iyi = [5, 7]


def ilk(kuyruk):
    return kuyruk[0]


def cikar(kuyruk):
    del kuyruk[0]


if __name__ == "__main__":
    print("kotu:", al_kotu(kuyruk_kotu), kuyruk_kotu)
    print("iyi :", ilk(kuyruk_iyi), end=" ")
    cikar(kuyruk_iyi)
    print(kuyruk_iyi)
