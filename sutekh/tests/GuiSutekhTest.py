# GuiSutekhTest.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Base for Sutekh test cases that use gtk windows"""

from sutekh.tests.TestCore import SutekhTest
from nose import SkipTest
import gtk
import tempfile, os
from sutekh.gui.MultiPaneWindow import MultiPaneWindow
from sutekh.gui.ConfigFile import ConfigFile

class ConfigSutekhTest(SutekhTest):
    """Base class for Sutekh tests that need a config file.

       Defines common startUp and tearDown routines."""
    # pylint: disable-msg=C0103
    # setUp + tearDown names are needed by unittest - use their convention

    def setUp(self):
        """Setup config file for the tests"""
        super(ConfigSutekhTest, self).setUp()
        # Carry on with the test
        sConfigFile = self._create_tmp_file()
        self.oConfig = ConfigFile(sConfigFile)
        # Don't try and create a path in the user's home dir
        self.sImagesDir = tempfile.mkdtemp(suffix='dir', prefix='sutekhtests')
        self.oConfig.set_plugin_key('card image path', self.sImagesDir)
        self.oConfig.set_plugin_key('show starters', 'No')

    def tearDown(self):
        """Tear down config file stuff after test run"""
        os.rmdir(self.sImagesDir)
        super(ConfigSutekhTest, self).tearDown()

class GuiSutekhTest(ConfigSutekhTest):
    """Base class for Sutekh tests that use the main window.

       Define common setup and teardown routines common to gui test cases.
       """
    # pylint: disable-msg=C0103
    # setUp + tearDown names are needed by unittest - use their convention

    def setUp(self):
        """Setup gtk window for the tests"""
        # Skip if we're not under a windowing system
        # We need to do this before trying to run MultiPaneWindow's __init__,
        # which will fail if not under a windowing system
        if gtk.gdk.screen_get_default() is None:
            raise SkipTest
        super(GuiSutekhTest, self).setUp()
        # Carry on with the test
        self.oWin = MultiPaneWindow()

    def tearDown(self):
        """Tear down gtk framework after test run"""
        self.oWin.destroy()
        # Process pending gtk events so cleanup completes
        while gtk.events_pending():
            gtk.main_iteration()
        super(GuiSutekhTest, self).tearDown()
