#!/bin/bash
# 200 küçük değişiklikli sürüm; gevşek nesnelerden paketlemeye geçiş.
export GIT_AUTHOR_NAME="Kitap Deneme" GIT_AUTHOR_EMAIL="deneme@example.com"
export GIT_COMMITTER_NAME="Kitap Deneme" GIT_COMMITTER_EMAIL="deneme@example.com"
D="$T/pk"; rm -rf "$D" && mkdir "$D" && cd "$D"
git init -q -b main && git config --local user.name "Kitap Deneme" && git config --local user.email "deneme@example.com" && git config --local core.autocrlf false
python -I - <<'PY'
import random
random.seed(38)
satirlar = ["sensor %04d deger=%06d birim=mV\n" % (i, random.randint(0, 999999))
            for i in range(1500)]
open("olcum.log", "w").write("".join(satirlar))
PY
git add olcum.log && GIT_AUTHOR_DATE="2026-01-10T12:00:00+0300" GIT_COMMITTER_DATE="2026-01-10T12:00:00+0300" git commit -q -m "ilk olcum"
for i in $(seq 1 200); do
  python -I -c "
import random,sys
random.seed($i)
L=open('olcum.log').read().splitlines(True)
k=random.randrange(len(L))
L[k]='sensor %04d deger=%06d birim=mV\n' % (k, random.randint(0,999999))
open('olcum.log','w').write(''.join(L))"
  GIT_AUTHOR_DATE="2026-01-10T12:00:00+0300" GIT_COMMITTER_DATE="2026-01-10T12:00:00+0300" git commit -qam "olcum $i" 
done
echo "=== once (gevsek nesneler):"; git count-objects -v
echo "=== gc:"; git -c pack.threads=1 gc -q; git count-objects -v
echo "=== paket:"; ls -la .git/objects/pack/ | grep -E "pack|idx" | awk '{print $5, $9}'
