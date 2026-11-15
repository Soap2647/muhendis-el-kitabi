#!/bin/bash
set -e
rm -rf /tmp/b42repo && mkdir /tmp/b42repo
cp -r /mnt/c/Users/merty/AppData/Local/Temp/b42/proje/. /tmp/b42repo/
cd /tmp/b42repo
rm -rf api/__pycache__
git init -q && git config user.name "Kitap Deneme" && git config user.email deneme@example.com
git add -A && git commit -q -m "ilk surum" && git tag -a v1.2.0 -m "surum 1.2.0"
echo "\$ git describe --tags --always --dirty   (etiket tam üstünde)"
git describe --tags --always --dirty
echo "değişiklik" >> README.md
git add -A && git commit -q -m "kucuk degisiklik"
echo "\$ git describe --tags --always --dirty   (etiketten sonra 1 commit)"
git describe --tags --always --dirty
echo "değişiklik" >> ci.sh
echo "\$ git describe --tags --always --dirty   (kirli çalışma ağacı)"
git describe --tags --always --dirty
