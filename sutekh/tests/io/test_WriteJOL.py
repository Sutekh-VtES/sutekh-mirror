# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an JOL file"""

import unittest

from sutekh.base.core.CardSetHolder import CardSetWrapper

from sutekh.io.WriteJOL import WriteJOL
from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1

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
    # pylint: disable=R0904
    # R0904 - unittest.TestCase, so many public methods

    def test_deck_writer(self):
        """Test JOL deck writing"""
        oPhysCardSet1 = make_set_1()

        # Check output

        oWriter = WriteJOL()
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))

        self.assertEqual(sData, EXPECTED_1)


if __name__ == "__main__":
    unittest.main()
