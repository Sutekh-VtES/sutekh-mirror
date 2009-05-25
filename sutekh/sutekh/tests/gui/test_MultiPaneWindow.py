# test_MultiPaneWindow.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Test parts of the multipane window and config stuff"""

from sutekh.tests.TestCore import SutekhTest
from nose import SkipTest
import gtk
import unittest
import tempfile, os
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.gui.MultiPaneWindow import MultiPaneWindow
from sutekh.gui.ConfigFile import ConfigFile

class TestMultiPaneWindow(SutekhTest):
    """Class for the MultiPanewindow test cases"""

    def test_basic(self):
        """Set of simple tests of the MultiPaneWindow"""
        # Skip if we're not under a windowing system
        # We need to do this before trying to run MultiPaneWindow's __init__,
        # which will fail if not under a windowing system
        if gtk.gdk.screen_get_default() is None:
            raise SkipTest
        # Add card sets needed for the tests
        oPhysCardSet1 = PhysicalCardSet(name='My Collection')
        PhysicalCardSet(name='Test Set 1',
                parent=oPhysCardSet1)
        PhysicalCardSet(name='Test Set 2',
                parent=oPhysCardSet1)
        # Carry on with the test
        sConfigFile = self._create_tmp_file()
        oConfig = ConfigFile(sConfigFile)
        # Don't try and create a path in the user's home dir
        sImagesDir = tempfile.mkdtemp(suffix='dir', prefix='sutekhtests')
        oConfig.set_plugin_key('card image path', sImagesDir)
        oWin = MultiPaneWindow()
        oWin.setup(oConfig)
        # Check we have the correct panes in place
        self.assertNotEqual(oWin.find_pane_by_name('White Wolf Card List'),
            None)
        self.assertNotEqual(oWin.find_pane_by_name('Card Set List'), None)
        self.assertNotEqual(oWin.find_pane_by_name('My Collection'), None)
        self.assertNotEqual(oWin.find_pane_by_name('Card Text'), None)
        # Remove a pane
        oWin.remove_frame_by_name('Card Text')
        self.assertEqual(oWin.find_pane_by_name('Card Text'), None)
        # Check focus
        self.assertEqual(oWin.focussed_pane, None)
        oSetList = oWin.find_pane_by_name('Card Set List')
        oWin.win_focus(None, None, oSetList)
        self.assertEqual(oWin.focussed_pane, oSetList)
        # Replace frame
        oWin.replace_with_card_text(None)
        oText = oWin.find_pane_by_name('Card Text')
        self.assertNotEqual(oText, None)
        # Adding the pane will unset the focus
        self.assertEqual(oWin.focussed_pane, None)
        self.assertEqual(oWin.find_pane_by_name('Card Set List'), None)
        # Add a pane again
        oWin.add_new_pcs_list(None)
        self.assertEqual(oWin.focussed_pane, None)
        self.assertNotEqual(oWin.find_pane_by_name('Card Set List'), None)
        # Clean up
        oWin.destroy()
        # Process pending gtk events so cleanup completes
        while gtk.events_pending():
            gtk.main_iteration()
        os.rmdir(sImagesDir)

if __name__ == "__main__":
    unittest.main()
