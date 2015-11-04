FROM ubuntu:trusty

# sshd is disabled for upstart
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install python openssh-server && \
    sed -ri 's/#?UsePAM .*/UsePAM no/g' /etc/ssh/sshd_config && \
    echo "manual" > /etc/init/ssh.override && \
    mkdir -p /var/run/sshd

ADD https://raw.githubusercontent.com/mitchellh/vagrant/master/keys/vagrant.pub /root/.ssh/authorized_keys
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
