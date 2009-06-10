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
from sutekh.io.IdentifyXMLFile import IdentifyXMLFile
from sutekh.io.XmlFileHandling import PhysicalCardXmlFile
from sutekh.tests.core.test_PhysicalCardSet import ABSTRACT_CARDS
import unittest, os
from StringIO import StringIO


class PhysicalCardTests(SutekhTest):
    """class for the PhysicalCard tests"""
    aExpectedCards = test_WhiteWolfParser.WhiteWolfParserTests.aExpectedCards

    def test_physical(self):
        """Test physical card handling"""
        # pylint: disable-msg=E1101, R0915, R0914
        # E1101: SQLObject + PyProtocols magic confuses pylint
        # R0915, R0914: Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables

        # test IO

        oAC = IAbstractCard(ABSTRACT_CARDS[0])
        oPC = IPhysicalCard((oAC, None))
        sLastWriterVersion = "1.0"

        sExample = '<cards sutekh_xml_version="%s"><card count="1" ' \
                   'expansion="None Specified" id="%d" name="%s" /></cards>' \
                   % (sLastWriterVersion, oPC.id, oAC.name)

        oParser = PhysicalCardParser()
        oHolder = CardSetHolder()
        oParser.parse(StringIO(sExample), oHolder)
        oHolder.create_pcs()

        oMyCollection = IPhysicalCardSet("My Collection")
        assert(len(oMyCollection.cards) == 1)
        PhysicalCardSet.delete(oMyCollection.id)

        sTempFileName =  self._create_tmp_file()
        fOut = open(sTempFileName, 'w')
        fOut.write(sExample)
        fOut.close()

        oIdFile = IdentifyXMLFile()
        oIdFile.id_file(sTempFileName)
        self.assertEqual(oIdFile.type, 'PhysicalCard')

        fIn = open(sTempFileName, 'rU')
        oHolder = CardSetHolder()
        oParser.parse(fIn, oHolder)
        fIn.close()
        oHolder.create_pcs()

        # Test incorrect input
        oHolder = CardSetHolder()
        self.assertRaises(RuntimeError, oParser.parse, StringIO(
            '<ccaardd sutekh_xml_version="%s"><card count="1" ' \
            'expansion="None Specified" id="%d" name="%s" /></ccaardd>' \
            % (sLastWriterVersion, oPC.id, oAC.name)), oHolder)
        self.assertRaises(RuntimeError, oParser.parse, StringIO(
            '<cards sutekh_xml_version="5.0"><card count="1" ' \
            'expansion="None Specified" id="%d" name="%s" /></cards>' \
            % (oPC.id, oAC.name)), oHolder)

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
