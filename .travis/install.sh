#!/bin/bash

if [ $TRAVIS_OS_NAME == "osx" ]; then

  # Install some requirements on OS X
  # e.g. brew install pyenv-virtualenv

  set $(echo $TOXENV | tr "," " ") --

  while [ -n "${1%%*-}" ]
  do

    echo "USING: '${1}'"

    case $1 in

      py27)
        brew install python
        ;;

      py34)
        brew install python3
        ;;

    esac

    shift

  done

fi
