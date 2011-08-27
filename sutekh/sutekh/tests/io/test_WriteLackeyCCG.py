# test_WriteLackeyCCG.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an Lackey CCG file"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1
from sutekh.core.CardSetHolder import CardSetWrapper
from sutekh.io.WriteLackeyCCG import  WriteLackeyCCG
import unittest

EXPECTED_1 = """4\t.44 Magnum
2\tAK-47
1\tAaron's Feeding Razor
2\tAbbot
2\tAbombwe
1\tPath of Blood, The
1\tScapelli, The Family 'Mechanic'
Crypt:
1\tAbebe
1\tAlan Sovereign Adv.
1\tInez ''Nurse216'' Villagrande
1\tSiamese, The
"""


class LackeyWriterTests(SutekhTest):
    """class for the Lackey CCG deck writer tests"""

    def test_deck_writer(self):
        """Test Lackey CCG deck writing"""
        oPhysCardSet1 = make_set_1()

        # Check output

        oWriter = WriteLackeyCCG()
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))

        self.assertEqual(sData, EXPECTED_1)


if __name__ == "__main__":
    unittest.main()
