# test_WriteArdbText.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an ARDB deck XML file"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1
from sutekh.core.CardSetHolder import CardSetWrapper
from sutekh.io.WriteArdbText import WriteArdbText
from sutekh.io.ARDBTextParser import ARDBTextParser
import unittest

# This doesn't match the ARDB export for the same card set, due to
# the outstanding issues in the Export implementation
ARDB_TEXT_EXPECTED_1 = """Deck Name : Test Set 1
Author : A test author
Description :
A test comment

Crypt [4 vampires] Capacity min: 3 max: 7 average: 5.00
------------------------------------------------------------
 1x The Siamese            7 PRE SPI ani pro     Ahrimane:2
 1x Alan Sovereign     Adv 6 AUS DOM for pre     Ventrue:3
 1x Abebe                  4 nec obf thn         Samedi:4
 1x Inez "Nurse216" Vi     3 inn                 Innocent (Imbued):4

Library [13 cards]
------------------------------------------------------------
Action [2]
 2x Abbot

Ally [1]
 1x Scapelli, The Family "Mechanic"

Equipment [7]
 4x .44 Magnum
 2x AK-47
 1x Aaron's Feeding Razor

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

    def test_roundtrip(self):
        """Test we can round-trip a deck"""
        oPhysCardSet1 = make_set_1()
        oParser = ARDBTextParser()

        oWriter = WriteArdbText()
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))

        oHolder = self._make_holder_from_string(oParser, sData)

        self.assertEqual(oHolder.name, oPhysCardSet1.name)
        self.assertEqual(oHolder.author, oPhysCardSet1.author)
        self.assertEqual(oHolder.comment.strip(), oPhysCardSet1.comment)

        aCards = oHolder.get_cards()
        dSetCards = {}
        # Reformat cards in deck to match holder
        for sName in [x.abstractCard.name for x in oPhysCardSet1.cards]:
            # We truncate Inez here to match the writer output
            if sName.startswith('Inez'):
                sName = sName[:18]
            dSetCards.setdefault(sName, 0)
            dSetCards[sName] += 1

        for sName, iCnt in dSetCards.iteritems():
            self.failUnless((sName, iCnt) in aCards)


if __name__ == "__main__":
    unittest.main()
