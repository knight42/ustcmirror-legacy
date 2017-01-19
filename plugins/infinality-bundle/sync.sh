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
trap 'rm -f $LOCK; savelog -qc 20 $LOGDIR/update.log' EXIT

[[ -d $TO/multilib ]] || mkdir -p "$TO/multilib"

date '+===== started at %s %F %T ====='

lftp -e "
set xfer:log true
open http://bohoomil.com/repo/i686/
mirror $OPTIONS ../i686  $TO/
mirror $OPTIONS ../x86_64  $TO/
mirror $OPTIONS ../fonts  $TO/
mirror $OPTIONS ../multilib/x86_64 $TO/multilib/
bye"

if [ $? -eq 0 ]; then
    date '+%F %T' > "$LOGDIR/.lastsuccess"
    rm -f "$LOGDIR/.lastfail"
else
    date '+%F %T' > "$LOGDIR/.lastfail"
fi
