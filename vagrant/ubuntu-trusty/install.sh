#!/bin/bash

cat > /etc/hosts <<'EOF'
127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
::1         localhost localhost.localdomain localhost6 localhost6.localdomain6

EOF

grep "isofs" /etc/modules >>/dev/null 2>&1 || sudo echo "isofs" >> /etc/modules
lsmod | grep "^isofs" >>/dev/null 2>&1 || sudo modprobe isofs

[ -f ~/.bash_profile ] && . ~/.bash_profile
[ -f ~/.bashrc ] && . ~/.bashrc

[ -z "${TRAVIS_OS_NAME}" ] && echo 'export TRAVIS_OS_NAME="linux"' >> ~/.bash_profile
[ -z "${TRAVIS_OS_NAME}" ] && echo 'export TRAVIS_OS_NAME="linux"' >> ~/.bashrc

exit 0
