#!/bin/bash
export GIT_AUTHOR_NAME="Kitap Deneme" GIT_AUTHOR_EMAIL="deneme@example.com"
export GIT_COMMITTER_NAME="Kitap Deneme" GIT_COMMITTER_EMAIL="deneme@example.com"
D="$T/bs"; rm -rf "$D" && mkdir "$D" && cd "$D"
git init -q -b main && git config --local user.name "Kitap Deneme" && git config --local user.email "deneme@example.com" && git config --local core.autocrlf false
printf 'limit=100\n' > limit.txt
printf '#!/bin/sh\n# iyi (0) = limit 100 ; kotu (1) = degil\ngrep -q "^limit=100$" limit.txt\n' > test.sh
git add . && GIT_AUTHOR_DATE="2026-01-10T09:00:00+0300" GIT_COMMITTER_DATE="2026-01-10T09:00:00+0300" git commit -q -m "taban"
for k in $(seq 1 128); do
  printf 'kayit %03d\n' $k >> gunluk.txt
  if [ $k -eq 91 ]; then echo "limit=99" > limit.txt; fi
  GIT_AUTHOR_DATE="2026-01-10T12:00:00+0300" GIT_COMMITTER_DATE="2026-01-10T12:00:00+0300" git add -A && GIT_AUTHOR_DATE="2026-01-10T$(printf %02d $((k%24))):00:00+0300" GIT_COMMITTER_DATE="2026-01-10T$(printf %02d $((k%24))):00:00+0300" git commit -q -m "is $k"
done
echo "toplam commit: $(git rev-list --count HEAD)"
echo "=== bisect"
git bisect start
git bisect bad HEAD
git bisect good HEAD~127
git bisect run sh test.sh > bisect_cikti.txt 2>&1; grep -E "Bisecting|is the first bad commit|is [0-9a-f]{7}" bisect_cikti.txt | head -12; git bisect log | head -3
git bisect reset
echo "=== pickaxe: limit=99 metnini ilk ekleyen commit"
git log --oneline -S "limit=99" 
echo "=== blame limit.txt"
git blame limit.txt
