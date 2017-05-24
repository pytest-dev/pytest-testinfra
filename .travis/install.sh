#!/bin/bash

function install_osx_package() {

  brew list --versions ${1} || brew install ${1}
  return $?

}

function setup_osx() {

  install_osx_package 'pyenv'
  install_osx_package 'pyenv-virtualenv'
  install_osx_package 'python'
  install_osx_package 'python3'

  [ -d /usr/local/Cellar/python/3.4.2 ] || python-build 3.4.2 /usr/local/Cellar/python/3.4.2
  cd /usr/local/bin
  [ -L "python3.4" ] || ln -sf ../Cellar/python/3.4.2/bin/python3.4

  python3.4 --version
  python --version

}

function setup_linux() {

  sudo apt-get update -qq && \
  sudo apt-get install -y -o Dpkg::Options::="--force-confnew" \
    docker-engine \
    curl

  docker version
}


case "${TRAVIS_OS_NAME}" in

  osx)
    setup_osx
    ;;

  linux)
    setup_linux
    ;;

esac
