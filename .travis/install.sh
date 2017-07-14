#!/bin/bash

function install_osx_package() {

  if [ -z ${USE_CASK} ]; then
    brew list --versions ${1} || brew install ${1}
  else
    brew cask list --versions ${1} || brew cask install ${1}
  fi

  return $?

}

function setup_osx() {

  install_osx_package 'pyenv'
  install_osx_package 'pyenv-virtualenv'
  install_osx_package 'python'

  local USE_CASK=1
  install_osx_package 'vagrant'
  USE_CASK=

  [ -d /usr/local/Cellar/python/3.4.2 ] || python-build 3.4.2 /usr/local/Cellar/python/3.4.2
  cd /usr/local/bin
  [ -L "python3.4" ] || ln -sf ../Cellar/python/3.4.2/bin/python3.4

  python3.4 --version
  python --version

  echo ""
  echo "*** OS Ruby and Ruby Gems ***"
  ruby --version
  gem list

  echo ""
  echo "*** Vagrant Gems ***"
  /opt/vagrant/embedded/bin/gem list
}

function setup_linux() {

  sudo apt-get update -qq && \
  sudo apt-get install -y \
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
