# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an TWDA bbcode file"""

import time
from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1
from sutekh.base.core.CardSetHolder import CardSetWrapper
from sutekh.io.WriteTWDAText import WriteTWDAText
from sutekh.SutekhInfo import SutekhInfo
import unittest

TWDA_EXPECTED_1 = """Deck Name: Test Set 1
Author: A test author
Description:
A test comment

Crypt (4 cards, min=20, max=20, avg=5.00)
-----------------------------------------
1x Siamese, The\t\t\t7   PRE SPI ani pro\t   \tAhrimane:2
1x Alan Sovereign (ADV)\t\t6   AUS DOM for pre\t   \tVentrue:3
1x Abebe\t\t\t4   nec obf thn\t\t   \tSamedi:4
1x Inez "Nurse216" Villagrande\t3   inn\t\t\t   \tInnocent (Imbued):4

Library (13 cards)
Master (3, 2 trifles)
2x Abombwe
1x Path of Blood, The
Action (2)
2x Abbot
Ally (1)
1x Scapelli, The Family "Mechanic"
Equipment (7)
4x .44 Magnum
2x AK-47
1x Aaron's Feeding Razor
"""


class TWDATextWriterTests(SutekhTest):
    """class for the TWDA bbcode file writer tests"""
    # pylint: disable=R0904
    # R0904 - unittest.TestCase, so many public methods

    def test_deck_writer(self):
        """Test TWDA bbcode file writing"""
        oPhysCardSet1 = make_set_1()

        sCurDate = time.strftime('[ %Y-%m-%d ]', time.localtime())

        # Check output
        oWriter = WriteTWDAText()
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))
        sData = sData.replace(sCurDate, '[ DATE ]')

        self.assertEqual(sData, TWDA_EXPECTED_1)


if __name__ == "__main__":
    unittest.main()
