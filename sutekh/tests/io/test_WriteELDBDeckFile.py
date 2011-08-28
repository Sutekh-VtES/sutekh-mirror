# test_WriteELDBDeckFile.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an ELDB deck"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1
from sutekh.io.WriteELDBDeckFile import WriteELDBDeckFile
from sutekh.core.CardSetHolder import CardSetWrapper
import unittest

EXPECTED_1 = """"Test Set 1"
"A test author"
"A test comment"
4
"Abebe"
"Alan Sovereign (ADV)"
"Inez 'Nurse216' Villagrande"
"Siamese, The"
13
".44 Magnum"
".44 Magnum"
".44 Magnum"
".44 Magnum"
"AK-47"
"AK-47"
"Aaron`s Feeding Razor"
"Abbot"
"Abbot"
"Abombwe"
"Abombwe"
"Path of Blood, The"
"Scapelli, The Family `Mechanic`"
"""


class ELDBDeckWriterTests(SutekhTest):
    """class for the ELDB deck writer tests"""

    def test_deck_writer(self):
        """Test ELDB deck writing"""
        oPhysCardSet1 = make_set_1()

        # Check output

        oWriter = WriteELDBDeckFile()
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))

        self.assertEqual(sData, EXPECTED_1)

if __name__ == "__main__":
    unittest.main()
