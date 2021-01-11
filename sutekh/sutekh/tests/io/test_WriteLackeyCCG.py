# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an Lackey CCG file"""

import unittest

from sutekh.base.core.CardSetHolder import CardSetWrapper

from sutekh.io.WriteLackeyCCG import WriteLackeyCCG
from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1

EXPECTED_1 = """4\t.44 Magnum
2\tAK-47
1\tAaron's Feeding Razor
2\tAbbot
2\tAbombwe
3\tAire of Elation
1\tAnarch Manifesto, An
1\tHide the Heart
4\tImmortal Grapple
1\tPath of Blood, The
1\tScapelli, The Family 'Mechanic'
2\tSwallowed by the Night
4\tWalk of Flame
Crypt:
1\tAbebe
1\tAlan Sovereign Adv.
1\tHektor
1\tInez ''Nurse216'' Villagrande
2\tSiamese, The
"""


class LackeyWriterTests(SutekhTest):
    """class for the Lackey CCG deck writer tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_deck_writer(self):
        """Test Lackey CCG deck writing"""
        oPhysCardSet1 = make_set_1()

        # Check output

        oWriter = WriteLackeyCCG()
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))

        self.assertEqual(sData, EXPECTED_1)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
