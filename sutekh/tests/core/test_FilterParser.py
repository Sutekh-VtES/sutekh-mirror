# test_FilterParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007, 2008 Simon Cross <hodgestar@gmail.com>,
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Tests the Filter Parser and FilterBox code"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.io import test_WhiteWolfParser
from sutekh.tests.core.test_Filters import make_physical_card_sets
from sutekh.core.SutekhObjects import AbstractCard, PhysicalCardSet, \
        PhysicalCard, MapPhysicalCardToPhysicalCardSet, IAbstractCard
from sutekh.core import FilterParser, Filters, FilterBox
from sutekh.core.FilterParser import escape, unescape
import unittest


class FilterParserTests(SutekhTest):
    """Class for the test cases"""
    aExpectedCards = test_WhiteWolfParser.WhiteWolfParserTests.aExpectedCards
    oFilterParser = FilterParser.FilterParser()

    # Useful helper functions
    def _parse_filter(self, sFilter):
        """Turn a filter expression into a filter"""
        oAST = self.oFilterParser.apply(sFilter)
        return oAST.get_filter()

    # pylint: disable-msg=R0201
    # I prefer to have these as methods
    def _get_abs_names(self, oFilter):
        """Get the names of the cards selected by a filter on the
           AbstractCards"""
        aCards = oFilter.select(AbstractCard).distinct()
        return sorted([oC.name for oC in aCards])

    def _get_physical_names(self, oPCSFilter, oFilter):
        """Combine a card set filter with the filter and return the card
           names"""
        # pylint: disable-msg=E1101
        # pyprotocols confuses pylinta
        oFullFilter = Filters.FilterAndBox([oPCSFilter, oFilter])
        aNames = [IAbstractCard(x).name for x in oFullFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        return sorted(aNames)

    # pylint: enable-msg=R0201

    # pylint: disable-msg=R0914
    # We don't really care about the number of local variables here
    def test_basic(self):
        """Set of simple tests of the filter parser."""
        # setup filters
        # The tests a given as "Expression", "Equivilant Filter"
        # where the two filters should give the same results
        aTests = [
            # Single & Multiple value tests
            ('Clan in "Follower of Set"',
                Filters.ClanFilter('Follower of Set')),
            ('Clan in Ravnos, Samedi',
                Filters.MultiClanFilter(['Ravnos', 'Samedi'])),
            ('Discipline in obf', Filters.DisciplineFilter('obf')),
            ('Discipline in fli', Filters.DisciplineFilter('fli')),
            ('Discipline in nec, Quietus',
                Filters.MultiDisciplineFilter(['nec', 'qui'])),
            ('Expansion_with_Rarity in Sabbat with Rare',
                Filters.ExpansionRarityFilter(('Sabbat', 'Rare'))),
            ('Expansion_with_Rarity in Third with Uncommon, Jyhad with Rare',
                Filters.MultiExpansionRarityFilter([('Third', 'Uncommon'),
                    ('Jyhad', 'Rare')])),
            ('Discipline_with_Level in cel with superior',
                Filters.DisciplineLevelFilter(('cel', 'superior'))),
            ('Discipline_with_Level in obt with inferior,'
                ' Potence with inferior, obf with superior',
                Filters.MultiDisciplineLevelFilter([('obt', 'inferior'),
                    ('pot', 'inferior'), ('obf', 'superior')])),
            ('CardType in Equipment', Filters.CardTypeFilter('Equipment')),
            ('CardType in Reflex', Filters.CardTypeFilter('Reflex')),
            ('CardType in Power,Action',
                Filters.MultiCardTypeFilter(['Power', 'Action'])),
            ('Sect in Sabbat', Filters.SectFilter('Sabbat')),
            ('Sect in Sabbat, Independent',
                Filters.MultiSectFilter(['Sabbat', 'Independent'])),
            ('Title in Bishop', Filters.TitleFilter('Bishop')),
            ('Title in "Independent with 1 vote"',
                Filters.TitleFilter('Independent with 1 vote')),
            ('Title in Bishop, Prince',
                Filters.MultiTitleFilter(['Bishop', 'Prince'])),
            ('Title in Magaji, Regent',
                Filters.MultiTitleFilter(['Magaji', 'Regent'])),
            ('Title in Primogen, Priscus, Cardinal',
                Filters.MultiTitleFilter(['Primogen', 'Priscus', 'Cardinal'])),
            ('Creed = Martyr', Filters.CreedFilter('Martyr')),
            ('Creed = Martyr, Innocent',
                Filters.MultiCreedFilter(['Martyr', 'Innocent'])),
            ('Virtue in Redemption', Filters.VirtueFilter('Redemption')),
            ('Virtue in Redemption, jud',
                Filters.MultiVirtueFilter(['Redemption', 'Judgement'])),
            ('Group in 4', Filters.GroupFilter(4)),
            ('Group in 4, 5', Filters.MultiGroupFilter([4, 5])),
            ('Capacity in 2', Filters.MultiCapacityFilter([2])),
            ('Capacity in 2,1', Filters.MultiCapacityFilter([1, 2])),
            ('Cost in 5', Filters.CostFilter(5)),
            ('Cost in 2,5', Filters.MultiCostFilter([2, 5])),
            ('Cost in 0', Filters.CostFilter(0)),
            ('Cost in 0,5', Filters.MultiCostFilter([0, 5])),
            ('Life in 6', Filters.LifeFilter(6)),
            ('Life = 3, 6', Filters.MultiLifeFilter([3, 6])),
            ('CostType in Pool', Filters.CostTypeFilter('pool')),
            ('CostType in Blood', Filters.CostTypeFilter('blood')),
            ('CostType in Pool, Blood',
                    Filters.MultiCostTypeFilter(['blood', 'pool'])),
            ('Artist in "Leif Jones"', Filters.ArtistFilter('Leif Jones')),
            (u'Artist in "William O\'Connor", "N\xe9 N\xe9 Thomas"',
                    Filters.MultiArtistFilter(["William O'Connor",
                        u"N\xe9 N\xe9 Thomas"])),
            ('Keyword in "burn option"', Filters.KeywordFilter('burn option')),

            # Text Entry Filters Filters
            ('CardText in strike', Filters.CardTextFilter('strike')),
            ('CardName in cameron', Filters.CardNameFilter('cameron')),
            (u'CardName = "L\xe1z\xe1r"',
                    Filters.CardNameFilter(u"L\xe1z\xe1r")),

            # Compound Filters
            ('CardType in Equipment AND Cost in 5', Filters.FilterAndBox([
                Filters.CardTypeFilter('Equipment'),
                Filters.CostFilter(5),
                ])),
            ('CardType in Equipment OR CardType in Power',
                    Filters.MultiCardTypeFilter(['Equipment', 'Power'])),
            ('NOT CardType in Equipment, Vampire', Filters.FilterNot(
                Filters.MultiCardTypeFilter(['Equipment', 'Vampire']))),
            ('CardType not in Equipment, Vampire', Filters.FilterNot(
                Filters.MultiCardTypeFilter(['Equipment', 'Vampire']))),
            ('NOT CardType in Equipment AND NOT Cost in 5',
                    Filters.FilterAndBox([
                Filters.FilterNot(Filters.CardTypeFilter('Equipment')),
                Filters.FilterNot(Filters.CostFilter(5)),
                ])),
            ('NOT (CardType in Equipment AND Cost in 5)',
                    Filters.FilterNot(Filters.FilterAndBox([
                Filters.CardTypeFilter('Equipment'),
                Filters.CostFilter(5),
                ]))),
        ]

        # Abstract Card Filtering Tests
        for sFilter, oEquivFilter in aTests:
            oFilter = self._parse_filter(sFilter)
            aNames = self._get_abs_names(oFilter)
            aExpectedNames = self._get_abs_names(oEquivFilter)
            self.assertEqual(aNames, aExpectedNames, "Filter Object %s "
                    "failed. %s != %s." % (oFilter, aNames, aExpectedNames))

        # Test bouncing through filter box code
        for sFilter, oEquivFilter in aTests:
            oAST = self.oFilterParser.apply(sFilter)
            oBoxModel = FilterBox.FilterBoxModel(oAST, 'AbstractCard')
            # Test get_text round-trip
            oFilter = self._parse_filter(oBoxModel.get_text())
            aNames = self._get_abs_names(oFilter)
            aExpectedNames = self._get_abs_names(oEquivFilter)
            self.assertEqual(aNames, aExpectedNames, "Filter Object %s "
                    "failed. %s != %s." % (oFilter, aNames, aExpectedNames))
            # test get_ast + get_values round-trip
            oAST = oBoxModel.get_ast_with_values()
            oFilter = oAST.get_filter()
            aNames = self._get_abs_names(oFilter)
            self.assertEqual(aNames, aExpectedNames, "Filter Object %s "
                    "failed. %s != %s." % (oFilter, aNames, aExpectedNames))

    def test_escape_helpers(self):
        """Test the unescape and escape helpers"""
        aStrings = [
                ('aaaa', 'aaaa'),
                ('"', '\\"'),
                ("'", "\\'"),
                ("\\", "\\\\"),
                ("\\'", "\\\\\\'"),
                ("\\\"", "\\\\\\\""),
                ('"\\', '\\"\\\\'),
                ]

        for sData, sEscaped in aStrings:
            self.assertEqual(sData, unescape(escape(sData)))
            self.assertEqual(escape(sData), sEscaped)

    def test_quoting(self):
        """Check that both single and double quotes work"""
        aTests = [
            ('Clan in "Follower of Set"',
                Filters.ClanFilter('Follower of Set')),
            ('Clan in "Ravnos", "Samedi"',
                Filters.MultiClanFilter(['Ravnos', 'Samedi'])),
            ("Clan in 'Ravnos', 'Samedi'",
                Filters.MultiClanFilter(['Ravnos', 'Samedi'])),
            ("CardName in 'Aaron'", Filters.CardNameFilter('Aaron')),
            ('CardName in "Aaron"', Filters.CardNameFilter('Aaron')),
            ('CardName in "Aaron\'s"', Filters.CardNameFilter("Aaron's")),
            ('CardName in "Aaron\\\'s"', Filters.CardNameFilter("Aaron's")),
            ("CardName in '\\\"Di'", Filters.CardNameFilter('"Di')),
            ("CardName in '\"Di'", Filters.CardNameFilter('"Di')),
            ]
        # Only test on AbstractCards
        for sFilter, oEquivFilter in aTests:
            oFilter = self._parse_filter(sFilter)
            aNames = self._get_abs_names(oFilter)
            aExpectedNames = self._get_abs_names(oEquivFilter)
            self.assertEqual(aNames, aExpectedNames, "Filter Object %s "
                    "failed. %s != %s." % (oFilter, aNames, aExpectedNames))

        # Create some nasty cases for testing escaping
        _oPCS = PhysicalCardSet(name='\\')
        _oPCS = PhysicalCardSet(name='\\\\')
        _oPCS = PhysicalCardSet(name='"')
        _oPCS = PhysicalCardSet(name="'")

        aPhysicalCardSetTests = [
            # test different quote types
            ("CardSetName = '\"'", Filters.CardSetNameFilter('"')),
            ('CardSetName in "\'"', Filters.CardSetNameFilter("'")),
            # Test escaping quotes
            ("CardSetName in '\\\''", Filters.CardSetNameFilter("'")),
            ("CardSetName in '\\\"'", Filters.CardSetNameFilter('"')),
            ('CardSetName in "\\\""', Filters.CardSetNameFilter('"')),
            # Test escaping \
            # raw strings to save on toothpicks
            (r'CardSetName in "\\"', Filters.CardSetNameFilter('\\')),
            (r'CardSetName in "\\\\"', Filters.CardSetNameFilter(r'\\')),
            ]

        for sFilter, oEquivFilter in aPhysicalCardSetTests:
            oFilter = self._parse_filter(sFilter)
            aCardSets = sorted(oFilter.select(PhysicalCardSet).distinct())
            aExpectedSets = sorted(oEquivFilter.select(
                PhysicalCardSet).distinct())
            self.assertEqual(aCardSets, aExpectedSets, "Filter Object %s"
                    " failed. %s != %s." % (oFilter, aCardSets, aExpectedSets))

        # Test bouncing through filter box code
        for sFilter, oEquivFilter in aPhysicalCardSetTests:
            oAST = self.oFilterParser.apply(sFilter)
            oBoxModel = FilterBox.FilterBoxModel(oAST, 'PhysicalCardSet')
            # Test get_text round-trip
            oFilter = self._parse_filter(oBoxModel.get_text())
            aExpectedSets = sorted(oEquivFilter.select(
                PhysicalCardSet).distinct())
            aCardSets = sorted(oFilter.select(PhysicalCardSet).distinct())
            self.assertEqual(aCardSets, aExpectedSets, "Filter Object %s"
                    " failed. %s != %s." % (oFilter, aCardSets, aExpectedSets))
            # test get_ast + get_values round-trip
            oAST = oBoxModel.get_ast_with_values()
            oFilter = oAST.get_filter()
            aCardSets = sorted(oFilter.select(PhysicalCardSet).distinct())
            self.assertEqual(aCardSets, aExpectedSets, "Filter Object %s"
                    " failed. %s != %s." % (oFilter, aCardSets, aExpectedSets))

    def test_card_set_filters(self):
        """Tests for the physical card set filters."""
        aPCSs = make_physical_card_sets()
        # Tests on the physical card set properties
        # Also Filter Expression, eqiv Filter pairs
        aPhysicalCardSetTests = [
                ('CardSetName = "Test 1"',
                    Filters.CardSetNameFilter('Test 1')),
                ('CardSetName = Test', Filters.CardSetNameFilter('Test')),
                ('CSSetsInUse', Filters.CSPhysicalCardSetInUseFilter()),
                ('CardSetAuthor = "Author A"',
                    Filters.CardSetAuthorFilter('Author A')),
                ('CardSetDescription = set',
                    Filters.CardSetDescriptionFilter('set')),
                ('CardSetDescription in different',
                    Filters.CardSetDescriptionFilter('different')),
                ]

        for sFilter, oEquivFilter in aPhysicalCardSetTests:
            oFilter = self._parse_filter(sFilter)
            aCardSets = sorted(oFilter.select(PhysicalCardSet).distinct())
            aExpectedSets = sorted(oEquivFilter.select(
                PhysicalCardSet).distinct())
            self.assertEqual(aCardSets, aExpectedSets, "Filter Object %s"
                    " failed. %s != %s." % (oFilter, aCardSets, aExpectedSets))

        # Test bouncing through filter box code
        for sFilter, oEquivFilter in aPhysicalCardSetTests:
            oAST = self.oFilterParser.apply(sFilter)
            oBoxModel = FilterBox.FilterBoxModel(oAST, 'PhysicalCardSet')
            # Test get_text round-trip
            oFilter = self._parse_filter(oBoxModel.get_text())
            aExpectedSets = sorted(oEquivFilter.select(
                PhysicalCardSet).distinct())
            aCardSets = sorted(oFilter.select(PhysicalCardSet).distinct())
            self.assertEqual(aCardSets, aExpectedSets, "Filter Object %s"
                    " failed. %s != %s." % (oFilter, aCardSets, aExpectedSets))
            # test get_ast + get_values round-trip
            oAST = oBoxModel.get_ast_with_values()
            oFilter = oAST.get_filter()
            aCardSets = sorted(oFilter.select(PhysicalCardSet).distinct())
            self.assertEqual(aCardSets, aExpectedSets, "Filter Object %s"
                    " failed. %s != %s." % (oFilter, aCardSets, aExpectedSets))

        # Test data for the Specific card filters

        aPCSAbsCardTests = [
                (Filters.PhysicalCardSetFilter('Test 1'),
                    'CardType in Vampire', Filters.CardTypeFilter('Vampire')),
                (Filters.PhysicalCardSetFilter('Test 1'),
                    'CardType in Master', Filters.CardTypeFilter('Master')),
                (Filters.PhysicalCardSetFilter('Test 2'),
                    'CardType in Equipment',
                    Filters.CardTypeFilter('Equipment')),
                ]

        for oPCSFilter, sFilter, oEquivFilter in aPCSAbsCardTests:
            oFilter = self._parse_filter(sFilter)
            aExpectedCards = self._get_physical_names(oPCSFilter, oEquivFilter)
            aCSCards = self._get_physical_names(oPCSFilter, oFilter)
            self.assertEqual(aCSCards, aExpectedCards, "Filter %s, %s"
                    " failed. %s != %s." % (oPCSFilter, sFilter, aCSCards,
                        aExpectedCards))

        oInUseFilter = self.oFilterParser.apply(
                'SetsInUse = "Test 1"').get_filter()
        aPCSCardsInUse = list(oInUseFilter.select(PhysicalCard).distinct())
        aExpectedCards = list(aPCSs[2].cards)
        self.assertEqual(aPCSCardsInUse, aExpectedCards, 'PhysicalCardSet In '
                'Use Filter failed %s != %s' % (aPCSCardsInUse,
                    aExpectedCards))

        oInUseFilter = self.oFilterParser.apply('CSSetsInUse').get_filter()
        aCSInUse = list(oInUseFilter.select(PhysicalCardSet).distinct())
        aExpectedSets = [aPCSs[2]]
        self.assertEqual(aCSInUse, aExpectedSets, 'CSPhysicalCardSet In'
                'Use Filter failed %s != %s' % (aCSInUse, aExpectedSets))

        # Number tests
        aPCSNumberTests = [
                (Filters.PhysicalCardSetFilter('Test 1'),
                    'CardCount = 4 from "%s"' % aPCSs[0].name,
                    Filters.CardSetMultiCardCountFilter(('4',
                        [aPCSs[0].name]))),
                (Filters.PhysicalCardSetFilter('Test 1'),
                    'CardCount = 7 from "%s"' % aPCSs[0].name,
                    Filters.CardSetMultiCardCountFilter(('7', aPCSs[0].name))),
                (Filters.PhysicalCardSetFilter('Test 1'),
                    'CardCount in "1" from "%s"' % aPCSs[0].name,
                    Filters.CardSetMultiCardCountFilter(('1', aPCSs[0].name))),
                (Filters.PhysicalCardSetFilter('Test 1'),
                    'CardCount in 1, 4 from "%s"' % aPCSs[0].name,
                    Filters.CardSetMultiCardCountFilter((['1', '4'],
                        aPCSs[0].name))),
                (Filters.PhysicalCardSetFilter('Test 1'),
                    'CardCount in 1, 4 from "%s", "%s"' % (aPCSs[0].name,
                        aPCSs[1].name),
                    Filters.CardSetMultiCardCountFilter((['1', '4'],
                        [aPCSs[0].name, aPCSs[1].name]))),
                (Filters.PhysicalCardSetFilter('Test 1'),
                    'CardCount in 1 from "%s", "%s"' % (aPCSs[0].name,
                        aPCSs[1].name),
                    Filters.CardSetMultiCardCountFilter((['1'],
                        [aPCSs[0].name, aPCSs[1].name]))),
                # Cards in 'Test 2' with zero count in 'Test 1'
                (Filters.PhysicalCardSetFilter('Test 2'),
                    'CardCount = 0 from "%s"' % aPCSs[0].name,
                    Filters.CardSetMultiCardCountFilter(('0', aPCSs[0].name))),
                (Filters.PhysicalCardSetFilter('Test 2'),
                    'CardCount = " 0" from "%s"' % aPCSs[0].name,
                    Filters.CardSetMultiCardCountFilter(('0', aPCSs[0].name))),
                (Filters.PhysicalCardSetFilter('Test 2'),
                    'CardCount = 0 from "%s" and CardType = Vampire' %
                    aPCSs[0].name,
                    Filters.FilterAndBox([
                        Filters.CardSetMultiCardCountFilter(('0',
                            aPCSs[0].name)),
                        Filters.CardTypeFilter('Vampire')])),
                    ]

        for oPCSFilter, sFilter, oEquivFilter in aPCSNumberTests:
            # pylint: disable-msg=E1101
            # pyprotocols confuses pylinta
            oFilter = self._parse_filter(sFilter)
            aExpectedCards = self._get_physical_names(oPCSFilter, oEquivFilter)
            aCSCards = self._get_physical_names(oPCSFilter, oFilter)
            self.assertEqual(aCSCards, aExpectedCards, "Filter %s, %s"
                    " failed. %s != %s." % (oPCSFilter, sFilter, aCSCards,
                        aExpectedCards))

    def test_variables(self):
        """Test parsing filters with variables"""

        aTests = ['CardType = $a', 'CardType in $a', 'Clan in $a']

        for sFilter in aTests:
            oAST = self.oFilterParser.apply(sFilter)
            oFilterPart = oAST.aChildren[0]  # Because they're simple children
            self.assertEqual(oFilterPart.get_name(), '$a')
            self.assertTrue(oFilterPart.aFilterValues is None)

        # Test error case
        self.assertRaises(ValueError, self.oFilterParser.apply,
            'CardType in $a and Clan in $a')
        self.assertRaises(ValueError, self.oFilterParser.apply,
            'CardType not in $a and Clan in $a')
        self.assertRaises(ValueError, self.oFilterParser.apply,
            'CardType in')
        self.assertRaises(ValueError, self.oFilterParser.apply,
            'Vampire in $a')

        oAST = self.oFilterParser.apply('CardType in "Vampire","Action Mod"')
        self.assertEqual(oAST.get_invalid_values(), ["Action Mod"])

    def test_filter_box_missing_values(self):
        """Test that filter box handle missing values as expected"""
        # Test filters that should be treated as empty
        aNullTests = ['CardType = $a', 'CardType in $a']
        for sFilter in aNullTests:
            oAST = self.oFilterParser.apply(sFilter)
            oBoxModel = FilterBox.FilterBoxModel(oAST, 'AbstractCard')
            oAST = oBoxModel.get_ast_with_values()
            self.assertEqual(oAST, None, "Didn't get expected None Filter "
                    "for empty box model")
        # Check partially filled filters
        # The tests a given as "Expression", "Equivilant Filter"
        # where the two filters should give the same results
        aTests = [
            ('Clan in "Follower of Set" and CardType in $a',
                Filters.ClanFilter('Follower of Set')),
            ('Clan in Ravnos, Samedi and Clan in $a',
                Filters.MultiClanFilter(['Ravnos', 'Samedi'])),
            ('Discipline in obf or Discipline in $a',
                Filters.DisciplineFilter('obf')),
            ('Discipline in nec, Quietus or Clan in $a',
                Filters.MultiDisciplineFilter(['nec', 'qui']))]

        for sFilter, oEquivFilter in aTests:
            oAST = self.oFilterParser.apply(sFilter)
            oBoxModel = FilterBox.FilterBoxModel(oAST, 'AbstractCard')
            # Test get_text round-trip
            oFilter = self._parse_filter(oBoxModel.get_text())
            aNames = self._get_abs_names(oFilter)
            aExpectedNames = self._get_abs_names(oEquivFilter)
            self.assertEqual(aNames, aExpectedNames, "Filter Object %s "
                    "failed. %s != %s." % (oFilter, aNames, aExpectedNames))
            # test get_ast + get_values round-trip
            oAST = oBoxModel.get_ast_with_values()
            oFilter = oAST.get_filter()
            aNames = self._get_abs_names(oFilter)
            self.assertEqual(aNames, aExpectedNames, "Filter Object %s "
                    "failed. %s != %s." % (oFilter, aNames, aExpectedNames))

        # Test disabling sections
        # We will always disable the first section in these filters
        aDisableTests = [
            ('Clan in "Assamite" and Clan in "Follower of Set"',
                Filters.ClanFilter('Follower of Set')),
            ('Clan in "Assamite" and Clan in Ravnos, Samedi',
                Filters.MultiClanFilter(['Ravnos', 'Samedi'])),
            ('Clan in "Assamite" and Discipline in obf',
                Filters.DisciplineFilter('obf')),
            ('Discipline in obf or Discipline in nec, Quietus',
                Filters.MultiDisciplineFilter(['nec', 'qui']))]

        for sFilter, oEquivFilter in aDisableTests:
            oAST = self.oFilterParser.apply(sFilter)
            aExpectedNames = self._get_abs_names(oEquivFilter)
            oBoxModel = FilterBox.FilterBoxModel(oAST, 'AbstractCard')
            oBoxModel[0].bDisabled = True
            # test get_ast_with_values round-trip
            oAST = oBoxModel.get_ast_with_values()
            oFilter = oAST.get_filter()
            aNames = self._get_abs_names(oFilter)
            self.assertEqual(aNames, aExpectedNames, "Filter Object %s "
                    "failed. %s != %s." % (oFilter, aNames, aExpectedNames))


if __name__ == "__main__":
    unittest.main()
