FROM debian:jessie

# ntpd is linked to /bin/false, so the service is not running but is enabled
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install python openssh-server \
        puppet salt-minion locales ntp sudo supervisor && \
    mkdir -p /var/run/sshd && \
    (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do if ! test $i = systemd-tmpfiles-setup.service; then rm -f $i; fi; done) && \
    rm -f /lib/systemd/system/multi-user.target.wants/* && \
    rm -f /etc/systemd/system/*.wants/* && \
    rm -f /lib/systemd/system/local-fs.target.wants/* && \
    rm -f /lib/systemd/system/sockets.target.wants/*udev* && \
    rm -f /lib/systemd/system/sockets.target.wants/*initctl* && \
    systemctl enable ssh.service && \
    systemctl disable salt-minion.service && \
    systemctl enable ntp.service && \
    systemctl enable supervisor.service && \
    ln -fsn /bin/false /usr/sbin/ntpd && \
    echo "python hold" | dpkg --set-selections && \
    echo "LANG=fr_FR.ISO-8859-15" > /etc/default/locale && \
    echo "LANGUAGE=fr_FR" >> /etc/default/locale && \
    echo "fr_FR.ISO-8859-15 ISO-8859-15" >> /etc/locale.gen && \
    locale-gen && \
    update-locale && \
    useradd -m user && \
    adduser user sudo && \
    echo "user ALL=NOPASSWD: ALL" > /etc/sudoers.d/user && \
    mkdir -p /root/.ssh && \
    echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCgDryK4AjJeifuc2N54St13KMNlnGLAtibQSMmvSyrhH7XJ1atnBo1HrJhGZNNBVKM67+zYNc9J3fg3qI1g63vSQAA+nXMsDYwu4BPwupakpwJELcGZJxsUGzjGVotVpqPIX5nW8NBGvkVuObI4UELOleq5mQMTGerJO64KkSVi20FDwPJn3q8GG2zk3pESiDA5ShEyFhYC8vOLfSSYD0LYmShAVGCLEgiNb+OXQL6ZRvzqfFEzL0QvaI/l3mb6b0VFPAO4QWOL0xj3cWzOZXOqht3V85CZvSk8ISdNgwCjXLZsPeaYL/toHNvBF30VMrDZ7w4SDU0ZZLEsc/ezxjb" > /root/.ssh/authorized_keys && \
    mkdir -p /home/user/.ssh && \
    cp /root/.ssh/authorized_keys /home/user/.ssh/authorized_keys && \
    chown -R user:user /home/user/.ssh && \
    echo "[program:tail]\ncommand=tail -f /dev/null\nuser=user\ngroup=user\n" > /etc/supervisor/conf.d/tail.conf

RUN echo "root:foo" | chpasswd


ENV LANG fr_FR.ISO-8859-15
ENV LANGUAGE fr_FR

EXPOSE 22
CMD ["/sbin/init"]
