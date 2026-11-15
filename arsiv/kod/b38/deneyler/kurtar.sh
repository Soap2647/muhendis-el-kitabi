#!/bin/bash
export GIT_AUTHOR_NAME="Kitap Deneme" GIT_AUTHOR_EMAIL="deneme@example.com"
export GIT_COMMITTER_NAME="Kitap Deneme" GIT_COMMITTER_EMAIL="deneme@example.com"
D="$T/kz"; rm -rf "$D" && mkdir "$D" && cd "$D"
git init -q -b main && git config --local user.name "Kitap Deneme" && git config --local user.email "deneme@example.com" && git config --local core.autocrlf false
c(){ GIT_AUTHOR_DATE="$1" GIT_COMMITTER_DATE="$1" git commit -q -m "$2"; }
echo "v1" > a.txt && git add a.txt && c "2026-01-10T10:00:00+0300" "a ilk"
echo "v2" > a.txt && git add a.txt && c "2026-01-10T11:00:00+0300" "a ikinci"
echo "onemli is" > b.txt && git add b.txt && c "2026-01-10T12:00:00+0300" "deneysel is"
echo '$ git log --oneline'; git log --oneline
echo '$ git reset --hard HEAD~1'; git reset --hard HEAD~1
echo '$ git log --oneline'; git log --oneline
echo '$ git reflog'; git reflog
echo '$ git fsck --no-reflogs'; git fsck --no-reflogs 2>&1
echo '$ git reset --hard HEAD@{1}'; git reset -q --hard HEAD@{1}
echo '$ git log --oneline'; git log --oneline
echo '$ cat b.txt'; cat b.txt
