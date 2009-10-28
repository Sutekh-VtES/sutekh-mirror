# test_ELDBHTMLParser.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test case for ELDB HTML parser"""

from sutekh.io.ELDBHTMLParser import ELDBHTMLParser
from sutekh.tests.TestCore import SutekhTest
import unittest

ELDB_HTML_EXAMPLE_1 = """<HTML>
<HEAD>
<TITLE>Test Deck</TITLE>
</HEAD>
<BODY BGCOLOR="#ffffff">
<TABLE WIDTH=650 ALIGN="center" CELLSPACING=0 CELLPADDING=0 BORDER=0>
<TR><TD WIDTH=130>Deck Name:</TD><TD WIDTH=520>Test Deck</TD></TR>
<TR><TD WIDTH=130>Created By:</TD><TD WIDTH=520>Anon Y Mous</TD></TR>
<TR><TD WIDTH=130 VALIGN="top">Description:</TD><TD WIDTH=520>Simple test deck.</TD></TR>
<TR><TD COLSPAN=2 WIDTH=650>&nbsp;</TD><TR>
<TR><TD COLSPAN=2 WIDTH=650 BGCOLOR="#eeeeee">Crypt: (3 cards, Min: 2, Max: 4, Avg: 4.67)</TD></TR>
<TR><TD COLSPAN=2 WIDTH=650>1&nbsp;&nbsp;<a href="http://monger.vekn.org/showvamp.html?ID=123" class="textLink">Test Vamp 1</a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;aus FOR OBE&nbsp;&nbsp;6,&nbsp;&nbsp;Salubri</TD></TR>
<TR><TD COLSPAN=2 WIDTH=650>2&nbsp;&nbsp;<a href="http://monger.vekn.org/showvamp.html?ID=321" class="textLink">Test Vamp 2</a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ani FOR PRO&nbsp;&nbsp;5,&nbsp;&nbsp;Gangrel</TD></TR>
<TR><TD COLSPAN=2 WIDTH=650>&nbsp;</TD></TR>
<TR><TD COLSPAN=2 WIDTH=650 BGCOLOR="#eeeeee">Library: (7 cards)</TD></TR>
<TR><TD COLSPAN=2 WIDTH=650>Master (2 cards)</TD></TR>
<TR><TD COLSPAN=2 WIDTH=650>2&nbsp;&nbsp;<a href="http://monger.vekn.org/showcard.html?ID=111" class="textLink">Test Card 1</a></TD></TR>
<TR><TD COLSPAN=2 WIDTH=650>&nbsp;</TD></TR>
<TR><TD COLSPAN=2 WIDTH=650>Action (5 cards)</TD></TR>
<TR><TD COLSPAN=2 WIDTH=650>3&nbsp;&nbsp;<a href="http://monger.vekn.org/showcard.html?ID=222" class="textLink">Test Card 2</a></TD></TR>
<TR><TD COLSPAN=2 WIDTH=650>2&nbsp;&nbsp;<a href="http://monger.vekn.org/showcard.html?ID=3333" class="textLink">Test Card 3</a></TD></TR>
<TR><TD COLSPAN=2 WIDTH=650>&nbsp;</TD></TR>
<TR><TD COLSPAN=2 WIDTH=650 ALIGN="right">This file was last saved at 11:29:00 PM  on 01/09/08 </TD></TR>
</TABLE>
</BODY>
</HTML>
"""


class ELDBHTMLParserTests(SutekhTest):
    """class for the ELDB HTML input parser"""

    def test_basic(self):
        """Run the input test."""
        oHolder = self._make_holder_from_string(ELDBHTMLParser(),
                ELDB_HTML_EXAMPLE_1)

        self.assertEqual(oHolder.name, "Test Deck")
        self.assertEqual(oHolder.author, "Anon Y Mous")
        self.failUnless(oHolder.comment.startswith("Simple test deck."))

        aCards = oHolder.get_cards()

        self.assertEqual(len(aCards), 5)
        self.failUnless(("Test Vamp 1", 1) in aCards)
        self.failUnless(("Test Vamp 2", 2) in aCards)
        self.failUnless(("Test Card 1", 2) in aCards)
        self.failUnless(("Test Card 2", 3) in aCards)
        self.failUnless(("Test Card 3", 2) in aCards)


if __name__ == "__main__":
    unittest.main()
