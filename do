#!/bin/bash
set -e

cmd=$1
shift
args="$@"

build_mbit () {
  yotta buil
}

push_mbit () {
  cp build/$(yt --plain target | head -n 1 | cut -f 1 -d" ")/source/$(yt --plain ls | head -n 1 | cut -f 1 -d" ")-combined.hex /media/$(whoami)/MICROBIT/
}

usage () {
    echo 'Usage: < read the actual script source >'
}

wrong_command () {
    echo "${0##*/} - unknown command: '${1}'" >&2
    usage
}

case $cmd in
  build_mbit) build_mbit;;
  push_mbit) push_mbit;;
  help|"") usage;;
  *) wrong_command "$cmd";;
esac