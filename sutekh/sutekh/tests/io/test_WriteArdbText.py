# test_WriteArdbXML.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an ARDB deck XML file"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1
from sutekh.core.CardSetHolder import CardSetWrapper
from sutekh.io.WriteArdbText import WriteArdbText
import unittest

# This doesn't match the ARDB export for the same card set, due to
# the outstanding issues in the Export implementation
ARDB_TEXT_EXPECTED_1 = """Deck Name : Test Set 1
Author : A test author
Description :
A test comment

Crypt [3 vampires] Capacity min: 4 max: 7 average: 5.67
------------------------------------------------------------
  1x The Siamese          7 PRE SPI ani pro      Ahrimane :2
  1x Alan Sovereign (Advanced) 6 AUS DOM for pre      Ventrue :3
  1x Abebe                4 nec obf thn          Samedi :4

Library [11 cards]
------------------------------------------------------------
Action [2]
  2x Abbot

Equipment [6]
  4x .44 Magnum
  2x AK-47

Master [3]
  2x Abombwe
  1x The Path of Blood

"""

class ArdbTextWriterTests(SutekhTest):
    """class for the ARDB text file writer tests"""

    def test_deck_writer(self):
        """Test ARDB text file writing"""
        oPhysCardSet1 = make_set_1()

        # Check output

        oWriter = WriteArdbText()
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))

        self.assertEqual(sData, ARDB_TEXT_EXPECTED_1)

if __name__ == "__main__":
    unittest.main()
