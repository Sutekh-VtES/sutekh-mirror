# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Card Set reading from file"""

import unittest
import os
from io import StringIO

from sutekh.base.core.BaseTables import (PhysicalCardSet,
                                         MapPhysicalCardToPhysicalCardSet)
from sutekh.base.core.BaseAdapters import IPhysicalCardSet
from sutekh.base.core.CardSetHolder import CardSetHolder

from sutekh.io.PhysicalCardSetParser import PhysicalCardSetParser
from sutekh.io.XmlFileHandling import PhysicalCardSetXmlFile
from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import (CARD_SET_NAMES,
                                                    get_phys_cards,
                                                    make_set_1,
                                                    make_set_3)
from sutekh.tests.io.test_PhysicalCardSetWriter import (EXPECTED_1,
                                                        EXPECTED_4)

# Test's include single quotes both escaped and not escape by ET
PCS_EXAMPLE_1 = ('<physicalcardset author="A test author" '
                 'comment="A test comment" name="Test Set 1" '
                 'sutekh_xml_version="1.2"><annotations /><card count="1" '
                 'expansion="None Specified" id="11" name="Abebe" /><card '
                 'count="1" expansion="None Specified" id="1" '
                 'name=".44 Magnum" /><card count="1" expansion="None '
                 'Specified" id="8" name="Abbot" /><card count="1" '
                 'expansion="None Specified" id="2" name="AK-47" /><card '
                 'count="1" expansion="None Specified" id="14" '
                 'name="Abombwe" /></physicalcardset>')

PCS_EXAMPLE_2 = ('<physicalcardset author="A test author" '
                 'name="Test Set 2" '
                 'sutekh_xml_version="1.3"><comment>A test comment</comment>'
                 '<annotations />\n"'
                 '<card count="1" expansion="None Specified" id="8" '
                 'name="Abbot" />\n'
                 '<card count="2" expansion="None Specified" id="2" '
                 'name="AK-47" />\n'
                 '<card count="1" expansion="None Specified" id="14" '
                 'name="Abombwe" />\n'
                 '<card count="1" expansion = "Jyhad" id="1" '
                 'name=".44 Magnum" />\n'
                 '<card count="1" expansion = "Nights of Reckoning" id="16" '
                 'name="Inez &quot;Nurse216&quot; " />\n'
                 '<card count="1" expansion = "Nights of Reckoning" id="16" '
                 'name="Inez &quot;Nurse216&quot; Villagrande" />\n'
                 '<card count="1" expansion="Keepers of Tradition" id="17" '
                 'name="Aaron\'s Feeding Razor" />\n'
                 '<card count="1" expansion="Lords of the Night" id="2" '
                 'name="AK-47" />\n</physicalcardset>')

PCS_EXAMPLE_2_NO_ID = ('<physicalcardset author="A test author" '
                       'name="Test Set 2" '
                       'sutekh_xml_version="1.3">'
                       '<comment>A test comment</comment>'
                       '<annotations />\n"'
                       '<card count="1" expansion="None Specified"'
                       ' name="Abbot" />\n'
                       '<card count="2" expansion="None Specified"'
                       ' name="AK-47" />\n'
                       '<card count="1" expansion="None Specified"'
                       ' name="Abombwe" />\n'
                       '<card count="1" expansion = "Jyhad"'
                       ' name=".44 Magnum" />\n'
                       '<card count="1" expansion = "Nights of Reckoning" '
                       'name="Inez &quot;Nurse216&quot; Villagrande" />\n'
                       '<card count="1" expansion="Keepers of Tradition" '
                       'name="Aaron&apos;s Feeding Razor" />\n'
                       '<card count="1" expansion="Lords of the Night" '
                       'name="AK-47" />\n</physicalcardset>')

PCS_EXAMPLE_3 = ('<physicalcardset author="A test author" '
                 'name="Test Set 3" '
                 'sutekh_xml_version="1.3">'
                 '<comment>A formatted test comment\n'
                 'A second line</comment>'
                 '<annotations>Some annotations</annotations>\n"'
                 '<card count="1" expansion="None Specified" id="8" '
                 'name="Abbot" />\n'
                 '<card count="2" expansion="None Specified" id="2" '
                 'name="AK-47" />\n'
                 '<card count="1" expansion="None Specified" id="14" '
                 'name="Abombwe" />\n'
                 '<card count="1" expansion = "Jyhad" id="1" '
                 'name=".44 Magnum" />\n'
                 '<card count="1" expansion="Keepers of Tradition" id="17" '
                 'name="Aaron&apos;s Feeding Razor" />\n'
                 '<card count="1" expansion="Lords of the Night" id="2" '
                 'name="AK-47" />\n</physicalcardset>')


