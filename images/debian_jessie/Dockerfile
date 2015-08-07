FROM debian:jessie

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install python openssh-server \
        puppet salt-minion locales && \
    mkdir -p /var/run/sshd && \
    (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do if ! test $i = systemd-tmpfiles-setup.service; then rm -f $i; fi; done) && \
    rm -f /lib/systemd/system/multi-user.target.wants/* && \
    rm -f /etc/systemd/system/*.wants/* && \
    rm -f /lib/systemd/system/local-fs.target.wants/* && \
    rm -f /lib/systemd/system/sockets.target.wants/*udev* && \
    rm -f /lib/systemd/system/sockets.target.wants/*initctl* && \
    systemctl enable ssh.service && \
    echo "LANG=fr_FR.ISO-8859-15" > /etc/default/locale && \
    echo "LANGUAGE=fr_FR" >> /etc/default/locale && \
    echo "fr_FR.ISO-8859-15 ISO-8859-15" >> /etc/locale.gen && \
    locale-gen && \
    update-locale

ENV LANG fr_FR.ISO-8859-15
ENV LANGUAGE fr_FR

ADD https://raw.githubusercontent.com/mitchellh/vagrant/master/keys/vagrant.pub /root/.ssh/authorized_keys
EXPOSE 22
CMD ["/sbin/init"]
