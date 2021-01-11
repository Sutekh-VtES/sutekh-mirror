# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an PmWiki importable format"""

import unittest

from sutekh.base.core.CardSetHolder import CardSetWrapper

from sutekh.io.WritePmwiki import WritePmwiki
from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1

EXPECTED_1 = """(:title Test Set 1 by A test author :)

!! Description
A test comment
!! Notes


!! Crypt [6 vampires]
 2x The Siamese
 1x Hektor
 1x Alan Sovereign Adv
 1x Abebe
 1x Inez "Nurse216" Villagrande

!! Library [28 cards]

!!! Action [2]
 2x Abbot

!!! Action Modifier [3]
 3x Aire of Elation

!!! Action Modifier/Combat [2]
 2x Swallowed by the Night

!!! Ally [1]
 1x Scapelli, The Family "Mechanic"

!!! Combat [8]
 4x Immortal Grapple
 4x Walk of Flame

!!! Equipment [8]
 4x .44 Magnum
 2x AK-47
 1x Aaron\'s Feeding Razor
 1x An Anarch Manifesto

!!! Master [3]
 2x Abombwe
 1x The Path of Blood

!!! Reaction [1]
 1x Hide the Heart

"""


class PmwikiDeckWriterTests(SutekhTest):
    """class for the JOL deck writer tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_deck_writer(self):
        """Test Pmwiki deck writing"""
        oPhysCardSet1 = make_set_1()

        # Check output

        oWriter = WritePmwiki()
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))

        self.assertEqual(sData, EXPECTED_1)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
