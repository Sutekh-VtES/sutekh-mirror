# test_FilterParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007,2008 Simon Cross <hodgestar@gmail.com>,
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Tests the Filter Parser code"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests import test_WhiteWolfParser
from sutekh.core.SutekhObjects import AbstractCard, IAbstractCard
from sutekh.core import FilterParser, Filters
import unittest

class FilterTests(SutekhTest):
    aExpectedCards = test_WhiteWolfParser.WhiteWolfParserTests.aExpectedCards
    oFilterParser = FilterParser.FilterParser()

    def testBasic(self):
        # setup filters
        aTests = [
            # Single & Multiple value tests
            ('Clan in "Follower of Set"', [u"Aabbt Kindred", u"Abdelsobek"]),
            ('Clan in Ravnos, Samedi', [u"Abebe", u"L\xe1z\xe1r Dobrescu"]),
            ('Discipline in obf', [u"Aaron Bathurst", u"Abd al-Rashid", u"Abdelsobek", u"Abebe"]),
            ('Discipline in nec, Quietus', [u"Abd al-Rashid", u"Abdelsobek", u"Abebe"]),
            ('Expansion_with_Rarity in Sabbat with Rare', [u"Ablative Skin"]),
            ('Expansion_with_Rarity in Third with Uncommon, Jyhad with Rare', [u"Aaron's Feeding Razor", u"Abbot"]),
            ('Discipline_with_Level in cel with superior', [u"Abd al-Rashid"]),
            ('Discipline_with_Level in obt with inferior, Potence with inferior, obf with superior', [u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady"]),
            ('CardType in Equipment', [u".44 Magnum", u"AK-47", u"Aaron's Feeding Razor"]),
            ('CardType in Power,Action', [u"Abbot", u"Abjure", u"Ablative Skin"]),
            ('Sect in Sabbat', [u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady"]),
            ('Sect in Sabbat, Independent', [u"Aabbt Kindred", u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady", u"Abd al-Rashid", u"Abdelsobek", u"Abebe", u"L\xe1z\xe1r Dobrescu"]),
            ('Virtue in Redemption', [u"Abjure"]),
            ('Group in 4', [u"Aaron Bathurst", u"Abebe"]),
            ('Group in 4, 5', [u"Aaron Bathurst", u"Abdelsobek", u"Abebe"]),
            ('Capacity in 2', [u"Aaron Duggan, Cameron's Toady"]),
            ('Capacity in 2,1', [u"Aaron Duggan, Cameron's Toady", u"Abombwe"]),
            ('Cost in 5', [u"AK-47"]),
            ('Cost in 2,5', [u".44 Magnum", u"AK-47"]),
            ('CostType in Pool', [u".44 Magnum", u"AK-47", u"Aaron's Feeding Razor"]),
            ('CostType in Blood', []),
            ('CostType in Pool, Blood', [u".44 Magnum", u"AK-47", u"Aaron's Feeding Razor"]),
            ('Life in 4', []),
            ('Life in 4,5', []),

            # Text Entry Filters Filters
            ('CardText in strike', [u".44 Magnum", u"AK-47"]),
            ('CardName in cameron', [u"Aaron Duggan, Cameron's Toady"]),
            (u'CardName in "L\xe1z\xe1r"', [u"L\xe1z\xe1r Dobrescu"]),

            # Compound Filters
            ('CardType in Equipment AND Cost in 5', [u"AK-47"]),
            ('CardType in Equipment OR CardType in Power', 
                    [u".44 Magnum", u"AK-47", u"Aaron's Feeding Razor", u"Abjure"]),
            ('NOT CardType in Equipment, Vampire',
                    [u"Abandoning the Flesh", u"Abbot", u"Abjure", u"Ablative Skin", u"Abombwe"]),
            ('CardType not in Equipment, Vampire',
                    [u"Abandoning the Flesh", u"Abbot", u"Abjure", u"Ablative Skin", u"Abombwe"]),
        ]

        # Abstract Card Filtering Tests
        for sFilter, aExpectedNames in aTests:
            oAST = self.oFilterParser.apply(sFilter)
            oFilter = oAST.get_filter()
            aCards = oFilter.select(AbstractCard).distinct()
            aNames = sorted([oC.name for oC in aCards])
            self.assertEqual(aNames,aExpectedNames,"Filter Object %s failed. %s != %s." % (oFilter,aNames,aExpectedNames))

if __name__ == "__main__":
    unittest.main()
