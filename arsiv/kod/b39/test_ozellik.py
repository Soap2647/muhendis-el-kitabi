import random
from collections import deque

import pytest
from hypothesis import given, settings, strategies as st

from halka import HalkaTampon
from ikili import ikili_arama, ikili_arama_hatali
from rle import coz, kodla


@settings(derandomize=True, max_examples=300)
@given(st.lists(st.integers(), unique=True).map(sorted),
       st.integers())
def test_ikili_arama_ozelligi(xs, hedef):
    i = ikili_arama(xs, hedef)
    if i == -1:
        assert hedef not in xs
    else:
        assert xs[i] == hedef


@settings(derandomize=True, max_examples=300)
@given(st.lists(st.integers(), unique=True).map(sorted),
       st.integers())
def test_hatali_ikili_arama_ozelligi(xs, hedef):
    i = ikili_arama_hatali(xs, hedef)
    if i == -1:
        assert hedef not in xs
    else:
        assert xs[i] == hedef


@settings(derandomize=True, max_examples=300)
@given(st.text())
def test_rle_gidis_donus(s):
    parcalar = kodla(s)
    assert coz(parcalar) == s
    assert all(k >= 1 for _, k in parcalar)
    assert all(a[0] != b[0] for a, b in zip(parcalar, parcalar[1:]))


def test_halka_referans_deque_ile():
    # Diferansiyel test: iki gerçekleme aynı işlemlerde aynı mı?
    rng = random.Random(42)
    t = HalkaTampon(4)
    ref = deque()
    for _ in range(5000):
        if rng.random() < 0.5:
            x = rng.randint(-9, 9)
            if len(ref) < 4:
                ref.append(x)
                t.ekle(x)
            else:
                with pytest.raises(BufferError):
                    t.ekle(x)
        elif ref:
            assert t.al() == ref.popleft()
        else:
            with pytest.raises(IndexError):
                t.al()
        assert len(t) == len(ref)
