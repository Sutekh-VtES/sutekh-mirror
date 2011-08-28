# test_WriteArdbText.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an VEKN bbcode file"""

import time
from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1
from sutekh.core.CardSetHolder import CardSetWrapper
from sutekh.io.WriteVEKNForum import WriteVEKNForum
from sutekh.SutekhInfo import SutekhInfo
import unittest

VEKN_EXPECTED_1 = """[size=18][b]Deck Name : Test Set 1[/b][/size]
[b][u]Author :[/u][/b] A test author
[b][u]Description :[/u][/b]
A test comment

[size=18][u]Crypt [4 vampires] Capacity min: 3 max: 7 average: 5.00[/u][/size]
[table]
[tr][td]1x[/td][td][url=http://www.secretlibrary.info/?crypt=Siamese,+The]The Siamese[/url][/td][td][/td][td](7)[/td][td]:PRE: :SPI: :ani: :pro:[/td][td]   [/td][td]:ahri: Ahrimane[/td][td](group 2)[/td][/tr]
[tr][td]1x[/td][td][url=http://www.secretlibrary.info/?crypt=Alan+Sovereign+Adv]Alan Sovereign[/url][/td][td]Adv[/td][td](6)[/td][td]:AUS: :DOM: :for: :pre:[/td][td]   [/td][td]:vent: Ventrue[/td][td](group 3)[/td][/tr]
[tr][td]1x[/td][td][url=http://www.secretlibrary.info/?crypt=Abebe]Abebe[/url][/td][td][/td][td](4)[/td][td]:nec: :obf: :thn:[/td][td]   [/td][td]:same: Samedi[/td][td](group 4)[/td][/tr]
[tr][td]1x[/td][td][url=http://www.secretlibrary.info/?crypt=Inez+Nurse216+Villagrande]Inez "Nurse216" Villagrande[/url][/td][td][/td][td](3)[/td][td]:inn:[/td][td]   [/td][td]:inno: Innocent (Imbued)[/td][td](group 4)[/td][/tr]
[/table]
[size=18][u]Library [13 cards][/u][/size]
[b][u]Action [2][/u][/b]
 2x [url=http://www.secretlibrary.info/?lib=Abbot]Abbot[/url]

[b][u]Ally [1][/u][/b]
 1x [url=http://www.secretlibrary.info/?lib=Scapelli,+The+Family+Mechanic]Scapelli, The Family "Mechanic"[/url]

[b][u]Equipment [7][/u][/b]
 4x [url=http://www.secretlibrary.info/?lib=.44+Magnum].44 Magnum[/url]
 2x [url=http://www.secretlibrary.info/?lib=AK-47]AK-47[/url]
 1x [url=http://www.secretlibrary.info/?lib=Aaron's+Feeding+Razor]Aaron's Feeding Razor[/url]

[b][u]Master [3][/u][/b]
 2x [url=http://www.secretlibrary.info/?lib=Abombwe]Abombwe[/url]
 1x [url=http://www.secretlibrary.info/?lib=Path+of+Blood,+The]The Path of Blood[/url]


Recorded with : Sutekh %s [ DATE ]
""" % SutekhInfo.VERSION_STR


class VEKNForumWriterTests(SutekhTest):
    """class for the VEKN bbcode file writer tests"""

    def test_deck_writer(self):
        """Test VEKN bbcode file writing"""
        oPhysCardSet1 = make_set_1()

        sCurDate = time.strftime('[ %Y-%m-%d ]', time.localtime())

        # Check output
        oWriter = WriteVEKNForum()
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))
        sData = sData.replace(sCurDate, '[ DATE ]')

        self.assertEqual(sData, VEKN_EXPECTED_1)


if __name__ == "__main__":
    unittest.main()