PCS_EXAMPLE_3_NO_ID = ('<physicalcardset author="A test author" '
                       'name="Test Set 3" '
                       'sutekh_xml_version="1.3">'
                       '<comment>A formatted test comment\n'
                       'A second line</comment>'
                       '<annotations>Some annotations</annotations>\n"'
                       '<card count="1" expansion="None Specified"'
                       ' name="Abbot" />\n'
                       '<card count="2" expansion="None Specified"'
                       ' name="AK-47" />\n'
                       '<card count="1" expansion="None Specified"'
                       ' name="Abombwe" />\n'
                       '<card count="1" expansion="Jyhad"'
                       ' name=".44 Magnum" />\n'
                       '<card count="1" expansion="Keepers of Tradition" '
                       'name="Aaron\'s Feeding Razor" />\n'
                       '<card count="1" expansion="Lords of the Night"'
                       ' name="AK-47" />\n'
                       '</physicalcardset>')

PCS_EXAMPLE_NO_AUTH = ('<physicalcardset '
                       'name="Test Set 3" '
                       'sutekh_xml_version="1.3">'
                       '<comment>A formatted test comment\n'
                       'A second line</comment>'
                       '<annotations>Some annotations</annotations>\n"'
                       '<card count="1" expansion="None Specified" id="8" '
                       'name="Abbot" />\n'
                       '<card count="2" expansion="None Specified" id="2" '
                       'name="AK-47" />\n'
                       '<card count="1" expansion="None Specified" id="14" '
                       'name="Abombwe" />\n'
                       '<card count="1" expansion = "Jyhad" id="1" '
                       'name=".44 Magnum" />\n'
                       '<card count="1" expansion="Keepers of Tradition"'
                       ' id="17" name="Aaron\'s Feeding Razor" />\n'
                       '<card count="1" expansion="Lords of the Night" id="2" '
                       'name="AK-47" />\n</physicalcardset>')


