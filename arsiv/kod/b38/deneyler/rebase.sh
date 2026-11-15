#!/bin/bash
# Rebase, autosquash, cherry-pick, revert. Sabit tarihler.
export GIT_AUTHOR_NAME="Kitap Deneme" GIT_AUTHOR_EMAIL="deneme@example.com"
export GIT_COMMITTER_NAME="Kitap Deneme" GIT_COMMITTER_EMAIL="deneme@example.com"
export GIT_AUTHOR_DATE="2026-01-10T12:00:00+0300" GIT_COMMITTER_DATE="2026-01-10T12:00:00+0300"
D="$T/rb"; rm -rf "$D" && mkdir "$D" && cd "$D"
git init -q -b main
git config --local user.name "Kitap Deneme"
git config --local user.email "deneme@example.com"
git config --local core.autocrlf false
echo "a" > a.txt && git add a.txt && git commit -q -m "taban"
git switch -q -c ozellik
echo "b1" > b.txt && git add b.txt && git commit -q -m "ozellik: b1"
echo "c1" > c.txt && git add c.txt && git commit -q -m "ozellik: c1"
echo "d1" > d.txt && git add d.txt && git commit -q -m "ozellik: d1"
git switch -q main
echo "m1" > m.txt && git add m.txt && git commit -q -m "main: m1"
echo "=== once"
git log --oneline --graph --all
echo "ozellik ucu eski: $(git rev-parse --short ozellik)"
echo "=== rebase"
git switch -q ozellik
git rebase main
echo "ozellik ucu yeni: $(git rev-parse --short HEAD)"
git log --oneline --graph --all
echo "=== fixup: b1'e duzeltme"
B1=$(git log --format=%h --grep="ozellik: b1")
echo "b1 duzeltildi" > b.txt && git add b.txt && git commit -q --fixup=$B1
git log --oneline -1
GIT_SEQUENCE_EDITOR=true git rebase -q -i --autosquash main
echo "--- autosquash sonrasi:"
git log --oneline --graph --all
echo "=== cherry-pick: main'e tek commit"
git switch -q main
git cherry-pick ozellik~1
git log --oneline -2
echo "=== revert: gecmisi silmeden tersini kaydet"
git revert --no-edit HEAD
git log --oneline -3
echo "--- son durum:"; git status --short; ls
