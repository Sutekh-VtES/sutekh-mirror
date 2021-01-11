# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an SL Deck 'import a deck' format"""

import unittest

from sutekh.base.core.CardSetHolder import CardSetWrapper

from sutekh.io.WriteSLDeck import WriteSLDeck
from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1

EXPECTED_1 = """Deck Name: Test Set 1
Author: A test author
Description:
A test comment
Crypt
---
1 Abebe
1 Alan Sovereign (Adv)
1 Hektor
1 Inez Nurse216 Villagrande
2 Siamese, The

Library
---
4 .44 Magnum
2 AK-47
1 Aaron's Feeding Razor
2 Abbot
2 Abombwe
3 Aire of Elation
1 Anarch Manifesto, An
1 Hide the Heart
4 Immortal Grapple
1 Path of Blood, The
1 Scapelli, The Family Mechanic
2 Swallowed by the Night
4 Walk of Flame
"""


class SLDeckWriterTests(SutekhTest):
    """class for the JOL deck writer tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_deck_writer(self):
        """Test SL deck writing"""
        oPhysCardSet1 = make_set_1()

        # Check output

        oWriter = WriteSLDeck()
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))

        self.assertEqual(sData, EXPECTED_1)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
