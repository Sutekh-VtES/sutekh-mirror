# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an ARDB inventory XML file"""

import unittest
import time

from sutekh.base.core.CardSetHolder import CardSetWrapper

from sutekh.io.WriteArdbInvXML import WriteArdbInvXML
from sutekh.SutekhInfo import SutekhInfo
from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1

# pylint: disable=fixme, line-too-long
# this is not a actual TODO item
# Ignore line length limits for this string, since it's for testing
EXPECTED_1 = """<inventory databaseVersion="%s" formatVersion="-TODO-1.0" generator="Sutekh [ %s ]">
  <date>DATE</date>
  <crypt size="6">
    <vampire databaseID="11" have="1" need="0" spare="0">
      <adv />
      <name>Abebe</name>
      <set>LoB</set>
    </vampire><vampire databaseID="20" have="1" need="0" spare="0">
      <adv>Advanced</adv>
      <name>Alan Sovereign</name>
      <set>Promo20051001</set>
    </vampire><vampire databaseID="47" have="1" need="0" spare="0">
      <adv />
      <name>Hektor</name>
      <set>Third</set>
    </vampire><vampire databaseID="50" have="1" need="0" spare="0">
      <adv />
      <name>Inez "Nurse216" Villagrande</name>
      <set>NoR</set>
    </vampire><vampire databaseID="75" have="2" need="0" spare="0">
      <adv />
      <name>Siamese, The</name>
      <set>BL</set>
    </vampire>
  </crypt><library size="28">
    <card databaseID="1" have="4" need="0" spare="0">
      <name>.44 Magnum</name>
      <set>CE</set>
    </card><card databaseID="2" have="2" need="0" spare="0">
      <name>AK-47</name>
      <set>LotN</set>
    </card><card databaseID="6" have="1" need="0" spare="0">
      <name>Aaron's Feeding Razor</name>
      <set>KoT</set>
    </card><card databaseID="8" have="2" need="0" spare="0">
      <name>Abbot</name>
      <set>Third</set>
    </card><card databaseID="14" have="2" need="0" spare="0">
      <name>Abombwe</name>
      <set>LoB</set>
    </card><card databaseID="17" have="3" need="0" spare="0">
      <name>Aire of Elation</name>
      <set>CE</set>
    </card><card databaseID="26" have="1" need="0" spare="0">
      <name>Anarch Manifesto, An</name>
      <set>TR</set>
    </card><card databaseID="80" have="1" need="0" spare="0">
      <name>Hide the Heart</name>
      <set>HttB</set>
    </card><card databaseID="49" have="4" need="0" spare="0">
      <name>Immortal Grapple</name>
      <set>Jyhad</set>
    </card><card databaseID="70" have="1" need="0" spare="0">
      <name>Scapelli, The Family "Mechanic"</name>
      <set>DS</set>
    </card><card databaseID="74" have="2" need="0" spare="0">
      <name>Swallowed by the Night</name>
      <set>Third</set>
    </card><card databaseID="62" have="1" need="0" spare="0">
      <name>Path of Blood, The</name>
      <set>LotN</set>
    </card><card databaseID="81" have="4" need="0" spare="0">
      <name>Walk of Flame</name>
      <set>KoT</set>
    </card>
  </library>
</inventory>""" % (WriteArdbInvXML.sDatabaseVersion, SutekhInfo.VERSION_STR)
# pylint: enable=fixme, line-too-long


class ArdbInvXMLWriterTests(SutekhTest):
    """class for the ARDB inventory XML writer tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_deck_writer(self):
        """Test ARDB XML inventory writing"""
        oPhysCardSet1 = make_set_1()
        sCurDate = time.strftime('>%Y-%m-%d<', time.localtime())

        # Check output

        oWriter = WriteArdbInvXML()
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))
        sData = sData.replace(sCurDate, '>DATE<')

        self._compare_xml_strings(sData, EXPECTED_1)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
