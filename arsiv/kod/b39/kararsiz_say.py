"""test_rastgele_zar'ı n kez ayrı süreçte çalıştırıp sayar."""
import subprocess
import sys

n = int(sys.argv[1])
basarisiz = 0
for _ in range(n):
    r = subprocess.run([sys.executable, "-m", "pytest", "-q",
                        "--no-header", "-p", "no:cacheprovider",
                        "test_kararsiz.py::test_rastgele_zar"],
                       capture_output=True)
    if r.returncode != 0:
        basarisiz += 1
print("%d koşu: %d başarısız, %d başarılı" % (
    n, basarisiz, n - basarisiz))
