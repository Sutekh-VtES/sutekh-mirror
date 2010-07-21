# CardSetManagementMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Menu for the CardSet View's
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Menu for the card set list"""

import gtk
from sutekh.gui.FilteredViewMenu import FilteredViewMenu
from sutekh.gui.CardSetManagementProfileEditor import \
        CardSetManagementProfileEditor
from sutekh.gui.ConfigFile import CARDSET_LIST

class CardSetManagementMenu(FilteredViewMenu):
    """Card Set List Management menu.
       """
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    def __init__(self, oFrame, oWindow, oController):
        super(CardSetManagementMenu, self).__init__(oFrame, oWindow,
                oController)
        self.__sName = 'Card Set List'
        self.__sSetTypeName = 'Card Set'
        self._oController = oController
        self._oCardSetlistProfileMenu = None
        self.__create_actions_menu()
        self.create_edit_menu()
        self.create_filter_menu()
        self.add_plugins_to_menus(self._oFrame)

    # pylint: disable-msg=W0201
    # called from __init__, so OK
    def __create_actions_menu(self):
        """Add the Actions Menu"""
        oMenu  = self.create_submenu(self, "_Actions")
        self.create_menu_item('Create New Card Set', oMenu,
                self._oController.create_new_card_set)
        self.create_menu_item('Edit Card Set Properties', oMenu,
                self._oController.edit_card_set_properties)
        self.create_menu_item('Mark/UnMark Card Set as in use', oMenu,
                    self._oController.toggle_in_use_flag)
        self.create_menu_item('Delete selected Card Set', oMenu,
                self._oController.delete_card_set, 'Delete')
        oMenu.add(gtk.SeparatorMenuItem())
        self.add_common_actions(oMenu)

    # pylint: enable-msg=W0201

    def create_edit_menu(self):
        """Create the edit menu and populate it"""
        oMenu = self.create_submenu(self, "_Edit")

        self.create_menu_item('Edit _Profiles', oMenu, self._edit_profiles)

        sProfile = self._oMainWindow.config_file.get_profile(CARDSET_LIST,
                CARDSET_LIST)
        self._oCardSetlistProfileMenu = self._create_profile_menu(oMenu,
            "CardSet list Profile", self._select_cardset_list_profile,
            sProfile)

        self.add_edit_menu_actions(oMenu)

    def _create_profile_menu(self, oParentMenu, sTitle, fCallback, sProfile):
        """Create a radio group sub-menu for selecting a profile."""
        oMenu = self.create_submenu(oParentMenu, sTitle)
        oConfig = self._oMainWindow.config_file

        oGroup = gtk.RadioMenuItem(None,
            oConfig.get_profile_option(CARDSET_LIST, None, "name"))
        oGroup.connect("toggled", fCallback, None)
        oMenu.append(oGroup)

        self._update_profile_group(oMenu, fCallback, sProfile)

        return oMenu

    def _update_profile_group(self, oMenu, fCallback, sProfile):
        """Update the profile selection menu"""
        oConfig = self._oMainWindow.config_file
        oGroup = oMenu.get_children()[0]

        aProfiles = [(sKey, oConfig.get_profile_option(CARDSET_LIST, sKey,
            "name"))
            for sKey in oConfig.cardset_list_profiles()]
        aProfiles.sort(key=lambda tProfile: tProfile[1])

        if sProfile is None or sProfile == 'Default':
            oGroup.set_active(True)

        # clear out existing radio items
        for oRadio in oGroup.get_group():
            if oRadio is not oGroup:
                oRadio.set_group(None)
                oMenu.remove(oRadio)

        for sKey, sName in aProfiles:
            oRadio = gtk.RadioMenuItem(oGroup, sName)
            oRadio.connect("toggled", fCallback, sKey)
            if sKey == sProfile:
                oRadio.set_active(True)
            oMenu.append(oRadio)
            oRadio.show()


    def _edit_profiles(self, _oWidget):
        """Open an options profiles editing dialog."""
        oDlg = CardSetManagementProfileEditor(self._oMainWindow,
            self._oMainWindow.config_file)
        oDlg.run()

        sProfile = self._oMainWindow.config_file.get_profile(CARDSET_LIST,
                CARDSET_LIST)
        self._update_profile_group(self._oCardSetlistProfileMenu,
            self._select_cardset_list_profile, sProfile)

    def _select_cardset_list_profile(self, oRadio, sProfileKey):
        """Callback to change the profile of the current card set."""
        if oRadio.get_active():
            oConfig = self._oMainWindow.config_file
            oConfig.set_profile(CARDSET_LIST, CARDSET_LIST, sProfileKey)

