#!/bin/bash
# Her reset türünü aynı başlangıç durumundan dener ve üç ağacı raporlar.
export GIT_AUTHOR_NAME="Kitap Deneme" GIT_AUTHOR_EMAIL="deneme@example.com"
export GIT_COMMITTER_NAME="Kitap Deneme" GIT_COMMITTER_EMAIL="deneme@example.com"
kur() {
  rm -rf "$1" && mkdir "$1" && cd "$1"
  git init -q -b main
  git config --local user.name "Kitap Deneme"
  git config --local user.email "deneme@example.com"
  git config --local core.autocrlf false
  c(){ GIT_AUTHOR_DATE="$1" GIT_COMMITTER_DATE="$1" git commit -q -m "$2"; }
  echo "v1" > a.txt; git add a.txt; c "2026-01-10T10:00:00+0300" "a ilk"
  echo "v2" > a.txt; git add a.txt; c "2026-01-10T11:00:00+0300" "a ikinci"
  echo "v3" > a.txt; git add a.txt; echo "v4" > a.txt
}
rapor() {
  echo "  HEAD=$(git show HEAD:a.txt)  INDEX=$(git show :a.txt)  CALISMA=$(cat a.txt)  commit=$(git log --oneline | wc -l)"
}
for mod in soft mixed hard; do
  kur "$T/r_$mod"
  echo "reset --$mod HEAD~1 (once):"; rapor
  git reset -q --$mod HEAD~1
  echo "reset --$mod HEAD~1 (sonra):"; rapor
done
