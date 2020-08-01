#!/bin/bash
# Neil Muller <drnlmuller+sutekh@gmail.com>, 2008
# Arguably not copyrightable, since this is basically self-evident,
# but, if a license is needed, consider this to be in the public domain

if which pytest-3 > /dev/null; then
   # Use pytest if available
   echo "Running tests using pytest-3"
   (cd ../sutekh && pytest-3 )
else
   echo "Unable to find nosetests. Not running the test suite"
fi
