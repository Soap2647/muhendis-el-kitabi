def olc_kosul(tip, ham):
    if tip == "sicaklik":
        return ham * 0.1 - 40.0
    elif tip == "basinc":
        return ham * 0.01
    elif tip == "nem":
        return min(max(ham, 0.0), 100.0)
    raise ValueError(tip)


DONUSUMLER = {
    "sicaklik": lambda ham: ham * 0.1 - 40.0,
    "basinc": lambda ham: ham * 0.01,
    "nem": lambda ham: min(max(ham, 0.0), 100.0),
}


def olc_tablo(tip, ham):
    try:
        return DONUSUMLER[tip](ham)
    except KeyError:
        raise ValueError(tip) from None


if __name__ == "__main__":
    for t, h in [("sicaklik", 650), ("basinc", 101325), ("nem", 120)]:
        print(t, olc_kosul(t, h), olc_tablo(t, h))
