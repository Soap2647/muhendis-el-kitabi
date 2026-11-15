#!/bin/bash
echo "== E3a: PID 1 zombi toplamıyor (yetim torunlar) =="
unshare -r -p -f --mount-proc python3 -c '
import os, subprocess, time
subprocess.run(["sh", "-c", "sleep 0.3 & exit 0"])   # torun yetim kalır
time.sleep(1.0)
for p in sorted(os.listdir("/proc"), key=lambda s: (not s.isdigit(), s)):
    if not p.isdigit(): continue
    try:
        f = open("/proc/%s/stat" % p).read()
    except OSError:
        continue
    alan = f.rsplit(")", 1)[1].split()
    durum, ppid = alan[0], alan[1]
    comm = f[f.index("(")+1:f.rindex(")")]
    print("pid=%s ppid=%s durum=%s ad=%s" % (p, ppid, durum, comm))
' 2>&1 | grep -v "screen size"
echo "== E3b: cgroup v2 sınır dosyaları (okuma) =="
cat /proc/self/cgroup
CG=/sys/fs/cgroup$(sed -n 's/^0:://p' /proc/self/cgroup)
echo "cgroup yolu: $CG"
for f in cgroup.controllers memory.max memory.current cpu.max pids.max; do
  printf "%-18s " $f; cat $CG/$f 2>&1 | head -1
done
echo "== E3c: alt cgroup oluşturma denemesi =="
mkdir $CG/b42_demo 2>&1 && echo "oluştu" || echo "izin yok (cgroup delegasyonu yok)"
echo "== E3d: cgroup ad alanı =="
unshare -r -C sh -c 'cat /proc/self/cgroup'
