FROM debian:buster

ENV container docker

# ntpd is linked to /bin/false, so the service is not running but is enabled
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install --no-install-recommends \
    lsb-release \
    python \
    openssh-server \
    puppet \
    salt-minion \
    locales \
    ntp \
    sudo \
    supervisor \
    systemd-sysv \
    python-pip \
    python-virtualenv \
    iptables \
    iptables-persistent && \
    rm -rf /var/lib/apt/lists/*
RUN mkdir -p /var/run/sshd && \
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
    systemctl enable netfilter-persistent.service && \
    ln -fsn /bin/false /usr/sbin/ntpd && \
    echo "python hold" | dpkg --set-selections && \
    echo "LANG=fr_FR.ISO-8859-15" > /etc/default/locale && \
    echo "LANGUAGE=fr_FR" >> /etc/default/locale && \
    echo "fr_FR.ISO-8859-15 ISO-8859-15" >> /etc/locale.gen && \
    locale-gen && \
    update-locale && \
    useradd -m user -c "gecos.comment" && \
    adduser user sudo && \
    echo "user ALL=NOPASSWD: ALL" > /etc/sudoers.d/user && \
    useradd -m unprivileged && \
    mkdir -p /root/.ssh && \
    echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCgDryK4AjJeifuc2N54St13KMNlnGLAtibQSMmvSyrhH7XJ1atnBo1HrJhGZNNBVKM67+zYNc9J3fg3qI1g63vSQAA+nXMsDYwu4BPwupakpwJELcGZJxsUGzjGVotVpqPIX5nW8NBGvkVuObI4UELOleq5mQMTGerJO64KkSVi20FDwPJn3q8GG2zk3pESiDA5ShEyFhYC8vOLfSSYD0LYmShAVGCLEgiNb+OXQL6ZRvzqfFEzL0QvaI/l3mb6b0VFPAO4QWOL0xj3cWzOZXOqht3V85CZvSk8ISdNgwCjXLZsPeaYL/toHNvBF30VMrDZ7w4SDU0ZZLEsc/ezxjb" > /root/.ssh/authorized_keys && \
    mkdir -p /home/user/.ssh && \
    cp /root/.ssh/authorized_keys /home/user/.ssh/authorized_keys && \
    chown -R user:user /home/user/.ssh && \
    echo "[program:tail]\ncommand=tail -f /dev/null\nuser=user\ngroup=user\n" > /etc/supervisor/conf.d/tail.conf

RUN echo "root:foo" | chpasswd

# Enable ssh login for user and fix side effect on environment variables...
RUN sed -ri 's/^UsePAM yes$/UsePAM no/' /etc/ssh/sshd_config
RUN sed -ri 's/AcceptEnv LANG LC_*/#AcceptEnv LANG LC_*/' /etc/ssh/sshd_config
RUN echo "PermitUserEnvironment yes" >> /etc/ssh/sshd_config
RUN echo "LANG=fr_FR.ISO-8859-15" >> /root/.ssh/environment
RUN echo "user:foo" | chpasswd

# Iptables rules
RUN echo "*nat\n:PREROUTING ACCEPT [0:0]\n:INPUT ACCEPT [0:0]\n:OUTPUT ACCEPT [0:0]\n:POSTROUTING ACCEPT [0:0]\n-A PREROUTING -d 192.168.0.1/32 -j REDIRECT\nCOMMIT\n*filter\n:INPUT ACCEPT [0:0]\n:FORWARD ACCEPT [0:0]\n:OUTPUT ACCEPT [0:0]\n-A INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT\nCOMMIT" > /etc/iptables/rules.v4

# Expiration date for user "user"
RUN chage -E 20000 user

# Some python virtualenv
RUN python -m virtualenv /v && /v/bin/pip install 'pytest>2,<3'

ENV LANG fr_FR.ISO-8859-15
ENV LANGUAGE fr_FR

EXPOSE 22
CMD ["/sbin/init"]
