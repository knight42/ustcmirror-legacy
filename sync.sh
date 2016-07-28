#!/bin/bash

LOGDIR='/opt/ustcsync/log/infinality-bundle/'
[[ -d $LOGDIR ]] || mkdir -p "$LOGDIR"
exec > >(tee -a "$LOGDIR/update.log") 2>&1

MIRRORNAME="$(hostname -f)"
TO='/srv/repo/infinality-bundle'
NPROC="$(getconf _NPROCESSORS_ONLN)"
LOCK="$TO/Archive-Update-in-Progress-$MIRRORNAME"
OPTIONS="-X $LOCK --parallel=$NPROC -cev --skip-noaccess"

touch "$LOCK"
trap 'rm -f $LOCK &> /dev/null' EXIT

[[ -d $TO/multilib ]] || mkdir -p "$TO/multilib"

lftp -e "
set xfer:log true
open http://bohoomil.com/repo/i686/
mirror $OPTIONS ../i686  $TO/
mirror $OPTIONS ../x86_64  $TO/
mirror $OPTIONS ../fonts  $TO/
mirror $OPTIONS ../multilib/x86_64 $TO/multilib/
bye"

savelog -qc 20 "$LOGDIR/update.log"
