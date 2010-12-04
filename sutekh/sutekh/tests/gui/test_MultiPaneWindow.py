# test_MultiPaneWindow.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test parts of the multipane window and config stuff"""

import unittest
from sutekh.tests.GuiSutekhTest import GuiSutekhTest
from sutekh.core.SutekhObjects import PhysicalCardSet


class TestMultiPaneWindow(GuiSutekhTest):
    """Class for the MultiPanewindow test cases"""

    def test_basic(self):
        """Set of simple tests of the MultiPaneWindow"""
        # Add card sets needed for the tests
        oPhysCardSet1 = PhysicalCardSet(name='My Collection')
        PhysicalCardSet(name='Test Set 1',
                parent=oPhysCardSet1)
        PhysicalCardSet(name='Test Set 2',
                parent=oPhysCardSet1)
        self.oWin.setup(self.oConfig)
        # Check we have the correct panes in place
        self.assertTrue(
                self.oWin.is_open_by_menu_name('White Wolf Card List'))
        self.assertTrue(self.oWin.is_open_by_menu_name('Card Set List'))
        self.assertTrue(self.oWin.is_open_by_menu_name('Card Text'))
        self.assertNotEqual(
                self.oWin.find_cs_pane_by_set_name('My Collection'), [])
        # Remove a pane
        for oPane in self.oWin.aOpenFrames[:]:
            if oPane.title == 'Card Text':
                self.oWin.remove_frame(oPane)
            if oPane.title == 'Card Set List':
                oSetList = oPane
        self.assertFalse(self.oWin.is_open_by_menu_name('Card Text'))
        # Check focus
        self.assertEqual(self.oWin.focussed_pane, None)
        self.oWin.win_focus(None, None, oSetList)
        self.assertEqual(self.oWin.focussed_pane, oSetList)
        # Replace frame
        self.oWin.replace_with_card_text(None)
        self.assertTrue(self.oWin.is_open_by_menu_name('Card Text'))
        # Adding the pane will unset the focus
        self.assertEqual(self.oWin.focussed_pane, None)
        self.assertFalse(self.oWin.is_open_by_menu_name('Card Set List'))
        # Add a pane again
        self.oWin.add_new_pcs_list(None)
        self.assertEqual(self.oWin.focussed_pane, None)
        self.assertTrue(self.oWin.is_open_by_menu_name('Card Set List'))
        # Check that we can add multiple copies of My Collection
        self.oWin.add_new_physical_card_set('My Collection')
        self.assertEqual(len(
            self.oWin.find_cs_pane_by_set_name('My Collection')), 2)
        self.oWin.add_new_physical_card_set('My Collection')
        self.assertEqual(len(
            self.oWin.find_cs_pane_by_set_name('My Collection')), 3)
        oPane = self.oWin.find_cs_pane_by_set_name('My Collection')[0]
        self.oWin.remove_frame(oPane)
        self.assertEqual(len(
            self.oWin.find_cs_pane_by_set_name('My Collection')), 2)
        oPane = self.oWin.find_cs_pane_by_set_name('My Collection')[0]
        self.oWin.minimize_to_toolbar(oPane)
        self.assertEqual(len(self.oWin.aClosedFrames), 1)
        self.assertEqual(len(self.oWin.aOpenFrames), 4)
        self.assertTrue(oPane in self.oWin.aClosedFrames)
        self.assertFalse(oPane in self.oWin.aOpenFrames)
        self.oWin.save_frames()
        self.oWin.remove_frame(oPane)
        self.assertEqual(len(self.oWin.aClosedFrames), 0)
        self.oWin.restore_from_config()
        self.assertEqual(len(self.oWin.aClosedFrames), 1)
        self.assertEqual(len(self.oWin.aOpenFrames), 4)
        self.assertEqual(len(
            self.oWin.find_cs_pane_by_set_name('My Collection')), 2)

if __name__ == "__main__":
    unittest.main()
