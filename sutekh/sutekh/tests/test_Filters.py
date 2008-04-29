# test_Filters.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Sutekh Filters tests"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests import test_WhiteWolfParser
from sutekh.core.SutekhObjects import AbstractCard, IAbstractCard, \
        PhysicalCard, IPhysicalCard, Expansion, IExpansion
from sutekh.core import Filters
import unittest

class FilterTests(SutekhTest):
    """Test class for testing Sutekh Filters"""
    aExpectedCards = test_WhiteWolfParser.WhiteWolfParserTests.aExpectedCards

    @staticmethod
    def _physical_test(tTest):
        if len(tTest) == 2:
            oFilter, aExpectedNames = tTest
            aAllowedExpansions = set(Expansion.select())
            aAllowedExpansions.add(None)
        else:
            assert len(tTest) == 3
            oFilter, aExpectedNames = tTest[:2]
            aAllowedExpansions = set([IExpansion(sExp) for sExp in tTest[2]
                                        if sExp is not None])
            if None in tTest[2]:
                aAllowedExpansions.add(None)

        aPhysicalCards = []
        for sName in aExpectedNames:
            oAbs = IAbstractCard(sName)
            aExps = set([oRarity.expansion for oRarity in oAbs.rarity])

            if None in aAllowedExpansions:
                aPhysicalCards.append(IPhysicalCard((oAbs,None)))

            aPhysicalCards.extend([IPhysicalCard((oAbs, oExp)) \
                                   for oExp in aExps \
                                   if oExp in aAllowedExpansions])

        oFullFilter = Filters.FilterAndBox([Filters.PhysicalCardFilter(),
                                            oFilter])

        return oFullFilter, sorted(aPhysicalCards)

    # pylint: disable-msg=R0914
    # We don't really care about the number of local variables here
    def test_basic(self):
        """Simple tests of the filter"""
        # setup filters
        aTests = [
            # Single / Multi Filters
            (Filters.ClanFilter('Follower of Set'), [u"Aabbt Kindred",
                u"Abdelsobek"]),
            (Filters.MultiClanFilter(['Ravnos', 'Samedi']), [u"Abebe",
                u"L\xe1z\xe1r Dobrescu"]),
            (Filters.DisciplineFilter('obf'), [u"Aaron Bathurst",
                u"Abd al-Rashid", u"Abdelsobek", u"Abebe"]),
            (Filters.MultiDisciplineFilter(['nec', 'qui']), [u"Abd al-Rashid",
                u"Abdelsobek", u"Abebe"]),
            (Filters.ExpansionFilter('NoR'), [u"Abjure"]),
            (Filters.MultiExpansionFilter(['NoR', 'LoB']), [u".44 Magnum",
                u"Abebe", u"Abjure", u"Abombwe"]),
            (Filters.ExpansionRarityFilter(('Sabbat', 'Rare')),
                [u"Ablative Skin"]),
            (Filters.MultiExpansionRarityFilter([('Third', 'Uncommon'),
                ('Jyhad', 'Rare')]), [u"Aaron's Feeding Razor", u"Abbot"]),
            (Filters.DisciplineLevelFilter(('cel', 'superior')),
                [u"Abd al-Rashid"]),
            (Filters.MultiDisciplineLevelFilter([('obt', 'inferior'),
                ('pot', 'inferior'), ('obf', 'superior')]),
                [u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady"]),
            (Filters.MultiDisciplineLevelFilter(['obt with inferior',
                'pot with inferior', 'obf with superior']),
                [u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady"]),
            (Filters.CardTypeFilter('Equipment'), [u".44 Magnum", u"AK-47",
                u"Aaron's Feeding Razor"]),
            (Filters.MultiCardTypeFilter(['Power', 'Action']), [u"Abbot",
                u"Abjure", u"Ablative Skin"]),
            (Filters.SectFilter('Sabbat'), [u"Aaron Bathurst",
                u"Aaron Duggan, Cameron's Toady"]),
            (Filters.MultiSectFilter(['Sabbat', 'Independent']),
                [u"Aabbt Kindred", u"Aaron Bathurst",
                    u"Aaron Duggan, Cameron's Toady", u"Abd al-Rashid",
                    u"Abdelsobek", u"Abebe", u"L\xe1z\xe1r Dobrescu"]),
            # (Filters.TitleFilter('Bishop'), []),
            # (Filters.MultiTitleFilter(['Bishop', 'Prince']), []),
            # (Filters.CreedFilter('Judge'), []),
            # (Filters.MultiCreedFilter(['Judge', 'Innocent']), []),
            (Filters.VirtueFilter('Redemption'), [u"Abjure"]),
            #(Filters.MultiVirtueFilter(['Redemption', 'Judgement']),
            #    [u"Abjure"]),
            (Filters.GroupFilter(4), [u"Aaron Bathurst", u"Abebe"]),
            (Filters.MultiGroupFilter([4, 5]), [u"Aaron Bathurst",
                u"Abdelsobek", u"Abebe"]),
            (Filters.CapacityFilter(2), [u"Aaron Duggan, Cameron's Toady"]),
            (Filters.MultiCapacityFilter([2, 1]),
                [u"Aaron Duggan, Cameron's Toady", u"Abombwe"]),
            (Filters.CostFilter(5), [u"AK-47"]),
            (Filters.MultiCostFilter([2, 5]), [u".44 Magnum", u"AK-47"]),
            (Filters.CostTypeFilter('Pool'), [u".44 Magnum", u"AK-47",
                u"Aaron's Feeding Razor"]),
            (Filters.CostTypeFilter('Blood'), []),
            (Filters.MultiCostTypeFilter(['Pool', 'Blood']), [u".44 Magnum",
                u"AK-47", u"Aaron's Feeding Razor"]),
            (Filters.LifeFilter(4), []),
            (Filters.MultiLifeFilter([4, 5]), []),

            # Other Filters
            (Filters.CardTextFilter('strike'), [u".44 Magnum", u"AK-47"]),
            (Filters.CardNameFilter(u'L\xe1z\xe1r'),
                [u"L\xe1z\xe1r Dobrescu"]),
            (Filters.NullFilter(), self.aExpectedCards),
            (Filters.SpecificCardFilter(IAbstractCard("Abebe")),
                [u"Abebe"]),

            # Compound Filters
            (Filters.FilterAndBox([Filters.CardTypeFilter('Equipment'),
                Filters.CostFilter(5)]),
                [u"AK-47"]),
            (Filters.FilterOrBox([Filters.CardTypeFilter('Equipment'),
                Filters.CardTypeFilter('Power')]), [u".44 Magnum", u"AK-47",
                    u"Aaron's Feeding Razor", u"Abjure"]),
            (Filters.FilterNot(Filters.MultiCardTypeFilter(['Equipment',
                'Vampire'])), [u"Abandoning the Flesh", u"Abbot", u"Abjure",
                    u"Ablative Skin", u"Abombwe"]),
        ]

        aPhysicalTests = [self._physical_test(tTest) for tTest in aTests]
        # TODO: Put in some data for titles, creeds, virtues and life

        # Abstract Card Filtering Tests
        for oFilter, aExpectedNames in aTests:
            aCards = oFilter.select(AbstractCard).distinct()
            aNames = sorted([oC.name for oC in aCards])
            self.assertEqual(aNames, aExpectedNames, "Filter Object %s"
                    " failed. %s != %s." % (oFilter, aNames, aExpectedNames))

        # Filter values Tests
        self.assertEqual(Filters.MultiClanFilter.get_values(), [u"Assamite",
            u"Follower of Set", u"Lasombra", u"Nosferatu antitribu", u"Ravnos",
            u"Samedi"])
        self.assertEqual(Filters.MultiDisciplineFilter.get_values(),
                [u"Celerity", u"Dementation", u"Fortitude", u"Necromancy",
                    u"Obfuscate", u"Obtenebration", u"Potence", u"Presence",
                    u"Quietus", u"Serpentis", u"Thanatosis"])
        self.assertEqual(Filters.MultiCardTypeFilter.get_values(), [u"Action",
            u"Combat", u"Equipment", u"Master", u"Power", u"Reaction",
            u"Vampire"])
        self.assertEqual(Filters.MultiTitleFilter.get_values(), [])
        self.assertEqual(Filters.MultiCreedFilter.get_values(), [])
        self.assertEqual(Filters.MultiVirtueFilter.get_values(),
                [u"Redemption"])

        # Test the physical card filtering
        for oFilter, aExpectedCards in aPhysicalTests:
            aCards = sorted(oFilter.select(PhysicalCard).distinct())
            self.assertEqual(aCards, aExpectedCards, "Filter Object %s"
                    " failed. %s != %s." % (oFilter, aCards, aExpectedCards))

        # test filtering on expansion
        aCardExpansions = [('.44 Magnum', 'Jyhad'),
                ('AK-47', 'LotN'),
                ('Abbot', 'Third Edition'),
                ('Abombwe', 'Legacy of Blood')]

        aExpansionTests = [
                (Filters.PhysicalExpansionFilter('Jyhad'),
                    ['.44 Magnum', "Aaron's Feeding Razor"],
                    ['Jyhad']),
                (Filters.PhysicalExpansionFilter('LoB'),
                    ['Abombwe','.44 Magnum', 'Abebe'],
                    ['LoB']),
                (Filters.PhysicalExpansionFilter(None),
                    self.aExpectedCards,
                    [None]),
                (Filters.MultiPhysicalExpansionFilter(['LoB', 'LotN']),
                    ['Abombwe','.44 Magnum', 'Abebe', 'AK-47', 'Abdelsobek'],
                    ['LoB', 'LotN']),
                (Filters.MultiPhysicalExpansionFilter(
                    ['  Unspecified Expansion', 'VTES']),
                    self.aExpectedCards,
                    [None,'VTES']),
        ]

        for tTest in aExpansionTests:
            oFilter, aExpectedCards = self._physical_test(tTest)
            aCards = sorted(oFilter.select(PhysicalCard).distinct())
            self.assertEqual(aCards, aExpectedCards, "Filter Object %s"
                    " failed. %s != %s." % (oFilter, aCards, aExpectedCards))

        aNumberTests = [
                (Filters.MultiPhysicalCardCountFilter(['3']),
                    ["Aaron Duggan, Cameron's Toady", 'Abandoning the Flesh',
                     'Abd al-Rashid', u'L\xe1z\xe1r Dobrescu']),
                (Filters.MultiPhysicalCardCountFilter(['4']),
                    ["Aaron's Feeding Razor", 'Ablative Skin']),
        ]

        # test abstract card selects
        for oFilter, aExpectedNames in aNumberTests:
            aCards = oFilter.select(AbstractCard).distinct()
            aNames = sorted([oC.name for oC in aCards])
            self.assertEqual(aNames, aExpectedNames, "Filter Object"
                    " %s failed. %s != %s." % (oFilter, aNames,
                        aExpectedNames))

        # test physical card selects
        for oFilter, aExpectedNames in aNumberTests:
            oFilter, aExpectedCards = self._physical_test((oFilter,aExpectedNames))
            aCards = sorted(oFilter.select(PhysicalCard).distinct())
            self.assertEqual(aCards, aExpectedCards, "Filter Object %s"
                    " failed. %s != %s." % (oFilter, aCards, aExpectedCards))

        # TODO: Add tests for:
        #   PhysicalCardSetFilter
        #   AbstractCardSetFilter

if __name__ == "__main__":
    unittest.main()
