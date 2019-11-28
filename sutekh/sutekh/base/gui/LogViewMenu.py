# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Menu for the CardSet View's
# Copyright 2019 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Menu for the card set pane"""

import gtk

from .SutekhMenu import SutekhMenu


class LogViewMenu(SutekhMenu):
    # pylint: disable=too-many-public-methods
    # gtk.Widget, so many public methods
    # pylint: disable=property-on-old-class
    # gtk classes aren't old-style, but pylint thinks they are
    """Log View Menu.

       Provides options for filtering the log messages on severity,
       and an options to export the current filtered list to a file.
       """
    def __init__(self, oFrame, oWindow):
        super(LogViewMenu, self).__init__(oWindow)
        self._oLogFrame = oFrame
        self._create_actions_menu()

    # pylint: disable=attribute-defined-outside-init
    # these methods are called from __init__, so it's OK
    def _create_actions_menu(self):
        """Create the Actions menu for Card Sets."""
        oMenu = self.create_submenu(self, '_Actions')
        oFilterList = self.create_submenu(oMenu, '_Filter log level')
        self._create_filter_list(oFilterList)
        oMenu.add(gtk.SeparatorMenuItem())
        self.create_menu_item("_Save current view to File", oMenu,
                              self._save_to_file)

    def _create_filter_list(self, oSubMenu):
        """Create list of 'Filter' radio options."""

    # pylint: enable=attribute-defined-outside-init

    def _save_to_file(self, _oWidget):
        """Popup the Save File dialog."""
        # self._oFrame.save_to_file()
