# WwFile.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""
Tools for dealing with unopened files that follow the White Wolf encoding
conventions.
"""

import codecs
import urllib2

WW_CARDLIST_URL = "http://www.white-wolf.com/vtes/index.php?line=cardlist"
WW_RULINGS_URL = "http://www.white-wolf.com/vtes/index.php?line=rulings"

class WwFile(object):
    """WwFile is a convenience class which has an .open(..) method which
       returns a file-like object with the encoding set correctly.
       """

    def __init__(self, sfFile, bUrl=False, bFileObj=False):
        self.sfFile = sfFile
        self.bUrl = bUrl
        self.bFileObj = bFileObj

        if bUrl and bFileObj:
            raise ValueError("WwFile cannot be both a URL and a fileobject")

    def open(self):
        """Return a file object for the file."""
        if self.bFileObj:
            return self.sfFile
        elif self.bUrl:
            return codecs.EncodedFile(urllib2.urlopen(self.sfFile), 'utf8',
                    'cp1252')
        else:
            return codecs.open(self.sfFile, 'rU', 'cp1252')

