# test_PhysicalCardSetWriter.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing Card Set handling"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.core.SutekhObjects import IAbstractCard, IPhysicalCard, \
        IExpansion, PhysicalCardSet
from sutekh.io.PhysicalCardSetWriter import PhysicalCardSetWriter
import unittest

class PhysicalCardSetWriterTests(SutekhTest):
    """class for the Physical Card Set writer tests"""
    aAbstractCards = ['.44 magnum', 'ak-47', 'abbot', 'abebe', 'abombwe']
    aCardExpansions = [('.44 magnum', 'Jyhad'),
            ('ak-47', 'LotN'),
            ('abbot', 'Third Edition'),
            ('abombwe', 'Legacy of Blood')]
    aCardSetNames = ['Test Set 1', 'Test Set 2']

    def _get_phys_cards(self):
        """Fill contents of the physical card table"""
        aAddedPhysCards = []
        for sName in self.aAbstractCards:
            oAC = IAbstractCard(sName)
            oPC = IPhysicalCard((oAC, None))
            aAddedPhysCards.append(oPC)
        for sName, sExpansion in self.aCardExpansions:
            oAC = IAbstractCard(sName)
            oExpansion = IExpansion(sExpansion)
            oPC = IPhysicalCard((oAC, oExpansion))
            aAddedPhysCards.append(oPC)
        return aAddedPhysCards

    def test_physical_card_set_writer(self):
        """Test physical card set writing"""
        # pylint: disable-msg=E1101, R0915, R0914
        # E1101: SQLObject + PyProtocols magic confuses pylint
        # R0915, R0914: Want a long, sequentila test case to minimise
        # repeated setups, so it has lots of lines + variables
        aAddedPhysCards = self._get_phys_cards()
        # We have a physical card list, so create some physical card sets
        oPhysCardSet1 = PhysicalCardSet(name=self.aCardSetNames[0])
        oPhysCardSet1.comment = 'A test comment'
        oPhysCardSet1.author = 'A test author'

        for iLoop in range(5):
            oPhysCardSet1.addPhysicalCard(aAddedPhysCards[iLoop].id)
            oPhysCardSet1.syncUpdate()

        # Check output

        oWriter = PhysicalCardSetWriter()
        self.assertEqual(oWriter.gen_xml_string(oPhysCardSet1.name),
            oWriter.gen_xml_string(oPhysCardSet1.name))
        sExpected = '<physicalcardset author="A test author" ' \
                'comment="A test comment" name="Test Set 1" '\
                'sutekh_xml_version="1.2"><annotations /><card count="1" ' \
                'expansion="None Specified" id="11" name="Abebe" /><card ' \
                'count="1" expansion="None Specified" id="1" ' \
                'name=".44 Magnum" /><card count="1" expansion="None ' \
                'Specified" id="8" name="Abbot" /><card count="1" ' \
                'expansion="None Specified" id="2" name="AK-47" /><card ' \
                'count="1" expansion="None Specified" id="14" ' \
                'name="Abombwe" /></physicalcardset>'
        self.assertEqual(oWriter.gen_xml_string(oPhysCardSet1.name),
                sExpected)

        sTempFileName =  self._create_tmp_file()
        fOut = open(sTempFileName, 'w')
        oWriter.write(fOut, self.aCardSetNames[0])
        fOut.close()

        fIn = open(sTempFileName, 'r')
        sData = fIn.read()
        # Writing to file adds newlines + formatting, which we remove before
        # comparing
        self.assertEqual(sData.replace('\n', '').replace('  ', ''), sExpected)

if __name__ == "__main__":
    unittest.main()
