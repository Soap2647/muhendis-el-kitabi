import os, subprocess, sys, time
os.environ["PYTHONIOENCODING"] = "utf-8"
sira = ["g01_parca.py", "g02_geri_getirme.py", "g03_bootstrap.py",
        "g04_ivf.py", "g06_kuantizasyon.py", "g07_kv.py",
        "g08_spekulatif.py", "g09_kisit.py", "g10_ajan.py",
        "g11_pii.py", "g12_servis.py", "g13_gecikme.py", "g14_eval.py"]
for f in sira:
    t = time.time()
    r = subprocess.run([sys.executable, f], capture_output=True,
                       encoding="utf-8", errors="replace")
    ad = f[:-3] + ".txt"
    with open(os.path.join("cikti", ad), "w", encoding="utf-8") as h:
        h.write(r.stdout)
        if r.returncode:
            h.write("\nHATA:\n" + r.stderr)
    print(f, r.returncode, round(time.time() - t), "sn", flush=True)
print("KOSU_BITTI", flush=True)
