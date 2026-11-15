import os, subprocess, time
# Torun süreç yetim kalır: ebeveyni (sh) çıkar, PID 1 toplamaz
subprocess.run(["sh", "-c", "sleep 0.3 & exit 0"])
time.sleep(1.0)
for n in sorted(int(p) for p in os.listdir("/proc") if p.isdigit()):
    try:
        f = open("/proc/%d/stat" % n).read()
    except OSError:
        continue
    alan = f.rsplit(")", 1)[1].split()
    durum, ppid = alan[0], alan[1]
    comm = f[f.index("(") + 1:f.rindex(")")]
    print("pid=%d ppid=%s durum=%s ad=%s" % (n, ppid, durum, comm))
