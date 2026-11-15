import json


def derinlik(veri):
    if isinstance(veri, dict):
        return 1 + max((derinlik(v) for v in veri.values()),
                       default=0)
    if isinstance(veri, list):
        return 1 + max((derinlik(v) for v in veri), default=0)
    return 0


def anahtar_say(veri):
    if isinstance(veri, dict):
        return len(veri) + sum(anahtar_say(v)
                               for v in veri.values())
    if isinstance(veri, list):
        return sum(anahtar_say(v) for v in veri)
    return 0


if __name__ == "__main__":
    metin = ('{"kullanici": {"ad": "Mert", "roller": '
             '["ogrenci", {"seviye": 3}]}, "aktif": true}')
    veri = json.loads(metin)
    print("derinlik =", derinlik(veri))
    print("anahtar  =", anahtar_say(veri))
    print(json.dumps(veri, ensure_ascii=False, indent=1))
