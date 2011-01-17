# test_ARDBXMLDeckParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test reading a card set from an ARDB XML deck file"""

import unittest
from sutekh.tests.TestCore import SutekhTest
from sutekh.io.ARDBXMLDeckParser import ARDBXMLDeckParser
from sutekh.tests.io.test_AbstractCardSetParser import ACS_EXAMPLE_1

ARDB_DECK_EXAMPLE_1 = """
<deck generator="Sutekh [ Test ]" fromatVersion="val">
    <name>Test Deck</name>
    <author>Anon Y Mous</author>
    <description>Simple test deck.

    http://www.example.url/in/description</description>
    <date>2008-09-01</date>
    <crypt size="3" min="1" max="2" avg="1.1">
        <vampire databaseID="1" count="2">
           <name>Test Vamp 1</name>
           <adv></adv>
           <set>CE</set>
           <capacity></capacity>
           <text></text>
           <group />
           <disciplines></disciplines>
        </vampire>
        <vampire databaseID="2" count="1">
           <name>Test Vamp 2</name>
           <adv></adv>
           <set>SW</set>
           <capacity></capacity>
           <text></text>
           <group></group>
           <disciplines></disciplines>
        </vampire>
        <vampire databaseID="2" count="1">
           <name>Test Vamp 2</name>
           <adv>(Advanced)</adv>
           <set>Promo20051001</set>
           <capacity></capacity>
           <text></text>
           <group></group>
           <disciplines></disciplines>
        </vampire>
    </crypt>
    <library size="17">
       <card databaseID="3" count="4">
          <name>Test Card 1</name>
          <set>Sabbat</set>
          <type></type>
          <cost></cost>
          <requirement></requirement>
          <text />
       </card>
       <card databaseID="3" count="2">
          <name>Test Card 2</name>
          <set>BH</set>
          <type></type>
          <cost></cost>
          <requirement />
          <text></text>
       </card>
       <card databaseID="3" count="12">
          <name>Test Card 3</name>
          <set>BH</set>
          <type></type>
          <cost></cost>
          <requirement></requirement>
          <text></text>
       </card>
       <card databaseID="3" count="1">
          <name>Test Card 4</name>
          <set></set>
          <type></type>
          <cost></cost>
          <requirement></requirement>
          <text></text>
       </card>
       <card databaseID="50" count="1">
          <name>Test Card 5, The</name>
          <set></set>
          <type></type>
          <cost></cost>
          <requirement></requirement>
          <text></text>
       </card>
    </library>
</deck>
"""


class ArdbXMLDeckParserTests(SutekhTest):
    """class for the ARDB XML deck file parser tests"""

    # ARDB produces tag pairs for empty elements, we produce minimal
    # tags (<set></set> vs <set />, so we have both in the test data

    def test_basic(self):
        """Run the input test."""
        oHolder = self._make_holder_from_string(ARDBXMLDeckParser(),
                ARDB_DECK_EXAMPLE_1)

        self.assertEqual(oHolder.name, "Test Deck")
        self.assertEqual(oHolder.author, "Anon Y Mous")
        self.failUnless(oHolder.comment.startswith("Simple test deck."))
        self.failUnless(oHolder.comment.endswith("in/description"))

        aCards = oHolder.get_cards_exps()

        self.assertEqual(len(aCards), 8)
        self.failUnless((("Test Vamp 1", "CE"), 2) in aCards)
        self.failUnless((("Test Vamp 2", "SW"), 1) in aCards)
        self.failUnless((("Test Vamp 2 (Advanced)", "Promo-20051001"), 1)
                in aCards)
        self.failUnless((("Test Card 1", "Sabbat"), 4) in aCards)
        self.failUnless((("Test Card 2", "BH"), 2) in aCards)
        self.failUnless((("Test Card 3", "BH"), 12) in aCards)
        self.failUnless((("Test Card 4", None), 1) in aCards)
        self.failUnless((("The Test Card 5", None), 1) in aCards)

        oParser = ARDBXMLDeckParser()
        self.assertRaises(IOError, self._make_holder_from_string, oParser,
                ACS_EXAMPLE_1)
        self.assertRaises(IOError, self._make_holder_from_string, oParser,
                'random stuff')


if __name__ == "__main__":
    unittest.main()
