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
Keywords:
*\t3 bleed
*\t0 intercept
*\t0 stealth
*\t1 strength
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


GYPSIES = """Gypsies
Cost: 3 pool
Life: 1
Card Type:
*\tAlly
Keywords:
*\t1 bleed
*\t1 stealth
*\t1 strength
*\tmortal
*\tunique
Clan:
*\tGangrel

Unique mortal with 1 life. 1 strength, 1 bleed.
Gypsies get +1 stealth on each of their actions.

Expansions:
*\tJyhad (Uncommon)
*\tVTES (Uncommon)

Artists:
*\tPete Venters"""

GYPSIES_ERRATA = """Gypsies
Cost: 3 pool
Life: 1
Card Type:
*\tAlly
Keywords:
*\t1 bleed
*\t1 stealth
*\t1 strength
*\tmortal
*\tunique
Clan:
*\tGangrel

Unique {mortal} with 1 life. 1 {strength}, 1 bleed.
Gypsies get +1 stealth on each of their actions.

Expansions:
*\tJyhad (Uncommon)
*\tVTES (Uncommon)

Artists:
*\tPete Venters"""


HIGH_TOP = """High Top
Cost: 4 pool
Life: 3
Card Type:
*\tAlly
Keywords:
*\t0 bleed
*\t1 intercept
*\t1 strength
*\tunique
*\twerewolf
Clan:
*\tAhrimane

Unique werewolf with 3 life. 1 strength, 0 bleed.
High Top gets +1 intercept. High Top may enter combat with any minion controlled by another Methuselah as a (D) action. High Top gets an additional strike each round and an optional maneuver once each combat. He may play cards requiring basic Celerity [cel] as a vampire with a capacity of 4. If High Top has less than 3 life during your unlock phase, he gains 1 life.

Expansions:
*\tBloodlines (Rare)
*\tLegacy of Blood (Rare)

Artists:
*\tMark Nelson"""


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
        oCardTextFrame = self.oWin._oCardTextPane
        # Card text should start empty
        self.assertEqual(oCardTextFrame.view._oBuf.get_all_text(), "")
        # Set a card
        oCard = make_card('Aire of Elation', None)
        oCardTextFrame.set_card_text(oCard)
        self.assertEqual(oCardTextFrame.view._oBuf.get_all_text(), AIRE)
        # Check expansion works as expected
        oCard = make_card('Aire of Elation', 'Anarchs')
        oCardTextFrame.set_card_text(oCard)
        self.assertEqual(oCardTextFrame.view._oBuf.get_all_text(), AIRE)
        # Check different cards
        oCard = make_card('Alexandra', None)
        oCardTextFrame.set_card_text(oCard)
        self.assertEqual(oCardTextFrame.view._oBuf.get_all_text(), ALEXANDRA)

        oCard = make_card('Gypsies', None)
        oCardTextFrame.set_card_text(oCard)
        self.assertEqual(oCardTextFrame.view._oBuf.get_all_text(), GYPSIES)

        oCard = make_card('High Top', None)
        oCardTextFrame.set_card_text(oCard)
        self.assertEqual(oCardTextFrame.view._oBuf.get_all_text(), HIGH_TOP)

    def test_show_errata(self):
        """Test with 'show errata markers' set"""
        # 'My Collection' is needed for default config
        _oMyCollection = PhysicalCardSet(name='My Collection')
        self.oWin.setup(self.oConfig)
        # Get the card text frame
        oCardTextFrame = self.oWin._oCardTextPane
        # Card text should start empty
        self.assertEqual(oCardTextFrame.view._oBuf.get_all_text(), "")
        # Set the 'show errata markers' option
        self.oConfig.set_show_errata_markers(True)

        oCard = make_card('Gypsies', None)
        oCardTextFrame.set_card_text(oCard)
        self.assertEqual(oCardTextFrame.view._oBuf.get_all_text(),
                         GYPSIES_ERRATA)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
