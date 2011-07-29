# PhysicalCardMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Menu for the Physical Card View
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Menu for the Physical card collection."""

import gtk
from sutekh.gui.FilteredViewMenu import CardListMenu
from sutekh.gui.FrameProfileEditor import FrameProfileEditor
from sutekh.gui.ConfigFile import ConfigFileListener, WW_CARDLIST


class PhysicalCardMenu(CardListMenu, ConfigFileListener):
    """Menu for the Physical card collection.

       Enables actions specific to the physical card collection (export to
       file, etc), filtering and plugins.
       """
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    def __init__(self, oFrame, oController, oWindow):
        super(PhysicalCardMenu, self).__init__(oFrame, oWindow, oController)
        self.__create_physical_cl_menu()
        self.create_edit_menu()
        self.create_filter_menu()
        self.create_analyze_menu()
        self.add_plugins_to_menus(self._oFrame)
        self.sort_menu(self._dMenus['Analyze'])

    # pylint: disable-msg=W0201
    # called from __init__, so OK
    def __create_physical_cl_menu(self):
        """Create the Actions menu for the card list."""
        # setup sub menu
        oMenu = self.create_submenu(self, "_Actions")

        # items
        self.create_check_menu_item('Show Card Expansions', oMenu,
                self._oController.toggle_expansion, True)

        self.create_check_menu_item('Show icons for the grouping',
                oMenu, self._oController.toggle_icons, True)

        oMenu.add(gtk.SeparatorMenuItem())
        self.add_common_actions(oMenu)

    def create_edit_menu(self):
        """Create the edit menu and populate it"""
        oMenu = self.create_submenu(self, "_Edit")
        self.create_menu_item('Copy selection', oMenu, self.copy_selection,
                '<Ctrl>c')

        self.create_menu_item('Edit _Profiles', oMenu, self._edit_profiles)

        sProfile = self._oMainWindow.config_file.get_profile(WW_CARDLIST,
                WW_CARDLIST)
        self._oCardlistProfileMenu = self._create_profile_menu(oMenu,
            "Cardlist Profile", WW_CARDLIST, self._select_cardlist_profile,
            sProfile)

        self._oMainWindow.config_file.add_listener(self)

        self.add_edit_menu_actions(oMenu)

    def cleanup(self):
        """Remove the menu listener"""
        self._oMainWindow.config_file.remove_listener(self)

    def _edit_profiles(self, _oWidget):
        """Open an options profiles editing dialog."""
        oDlg = FrameProfileEditor(self._oMainWindow,
            self._oMainWindow.config_file, WW_CARDLIST)
        sCurProfile = self._oMainWindow.config_file.get_profile(WW_CARDLIST,
            WW_CARDLIST)
        oDlg.set_selected_profile(sCurProfile)
        oDlg.run()

        self._fix_profile_menu()

    def _fix_profile_menu(self):
        """Set the profile menu correctly"""
        sProfile = self._oMainWindow.config_file.get_profile(WW_CARDLIST,
                WW_CARDLIST)
        self._update_profile_group(self._oCardlistProfileMenu, WW_CARDLIST,
            self._select_cardlist_profile, sProfile)

    def _select_cardlist_profile(self, oRadio, sProfileKey):
        """Callback to change the profile of the current card set."""
        if oRadio.get_active():
            oConfig = self._oMainWindow.config_file
            oConfig.set_profile(WW_CARDLIST, WW_CARDLIST, sProfileKey)

    # Respond to profile changes

    def remove_profile(self, sType, _sProfile):
        """A profile has been removed"""
        if sType == WW_CARDLIST:
            self._fix_profile_menu()

    def profile_option_changed(self, sType, _sProfile, sKey):
        """Update menu if profiles are renamed."""
        if sType == WW_CARDLIST and sKey == 'name':
            self._fix_profile_menu()
