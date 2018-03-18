FROM archlinux/base

RUN pacman -Syu --noconfirm --noprogressbar --quiet python openssh procps systemd systemd-sysvcompat && \
    systemctl enable sshd.service

EXPOSE 22
CMD ["/usr/sbin/init"]
