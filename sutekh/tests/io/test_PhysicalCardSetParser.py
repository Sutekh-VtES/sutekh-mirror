# test_PhysicalCardSetParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Card Set reading from file"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import aCardSetNames, \
        get_phys_cards
from sutekh.core.SutekhObjects import IPhysicalCardSet, \
        MapPhysicalCardToPhysicalCardSet, PhysicalCardSet
from sutekh.io.PhysicalCardSetParser import PhysicalCardSetParser
from sutekh.io.XmlFileHandling import PhysicalCardSetXmlFile
import unittest, os

class PhysicalCardSetParserTests(SutekhTest):
    """class for the Card Set Parser tests"""

    def test_physical_card_set_parser(self):
        """Test physical card set reading"""
        # pylint: disable-msg=E1101, R0915, R0914
        # E1101: SQLObject + PyProtocols magic confuses pylint
        # R0915, R0914: Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables
        aAddedPhysCards = get_phys_cards()
        # We have a physical card list, so create some physical card sets

        sExpected1 = '<physicalcardset author="A test author" ' \
                'comment="A test comment" name="Test Set 1" '\
                'sutekh_xml_version="1.2"><annotations /><card count="1" ' \
                'expansion="None Specified" id="11" name="Abebe" /><card ' \
                'count="1" expansion="None Specified" id="1" ' \
                'name=".44 Magnum" /><card count="1" expansion="None ' \
                'Specified" id="8" name="Abbot" /><card count="1" ' \
                'expansion="None Specified" id="2" name="AK-47" /><card ' \
                'count="1" expansion="None Specified" id="14" ' \
                'name="Abombwe" /></physicalcardset>'

        sExpected2 = '<physicalcardset author="A test author" ' \
                'name="Test Set 2" '\
                'sutekh_xml_version="1.3"><comment>A test comment</comment>' \
                '<annotations />\n"' \
                '<card count="1" expansion="None Specified" id="8" ' \
                'name="Abbot" />\n' \
                '<card count="2" expansion="None Specified" id="2" ' \
                'name="AK-47" />\n' \
                '<card count="1" expansion="None Specified" id="14" ' \
                'name="Abombwe" />\n' \
                '<card count="1" expansion = "Jyhad" id="1" ' \
                'name=".44 Magnum" />\n' \
                '<card count="1" expansion="Lords of the Night" id="2" ' \
                'name="AK-47" />\n</physicalcardset>'

        sExpected3 = '<physicalcardset author="A test author" ' \
                'name="Test Set 3" '\
                'sutekh_xml_version="1.3">' \
                '<comment>A formatted test comment\n' \
                'A second line</comment>' \
                '<annotations>Some annotations</annotations>\n"' \
                '<card count="1" expansion="None Specified" id="8" ' \
                'name="Abbot" />\n' \
                '<card count="2" expansion="None Specified" id="2" ' \
                'name="AK-47" />\n' \
                '<card count="1" expansion="None Specified" id="14" ' \
                'name="Abombwe" />\n' \
                '<card count="1" expansion = "Jyhad" id="1" ' \
                'name=".44 Magnum" />\n' \
                '<card count="1" expansion="Lords of the Night" id="2" ' \
                'name="AK-47" />\n</physicalcardset>'


        # Check input

        oParser = PhysicalCardSetParser()

        oParser.parse_string(sExpected1)

        sTempFileName = self._create_tmp_file()
        fIn = open(sTempFileName, 'w')
        fIn.write(sExpected2)
        fIn.close()
        fIn = open(sTempFileName, 'rU')
        oParser.parse(fIn)
        fIn.close()

        oParser.parse_string(sExpected3)

        oPhysCardSet1 = IPhysicalCardSet(aCardSetNames[0])
        oPhysCardSet2 = IPhysicalCardSet(aCardSetNames[1])
        oPhysCardSet3 = IPhysicalCardSet(aCardSetNames[2])

        self.assertEqual(len(oPhysCardSet1.cards), 5)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID = aAddedPhysCards[0].id).count(), 1)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID = aAddedPhysCards[7].id).count(), 0)
        self.assertEqual(len(oPhysCardSet2.cards), 6)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID = aAddedPhysCards[4].id).count(), 3)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID = aAddedPhysCards[0].id).count(), 1)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID = aAddedPhysCards[1].id).count(), 5)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID = aAddedPhysCards[6].id).count(), 2)

        PhysicalCardSet.delete(oPhysCardSet2.id)
        oFile = PhysicalCardSetXmlFile()
        self.assertRaises(RuntimeError, oFile.read)
        oFile = PhysicalCardSetXmlFile(sTempFileName)
        oFile.read()
        oPhysCardSet2 = IPhysicalCardSet("Test Set 2")
        self.assertEqual(len(oPhysCardSet2.cards), 6)
        oFile.delete()
        self.assertFalse(os.path.exists(sTempFileName))
        oFile.write('Test Set 2')
        PhysicalCardSet.delete(oPhysCardSet2.id)
        self.assertTrue(os.path.exists(sTempFileName))
        oFile.read()
        oPhysCardSet2 = IPhysicalCardSet("Test Set 2")
        self.assertEqual(len(oPhysCardSet2.cards), 6)

        self.assertEqual(oPhysCardSet2.annotations, None)
        self.assertEqual(oPhysCardSet3.annotations, 'Some annotations')

        self.assertEqual(oPhysCardSet2.comment, 'A test comment')
        self.assertEqual(oPhysCardSet3.comment, 'A formatted test comment\n'
                'A second line')


if __name__ == "__main__":
    unittest.main()
