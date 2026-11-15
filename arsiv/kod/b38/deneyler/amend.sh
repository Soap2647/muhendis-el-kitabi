#!/bin/bash
export GIT_AUTHOR_NAME="Kitap Deneme" GIT_AUTHOR_EMAIL="deneme@example.com"
export GIT_COMMITTER_NAME="Kitap Deneme" GIT_COMMITTER_EMAIL="deneme@example.com"
export GIT_AUTHOR_DATE="2026-01-10T13:00:00+0300" GIT_COMMITTER_DATE="2026-01-10T13:00:00+0300"
cd "$T/b"
echo '$ git log --oneline -1'; git log --oneline -1
echo '$ git commit --amend -m "b: satir2 (mesaj duzeltildi)"'
git commit -q --amend -m "b: satir2 (mesaj duzeltildi)"
echo '$ git log --oneline -1'; git log --oneline -1
echo '$ git push origin main'; git push origin main 2>&1 | sed -n 2,3p
echo '$ git push --force-with-lease origin main'; git push --force-with-lease origin main 2>&1 | sed -n 2,2p
echo '$ cd a && git fetch && git log --oneline --graph --all -4'
cd "$T/a" && git fetch -q && git log --oneline --graph --all -4
