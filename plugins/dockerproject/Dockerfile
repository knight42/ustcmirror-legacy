FROM ustclug/apt-mirror:latest
MAINTAINER Jian Zeng <anonymousknight96 AT gmail.com>
ENTRYPOINT ["/entrypoint.sh"]
ADD ["apt.conf", "entrypoint.sh", "/"]
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -y install sudo && apt-get clean && rm -rf /var/lib/apt/lists/*
