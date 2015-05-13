FROM debian:wheezy

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install python openssh-server && \
    mkdir -p /var/run/sshd

ADD https://raw.githubusercontent.com/mitchellh/vagrant/master/keys/vagrant.pub /root/.ssh/authorized_keys
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
