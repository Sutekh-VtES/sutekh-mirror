# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an ARDB deck XML file"""

import unittest

from sutekh.base.core.CardSetHolder import CardSetWrapper

from sutekh.io.WriteArdbText import WriteArdbText
from sutekh.io.ARDBTextParser import ARDBTextParser
from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1

# This doesn't match the ARDB export for the same card set, due to
# the outstanding issues in the Export implementation
ARDB_TEXT_EXPECTED_1 = """Deck Name : Test Set 1
Author : A test author
Description :
A test comment

Crypt [6 vampires] Capacity min: 3 max: 9 average: 6.00
------------------------------------------------------------
 2x The Siamese            7 PRE SPI ani pro             Ahrimane:2
 1x Hektor                 9 CEL POT PRE QUI for Priscus !Brujah:4
 1x Alan Sovereign     Adv 6 AUS DOM for pre             Ventrue:3
 1x Abebe                  4 nec obf thn                 Samedi:4
 1x Inez "Nurse216" Vi     3 inn                         Innocent (Imbued):4

Library [28 cards]
------------------------------------------------------------
Action [2]
 2x Abbot

Action Modifier [3]
 3x Aire of Elation

Action Modifier/Combat [2]
 2x Swallowed by the Night

Ally [1]
 1x Scapelli, The Family "Mechanic"

Combat [8]
 4x Immortal Grapple
 4x Walk of Flame

Equipment [8]
 4x .44 Magnum
 2x AK-47
 1x Aaron's Feeding Razor
 1x An Anarch Manifesto

Master [3] (2 trifles)
 2x Abombwe
 1x The Path of Blood

Reaction [1]
 1x Hide the Heart

"""


class ArdbTextWriterTests(SutekhTest):
    """class for the ARDB text file writer tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

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
        # pylint: disable=not-an-iterable
        # SQLObject confuses pylint
        for sName in [x.abstractCard.name for x in oPhysCardSet1.cards]:
            # We truncate Inez here to match the writer output
            if sName.startswith('Inez'):
                sName = sName[:18]
            dSetCards.setdefault(sName, 0)
            dSetCards[sName] += 1
        # pylint: enable=not-an-iterable

        for sName, iCnt in dSetCards.items():
            self.assertTrue((sName, iCnt) in aCards)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
