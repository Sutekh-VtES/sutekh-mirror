# test_WriteJOL.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an JOL file"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1
from sutekh.core.CardSetHolder import CardSetWrapper
from sutekh.io.WriteJOL import  WriteJOL
import unittest

EXPECTED_1 = """Abebe
Alan Sovereign (advanced)
Inez "Nurse216" Villagrande
The Siamese

4x.44 Magnum
2xAK-47
Aaron's Feeding Razor
2xAbbot
2xAbombwe
Scapelli, The Family "Mechanic"
The Path of Blood
"""


class JOLWriterTests(SutekhTest):
    """class for the JOL deck writer tests"""

    def test_deck_writer(self):
        """Test JOL deck writing"""
        oPhysCardSet1 = make_set_1()

        # Check output

        oWriter = WriteJOL()
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))

        self.assertEqual(sData, EXPECTED_1)


if __name__ == "__main__":
    unittest.main()
