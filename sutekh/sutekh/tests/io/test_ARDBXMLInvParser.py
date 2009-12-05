# test_ARDBXMLInvParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test reading a card set from an ARDB XML inventory file"""

import unittest
from sutekh.tests.TestCore import SutekhTest
from sutekh.io.ARDBXMLInvParser import ARDBXMLInvParser
from sutekh.tests.io.test_ARDBXMLDeckParser import ARDB_DECK_EXAMPLE_1
from sutekh.tests.io.test_AbstractCardSetParser import ACS_EXAMPLE_1

# ARDB produces tag pairs for empty elements, we produce minimal
# tags (<set></set> vs <set />, so we have both in the test data

ARDB_INV_EXAMPLE_1 = """
<inventory generator="Sutekh [ Test ]" fromatVersion="val">
    <date>2008-09-01</date>
    <crypt size="3">
        <vampire databaseID="1" have="2" spare="0" need="2">
           <name>Test Vamp 1</name>
           <adv></adv>
           <set>CE</set>
           <rarity>U2</rarity>
        </vampire>
        <vampire databaseID="2" have="1" spare="0" need="0">
           <name>Test Vamp 2</name>
           <adv></adv>
           <set>SW</set>
           <rarity>U</rarity>
        </vampire>
        <vampire databaseID="12" have="1" spare="0" needs="0">
           <name>Alan Sovereign</name>
           <adv>(Advanced)</adv>
           <set>Promo20051001</set>
           <rarity>P</rarity>
        </vampire>
    </crypt>
    <library size="17">
       <card databaseID="3" have="4" spare="0" need="0">
          <name>Test Card 1</name>
          <set>Sabbat</set>
          <rarity>C</rarity>
       </card>
       <card databaseID="3" have="2" spare="0" need="0">
          <name>Test Card 2</name>
          <set>BH</set>
          <rarity>C</rarity>
       </card>
       <card databaseID="3" have="12" spare="0" need="0">
          <name>Test Card 3</name>
          <set>BH</set>
          <rarity>C</rarity>
       </card>
       <card databaseID="3" have="1" spare="0" need="0">
          <name>Test Card 4</name>
          <set></set>
          <rarity>C</rarity>
       </card>
       <card databaseID="30" have="1" spare="0" need="0">
          <name>Path of Blood, The</name>
          <set></set>
          <rarity>C</rarity>
       </card>

    </library>
</inventory>
"""


class ArdbXMLInvParserTests(SutekhTest):
    """class for the ARDB XML inventory file parser tests"""

    def test_basic(self):
        """Run the input test."""
        oHolder = self._make_holder_from_string(ARDBXMLInvParser(),
                ARDB_INV_EXAMPLE_1)

        self.assertEqual(oHolder.name, "")

        aCards = oHolder.get_cards_exps()

        self.assertEqual(len(aCards), 8)
        self.failUnless((("Test Vamp 1", "CE"), 2) in aCards)
        self.failUnless((("Test Vamp 2", "SW"), 1) in aCards)
        self.failUnless((("Test Card 1", "Sabbat"), 4) in aCards)
        self.failUnless((("Test Card 2", "BH"), 2) in aCards)
        self.failUnless((("Test Card 3", "BH"), 12) in aCards)
        self.failUnless((("Test Card 4", None), 1) in aCards)
        self.failUnless((("The Path of Blood", None), 1) in aCards)
        self.failUnless((("Alan Sovereign (Advanced)", 'Promo-20051001'), 1)
                in aCards)

        oParser = ARDBXMLInvParser()
        self.assertRaises(IOError, self._make_holder_from_string, oParser,
                ACS_EXAMPLE_1)
        self.assertRaises(IOError, self._make_holder_from_string, oParser,
                ARDB_DECK_EXAMPLE_1)
        self.assertRaises(IOError, self._make_holder_from_string, oParser,
                'random stuff')

if __name__ == "__main__":
    unittest.main()
