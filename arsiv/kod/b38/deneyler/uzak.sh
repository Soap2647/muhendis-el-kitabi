#!/bin/bash
# Çıplak uzak depo + iki geliştirici (a, b). Sabit tarihler.
export GIT_AUTHOR_NAME="Kitap Deneme" GIT_AUTHOR_EMAIL="deneme@example.com"
export GIT_COMMITTER_NAME="Kitap Deneme" GIT_COMMITTER_EMAIL="deneme@example.com"
export GIT_AUTHOR_DATE="2026-01-10T12:00:00+0300" GIT_COMMITTER_DATE="2026-01-10T12:00:00+0300"
cfg(){ git config --local user.name "Kitap Deneme"; git config --local user.email "deneme@example.com"; git config --local core.autocrlf false; }
R="$T/uzak.git"; rm -rf "$R" "$T/a" "$T/b" "$T/ilk"
git init -q --bare -b main "$R"
echo "=== 0) ilk kurulum"
mkdir "$T/ilk" && cd "$T/ilk" && git init -q -b main && cfg && git config --local core.autocrlf false
printf 'satir1\nsatir2\nsatir3\n' > not.txt && git add not.txt && git commit -q -m "ilk surum"
git remote add origin "$R" && git push -q -u origin main && cd "$T"
git -c core.autocrlf=false clone -q "$R" "$T/a" && git -c core.autocrlf=false clone -q "$R" "$T/b"
(cd "$T/a" && cfg) ; (cd "$T/b" && cfg)
echo "=== 1) b, bir commit gonderir"
cd "$T/b" && echo "b-degisikligi" >> not.txt && git commit -qam "b: sonuna ekle" && git push -q origin main && git log --oneline -1
echo "=== 2) a, uzaktan geride; commit yapip push ederse"
cd "$T/a" && echo "a-degisikligi" >> yeni.txt && git add yeni.txt && git commit -q -m "a: yeni dosya"
git push origin main 2>&1 | grep -E "rejected|non-fast|hint: Updates" | head -3; echo "push exit=${PIPESTATUS[0]}"
echo "=== 3) fetch: dosyalara dokunmadan uzakta ne var?"
git fetch -q origin && git log --oneline --graph --all | head -6
echo "izleme dali: $(git rev-parse --abbrev-ref --symbolic-full-name @{u})"
echo "=== 4) pull: fetch + merge (farkli dosyalar, cakisma yok)"
git pull -q --no-rebase --no-edit && git log --oneline --graph | head -4 && git push -q origin main && echo "push basarili"
echo "=== 5) ayni satirda cakisma"
cd "$T/b" && git pull -q --no-rebase --no-edit && sed -i 's/satir2/B-satir2/' not.txt && git commit -qam "b: satir2" && git push -q origin main
cd "$T/a" && sed -i 's/satir2/A-satir2/' not.txt && git commit -qam "a: satir2"
git pull --no-rebase --no-edit 2>&1 | head -4; echo "--- cakisma dosyasi:"; sed -n 1,8p not.txt
echo "--- refspec ve uzaklar:"; git config --get-all remote.origin.fetch; git remote -v | head -2
echo "--- ls-remote:"; git ls-remote origin | head -4
