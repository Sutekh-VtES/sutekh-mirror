# test_PhysicalCard.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test PhysicalCard handling"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests import test_WhiteWolfParser
from sutekh.core.SutekhObjects import IAbstractCard, PhysicalCard, IExpansion
from sutekh.io.PhysicalCardParser import PhysicalCardParser
from sutekh.io.PhysicalCardWriter import PhysicalCardWriter
import unittest

class PhysicalCardTests(SutekhTest):
    """class for the PhysicalCard tests"""
    aExpectedCards = test_WhiteWolfParser.WhiteWolfParserTests.aExpectedCards

    def test_physical(self):
        """Test physical card handling"""
        # pylint: disable-msg=E1101
        # SQLObject + PyProtocols magic confuses pylint
        aAbstractCards = ['.44 magnum', 'ak-47', 'abbot', 'abebe', 'abombwe']
        aCardExpansions = [('.44 magnum', 'Jyhad'),
                ('ak-47', 'LotN'),
                ('abbot', 'Third Edition'),
                ('abombwe', 'Legacy of Blood')]
        # Test addition
        for sName in aAbstractCards:
            oAC = IAbstractCard(sName)
            oPC = PhysicalCard(abstractCard=oAC, expansion=None)
            self.assertEqual(PhysicalCard.selectBy(
                abstractCardID=oAC.id).count(), 1)
        self.assertEqual(PhysicalCard.select().count(), len(aAbstractCards))

        for sName, sExpansion in aCardExpansions:
            oAC = IAbstractCard(sName)
            oExpansion = IExpansion(sExpansion)
            oPC = PhysicalCard(abstractCard=oAC, expansion=oExpansion)
            self.assertEqual(PhysicalCard.selectBy(
                abstractCardID=oAC.id).count(), 2)
            self.assertEqual(PhysicalCard.selectBy(abstractCardID=oAC.id,
                expansionID=oExpansion.id).count(), 1)

        self.assertEqual(PhysicalCard.select().count(), len(aAbstractCards) + \
                len(aCardExpansions))

        # test removal

        for sName, sExpansion in aCardExpansions:
            oAC = IAbstractCard(sName)
            oExpansion = IExpansion(sExpansion)
            oPC = list(PhysicalCard.selectBy(abstractCard=oAC,
                expansion=oExpansion))[0]
            PhysicalCard.delete(oPC.id)
            self.assertEqual(PhysicalCard.selectBy(
                abstractCardID=oAC.id).count(), 1)
            self.assertEqual(PhysicalCard.selectBy(abstractCardID=oAC.id,
                expansionID=oExpansion.id).count(), 0)
        self.assertEqual(PhysicalCard.select().count(), len(aAbstractCards))

        for sName in aAbstractCards:
            oAC = IAbstractCard(sName)
            oPC = list(PhysicalCard.selectBy(abstractCard=oAC))[0]
            PhysicalCard.delete(oPC.id)
            self.assertEqual(PhysicalCard.selectBy(
                abstractCardID=oAC.id).count(), 0)

        self.assertEqual(PhysicalCard.select().count(), 0)
        # test IO
        oAC = IAbstractCard(aAbstractCards[0])
        oPC = PhysicalCard(abstractCard=oAC, expansion=None)
        oWriter = PhysicalCardWriter()
        sExpected = '<cards sutekh_xml_version="%s"><card count="1" ' \
                 'expansion="None Specified" id="%d" name="%s" /></cards>' \
                 % (oWriter.sMyVersion, oPC.id, oAC.name)
        self.assertEqual(oWriter.gen_xml_string(), sExpected)

        PhysicalCard.delete(oPC.id)
        oParser = PhysicalCardParser()
        oParser.parse_string(sExpected)
        self.assertEqual(oWriter.gen_xml_string(), sExpected)

if __name__ == "__main__":
    unittest.main()
