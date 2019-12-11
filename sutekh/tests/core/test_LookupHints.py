# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test cases for the LookupHints behaviour"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.base.core.BaseAdapters import IAbstractCard


class LookupTests(SutekhTest):
    """class for various lookup tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_basic(self):
        """Test behaviour"""
        oCard = IAbstractCard("Pier 13, Port of Baltimore")
        self.assertEqual(oCard, IAbstractCard("Pier 13"))

        oCard = IAbstractCard("Anastasz di Zagreb")
        self.assertEqual(oCard, IAbstractCard("Anastaszdi Zagreb"))

        oCard = IAbstractCard("The Path of Blood")
        # Article shifting
        self.assertEqual(oCard, IAbstractCard("Path of Blood, The"))

        # Odd cases
        self.assertEqual(oCard, IAbstractCard("THE PATH OF bLOOD"))
        self.assertEqual(oCard, IAbstractCard("the paTH oF bLOOD"))

        # Check that the AKA parsing works as expected
        oCard = IAbstractCard(u"L\xe1z\xe1r Dobrescu")
        self.assertEqual(oCard, IAbstractCard("Lazar Dobrescu"))

        # check (Adv) automatic lookups
        oCard = IAbstractCard(u"Kemintiri (Advanced)")
        self.assertEqual(oCard, IAbstractCard("Kemintiri (Adv)"))

        oCard = IAbstractCard(u"Alan Sovereign (Advanced)")
        self.assertEqual(oCard, IAbstractCard("Alan Sovereign (Adv)"))
