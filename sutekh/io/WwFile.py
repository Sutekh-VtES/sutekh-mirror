# WwFile.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Tools for dealing with unopened files that follow the White Wolf encoding
   conventions."""

import codecs
import urllib2
import logging

#WW_CARDLIST_URL = "http://www.vekn.net/images/stories/downloads/cardlist.txt"
WW_CARDLIST_URL = "http://bitbucket.org/hodgestar/sutekh-extras/" \
        "raw/tip/CardList/cardlist-data/cardlist.txt"

EXTRA_CARD_URL = "http://bitbucket.org/hodgestar/sutekh-extras/" \
        "raw/tip/extra_list.txt"

WW_RULINGS_URL = ["http://bitbucket.org/hodgestar/sutekh-extras/"
        "raw/tip/Rulebooks/rulebook-data/rulings.html"]


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


class WwFile(object):
    """WwFile is a convenience class which has an .open(..) method which
       returns a file-like object with the encoding set correctly.
       """

    # pylint: disable-msg=C0103
    # we accept sfFile here
    def __init__(self, sfFile, bUrl=False, bFileObj=False):
        self.sfFile = sfFile
        self.bUrl = bUrl
        self.bFileObj = bFileObj

        if bUrl and bFileObj:
            raise ValueError("WwFile cannot be both a URL and a fileobject")

    # pylint: enable-msg=C0103

    def open(self):
        """Return a file object for the file.

           This expects a utf8 encoded file (possibly with BOM) and
           returns a file object producing utf8 strings."""
        if self.bFileObj:
            return self.sfFile
        elif self.bUrl:
            oFile = urllib2.urlopen(self.sfFile)
            sData = oFile.read(1000)
            sFileEnc = guess_encoding(sData, self.sfFile)
            oFile.close()
            return codecs.EncodedFile(urllib2.urlopen(self.sfFile), 'utf8',
                    sFileEnc)
        else:
            oFile = open(self.sfFile, 'rU')
            sData = oFile.read(1000)
            sFileEnc = guess_encoding(sData, self.sfFile)
            oFile.close()
            return codecs.EncodedFile(open(self.sfFile, 'rU'), 'utf8',
                    sFileEnc)
