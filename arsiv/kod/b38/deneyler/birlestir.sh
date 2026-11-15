#!/bin/bash
# Birleştirme deneyleri: hızlı ileri, üç yollu, çakışma. Sabit tarihler.
export GIT_AUTHOR_NAME="Kitap Deneme" GIT_AUTHOR_EMAIL="deneme@example.com"
export GIT_COMMITTER_NAME="Kitap Deneme" GIT_COMMITTER_EMAIL="deneme@example.com"
export GIT_AUTHOR_DATE="2026-01-10T12:00:00+0300" GIT_COMMITTER_DATE="2026-01-10T12:00:00+0300"
taban() {
  rm -rf "$1" && mkdir "$1" && cd "$1"
  git init -q -b main
  git config --local user.name "Kitap Deneme"
  git config --local user.email "deneme@example.com"
  git config --local core.autocrlf false
  printf '1 giris\n2 ortak\n3 orta\n4 son\n' > m.txt
  git add m.txt && git commit -q -m "taban"
}
echo "=== A) hizli ileri"
taban "$T/ma"
git switch -q -c ozellik-a
printf '1 giris\n2 ortak\n3 orta\n4 son\n5 yeni\n' > m.txt
git commit -qam "ozellik a: 5 eklendi"
git switch -q main
git merge --ff-only ozellik-a
git log --oneline --graph --all
echo "=== B) uc yollu birlestirme (farkli satirlar)"
taban "$T/mb"
git switch -q -c ozellik-b
printf '1 giris\n2 B-degisti\n3 orta\n4 son\n' > m.txt
git commit -qam "ozellik b: 2. satir"
git switch -q main
printf '1 giris\n2 ortak\n3 orta\n4 MAIN-degisti\n' > m.txt
git commit -qam "main: 4. satir"
echo "--- ortak ata:"; git merge-base main ozellik-b
git merge --no-edit ozellik-b
git log --oneline --graph --all
echo "--- birlesme commit'inin ebeveynleri:"; git cat-file -p HEAD | sed -n 1,3p
echo "=== C) cakisma"
taban "$T/mc"
git switch -q -c ozellik-c
printf '1 giris\n2 ortak\n3 C-versiyon\n4 son\n' > m.txt
git commit -qam "ozellik c: 3. satir"
git switch -q main
printf '1 giris\n2 ortak\n3 MAIN-versiyon\n4 son\n' > m.txt
git commit -qam "main: 3. satir"
git merge ozellik-c; echo "exit=$?"
echo "--- dosya:"; cat m.txt
echo "--- indeks asamalari (1=taban 2=ours 3=theirs):"; git ls-files -u
echo "--- :1 :2 :3 icerik"; for s in 1 2 3; do echo "stage $s: $(git show :$s:m.txt | sed -n 3p)"; done
echo "--- cozum: ours'i sec, ekle, commit"
git checkout --ours m.txt && git add m.txt && git commit -q --no-edit && git log --oneline --graph --all && cat m.txt
