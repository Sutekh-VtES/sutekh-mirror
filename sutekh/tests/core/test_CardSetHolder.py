# test_CardSetHolder.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test cases for the CardSetHolder functions, and some CardLookup stuff"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.core.CardSetHolder import CardSetHolder, CachedCardSetHolder
from sutekh.core.SutekhObjects import IPhysicalCardSet, IExpansion, \
        MapPhysicalCardToPhysicalCardSet, IAbstractCard
from sutekh.core import Filters
import unittest


class CardSetHolderTests(SutekhTest):
    """class for the Card Set Holder tests"""

    def test_basic(self):
        """Basic card set holder tests."""
        # pylint: disable-msg=E1101, R0915, R0914
        # E1101: SQLObject + PyProtocols magic confuses pylint
        # R0915, R0914: Want a long, sequential test case to minimise
        # Everything is in the database, so should be no problems
        dSet1 = {
                '.44 Magnum': [3, None],
                'AK-47': [2, 'LotN'],
                'Abebe': [3, 'LoB'],
                'Abombwe': [3, 'LoB'],
                'Abbot': [1, 'Third Edition'],
                }
        oCSH = CardSetHolder()
        aExpectedExpansions = []

        for sCardName, aInfo in dSet1.iteritems():
            iCnt, sExpName = aInfo
            oCSH.add(iCnt, sCardName, sExpName)
            if sExpName:
                oThisExp = IExpansion(sExpName)
            else:
                oThisExp = None
            aExpectedExpansions.extend([oThisExp] * iCnt)

        aExpectedExpansions.sort()
        self.assertRaises(RuntimeError, oCSH.create_pcs)
        oCSH.name = 'Test Set 1'
        oCSH.create_pcs()
        oCS = IPhysicalCardSet('Test Set 1')
        self.assertEqual(len(oCS.cards), 12)
        oPCSFilter = Filters.PhysicalCardSetFilter('Test Set 1')
        oAbbotFilter = Filters.FilterAndBox([
            oPCSFilter, Filters.SpecificCardFilter('Abbot')])
        aCSCards = [IAbstractCard(x).name for x in oAbbotFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'Abbot'])
        oVampireFilter = Filters.FilterAndBox([
            oPCSFilter, Filters.CardTypeFilter('Vampire')])
        aCSCards = [IAbstractCard(x).name for x in oVampireFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'Abebe', u'Abebe', u'Abebe'])
        aExpansions = [oCard.expansion for oCard in oCS.cards]
        aExpansions.sort()
        self.assertEqual(aExpansions, aExpectedExpansions)

        oCSH.name = 'Test Set 2'
        oCSH.parent = 'Test Set 1'
        self.assertRaises(RuntimeError, oCSH.remove, 1, 'Abbot', None)
        self.assertRaises(RuntimeError, oCSH.remove, 2, 'Abbot',
            'Third Edition')
        oCSH.remove(1, 'Abbot', 'Third Edition')
        oCSH.remove(1, 'Abombwe', 'LoB')
        oCSH.create_pcs()

        oCS2 = IPhysicalCardSet('Test Set 2')
        self.assertEqual(oCS2.parent, oCS)
        self.assertEqual(len(oCS2.cards), 10)

        oPCSFilter = Filters.PhysicalCardSetFilter('Test Set 2')
        oAbbotFilter = Filters.FilterAndBox([
            oPCSFilter, Filters.SpecificCardFilter('Abbot')])
        aCSCards = [IAbstractCard(x).name for x in oAbbotFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [])
        oVampireFilter = Filters.FilterAndBox([
            oPCSFilter, Filters.CardTypeFilter('Vampire')])
        aCSCards = [IAbstractCard(x).name for x in oVampireFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'Abebe', u'Abebe', u'Abebe'])

        # Misspelt cards - the default lookup should exclude these
        dSet2 = {
                '.44 Magnum': [3, None],
                'Abede': [3, 'LoB'],
                }
        oCSH = CardSetHolder()
        for sCardName, aInfo in dSet2.iteritems():
            iCnt, sExpName = aInfo
            oCSH.add(iCnt, sCardName, sExpName)

        oCSH.name = 'Test Set 3'

        oCSH.create_pcs()

        oCS = IPhysicalCardSet('Test Set 3')
        self.assertEqual(len(oCS.cards), 3)
        oPCSFilter = Filters.PhysicalCardSetFilter('Test Set 3')
        oGunFilter = Filters.FilterAndBox([
            oPCSFilter, Filters.SpecificCardFilter('.44 Magnum')])
        aCSCards = [IAbstractCard(x).name for x in oGunFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'.44 Magnum', u'.44 Magnum',
            '.44 Magnum'])
        oVampireFilter = Filters.FilterAndBox([
            oPCSFilter, Filters.CardTypeFilter('Vampire')])
        aCSCards = [IAbstractCard(x).name for x in oVampireFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [])

        # Misspelt expansions - all cards should be added, but some with
        # None for the expansion
        dSet3 = {
                'AK-47': [2, 'Lords of the Knight'],
                'Abebe': [3, 'Legacy of Bllod'],
                }

        oCSH = CardSetHolder()
        for sCardName, aInfo in dSet3.iteritems():
            iCnt, sExpName = aInfo
            oCSH.add(iCnt, sCardName, sExpName)

        aExpectedExpansions = [None] * 5

        # Also check parent warnings
        oCSH.parent = 'Test Set 5'
        oCSH.name = 'Test Set 4'
        self.assertEqual(oCSH.get_parent_pcs(), None)
        self.assertNotEqual(len(oCSH.get_warnings()), 0)
        oCSH.clear_warnings()
        self.assertEqual(len(oCSH.get_warnings()), 0)
        oCSH.create_pcs()
        self.assertNotEqual(len(oCSH.get_warnings()), 0)

        oCS = IPhysicalCardSet('Test Set 4')
        self.assertEqual(len(oCS.cards), 5)
        oPCSFilter = Filters.PhysicalCardSetFilter('Test Set 4')
        oGunFilter = Filters.FilterAndBox([
            oPCSFilter, Filters.SpecificCardFilter('AK-47')])
        aCSCards = [IAbstractCard(x).name for x in oGunFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'AK-47', u'AK-47'])
        oVampireFilter = Filters.FilterAndBox([
            oPCSFilter, Filters.CardTypeFilter('Vampire')])
        aCSCards = [IAbstractCard(x).name for x in oVampireFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'Abebe', u'Abebe', u'Abebe'])

        aExpansions = [oCard.expansion for oCard in oCS.cards]
        aExpansions.sort()
        self.assertEqual(aExpansions, aExpectedExpansions)

    def test_cache(self):
        """Cached card set holder tests."""
        # pylint: disable-msg=E1101, R0915, R0914
        # E1101: SQLObject + PyProtocols magic confuses pylint
        # R0915, R0914: Want a long, sequential test case to minimise
        # Everything is in the database, so should be no problems
        dSet1 = {
                '.44 Magnum': [3, None],
                'AK-47': [2, 'LotN'],
                'Abebe': [3, 'LoB'],
                'Abombwe': [3, 'LoB'],
                'Abbot': [1, 'Third Edition'],
                }
        oCSH = CachedCardSetHolder()
        aExpectedExpansions = []
        dLookupCache = {}

        for sCardName, aInfo in dSet1.iteritems():
            iCnt, sExpName = aInfo
            oCSH.add(iCnt, sCardName, sExpName)
            if sExpName:
                oThisExp = IExpansion(sExpName)
            else:
                oThisExp = None
            aExpectedExpansions.extend([oThisExp] * iCnt)

        aExpectedExpansions.sort()
        self.assertRaises(RuntimeError, oCSH.create_pcs)
        oCSH.name = 'Test Set 1'
        oCSH.create_pcs(dLookupCache=dLookupCache)
        oCS = IPhysicalCardSet('Test Set 1')
        self.assertEqual(len(oCS.cards), 12)
        oPCSFilter = Filters.PhysicalCardSetFilter('Test Set 1')
        oAbbotFilter = Filters.FilterAndBox([
            oPCSFilter, Filters.SpecificCardFilter('Abbot')])
        aCSCards = [IAbstractCard(x).name for x in oAbbotFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'Abbot'])
        oVampireFilter = Filters.FilterAndBox([
            oPCSFilter, Filters.CardTypeFilter('Vampire')])
        aCSCards = [IAbstractCard(x).name for x in oVampireFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'Abebe', u'Abebe', u'Abebe'])
        aExpansions = [oCard.expansion for oCard in oCS.cards]
        aExpansions.sort()
        self.assertEqual(aExpansions, aExpectedExpansions)
        self.assertEqual(dLookupCache['cards'][u'Abbot'], u'abbot')
        self.assertEqual(dLookupCache['expansions'][u'LotN'],
                u'Lords of the Night')

        oCSH.name = 'Test Set 2'
        oCSH.parent = 'Test Set 1'
        self.assertRaises(RuntimeError, oCSH.remove, 1, 'Abbot', None)
        self.assertRaises(RuntimeError, oCSH.remove, 2, 'Abbot',
            'Third Edition')
        oCSH.remove(1, 'Abbot', 'Third Edition')
        oCSH.remove(1, 'Abombwe', 'LoB')
        oCSH.create_pcs(dLookupCache=dLookupCache)

        oCS2 = IPhysicalCardSet('Test Set 2')
        self.assertEqual(oCS2.parent, oCS)
        self.assertEqual(len(oCS2.cards), 10)

        oPCSFilter = Filters.PhysicalCardSetFilter('Test Set 2')
        oAbbotFilter = Filters.FilterAndBox([
            oPCSFilter, Filters.SpecificCardFilter('Abbot')])
        aCSCards = [IAbstractCard(x).name for x in oAbbotFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [])
        oVampireFilter = Filters.FilterAndBox([
            oPCSFilter, Filters.CardTypeFilter('Vampire')])
        aCSCards = [IAbstractCard(x).name for x in oVampireFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'Abebe', u'Abebe', u'Abebe'])

        dLookupCache = {}

        # Misspelt cards - the default lookup should exclude these
        dSet2 = {
                '.44 Magnum': [3, None],
                'Abede': [3, 'LoB'],
                }
        oCSH = CachedCardSetHolder()
        for sCardName, aInfo in dSet2.iteritems():
            iCnt, sExpName = aInfo
            oCSH.add(iCnt, sCardName, sExpName)

        oCSH.name = 'Test Set 3'

        oCSH.create_pcs(dLookupCache=dLookupCache)

        oCS = IPhysicalCardSet('Test Set 3')
        self.assertEqual(len(oCS.cards), 3)
        oPCSFilter = Filters.PhysicalCardSetFilter('Test Set 3')
        oGunFilter = Filters.FilterAndBox([
            oPCSFilter, Filters.SpecificCardFilter('.44 Magnum')])
        aCSCards = [IAbstractCard(x).name for x in oGunFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'.44 Magnum', u'.44 Magnum',
            '.44 Magnum'])
        oVampireFilter = Filters.FilterAndBox([
            oPCSFilter, Filters.CardTypeFilter('Vampire')])
        aCSCards = [IAbstractCard(x).name for x in oVampireFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [])

        self.assertEqual(dLookupCache['cards'][u'Abede'], None)

        # Misspelt expansions - all cards should be added, but some with
        # None for the expansion
        dSet3 = {
                'AK-47': [2, 'Lords of the Knight'],
                'Abebe': [3, 'Legacy of Bllod'],
                }
        dLookupCache = {}

        oCSH = CachedCardSetHolder()
        for sCardName, aInfo in dSet3.iteritems():
            iCnt, sExpName = aInfo
            oCSH.add(iCnt, sCardName, sExpName)

        aExpectedExpansions = [None] * 5

        oCSH.name = 'Test Set 4'
        oCSH.create_pcs(dLookupCache=dLookupCache)

        oCS = IPhysicalCardSet('Test Set 4')
        self.assertEqual(len(oCS.cards), 5)
        oPCSFilter = Filters.PhysicalCardSetFilter('Test Set 4')
        oGunFilter = Filters.FilterAndBox([
            oPCSFilter, Filters.SpecificCardFilter('AK-47')])
        aCSCards = [IAbstractCard(x).name for x in oGunFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'AK-47', u'AK-47'])
        oVampireFilter = Filters.FilterAndBox([
            oPCSFilter, Filters.CardTypeFilter('Vampire')])
        aCSCards = [IAbstractCard(x).name for x in oVampireFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'Abebe', u'Abebe', u'Abebe'])

        aExpansions = [oCard.expansion for oCard in oCS.cards]
        aExpansions.sort()
        self.assertEqual(aExpansions, aExpectedExpansions)

        self.assertEqual(dLookupCache['expansions']['Legacy of Bllod'],
                None)


if __name__ == "__main__":
    unittest.main()
