# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Tools for dealing with unopened files that follow the White Wolf encoding
   conventions."""

import codecs
from urllib.request import urlopen, Request
import logging


def guess_encoding(sData, sFile):
    """Try to determine the correct encoding from the data"""
    # Try utf8 first, then iso8859-1, which covers what we've
    # seen so far. We may also need one of the cp codecs, but
    # it currently seems not.
    aEncodings = ['utf8', 'iso8859-1']
    for sEnc in aEncodings:
        try:
            logging.info('Trying %s for %s', sEnc, sFile)
            sData.decode(sEnc)
            return sEnc
        except UnicodeDecodeError:
            # We move onto the next one
            pass
    # We've fallen off the back of the loop, so we're in trouble
    # and there're no good choices left, so we raise a RuntimeError
    raise RuntimeError('Unable to indentify correct encoding for %s' % sFile)


class EncodedFile:
    """EncodedFile is a convenience class which has an .open(..) method which
       returns a file-like object with the encoding set correctly.
       read() will return unicode data.
       """

    # Callers needing something different can construct their
    # own request with header
    HEADER = "Sutekh URL Client"

    # pylint: disable=invalid-name
    # we accept sfFile here
    def __init__(self, sfFile, bUrl=False, bFileObj=False):
        self.sfFile = sfFile
        self.bUrl = bUrl
        self.bFileObj = bFileObj

        if bUrl and bFileObj:
            raise ValueError(
                "EncodedFile cannot be both a URL and a fileobject")

    # pylint: enable=invalid-name

    def open(self):
        """Return a file object for the file.

           This expects a utf8 encoded file (possibly with BOM) and
           returns a file object producing utf8 strings."""
        if self.bFileObj:
            return self.sfFile
        if self.bUrl:
            if isinstance(self.sfFile, str):
                # Only create a custom Request if we have a bare url
                oReq = Request(self.sfFile)
                oReq.add_header('User-Agent', self.HEADER)
            else:
                oReq = self.sfFile
            oFile = urlopen(oReq)
            sData = oFile.read(1000)
            sFileEnc = guess_encoding(sData, self.sfFile)
            oFile.close()
            return codecs.lookup(sFileEnc).streamreader(urlopen(oReq))
        oFile = open(self.sfFile, 'rb')
        sData = oFile.read(1000)
        sFileEnc = guess_encoding(sData, self.sfFile)
        oFile.close()
        return codecs.lookup(sFileEnc).streamreader(open(self.sfFile, 'rb'))
