# test_PhysicalCard.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests import test_WhiteWolfParser
from sutekh.core.SutekhObjects import AbstractCard, IAbstractCard, \
        PhysicalCard, IExpansion
from sutekh.core import Filters
from sutekh.io.PhysicalCardParser import PhysicalCardParser
from sutekh.io.PhysicalCardWriter import PhysicalCardWriter
import unittest

class PhysicalCardTests(SutekhTest):
    aExpectedCards = test_WhiteWolfParser.WhiteWolfParserTests.aExpectedCards

    def test_physical(self):
        """Test physical card handling"""
        aAbstractCards = ['.44 magnum', 'ak-47', 'abbot', 'abebe', 'abombwe']
        aCardExpansions = [('.44 magnum', 'Jyhad'),
                ('ak-47', 'LotN'),
                ('abbot', 'Third Edition'),
                ('abombwe', 'Legacy of Blood')]
        # Test addition
        for sName in aAbstractCards:
            oAC = IAbstractCard(sName)
            oPC = PhysicalCard(abstractCard=oAC, expansion=None)
            self.assertEqual(PhysicalCard.selectBy(abstractCardID=oAC.id).count(), 1)
        self.assertEqual(PhysicalCard.select().count(), len(aAbstractCards))

        for sName, sExpansion in aCardExpansions:
            oAC = IAbstractCard(sName)
            oExpansion = IExpansion(sExpansion)
            oPC = PhysicalCard(abstractCard=oAC, expansion=oExpansion)
            self.assertEqual(PhysicalCard.selectBy(abstractCardID=oAC.id).count(), 2)
            self.assertEqual(PhysicalCard.selectBy(abstractCardID=oAC.id, expansionID=oExpansion.id).count(), 1)

        self.assertEqual(PhysicalCard.select().count(), len(aAbstractCards)+len(aCardExpansions))

        # test removal

        for sName, sExpansion in aCardExpansions:
            oAC = IAbstractCard(sName)
            oExpansion = IExpansion(sExpansion)
            oPC = list(PhysicalCard.selectBy(abstractCard=oAC, expansion=oExpansion))[0]
            PhysicalCard.delete(oPC.id)
            self.assertEqual(PhysicalCard.selectBy(abstractCardID=oAC.id).count(), 1)
            self.assertEqual(PhysicalCard.selectBy(abstractCardID=oAC.id, expansionID=oExpansion.id).count(), 0)
        self.assertEqual(PhysicalCard.select().count(), len(aAbstractCards))

        for sName in aAbstractCards:
            oAC = IAbstractCard(sName)
            oPC = list(PhysicalCard.selectBy(abstractCard=oAC))[0]
            PhysicalCard.delete(oPC.id)
            self.assertEqual(PhysicalCard.selectBy(abstractCardID=oAC.id).count(), 0)

        self.assertEqual(PhysicalCard.select().count(), 0)
        # test IO
        oAC = IAbstractCard(aAbstractCards[0])
        oPC = PhysicalCard(abstractCard=oAC, expansion=None)
        oW = PhysicalCardWriter()
        sExpected = '<cards sutekh_xml_version="%s"><card count="1" ' \
                 'expansion="None Specified" id="%d" name="%s" /></cards>' \
                 % (oW.sMyVersion, oPC.id, oAC.name)
        self.assertEqual(oW.gen_xml_string(), sExpected)

        PhysicalCard.delete(oPC.id)
        oP = PhysicalCardParser()
        oP.parse_string(sExpected)
        self.assertEqual(oW.gen_xml_string(), sExpected)

if __name__ == "__main__":
    unittest.main()
