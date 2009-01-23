# test_WriteArdbInvXML.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an ARDB inventory XML file"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import aCardSetNames, \
        get_phys_cards
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.io.WriteArdbInvXML import WriteArdbInvXML
from sutekh.SutekhInfo import SutekhInfo
import unittest
import time

# pylint: disable-msg=W0511, C0301
# W0511 - this is not a actual TODO item
# C0301 - Ignore line length limits for this string
sExpected = """<inventory databaseVersion="%s" formatVersion="-TODO-1.0" generator="Sutekh [ %s ]">
  <date>%s</date>
  <crypt size="2">
    <vampire databaseID="11" have="1" need="0" spare="0">
      <adv />
      <name>Abebe</name>
      <set>LoB</set>
    </vampire><vampire databaseID="19" have="1" need="0" spare="0">
      <adv>(Advanced)</adv>
      <name>Alan Sovereign</name>
      <set>Promo20051001</set>
    </vampire>
  </crypt><library size="9">
    <card databaseID="1" have="2" need="0" spare="0">
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
        """Test ARDB XML inventroy writing"""
        # pylint: disable-msg=E1101, R0915, R0914
        # E1101: SQLObject + PyProtocols magic confuses pylint
        # R0915, R0914: Want a long, sequential test case to minimise
        # repeated setups, so it has lots of lines + variables
        aAddedPhysCards = get_phys_cards()
        # We have a physical card list, so create some physical card sets
        oPhysCardSet1 = PhysicalCardSet(name=aCardSetNames[0])
        oPhysCardSet1.comment = 'A test comment'
        oPhysCardSet1.author = 'A test author'

        for oCard in aAddedPhysCards:
            oPhysCardSet1.addPhysicalCard(oCard.id)
            oPhysCardSet1.syncUpdate()

        # Check output

        oWriter = WriteArdbInvXML()
        sTempFileName =  self._create_tmp_file()
        fOut = open(sTempFileName, 'w')
        oWriter.write(fOut, oPhysCardSet1.cards)
        fOut.close()

        fIn = open(sTempFileName, 'rU')
        sData = fIn.read()
        fIn.close()

        self.assertEqual(sData, sExpected)

if __name__ == "__main__":
    unittest.main()
