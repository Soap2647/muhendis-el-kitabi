# -*- coding: utf-8 -*-
"""Tum Bolum 64 betiklerini son haliyle calistirir; ciktilari yazar."""
import os
import subprocess
import time

ORDER = [
    ("test_np64.py", "out_test_np64.txt"),
    ("adam_iz.py", "out_adam_iz.txt"),
    ("bn_ornek.py", "out_bn_ornek.txt"),
    ("takvim_ornek.py", "out_takvim_ornek.txt"),
    ("t01_batch.py", "out_t01_batch.txt"),
    ("t02_optim.py", "out_t02_optim.txt"),
    ("t03a_yorunge.py", "out_t03a_yorunge.txt"),
    ("t03b_lr_aralik.py", "out_t03b_lr_aralik.txt"),
    ("t04_takvim.py", "out_t04_takvim.txt"),
    ("t05_baslatma.py", "out_t05_baslatma.txt"),
    ("t06_bn.py", "out_t06_bn.txt"),
    ("t07_duzenlilestirme.py", "out_t07_duzenlilestirme.txt"),
    ("t08_gradyan.py", "out_t08_gradyan.txt"),
    ("t09_teshis.py", "out_t09_teshis.txt"),
    ("t09b_nan.py", "out_t09b_nan.txt"),
    ("t10_tek_batch.py", "out_t10_tek_batch.txt"),
    ("t11_arama.py", "out_t11_arama.txt"),
    ("bozuk_egitim.py", "out_bozuk_egitim.txt"),
    ("bozuk_egitim_duzeltilmis.py", "out_bozuk_egitim_duzeltilmis.txt"),
]
env = dict(os.environ, PYTHONIOENCODING="utf-8")
for script, out in ORDER:
    t0 = time.time()
    r = subprocess.run(["python", script], capture_output=True,
                       env=env, encoding="utf-8", errors="replace")
    with open(out, "w", encoding="utf-8") as f:
        f.write(r.stdout)
        if r.returncode != 0:
            f.write("\nSTDERR:\n" + r.stderr)
    print(script, "exit", r.returncode,
          "%.0fs" % (time.time() - t0), flush=True)
print("TAMAM", flush=True)
