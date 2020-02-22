FROM alpine:3.11

RUN apk add --update --no-cache python openrc openssh && \
    sed -i "s/^#PermitRootLogin prohibit-password/PermitRootLogin without-password/g" /etc/ssh/sshd_config && \
    rm -f /etc/ssh/ssh_host_ecdsa_key /etc/ssh/ssh_host_rsa_key && \
    ssh-keygen -q -N "" -t dsa -f /etc/ssh/ssh_host_ecdsa_key && \
    ssh-keygen -q -N "" -t rsa -f /etc/ssh/ssh_host_rsa_key && \
    rc-update add sshd && \
    mkdir -p /root/.ssh && \
    chmod 700 /root/.ssh && \
    echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCgDryK4AjJeifuc2N54St13KMNlnGLAtibQSMmvSyrhH7XJ1atnBo1HrJhGZNNBVKM67+zYNc9J3fg3qI1g63vSQAA+nXMsDYwu4BPwupakpwJELcGZJxsUGzjGVotVpqPIX5nW8NBGvkVuObI4UELOleq5mQMTGerJO64KkSVi20FDwPJn3q8GG2zk3pESiDA5ShEyFhYC8vOLfSSYD0LYmShAVGCLEgiNb+OXQL6ZRvzqfFEzL0QvaI/l3mb6b0VFPAO4QWOL0xj3cWzOZXOqht3V85CZvSk8ISdNgwCjXLZsPeaYL/toHNvBF30VMrDZ7w4SDU0ZZLEsc/ezxjb" > /root/.ssh/authorized_keys

EXPOSE 22
CMD ["/sbin/init"]


