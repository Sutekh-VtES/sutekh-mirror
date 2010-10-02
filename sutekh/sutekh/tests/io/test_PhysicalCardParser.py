# test_PhysicalCardParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test PhysicalCard handling"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.io import test_WhiteWolfParser
from sutekh.core.SutekhObjects import IAbstractCard, IPhysicalCard, \
        IPhysicalCardSet, PhysicalCardSet
from sutekh.core.CardSetHolder import CardSetHolder
from sutekh.io.PhysicalCardParser import PhysicalCardParser
from sutekh.io.XmlFileHandling import PhysicalCardXmlFile
from sutekh.tests.core.test_PhysicalCardSet import ABSTRACT_CARDS
import unittest
import os
from StringIO import StringIO

LAST_WRITER_VERSION = "1.0"


def make_example_pcxml():
    """Create the example XML File"""
    # pylint: disable-msg=E1101
    # E1101: SQLObject + PyProtocols magic confuses pylint
    oAC = IAbstractCard(ABSTRACT_CARDS[0])
    oPC = IPhysicalCard((oAC, None))

    sExample = '<cards sutekh_xml_version="%s"><card count="1" ' \
            'expansion="None Specified" id="%d" name="%s" /></cards>' \
            % (LAST_WRITER_VERSION, oPC.id, oAC.name)
    return sExample


class PhysicalCardTests(SutekhTest):
    """class for the PhysicalCard tests"""
    aExpectedCards = test_WhiteWolfParser.WhiteWolfParserTests.aExpectedCards

    def test_physical(self):
        """Test physical card handling"""
        # pylint: disable-msg=E1101
        # E1101: SQLObject + PyProtocols magic confuses pylint

        # test IO
        sExample = make_example_pcxml()
        oParser = PhysicalCardParser()
        oHolder = CardSetHolder()
        oParser.parse(StringIO(sExample), oHolder)
        oHolder.create_pcs()

        oMyCollection = IPhysicalCardSet("My Collection")
        assert(len(oMyCollection.cards) == 1)
        PhysicalCardSet.delete(oMyCollection.id)

        sTempFileName = self._create_tmp_file()
        fOut = open(sTempFileName, 'w')
        fOut.write(sExample)
        fOut.close()

        fIn = open(sTempFileName, 'rU')
        oHolder = CardSetHolder()
        oParser.parse(fIn, oHolder)
        fIn.close()
        oHolder.create_pcs()

        # Test incorrect input
        oHolder = CardSetHolder()
        self.assertRaises(IOError, oParser.parse, StringIO(
            '<ccaardd sutekh_xml_version="1.0"><card count="1" ' \
            'expansion="None Specified" id="12" name="Abbot" /></ccaardd>'),
            oHolder)
        self.assertRaises(IOError, oParser.parse, StringIO(
            '<cards sutekh_xml_version="5.0"><card count="1" ' \
            'expansion="None Specified" id="12" name="Abbot" /></cards>'),
            oHolder)

        # Check read results
        oMyCollection = IPhysicalCardSet("My Collection")
        assert(len(oMyCollection.cards) == 1)
        PhysicalCardSet.delete(oMyCollection.id)

        oFile = PhysicalCardXmlFile(sTempFileName)
        oFile.read()
        oMyCollection = IPhysicalCardSet("My Collection")
        assert(len(oMyCollection.cards) == 1)
        oFile.delete()
        self.assertFalse(os.path.exists(sTempFileName))
        self.assertRaises(RuntimeError, oFile.write)


if __name__ == "__main__":
    unittest.main()
