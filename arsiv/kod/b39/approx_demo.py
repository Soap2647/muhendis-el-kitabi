import pytest

print(0.1 + 0.2 == pytest.approx(0.3))
print(1e-13 == pytest.approx(0))
print(1000000.5 == pytest.approx(1000000.0))
print(0.1 + 0.2 == 0.3)
