# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test cases for the CardSetHolder functions, and some CardLookup stuff"""

import unittest

from sutekh.base.core.CardSetHolder import CardSetHolder, CachedCardSetHolder
from sutekh.base.core.BaseAdapters import (IPhysicalCardSet, IExpansion,
                                           IAbstractCard, IPrinting)
from sutekh.base.core.BaseTables import MapPhysicalCardToPhysicalCardSet
from sutekh.base.core import BaseFilters

from sutekh.tests.TestCore import SutekhTest


class CardSetHolderTests(SutekhTest):
    """class for the Card Set Holder tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_basic(self):
        """Basic card set holder tests."""
        # pylint: disable=too-many-statements, too-many-locals
        # Want a long, sequential test case to minimise repeated setup
        # Everything is in the database, so should be no problems
        dSet1 = {
            '.44 Magnum': [3, None],
            'AK-47': [2, 'LotN'],
            'Abebe': [3, 'LoB'],
            'Abombwe': [3, 'LoB'],
            'Abbot': [1, 'Third Edition'],
        }
        oCSH = CardSetHolder()
        aExpectedPrintings = []

        for sCardName, aInfo in dSet1.items():
            iCnt, sExpName = aInfo
            oCSH.add(iCnt, sCardName, sExpName, None)
            if sExpName:
                oExp = IExpansion(sExpName)
                oThisPrint = IPrinting((oExp, None))
            else:
                oThisPrint = None
            aExpectedPrintings.extend([oThisPrint] * iCnt)

        aExpectedPrintings.sort(key=lambda x: x.id if x else -1)
        self.assertRaises(RuntimeError, oCSH.create_pcs)
        oCSH.name = 'Test Set 1'
        oCSH.create_pcs()
        oCS = IPhysicalCardSet('Test Set 1')
        self.assertEqual(len(oCS.cards), 12)
        oPCSFilter = BaseFilters.PhysicalCardSetFilter('Test Set 1')
        oAbbotFilter = BaseFilters.FilterAndBox([
            oPCSFilter, BaseFilters.SpecificCardFilter('Abbot')])
        aCSCards = [IAbstractCard(x).name for x in oAbbotFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'Abbot'])
        oVampireFilter = BaseFilters.FilterAndBox([
            oPCSFilter, BaseFilters.CardTypeFilter('Vampire')])
        aCSCards = [IAbstractCard(x).name for x in oVampireFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'Abebe', u'Abebe', u'Abebe'])
        aPrintings = [oCard.printing for oCard in oCS.cards]
        aPrintings.sort(key=lambda x: x.id if x else -1)
        self.assertEqual(aPrintings, aExpectedPrintings)

        oCSH.name = 'Test Set 2'
        oCSH.parent = 'Test Set 1'
        self.assertRaises(RuntimeError, oCSH.remove, 1, 'Abbot', None, None)
        self.assertRaises(RuntimeError, oCSH.remove, 2, 'Abbot',
                          'Third Edition', None)
        oCSH.remove(1, 'Abbot', 'Third Edition', None)
        oCSH.remove(1, 'Abombwe', 'LoB', None)
        oCSH.create_pcs()

        oCS2 = IPhysicalCardSet('Test Set 2')
        self.assertEqual(oCS2.parent, oCS)
        self.assertEqual(len(oCS2.cards), 10)

        oPCSFilter = BaseFilters.PhysicalCardSetFilter('Test Set 2')
        oAbbotFilter = BaseFilters.FilterAndBox([
            oPCSFilter, BaseFilters.SpecificCardFilter('Abbot')])
        aCSCards = [IAbstractCard(x).name for x in oAbbotFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [])
        oVampireFilter = BaseFilters.FilterAndBox([
            oPCSFilter, BaseFilters.CardTypeFilter('Vampire')])
        aCSCards = [IAbstractCard(x).name for x in oVampireFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'Abebe', u'Abebe', u'Abebe'])

        # Misspelt cards - the default lookup should exclude these
        dSet2 = {
            '.44 Magnum': [3, None],
            'Abede': [3, 'LoB'],
        }
        oCSH = CardSetHolder()
        for sCardName, aInfo in dSet2.items():
            iCnt, sExpName = aInfo
            oCSH.add(iCnt, sCardName, sExpName, None)

        oCSH.name = 'Test Set 3'

        oCSH.create_pcs()

        oCS = IPhysicalCardSet('Test Set 3')
        self.assertEqual(len(oCS.cards), 3)
        oPCSFilter = BaseFilters.PhysicalCardSetFilter('Test Set 3')
        oGunFilter = BaseFilters.FilterAndBox([
            oPCSFilter, BaseFilters.SpecificCardFilter('.44 Magnum')])
        aCSCards = [IAbstractCard(x).name for x in oGunFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'.44 Magnum', u'.44 Magnum',
                                    '.44 Magnum'])
        oVampireFilter = BaseFilters.FilterAndBox([
            oPCSFilter, BaseFilters.CardTypeFilter('Vampire')])
        aCSCards = [IAbstractCard(x).name for x in
                    oVampireFilter.select(
                        MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [])

        # Misspelt expansions - all cards should be added, but some with
        # None for the expansion
        dSet3 = {
            'AK-47': [2, 'Lords of the Knight'],
            'Abebe': [3, 'Legacy of Bllod'],
        }

        oCSH = CardSetHolder()
        for sCardName, aInfo in dSet3.items():
            iCnt, sExpName = aInfo
            oCSH.add(iCnt, sCardName, sExpName, None)

        aExpectedPrintings = [None] * 5

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
        oPCSFilter = BaseFilters.PhysicalCardSetFilter('Test Set 4')
        oGunFilter = BaseFilters.FilterAndBox([
            oPCSFilter, BaseFilters.SpecificCardFilter('AK-47')])
        aCSCards = [IAbstractCard(x).name for x in oGunFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'AK-47', u'AK-47'])
        oVampireFilter = BaseFilters.FilterAndBox([
            oPCSFilter, BaseFilters.CardTypeFilter('Vampire')])
        aCSCards = [IAbstractCard(x).name for x in oVampireFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'Abebe', u'Abebe', u'Abebe'])

        aPrintings = [oCard.printing for oCard in oCS.cards]
        aPrintings.sort(key=lambda x: x.id if x else -1)
        self.assertEqual(aPrintings, aExpectedPrintings)

    def test_cache(self):
        """Cached card set holder tests."""
        # pylint: disable=too-many-statements, too-many-locals
        # Want a long, sequential test case to minimise repeated setup
        # Everything is in the database, so should be no problems
        dSet1 = {
            '.44 Magnum': [3, None],
            'AK-47': [2, 'LotN'],
            'Abebe': [3, 'LoB'],
            'Abombwe': [3, 'LoB'],
            'Abbot': [1, 'Third Edition'],
        }
        oCSH = CachedCardSetHolder()
        aExpectedPrintings = []
        dLookupCache = {}

        for sCardName, aInfo in dSet1.items():
            iCnt, sExpName = aInfo
            oCSH.add(iCnt, sCardName, sExpName, None)
            if sExpName:
                oExp = IExpansion(sExpName)
                oThisPrint = IPrinting((oExp, None))
            else:
                oThisPrint = None
            aExpectedPrintings.extend([oThisPrint] * iCnt)

        aExpectedPrintings.sort(key=lambda x: x.id if x else -1)
        self.assertRaises(RuntimeError, oCSH.create_pcs)
        oCSH.name = 'Test Set 1'
        oCSH.create_pcs(dLookupCache=dLookupCache)
        oCS = IPhysicalCardSet('Test Set 1')
        self.assertEqual(len(oCS.cards), 12)
        oPCSFilter = BaseFilters.PhysicalCardSetFilter('Test Set 1')
        oAbbotFilter = BaseFilters.FilterAndBox([
            oPCSFilter, BaseFilters.SpecificCardFilter('Abbot')])
        aCSCards = [IAbstractCard(x).name for x in
                    oAbbotFilter.select(
                        MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'Abbot'])
        oVampireFilter = BaseFilters.FilterAndBox([
            oPCSFilter, BaseFilters.CardTypeFilter('Vampire')])
        aCSCards = [IAbstractCard(x).name for x in
                    oVampireFilter.select(
                        MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'Abebe', u'Abebe', u'Abebe'])
        aPrintings = [oCard.printing for oCard in oCS.cards]
        aPrintings.sort(key=lambda x: x.id if x else -1)
        self.assertEqual(aPrintings, aExpectedPrintings)
        self.assertEqual(dLookupCache['cards'][u'Abbot'], u'abbot')
        self.assertEqual(dLookupCache['printings'][(u'LotN', None)],
                         (u'Lords of the Night', None))

        oCSH.name = 'Test Set 2'
        oCSH.parent = 'Test Set 1'
        self.assertRaises(RuntimeError, oCSH.remove, 1, 'Abbot', None, None)
        self.assertRaises(RuntimeError, oCSH.remove, 2, 'Abbot',
                          'Third Edition', None)
        oCSH.remove(1, 'Abbot', 'Third Edition', None)
        oCSH.remove(1, 'Abombwe', 'LoB', None)
        oCSH.create_pcs(dLookupCache=dLookupCache)

        oCS2 = IPhysicalCardSet('Test Set 2')
        self.assertEqual(oCS2.parent, oCS)
        self.assertEqual(len(oCS2.cards), 10)

        oPCSFilter = BaseFilters.PhysicalCardSetFilter('Test Set 2')
        oAbbotFilter = BaseFilters.FilterAndBox([
            oPCSFilter, BaseFilters.SpecificCardFilter('Abbot')])
        aCSCards = [IAbstractCard(x).name for x in oAbbotFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [])
        oVampireFilter = BaseFilters.FilterAndBox([
            oPCSFilter, BaseFilters.CardTypeFilter('Vampire')])
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
        for sCardName, aInfo in dSet2.items():
            iCnt, sExpName = aInfo
            oCSH.add(iCnt, sCardName, sExpName, None)

        oCSH.name = 'Test Set 3'

        oCSH.create_pcs(dLookupCache=dLookupCache)

        oCS = IPhysicalCardSet('Test Set 3')
        self.assertEqual(len(oCS.cards), 3)
        oPCSFilter = BaseFilters.PhysicalCardSetFilter('Test Set 3')
        oGunFilter = BaseFilters.FilterAndBox([
            oPCSFilter, BaseFilters.SpecificCardFilter('.44 Magnum')])
        aCSCards = [IAbstractCard(x).name for x in oGunFilter.select(
            MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'.44 Magnum', u'.44 Magnum',
                                    '.44 Magnum'])
        oVampireFilter = BaseFilters.FilterAndBox([
            oPCSFilter, BaseFilters.CardTypeFilter('Vampire')])
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
        for sCardName, aInfo in dSet3.items():
            iCnt, sExpName = aInfo
            oCSH.add(iCnt, sCardName, sExpName, None)

        aExpectedPrintings = [None] * 5

        oCSH.name = 'Test Set 4'
        oCSH.create_pcs(dLookupCache=dLookupCache)

        oCS = IPhysicalCardSet('Test Set 4')
        self.assertEqual(len(oCS.cards), 5)
        oPCSFilter = BaseFilters.PhysicalCardSetFilter('Test Set 4')
        oGunFilter = BaseFilters.FilterAndBox([
            oPCSFilter, BaseFilters.SpecificCardFilter('AK-47')])
        aCSCards = [IAbstractCard(x).name for x in
                    oGunFilter.select(
                        MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'AK-47', u'AK-47'])
        oVampireFilter = BaseFilters.FilterAndBox([
            oPCSFilter, BaseFilters.CardTypeFilter('Vampire')])
        aCSCards = [IAbstractCard(x).name for x in
                    oVampireFilter.select(
                        MapPhysicalCardToPhysicalCardSet).distinct()]
        self.assertEqual(aCSCards, [u'Abebe', u'Abebe', u'Abebe'])

        aPrintings = [oCard.printing for oCard in oCS.cards]
        aPrintings.sort(key=lambda x: x.id if x else -1)
        self.assertEqual(aPrintings, aExpectedPrintings)

        self.assertEqual(dLookupCache['printings'][('Legacy of Bllod', None)],
                         (None, None))


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
