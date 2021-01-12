# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Menu for the CardSet View's
# Copyright 2019 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Menu for the card set pane"""

import logging

from gi.repository import Gtk

from .SutekhMenu import SutekhMenu
from .SutekhFileWidget import ExportDialog


class LogViewMenu(SutekhMenu):
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods
    """Log View Menu.

       Provides options for filtering the log messages on severity,
       and an options to export the current filtered list to a file.
       """
    def __init__(self, oFrame, oWindow):
        super().__init__(oWindow)
        self._oLogFrame = oFrame
        self._create_actions_menu()

    # pylint: disable=attribute-defined-outside-init
    # these methods are called from __init__, so it's OK
    def _create_actions_menu(self):
        """Create the Actions menu for Card Sets."""
        oMenu = self.create_submenu(self, 'Actions')
        oFilterList = self.create_submenu(oMenu, 'Filter log level')
        self._create_filter_list(oFilterList)
        oMenu.add(Gtk.SeparatorMenuItem())
        self.create_menu_item("_Save current view to File", oMenu,
                              self._save_to_file)

    def _create_filter_list(self, oSubMenu):
        """Create list of 'Filter' radio options."""
        oAll = Gtk.RadioMenuItem(group=None, label="Show all log messages")
        oInfo = Gtk.RadioMenuItem(group=oAll,
                                  label="Ignore debugging log messages")
        oWarn = Gtk.RadioMenuItem(group=oAll,
                                  label="Also Ignore Info messages")
        oError = Gtk.RadioMenuItem(group=oAll,
                                   label="Only show Error log messages")

        oAll.connect('activate', self._change_log_level, logging.NOTSET)
        oInfo.connect('activate', self._change_log_level, logging.INFO)
        oWarn.connect('activate', self._change_log_level, logging.WARN)
        oError.connect('activate', self._change_log_level, logging.ERROR)

        oAll.set_active(True)

        oSubMenu.add(oAll)
        oSubMenu.add(oInfo)
        oSubMenu.add(oWarn)
        oSubMenu.add(oError)

    # pylint: enable=attribute-defined-outside-init

    def _save_to_file(self, _oWidget):
        """Popup the Save File dialog."""
        oDlg = ExportDialog("Save logs as", self._oMainWindow)
        oDlg.add_filter_with_pattern("TXT files", ['*.txt'])
        oDlg.run()
        self._oLogFrame.view.save_to_file(oDlg.get_name())

    def _change_log_level(self, _oWidget, iNewLevel):
        """Pass the new log level to the view"""
        self._oLogFrame.set_filter_level(iNewLevel)
