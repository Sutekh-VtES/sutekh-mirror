# test_SLInventoryParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Simon Cross hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test reading a card set from an Secret Libary inventory file"""

import unittest
from sutekh.tests.TestCore import SutekhTest, DummyHolder
from sutekh.io.SLInventoryParser import SLInventoryParser

class TestSLInventoryParser(SutekhTest):
    """Class for the Secret Library inventory file parser tests"""

    sTestText1 = """
        ***SL***CRYPT***
        2;2;Abebe
        2;2;Alan Sovereign (Adv)
        4;3;Fran\xc3\xa7ois Warden Loehr
        ***SL***LIBRARY***
        1;1;Absimiliard's Army
        5;5;Ahriman's Demesne
        4;4;Atonement
        1;1;Textbook Damnation, The
        8;8;Watch Commander
        ***SL***ENDEXPORT***
        """

    def test_basic(self):
        """Run the Secret Libary inventory input test."""
        oHolder = DummyHolder()
        oParser = SLInventoryParser(oHolder)

        for sLine in self.sTestText1.split("\n"):
            oParser.feed(sLine + "\n")

        aCards = oHolder.get_cards()

        self.assertEqual(len(aCards), 8)
        self.failUnless(("Abebe", 2) in aCards)
        self.failUnless(("Alan Sovereign (Advanced)", 2) in aCards)
        self.failUnless(("Fran\xc3\xa7ois Warden Loehr", 4) in aCards)
        self.failUnless(("Absimiliard's Army", 1) in aCards)
        self.failUnless(("Ahriman's Demesne", 5) in aCards)
        self.failUnless(("Atonement", 4) in aCards)
        self.failUnless(("The Textbook Damnation", 1) in aCards)
        self.failUnless(("Watch Commander", 8) in aCards)

if __name__ == "__main__":
    unittest.main()
