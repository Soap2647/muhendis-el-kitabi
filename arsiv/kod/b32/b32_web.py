# -*- coding: utf-8 -*-
"""b32_web.py: oturum cerezi bayraklari ve CSRF jetonu.

Kullanim: python b32_web.py
"""
import hmac
import secrets
from http import cookies


def oturum_cerezi(deger):
    c = cookies.SimpleCookie()
    c["oturum"] = deger
    c["oturum"]["path"] = "/"
    c["oturum"]["max-age"] = 1800          # 30 dakika
    c["oturum"]["httponly"] = True         # JavaScript okuyamaz
    c["oturum"]["secure"] = True           # yalnizca HTTPS
    c["oturum"]["samesite"] = "Lax"     # capraz site istek yok
    return c["oturum"].OutputString()


def csrf_jetonu_uret():
    return secrets.token_urlsafe(32)       # 256 bit, oturuma bagli


def csrf_dogrula(oturum_jetonu, form_jetonu):
    if not oturum_jetonu or not form_jetonu:
        return False
    return hmac.compare_digest(oturum_jetonu, form_jetonu)


if __name__ == "__main__":
    kimlik = secrets.token_urlsafe(32)
    print("Set-Cookie:")
    for parca in oturum_cerezi(kimlik).split("; "):
        print("   ", parca)
    j = csrf_jetonu_uret()
    print("csrf dogru:", csrf_dogrula(j, j))
    print("csrf yanlis:", csrf_dogrula(j, csrf_jetonu_uret()))
    print("csrf eksik:", csrf_dogrula(j, ""))
