import os
import sys


def getUser(id, list=[]):
    for u in list:
        if u["id"] == id:
            return u
    return None


def ort(xs):
    try:
        return sum(xs) / len(xs)
    except:
        pass


def is_ok(x):
    if x == None:
        return False
    return True
