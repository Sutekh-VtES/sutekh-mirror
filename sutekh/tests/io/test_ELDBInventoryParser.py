# test_ELDBInventoryParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test reading a card set from an ELDB inventory file"""

import unittest
from sutekh.tests.TestCore import SutekhTest
from sutekh.io.ELDBInventoryParser import ELDBInventoryParser

# FELDB creates 0,0 entries, so they need to be in the test case
ELDB_INV_EXAMPLE_1 = """
"ELDB - Inventory"
"Test Vamp 1",2,0,"","Crypt"
"Lazar Dobrescu",1,0,"","Crypt"
"Test Vamp 2",0,0,"","Crypt"
"Test Card 1",2,0,"","Library"
"Test Card 2",4,0,"","Library"
"Test Card 3",12,0,"","Library"
"Test Card 4",1,0,"","Library"
"Test Card 5",0,0,"","Library"
"""


# Needs to be a SutekhTestCase so the name mapping cache test works
class TestELDBInventoryParser(SutekhTest):
    """class for the ELDB inventory reading test"""

    def test_basic(self):
        """Run the input test."""
        oHolder = self._make_holder_from_string(ELDBInventoryParser(),
                ELDB_INV_EXAMPLE_1)

        self.assertEqual(oHolder.name, '')  # DummyHolder default

        aCards = oHolder.get_cards()

        self.assertEqual(len(aCards), 6)
        self.failUnless(("Test Vamp 1", 2) in aCards)
        self.failUnless((u"L\xe1z\xe1r Dobrescu", 1) in aCards)
        self.failUnless(("Test Card 1", 2) in aCards)
        self.failUnless(("Test Card 2", 4) in aCards)
        self.failUnless(("Test Card 3", 12) in aCards)
        self.failUnless(("Test Card 4", 1) in aCards)
        # We don't need to test that the 0,0 entries have been skipped, as
        # that's covered by the len test

if __name__ == "__main__":
    unittest.main()
