# WwFile.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Tools for dealing with unopened files that follow the White Wolf encoding
   conventions."""

import codecs
import urllib2

WW_CARDLIST_URL = "http://www.vekn.net/images/stories/downloads/cardlist.txt"

EXTRA_CARD_URL = "http://bitbucket.org/hodgestar/sutekh-extras/" \
        "raw/tip/extra_list.txt"

# pylint: disable-msg=C0103
# We accept the overly long name here
WW_CARDLIST_PER_LETTER_URLS = [
        "http://www.white-wolf.com/vtes/index.php?line=cardlist__",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_A",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_B",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_C",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_D",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_E",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_F",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_G",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_H",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_I",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_J",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_K",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_L",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_M",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_N",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_O",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_P",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_Q",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_R",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_S",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_T",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_U",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_V",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_W",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_X",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_Y",
        "http://www.white-wolf.com/vtes/index.php?line=cardlist_Z",
        ]

# pylint: enable-msg=C0103

WW_OLD_RULINGS_URL = "http://www.white-wolf.com/vtes/index.php?line=rulings"

WW_RULINGS_URL = [
        # We skip the general rulings, since we only want card rulings
        #"http://www.vekn.net/index.php/all-rulings/general-rulings",
        "http://www.vekn.net/index.php/all-rulings/card-rulings-a-to-f",
        "http://www.vekn.net/index.php/all-rulings/card-rulings-g-to-o",
        "http://www.vekn.net/index.php/all-rulings/card-rulings-p-to-z",
        ]


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
            return codecs.EncodedFile(urllib2.urlopen(self.sfFile), 'utf8')
        else:
            return codecs.EncodedFile(open(self.sfFile, 'rU'), 'utf8')
