# test_Filters.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Sutekh Filters tests"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.io import test_WhiteWolfParser
from sutekh.core.SutekhObjects import AbstractCard, IAbstractCard, \
        PhysicalCard, IPhysicalCard, Expansion, IExpansion, PhysicalCardSet, \
        MapPhysicalCardToPhysicalCardSet
from sutekh.core import Filters
from sqlobject import SQLObjectNotFound
from sutekh.core.CardLookup import best_guess_filter
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

    def _convert_to_phys_cards(self, aList):
        """Converts a list of Name, Expansion Name tuples into physical
           cards"""
        aPhysCards = []
        for sName, sExp in aList:
            try:
                if sExp:
                    oExp = IExpansion(sExp)
                else:
                    oExp = None
                oAbs = IAbstractCard(sName)
                oCard = IPhysicalCard((oAbs, oExp))
                aPhysCards.append(oCard)
            except SQLObjectNotFound:
                self.fail("Invalid physical card (%s from expansion %s)"
                        % (sName, sExp))
        return sorted(aPhysCards)

    # pylint: disable-msg=R0914
    # We don't really care about the number of local variables here
    def test_basic(self):
        """Simple tests of the filter"""
        # setup filters
        aTests = [
            # Single / Multi Filters
            (Filters.ClanFilter('Follower of Set'), [u"Aabbt Kindred",
                u"Abdelsobek", u"Amisa", u"Kemintiri (Advanced)"]),
            (Filters.MultiClanFilter(['Ravnos', 'Samedi']), [u"Abebe",
                u"L\xe1z\xe1r Dobrescu"]),
            (Filters.DisciplineFilter('obf'), [u"Aaron Bathurst",
                u"Abd al-Rashid", u"Abdelsobek", u"Abebe", u"Aeron", u"Amisa",
                u"Angelica, The Canonicus", u"Cedric", u"Kabede Maru",
                u"Kemintiri (Advanced)", u"Sha-Ennu"]),
            (Filters.DisciplineFilter('fli'), [u"Cedric"]),
            (Filters.MultiDisciplineFilter(['nec', 'qui']), [u"Abd al-Rashid",
                u"Abdelsobek", u"Abebe", u"Akram", u"Ambrogino Giovanni",
                u"Kabede Maru"]),
            (Filters.ExpansionFilter('NoR'), [u"Abjure",
                u'Anna "Dictatrix11" Suljic', u'Earl "Shaka74" Deams',
                u'Inez "Nurse216" Villagrande']),
            (Filters.MultiExpansionFilter(['NoR', 'LoB']), [u".44 Magnum",
                u"Abebe", u"Abjure", u"Abombwe",
                u'Anna "Dictatrix11" Suljic', u"Cedric", u"Cesewayo",
                u'Earl "Shaka74" Deams', u'Inez "Nurse216" Villagrande',
                u"Predator's Communion"]),
            (Filters.ExpansionRarityFilter(('Sabbat', 'Rare')),
                [u"Ablative Skin"]),
            (Filters.ExpansionRarityFilter(('Blood Shadowed Court',
                'BSC')), [u"Alan Sovereign", u"Alfred Benezri",
                    u"Anastasz di Zagreb", u"Gracis Nostinus",
                    u"Yvette, The Hopeless"]),
            (Filters.MultiExpansionRarityFilter([('Third', 'Uncommon'),
                ('Jyhad', 'Rare')]), [u"Aaron's Feeding Razor", u"Abbot"]),
            (Filters.DisciplineLevelFilter(('cel', 'superior')),
                [u"Abd al-Rashid", u"Akram", u"Alexandra", u"Anson",
                    u"Bronwen", u"Cesewayo", u"Kabede Maru"]),
            (Filters.MultiDisciplineLevelFilter([('obt', 'inferior'),
                ('pot', 'inferior'), ('obf', 'superior')]),
                [u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady",
                    u"Aeron", u"Akram", u"Amisa", u"Bronwen", u"Cedric",
                    u"Kabede Maru", "Kemintiri (Advanced)"]),
            (Filters.MultiDisciplineLevelFilter(['obt with inferior',
                'pot with inferior', 'obf with superior']),
                [u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady",
                    u"Aeron", u"Akram", u"Amisa", u"Bronwen", u"Cedric",
                    u"Kabede Maru", u"Kemintiri (Advanced)"]),
            (Filters.CardTypeFilter('Equipment'), [u".44 Magnum", u"AK-47",
                u"Aaron's Feeding Razor"]),
            (Filters.CardTypeFilter('Reflex'), [u"Predator's Communion"]),
            (Filters.MultiCardTypeFilter(['Power', 'Action']), [u"Abbot",
                u"Abjure", u"Ablative Skin"]),
            (Filters.SectFilter('Sabbat'), [u"Aaron Bathurst",
                u"Aaron Duggan, Cameron's Toady", u"Aeron", u"Alfred Benezri",
                u"Angelica, The Canonicus", u"Bronwen", u"Sha-Ennu"]),
            (Filters.MultiSectFilter(['Sabbat', 'Independent']),
                [u"Aabbt Kindred",
                u"Aaron Bathurst", u"Aaron Duggan, Cameron's Toady",
                u"Abd al-Rashid", u"Abdelsobek", u"Abebe",
                u"Aeron", u"Alfred Benezri", u"Ambrogino Giovanni", u"Amisa",
                u"Angelica, The Canonicus", u"Bronwen",
                u"Kemintiri (Advanced)", u"L\xe1z\xe1r Dobrescu",
                u"Sha-Ennu"]),
            (Filters.TitleFilter('Bishop'), [u"Alfred Benezri"]),
            (Filters.TitleFilter('Independent with 1 vote'),
                [u"Ambrogino Giovanni"]),
            (Filters.MultiTitleFilter(['Bishop', 'Prince']),
                    [u"Alfred Benezri", u"Anson"]),
            (Filters.MultiTitleFilter(['Magaji', 'Regent']),
                    [u"Cesewayo", u"Kabede Maru", u"Sha-Ennu"]),
            (Filters.MultiTitleFilter(['Primogen', 'Priscus', 'Cardinal']),
                    [u"Akram", u"Angelica, The Canonicus", u"Bronwen"]),
            (Filters.CreedFilter('Martyr'),
                    [u'Anna "Dictatrix11" Suljic']),
            (Filters.MultiCreedFilter(['Martyr', 'Innocent']),
                    [u'Anna "Dictatrix11" Suljic',
                        u'Inez "Nurse216" Villagrande']),
            (Filters.VirtueFilter('Redemption'), [u"Abjure",
                u'Anna "Dictatrix11" Suljic']),
            #(Filters.MultiVirtueFilter(['Redemption', 'Judgement']),
            #    [u"Abjure"]),
            (Filters.GroupFilter(4), [u"Aaron Bathurst", u"Abebe",
                u'Anna "Dictatrix11" Suljic', u"Cedric", u"Cesewayo",
                u'Earl "Shaka74" Deams', u'Inez "Nurse216" Villagrande',
                u"Sha-Ennu"]),
            (Filters.MultiGroupFilter([4, 5]), [u"Aaron Bathurst",
                u"Abdelsobek", u"Abebe", u'Anna "Dictatrix11" Suljic',
                u"Cedric", u"Cesewayo", u'Earl "Shaka74" Deams',
                u'Inez "Nurse216" Villagrande', u"Kabede Maru", u"Sha-Ennu"]),
            (Filters.CapacityFilter(2), [u"Aaron Duggan, Cameron's Toady"]),
            (Filters.MultiCapacityFilter([2, 1]),
                [u"Aaron Duggan, Cameron's Toady", u"Abombwe"]),
            (Filters.CostFilter(5), [u"AK-47"]),
            (Filters.MultiCostFilter([2, 5]), [u".44 Magnum", u"AK-47"]),
            (Filters.MultiCostFilter([0]), [u'Aabbt Kindred',
                u'Aaron Bathurst', u"Aaron Duggan, Cameron's Toady",
                u'Abandoning the Flesh', u'Abbot', u'Abd al-Rashid',
                u'Abdelsobek', u'Abebe', u'Abjure', u'Ablative Skin',
                u'Abombwe', u'Aeron', u'Akram', u'Alan Sovereign',
                u'Alan Sovereign (Advanced)', u'Alexandra', u'Alfred Benezri',
                u'Ambrogino Giovanni', u'Amisa', u'Anastasz di Zagreb',
                u'Angelica, The Canonicus', u'Anna "Dictatrix11" Suljic',
                u'Anson', u'Bronwen', u'Cedric', u'Cesewayo',
                u'Earl "Shaka74" Deams', u'Gracis Nostinus',
                u'Inez "Nurse216" Villagrande', u'Kabede Maru',
                u'Kemintiri (Advanced)', u'L\xe1z\xe1r Dobrescu',
                u"Predator's Communion", u'Sha-Ennu',
                u'Yvette, The Hopeless']),
            (Filters.MultiCostFilter([0, 5]), [u"AK-47", u'Aabbt Kindred',
                u'Aaron Bathurst', u"Aaron Duggan, Cameron's Toady",
                u'Abandoning the Flesh', u'Abbot', u'Abd al-Rashid',
                u'Abdelsobek', u'Abebe', u'Abjure', u'Ablative Skin',
                u'Abombwe', u'Aeron', u'Akram', u'Alan Sovereign',
                u'Alan Sovereign (Advanced)', u'Alexandra', u'Alfred Benezri',
                u'Ambrogino Giovanni', u'Amisa', u'Anastasz di Zagreb',
                u'Angelica, The Canonicus', u'Anna "Dictatrix11" Suljic',
                u'Anson', u'Bronwen', u'Cedric', u'Cesewayo',
                u'Earl "Shaka74" Deams', u'Gracis Nostinus',
                u'Inez "Nurse216" Villagrande', u'Kabede Maru',
                u'Kemintiri (Advanced)', u'L\xe1z\xe1r Dobrescu',
                u"Predator's Communion", u'Sha-Ennu',
                u'Yvette, The Hopeless']),
            (Filters.LifeFilter(6), [u'Anna "Dictatrix11" Suljic',
                u'Earl "Shaka74" Deams']),
            (Filters.MultiLifeFilter([3, 6]), [u'Anna "Dictatrix11" Suljic',
                u'Earl "Shaka74" Deams', u'Inez "Nurse216" Villagrande']),
            (Filters.CostTypeFilter('Pool'), [u".44 Magnum", u"AK-47",
                u"Aaron's Feeding Razor", u"The Path of Blood"]),
            (Filters.CostTypeFilter('Blood'), [u"Aire of Elation"]),
            (Filters.MultiCostTypeFilter(['Pool', 'Blood']), [u".44 Magnum",
                u"AK-47", u"Aaron's Feeding Razor", u"Aire of Elation",
                U"The Path of Blood"]),
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
                    u"Ablative Skin", u"Abombwe", u"Aire of Elation",
                    u'Anna "Dictatrix11" Suljic', u'Earl "Shaka74" Deams',
                    u'Inez "Nurse216" Villagrande', u"Predator's Communion",
                    u"The Path of Blood"]),
        ]

        aPhysicalTests = [self._physical_test(tTest) for tTest in aTests]

        # Abstract Card Filtering Tests
        for oFilter, aExpectedNames in aTests:
            aCards = oFilter.select(AbstractCard).distinct()
            aNames = sorted([oC.name for oC in aCards])
            self.assertEqual(aNames, aExpectedNames, "Filter Object %s"
                    " failed. %s != %s." % (oFilter, aNames, aExpectedNames))

        # Filter values Tests
        self.assertEqual(Filters.MultiClanFilter.get_values(), [u"Assamite",
            u"Brujah", u"Brujah antitribu", u"Follower of Set", u"Gargoyle",
            u"Giovanni", u"Lasombra", u"Nosferatu antitribu", u"Osebo",
            u"Pander", u"Ravnos", u"Samedi", u"Toreador", u"Tremere",
            u"Tzimisce", u"Ventrue"])
        self.assertEqual(Filters.MultiDisciplineFilter.get_values(),
                [u"Abombwe", u"Animalism", u"Auspex", u"Celerity",
                    u"Chimerstry", u"Dementation", u"Dominate", u"Flight",
                    u"Fortitude", u"Necromancy", u"Obfuscate",
                    u"Obtenebration", u"Potence", u"Presence",
                    u"Protean", u"Quietus", u"Serpentis", u"Thaumaturgy",
                    u"Thanatosis", u"Vicissitude", u"Visceratika"])
        self.assertEqual(Filters.MultiCardTypeFilter.get_values(), [u"Action",
            u"Action Modifier", u"Combat", u"Equipment", u"Imbued", u"Master",
            u"Power", u"Reaction", u"Reflex", u"Vampire"])
        self.assertEqual(Filters.MultiTitleFilter.get_values(),
                [u"Archbishop", u"Bishop", u"Cardinal",
                    u"Independent with 1 vote", u"Independent with 2 votes",
                    u"Inner Circle", u"Justicar", u"Magaji", u"Primogen",
                    u"Prince", u"Priscus", u"Regent"])
        self.assertEqual(Filters.MultiCreedFilter.get_values(),
                [u"Innocent", u"Martyr", u"Visionary"])
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
                    ['Abombwe','.44 Magnum', 'Abebe', u"Cedric", u"Cesewayo",
                        u"Predator's Communion"], ['LoB']),
                (Filters.PhysicalExpansionFilter(None),
                    self.aExpectedCards,
                    [None]),
                (Filters.MultiPhysicalExpansionFilter(['LoB', 'LotN']),
                    ['Abombwe','.44 Magnum', 'Abebe', 'AK-47', 'Abdelsobek',
                        u"Cedric", u"Cesewayo", u"Kabede Maru",
                        u"Predator's Communion", u"The Path of Blood"],
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
                (Filters.CardSetNameFilter('Test 1'), [aPCSs[0]]),
                (Filters.CardSetNameFilter('Test'), sorted(aPCSs)),
                (Filters.CSPhysicalCardSetInUseFilter(), [aPCSs[2]]),
                (Filters.CardSetAuthorFilter('Author A'),
                    sorted([aPCSs[0], aPCSs[2]])),
                (Filters.CardSetDescriptionFilter('set'),
                    sorted([aPCSs[0], aPCSs[1]])),
                (Filters.CardSetDescriptionFilter('different'),
                    [aPCSs[2]]),
                ]

        for oFilter, aExpectedSets in aPhysicalCardSetTests:
            aCardSets = sorted(oFilter.select(PhysicalCardSet).distinct())
            self.assertEqual(aCardSets, aExpectedSets, "Filter Object %s"
                    " failed. %s != %s." % (oFilter, aCardSets, aExpectedSets))

        # Test data for the Specific card filters
        oAbsAK = IAbstractCard('ak-47')
        oExp = IExpansion('LotN')
        oPhysAK = IPhysicalCard((oAbsAK, oExp))

        aPCSAbsCardTests = [
                (Filters.PhysicalCardSetFilter('Test 1'),
                    Filters.CardTypeFilter('Vampire'),
                    [u"Alexandra", u"Sha-Ennu", u"Sha-Ennu", u"Sha-Ennu",
                        u"Sha-Ennu"]),
                (Filters.PhysicalCardSetFilter('Test 1'),
                    Filters.CardTypeFilter('Master'),
                    [u"Abombwe"]),
                (Filters.PhysicalCardSetFilter('Test 2'),
                    Filters.CardTypeFilter('Equipment'),
                    [u".44 Magnum", u"AK-47"]),
                (Filters.PhysicalCardSetFilter('Test 2'),
                    Filters.SpecificCardFilter('AK-47'),
                    [u"AK-47"]),
                (Filters.PhysicalCardSetFilter('Test 2'),
                    Filters.SpecificCardIdFilter(oAbsAK.id),
                    [u"AK-47"]),
                (Filters.PhysicalCardSetFilter('Test 2'),
                    Filters.SpecificPhysCardIdFilter(oPhysAK.id),
                    [u"AK-47"]),
                (Filters.PhysicalCardSetFilter('Test 3'),
                    Filters.SpecificPhysCardIdFilter(oPhysAK.id),
                    []),
                ]

        for oPCSFilter, oFilter, aExpectedCards in aPCSAbsCardTests:
            oFullFilter = Filters.FilterAndBox([oPCSFilter, oFilter])
            self.assertTrue('PhysicalCard' in oFullFilter.types)
            aCSCards = [IAbstractCard(x).name for x in oFullFilter.select(
                        MapPhysicalCardToPhysicalCardSet).distinct()]
            self.assertEqual(aCSCards, aExpectedCards, "Filter Object %s"
                    " failed. %s != %s." % (oFullFilter, aCSCards,
                        aExpectedCards))

        aPCSPhysCardTests = [
                (Filters.PhysicalCardSetFilter('Test 1'),
                    Filters.CardTypeFilter('Vampire'),
                    [('Alexandra', 'CE'), ('Sha-Ennu', None),
                        ('Sha-Ennu', None), ('Sha-Ennu', None),
                        ('Sha-Ennu', 'Third Edition')]),
                (Filters.PhysicalCardSetFilter('Test 2'),
                    Filters.SpecificCardFilter('AK-47'),
                    [('AK-47', 'LotN')]),
                (Filters.PhysicalCardSetFilter('Test 3'),
                    Filters.SpecificPhysCardIdFilter(oPhysAK.id),
                    []),
                ]

        for oPCSFilter, oFilter, aExpectedCards in aPCSPhysCardTests:
            oFullFilter = Filters.FilterAndBox([oPCSFilter, oFilter])
            self.assertTrue('PhysicalCard' in oFullFilter.types)
            aCSCards = sorted([IPhysicalCard(x) for x in oFullFilter.select(
                        MapPhysicalCardToPhysicalCardSet).distinct()])
            aExpectedPhysCards = self._convert_to_phys_cards(aExpectedCards)
            self.assertEqual(aCSCards, aExpectedPhysCards, "Filter Object %s"
                    " failed. %s != %s." % (oFullFilter, aCSCards,
                        aExpectedPhysCards))


        aPCSCardsInUse = list(Filters.PhysicalCardSetInUseFilter().select(
                PhysicalCard).distinct())
        aExpectedCards = list(aPCSs[2].cards)
        self.assertEqual(aPCSCardsInUse, aExpectedCards, 'PhysicalCardSet In '
                'Use Filter failed %s != %s' % (aPCSCardsInUse,
                    aExpectedCards))

        # Number tests
        aPCSNumberTests = [
                (Filters.PhysicalCardSetFilter('Test 1'),
                    Filters.CardSetMultiCardCountFilter(('4', aPCSs[0].name)),
                    [u"Sha-Ennu", u"Sha-Ennu", u"Sha-Ennu", u"Sha-Ennu"]),
                (Filters.PhysicalCardSetFilter('Test 1'),
                    Filters.CardSetMultiCardCountFilter(('7', aPCSs[0].name)),
                    []),
                (Filters.PhysicalCardSetFilter('Test 1'),
                    Filters.CardSetMultiCardCountFilter(('1', aPCSs[0].name)),
                    [u"Abombwe", u"Alexandra"]),
                (Filters.PhysicalCardSetFilter('Test 1'),
                    Filters.CardSetMultiCardCountFilter((['1', '4'],
                        aPCSs[0].name)),
                    [u"Abombwe", u"Alexandra", u"Sha-Ennu", u"Sha-Ennu",
                        u"Sha-Ennu", u"Sha-Ennu"]),
                # Cards in 'Test 2' with zero count in 'Test 1'
                (Filters.PhysicalCardSetFilter('Test 2'),
                    Filters.CardSetMultiCardCountFilter(('0', aPCSs[0].name)),
                    [u"Anson", u".44 Magnum", u"AK-47"]),
                    ]

        for oPCSFilter, oFilter, aExpectedCards in aPCSNumberTests:
            # pylint: disable-msg=E1101
            # pyprotocols confuses pylint
            oFullFilter = Filters.FilterAndBox([oPCSFilter, oFilter])
            aCSCards = [IAbstractCard(x).name for x in oFullFilter.select(
                        MapPhysicalCardToPhysicalCardSet).distinct()]
            self.assertEqual(aCSCards, aExpectedCards, "Filter Object %s"
                    " failed. %s != %s." % (oFullFilter, aCSCards,
                        aExpectedCards))

    def test_best_guess_filter(self):
        """Test the best guess filter"""
        # This seems the best fit, to include it with the other filter tests
        aTests = [('Sha-Ennu', [u'Sha-Ennu']),
                ('She-Ennu', [u'Sha-Ennu']),
                ('Saa-Ennu', [u'Sha-Ennu']),
                ('47', [u'AK-47']),
                ('4', [u'.44 Magnum', u'AK-47', u'Earl "Shaka74" Deams']),
                ('Alex', [u'Alexandra']),
                ('Raven', []),
                ('Path of Blood, The', [u'The Path of Blood']),
                ]
        for sGuess, aExpectedNames in aTests:
            oFilter = best_guess_filter(sGuess)
            aNames = [x.name for x in oFilter.select(AbstractCard)]
            self.assertEqual(aNames, aExpectedNames,
                    '%s != expected %s for guess %s' % (aNames, aExpectedNames,
                        sGuess))

if __name__ == "__main__":
    unittest.main()
