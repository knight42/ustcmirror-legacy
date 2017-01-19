#!/bin/bash
uid="$(stat -c '%u' "$1")"
gid="$(stat -c '%g' "$1")"
name='apt.dockerproject.org'
docker run --rm --name "syncing-$name" --label=syncing \
    -e "uid=$uid" -e "gid=$gid" \
    -v "$1":/var/spool/apt-mirror/mirror/$name \
    -v "$2":/var/spool/apt-mirror/var \
    ustclug/apt-dockerproject-mirror:latest
