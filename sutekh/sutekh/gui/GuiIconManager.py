# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""GTK gui icon manager."""

import os

from gi.repository import Gtk

from sutekh.base.Utility import prefs_dir, ensure_dir_exists
from sutekh.base.gui.SutekhDialog import do_complaint
from sutekh.base.gui.CachedIconManager import CachedIconManager

from sutekh.io.IconManager import IconManager
from sutekh.SutekhInfo import SutekhInfo


class GuiIconManager(CachedIconManager, IconManager):
    """Gui Manager for the VTES Icons.

       Also provides gui interface for setup
       """

    # pylint: disable=abstract-method
    # pylint doesn't follow the mro correctly here, so doesn't
    # see that IconManager provides the required methods.
    def __init__(self, sPath):
        if not sPath:
            sPath = os.path.join(prefs_dir(SutekhInfo.NAME), 'icons')
        super().__init__(sPath)

    def setup(self):
        """Prompt the user to download the icons if the icon directory
           doesn't exist"""
        if os.path.lexists(self._sPrefsDir):
            # We accept broken links as stopping the prompt
            if os.path.lexists("%s/clans" % self._sPrefsDir):
                return
            # Check if we need to upgrade to the V:EKN icons
            ensure_dir_exists("%s/clans" % self._sPrefsDir)
            if os.path.exists('%s/IconClanAbo.gif' % self._sPrefsDir):
                iResponse = do_complaint(
                    "Sutekh has switched to using the icons from the "
                    "V:EKN site.\nIcons won't work until you "
                    "re-download them.\n\nDownload icons?",
                    Gtk.MessageType.INFO, Gtk.ButtonsType.YES_NO, False)
            else:
                # Old icons not present, so skip
                return
        else:
            # Create directory, so we don't prompt next time unless the user
            # intervenes
            ensure_dir_exists(self._sPrefsDir)
            ensure_dir_exists("%s/clans" % self._sPrefsDir)
            # Ask the user if he wants to download
            iResponse = do_complaint("Sutekh can download icons for the cards "
                                     "from the V:EKN site\nThese icons will "
                                     "be stored in %s\n\nDownload icons?"
                                     % self._sPrefsDir,
                                     Gtk.MessageType.INFO,
                                     Gtk.ButtonsType.YES_NO,
                                     False)
        if iResponse == Gtk.ResponseType.YES:
            self.download_with_progress()
        else:
            # Let the user know about the other options
            do_complaint("Icon download skipped.\nYou can choose to download "
                         "the icons from the File menu.\nYou will not be"
                         " prompted again unless you delete %s"
                         % self._sPrefsDir,
                         Gtk.MessageType.INFO, Gtk.ButtonsType.CLOSE, False)
