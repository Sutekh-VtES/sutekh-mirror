# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an TWDA text file"""

import unittest

from sutekh.base.core.CardSetHolder import CardSetWrapper

from sutekh.io.WriteTWDAText import WriteTWDAText
from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import (make_set_1, make_set_2,
                                                    make_set_3)

TWDA_EXPECTED_1 = """Deck Name: Test Set 1
Author: A test author
Description:
A test comment

Crypt (6 cards, min=20, max=29, avg=6)
--------------------------------------
2x Siamese, The\t\t       7   PRE SPI ani pro\t\t\tAhrimane:2
1x Hektor\t\t       9   CEL POT PRE QUI for\tpriscus\t\tBrujah antitribu:4
1x Alan Sovereign (ADV)\t       6   AUS DOM for pre\t\t\tVentrue:3
1x Abebe\t\t       4   nec obf thn\t\t\t\tSamedi:4
1x Inez "Nurse216" Villagrande 3   inn\t\t\t\t\tInnocent (Imbued):4

Library (28 cards)
Master (3; 2 trifle)
2x Abombwe
1x Path of Blood, The

Action (2)
2x Abbot

Ally (1)
1x Scapelli, The Family "Mechanic"

Equipment (8)
4x .44 Magnum
1x Aaron's Feeding Razor
2x AK-47
1x Anarch Manifesto, An

Action Modifier (3)
3x Aire of Elation

Action Modifier/Combat (2)
2x Swallowed by the Night

Reaction (1)
1x Hide the Heart

Combat (8)
4x Immortal Grapple
4x Walk of Flame
"""

TWDA_EXPECTED_2 = """Deck Name: Test Set 2
Author: A test author
Description:
A formatted test comment
A second line
A third line

Crypt (3 cards, min=26, max=26, avg=8.67)
-----------------------------------------
2x Alexandra\t\t11  ANI AUS CEL PRE dom\tinner circle\tToreador:2
1x Abebe\t\t4   nec obf thn\t\t\t\tSamedi:4

Library (5 cards)
Master (1; 1 trifle)
1x Abombwe

Action (1)
1x Abbot

Equipment (2)
1x .44 Magnum
1x AK-47

Combat/Reaction (1)
1x Abandoning the Flesh
"""

TWDA_EXPECTED_3 = """Deck Name: Test Set 3
Author: A test author
Description:
A formatted test comment
A second line
A third line

Crypt (3 cards, min=30, max=30, avg=10)
---------------------------------------
2x Alexandra\t\t11  ANI AUS CEL PRE dom\tinner circle\tToreador:2
1x Étienne Fauberge\t8   ANI CEL CHI FOR\t\t\tRavnos:3

Library (5 cards)
Master (1; 1 trifle)
1x Abombwe

Action (1)
1x Abbot

Equipment (2)
1x .44 Magnum
1x AK-47

Combat/Reaction (1)
1x Abandoning the Flesh
"""


class TWDATextWriterTests(SutekhTest):
    """class for the TWDA text file writer tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_deck_writer(self):
        """Test TWDA text file writing"""
        oPhysCardSet = make_set_1()

        # Check output
        oWriter = WriteTWDAText()
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet))

        self.assertEqual(sData, TWDA_EXPECTED_1)

    def test_deck_with_titles(self):
        """Test TWDA writing with a titled vampire."""
        oPhysCardSet = make_set_2()

        # Check output
        oWriter = WriteTWDAText()
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet))

        self.assertEqual(sData, TWDA_EXPECTED_2)

    def test_deck_with_int_avg(self):
        """Test TWDA writing with a titled vampire and accented characters."""
        oPhysCardSet = make_set_3()

        # Check output
        oWriter = WriteTWDAText()
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet))

        self.assertEqual(sData, TWDA_EXPECTED_3)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
