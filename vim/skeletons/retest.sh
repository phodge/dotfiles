#!/usr/bin/env bash
clear
date

fail() { local z="$?"; echo -e "\e[01;31m[$(date +'%H:%M:%S%P')] FAIL[$z]: $@\e[0m" >&2; exit 1; }
win() { echo -e "\e[01;32m[$(date +'%H:%M:%S%P')] $@\e[0m" >&2; }
say() { echo -e "\e[01;34m[$(date +'%H:%M:%S%P')] $@\e[0m" >&2; }

say "about to do something"

echo winning || fail did not win

win retest.sh OK
