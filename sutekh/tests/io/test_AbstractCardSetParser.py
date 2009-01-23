# test_AbstractCardSetParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test the Abstract Card Set parser"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.core.SutekhObjects import IAbstractCard, IPhysicalCard, \
        IPhysicalCardSet, MapPhysicalCardToPhysicalCardSet, PhysicalCardSet
from sutekh.io.AbstractCardSetParser import AbstractCardSetParser
from sutekh.io.XmlFileHandling import AbstractCardSetXmlFile
import unittest, os

class AbstractCardSetParserTest(SutekhTest):
    """class for the Abstract Card Set Parser"""
    aAbstractCards = ['.44 magnum', 'ak-47', 'abbot', 'abebe', 'abombwe']
    aCardSetNames = ['Test Set 1', 'Test Set 2']

    def test_abstract_cs_parser(self):
        """Test abstract card set parser"""
        # pylint: disable-msg=E1101
        # E1101: SQLObject + PyProtocols magic confuses pylint

        # Support for everything except reading has been removed.
        # It is expected that reading in an ACS will create an
        # equivalent PCS.

        sExample1 = '<abstractcardset author="A test author" ' \
                'comment="A test comment" name="Test Set 1" ' \
                'sutekh_xml_version="1.1"><annotations /><card count="1" ' \
                'id="11" name="Abebe" /><card count="1" id="8" name="Abbot" ' \
                '/><card count="1" id="1" name=".44 Magnum" /><card ' \
                'count="1" id="2" name="AK-47" /><card count="1" id="14" ' \
                'name="Abombwe" /></abstractcardset>'

        sExample2 = '<abstractcardset author="A test author" ' \
                'comment="A test comment" name="Test Set 2" ' \
                'sutekh_xml_version="1.1"><annotations /><card count="2" ' \
                'id="11" name="Abebe" /><card count="1" id="8" name="Abbot" ' \
                '/><card count="2" id="2" name=".44 Magnum" /><card ' \
                'count="2" id="2" name="AK-47" /><card count="2" id="14" ' \
                'name="Abombwe" /></abstractcardset>'

        oParser = AbstractCardSetParser()

        sTempFileName =  self._create_tmp_file()
        fOut = open(sTempFileName, 'w')
        fOut.write(sExample1)
        fOut.close()

        oParser.parse_string(sExample2)
        fIn = open(sTempFileName, 'rU')
        oParser.parse(fIn)
        fIn.close()

        oCardSet1 = IPhysicalCardSet("(ACS) " + self.aCardSetNames[0])
        oCardSet2 = IPhysicalCardSet("(ACS) " + self.aCardSetNames[1])

        oAbsCard0 = IAbstractCard(self.aAbstractCards[0])
        oAbsCard2 = IAbstractCard(self.aAbstractCards[2])
        oPhysCard0 = IPhysicalCard((oAbsCard0, None))
        oPhysCard2 = IPhysicalCard((oAbsCard2, None))

        self.assertEqual(len(oCardSet1.cards), 5)
        self.assertEqual(len(oCardSet2.cards), 9)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID=oPhysCard0.id).count(),
            3)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID=oPhysCard2.id).count(),
            2)

        PhysicalCardSet.delete(oCardSet1.id)
        oFile = AbstractCardSetXmlFile()
        self.assertRaises(RuntimeError, oFile.read)
        oFile = AbstractCardSetXmlFile(sTempFileName)
        oFile.read()
        oCardSet1 = IPhysicalCardSet("(ACS) Test Set 1")
        self.assertEqual(len(oCardSet1.cards), 5)
        oFile.delete()
        self.assertFalse(os.path.exists(sTempFileName))
        self.assertRaises(RuntimeError, oFile.write, '(ACS) Test Set 1')


if __name__ == "__main__":
    unittest.main()
