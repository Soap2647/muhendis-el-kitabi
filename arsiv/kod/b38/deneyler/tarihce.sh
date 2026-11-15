#!/bin/bash
# Elle tarihçe kurar: blob -> tree -> commit. Deterministik: tarihler sabit.
set -e
export GIT_AUTHOR_NAME="Kitap Deneme" GIT_AUTHOR_EMAIL="deneme@example.com"
export GIT_COMMITTER_NAME="Kitap Deneme" GIT_COMMITTER_EMAIL="deneme@example.com"
rm -rf "$1" && mkdir "$1" && cd "$1"
git init -q -b main
git config --local user.name "Kitap Deneme"
git config --local user.email "deneme@example.com"
git config --local core.autocrlf false
printf 'int kare(int x) { return x * x; }\n' > mat.c
printf 'int kare(int x);\n' > mat.h
B1=$(git hash-object -w mat.c); B2=$(git hash-object -w mat.h)
printf "100644 blob %s\tmat.c\n100644 blob %s\tmat.h\n" $B1 $B2 > l1.txt
T1=$(git mktree < l1.txt)
C1=$(GIT_AUTHOR_DATE="2026-01-10T10:00:00+0300" GIT_COMMITTER_DATE="2026-01-10T10:00:00+0300" git commit-tree $T1 -m "ilk surum")
git update-ref refs/heads/main $C1
printf 'int kare(int x) { return x * x; }\nint kup(int x) { return x*x*x; }\n' > mat.c
B3=$(git hash-object -w mat.c)
printf "100644 blob %s\tmat.c\n100644 blob %s\tmat.h\n" $B3 $B2 > l2.txt
T2=$(git mktree < l2.txt)
C2=$(GIT_AUTHOR_DATE="2026-01-11T09:30:00+0300" GIT_COMMITTER_DATE="2026-01-11T09:30:00+0300" git commit-tree $T2 -p $C1 -m "kup eklendi")
git update-ref refs/heads/main $C2 -m "elle kuruldu"
echo "C1=$C1"
echo "C2=$C2"
