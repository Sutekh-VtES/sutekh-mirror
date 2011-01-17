# test_SLDeckParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test reading a card set from a Secret Library deck file"""

import unittest
import StringIO
from sutekh.tests.TestCore import SutekhTest, DummyHolder
from sutekh.io.SLDeckParser import SLDeckParser


class TestSLDeckParser(SutekhTest):
    """Class for the Secret Library deck parser tests"""

    sTestText1 = """
        ***SL***TITLE***
        NAME OF THE DECK
        ***SL***AUTHOR***
        CREATOR OF THE DECK
        ***SL***CREATED***
        YYYY-MM-DD
        ***SL***DESCRIPTION***
        DESCRIPTION OF THE DECK
        MAY SPAN ON MULTIPLE LINES
        ***SL***CRYPT***
        2 Count Germaine
        2 Count Germaine (Adv)
        2 Fran\xc3\xa7ois Warden Loehr
        ***SL***LIBRARY***
        10 Cloak the Gathering
        2 Coven, The
        2 Carlton Van Wyk (Hunter)
        ***SL***ENDDECK***
        """

    def test_basic(self):
        """Run the Secret Library deck input test."""
        oHolder = DummyHolder()
        fIn = StringIO.StringIO(self.sTestText1)
        oParser = SLDeckParser()
        oParser.parse(fIn, oHolder)

        aCards = oHolder.get_cards()

        self.assertEqual(len(aCards), 6)
        self.failUnless(("Count Germaine", 2) in aCards)
        self.failUnless(("Count Germaine (Advanced)", 2) in aCards)
        self.failUnless(("Fran\xc3\xa7ois Warden Loehr", 2) in aCards)
        self.failUnless(("Cloak the Gathering", 10) in aCards)
        self.failUnless(("The Coven", 2) in aCards)
        self.failUnless(("Carlton Van Wyk (Hunter)", 2) in aCards)
        self.assertEqual(oHolder.name, "NAME OF THE DECK")
        self.assertEqual(oHolder.author, "CREATOR OF THE DECK")
        self.assertEqual(oHolder.comment, "\n".join([
            "Created on YYYY-MM-DD",
            "DESCRIPTION OF THE DECK",
            "MAY SPAN ON MULTIPLE LINES",
        ]))

if __name__ == "__main__":
    unittest.main()
