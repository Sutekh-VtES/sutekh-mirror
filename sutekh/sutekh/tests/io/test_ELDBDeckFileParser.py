# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test reading a card set from an ELDB deck file"""

import unittest
from sutekh.tests.TestCore import SutekhTest
from sutekh.io.ELDBDeckFileParser import ELDBDeckFileParser

ELDB_TEXT_EXAMPLE_1 = """
"Test Deck"
"Anon Y Mous"
"Simple test deck.

http://www.example.url/in/description"
5
"Test Vamp 1"
"Test Vamp 1"
"Lazar Dobrescu"
"Alan Sovereign (ADV)"
"Inez 'Nurse216' Villagrande"
19
"Test Card 1"
"Test Card 1"
"Test Card 2"
"Test Card 2"
"Test Card 2"
"Test Card 2"
"Test Card 3"
"Test Card 3"
"Test Card 3"
"Test Card 3"
"Test Card 3"
"Test Card 3"
"Test Card 3"
"Test Card 3"
"Test Card 3"
"Test Card 3"
"Test Card 3"
"Test Card 3"
"Test Card 4"
"Path of Blood, The"
"Scapelli, The Family `Mechanic`"
"""


# Needs to be a SutekhTestCase so the name mapping cache test works
class TestELDBDeckFileParser(SutekhTest):
    """class for the ELDB deck file parser tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_basic(self):
        """Run the input test."""
        oHolder = self._make_holder_from_string(ELDBDeckFileParser(),
                                                ELDB_TEXT_EXAMPLE_1)

        self.assertEqual(oHolder.name, "Test Deck")
        self.assertEqual(oHolder.author, "Anon Y Mous")
        self.assertTrue(oHolder.comment.startswith(
            "Simple test deck."))
        self.assertTrue(oHolder.comment.endswith("in/description"))

        aCards = oHolder.get_cards()

        self.assertEqual(len(aCards), 10)
        self.assertTrue(("Test Vamp 1", 2) in aCards)
        self.assertTrue((u"L\xe1z\xe1r Dobrescu", 1) in aCards)
        self.assertTrue(('Inez "Nurse216" Villagrande', 1) in aCards)
        self.assertTrue(("Test Card 1", 2) in aCards)
        self.assertTrue(("Test Card 2", 4) in aCards)
        self.assertTrue(("Test Card 3", 12) in aCards)
        self.assertTrue(("Test Card 4", 1) in aCards)
        self.assertTrue(("Alan Sovereign (Advanced)", 1) in aCards)
        self.assertTrue(('Scapelli, The Family "Mechanic"', 1) in aCards)
        self.assertTrue(("The Path of Blood", 1) in aCards)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
