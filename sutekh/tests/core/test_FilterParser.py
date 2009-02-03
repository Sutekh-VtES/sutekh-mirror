# test_FilterParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007, 2008 Simon Cross <hodgestar@gmail.com>,
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Tests the Filter Parser code"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.io import test_WhiteWolfParser
from sutekh.core.SutekhObjects import AbstractCard, PhysicalCardSet, \
        PhysicalCard, MapPhysicalCardToPhysicalCardSet, IAbstractCard, \
        IPhysicalCard, IExpansion
from sutekh.core import FilterParser, Filters
import unittest

class FilterParserTests(SutekhTest):
    """Class for the test cases"""
    aExpectedCards = test_WhiteWolfParser.WhiteWolfParserTests.aExpectedCards
    oFilterParser = FilterParser.FilterParser()

    # pylint: disable-msg=R0914
    # We don't really care about the number of local variables here
    def test_basic(self):
        """Set of simple tests of the filter parser."""
        # setup filters
        aTests = [
            # Single & Multiple value tests
            ('Clan in "Follower of Set"', [u"Aabbt Kindred", u"Abdelsobek",
                u"Amisa", u"Kemintiri (Advanced)"]),
            ('Clan in Ravnos, Samedi', [u"Abebe", u"L\xe1z\xe1r Dobrescu"]),
            ('Discipline in obf', [u"Aaron Bathurst", u"Abd al-Rashid",
                u"Abdelsobek", u"Abebe", u"Aeron", u"Amisa",
                u"Angelica, The Canonicus", u"Cedric", u"Kabede Maru",
                u"Kemintiri (Advanced)", u"Sha-Ennu"]),
            ('Discipline in fli', [u"Cedric"]),
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
                    u"Aeron", u"Akram", u"Amisa", u"Bronwen", u"Cedric",
                    u"Kabede Maru", u"Kemintiri (Advanced)"]),
            ('CardType in Equipment', [u".44 Magnum", u"AK-47",
                u"Aaron's Feeding Razor"]),
            ('CardType in Reflex', [u"Predator's Communion"]),
            ('CardType in Power,Action', [u"Abbot", u"Abjure",
                u"Ablative Skin"]),
            ('Sect in Sabbat', [u"Aaron Bathurst",
                u"Aaron Duggan, Cameron's Toady", u"Aeron", u"Alfred Benezri",
                u"Angelica, The Canonicus", u"Bronwen", u"Sha-Ennu"]),
            ('Sect in Sabbat, Independent', [u"Aabbt Kindred",
                u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady",
                u"Abd al-Rashid", u"Abdelsobek", u"Abebe",
                u"Aeron", u"Alfred Benezri", u"Ambrogino Giovanni", u"Amisa",
                u"Angelica, The Canonicus", u"Bronwen",
                u"Kemintiri (Advanced)", u"L\xe1z\xe1r Dobrescu",
                u"Sha-Ennu"]),
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
                u'Anna "Dictatrix11" Suljic', u"Cedric", u"Cesewayo",
                u'Earl "Shaka74" Deams', u'Inez "Nurse216" Villagrande',
                u"Sha-Ennu"]),
            ('Group in 4, 5', [u"Aaron Bathurst", u"Abdelsobek", u"Abebe",
                u'Anna "Dictatrix11" Suljic', u"Cedric", u"Cesewayo",
                u'Earl "Shaka74" Deams', u'Inez "Nurse216" Villagrande',
                u"Kabede Maru", u"Sha-Ennu"]),
            ('Capacity in 2', [u"Aaron Duggan, Cameron's Toady"]),
            ('Capacity in 2,1', [u"Aaron Duggan, Cameron's Toady",
                u"Abombwe"]),
            ('Cost in 5', [u"AK-47"]),
            ('Cost in 2,5', [u".44 Magnum", u"AK-47"]),
            ('Cost in 0', [u'Aabbt Kindred', u'Aaron Bathurst',
                u"Aaron Duggan, Cameron's Toady", u'Abandoning the Flesh',
                u'Abbot', u'Abd al-Rashid', u'Abdelsobek', u'Abebe',
                u'Abjure', u'Ablative Skin', u'Abombwe', u'Aeron', u'Akram',
                u'Alan Sovereign', u'Alan Sovereign (Advanced)', u'Alexandra',
                u'Alfred Benezri', u'Ambrogino Giovanni', u'Amisa',
                u'Anastasz di Zagreb', u'Angelica, The Canonicus',
                u'Anna "Dictatrix11" Suljic', u'Anson', u'Bronwen',
                u'Cedric', u'Cesewayo', u'Earl "Shaka74" Deams',
                u'Gracis Nostinus', u'Inez "Nurse216" Villagrande',
                u'Kabede Maru', u'Kemintiri (Advanced)',
                u'L\xe1z\xe1r Dobrescu', u"Predator's Communion", u'Sha-Ennu',
                u'Yvette, The Hopeless']),
            ('Cost in 0,5', [u"AK-47", u'Aabbt Kindred', u'Aaron Bathurst',
                u"Aaron Duggan, Cameron's Toady", u'Abandoning the Flesh',
                u'Abbot', u'Abd al-Rashid', u'Abdelsobek', u'Abebe',
                u'Abjure', u'Ablative Skin', u'Abombwe', u'Aeron', u'Akram',
                u'Alan Sovereign', u'Alan Sovereign (Advanced)', u'Alexandra',
                u'Alfred Benezri', u'Ambrogino Giovanni', u'Amisa',
                u'Anastasz di Zagreb', u'Angelica, The Canonicus',
                u'Anna "Dictatrix11" Suljic', u'Anson', u'Bronwen',
                u'Cedric', u'Cesewayo', u'Earl "Shaka74" Deams',
                u'Gracis Nostinus', u'Inez "Nurse216" Villagrande',
                u'Kabede Maru', u'Kemintiri (Advanced)',
                u'L\xe1z\xe1r Dobrescu', u"Predator's Communion", u'Sha-Ennu',
                u'Yvette, The Hopeless']),
            ('Life in 6', [u'Anna "Dictatrix11" Suljic',
                u'Earl "Shaka74" Deams']),
            ('Life in 3, 6', [u'Anna "Dictatrix11" Suljic',
                u'Earl "Shaka74" Deams', u'Inez "Nurse216" Villagrande']),
            ('CostType in Pool', [u".44 Magnum", u"AK-47",
                u"Aaron's Feeding Razor", u"The Path of Blood"]),
            ('CostType in Blood', [u"Aire of Elation"]),
            ('CostType in Pool, Blood', [u".44 Magnum", u"AK-47",
                u"Aaron's Feeding Razor", u"Aire of Elation",
                u"The Path of Blood"]),
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
                        u"Ablative Skin", u"Abombwe", u"Aire of Elation",
                        u'Anna "Dictatrix11" Suljic', u'Earl "Shaka74" Deams',
                        u'Inez "Nurse216" Villagrande',
                        u"Predator's Communion", u"The Path of Blood"]),
            ('CardType not in Equipment, Vampire',
                    [u"Abandoning the Flesh", u"Abbot", u"Abjure",
                        u"Ablative Skin", u"Abombwe", u"Aire of Elation",
                        u'Anna "Dictatrix11" Suljic', u'Earl "Shaka74" Deams',
                        u'Inez "Nurse216" Villagrande',
                        u"Predator's Communion", u"The Path of Blood"]),
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

    def test_card_set_filters(self):
        """Tests for the physical card set filters."""
        # Although splitting this off does add an additional init
        # pass, the logical grouping is fairly different
        aCardSets = [('Test 1', 'Author A', 'A set', False),
                ('Test 2', 'Author B', 'Another set', False),
                ('Test 3', 'Author A', 'Something different', True)]
        aPCSCards = [
                # Set 1
                [('Abombwe', None), ('Alexandra', 'CE'),
                ('Sha-Ennu', None), ('Sha-Ennu', None), ('Sha-Ennu', None),
                ('Sha-Ennu', 'Third Edition')],
                # Set 2
                [('Sha-Ennu', 'Third Edition'), ('Anson', 'Jyhad'),
                    ('.44 magnum', 'Jyhad'), ('ak-47', 'LotN'),
                    ('Alexandra', 'CE'), ('Alexandra', 'CE')],
                # Set 3
                [('Yvette, The Hopeless', 'BSC')]]
        aPCSs = []
        # pylint: disable-msg=E1101
        # sqlobject confuses pylint
        for iCnt, tData in enumerate(aCardSets):
            sName, sAuthor, sComment, bInUse = tData
            oPCS = PhysicalCardSet(name=sName, comment=sComment,
                    author=sAuthor, inuse=bInUse)
            for sName, sExp in aPCSCards[iCnt]:
                if sExp:
                    oExp = IExpansion(sExp)
                else:
                    oExp = None
                oAbs = IAbstractCard(sName)
                oPhys = IPhysicalCard((oAbs, oExp))
                oPCS.addPhysicalCard(oPhys.id)
            aPCSs.append(oPCS)
        # Tests on the physical card set properties
        aPhysicalCardSetTests = [
                ('CardSetName = "Test 1"', [aPCSs[0]]),
                ('CardSetName = Test', sorted(aPCSs)),
                ('CSSetsInUse', [aPCSs[2]]),
                ('CardSetAuthor = "Author A"',
                    sorted([aPCSs[0], aPCSs[2]])),
                ('CardSetDescription = set',
                    sorted([aPCSs[0], aPCSs[1]])),
                ('CardSetDescription in different',
                    [aPCSs[2]]),
                ]

        for sFilter, aExpectedSets in aPhysicalCardSetTests:
            oAST = self.oFilterParser.apply(sFilter)
            oFilter = oAST.get_filter()
            aCardSets = sorted(oFilter.select(PhysicalCardSet).distinct())
            self.assertEqual(aCardSets, aExpectedSets, "Filter Object %s"
                    " failed. %s != %s." % (oFilter, aCardSets, aExpectedSets))

        # Test data for the Specific card filters

        aPCSAbsCardTests = [
                (Filters.PhysicalCardSetFilter('Test 1'),
                    'CardType in Vampire',
                    [u"Alexandra", u"Sha-Ennu", u"Sha-Ennu", u"Sha-Ennu",
                        u"Sha-Ennu"]),
                (Filters.PhysicalCardSetFilter('Test 1'),
                    'CardType in Master',
                    [u"Abombwe"]),
                (Filters.PhysicalCardSetFilter('Test 2'),
                    'CardType in Equipment',
                    [u".44 Magnum", u"AK-47"]),
                ]

        for oPCSFilter, sFilter, aExpectedCards in aPCSAbsCardTests:
            oAST = self.oFilterParser.apply(sFilter)
            oFilter = oAST.get_filter()
            oFullFilter = Filters.FilterAndBox([oPCSFilter, oFilter])
            aCSCards = [IAbstractCard(x).name for x in oFullFilter.select(
                        MapPhysicalCardToPhysicalCardSet).distinct()]
            self.assertEqual(aCSCards, aExpectedCards, "Filter Object %s"
                    " failed. %s != %s." % (oFullFilter, aCSCards,
                        aExpectedCards))

        oInUseFilter = self.oFilterParser.apply('SetsInUse').get_filter()
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
                    [u"Sha-Ennu", u"Sha-Ennu", u"Sha-Ennu", u"Sha-Ennu"]),
                (Filters.PhysicalCardSetFilter('Test 1'),
                    'CardCount = 7 from "%s"' % aPCSs[0].name,
                    []),
                (Filters.PhysicalCardSetFilter('Test 1'),
                    'CardCount in "1" from "%s"' % aPCSs[0].name,
                    [u"Abombwe", u"Alexandra"]),
                (Filters.PhysicalCardSetFilter('Test 1'),
                    'CardCount in 1, 4 from "%s"' % aPCSs[0].name,
                    [u"Abombwe", u"Alexandra", u"Sha-Ennu", u"Sha-Ennu",
                        u"Sha-Ennu", u"Sha-Ennu"]),
                # Cards in 'Test 2' with zero count in 'Test 1'
                (Filters.PhysicalCardSetFilter('Test 2'),
                    'CardCount = 0 from "%s"' % aPCSs[0].name,
                    [u"Anson", u".44 Magnum", u"AK-47"]),
                (Filters.PhysicalCardSetFilter('Test 2'),
                    'CardCount = 0 from "%s" and CardType = Vampire' %
                    aPCSs[0].name,
                    [u"Anson"]),
                    ]

        for oPCSFilter, sFilter, aExpectedCards in aPCSNumberTests:
            # pylint: disable-msg=E1101
            # pyprotocols confuses pylinta
            oAST = self.oFilterParser.apply(sFilter)
            oFilter = oAST.get_filter()
            oFullFilter = Filters.FilterAndBox([oPCSFilter, oFilter])
            aCSCards = [IAbstractCard(x).name for x in oFullFilter.select(
                        MapPhysicalCardToPhysicalCardSet).distinct()]
            self.assertEqual(aCSCards, aExpectedCards, "Filter Object %s"
                    " failed. %s != %s." % (oFullFilter, aCSCards,
                        aExpectedCards))

    def test_variables(self):
        """Test parsing filters with variables"""

        aTests = ['CardType = $a', 'CardType in $a', 'Clan in $a']

        for sFilter in aTests:
            oAST = self.oFilterParser.apply(sFilter)
            oFilterPart = oAST.aChildren[0] # Because they're simple children
            self.assertEqual(oFilterPart.get_name(), '$a')
            self.assertTrue(oFilterPart.aFilterValues is None)

        # Test error case
        self.assertRaises(ValueError, self.oFilterParser.apply,
            'CardType in $a and Clan in $a')
        self.assertRaises(ValueError, self.oFilterParser.apply,
            'CardType in')
        self.assertRaises(ValueError, self.oFilterParser.apply,
            'Vampire in $a')

        oAST = self.oFilterParser.apply('CardType in "Vampire","Action Mod"')
        self.assertEqual(oAST.get_invalid_values(), ["Action Mod"])


if __name__ == "__main__":
    unittest.main()
