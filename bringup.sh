#!/bin/bash
user="${3:-$USER}"
docker run --rm -v "$1":/srv/repo/infinality-bundle -v "$2":/opt/ustcsync/log/infinality-bundle -u "$(id -u $user):$(id -g $user)" --name syncing-infinality-bundle ustclug/infinality-bundle-mirror:latest
