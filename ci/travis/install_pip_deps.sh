#!/bin/bash

if [ "${TRAVIS_OS_NAME}" = "osx" ]; then
   PIP=pip3
else
   PIP=pip
fi

$PIP install mock pytest keyring ply sqlobject configobj PyGObject pycairo
