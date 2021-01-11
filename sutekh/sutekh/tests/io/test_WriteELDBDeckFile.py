# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an ELDB deck"""

import unittest

from sutekh.base.core.CardSetHolder import CardSetWrapper

from sutekh.io.WriteELDBDeckFile import WriteELDBDeckFile
from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1

EXPECTED_1 = """"Test Set 1"
"A test author"
"A test comment"
6
"Abebe"
"Alan Sovereign (ADV)"
"Hektor"
"Inez 'Nurse216' Villagrande"
"Siamese, The"
"Siamese, The"
28
".44 Magnum"
".44 Magnum"
".44 Magnum"
".44 Magnum"
"AK-47"
"AK-47"
"Aaron`s Feeding Razor"
"Abbot"
"Abbot"
"Abombwe"
"Abombwe"
"Aire of Elation"
"Aire of Elation"
"Aire of Elation"
"Anarch Manifesto, An"
"Hide the Heart"
"Immortal Grapple"
"Immortal Grapple"
"Immortal Grapple"
"Immortal Grapple"
"Path of Blood, The"
"Scapelli, The Family `Mechanic`"
"Swallowed by the Night"
"Swallowed by the Night"
"Walk of Flame"
"Walk of Flame"
"Walk of Flame"
"Walk of Flame"
"""


class ELDBDeckWriterTests(SutekhTest):
    """class for the ELDB deck writer tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_deck_writer(self):
        """Test ELDB deck writing"""
        oPhysCardSet1 = make_set_1()

        # Check output

        oWriter = WriteELDBDeckFile()
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))

        self.assertEqual(sData, EXPECTED_1)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
