#!/bin/bash
set -e
D=$(mktemp -d /tmp/bisect_demo.XXXX)
cd "$D"
git init -q .
git config user.email a@b.c
git config user.name t
for i in $(seq 1 100); do
  if [ "$i" -lt 61 ]; then echo "ok $i" > f.txt; else echo "bad $i" > f.txt; fi
  git add f.txt
  git commit -qm "c$i"
done
printf '#!/bin/sh\ngrep -q ok f.txt\n' > /tmp/bisect_test.sh
chmod +x /tmp/bisect_test.sh
git bisect start HEAD HEAD~99 >/dev/null
git bisect run /tmp/bisect_test.sh > /tmp/bisect_out.txt 2>&1 || true
grep -E "is the first bad commit|Bisecting" /tmp/bisect_out.txt | head -5
grep -c "^running" /tmp/bisect_out.txt || true
git bisect log | grep -c "^# " || true
cd /tmp
rm -rf "$D"
