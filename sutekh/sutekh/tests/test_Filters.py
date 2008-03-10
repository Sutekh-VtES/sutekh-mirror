# test_Filters.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests import test_WhiteWolfParser
from sutekh.core.SutekhObjects import AbstractCard, IAbstractCard
from sutekh.core import Filters
import unittest

class FilterTests(SutekhTest):
    aExpectedCards = test_WhiteWolfParser.WhiteWolfParserTests.aExpectedCards

    def testBasic(self):
        # setup filters
        aTests = [
            # Single / Multi Filters
            (Filters.ClanFilter('Follower of Set'), [u"Aabbt Kindred", u"Abdelsobek"]),
            (Filters.MultiClanFilter(['Ravnos','Samedi']), [u"Abebe", u"L\xe1z\xe1r Dobrescu"]),
            (Filters.DisciplineFilter('obf'), [u"Aaron Bathurst", u"Abd al-Rashid", u"Abdelsobek", u"Abebe"]),
            (Filters.MultiDisciplineFilter(['nec','qui']), [u"Abd al-Rashid", u"Abdelsobek", u"Abebe"]),
            (Filters.ExpansionFilter('NoR'), [u"Abjure"]),
            (Filters.MultiExpansionFilter(['NoR','LoB']), [u".44 Magnum", u"Abebe", u"Abjure", u"Abombwe"]),
            (Filters.ExpansionRarityFilter(('Sabbat','Rare')), [u"Ablative Skin"]),
            (Filters.MultiExpansionRarityFilter([('Third','Uncommon'),('Jyhad','Rare')]), [u"Aaron's Feeding Razor", u"Abbot"]),
            (Filters.DisciplineLevelFilter(('cel','superior')), [u"Abd al-Rashid"]),
            (Filters.MultiDisciplineLevelFilter([('obt','inferior'),('pot','inferior'),('obf','superior')]), [u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady"]),
            (Filters.MultiDisciplineLevelFilter(['obt with inferior','pot with inferior','obf with superior']), [u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady"]),
            (Filters.CardTypeFilter('Equipment'), [u".44 Magnum", u"AK-47", u"Aaron's Feeding Razor"]),
            (Filters.MultiCardTypeFilter(['Power','Action']), [u"Abbot", u"Abjure", u"Ablative Skin"]),
            (Filters.SectFilter('Sabbat'), [u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady"]),
            (Filters.MultiSectFilter(['Sabbat','Independent']), [u"Aabbt Kindred", u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady", u"Abd al-Rashid", u"Abdelsobek", u"Abebe", u"L\xe1z\xe1r Dobrescu"]),
            # (Filters.TitleFilter('Bishop'), []),
            # (Filters.MultiTitleFilter(['Bishop','Prince']), []),
            # (Filters.CreedFilter('Judge'), []),
            # (Filters.MultiCreedFilter(['Judge','Innocent']), []),
            (Filters.VirtueFilter('Redemption'), [u"Abjure"]),
            # (Filters.MultiVirtueFilter(['Redemption','Judgement']), [u"Abjure"]),
            (Filters.GroupFilter(4), [u"Aaron Bathurst", u"Abebe"]),
            (Filters.MultiGroupFilter([4,5]), [u"Aaron Bathurst", u"Abdelsobek", u"Abebe"]),
            (Filters.CapacityFilter(2), [u"Aaron Duggan, Cameron's Toady"]),
            (Filters.MultiCapacityFilter([2,1]), [u"Aaron Duggan, Cameron's Toady", u"Abombwe"]),
            (Filters.CostFilter(5), [u"AK-47"]),
            (Filters.MultiCostFilter([2,5]), [u".44 Magnum", u"AK-47"]),
            (Filters.CostTypeFilter('Pool'), [u".44 Magnum", u"AK-47", u"Aaron's Feeding Razor"]),
            (Filters.CostTypeFilter('Blood'), []),
            (Filters.MultiCostTypeFilter(['Pool','Blood']), [u".44 Magnum", u"AK-47", u"Aaron's Feeding Razor"]),
            (Filters.LifeFilter(4), []),
            (Filters.MultiLifeFilter([4,5]), []),

            # Other Filters
            (Filters.CardTextFilter('strike'), [u".44 Magnum", u"AK-47"]),
            (Filters.CardNameFilter(u'L\xe1z\xe1r'), [u"L\xe1z\xe1r Dobrescu"]),
            (Filters.NullFilter(), self.aExpectedCards),
            (Filters.SpecificCardFilter(IAbstractCard("Abebe")), [u"Abebe"]),

            # Compound Filters
            (Filters.FilterAndBox([Filters.CardTypeFilter('Equipment'),Filters.CostFilter(5)]), [u"AK-47"]),
            (Filters.FilterOrBox([Filters.CardTypeFilter('Equipment'),Filters.CardTypeFilter('Power')]), [u".44 Magnum", u"AK-47", u"Aaron's Feeding Razor", u"Abjure"]),
            (Filters.FilterNot(Filters.MultiCardTypeFilter(['Equipment','Vampire'])), [u"Abandoning the Flesh", u"Abbot", u"Abjure", u"Ablative Skin", u"Abombwe"]),
        ]

        # TODO: Put in some data for titles, creeds, virtues and life

        # Abstract Card Filtering Tests
        for oFilter, aExpectedNames in aTests:
            aCards = oFilter.select(AbstractCard).distinct()
            aNames = sorted([oC.name for oC in aCards])
            self.assertEqual(aNames,aExpectedNames,"Filter Object %s failed. %s != %s." % (oFilter,aNames,aExpectedNames))

        # Filter values Tests
        self.assertEqual(Filters.MultiClanFilter.get_values(),[u"Assamite", u"Follower of Set", u"Lasombra", u"Nosferatu antitribu", u"Ravnos", u"Samedi"])
        self.assertEqual(Filters.MultiDisciplineFilter.get_values(),[u"Celerity", u"Dementation", u"Fortitude", u"Necromancy", u"Obfuscate", u"Obtenebration", u"Potence", u"Presence", u"Quietus", u"Serpentis", u"Thanatosis"])
        self.assertEqual(Filters.MultiCardTypeFilter.get_values(),[u"Action", u"Combat", u"Equipment", u"Master", u"Power", u"Reaction", u"Vampire"])
        self.assertEqual(Filters.MultiTitleFilter.get_values(),[])
        self.assertEqual(Filters.MultiCreedFilter.get_values(),[])
        self.assertEqual(Filters.MultiVirtueFilter.get_values(),[u"Redemption"])

        # TODO: Add tests for:
        #   PhysicalCardFilter
        #   PhysicalCardSetFilter
        #   AbstractCardSetFilter

if __name__ == "__main__":
    unittest.main()
