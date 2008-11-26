# test_WriteELDBDeckFile.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an ELDB deck"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import aCardSetNames, \
        get_phys_cards
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.io.WriteELDBDeckFile import WriteELDBDeckFile
import unittest

sExpected = """"Test Set 1"
"A test author"
"A test comment"
1
"Abebe"
4
".44 Magnum"
"AK-47"
"Abbot"
"Abombwe"
"""

class ELDBDeckWriterTests(SutekhTest):
    """class for the ELDB deck writer tests"""

    def test_deck_writer(self):
        """Test ELDB deck writing"""
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

        oWriter = WriteELDBDeckFile()
        sTempFileName =  self._create_tmp_file()
        fOut = open(sTempFileName, 'w')
        oWriter.write(fOut, oPhysCardSet1)
        fOut.close()

        fIn = open(sTempFileName, 'rU')
        sData = fIn.read()
        fIn.close()

        self.assertEqual(sData, sExpected)

if __name__ == "__main__":
    unittest.main()