class PhysicalCardSetParserTests(SutekhTest):
    """class for the Card Set Parser tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_physical_card_set_parser(self):
        """Test physical card set reading"""
        # pylint: disable=too-many-statements, too-many-locals
        # Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables
        aAddedPhysCards = get_phys_cards()
        # We have a physical card list, so create some physical card sets

        # Check input

        oParser = PhysicalCardSetParser()

        oHolder = CardSetHolder()
        oParser.parse(StringIO(PCS_EXAMPLE_1), oHolder)
        oHolder.create_pcs()

        sTempFileName = self._create_tmp_file()
        fIn = open(sTempFileName, 'w')
        fIn.write(PCS_EXAMPLE_2)
        fIn.close()
        fIn = open(sTempFileName, 'r')
        oHolder = CardSetHolder()
        oParser.parse(fIn, oHolder)
        oHolder.create_pcs()
        fIn.close()

        oHolder = CardSetHolder()
        oParser.parse(StringIO(PCS_EXAMPLE_3), oHolder)
        oHolder.create_pcs()

        oPhysCardSet1 = IPhysicalCardSet(CARD_SET_NAMES[0])
        oPhysCardSet2 = IPhysicalCardSet(CARD_SET_NAMES[1])
        oPhysCardSet3 = IPhysicalCardSet(CARD_SET_NAMES[2])

        self.assertEqual(len(oPhysCardSet1.cards), 5)
        self.assertEqual(len(oPhysCardSet2.cards), 8)
        self.assertEqual(len(oPhysCardSet3.cards), 7)
        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[0].id).count(), 1)
        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[7].id).count(), 2)
        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[4].id).count(), 3)
        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[1].id).count(), 1)
        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[6].id).count(), 3)
        # Aaron's Feeding razor
        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[14].id).count(), 0)
        # Inez
        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[12].id).count(), 0)

        PhysicalCardSet.delete(oPhysCardSet2.id)
        oFile = PhysicalCardSetXmlFile()
        self.assertRaises(IOError, oFile.read)
        oFile = PhysicalCardSetXmlFile(sTempFileName)
        oFile.read()
        oPhysCardSet2 = IPhysicalCardSet("Test Set 2")
        self.assertEqual(len(oPhysCardSet2.cards), 8)
        oFile.delete()
        self.assertFalse(os.path.exists(sTempFileName))
        oFile.write('Test Set 2')
        PhysicalCardSet.delete(oPhysCardSet2.id)
        self.assertTrue(os.path.exists(sTempFileName))
        oFile.read()
        oPhysCardSet2 = IPhysicalCardSet("Test Set 2")
        self.assertEqual(len(oPhysCardSet2.cards), 8)

        self.assertEqual(oPhysCardSet2.annotations, None)
        self.assertEqual(oPhysCardSet3.annotations, 'Some annotations')

        self.assertEqual(oPhysCardSet2.comment, 'A test comment')
        self.assertEqual(oPhysCardSet3.comment, 'A formatted test comment\n'
                                                'A second line')

        oHolder = CardSetHolder()
        self.assertRaises(IOError, oParser.parse,
                          StringIO('<caards></caards>'), oHolder)

    def test_card_set_parser_no_id(self):
        """Test physical card set reading for new card sets"""
        aAddedPhysCards = get_phys_cards()
        # We have a physical card list, so create some physical card sets

        # Check input

        oParser = PhysicalCardSetParser()

        # Repeat set 1 so the numbers match up
        oHolder = CardSetHolder()
        oParser.parse(StringIO(PCS_EXAMPLE_1), oHolder)
        oHolder.create_pcs()

        oHolder = CardSetHolder()
        oParser.parse(StringIO(PCS_EXAMPLE_2_NO_ID), oHolder)
        oHolder.create_pcs()

        oHolder = CardSetHolder()
        oParser.parse(StringIO(PCS_EXAMPLE_3_NO_ID), oHolder)
        oHolder.create_pcs()

        oPhysCardSet2 = IPhysicalCardSet(CARD_SET_NAMES[1])
        oPhysCardSet3 = IPhysicalCardSet(CARD_SET_NAMES[2])

        self.assertEqual(len(oPhysCardSet2.cards), 8)
        self.assertEqual(len(oPhysCardSet3.cards), 7)

        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[7].id).count(), 2)
        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[4].id).count(), 3)
        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[0].id).count(), 1)
        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[1].id).count(), 1)
        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[6].id).count(), 3)
        # Aaron's Feeding razor
        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[14].id).count(), 0)
        # Inez
        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[12].id).count(), 0)

        self.assertEqual(oPhysCardSet2.annotations, None)
        self.assertEqual(oPhysCardSet3.annotations, 'Some annotations')

        self.assertEqual(oPhysCardSet2.comment, 'A test comment')
        self.assertEqual(oPhysCardSet3.comment, 'A formatted test comment\n'
                                                'A second line')

    def test_card_set_parser_no_author(self):
        """Test physical card set reading for card sets without an author"""
        oParser = PhysicalCardSetParser()

        oHolder = CardSetHolder()
        oParser.parse(StringIO(PCS_EXAMPLE_NO_AUTH), oHolder)
        oHolder.create_pcs()

        oPhysCardSet3 = IPhysicalCardSet(CARD_SET_NAMES[2])
        self.assertEqual(len(oPhysCardSet3.cards), 7)

        self.assertEqual(oPhysCardSet3.annotations, 'Some annotations')

        self.assertEqual(oPhysCardSet3.comment, 'A formatted test comment\n'
                                                'A second line')

        # This test is a bit funky, as we may get either None or ''
        # depending on sqlobject version,
        self.assertTrue(oPhysCardSet3.author in (None, ''))

    def test_roundtrip(self):
        """Test that we round trip one of the card sets from the
           writer successfully"""
        # We rely on the writer tests to ensure that the strings
        # are the output of the card sets
        oParser = PhysicalCardSetParser()
        for sData, fCardSet, sName in [
                (EXPECTED_1, make_set_1, CARD_SET_NAMES[0]),
                (EXPECTED_4, make_set_3, CARD_SET_NAMES[2])]:
            oOrig = fCardSet()
             # Make sure we don't clash
            oOrig.name = 'Original ' + oOrig.name
            oOrig.syncUpdate()
            oHolder = CardSetHolder()
            oParser.parse(StringIO(sData), oHolder)
            oHolder.create_pcs()
            oRead = IPhysicalCardSet(sName)
            self.assertEqual(oRead.author, oOrig.author)
            self.assertEqual(oRead.comment, oOrig.comment)

            # Check that the card sets have the same cards
            self.assertEqual(len(oRead.cards), len(oOrig.cards))
            # pylint: disable=not-an-iterable
            # SQLObject confuses pylint here
            for oCard in oOrig.cards:
                self.assertTrue(oCard in oRead.cards,
                                "%s and %s differ on card %s" % (
                                    oRead.name, oOrig.name,
                                    oCard.abstractCard.name))


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
