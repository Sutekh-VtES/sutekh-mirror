# test_PhysicalCardSetWriter.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing Card Set handling"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import aCardSetNames, \
        get_phys_cards
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.io.PhysicalCardSetWriter import PhysicalCardSetWriter
import unittest

sExpected1 = '<physicalcardset author="A test author" ' \
        'name="Test Set 1" '\
        'sutekh_xml_version="1.3">\n' \
        '  <comment>A test comment</comment>\n' \
        '  <annotations />\n' \
        '  <card count="1" expansion="None Specified" id="1"' \
        ' name=".44 Magnum" />\n' \
        '  <card count="1" expansion="None Specified" id="2"' \
        ' name="AK-47" />\n' \
        '  <card count="1" expansion="None Specified" id="8"' \
        ' name="Abbot" />\n' \
        '  <card count="1" expansion="None Specified" id="11"' \
        ' name="Abebe" />\n' \
        '  <card count="1" expansion="None Specified" id="14"' \
        ' name="Abombwe" />\n' \
        '</physicalcardset>'

sExpected2 = '<physicalcardset author="A test author" ' \
        'name="Test Set 2" '\
        'sutekh_xml_version="1.3">\n' \
        '  <comment>A formatted test comment\n' \
        'A second line\n' \
        'A third line</comment>\n' \
        '  <annotations>Some Annotations</annotations>\n' \
        '  <card count="1" expansion="Jyhad" id="1" name=".44 Magnum" />\n' \
        '  <card count="1" expansion="Lords of the Night"' \
        ' id="2" name="AK-47" />\n' \
        '  <card count="1" expansion="Third Edition" id="8"' \
        ' name="Abbot" />\n' \
        '  <card count="1" expansion="Legacy of Blood" id="14"' \
        ' name="Abombwe" />\n ' \
        ' <card count="1" expansion="Promo-20051001" id="19"' \
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
        oPhysCardSet1 = PhysicalCardSet(name=aCardSetNames[0])
        oPhysCardSet1.comment = 'A test comment'
        oPhysCardSet1.author = 'A test author'

        for iLoop in range(5):
            oPhysCardSet1.addPhysicalCard(aAddedPhysCards[iLoop].id)
            oPhysCardSet1.syncUpdate()

        # Check output

        oWriter = PhysicalCardSetWriter()
        sWriterXML = oWriter.gen_xml_string(oPhysCardSet1.name)
        self.assertEqual(sWriterXML,
            oWriter.gen_xml_string(aCardSetNames[0]))
        # The writer uses database order - this is not
        # the same across databases, hence the nature of the checks below
        self.assertEqual(sWriterXML, sExpected1)
        self.assertEqual(len(sWriterXML), len(sExpected1))

        sTempFileName =  self._create_tmp_file()
        fOut = open(sTempFileName, 'w')
        oWriter.write(fOut, aCardSetNames[0])
        fOut.close()

        fIn = open(sTempFileName, 'rU')
        sData = fIn.read()
        self.assertEqual(sData, sWriterXML)
        self.assertEqual(len(sData), len(sExpected1))
        self.assertEqual(sorted(sData), sorted(sExpected1))

        oPhysCardSet2 = PhysicalCardSet(name=aCardSetNames[1])
        oPhysCardSet2.author = 'A test author'
        oPhysCardSet2.comment = 'A formatted test comment\nA second line\n' \
                'A third line'
        oPhysCardSet2.annotations = 'Some Annotations'

        for iLoop in range(5, 10):
            oPhysCardSet2.addPhysicalCard(aAddedPhysCards[iLoop].id)
            oPhysCardSet2.syncUpdate()

        sWriterXML = oWriter.gen_xml_string(oPhysCardSet2.name)
        # The writer uses database order - this is not
        # the same across databases, hence the nature of the checks below
        self.assertEqual(len(sWriterXML), len(sExpected2))
        self.assertEqual(sorted(sWriterXML), sorted(sExpected2))


if __name__ == "__main__":
    unittest.main()
