# test_ConfigFileLegacy.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2010 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Tests the legacy config file support"""

from sutekh.tests.TestCore import SutekhTest
from sutekh.gui.ConfigFileLegacy import ConfigFileLegacy
from sutekh.gui.ConfigFile import CARDSET, CARDSET_LIST, FRAME, WW_CARDLIST


EMPTY_LEGACY_CONFIG = """
"""

BASIC_LEGACY_CONFIG = """
[Pane settings]
pane 4 = 1:0:1:My Collection

[GUI Preferences]
window size = 1429, 826
show zero count cards = no
save on exit = yes
database url = sqlite:///home/user/.sutekh/sutekh.db
postfix name display = yes
save window size = yes
save pane sizes = yes

[Plugin Options]
html export mode = Secret Library
show starters = No
card image path = /home/user/.sutekh/cardimages

[Filters]
test filter = Clan in Malkavian

[Open Panes]
pane 4 = physical_card_set.340:My Collection
pane 5 = physical_card.435:White Wolf Card List
pane 1 = Card Set List:Card Set List
pane 2 = Card Text.209:Card Text
pane 3 = Card Image Frame.V.306:Card Image Frame
"""


class ConfigFileLegacyTests(SutekhTest):
    """Tests for the legacy config file support."""

    def _convert_config(self, sConfigData):
        """Run the config update code"""
        sLegacyConf = self._create_tmp_file(sConfigData)
        sNewConf = self._create_tmp_file()
        oLegacyConf = ConfigFileLegacy(sLegacyConf)
        oConfig = oLegacyConf.convert(sNewConf)
        return oConfig, oLegacyConf

    def _check_global_options(self, oNew, oOld):
        """Check that the global options are converted correctly"""
        for sMethod in ('get_database_uri', 'get_icon_path',
                'get_postfix_the_display', 'get_save_on_exit',
                'get_save_precise_pos', 'get_save_window_size',
                'get_window_size'):
            sNewValue = getattr(oNew, sMethod)()
            sOldValue = getattr(oOld, sMethod)()
            self.assertEqual(sNewValue, sOldValue)

    def test_empty_import(self):
        """Test updating from an empty config file"""
        oConfig, oLegacyConfig = self._convert_config(EMPTY_LEGACY_CONFIG)

        self._check_global_options(oConfig, oLegacyConfig)

        self.assertEqual(oConfig.open_frames(), [
            (1, 'physical_card', 'White Wolf Card List', None, False, False,
                -1),
            (2, 'Card Text', 'Card Text', None, False, False, -1),
            (3, 'Card Set List', 'Card Set List', None, False, False, -1),
            (4, 'physical_card_set', 'My Collection', None, False, False, -1),
        ])

        self.assertEqual(oConfig.get_filter_keys(), [])

        self.assertEqual(oConfig.profiles(CARDSET), [])
        self.assertEqual(oConfig.profiles(CARDSET_LIST), [])
        self.assertEqual(oConfig.profiles(FRAME), [])
        self.assertEqual(oConfig.profiles(WW_CARDLIST), [])

    def test_basic_import(self):
        """Test converting a simple old config file"""
        oConfig, oLegacyConfig = self._convert_config(BASIC_LEGACY_CONFIG)

        self._check_global_options(oConfig, oLegacyConfig)
        self.assertEqual(oConfig.open_frames(), [
            (1, 'Card Set List', 'Card Set List', None, False, False, -1),
            (2, 'Card Text', 'Card Text', None, False, False, 209),
            (3, 'Card Image Frame', 'Card Image Frame', None, True, False,
                306),
            (4, 'physical_card_set', 'My Collection', None, False, False, 340),
            (5, 'physical_card', 'White Wolf Card List', None, False, False,
                435),
        ])

        self.assertEqual(oConfig.get_filter_keys(),
                [("test filter", "Clan in Malkavian")])
        self.assertEqual(oConfig.get_filter_values("test filter"), {})

        self.assertEqual(oConfig.profiles(CARDSET), [])
        self.assertEqual(oConfig.profiles(CARDSET_LIST), [])
        self.assertEqual(oConfig.profiles(FRAME), [])
        self.assertEqual(oConfig.profiles(WW_CARDLIST), [])

        for sPlugin, sKey in [
            ('card image path', 'CardImagePlugin'),
            ('HTML export mode', 'CardSetExportHTML'),
            ('show starters', 'StarterInfoPlugin'),
            ]:
            self.assertEqual(oConfig.get_plugin_key(sPlugin, sKey),
                oLegacyConfig.get_plugin_key(sKey))
