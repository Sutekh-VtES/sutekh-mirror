# test_Filters.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Sutekh Filters tests"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.io import test_WhiteWolfParser
from sutekh.core.SutekhObjects import AbstractCard, IAbstractCard, \
        PhysicalCard, IPhysicalCard, Expansion, IExpansion
from sutekh.core import Filters
from sqlobject import SQLObjectNotFound
import unittest

class FilterTests(SutekhTest):
    """Test class for testing Sutekh Filters"""
    aExpectedCards = test_WhiteWolfParser.WhiteWolfParserTests.aExpectedCards

    def _physical_test(self, tTest):
        """Convert the tuple describing the test as a filter and a list of
           card names and optional expansions into the correct
           filter on the physical card list and a list of expected
           PhysicalCard objects."""
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
            # pylint: disable-msg=E1101
            # sqlobject confuses pylint
            oAbs = IAbstractCard(sName)
            aExps = set([oRarity.expansion for oRarity in oAbs.rarity])

            if None in aAllowedExpansions:
                aPhysicalCards.append(IPhysicalCard((oAbs, None)))

            for oExp in aExps:
                if not oExp in aAllowedExpansions:
                    continue
                try:
                    aPhysicalCards.append(IPhysicalCard((oAbs, oExp)))
                except SQLObjectNotFound:
                    self.fail(
                        "Missing physical card %s from expansion %s"
                        % (oAbs.name, oExp.name)
                    )

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
                u"Abd al-Rashid", u"Abdelsobek", u"Abebe", u"Aeron",
                u"Angelica, The Canonicus", u"Kabede Maru", u"Sha-Ennu"]),
            (Filters.MultiDisciplineFilter(['nec', 'qui']), [u"Abd al-Rashid",
                u"Abdelsobek", u"Abebe", u"Akram", u"Ambrogino Giovanni",
                u"Kabede Maru"]),
            (Filters.ExpansionFilter('NoR'), [u"Abjure",
                u'Anna "Dictatrix11" Suljic', u'Earl "Shaka74" Deams',
                u'Inez "Nurse216" Villagrande']),
            (Filters.MultiExpansionFilter(['NoR', 'LoB']), [u".44 Magnum",
                u"Abebe", u"Abjure", u"Abombwe",
                u'Anna "Dictatrix11" Suljic', u"Cesewayo",
                u'Earl "Shaka74" Deams', u'Inez "Nurse216" Villagrande']),
            (Filters.ExpansionRarityFilter(('Sabbat', 'Rare')),
                [u"Ablative Skin"]),
            (Filters.MultiExpansionRarityFilter([('Third', 'Uncommon'),
                ('Jyhad', 'Rare')]), [u"Aaron's Feeding Razor", u"Abbot"]),
            (Filters.DisciplineLevelFilter(('cel', 'superior')),
                [u"Abd al-Rashid", u"Akram", u"Alexandra", u"Anson",
                    u"Bronwen", u"Cesewayo", u"Kabede Maru"]),
            (Filters.MultiDisciplineLevelFilter([('obt', 'inferior'),
                ('pot', 'inferior'), ('obf', 'superior')]),
                [u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady",
                    u"Aeron", u"Akram", u"Bronwen", u"Kabede Maru"]),
            (Filters.MultiDisciplineLevelFilter(['obt with inferior',
                'pot with inferior', 'obf with superior']),
                [u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady",
                    u"Aeron", u"Akram", u"Bronwen", u"Kabede Maru"]),
            (Filters.CardTypeFilter('Equipment'), [u".44 Magnum", u"AK-47",
                u"Aaron's Feeding Razor"]),
            (Filters.MultiCardTypeFilter(['Power', 'Action']), [u"Abbot",
                u"Abjure", u"Ablative Skin"]),
            (Filters.SectFilter('Sabbat'), [u"Aaron Bathurst",
                u"Aaron Duggan, Cameron's Toady", u"Aeron", u"Alfred Benezri",
                u"Angelica, The Canonicus", u"Bronwen", u"Sha-Ennu"]),
            (Filters.MultiSectFilter(['Sabbat', 'Independent']),
                [u"Aabbt Kindred",
                u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady",
                u"Abd al-Rashid", u"Abdelsobek", u"Abebe",
                u"Aeron", u"Alfred Benezri", u"Ambrogino Giovanni",
                u"Angelica, The Canonicus", u"Bronwen",
                u"L\xe1z\xe1r Dobrescu", u"Sha-Ennu"]),
            # (Filters.TitleFilter('Bishop'), []),
            # (Filters.MultiTitleFilter(['Bishop', 'Prince']), []),
            # (Filters.CreedFilter('Judge'), []),
            # (Filters.MultiCreedFilter(['Judge', 'Innocent']), []),
            (Filters.VirtueFilter('Redemption'), [u"Abjure",
                u'Anna "Dictatrix11" Suljic']),
            #(Filters.MultiVirtueFilter(['Redemption', 'Judgement']),
            #    [u"Abjure"]),
            (Filters.GroupFilter(4), [u"Aaron Bathurst", u"Abebe",
                u'Anna "Dictatrix11" Suljic', u"Cesewayo",
                u'Earl "Shaka74" Deams', u'Inez "Nurse216" Villagrande',
                u"Sha-Ennu"]),
            (Filters.MultiGroupFilter([4, 5]), [u"Aaron Bathurst",
                u"Abdelsobek", u"Abebe", u'Anna "Dictatrix11" Suljic',
                u"Cesewayo", u'Earl "Shaka74" Deams',
                u'Inez "Nurse216" Villagrande', u"Kabede Maru",
                u"Sha-Ennu"]),
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
            (Filters.CardTextFilter('strike'), [u".44 Magnum", u"AK-47",
                u"Aeron", u"Anastasz di Zagreb", u"Bronwen"]),
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
                    u"Ablative Skin", u"Abombwe", u'Anna "Dictatrix11" Suljic',
                    u'Earl "Shaka74" Deams', u'Inez "Nurse216" Villagrande']),
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
            u"Brujah", u"Brujah antitribu", u"Follower of Set", u"Giovanni",
            u"Lasombra", u"Nosferatu antitribu", u"Osebo", u"Pander",
            u"Ravnos", u"Samedi", u"Toreador", u"Tremere", u"Tzimisce",
            u"Ventrue"])
        self.assertEqual(Filters.MultiDisciplineFilter.get_values(),
                [u"Abombwe", u"Animalism", u"Auspex", u"Celerity",
                    u"Chimerstry", u"Dementation", u"Dominate", u"Fortitude",
                    u"Necromancy", u"Obfuscate", u"Obtenebration", u"Potence",
                    u"Presence", u"Protean", u"Quietus", u"Serpentis",
                    u"Thaumaturgy", u"Thanatosis", u"Vicissitude"])
        self.assertEqual(Filters.MultiCardTypeFilter.get_values(), [u"Action",
            u"Combat", u"Equipment", u"Imbued", u"Master", u"Power",
            u"Reaction", u"Vampire"])
        #self.assertEqual(Filters.MultiTitleFilter.get_values(), [])
        #self.assertEqual(Filters.MultiCreedFilter.get_values(), [])
        self.assertEqual(Filters.MultiVirtueFilter.get_values(),
                [u"Innocence", u"Judgment", u"Martyrdom", u"Redemption",
                    u"Vision"])

        # Test the physical card filtering
        for oFilter, aExpectedCards in aPhysicalTests:
            aCards = sorted(oFilter.select(PhysicalCard).distinct())
            self.assertEqual(aCards, aExpectedCards, "Filter Object %s"
                    " failed. %s != %s." % (oFilter, aCards, aExpectedCards))

        # test filtering on expansion
        aExpansionTests = [
                (Filters.PhysicalExpansionFilter('Jyhad'),
                    ['.44 Magnum', "Aaron's Feeding Razor", u"Anson"],
                    ['Jyhad']),
                (Filters.PhysicalExpansionFilter('LoB'),
                    ['Abombwe','.44 Magnum', 'Abebe', u"Cesewayo"],
                    ['LoB']),
                (Filters.PhysicalExpansionFilter(None),
                    self.aExpectedCards,
                    [None]),
                (Filters.MultiPhysicalExpansionFilter(['LoB', 'LotN']),
                    ['Abombwe','.44 Magnum', 'Abebe', 'AK-47', 'Abdelsobek',
                        u"Cesewayo", u"Kabede Maru"], ['LoB', 'LotN']),
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
                    [u"Aaron Duggan, Cameron's Toady", u"Abandoning the Flesh",
                     u"Abd al-Rashid", u"Akram", u"Alexandra",
                     u"Alfred Benezri", u"Angelica, The Canonicus", u"Bronwen",
                     u"Gracis Nostinus", u'L\xe1z\xe1r Dobrescu',
                     u'Yvette, The Hopeless']),
                (Filters.MultiPhysicalCardCountFilter(['4']),
                    ["Aaron's Feeding Razor", 'Ablative Skin',
                        u"Anastasz di Zagreb", u"Anson"]),
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
            oFilter, aExpectedCards = self._physical_test((oFilter,
                aExpectedNames))
            aCards = sorted(oFilter.select(PhysicalCard).distinct())
            self.assertEqual(aCards, aExpectedCards, "Filter Object %s"
                    " failed. %s != %s." % (oFilter, aCards, aExpectedCards))

        # TODO: Add tests for:
        #   PhysicalCardSetFilter

if __name__ == "__main__":
    unittest.main()
