# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test reading a card set from an ELDB deck file"""

import unittest
from sutekh.tests.TestCore import SutekhTest
from sutekh.base.io.CSVParser import CSVParser
from sutekh.tests.io.test_WriteCSV import (EXPECTED_1, EXPECTED_2, EXPECTED_3,
                                           EXPECTED_4)


# Needs to be a SutekhTestCase so the name mapping cache test works
class TestCSVParser(SutekhTest):
    """class for the CSV deck file parser tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_basic(self):
        """Run the input test."""

        # Check we can round trip from our own CSV files
        aTests = [
            (0, 2, 1, True, EXPECTED_1),
            (0, 2, 1, False, EXPECTED_2),
            (0, 1, None, True, EXPECTED_3),
            (0, 1, None, False, EXPECTED_4),
        ]

        for tTestInfo in aTests:
            oParser = CSVParser(tTestInfo[0], tTestInfo[1], tTestInfo[2],
                                tTestInfo[3])

            oHolder = self._make_holder_from_string(oParser, tTestInfo[4])

            aCards = oHolder.get_cards()

            self.assertEqual(len(aCards), 18)
            self.assertTrue((".44 Magnum", 4) in aCards)
            self.assertTrue(("Abebe", 1) in aCards)
            self.assertTrue(("Alan Sovereign (Advanced)", 1) in aCards)
            self.assertTrue(("Aaron's Feeding Razor", 1) in aCards)
            self.assertTrue(('Inez "Nurse216" Villagrande', 1) in aCards)
            self.assertTrue(('Scapelli, The Family "Mechanic"', 1) in aCards)
            self.assertTrue(('Swallowed by the Night', 2) in aCards)
            self.assertTrue(("The Siamese", 2) in aCards)
            self.assertTrue(("Abbot", 2) in aCards)
            self.assertTrue(("Immortal Grapple", 4) in aCards)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
