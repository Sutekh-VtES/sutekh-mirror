# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Test case for ARDB text parser"""

import unittest

from sutekh.io.ARDBTextParser import ARDBTextParser
from sutekh.tests.TestCore import SutekhTest

ARDB_TEXT_EXAMPLE_1 = """
Deck Name : Test Deck
Author : Anon Y Mous
Description :
    Simple test deck.

http://www.example.url/in/description

Crypt [3 vampires] Capacity min: 2 max: 10 average: 7.33
------------------------------------------------------------
2x Test Vamp 1			  10 ...
1x Test Vamp 2			  2  ...
...

Library [19 cards]
------------------------------------------------------------
Action [6]
2x Test Card 1
4x Test Card 2

Action Modifier [12]
12x Test Card 3

Reaction [1]
1x Test Card 4
...
"""

ARDB_TEXT_EXAMPLE_2 = """
Deck Name : Test Deck 2
Author : Anon Y Mous
Description : Simple test deck.
Crypt: (3 vampires, Min: 2, Max: 10 Ave: 7.33)
------------------------------------------------------------
2 Test Vamp 1			  aus dom for   10 ...
1 Test Vamp 2			  DOM for obf   2  ...
...

Library [19 cards]
------------------------------------------------------------
Action [6]
2 Test Card 1
4 Test Card 2

Action Modifier [12]
12 Test Card 3

Reaction [1]
1 Test Card 4
...
"""

ARDB_TEXT_EXAMPLE_3 = """
Deck Name : Test Deck 2
Created By: Anon Y Mous

Crypt: (3 vampires, Min: 2, Max: 10 Ave: 7.33)
------------------------------------------------------------
2 x Test Vamp 1			  aus dom for   10 ...
1 x Test Vamp 2			  DOM for obf   2  ...
...

Library [19 cards]
------------------------------------------------------------
Action [6]
2 x Test Card 1
4 x Test Card 2

Action Modifier [12]
12 Test Card 3

Reaction [1]
1 Test Card 4
...
"""


class ARDBTextParserTests(SutekhTest):
    """class for the ARDB/FELDB text input parser"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_basic(self):
        """Run the input test."""
        oParser = ARDBTextParser()
        oHolder = self._make_holder_from_string(oParser, ARDB_TEXT_EXAMPLE_1)

        self.assertEqual(oHolder.name, "Test Deck")
        self.assertEqual(oHolder.author, "Anon Y Mous")
        self.assertTrue(oHolder.comment.startswith(
            "    Simple test deck."))
        self.assertTrue(oHolder.comment.endswith("in/description\n\n"))

        aCards = oHolder.get_cards()

        self.assertEqual(len(aCards), 6)
        self.assertTrue(("Test Vamp 1", 2) in aCards)
        self.assertTrue(("Test Vamp 2", 1) in aCards)
        self.assertTrue(("Test Card 1", 2) in aCards)
        self.assertTrue(("Test Card 2", 4) in aCards)
        self.assertTrue(("Test Card 3", 12) in aCards)
        self.assertTrue(("Test Card 4", 1) in aCards)

        oHolder = self._make_holder_from_string(oParser, ARDB_TEXT_EXAMPLE_2)

        self.assertEqual(oHolder.name, "Test Deck 2")
        self.assertEqual(oHolder.author, "Anon Y Mous")
        self.assertTrue(oHolder.comment.startswith(
            "Simple test deck."))

        aCards = oHolder.get_cards()

        self.assertEqual(len(aCards), 6)
        self.assertTrue(("Test Vamp 1", 2) in aCards)
        self.assertTrue(("Test Vamp 2", 1) in aCards)
        self.assertTrue(("Test Card 1", 2) in aCards)
        self.assertTrue(("Test Card 2", 4) in aCards)
        self.assertTrue(("Test Card 3", 12) in aCards)
        self.assertTrue(("Test Card 4", 1) in aCards)

        oHolder = self._make_holder_from_string(oParser, ARDB_TEXT_EXAMPLE_3)

        self.assertEqual(oHolder.name, "Test Deck 2")
        self.assertEqual(oHolder.author, "Anon Y Mous")

        aCards = oHolder.get_cards()

        self.assertEqual(len(aCards), 6)
        self.assertTrue(("Test Vamp 1", 2) in aCards)
        self.assertTrue(("Test Vamp 2", 1) in aCards)
        self.assertTrue(("Test Card 1", 2) in aCards)
        self.assertTrue(("Test Card 2", 4) in aCards)
        self.assertTrue(("Test Card 3", 12) in aCards)
        self.assertTrue(("Test Card 4", 1) in aCards)


if __name__ == "__main__":
    unittest.main()
