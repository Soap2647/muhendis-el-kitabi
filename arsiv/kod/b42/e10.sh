#!/bin/bash
cd /sys/fs/cgroup/init.scope && mkdir deneme
echo "rc=$?"
cd /sys/fs/cgroup/init.scope && cat memory.max pids.max
echo "--- ps:"
unshare -r -p -f --mount-proc sh -c 'readlink /proc/$$/ns/pid; \
    echo "PID: $$"; ps -e -o pid,comm'
echo "--- chroot home:"
R=/tmp/b42ov/rootfs; unshare -r -m chroot $R /bin/sh -c 'if [ -d /home ]; then echo var; \
  else echo yok; fi'
