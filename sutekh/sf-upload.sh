#!/bin/bash
SF_USER=$1
RELEASE_VER=$2
RELEASE_FILE=$3

if [ "x$RELEASE_FILE" = "x" ]
then
    echo "Usage: $0 <sourceforge username> <release version number> <file to upload>"
    echo "  Please ensure your Sourceforge SSH key is available."
    echo "  E.g."
    echo "     ./sf-upload.sh sfuser 0.8.0rc1 dist/Sutekh-0.8.0rc1-py2.7.egg"
    echo "     ./sf-upload.sh sfuser 0.8.0rc1 README"
    exit 1
fi

MINOR=${RELEASE_VER#*.}
MINOR=${MINOR%%.*}

STABLE="unstable"
if [ $((MINOR % 2)) = 0 ]
then
   STABLE="stable"
fi

# use wildcards to avoid
RELEASE_FOLDER="Sutekh\ $RELEASE_VER\ ($STABLE)"
RELEASE_FILE_BASE=$(basename "$RELEASE_FILE")

scp "$RELEASE_FILE" "$SF_USER,sutekh@frs.sourceforge.net:/home/frs/project/s/su/sutekh/sutekh/$RELEASE_FOLDER/$RELEASE_FILE_BASE"
