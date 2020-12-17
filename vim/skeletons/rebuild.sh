#!/usr/bin/env bash
clear
date

fail() { local z="$?"; echo -e "\033[01;31m[$(date +'%H:%M:%S%P')] FAIL[$z]: $@\033[0m" >&2; exit 1; }
win() { echo -e "\033[01;32m[$(date +'%H:%M:%S%P')] $@\033[0m" >&2; }
say() { echo -e "\033[01;35m[$(date +'%H:%M:%S%P')] $@\033[0m" >&2; }

say "about to do something"

echo winning || fail did not win

win rebuild.sh OK
