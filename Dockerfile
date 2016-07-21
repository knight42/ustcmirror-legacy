FROM ustclug/alpine:3.4
MAINTAINER Jian Zeng <anonymousknight96 AT gmail.com>
ENV PATH /opt/ustcsync/bin:$PATH
ENTRYPOINT ["ustcsync"]
RUN apk update &&  apk add --update bash git lftp rsync && rm -rf /var/cache
COPY etc /opt/ustcsync/etc/
COPY bin /opt/ustcsync/bin/
