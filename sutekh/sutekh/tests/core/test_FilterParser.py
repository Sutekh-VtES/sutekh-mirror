# test_FilterParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007, 2008 Simon Cross <hodgestar@gmail.com>,
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Tests the Filter Parser code"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.io import test_WhiteWolfParser
from sutekh.core.SutekhObjects import AbstractCard
from sutekh.core import FilterParser
import unittest

class FilterParserTests(SutekhTest):
    """Class for the test cases"""
    aExpectedCards = test_WhiteWolfParser.WhiteWolfParserTests.aExpectedCards
    oFilterParser = FilterParser.FilterParser()

    def test_basic(self):
        """Set of simple tests of the filter parser."""
        # setup filters
        aTests = [
            # Single & Multiple value tests
            ('Clan in "Follower of Set"', [u"Aabbt Kindred", u"Abdelsobek"]),
            ('Clan in Ravnos, Samedi', [u"Abebe", u"L\xe1z\xe1r Dobrescu"]),
            ('Discipline in obf', [u"Aaron Bathurst", u"Abd al-Rashid",
                u"Abdelsobek", u"Abebe", u"Aeron", u"Angelica, The Canonicus",
                u"Kabede Maru", u"Sha-Ennu"]),
            ('Discipline in nec, Quietus', [u"Abd al-Rashid", u"Abdelsobek",
                u"Abebe", u"Akram", u"Ambrogino Giovanni", u"Kabede Maru"]),
            ('Expansion_with_Rarity in Sabbat with Rare', [u"Ablative Skin"]),
            ('Expansion_with_Rarity in Third with Uncommon, Jyhad with Rare',
                [u"Aaron's Feeding Razor", u"Abbot"]),
            ('Discipline_with_Level in cel with superior', [u"Abd al-Rashid",
                u"Akram", u"Alexandra", u"Anson", u"Bronwen", u"Cesewayo",
                u"Kabede Maru"]),
            ('Discipline_with_Level in obt with inferior,'
                ' Potence with inferior, obf with superior',
                [u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady",
                    u"Aeron", u"Akram", u"Bronwen", u"Kabede Maru"]),
            ('CardType in Equipment', [u".44 Magnum", u"AK-47",
                u"Aaron's Feeding Razor"]),
            ('CardType in Power,Action', [u"Abbot", u"Abjure",
                u"Ablative Skin"]),
            ('Sect in Sabbat', [u"Aaron Bathurst",
                u"Aaron Duggan, Cameron's Toady", u"Aeron", u"Alfred Benezri",
                u"Angelica, The Canonicus", u"Bronwen", u"Sha-Ennu"]),
            ('Sect in Sabbat, Independent', [u"Aabbt Kindred",
                u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady",
                u"Abd al-Rashid", u"Abdelsobek", u"Abebe",
                u"Aeron", u"Alfred Benezri", u"Ambrogino Giovanni",
                u"Angelica, The Canonicus", u"Bronwen",
                u"L\xe1z\xe1r Dobrescu", u"Sha-Ennu"]),
            ('Title in Bishop', [u"Alfred Benezri"]),
            ('Title in "Independent with 1 vote"',
                [u"Ambrogino Giovanni"]),
            ('Title in Bishop, Prince',
                    [u"Alfred Benezri", u"Anson"]),
            ('Title in Magaji, Regent',
                    [u"Cesewayo", u"Kabede Maru", u"Sha-Ennu"]),
            ('Title in Primogen, Priscus, Cardinal',
                    [u"Akram", u"Angelica, The Canonicus", u"Bronwen"]),
            ('Creed = Martyr',
                    [u'Anna "Dictatrix11" Suljic']),
            ('Creed = Martyr, Innocent',
                    [u'Anna "Dictatrix11" Suljic',
                        u'Inez "Nurse216" Villagrande']),
            ('Virtue in Redemption', [u"Abjure",
                u'Anna "Dictatrix11" Suljic']),
            ('Group in 4', [u"Aaron Bathurst", u"Abebe",
                u'Anna "Dictatrix11" Suljic', u"Cesewayo",
                u'Earl "Shaka74" Deams', u'Inez "Nurse216" Villagrande',
                u"Sha-Ennu"]),
            ('Group in 4, 5', [u"Aaron Bathurst", u"Abdelsobek", u"Abebe",
                u'Anna "Dictatrix11" Suljic', u"Cesewayo",
                u'Earl "Shaka74" Deams', u'Inez "Nurse216" Villagrande',
                u"Kabede Maru", u"Sha-Ennu"]),
            ('Capacity in 2', [u"Aaron Duggan, Cameron's Toady"]),
            ('Capacity in 2,1', [u"Aaron Duggan, Cameron's Toady",
                u"Abombwe"]),
            ('Cost in 5', [u"AK-47"]),
            ('Cost in 2,5', [u".44 Magnum", u"AK-47"]),
            ('Life in 6', [u'Anna "Dictatrix11" Suljic',
                u'Earl "Shaka74" Deams']),
            ('Life in 3, 6', [u'Anna "Dictatrix11" Suljic',
                u'Earl "Shaka74" Deams', u'Inez "Nurse216" Villagrande']),
            ('CostType in Pool', [u".44 Magnum", u"AK-47",
                u"Aaron's Feeding Razor"]),
            ('CostType in Blood', []),
            ('CostType in Pool, Blood', [u".44 Magnum", u"AK-47",
                u"Aaron's Feeding Razor"]),
            ('Life in 4', []),
            ('Life in 4,5', []),

            # Text Entry Filters Filters
            ('CardText in strike', [u".44 Magnum", u"AK-47", u"Aeron",
                u"Anastasz di Zagreb", u"Bronwen"]),
            ('CardName in cameron', [u"Aaron Duggan, Cameron's Toady"]),
            (u'CardName in "L\xe1z\xe1r"', [u"L\xe1z\xe1r Dobrescu"]),

            # Compound Filters
            ('CardType in Equipment AND Cost in 5', [u"AK-47"]),
            ('CardType in Equipment OR CardType in Power',
                    [u".44 Magnum", u"AK-47", u"Aaron's Feeding Razor",
                        u"Abjure"]),
            ('NOT CardType in Equipment, Vampire',
                    [u"Abandoning the Flesh", u"Abbot", u"Abjure",
                        u"Ablative Skin", u"Abombwe",
                        u'Anna "Dictatrix11" Suljic', u'Earl "Shaka74" Deams',
                        u'Inez "Nurse216" Villagrande']),
            ('CardType not in Equipment, Vampire',
                    [u"Abandoning the Flesh", u"Abbot", u"Abjure",
                        u"Ablative Skin", u"Abombwe",
                        u'Anna "Dictatrix11" Suljic', u'Earl "Shaka74" Deams',
                        u'Inez "Nurse216" Villagrande']),
        ]

        # Abstract Card Filtering Tests
        for sFilter, aExpectedNames in aTests:
            oAST = self.oFilterParser.apply(sFilter)
            oFilter = oAST.get_filter()
            aCards = oFilter.select(AbstractCard).distinct()
            aNames = sorted([oC.name for oC in aCards])
            self.assertEqual(aNames, aExpectedNames,
                    "Filter Object %s failed."
                    " %s != %s." % (oFilter, aNames, aExpectedNames))

if __name__ == "__main__":
    unittest.main()
