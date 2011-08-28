# test_PhysicalCardSet.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test the PhysicalCardSet object handling"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.core.SutekhObjects import PhysicalCardSet, IPhysicalCardSet, \
        MapPhysicalCardToPhysicalCardSet
from sutekh.tests.core.test_Filters import make_card
from sutekh.core.CardSetUtilities import delete_physical_card_set
from sqlobject import SQLObjectNotFound
import unittest

ABSTRACT_CARDS = ['.44 magnum', 'ak-47', 'abbot', 'abebe', 'abombwe']
CARD_EXPANSIONS = [('.44 magnum', 'Jyhad'),
        ('ak-47', 'LotN'),
        ('abbot', 'Third Edition'),
        ('abombwe', 'Legacy of Blood'),
        ('alan sovereign (advanced)', 'Promo-20051001'),
        ('the path of blood', 'LotN'),
        ('the siamese', 'BL'),
        ('inez "nurse216" villagrande', 'NoR'),
        ('Scapelli, the Family "Mechanic"', 'DS'),
        ("Aaron's Feeding Razor", "KoT")]
CARD_SET_NAMES = ['Test Set 1', 'Test Set 2', 'Test Set 3', 'Test Set 4']


def get_phys_cards():
    """Get Physical Cards for the given lists"""
    aAddedPhysCards = []
    for sName in ABSTRACT_CARDS:
        oPC = make_card(sName, None)
        aAddedPhysCards.append(oPC)
    for sName, sExpansion in CARD_EXPANSIONS:
        oPC = make_card(sName, sExpansion)
        aAddedPhysCards.append(oPC)
    return aAddedPhysCards


def make_set_1():
    """Make the first card set.

       Function as this is also used in the io tests.
       """

    # pylint: disable-msg=E1101
    # E1101: SQLObject + PyProtocols magic confuses pylint
    aAddedPhysCards = get_phys_cards()
    oPhysCardSet1 = PhysicalCardSet(name=CARD_SET_NAMES[0])
    oPhysCardSet1.comment = 'A test comment'
    oPhysCardSet1.author = 'A test author'
    for oCard in aAddedPhysCards:
        oPhysCardSet1.addPhysicalCard(oCard.id)
    oPhysCardSet1.addPhysicalCard(aAddedPhysCards[0])
    oPhysCardSet1.addPhysicalCard(aAddedPhysCards[0])
    oPhysCardSet1.syncUpdate()
    return oPhysCardSet1


class PhysicalCardSetTests(SutekhTest):
    """class for the Physical Card Set tests"""

    def test_physical_card_set(self):
        """Test physical card set object"""
        # pylint: disable-msg=E1101, R0915, R0914
        # E1101: SQLObject + PyProtocols magic confuses pylint
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
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID=aAddedPhysCards[0].id).count(), 1)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID=aAddedPhysCards[4].id).count(), 1)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID=aAddedPhysCards[7].id).count(), 0)

        oPhysCardSet2 = PhysicalCardSet(name=CARD_SET_NAMES[1],
                comment='Test 2', author=oPhysCardSet1.author)

        self.assertEqual(oPhysCardSet2.name, CARD_SET_NAMES[1])
        self.assertEqual(oPhysCardSet2.author, oPhysCardSet1.author)
        self.assertEqual(oPhysCardSet2.comment, 'Test 2')

        for iLoop in range(3, 8):
            oPhysCardSet2.addPhysicalCard(aAddedPhysCards[iLoop].id)
        oPhysCardSet2.syncUpdate()

        self.assertEqual(len(oPhysCardSet2.cards), 5)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID=aAddedPhysCards[0].id).count(), 1)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID=aAddedPhysCards[4].id).count(), 2)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID=aAddedPhysCards[7].id).count(), 1)

        oPhysCardSet3 = make_set_1()
        self.assertEqual(len(oPhysCardSet3.cards), len(aAddedPhysCards) + 2)

        self.assertEqual(oPhysCardSet3.name, CARD_SET_NAMES[0])
        self.assertEqual(oPhysCardSet3.comment, 'A test comment')

        oPhysCardSet4 = IPhysicalCardSet(CARD_SET_NAMES[0])

        self.assertEqual(oPhysCardSet3, oPhysCardSet4)

        oPhysCardSet5 = PhysicalCardSet.byName(CARD_SET_NAMES[1])
        self.assertEqual(oPhysCardSet2, oPhysCardSet5)

        # Check Deletion

        for oCard in oPhysCardSet3.cards:
            oPhysCardSet3.removePhysicalCard(oCard.id)

        self.assertEqual(len(oPhysCardSet3.cards), 0)
        PhysicalCardSet.delete(oPhysCardSet3.id)

        self.assertRaises(SQLObjectNotFound, PhysicalCardSet.byName,
            CARD_SET_NAMES[0])

        delete_physical_card_set(CARD_SET_NAMES[1])

        self.assertRaises(SQLObjectNotFound, PhysicalCardSet.byName,
            CARD_SET_NAMES[1])

        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID=aAddedPhysCards[0].id).count(), 1)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID=aAddedPhysCards[4].id).count(), 1)

        delete_physical_card_set(CARD_SET_NAMES[2])

        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID=aAddedPhysCards[0].id).count(), 0)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID=aAddedPhysCards[4].id).count(), 0)

if __name__ == "__main__":
    unittest.main()
