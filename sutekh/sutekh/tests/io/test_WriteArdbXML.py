# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an ARDB deck XML file"""

import unittest
import time

from sutekh.base.core.CardSetHolder import CardSetWrapper

from sutekh.io.WriteArdbXML import WriteArdbXML
from sutekh.SutekhInfo import SutekhInfo
from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1

# pylint: disable=fixme, line-too-long
# this is not a actual TODO item
# Ignore line length limits for this string, since it's for testing
EXPECTED_1 = """<deck databaseVersion="%s" formatVersion="-TODO-1.0" generator="Sutekh [ %s ]">
  <date>DATE</date>
  <name>Test Set 1</name>
  <author>A test author</author>
  <description>A test comment</description>
  <crypt avg="6.00" max="9" min="3" size="6">
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
    </vampire><vampire count="1" databaseID="47">
      <adv />
      <name>Hektor</name>
      <set>Third</set>
      <disciplines>CEL POT PRE QUI for</disciplines>
      <clan>Brujah antitribu</clan>
      <capacity>9</capacity>
      <group>4</group>
      <title>Priscus</title>
      <text>Sabbat priscus: Damage from Hektor's hand strikes is aggravated. Baali get +1 bleed
when bleeding you.</text>
    </vampire><vampire count="1" databaseID="50">
      <adv />
      <name>Inez "Nurse216" Villagrande</name>
      <set>NoR</set>
      <disciplines>inn</disciplines>
      <clan>Imbued</clan>
      <capacity>3</capacity>
      <group>4</group>
      <text>When Inez enters play, you may search your library (shuffle afterward) or hand for a power that requires innocence and put it on her.</text>
    </vampire><vampire count="2" databaseID="75">
      <adv />
      <name>Siamese, The</name>
      <set>BL</set>
      <disciplines>PRE SPI ani pro</disciplines>
      <clan>Ahrimane</clan>
      <capacity>7</capacity>
      <group>2</group>
      <text>Sabbat: +1 bleed. Sterile.</text>
    </vampire>
  </crypt><library size="28">
    <card count="3" databaseID="1">
      <name>.44 Magnum</name>
      <set>CE</set>
      <cost>2 pool</cost>
      <type>Equipment</type>
      <text>Weapon, gun.
2R damage each strike, with an optional maneuver each combat.</text>
    </card><card count="1" databaseID="1">
      <name>.44 Magnum</name>
      <set>Jyhad</set>
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
      <name>Aaron\'s Feeding Razor</name>
      <set>KoT</set>
      <cost>1 pool</cost>
      <type>Equipment</type>
      <text>Unique.
The bearer gets +1 hunt.</text>
    </card><card count="2" databaseID="8">
      <name>Abbot</name>
      <set>Third</set>
      <type>Action</type>
      <text>+1 stealth action. Requires a Sabbat vampire.
Put this card on this acting Sabbat vampire and unlock him or her. This Sabbat vampire gets +1 intercept against (D) actions directed at his or her controller. A vampire may have only one Abbot.</text>
    </card><card count="2" databaseID="14">
      <name>Abombwe</name>
      <set>LoB</set>
      <type>Master</type>
      <text>Master: Discipline. Trifle.
Put this card on a Laibon or on a vampire with Protean [pro]. This vampire gains one level of Abombwe [abo]. Capacity increases by 1: the vampire is one generation older. Cannot be placed on a vampire with superior Abombwe.</text>
    </card><card count="3" databaseID="17">
      <name>Aire of Elation</name>
      <set>CE</set>
      <cost>1 blood</cost>
      <type>Action Modifier</type>
      <disciplines>PRE</disciplines>
      <text>You cannot play another action modifier to further increase the bleed for this action.
[pre] +1 bleed; +2 bleed if the acting vampire is Toreador. [PRE] +2 bleed; +3 bleed if the acting vampire is Toreador.</text>
    </card><card count="1" databaseID="26">
      <name>Anarch Manifesto, An</name>
      <set>TR</set>
      <type>Equipment</type>
      <text>Equipment.
The anarch with this equipment gets +1 stealth on actions that require an anarch. Titled non-anarch vampires get +1 strength in combat with this minion. A minion may have only one Anarch Manifesto.</text>
    </card><card count="1" databaseID="80">
      <name>Hide the Heart</name>
      <set>HttB</set>
      <type>Reaction</type>
      <disciplines>AUS VAL</disciplines>
      <text>[aus] Reduce a bleed against you by 1.
[val] The action ends (unsuccessfully). The acting minion may burn 1 blood to cancel this card as it is played. Only one Hide the Heart may be played at [val] each action. [VAL] Reduce a bleed against you by 2, or lock to reduce a bleed against any Methuselah by 2.</text>
    </card><card count="2" databaseID="49">
      <name>Immortal Grapple</name>
      <set>Jyhad</set>
      <type>Combat</type>
      <disciplines>POT</disciplines>
      <text>Only usable at close range before strikes are chosen. Grapple.
[pot] Strikes that are not hand strikes may not be used this round (by either combatant). A vampire may play only one Immortal Grapple each round. [POT] As above, with an optional press. If another round of combat occurs, that round is at close range; skip the determine range step for that round.</text>
    </card><card count="2" databaseID="49">
      <name>Immortal Grapple</name>
      <set>KoT</set>
      <type>Combat</type>
      <disciplines>POT</disciplines>
      <text>Only usable at close range before strikes are chosen. Grapple.
[pot] Strikes that are not hand strikes may not be used this round (by either combatant). A vampire may play only one Immortal Grapple each round. [POT] As above, with an optional press. If another round of combat occurs, that round is at close range; skip the determine range step for that round.</text>
    </card><card count="1" databaseID="70">
      <name>Scapelli, The Family "Mechanic"</name>
      <set>DS</set>
      <cost>3 pool</cost>
      <requirement>Giovanni</requirement>
      <type>Ally</type>
      <text>Unique {mortal} with 3 life. {0 strength}, 1 bleed.
{Scapelli may strike for 2R damage.} Once each combat, Scapelli may press to continue combat.</text>
    </card><card count="2" databaseID="74">
      <name>Swallowed by the Night</name>
      <set>Third</set>
      <type>Action Modifier/Combat</type>
      <disciplines>OBF</disciplines>
      <text>[obf] [ACTION MODIFIER] +1 stealth.
[OBF] [COMBAT] Maneuver.</text>
    </card><card count="1" databaseID="62">
      <name>Path of Blood, The</name>
      <set>LotN</set>
      <cost>1 pool</cost>
      <requirement>Assamite</requirement>
      <type>Master</type>
      <text>Unique master.
Put this card in play. Cards that require Quietus [qui] {cost Assamites 1 less blood}. Any minion may burn this card as a (D) action; if that minion is a vampire, he or she then takes 1 unpreventable damage when this card is burned.</text>
    </card><card count="1" databaseID="81">
      <name>Walk of Flame</name>
      <set>KoT</set>
      <type>Combat</type>
      <disciplines>THA</disciplines>
      <text>Not usable on the first round of combat.
[tha] Strike: 1R aggravated damage. [THA] Strike: 2R aggravated damage.</text>
    </card><card count="3" databaseID="81">
      <name>Walk of Flame</name>
      <set>Third</set>
      <type>Combat</type>
      <disciplines>THA</disciplines>
      <text>Not usable on the first round of combat.
[tha] Strike: 1R aggravated damage. [THA] Strike: 2R aggravated damage.</text>
    </card>
  </library>
</deck>""" % (WriteArdbXML.sDatabaseVersion, SutekhInfo.VERSION_STR)
# pylint: enable=fixme, line-too-long


class ArdbXMLWriterTests(SutekhTest):
    """class for the ARDB deck XML writer tests"""
    # pylint: disable=too-many-public-methods
    # unittest.TestCase, so many public methods

    def test_deck_writer(self):
        """Test ARDB XML deck writing"""
        oPhysCardSet1 = make_set_1()
        sCurDate = time.strftime('>%Y-%m-%d<', time.localtime())

        # Check output

        oWriter = WriteArdbXML()
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))
        sData = sData.replace(sCurDate, '>DATE<')

        self._compare_xml_strings(sData, EXPECTED_1)


if __name__ == "__main__":
    unittest.main()  # pragma: no cover
