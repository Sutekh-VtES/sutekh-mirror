# test_WhiteWolfParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Test the white wolf card reader"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.core.SutekhObjects import AbstractCard, IAbstractCard
import unittest

class WhiteWolfParserTests(SutekhTest):
    """Test class for the white wolf card reader.

       Check the parsing done in SutekhTest setup and verify the results
       are correct.
       """
    aExpectedCards = [
        u".44 Magnum", u"AK-47", u"Aabbt Kindred",
        u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady",
        u"Aaron's Feeding Razor", u"Abandoning the Flesh",
        u"Abbot", u"Abd al-Rashid", u"Abdelsobek",
        u"Abebe", u"Abjure", u"Ablative Skin",
        u"Abombwe", u"L\xe1z\xe1r Dobrescu",
    ]

    def test_basic(self):
        """Basic WW list parser tests"""
        # pylint: disable-msg=E1101
        # IAbstractCard + SQLObject magic confuses pylint
        aCards = sorted(list(AbstractCard.select()), cmp=lambda oC1, oC2:
                cmp(oC1.name, oC2.name))

        # Check card names
        self.assertEqual([oC.name for oC in aCards], self.aExpectedCards)

        # Check Magnum
        # pylint: disable-msg=C0103
        # 044 is OK here
        o44 = IAbstractCard(".44 Magnum")
        self.assertEqual(o44.canonicalName, u".44 magnum")
        self.assertEqual(o44.name, u".44 Magnum")
        self.failUnless(o44.text.startswith(u"Weapon, gun.\n2R"))
        self.failUnless(o44.text.endswith(u"each combat."))
        self.assertEqual(o44.group, None)
        self.assertEqual(o44.capacity, None)
        self.assertEqual(o44.cost, 2)
        self.assertEqual(o44.life, None)
        self.assertEqual(o44.costtype, 'pool')
        self.assertEqual(o44.level, None)
        # pylint: enable-msg=C0103

        # Check Dobrescu
        oDob = IAbstractCard(u"L\xe1z\xe1r Dobrescu")
        self.assertEqual(oDob.canonicalName, u"l\xe1z\xe1r dobrescu")
        self.assertEqual(oDob.name, u"L\xe1z\xe1r Dobrescu")
        self.failUnless(oDob.text.startswith(
            u"Independent: L\xe1z\xe1r may move"))
        self.failUnless(oDob.text.endswith(u"as a (D) action."))
        self.assertEqual(oDob.group, 2)
        self.assertEqual(oDob.capacity, 3)
        self.assertEqual(oDob.cost, None)
        self.assertEqual(oDob.life, None)
        self.assertEqual(oDob.costtype, None)
        self.assertEqual(oDob.level, None)

        # Things still to check:
        #discipline
        #rarity
        #clan
        #cardtype
        #sect
        #title
        #creed
        #virtue
        #rulings


if __name__ == "__main__":
    unittest.main()
