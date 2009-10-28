# test_WriteArdbInvXML.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an ARDB inventory XML file"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1
from sutekh.core.CardSetHolder import CardSetWrapper
from sutekh.io.WriteArdbInvXML import WriteArdbInvXML
from sutekh.SutekhInfo import SutekhInfo
import unittest
import time

# pylint: disable-msg=W0511, C0301
# W0511 - this is not a actual TODO item
# C0301 - Ignore line length limits for this string
EXPECTED_1 = """<inventory databaseVersion="%s" formatVersion="-TODO-1.0" generator="Sutekh [ %s ]">
  <date>%s</date>
  <crypt size="3">
    <vampire databaseID="11" have="1" need="0" spare="0">
      <adv />
      <name>Abebe</name>
      <set>LoB</set>
    </vampire><vampire databaseID="19" have="1" need="0" spare="0">
      <adv>Advanced</adv>
      <name>Alan Sovereign</name>
      <set>Promo20051001</set>
    </vampire><vampire databaseID="41" have="1" need="0" spare="0">
      <adv />
      <name>Siamese, The</name>
      <set>BL</set>
    </vampire>
  </crypt><library size="11">
    <card databaseID="1" have="4" need="0" spare="0">
      <name>.44 Magnum</name>
      <set>Jyhad</set>
    </card><card databaseID="2" have="2" need="0" spare="0">
      <name>AK-47</name>
      <set>LotN</set>
    </card><card databaseID="8" have="2" need="0" spare="0">
      <name>Abbot</name>
      <set>Third</set>
    </card><card databaseID="14" have="2" need="0" spare="0">
      <name>Abombwe</name>
      <set>LoB</set>
    </card><card databaseID="37" have="1" need="0" spare="0">
      <name>Path of Blood, The</name>
      <set>LotN</set>
    </card>
  </library>
</inventory>""" % (WriteArdbInvXML.sDatabaseVersion, SutekhInfo.VERSION_STR,
        time.strftime('%Y-%m-%d', time.localtime()))
# pylint: enable-msg=W0511, C0301

class ArdbInvXMLWriterTests(SutekhTest):
    """class for the ARDB inventory XML writer tests"""

    def test_deck_writer(self):
        """Test ARDB XML inventory writing"""
        oPhysCardSet1 = make_set_1()

        # Check output

        oWriter = WriteArdbInvXML()
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))

        self.assertEqual(sData, EXPECTED_1)

if __name__ == "__main__":
    unittest.main()
