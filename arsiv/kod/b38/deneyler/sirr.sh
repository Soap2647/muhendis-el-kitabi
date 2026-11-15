#!/bin/bash
export GIT_AUTHOR_NAME="Kitap Deneme" GIT_AUTHOR_EMAIL="deneme@example.com"
export GIT_COMMITTER_NAME="Kitap Deneme" GIT_COMMITTER_EMAIL="deneme@example.com"
D="$T/sir2"; rm -rf "$D" && mkdir "$D" && cd "$D"
git init -q -b main && git config --local user.name "Kitap Deneme" && git config --local user.email "deneme@example.com" && git config --local core.autocrlf false
c(){ GIT_AUTHOR_DATE="$1" GIT_COMMITTER_DATE="$1" git commit -q -m "$2"; }
echo "uygulama=1" > ayar.env && git add ayar.env && c "2026-01-10T10:00:00+0300" "ayarlar"
echo "API_ANAHTARI=AKIAIOSFODNN7EXAMPLE" >> ayar.env && git add ayar.env && c "2026-01-10T11:00:00+0300" "api anahtari eklendi"
echo "uygulama=1" > ayar.env && git add ayar.env && c "2026-01-10T12:00:00+0300" "anahtar kaldirildi"
echo '$ cat ayar.env'; cat ayar.env
echo '$ git log --oneline'; git log --oneline
echo '$ git show HEAD~1:ayar.env'; git show HEAD~1:ayar.env
echo '$ git log --oneline -S "AKIAIOSFODNN7EXAMPLE"'; git log --oneline -S "AKIAIOSFODNN7EXAMPLE"
