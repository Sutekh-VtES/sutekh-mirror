# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test the PhysicalCardSet object handling"""

import unittest

from sqlobject import SQLObjectNotFound

from sutekh.base.core.BaseTables import (PhysicalCardSet,
                                         MapPhysicalCardToPhysicalCardSet)
from sutekh.base.core.BaseAdapters import IPhysicalCardSet
from sutekh.base.tests.TestUtils import make_card
from sutekh.base.core.CardSetUtilities import delete_physical_card_set

from sutekh.tests.TestCore import SutekhTest

ABSTRACT_CARDS = [
    ('.44 magnum', 3),
    ('ak-47', 1),
    ('abbot', 1),
    ('abebe', 1),
    ('abombwe', 1)
]

CARD_EXPANSIONS = [
    ('.44 magnum', 'Jyhad', 1),
    ('ak-47', 'LotN', 1),
    ('abbot', 'Third Edition', 1),
    ('abombwe', 'Legacy of Blood', 1),
    ('alan sovereign (advanced)', 'Promo-20051001', 1),
    ('the path of blood', 'LotN', 1),
    ('the siamese', 'BL', 2),
    ('inez "nurse216" villagrande', 'NoR', 1),
    ('Scapelli, the Family "Mechanic"', 'DS', 1),
    ("Aaron's Feeding Razor", "KoT", 1),
    ('Swallowed by the Night', 'Third', 2),
    ('Aire of Elation', 'CE', 3),
    ('Hide the Heart', 'HttB', 1),
]

SET_2_ONLY_CARDS = [
    ('alexandra', 'DS', 1),
    ('Abandoning the Flesh', 'CE', 1),
]
CARD_SET_NAMES = ['Test Set 1', 'Test Set 2', 'Test Set 3', 'Test Set 4']


def get_phys_cards():
    """Get Physical Cards for the given lists"""
    aAddedPhysCards = []
    for sName, iCount in ABSTRACT_CARDS:
        oPC = make_card(sName, None)
        for _iNum in range(iCount):
            aAddedPhysCards.append(oPC)
    for sName, sExpansion, iCount in CARD_EXPANSIONS:
        oPC = make_card(sName, sExpansion)
        for _iNum in range(iCount):
            aAddedPhysCards.append(oPC)
    return aAddedPhysCards


def make_set_1():
    """Make the first card set.

       Function as this is also used in the io tests.
       """

    aAddedPhysCards = get_phys_cards()
    oPhysCardSet1 = PhysicalCardSet(name=CARD_SET_NAMES[0])
    oPhysCardSet1.comment = 'A test comment'
    oPhysCardSet1.author = 'A test author'
    for oCard in aAddedPhysCards:
        oPhysCardSet1.addPhysicalCard(oCard.id)
    oPhysCardSet1.syncUpdate()
    return oPhysCardSet1


def make_set_2():
    """Make a second card set"""
    aAddedPhysCards = get_phys_cards()
    oPhysCardSet2 = PhysicalCardSet(name=CARD_SET_NAMES[1])
    oPhysCardSet2.comment = ('A formatted test comment\nA second line\n'
                             'A third line')
    oPhysCardSet2.author = 'A test author'
    oPhysCardSet2.annotations = 'Some Annotations'
    for iLoop in range(5, 10):
        oPhysCardSet2.addPhysicalCard(aAddedPhysCards[iLoop].id)
    for sName, sExpansion, iCount in SET_2_ONLY_CARDS:
        oPC = make_card(sName, sExpansion)
        for _iNum in range(iCount):
            oPhysCardSet2.addPhysicalCard(oPC.id)
    oPhysCardSet2.syncUpdate()
    return oPhysCardSet2


class PhysicalCardSetTests(SutekhTest):
    """class for the Physical Card Set tests"""
    # pylint: disable=R0904
    # R0904 - unittest.TestCase, so many public methods

    def test_physical_card_set(self):
        """Test physical card set object"""
        # pylint: disable=R0915, R0914
        # R0915, R0914: Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables
        aAddedPhysCards = get_phys_cards()
        # We have a physical card list, so create some physical card sets

        oPhysCardSet1 = PhysicalCardSet(name=CARD_SET_NAMES[2])

        # Add cards to the physical card sets

        for iLoop in range(5):
            oPhysCardSet1.addPhysicalCard(aAddedPhysCards[iLoop].id)
        oPhysCardSet1.syncUpdate()

        self.assertEqual(len(oPhysCardSet1.cards), 5)
        # Because we repeat .44 Magnum 3 times
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID=aAddedPhysCards[0].id).count(), 3)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID=aAddedPhysCards[4].id).count(), 1)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID=aAddedPhysCards[7].id).count(), 0)

        oPhysCardSet2 = PhysicalCardSet(name=CARD_SET_NAMES[1],
                                        comment='Test 2',
                                        author=oPhysCardSet1.author)

        self.assertEqual(oPhysCardSet2.name, CARD_SET_NAMES[1])
        self.assertEqual(oPhysCardSet2.author, oPhysCardSet1.author)
        self.assertEqual(oPhysCardSet2.comment, 'Test 2')

        for iLoop in range(3, 8):
            oPhysCardSet2.addPhysicalCard(aAddedPhysCards[iLoop].id)
        oPhysCardSet2.syncUpdate()

        self.assertEqual(len(oPhysCardSet2.cards), 5)
        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[0].id).count(), 3)
        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[4].id).count(), 2)
        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[7].id).count(), 1)

        oPhysCardSet3 = make_set_1()
        self.assertEqual(len(oPhysCardSet3.cards), len(aAddedPhysCards))

        self.assertEqual(oPhysCardSet3.name, CARD_SET_NAMES[0])
        self.assertEqual(oPhysCardSet3.comment, 'A test comment')

        oPhysCardSet4 = IPhysicalCardSet(CARD_SET_NAMES[0])

        self.assertEqual(oPhysCardSet3, oPhysCardSet4)

        # pylint: disable=no-member
        # SQLObject confuses pylint
        oPhysCardSet5 = PhysicalCardSet.byName(CARD_SET_NAMES[1])
        self.assertEqual(oPhysCardSet2, oPhysCardSet5)

        # Check Deletion

        # pylint: disable=not-an-iterable
        # SQLOBject confuses pylint
        for oCard in oPhysCardSet3.cards:
            oPhysCardSet3.removePhysicalCard(oCard.id)
        # pylint: enable=not-an-iterable

        self.assertEqual(len(oPhysCardSet3.cards), 0)
        PhysicalCardSet.delete(oPhysCardSet3.id)

        self.assertRaises(SQLObjectNotFound, PhysicalCardSet.byName,
                          CARD_SET_NAMES[0])

        delete_physical_card_set(CARD_SET_NAMES[1])

        self.assertRaises(SQLObjectNotFound, PhysicalCardSet.byName,
                          CARD_SET_NAMES[1])
        # pylint: enable=no-member

        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[0].id).count(), 3)
        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[4].id).count(), 1)

        delete_physical_card_set(CARD_SET_NAMES[2])

        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[0].id).count(), 0)
        self.assertEqual(
            MapPhysicalCardToPhysicalCardSet.selectBy(
                physicalCardID=aAddedPhysCards[4].id).count(), 0)

if __name__ == "__main__":
    unittest.main()
