import statistics

import pytest
from hypothesis import given, settings, strategies as st

from kapsama_ornek import ortalama


@settings(derandomize=True, max_examples=300)
@given(st.lists(st.integers(-1000, 1000), min_size=1))
def test_ortalama_ozelligi(xs):
    assert ortalama(xs) == pytest.approx(statistics.fmean(xs))
