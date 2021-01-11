# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test PhysicalCard handling"""

import unittest
import os
from io import StringIO

from sutekh.base.tests.TestUtils import make_card
from sutekh.tests.io import test_WhiteWolfParser
from sutekh.base.core.BaseTables import PhysicalCardSet
from sutekh.base.core.BaseAdapters import IPhysicalCardSet
from sutekh.base.core.CardSetHolder import CardSetHolder

from sutekh.io.PhysicalCardParser import PhysicalCardParser
from sutekh.io.XmlFileHandling import PhysicalCardXmlFile
from sutekh.tests.core.test_PhysicalCardSet import ABSTRACT_CARDS
from sutekh.tests.TestCore import SutekhTest

LAST_WRITER_VERSION = "1.0"


def make_example_pcxml():
    """Create the example XML File"""
    oPC = make_card(ABSTRACT_CARDS[0][0], None)

    sExample = ('<cards sutekh_xml_version="%s"><card count="1" '
                'expansion="None Specified" id="%d" name="%s" /></cards>'
                % (LAST_WRITER_VERSION, oPC.id, ABSTRACT_CARDS[0][0]))
    return sExample


class PhysicalCardTests(SutekhTest):
    """class for the PhysicalCard tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods
    aExpectedCards = test_WhiteWolfParser.WhiteWolfParserTests.aExpectedCards

    def test_physical(self):
        """Test physical card handling"""
        # test IO
        sExample = make_example_pcxml()
        oParser = PhysicalCardParser()
        oHolder = CardSetHolder()
        oParser.parse(StringIO(sExample), oHolder)
        oHolder.create_pcs()

        oMyCollection = IPhysicalCardSet("My Collection")
        self.assertEqual(len(oMyCollection.cards), 1)
        PhysicalCardSet.delete(oMyCollection.id)

        sTempFileName = self._create_tmp_file()
        fOut = open(sTempFileName, 'w')
        fOut.write(sExample)
        fOut.close()

        fIn = open(sTempFileName, 'r')
        oHolder = CardSetHolder()
        oParser.parse(fIn, oHolder)
        fIn.close()
        oHolder.create_pcs()

        # Test incorrect input
        oHolder = CardSetHolder()
        self.assertRaises(IOError, oParser.parse,
                          StringIO('<ccaardd sutekh_xml_version="1.0"><card'
                                   ' count="1" expansion="None Specified"'
                                   ' id="12" name="Abbot" /></ccaardd>'),
                          oHolder)
        self.assertRaises(IOError, oParser.parse,
                          StringIO('<cards sutekh_xml_version="5.0"><card'
                                   ' count="1" expansion="None Specified"'
                                   ' id="12" name="Abbot" /></cards>'),
                          oHolder)

        # Check read results
        oMyCollection = IPhysicalCardSet("My Collection")
        self.assertEqual(len(oMyCollection.cards), 1)
        PhysicalCardSet.delete(oMyCollection.id)

        oFile = PhysicalCardXmlFile(sTempFileName)
        oFile.read()
        oMyCollection = IPhysicalCardSet("My Collection")
        self.assertEqual(len(oMyCollection.cards), 1)
        oFile.delete()
        self.assertFalse(os.path.exists(sTempFileName))
        self.assertRaises(RuntimeError, oFile.write)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
