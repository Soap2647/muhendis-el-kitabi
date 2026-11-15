#!/bin/bash
echo "### A"; echo "uid dışarıda: $(id -u)"; unshare -r sh -c 'echo "uid içeride: $(id -u)"'
echo "### B"; readlink /proc/$$/ns/pid; unshare -r -p -f --mount-proc sh -c 'readlink /proc/$$/ns/pid; echo "PID: $$"; ps -e -o pid,comm'
echo "### C"; unshare -r -u sh -c 'hostname konteyner; echo "içeride: $(hostname)"'; echo "dışarıda: $(hostname)"
echo "### D"; cat /proc/self/cgroup; unshare -r -C sh -c 'cat /proc/self/cgroup'
echo "### E"; cat /sys/fs/cgroup/init.scope/memory.max /sys/fs/cgroup/init.scope/pids.max 2>&1
echo "### F"; mkdir /sys/fs/cgroup/init.scope/deneme 2>&1 | head -1
echo "### G"; ls -l /proc/self/ns/ | head -4 | sed 's/^.*\(ns\/\)/\1/'
