# test_WriteArdbXML.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an ARDB deck XML file"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1
from sutekh.core.CardSetHolder import CardSetWrapper
from sutekh.io.WriteArdbXML import WriteArdbXML
from sutekh.SutekhInfo import SutekhInfo
import unittest
import time

# pylint: disable-msg=W0511, C0301
# W0511 - this is not a actual TODO item
# C0301 - Ignore line length limits for this string
EXPECTED_1 = """<deck databaseVersion="%s" formatVersion="-TODO-1.0" generator="Sutekh [ %s ]">
  <date>DATE</date>
  <name>Test Set 1</name>
  <author>A test author</author>
  <description>A test comment</description>
  <crypt avg="5.00" max="7" min="3" size="4">
    <vampire count="1" databaseID="11">
      <adv />
      <name>Abebe</name>
      <set>LoB</set>
      <disciplines>nec obf thn</disciplines>
      <clan>Samedi</clan>
      <capacity>4</capacity>
      <group>4</group>
      <text>Independent.</text>
    </vampire><vampire count="1" databaseID="20">
      <adv>Advanced</adv>
      <name>Alan Sovereign</name>
      <set>Promo20051001</set>
      <disciplines>AUS DOM for pre</disciplines>
      <clan>Ventrue</clan>
      <capacity>6</capacity>
      <group>3</group>
      <text>Advanced, Camarilla: While Alan is ready, you may pay some or all of the pool cost of equipping from any investment cards you control.
[MERGED] During your master phase, if Alan is ready, you may move a counter from any investment card to your pool.</text>
    </vampire><vampire count="1" databaseID="42">
      <adv />
      <name>Inez "Nurse216" Villagrande</name>
      <set>NoR</set>
      <disciplines>inn</disciplines>
      <clan>Imbued</clan>
      <capacity>3</capacity>
      <group>4</group>
      <text>When Inez enters play, you may search your library (shuffle afterward) or hand for a power that requires innocence and put it on her.</text>
    </vampire><vampire count="1" databaseID="63">
      <adv />
      <name>Siamese, The</name>
      <set>BL</set>
      <disciplines>PRE SPI ani pro</disciplines>
      <clan>Ahrimane</clan>
      <capacity>7</capacity>
      <group>2</group>
      <text>Sabbat: +1 bleed. Sterile.</text>
    </vampire>
  </crypt><library size="13">
    <card count="1" databaseID="1">
      <name>.44 Magnum</name>
      <set>Jyhad</set>
      <cost>2 pool</cost>
      <type>Equipment</type>
      <text>Weapon, gun.
2R damage each strike, with an optional maneuver each combat.</text>
    </card><card count="3" databaseID="1">
      <name>.44 Magnum</name>
      <set>CE</set>
      <cost>2 pool</cost>
      <type>Equipment</type>
      <text>Weapon, gun.
2R damage each strike, with an optional maneuver each combat.</text>
    </card><card count="2" databaseID="2">
      <name>AK-47</name>
      <set>LotN</set>
      <cost>5 pool</cost>
      <type>Equipment</type>
      <text>Weapon. Gun.
2R damage each strike, with an optional maneuver {each combat}. When bearer strikes with this gun, he or she gets an optional additional strike this round, only usable to strike with this gun.</text>
    </card><card count="1" databaseID="6">
      <name>Aaron's Feeding Razor</name>
      <set>KoT</set>
      <cost>1 pool</cost>
      <type>Equipment</type>
      <text>Unique equipment.
When this vampire successfully hunts, he or she gains 1 additional blood.</text>
    </card><card count="2" databaseID="8">
      <name>Abbot</name>
      <set>Third</set>
      <type>Action</type>
      <text>+1 stealth action. Requires a Sabbat vampire.
Put this card on this acting Sabbat vampire and untap him or her. This Sabbat vampire gets +1 intercept against (D) actions directed at his or her controller. A vampire may have only one Abbot.</text>
    </card><card count="2" databaseID="14">
      <name>Abombwe</name>
      <set>LoB</set>
      <type>Master</type>
      <text>Master: Discipline. Trifle.
Put this card on a Laibon or on a vampire with Protean [pro]. This vampire gains one level of Abombwe [abo]. Capacity increases by 1: the vampire is one generation older. Cannot be placed on a vampire with superior Abombwe.</text>
    </card><card count="1" databaseID="60">
      <name>Scapelli, The Family "Mechanic"</name>
      <set>DS</set>
      <cost>3 pool</cost>
      <requirement>Giovanni</requirement>
      <type>Ally</type>
      <text>Unique {mortal} with 3 life. {0 strength}, 1 bleed.
{Scapelli may strike for 2R damage.} Once each combat, Scapelli may press to continue combat.</text>
    </card><card count="1" databaseID="52">
      <name>Path of Blood, The</name>
      <set>LotN</set>
      <cost>1 pool</cost>
      <requirement>Assamite</requirement>
      <type>Master</type>
      <text>Unique master.
Put this card in play. Cards that require Quietus [qui] {cost Assamites 1 less blood}. Any minion may burn this card as a (D) action; if that minion is a vampire, he or she then takes 1 unpreventable damage when this card is burned.</text>
    </card>
  </library>
</deck>""" % (WriteArdbXML.sDatabaseVersion, SutekhInfo.VERSION_STR)
# pylint: enable-msg=W0511, C0301


class ArdbXMLWriterTests(SutekhTest):
    """class for the ARDB deck XML writer tests"""

    def test_deck_writer(self):
        """Test ARDB XML deck writing"""
        oPhysCardSet1 = make_set_1()
        sCurDate = time.strftime('>%Y-%m-%d<', time.localtime())

        # Check output

        oWriter = WriteArdbXML()
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))
        sData = sData.replace(sCurDate, '>DATE<')

        self.assertEqual(sData, EXPECTED_1)

if __name__ == "__main__":
    unittest.main()
