# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2011 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test the Data Pack utilities"""

import json
import unittest

from urllib.parse import urljoin
from urllib.request import pathname2url

from sutekh.tests.TestCore import SutekhTest
from sutekh.io.DataPack import find_data_pack, find_all_data_packs

TEST_DATA = json.dumps({
    "datapacks": [
        {
            "description": ("Zip file of starter decks from Sabbat War to"
                            " Heirs to the Blood"),
            "file": "Starters/Starters_SW_to_HttB.zip",
            "sha256": "aaabb",
            "tag": "starters",
            "updated_at": "2010-03-03T18:54:31.802636",
        },
        {
            "description": "Zip file of useful rulings and rulebooks",
            "file": "Rulebooks/Rulebooks.zip",
            "sha256": "dddeee",
            "tag": "rulebooks",
            "updated_at": "2010-08-16T18:54:31.802636",
        },
        {
            "description": "2009 decks",
            "file": "TWD/TWDA_2009.zip",
            "sha256": "a",
            "tag": "twd",
            "updated_at": "2013-12-10T18:54:31.802636",
        },
        {
            "description": "2010 decks",
            "file": "TWD/TWDA_2010.zip",
            "sha256": "b",
            "tag": "twd",
            "updated_at": "2013-12-20T18:54:31.802636",
        },
    ],
    "format": "sutekh-datapack",
    "format-version": "1.0",
})


class DataPackTest(SutekhTest):
    """Class for the data pack tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def create_index(self, sData):
        """Create a test index and return a URL for it."""
        sTempFileName = self._create_tmp_file()
        fFile = open(sTempFileName, 'w')
        fFile.write(sData)
        fFile.close()
        sTempUrl = 'file://%s' % pathname2url(sTempFileName)
        return sTempUrl

    def test_find_data_pack(self):
        """Test finding data pack in sane documentation page"""
        sTempUrl = self.create_index(TEST_DATA)

        sUrl, sHash = find_data_pack('starters', sTempUrl)

        self.assertEqual(sUrl, urljoin(
            sTempUrl, "Starters/Starters_SW_to_HttB.zip"))

        self.assertEqual(sHash, 'aaabb')

        sUrl, sHash = find_data_pack('rulebooks', sTempUrl)

        self.assertEqual(sUrl, urljoin(
            sTempUrl, "Rulebooks/Rulebooks.zip"))

        self.assertEqual(sHash, 'dddeee')

        aUrls, aDates, aHashes = find_all_data_packs('twd', sTempUrl)

        self.assertEqual(len(aUrls), 2)
        self.assertEqual(len(aDates), 2)
        self.assertEqual(len(aHashes), 2)

        self.assertEqual('2013-12-10', aDates[0])
        self.assertEqual('2013-12-20', aDates[1])

        self.assertEqual(aUrls[0], urljoin(
            sTempUrl, "TWD/TWDA_2009.zip"))
        self.assertEqual(aUrls[1], urljoin(
            sTempUrl, "TWD/TWDA_2010.zip"))
        self.assertEqual(aHashes[0], 'a')
        self.assertEqual(aHashes[1], 'b')

        sUrl, sHash = find_data_pack('twd', sTempUrl)
        # We return the last one in this case
        self.assertEqual(sUrl, urljoin(
            sTempUrl, "TWD/TWDA_2010.zip"))
        self.assertEqual(sHash, 'b')

    def test_error_handler_bad_index(self):
        """Test error handling for badly formatted index files."""
        sTempUrl = self.create_index("""Not JSON""")
        aErrors = []

        _sUrl, _sHash = find_data_pack('starters', sTempUrl,
                                       fErrorHandler=aErrors.append)
        # pylint: disable=unbalanced-tuple-unpacking
        # by construction, this unpacking is safe
        [oExp] = aErrors
        # pylint: enable=unbalanced-tuple-unpacking
        self.assertTrue(isinstance(oExp, json.decoder.JSONDecodeError))
        self.assertTrue('Expecting value:' in str(oExp))


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
