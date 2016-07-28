FROM ustclug/mirror:latest
MAINTAINER Jian Zeng <anonymousknight96 AT gmail.com>
ADD ["sync.sh", "/usr/bin/"]
VOLUME /srv/repo/infinality-bundle /opt/ustcsync/log/infinality-bundle
ENTRYPOINT ["sync.sh"]
