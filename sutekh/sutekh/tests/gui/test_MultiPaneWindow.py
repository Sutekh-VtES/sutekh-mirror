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
        self.assertNotEqual(
                self.oWin.find_pane_by_name('White Wolf Card List'), None)
        self.assertNotEqual(self.oWin.find_pane_by_name('Card Set List'), None)
        self.assertNotEqual(self.oWin.find_pane_by_name('My Collection'), None)
        self.assertNotEqual(self.oWin.find_pane_by_name('Card Text'), None)
        # Remove a pane
        self.oWin.remove_frame_by_name('Card Text')
        self.assertEqual(self.oWin.find_pane_by_name('Card Text'), None)
        # Check focus
        self.assertEqual(self.oWin.focussed_pane, None)
        oSetList = self.oWin.find_pane_by_name('Card Set List')
        self.oWin.win_focus(None, None, oSetList)
        self.assertEqual(self.oWin.focussed_pane, oSetList)
        # Replace frame
        self.oWin.replace_with_card_text(None)
        oText = self.oWin.find_pane_by_name('Card Text')
        self.assertNotEqual(oText, None)
        # Adding the pane will unset the focus
        self.assertEqual(self.oWin.focussed_pane, None)
        self.assertEqual(self.oWin.find_pane_by_name('Card Set List'), None)
        # Add a pane again
        self.oWin.add_new_pcs_list(None)
        self.assertEqual(self.oWin.focussed_pane, None)
        self.assertNotEqual(self.oWin.find_pane_by_name('Card Set List'), None)

if __name__ == "__main__":
    unittest.main()
