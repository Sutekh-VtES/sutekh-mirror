# test_PhysicalCardSetWriter.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing Card Set handling"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import CARD_SET_NAMES, \
        get_phys_cards, make_set_1
from sutekh.core.SutekhObjects import PhysicalCardSet, IPhysicalCardSet
from sutekh.core.CardSetHolder import CardSetWrapper
from sutekh.io.PhysicalCardSetWriter import PhysicalCardSetWriter
from sutekh.io.XmlFileHandling import PhysicalCardSetXmlFile
from StringIO import StringIO
import unittest

EXPECTED_1 = '<physicalcardset author="A test author"'\
        ' name="Test Set 1" sutekh_xml_version="1.3">\n' \
        '  <comment>A test comment</comment>\n' \
        '  <annotations />\n' \
        '  <card count="1" expansion="Jyhad" name=".44 Magnum" />\n' \
        '  <card count="3" expansion="None Specified" name=".44 Magnum" />\n' \
        '  <card count="1" expansion="Lords of the Night"' \
        ' name="AK-47" />\n' \
        '  <card count="1" expansion="None Specified" name="AK-47" />\n' \
        '  <card count="1" expansion="Keepers of Tradition"' \
        ' name="Aaron\'s Feeding Razor" />\n' \
        '  <card count="1" expansion="None Specified" name="Abbot" />\n' \
        '  <card count="1" expansion="Third Edition" name="Abbot" />\n' \
        '  <card count="1" expansion="None Specified" name="Abebe" />\n' \
        '  <card count="1" expansion="Legacy of Blood" name="Abombwe" />\n' \
        '  <card count="1" expansion="None Specified" name="Abombwe" />\n' \
        '  <card count="1" expansion="Promo-20051001"' \
        ' name="Alan Sovereign (Advanced)" />\n' \
        '  <card count="1" expansion="Nights of Reckoning"' \
        ' name="Inez &quot;Nurse216&quot; Villagrande" />\n' \
        '  <card count="1" expansion="Dark Sovereigns"' \
        ' name="Scapelli, The Family &quot;Mechanic&quot;" />\n' \
        '  <card count="1" expansion="Lords of the Night"' \
        ' name="The Path of Blood" />\n' \
        '  <card count="1" expansion="Bloodlines" name="The Siamese" />\n' \
        '</physicalcardset>'

EXPECTED_2 = '<physicalcardset author="A test author" ' \
        'name="Test Set 2" '\
        'sutekh_xml_version="1.3">\n' \
        '  <comment>A formatted test comment\n' \
        'A second line\n' \
        'A third line</comment>\n' \
        '  <annotations>Some Annotations</annotations>\n' \
        '  <card count="1" expansion="Jyhad" name=".44 Magnum" />\n' \
        '  <card count="1" expansion="Lords of the Night" name="AK-47" />\n' \
        '  <card count="1" expansion="Third Edition" name="Abbot" />\n' \
        '  <card count="1" expansion="Legacy of Blood" name="Abombwe" />\n ' \
        ' <card count="1" expansion="Promo-20051001"' \
        ' name="Alan Sovereign (Advanced)" />\n' \
        '</physicalcardset>'

EXPECTED_3 = '<physicalcardset author="" name="Test Set 2" '\
        'sutekh_xml_version="1.3">\n' \
        '  <comment>A formatted test comment\n' \
        'A second line\n' \
        'A third line</comment>\n' \
        '  <annotations>Some Annotations</annotations>\n' \
        '  <card count="1" expansion="Jyhad" name=".44 Magnum" />\n' \
        '  <card count="1" expansion="Lords of the Night" name="AK-47" />\n' \
        '  <card count="1" expansion="Third Edition" name="Abbot" />\n' \
        '  <card count="1" expansion="Legacy of Blood" name="Abombwe" />\n ' \
        ' <card count="1" expansion="Promo-20051001"' \
        ' name="Alan Sovereign (Advanced)" />\n' \
        '</physicalcardset>'


class PhysicalCardSetWriterTests(SutekhTest):
    """class for the Physical Card Set writer tests"""

    def test_physical_card_set_writer(self):
        """Test physical card set writing"""
        # pylint: disable-msg=E1101, R0915, R0914
        # E1101: SQLObject + PyProtocols magic confuses pylint
        # R0915, R0914: Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables
        aAddedPhysCards = get_phys_cards()
        # We have a physical card list, so create some physical card sets
        oPhysCardSet1 = make_set_1()

        # Check output

        oWriter = PhysicalCardSetWriter()
        oFile = StringIO()
        oWriter.write(oFile, CardSetWrapper(oPhysCardSet1))
        sWriterXML = oFile.getvalue()
        oFile.close()
        self.assertEqual(sWriterXML, EXPECTED_1)
        self.assertEqual(len(sWriterXML), len(EXPECTED_1))

        oPCS = IPhysicalCardSet(CARD_SET_NAMES[0])
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPCS))
        self.assertEqual(sData, sWriterXML)
        self.assertEqual(len(sData), len(EXPECTED_1))
        self.assertEqual(sData, EXPECTED_1)

        oPhysCardSet2 = PhysicalCardSet(name=CARD_SET_NAMES[1])
        oPhysCardSet2.author = 'A test author'
        oPhysCardSet2.comment = 'A formatted test comment\nA second line\n' \
                'A third line'
        oPhysCardSet2.annotations = 'Some Annotations'

        for iLoop in range(5, 10):
            oPhysCardSet2.addPhysicalCard(aAddedPhysCards[iLoop].id)
            oPhysCardSet2.syncUpdate()

        oFile = StringIO()
        oWriter.write(oFile, CardSetWrapper(oPhysCardSet2))
        sWriterXML = oFile.getvalue()
        oFile.close()
        self.assertEqual(len(sWriterXML), len(EXPECTED_2))
        self.assertEqual(sWriterXML, EXPECTED_2)

        sTempFileName = self._create_tmp_file()
        oFileXML = PhysicalCardSetXmlFile(sTempFileName)
        oFileXML.write(CARD_SET_NAMES[1])
        fIn = open(sTempFileName, 'rU')
        sData = fIn.read()
        self.assertEqual(len(sData), len(EXPECTED_2))
        self.assertEqual(sData, EXPECTED_2)

        # Unset the author
        oPhysCardSet2.author = None
        oFile = StringIO()
        oWriter.write(oFile, CardSetWrapper(oPhysCardSet2))
        sWriterXML = oFile.getvalue()
        oFile.close()
        self.assertEqual(len(sWriterXML), len(EXPECTED_3))
        self.assertEqual(sWriterXML, EXPECTED_3)


if __name__ == "__main__":
    unittest.main()
