# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test IdentifyXMLFile handling"""

import unittest
from io import StringIO

from sutekh.io.IdentifyXMLFile import IdentifyXMLFile
from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.io.test_AbstractCardSetParser import ACS_EXAMPLE_1
from sutekh.tests.io.test_PhysicalCardSetParser import PCS_EXAMPLE_1
from sutekh.tests.io.test_PhysicalCardParser import make_example_pcxml


class TestIdentifyXMLFile(SutekhTest):
    """class for the IdentifyXMLFile tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_identify_xml_file(self):
        """Test IdentifyXMLFile"""
        # test IO
        self.maxDiff = None
        sExample = make_example_pcxml()

        sTempFileName = self._create_tmp_file()
        fOut = open(sTempFileName, 'w')
        fOut.write(sExample)
        fOut.close()

        oIdFile = IdentifyXMLFile()
        oIdFile.id_file(sTempFileName)
        self.assertEqual(oIdFile.type, 'PhysicalCard')

        oIdFile.parse(StringIO(sExample), None)
        self.assertEqual(oIdFile.type, 'PhysicalCard')

        oIdFile.parse(StringIO('garbage input'))
        self.assertEqual(oIdFile.type, 'Unknown')

        oIdFile.parse(StringIO(ACS_EXAMPLE_1))
        self.assertEqual(oIdFile.type, 'AbstractCardSet')

        oIdFile.parse(StringIO(PCS_EXAMPLE_1))
        self.assertEqual(oIdFile.type, 'PhysicalCardSet')


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
