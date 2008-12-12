# test_WriteELDBInventory.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an ELDB Inventory"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import aCardSetNames, \
        get_phys_cards
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.io.WriteELDBInventory import WriteELDBInventory
import unittest

sExpected = """"ELDB - Inventory"
"Cedric",0,0,"","Crypt"
"Inez "Nurse216" Villagrande",0,0,"","Crypt"
"Alan Sovereign",0,0,"","Crypt"
"Alan Sovereign (ADV)",0,0,"","Crypt"
"Alexandra",0,0,"","Crypt"
".44 Magnum",1,0,"","Library"
"Ablative Skin",0,0,"","Library"
"Aeron",0,0,"","Crypt"
"Gracis Nostinus",0,0,"","Crypt"
"Abombwe",1,0,"","Library"
"Anson",0,0,"","Crypt"
"Kabede Maru",0,0,"","Crypt"
"Amisa",0,0,"","Crypt"
"Kemintiri (ADV)",0,0,"","Crypt"
"Earl "Shaka74" Deams",0,0,"","Crypt"
"Lazar Dobrescu",0,0,"","Crypt"
"Abdelsobek",0,0,"","Crypt"
"Cesewayo",0,0,"","Crypt"
"Angelica, The Canonicus",0,0,"","Crypt"
"Bronwen",0,0,"","Crypt"
"Alfred Benezri",0,0,"","Crypt"
"Path of Blood, The",0,0,"","Library"
"Abjure",0,0,"","Library"
"Yvette, The Hopeless",0,0,"","Crypt"
"AK-47",1,0,"","Library"
"Aire of Elation",0,0,"","Library"
"Abandoning the Flesh",0,0,"","Library"
"Aaron`s Feeding Razor",0,0,"","Library"
"Aabbt Kindred",0,0,"","Crypt"
"Abebe",1,0,"","Crypt"
"Ambrogino Giovanni",0,0,"","Crypt"
"Aaron Duggan, Cameron`s Toady",0,0,"","Crypt"
"Anna "Dictatrix11" Suljic",0,0,"","Crypt"
"Predator`s Communion",0,0,"","Library"
"Akram",0,0,"","Crypt"
"Anastasz di Zagreb",0,0,"","Crypt"
"Abd al-Rashid",0,0,"","Crypt"
"Abbot",1,0,"","Library"
"Sha-Ennu",0,0,"","Crypt"
"Aaron Bathurst",0,0,"","Crypt"
"""

class ELDBInventoryWriterTests(SutekhTest):
    """class for the ELDB Inventory writer tests"""

    def test_inventory_writer(self):
        """Test ELDB inventory writing"""
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

        oWriter = WriteELDBInventory()
        sTempFileName =  self._create_tmp_file()
        fOut = open(sTempFileName, 'w')
        oWriter.write(fOut, oPhysCardSet1)
        fOut.close()

        fIn = open(sTempFileName, 'rU')
        sData = fIn.read()
        fIn.close()

        self.assertEqual(sorted(sData), sorted(sExpected), "Output differs : "
                "%s vs %s" % (sData, sExpected))

if __name__ == "__main__":
    unittest.main()
