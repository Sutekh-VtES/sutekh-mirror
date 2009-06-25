# test_WriteELDBInventory.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an ELDB Inventory"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1
from sutekh.io.WriteELDBInventory import WriteELDBInventory
import unittest

EXPECTED = """"ELDB - Inventory"
"Anastasz di Zagreb",0,0,"","Crypt"
"Alfred Benezri",0,0,"","Crypt"
"Bronwen",0,0,"","Crypt"
"Akram",0,0,"","Crypt"
"Lazar Dobrescu",0,0,"","Crypt"
"Aaron`s Feeding Razor",0,0,"","Library"
"Inez "Nurse216" Villagrande",0,0,"","Crypt"
"Angelica, The Canonicus",0,0,"","Crypt"
"Abdelsobek",0,0,"","Crypt"
"Aeron",0,0,"","Crypt"
"Aaron Bathurst",0,0,"","Crypt"
"Aaron Duggan, Cameron`s Toady",0,0,"","Crypt"
"Kemintiri (ADV)",0,0,"","Crypt"
"Predator`s Communion",0,0,"","Library"
"Abombwe",2,0,"","Library"
"Alan Sovereign (ADV)",1,0,"","Crypt"
"Anna "Dictatrix11" Suljic",0,0,"","Crypt"
"Gracis Nostinus",0,0,"","Crypt"
"Aire of Elation",0,0,"","Library"
"Amisa",0,0,"","Crypt"
".44 Magnum",4,0,"","Library"
"Ambrogino Giovanni",0,0,"","Crypt"
"Abebe",1,0,"","Crypt"
"Cedric",0,0,"","Crypt"
"Kabede Maru",0,0,"","Crypt"
"Cesewayo",0,0,"","Crypt"
"Alan Sovereign",0,0,"","Crypt"
"Ablative Skin",0,0,"","Library"
"Abbot",2,0,"","Library"
"Alexandra",0,0,"","Crypt"
"Abd al-Rashid",0,0,"","Crypt"
"Slaughterhouse, The",0,0,"","Library"
"Path of Blood, The",1,0,"","Library"
"Sha-Ennu",0,0,"","Crypt"
"Siamese, The",1,0,"","Crypt"
"Aabbt Kindred",0,0,"","Crypt"
"Abandoning the Flesh",0,0,"","Library"
"AK-47",2,0,"","Library"
"Abjure",0,0,"","Library"
"Yvette, The Hopeless",0,0,"","Crypt"
"Anson",0,0,"","Crypt"
"Earl "Shaka74" Deams",0,0,"","Crypt"
"""

class ELDBInventoryWriterTests(SutekhTest):
    """class for the ELDB Inventory writer tests"""

    def test_inventory_writer(self):
        """Test ELDB inventory writing"""
        oPhysCardSet1 = make_set_1()

        # Check output

        oWriter = WriteELDBInventory()
        sData = self._round_trip_obj(oWriter, oPhysCardSet1)

        self.assertEqual(sorted(sData), sorted(EXPECTED), "Output differs : "
                "%s vs %s" % (sData, EXPECTED))

if __name__ == "__main__":
    unittest.main()
