# test_WriteArdbText.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test Writing a card set to an ARDB deck XML file"""

import time
from sutekh.tests.TestCore import SutekhTest
from sutekh.tests.core.test_PhysicalCardSet import make_set_1
from sutekh.core.CardSetHolder import CardSetWrapper
from sutekh.io.WriteVEKNForum import WriteVEKNForum
import unittest

# This doesn't match the ARDB export for the same card set, due to
# the outstanding issues in the Export implementation
VEKN_EXPECTED_1 = """[size=18][b]Deck Name : Test Set 1[/b][/size]
[b][u]Author :[/u][/b] A test author
[b][u]Description :[/u][/b]
A test comment

[size=18][u]Crypt [3 vampires] Capacity min: 4 max: 7 average: 5.67[/u][/size]
[table]
[tr][td]1x[/td][td][url=http://www.secretlibrary.info/?crypt=Siamese,+The]The Siamese[/url][/td][td][/td][td](7)[/td][td]:PRE: :SPI: :ani: :pro:[/td][td]   [/td][td]:ahri: Ahrimane[/td][td](group 2)[/td][/tr]
[tr][td]1x[/td][td][url=http://www.secretlibrary.info/?crypt=Alan+Sovereign+Adv]Alan Sovereign[/url][/td][td]Adv[/td][td](6)[/td][td]:AUS: :DOM: :for: :pre:[/td][td]   [/td][td]:vent: Ventrue[/td][td](group 3)[/td][/tr]
[tr][td]1x[/td][td][url=http://www.secretlibrary.info/?crypt=Abebe]Abebe[/url][/td][td][/td][td](4)[/td][td]:nec: :obf: :thn:[/td][td]   [/td][td]:same: Samedi[/td][td](group 4)[/td][/tr]
[/table]
[size=18][u]Library [11 cards][/u][/size]
[b][u]Action [2][/u][/b]
 2x [url=http://www.secretlibrary.info/?lib=Abbot]Abbot[/url]

[b][u]Equipment [6][/u][/b]
 4x [url=http://www.secretlibrary.info/?lib=.44+Magnum].44 Magnum[/url]
 2x [url=http://www.secretlibrary.info/?lib=AK-47]AK-47[/url]

[b][u]Master [3][/u][/b]
 2x [url=http://www.secretlibrary.info/?lib=Abombwe]Abombwe[/url]
 1x [url=http://www.secretlibrary.info/?lib=Path+of+Blood,+The]The Path of Blood[/url]


Recorded with : Sutekh 0.8.0a0 [ DATE ]
"""


class VEKNForumWriterTests(SutekhTest):
    """class for the ARDB text file writer tests"""

    def test_deck_writer(self):
        """Test ARDB text file writing"""
        oPhysCardSet1 = make_set_1()

        sCurDate = time.strftime('[ %Y-%m-%d ]', time.localtime())

        # Check output
        oWriter = WriteVEKNForum()
        sData = self._round_trip_obj(oWriter, CardSetWrapper(oPhysCardSet1))
        sData = sData.replace(sCurDate, '[ DATE ]')

        self.assertEqual(sData, VEKN_EXPECTED_1)


if __name__ == "__main__":
    unittest.main()
