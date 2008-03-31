#!/bin/bash
# Neil Muller <drnlmuller+sutekh@gmail.com>, 2008
# Arguably not copyrightable, since this is basically self-evident,
# but, if a license is needed, consider this to be in the public domain

export PYTHONPATH=../sutekh
for file in ../sutekh/sutekh/tests/test_*py; do
   echo "Running $file"
   python $file
done
