#!/bin/bash
set -u
rm -rf /tmp/b42repo && mkdir /tmp/b42repo
cp -r /mnt/c/Users/merty/AppData/Local/Temp/b42/proje/. /tmp/b42repo/
cd /tmp/b42repo && rm -rf dist api/__pycache__
git init -q && git config user.name "Kitap Deneme" && git config user.email deneme@example.com
git add -A && git commit -q -m "ilk surum" && git tag -a v1.2.0 -m "surum 1.2.0"
echo '$ ./ci.sh tum'
bash ci.sh tum; echo "tum_rc=$?"
echo '$ ./ci.sh imaj (IMAJ_ZORUNLU=1)'
IMAJ_ZORUNLU=1 bash ci.sh imaj; echo "imaj_rc=$?"
echo '$ ./ci.sh bilinmeyen'
bash ci.sh bilinmeyen; echo "bilinmeyen_rc=$?"
echo "--- SHA256SUMS:"; cat dist/SHA256SUMS
echo "--- saglik.py (API calismiyor):"
cd api && python3 saglik.py; echo "saglik_rc=$?"
PORT=8080 python3 telemetri_api.py > /tmp/api8080.log 2>&1 &
APIPID=$!; sleep 1
python3 saglik.py; echo "saglik_rc=$? (API calisirken)"
kill -TERM $APIPID; sleep 1; wait $APIPID 2>/dev/null; echo "api_rc=$?"
echo "--- api 8080 gunlugu:"; cat /tmp/api8080.log
