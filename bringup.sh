#!/bin/bash
user="${2:-$USER}"
docker run --rm -v "$1":/var/spool/apt-mirror -u "$(id -u $user):$(id -g $user)" ustclug/apt-dockerproject-mirror:latest
