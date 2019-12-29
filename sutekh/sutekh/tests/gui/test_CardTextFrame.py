# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2019 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Tests parts of the CardTextFrame"""

import unittest

from sutekh.tests.GuiSutekhTest import GuiSutekhTest
from sutekh.base.tests.TestUtils import make_card

from sutekh.base.core.BaseTables import PhysicalCardSet


AIRE = """Aire of Elation
Cost: 1 blood
Card Type:
*\tAction Modifier
Disciplines:
*\tPRE

You cannot play another action modifier to further increase the bleed for this action.
[pre] +1 bleed; +2 bleed if the acting vampire is Toreador.
[PRE] +2 bleed; +3 bleed if the acting vampire is Toreador.

Expansions:
*\tAnarchs (Precon)
*\tCamarilla Edition (Common, Precon)
*\tDark Sovereigns (Common)
*\tFinal Nights (Precon)
*\tKindred Most Wanted (Precon)

Artists:
*\tGreg Simanson"""

ALEXANDRA = """Alexandra
Capacity: 11
Group: 2
Card Type:
*\tVampire
Keywords::
*\t0 stealth
*\t1 strength
*\t3 bleed
*\t0 intercept
Clan:
*\tToreador
Sect: Camarilla
Title: Inner Circle
Disciplines:
*\tdom
*\tANI
*\tAUS
*\tCEL
*\tPRE

Camarilla Inner Circle: Once during your turn, you may lock or unlock another ready Toreador. +2 bleed.

Expansions:
*\tCamarilla Edition (Precon)
*\tDark Sovereigns (Vampire)

Artists:
*\tLawrence Snelly"""


class TestCardTextFrame(GuiSutekhTest):
    """Class for the LogViewFrame test cases"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_basic(self):
        """Set of simple tests of the CardTextFrame"""
        # 'My Collection' is needed for default config
        _oMyCollection = PhysicalCardSet(name='My Collection')
        self.oWin.setup(self.oConfig)
        # Get the card text frame
        oCardTextFrame =  self.oWin._oCardTextPane
        # Card text should start empty
        self.assertEqual(oCardTextFrame.view._oBuf.get_all_text(), "")
        # Set a card
        oCard = make_card('Aire of Elation', None)
        oCardTextFrame.set_card_text(oCard)
        sCardText = oCardTextFrame.view._oBuf.get_all_text()
        self.assertEqual(oCardTextFrame.view._oBuf.get_all_text(), AIRE)
        # Check expansion works as expected
        oCard = make_card('Aire of Elation', 'Anarchs')
        oCardTextFrame.set_card_text(oCard)
        sCardText = oCardTextFrame.view._oBuf.get_all_text()
        self.assertEqual(oCardTextFrame.view._oBuf.get_all_text(), AIRE)
        # Check different card
        oCard = make_card('Alexandra', None)
        oCardTextFrame.set_card_text(oCard)
        sCardText = oCardTextFrame.view._oBuf.get_all_text()
        self.assertEqual(oCardTextFrame.view._oBuf.get_all_text(), ALEXANDRA)


if __name__ == "__main__":
    unittest.main()
