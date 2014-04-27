# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2011 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test the Data Pack utilities"""

import urllib
import unittest
import urllib2
import socket
from sutekh.tests.TestCore import SutekhTest
from sutekh.io.DataPack import find_data_pack, find_all_data_packs
from sutekh.base.io.UrlOps import fetch_data

TEST_DATA = """
= User Documentation =

== A Heading ==

  * [GettingStarted Starting out with Sutekh]

== Data Packs ==

{{{
#!comment
A comment.
}}}

|| '''Description''' || '''Tag''' || '''Date Updated''' || '''File''' || SHA256 Checksum ||
|| Zip file of starter decks from Sabbat War to Heirs to the Blood || starters || 2010-03-03 || [attachment:Starters_SW_to_HttB.zip:wiki:MiscWikiFiles Starters_SW_to_HttB.zip] || aaabb ||
|| Zip file of useful rulings and rulebooks || rulebooks || 2013-08-16 || [attachment:Rulebooks.zip:wiki:MiscWikiFiles Rulebooks.zip] || dddeee ||
|| 2009 decks || twd || 2013-12-10 || [attachment:TWDA_2009.zip:wiki:MiscWikiFiles TWDA_2009.zip] || a ||
|| 2010 decks || twd || 2013-12-20 || [attachment:TWDA_2010.zip:wiki:MiscWikiFiles TWDA_2010.zip] || b ||
"""


class FailFile(object):
    """File'ish that raises exceptions for checking the error handler stuff"""

    def __init__(self, oExp):
        self._oExp = oExp

    def read(self):
        """Dummy method"""
        raise self._oExp


class DataPackTest(SutekhTest):
    """Class for the data pack tests"""
    # pylint: disable-msg=R0904
    # R0904 - unittest.TestCase, so many public methods

    bCalled = False  # Used for error handler tests

    def test_find_data_pack(self):
        """Test finding data pack in sane documentation page"""
        sTempFileName = self._create_tmp_file()
        sTempUrl = 'file://%s' % urllib.pathname2url(sTempFileName)
        fFile = open(sTempFileName, 'w')
        fFile.write(TEST_DATA)
        fFile.close()

        sUrl, sHash = find_data_pack('starters', sTempUrl)

        self.assertEqual(sUrl, "http://sourceforge.net/apps/trac/sutekh/"
                         "raw-attachment/wiki/MiscWikiFiles/"
                         "Starters_SW_to_HttB.zip")

        self.assertEqual(sHash, 'aaabb')

        sUrl, sHash = find_data_pack('rulebooks', sTempUrl)

        self.assertEqual(sUrl, "http://sourceforge.net/apps/trac/sutekh/"
                         "raw-attachment/wiki/MiscWikiFiles/"
                         "Rulebooks.zip")

        self.assertEqual(sHash, 'dddeee')

        aUrls, aDates, aHashes = find_all_data_packs('twd', sTempUrl)

        self.assertEqual(len(aUrls), 2)
        self.assertEqual(len(aDates), 2)
        self.assertEqual(len(aHashes), 2)

        self.assertEqual('2013-12-10', aDates[0])
        self.assertEqual('2013-12-20', aDates[1])

        self.assertEqual(aUrls[0], "http://sourceforge.net/apps/trac/sutekh/"
                         "raw-attachment/wiki/MiscWikiFiles/"
                         "TWDA_2009.zip")
        self.assertEqual(aUrls[1], "http://sourceforge.net/apps/trac/sutekh/"
                         "raw-attachment/wiki/MiscWikiFiles/"
                         "TWDA_2010.zip")
        self.assertEqual(aHashes[0], 'a')
        self.assertEqual(aHashes[1], 'b')

        sUrl, sHash = find_data_pack('twd', sTempUrl)
        # We return the last one in this case
        self.assertEqual(sUrl, "http://sourceforge.net/apps/trac/sutekh/"
                         "raw-attachment/wiki/MiscWikiFiles/"
                         "TWDA_2010.zip")
        self.assertEqual(sHash, 'b')

    def test_error_handler(self):
        """Test triggering the error handler"""

        def error_handler(_oExp):
            """Dummy error handler"""
            self.bCalled = True

        oFile = FailFile(socket.timeout)
        fetch_data(oFile, fErrorHandler=error_handler)
        self.assertEqual(self.bCalled, True)
        self.bCalled = False
        oFile = FailFile(urllib2.URLError('aaa'))
        fetch_data(oFile, fErrorHandler=error_handler)
        self.assertEqual(self.bCalled, True)

if __name__ == "__main__":
    unittest.main()
