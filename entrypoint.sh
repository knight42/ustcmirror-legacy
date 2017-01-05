#!/bin/bash
uid="${uid:-0}"
gid="${gid:-0}"
chown -R "$uid:$gid" /var/spool/apt-mirror/skel
sudo -u "#$uid" -g "#$gid" apt-mirror /apt.conf
