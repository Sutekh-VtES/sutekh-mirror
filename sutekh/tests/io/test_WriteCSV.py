# test_WriteCSV.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an CSV file"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1
from sutekh.io.WriteCSV import  WriteCSV
from sutekh.core.CardSetHolder import CardSetWrapper
import unittest

EXPECTED_1 = """"Card Name", "Expansion", "Number"
".44 Magnum", "Jyhad", 1
".44 Magnum", "Unknown Expansion", 3
"AK-47", "Lords of the Night", 1
"AK-47", "Unknown Expansion", 1
"Aaron's Feeding Razor", "Keepers of Tradition", 1
"Abbot", "Third Edition", 1
"Abbot", "Unknown Expansion", 1
"Abebe", "Unknown Expansion", 1
"Abombwe", "Legacy of Blood", 1
"Abombwe", "Unknown Expansion", 1
"Alan Sovereign (Advanced)", "Promo-20051001", 1
"Inez ""Nurse216"" Villagrande", "Nights of Reckoning", 1
"Scapelli, The Family ""Mechanic""\", "Dark Sovereigns", 1
"The Path of Blood", "Lords of the Night", 1
"The Siamese", "Bloodlines", 1
"""

EXPECTED_2 = """".44 Magnum", "Jyhad", 1
".44 Magnum", "Unknown Expansion", 3
"AK-47", "Lords of the Night", 1
"AK-47", "Unknown Expansion", 1
"Aaron's Feeding Razor", "Keepers of Tradition", 1
"Abbot", "Third Edition", 1
"Abbot", "Unknown Expansion", 1
"Abebe", "Unknown Expansion", 1
"Abombwe", "Legacy of Blood", 1
"Abombwe", "Unknown Expansion", 1
"Alan Sovereign (Advanced)", "Promo-20051001", 1
"Inez ""Nurse216"" Villagrande", "Nights of Reckoning", 1
"Scapelli, The Family ""Mechanic""\", "Dark Sovereigns", 1
"The Path of Blood", "Lords of the Night", 1
"The Siamese", "Bloodlines", 1
"""


EXPECTED_3 = """"Card Name", "Number"
".44 Magnum", 4
"AK-47", 2
"Aaron's Feeding Razor", 1
"Abbot", 2
"Abebe", 1
"Abombwe", 2
"Alan Sovereign (Advanced)", 1
"Inez ""Nurse216"" Villagrande", 1
"Scapelli, The Family ""Mechanic""\", 1
"The Path of Blood", 1
"The Siamese", 1
"""

EXPECTED_4 = """".44 Magnum", 4
"AK-47", 2
"Aaron's Feeding Razor", 1
"Abbot", 2
"Abebe", 1
"Abombwe", 2
"Alan Sovereign (Advanced)", 1
"Inez ""Nurse216"" Villagrande", 1
"Scapelli, The Family ""Mechanic""\", 1
"The Path of Blood", 1
"The Siamese", 1
"""


class CSVWriterTests(SutekhTest):
    """class for the CSV deck writer tests"""

    def test_deck_writer(self):
        """Test CSV deck writing"""
        oPhysCardSet1 = make_set_1()

        # Check output

        oWriter = WriteCSV(True, True)
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))

        self.assertEqual(sData, EXPECTED_1)

        oWriter = WriteCSV(False, True)
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))

        self.assertEqual(sData, EXPECTED_2)

        oWriter = WriteCSV(True, False)
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))

        self.assertEqual(sData, EXPECTED_3)

        oWriter = WriteCSV(False, False)
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))

        self.assertEqual(sData, EXPECTED_4)


if __name__ == "__main__":
    unittest.main()
