#!/bin/bash
export GIT_AUTHOR_NAME="Kitap Deneme" GIT_AUTHOR_EMAIL="deneme@example.com"
export GIT_COMMITTER_NAME="Kitap Deneme" GIT_COMMITTER_EMAIL="deneme@example.com"
export GIT_AUTHOR_DATE="2026-01-10T12:00:00+0300" GIT_COMMITTER_DATE="2026-01-10T12:00:00+0300"
S=$T/hk_src
cd "$T" && rm -rf hk && mkdir hk && cd hk
git init -q -b main && git config --local user.name "Kitap Deneme" && git config --local user.email "deneme@example.com" && git config --local core.autocrlf false && git config --local core.hooksPath .githooks
mkdir -p tools .githooks
cp $S/tools/*.py tools/ && cp $S/.githooks/* .githooks/ && chmod +x .githooks/*
git add . && git commit -q -m "chore(hook): denetim betikleri" && git log --oneline -1
echo "=== 1) temiz dosya, iyi mesaj"
echo 'print("merhaba")' > ok.py && git add ok.py && git commit -q -m "feat(io): merhaba yazdır"; echo "exit=$?"
echo "=== 2) 90 karakterlik satır"
python -c "print('x'*90)" > uzun.py && git add uzun.py && git commit -q -m "fix(io): uzun satır"; echo "exit=$?"; git rm -q -f --cached uzun.py; rm -f uzun.py
echo "=== 3) sahte anahtar"
echo 'K = "AKIA0123456789ABCDEF"' > anahtar.py && git add anahtar.py && git commit -q -m "feat(auth): anahtar"; echo "exit=$?"; git rm -q -f --cached anahtar.py; rm -f anahtar.py
echo "=== 4) kötü commit mesajı"
echo "x" > k.txt && git add k.txt && git commit -q -m "düzeltme"; echo "exit=$?"; git rm -q -f --cached k.txt; rm -f k.txt
echo "=== 5) indeks esas alınır: sahnelenmemiş sır commit'i engellemez"
echo 'K = "AKIA0123456789ABCDEF"' >> ok.py
echo "temiz satır" > temiz.txt && git add temiz.txt && git commit -q -m "docs(not): temiz dosya"; echo "exit=$?"
git status --short
git checkout -q -- ok.py
git log --oneline
