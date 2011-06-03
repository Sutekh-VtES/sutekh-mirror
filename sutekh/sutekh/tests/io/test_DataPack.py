# test_DataPack.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
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

|| '''Description''' || '''Tag''' || '''File'''
|| Zip file of starter decks from Sabbat War to Heirs to the Blood || starters || [attachment:Starters_SW_to_HttB.zip:wiki:MiscWikiFiles Starters_SW_to_HttB.zip] ||
|| Zip file of userful rulings and rulebooks || rulebooks || [attachment:Rulebooks.zip:wiki:MiscWikiFiles Rulebooks.zip] ||
"""


class DataPackTest(SutekhTest):
    """Class for the data pack tests"""

    def test_find_data_pack(self):
        """Test finding data pack in sane documentation page"""
        sTempFileName = self._create_tmp_file()
        sTempUrl = 'file://%s' % urllib.pathname2url(sTempFileName)
        fFile = open(sTempFileName, 'w')
        fFile.write(TEST_DATA)
        fFile.close()

        self.assertEqual(find_data_pack('starters', sTempUrl),
                         "http://sourceforge.net/apps/trac/sutekh/"
                         "raw-attachment/wiki/MiscWikiFiles/"
                         "Starters_SW_to_HttB.zip")

        self.assertEqual(find_data_pack('rulebooks', sTempUrl),
                         "http://sourceforge.net/apps/trac/sutekh/"
                         "raw-attachment/wiki/MiscWikiFiles/"
                         "Rulebooks.zip")


if __name__ == "__main__":
    unittest.main()
