# -*- coding: utf-8 -*-
"""b40_8_sozlesme.py: JSON Schema ile sozlesme dogrulamasi.

Iki parca: (1) istek govdesi dogrulamasi, (2) tuketici odakli
sozlesme testi: API'nin gercek yanit govdesi istemcinin
beklentisine uyuyor mu?
"""

import jsonschema

import b40_6_ihafilo_api as api

# Istemcinin (tuketicinin) bekledigi yanit bicimi.
YANIT_SEMA = {
    "type": "object",
    "required": ["id", "ad", "tip", "durum"],
    "properties": {
        "id": {"type": "integer", "minimum": 1},
        "ad": {"type": "string"},
        "tip": {"enum": ["sabit_kanat", "dortrotor"]},
        "durum": {"enum": ["hazir", "ucuyor", "bakimda"]},
    },
}


def hatalar(sema, nesne):
    dogrulayici = jsonschema.Draft202012Validator(sema)
    return [
        ("/".join(str(p) for p in e.path) or "(kok)", e.message)
        for e in dogrulayici.iter_errors(nesne)
    ]


def istek_testi():
    ornekler = [
        {"ad": "ALFA-1", "tip": "sabit_kanat"},
        {"ad": "ALFA-1", "tipp": "sabit_kanat"},
        {"ad": "A", "tip": "helikopter", "durum": "ucuyor"},
    ]
    for i, o in enumerate(ornekler, 1):
        h = hatalar(api.IHA_SEMA, o)
        if not h:
            print("ornek %d: gecerli" % i)
            continue
        print("ornek %d:" % i)
        for alan, mesaj in h:
            print("  %s: %s" % (alan, mesaj))


def sozlesme_testi():
    # Gercek kod yolunu calistirir: HTTP katmani olmadan.
    durum, nesne, _, _ = api.ihalari_olustur(
        "ali", {"ad": "ZETA-9", "tip": "dortrotor"}, None
    )
    print("provider durum:", durum)
    print("yanit gecerli mi:", hatalar(YANIT_SEMA, nesne) == [])
    kirik = dict(nesne)
    kirik["state"] = kirik.pop("durum")  # alan adini degistirmek
    print("alan adi degisince:", hatalar(YANIT_SEMA, kirik))


if __name__ == "__main__":
    istek_testi()
    sozlesme_testi()
