FROM ustclug/apt-mirror:latest
MAINTAINER Jian Zeng <anonymousknight96 AT gmail.com>
ENTRYPOINT ["apt-mirror", "/apt.conf"]
ADD apt.conf /
