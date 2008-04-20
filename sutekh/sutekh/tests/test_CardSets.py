# test_CardSets.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Card Set handling"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests import test_WhiteWolfParser
from sutekh.core.SutekhObjects import IAbstractCard, PhysicalCard, \
        IExpansion, PhysicalCardSet, AbstractCardSet, IPhysicalCardSet, \
        IAbstractCardSet
from sutekh.io.PhysicalCardSetParser import PhysicalCardSetParser
from sutekh.io.PhysicalCardSetWriter import PhysicalCardSetWriter
from sutekh.io.AbstractCardSetParser import AbstractCardSetParser
from sutekh.io.AbstractCardSetWriter import AbstractCardSetWriter
import unittest

class PhysicalCardSetTests(SutekhTest):
    """class for the Card Set tests"""
    aExpectedCards = test_WhiteWolfParser.WhiteWolfParserTests.aExpectedCards

    def test_physical_card_set(self):
        """Test physical card set handling"""
        # pylint: disable-msg=E1101
        # SQLObject + PyProtocols magic confuses pylint
        aAbstractCards = ['.44 magnum', 'ak-47', 'abbot', 'abebe', 'abombwe']
        aCardExpansions = [('.44 magnum', 'Jyhad'),
                ('ak-47', 'LotN'),
                ('abbot', 'Third Edition'),
                ('abombwe', 'Legacy of Blood')]
        aCardSetNames = ['Test Set 1', 'Test Set 2']
        # Set Physical Card List
        for sName in aAbstractCards:
            oAC = IAbstractCard(sName)
            PhysicalCard(abstractCard=oAC, expansion=None)

        for sName, sExpansion in aCardExpansions:
            oAC = IAbstractCard(sName)
            oExpansion = IExpansion(sExpansion)
            PhysicalCard(abstractCard=oAC, expansion=oExpansion)
        # We have a physical card list, so create some physical card sets
        oPCS1 = PhysicalCardSet(name=aCardSetNames[0])
        oPCS1.comment = 'A test comment'
        oPCS1.author = 'A test author'

        self.assertEqual(oPCS1.name, aCardSetNames[0])
        self.assertEqual(oPCS1.comment, 'A test comment')
        oPCS2 = PhysicalCardSet(name=aCardSetNames[1], comment='Test 2',
                author=oPCS1.author)
        self.assertEqual(oPCS2.name, aCardSetNames[1])
        self.assertEqual(oPCS2.author, oPCS1.author)
        self.assertEqual(oPCS2.comment, 'Test 2')

        oPCS3 = IPhysicalCardSet(aCardSetNames[0])

        self.assertEqual(oPCS1, oPCS3)

        oPCS4 = PhysicalCardSet.byName(aCardSetNames[1])
        self.assertEqual(oPCS2, oPCS4)

        # Add cards to the physical card sets

        # Check output

        # Check Deletion

        # Check input

    def test_abstract_card_set(self):
        """Test abstract card set handling"""
        # pylint: disable-msg=E1101
        # SQLObject + PyProtocols magic confuses pylint
        aAbstractCards = ['.44 magnum', 'ak-47', 'abbot', 'abebe', 'abombwe']
        aCardSetNames = ['Test AC 1', 'Test AC 2']
        # Create Abstract Card Sets
        oACS1 = AbstractCardSet(name=aCardSetNames[0])
        oACS1.comment = 'A test comment'
        oACS1.author = 'A test author'

        self.assertEqual(oACS1.name, aCardSetNames[0])
        self.assertEqual(oACS1.comment, 'A test comment')
        oACS2 = AbstractCardSet(name=aCardSetNames[1], comment='Test 2',
                author=oACS1.author)
        self.assertEqual(oACS2.name, aCardSetNames[1])
        self.assertEqual(oACS2.author, oACS1.author)
        self.assertEqual(oACS2.comment, 'Test 2')

        oACS3 = IAbstractCardSet(aCardSetNames[0])

        self.assertEqual(oACS1, oACS3)

        oACS4 = AbstractCardSet.byName(aCardSetNames[1])
        self.assertEqual(oACS2, oACS4)


        # Test addition

        # check output

        # check Deletion

        # check input


if __name__ == "__main__":
    unittest.main()
