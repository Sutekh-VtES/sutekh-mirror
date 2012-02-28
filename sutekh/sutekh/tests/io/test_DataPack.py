# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2011 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test the Data Pack utilities"""

import urllib
import unittest
from sutekh.tests.TestCore import SutekhTest
from sutekh.io.DataPack import find_data_pack

TEST_DATA = """
= User Documentation =

== A Heading ==

  * [GettingStarted Starting out with Sutekh]

== Data Packs ==

{{{
#!comment
A comment.
}}}

|| '''Description''' || '''Tag''' || '''File''' || SHA256 Checksum ||
|| Zip file of starter decks from Sabbat War to Heirs to the Blood || starters || [attachment:Starters_SW_to_HttB.zip:wiki:MiscWikiFiles Starters_SW_to_HttB.zip] || aaabb ||
|| Zip file of userful rulings and rulebooks || rulebooks || [attachment:Rulebooks.zip:wiki:MiscWikiFiles Rulebooks.zip] || dddeee ||
"""


class DataPackTest(SutekhTest):
    """Class for the data pack tests"""
    # pylint: disable-msg=R0904
    # R0904 - unittest.TestCase, so many public methods

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


if __name__ == "__main__":
    unittest.main()
