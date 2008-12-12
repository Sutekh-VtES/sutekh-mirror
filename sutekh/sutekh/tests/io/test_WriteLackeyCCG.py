# test_WriteLackeyCCG.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an Lackey CCG file"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import aCardSetNames, \
        get_phys_cards
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.io.WriteLackeyCCG import  WriteLackeyCCG
import unittest

sExpected1 = """4\t.44 Magnum
2\tAK-47
2\tAbbot
2\tAbombwe
1\tPath of Blood, The
Crypt:
1\tAbebe
1\tAlan Sovereign Adv.
"""

class LackeyWriterTests(SutekhTest):
    """class for the Lackey CCG deck writer tests"""

    def test_deck_writer(self):
        """Test Lackey CCG deck writing"""
        # pylint: disable-msg=E1101, R0915, R0914
        # E1101: SQLObject + PyProtocols magic confuses pylint
        # R0915, R0914: Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables
        aAddedPhysCards = get_phys_cards()
        # We have a physical card list, so create some physical card sets
        oPhysCardSet1 = PhysicalCardSet(name=aCardSetNames[0])
        oPhysCardSet1.comment = 'A test comment'
        oPhysCardSet1.author = 'A test author'

        for oCard in aAddedPhysCards:
            oPhysCardSet1.addPhysicalCard(oCard.id)
            oPhysCardSet1.syncUpdate()
        oPhysCardSet1.addPhysicalCard(aAddedPhysCards[0])
        oPhysCardSet1.addPhysicalCard(aAddedPhysCards[0])
        oPhysCardSet1.syncUpdate()

        # Check output

        oWriter = WriteLackeyCCG()
        sTempFileName =  self._create_tmp_file()
        fOut = file(sTempFileName, 'w')
        oWriter.write(fOut, oPhysCardSet1)
        fOut.close()

        fIn = open(sTempFileName, 'rU')
        sData = fIn.read()
        fIn.close()

        self.assertEqual(sData, sExpected1)


if __name__ == "__main__":
    unittest.main()
