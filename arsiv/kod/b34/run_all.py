# run_all.py: her bölüm betiğini çalıştırır, çıktıyı $ satırıyla birlikte kaydeder
import os
import subprocess
import sys

KLASOR = os.path.dirname(os.path.abspath(__file__))
os.chdir(KLASOR)
env = dict(os.environ, PYTHONIOENCODING="utf-8")
KOMUTLAR = [
    ("sema", "b34_sema.py iha.db"),
    ("sira", "b34_sira.py iha.db"),
    ("join", "b34_join.py iha.db"),
    ("ozyin", "b34_ozyin.py iha.db"),
    ("pencere", "b34_pencere.py iha.db"),
    ("upsert", "b34_upsert.py iha.db"),
    ("plan", "b34_plan.py iha.db"),
    ("savepoint", "b34_savepoint.py"),
    ("enjeksiyon", "b34_enjeksiyon.py iha.db"),
    ("ornek1", "b34_ornek1.py iha.db"),
    ("ornek2", "b34_ornek2.py iha.db"),
    ("ornek3", "b34_ornek3.py iha.db"),
    ("ornek4", "b34_ornek4.py iha.db"),
    ("kodokuma", "b34_kodokuma.py"),
    ("kilit", "b34_kilit.py"),
]
for ad, arg in KOMUTLAR:
    p = subprocess.run([sys.executable] + arg.split(), env=env,
                       capture_output=True, text=True, encoding="utf-8")
    cikti = p.stdout + p.stderr
    with open(os.path.join(KLASOR, "cikti", "T_%s.txt" % ad), "w",
              encoding="utf-8", newline="\n") as f:
        f.write("$ python %s\n" % arg)
        f.write(cikti.rstrip("\n") + "\n")
    print(ad, p.returncode, len(cikti.splitlines()))
