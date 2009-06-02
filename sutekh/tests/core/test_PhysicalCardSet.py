# test_PhysicalCardSet.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test the PhysicalCardSet object handling"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.core.SutekhObjects import IAbstractCard, IPhysicalCard, \
        IExpansion, PhysicalCardSet, IPhysicalCardSet, \
        MapPhysicalCardToPhysicalCardSet
from sutekh.core.CardSetUtilities import delete_physical_card_set
from sqlobject import SQLObjectNotFound
import unittest

aAbstractCards = ['.44 magnum', 'ak-47', 'abbot', 'abebe', 'abombwe']
aCardExpansions = [('.44 magnum', 'Jyhad'),
        ('ak-47', 'LotN'),
        ('abbot', 'Third Edition'),
        ('abombwe', 'Legacy of Blood'),
        ('alan sovereign (advanced)', 'Promo-20051001'),
        ('the path of blood', 'LotN')]
aCardSetNames = ['Test Set 1', 'Test Set 2', 'Test Set 3']

def get_phys_cards():
    """Get Physical Cards for the given lists"""
    aAddedPhysCards = []
    for sName in aAbstractCards:
        oAC = IAbstractCard(sName)
        oPC = IPhysicalCard((oAC, None))
        aAddedPhysCards.append(oPC)
    for sName, sExpansion in aCardExpansions:
        oAC = IAbstractCard(sName)
        oExpansion = IExpansion(sExpansion)
        oPC = IPhysicalCard((oAC, oExpansion))
        aAddedPhysCards.append(oPC)
    return aAddedPhysCards

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
        oPhysCardSet1 = PhysicalCardSet(name=aCardSetNames[0])
        oPhysCardSet1.comment = 'A test comment'
        oPhysCardSet1.author = 'A test author'

        self.assertEqual(oPhysCardSet1.name, aCardSetNames[0])
        self.assertEqual(oPhysCardSet1.comment, 'A test comment')
        oPhysCardSet2 = PhysicalCardSet(name=aCardSetNames[1],
                comment='Test 2', author=oPhysCardSet1.author)
        self.assertEqual(oPhysCardSet2.name, aCardSetNames[1])
        self.assertEqual(oPhysCardSet2.author, oPhysCardSet1.author)
        self.assertEqual(oPhysCardSet2.comment, 'Test 2')

        oPhysCardSet3 = IPhysicalCardSet(aCardSetNames[0])

        self.assertEqual(oPhysCardSet1, oPhysCardSet3)

        oPhysCardSet4 = PhysicalCardSet.byName(aCardSetNames[1])
        self.assertEqual(oPhysCardSet2, oPhysCardSet4)

        # Add cards to the physical card sets

        for iLoop in range(5):
            oPhysCardSet1.addPhysicalCard(aAddedPhysCards[iLoop].id)
            oPhysCardSet1.syncUpdate()

        self.assertEqual(len(oPhysCardSet1.cards), 5)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID = aAddedPhysCards[0].id).count(), 1)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID = aAddedPhysCards[7].id).count(), 0)

        for iLoop in range(3, 8):
            oPhysCardSet2.addPhysicalCard(aAddedPhysCards[iLoop].id)
            oPhysCardSet2.syncUpdate()

        self.assertEqual(len(oPhysCardSet2.cards), 5)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID = aAddedPhysCards[0].id).count(), 1)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID = aAddedPhysCards[4].id).count(), 2)

        # Check Deletion

        for oCard in oPhysCardSet1.cards:
            oPhysCardSet1.removePhysicalCard(oCard.id)

        self.assertEqual(len(oPhysCardSet1.cards), 0)
        PhysicalCardSet.delete(oPhysCardSet1.id)

        self.assertRaises(SQLObjectNotFound, PhysicalCardSet.byName,
            aCardSetNames[0])

        delete_physical_card_set(aCardSetNames[1])

        self.assertRaises(SQLObjectNotFound, PhysicalCardSet.byName,
            aCardSetNames[1])

        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID = aAddedPhysCards[0].id).count(), 0)
        self.assertEqual(MapPhysicalCardToPhysicalCardSet.selectBy(
            physicalCardID = aAddedPhysCards[4].id).count(), 0)

if __name__ == "__main__":
    unittest.main()
