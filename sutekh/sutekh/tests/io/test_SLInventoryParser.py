# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test reading a card set from an Secret Library inventory file"""

import unittest
from io import StringIO
from sutekh.tests.TestCore import SutekhTest
from sutekh.base.tests.TestUtils import DummyHolder
from sutekh.io.SLInventoryParser import SLInventoryParser


class TestSLInventoryParser(SutekhTest):
    """Class for the Secret Library inventory file parser tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

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
        """Run the Secret Library inventory input test."""
        oHolder = DummyHolder()
        fIn = StringIO(self.sTestText1)
        oParser = SLInventoryParser()
        oParser.parse(fIn, oHolder)

        aCards = oHolder.get_cards()

        self.assertEqual(len(aCards), 8)
        self.assertTrue(("Abebe", 2) in aCards)
        self.assertTrue(("Alan Sovereign (Advanced)", 2) in aCards)
        self.assertTrue(("Fran\xc3\xa7ois Warden Loehr", 4) in aCards)
        self.assertTrue(("Absimiliard's Army", 1) in aCards)
        self.assertTrue(("Ahriman's Demesne", 5) in aCards)
        self.assertTrue(("Atonement", 4) in aCards)
        self.assertTrue(("The Textbook Damnation", 1) in aCards)
        self.assertTrue(("Watch Commander", 8) in aCards)

        self.assertRaises(IOError, self._make_holder_from_string, oParser,
                          'random stuff')


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
