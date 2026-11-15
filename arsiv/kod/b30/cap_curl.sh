#!/bin/bash
cd "C:/Users/merty/AppData/Local/Temp/b30"
export PYTHONIOENCODING=utf-8
S=http://127.0.0.1:8100
python -I b30_4_http_sunucu.py site 8100 6 > cikti/b30_4_log_raw.txt 2>&1 &
sleep 1
{
echo '$ S=http://127.0.0.1:8100'
echo '$ curl -i $S/ornek/not.txt'
curl -s -i $S/ornek/not.txt; echo
echo '$ curl -i -H '"'"'If-None-Match: "7932a007eaf77af7"'"'"' $S/ornek/not.txt'
curl -s -i -H 'If-None-Match: "7932a007eaf77af7"' $S/ornek/not.txt; echo
echo '$ curl -i $S/yok.html'
curl -s -i $S/yok.html; echo
echo '$ curl -i -X POST $S/'
curl -s -i -X POST $S/; echo
echo '$ curl -i --path-as-is $S/../b30_4_http_sunucu.py'
curl -s -i --path-as-is $S/../b30_4_http_sunucu.py; echo
echo '$ curl -v $S/ornek/not.txt $S/index.html'
curl -sv $S/ornek/not.txt $S/index.html 2>&1 | grep -E "left intact|^< HTTP"
} > cikti/b30_4_curl_raw.txt 2>&1
sleep 1
grep -v "^dinleniyor" cikti/b30_4_log_raw.txt > cikti/b30_4_log.txt
cat cikti/b30_4_curl_raw.txt
echo ==== LOG
cat cikti/b30_4_log.txt
