# CardSetMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Menu for the CardSet View's
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Menu for the card set pane"""

import gtk
from sutekh.SutekhUtility import safe_filename
from sutekh.gui.SutekhFileWidget import ExportDialog
from sutekh.io.XmlFileHandling import PhysicalCardSetXmlFile
from sutekh.gui.FilteredViewMenu import CardListMenu
from sutekh.gui.FrameProfileEditor import FrameProfileEditor
from sutekh.gui.LocalProfileEditor import LocalProfileEditor
from sutekh.gui.ConfigFile import CARDSET, FRAME

class CardSetMenu(CardListMenu):
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    """Card Set Menu.

       Provide the usual menu options, and implement several of the
       card set specific actions - editing card set properties, editng
       annotations, exporting to file, and so on.
       """
    # pylint: disable-msg=R0902
    # R0902 - we are keeping a lot of state, so many instance variables
    def __init__(self, oFrame, oController, oWindow):
        super(CardSetMenu, self).__init__(oFrame, oWindow, oController)
        self.__create_card_set_menu()
        self.create_edit_menu()
        self.create_filter_menu()
        self.create_analyze_menu()
        self.add_plugins_to_menus(self._oFrame)
        self.sort_menu(self._dMenus['Export Card Set'])
        self.sort_menu(self._dMenus['Analyze'])

    # pylint: disable-msg=W0212
    # We allow access via these properties
    name = property(fget=lambda self: self._oController.view.sSetName,
            doc="Associated Card Set Name")

    frame_id = property(fget=lambda self: self._oController.model.frame_id,
            doc="Frame ID of associated card set (for selecting profiles)")

    cardset_id = property(fget=lambda self: self._oController.model.cardset_id,
            doc="Cardset ID of associated card set (for selecting profiles)")

    #pylint: enable-msg=W0212


    # pylint: disable-msg=W0201
    # these methods are called from __init__, so it's OK
    def __create_card_set_menu(self):
        """Create the Actions menu for Card Sets."""
        oMenu = self.create_submenu(self, '_Actions')
        self.create_menu_item("Edit Card Set _Properties", oMenu,
                self._edit_properties)
        self.create_menu_item("_Save Card Set to File", oMenu,
                self._do_export)
        # Submenu for plugins
        self.create_submenu(oMenu, "_Export Card Set")

        oMenu.add(gtk.SeparatorMenuItem())
        self.add_common_actions(oMenu)

        oMenu.add(gtk.SeparatorMenuItem())
        self.create_menu_item("Delete Card Set", oMenu, self._card_set_delete)

    def create_edit_menu(self):
        """Create the 'Edit' menu, and populate it."""
        oMenu = self.create_submenu(self, "_Edit")
        self._oEditable = self.create_check_menu_item('Card Set is Editable',
                oMenu, self.toggle_editable, False, '<Ctrl>e')
        self._oController.view.set_menu(self)
        self.create_menu_item('Copy selection', oMenu, self.copy_selection,
                '<Ctrl>c')
        self._oPaste = self.create_menu_item('Paste', oMenu,
                self._paste_selection, '<Ctrl>v')
        self._oDel = self.create_menu_item('Delete selection', oMenu,
                self._del_selection, 'Delete')
        self._oPaste.set_sensitive(False)
        self._oDel.set_sensitive(False)

        self.create_menu_item('Edit _Local Profile', oMenu,
            self._edit_local_profile)
        self.create_menu_item('Edit _Profiles', oMenu, self._edit_profiles)

        sCardsetProfile = self._oMainWindow.config_file.get_profile(CARDSET,
            self.cardset_id)
        self._oCardsetProfileMenu = self._create_profile_menu(oMenu,
            "Cardset Profile", self._select_cardset_profile, sCardsetProfile)

        sFrameProfiles = self._oMainWindow.config_file.get_profile(FRAME,
            self.frame_id)
        self._oFrameProfileMenu = self._create_profile_menu(oMenu,
            "Pane Profile", self._select_frame_profile, sFrameProfiles)

        self.add_edit_menu_actions(oMenu)

    def _create_profile_menu(self, oParentMenu, sTitle, fCallback, sProfile):
        """Create a radio group sub-menu for selecting a profile."""
        oMenu = self.create_submenu(oParentMenu, sTitle)
        oConfig = self._oMainWindow.config_file

        oGroup = gtk.RadioMenuItem(None,
            oConfig.get_deck_profile_option(None, "name"))
        oGroup.connect("toggled", fCallback, None)
        oMenu.append(oGroup)

        self._update_profile_group(oMenu, fCallback, sProfile)

        return oMenu

    def _update_profile_group(self, oMenu, fCallback, sProfile):
        oConfig = self._oMainWindow.config_file
        oGroup = oMenu.get_children()[0]

        aProfiles = [(sKey, oConfig.get_deck_profile_option(sKey, "name")) \
            for sKey in oConfig.profiles()]
        aProfiles.sort(key=lambda tProfile: tProfile[1])

        if sProfile is None:
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

    # pylint: enable-msg=W0201

    def _edit_properties(self, _oWidget):
        """Popup the Edit Properties dialog to change card set properties."""
        # pylint: disable-msg=E1101
        # sqlobject confuses pylint
        self._oController.edit_properties(self)

    def update_card_set_menu(self, oCardSet):
        """Update the menu to reflect changes in the card set name."""
        sNewName = oCardSet.name
        self._oFrame.update_name(sNewName)
        self._oController.view.update_name(sNewName)

    def _do_export(self, _oWidget):
        """Export the card set to the chosen filename."""
        oFileChooser = ExportDialog("Save Card Set As ", self._oMainWindow,
                '%s.xml' % safe_filename(self.name))
        oFileChooser.add_filter_with_pattern('XML Files', ['*.xml'])
        oFileChooser.run()
        sFileName = oFileChooser.get_name()
        if sFileName is not None:
            # User has OK'd us overwriting anything
            oWriter = PhysicalCardSetXmlFile(sFileName)
            oWriter.write(self.name)

    def _card_set_delete(self, _oWidget):
        """Delete the card set."""
        self._oController.delete_card_set()

    def toggle_editable(self, oWidget):
        """Toggle the editable state of the card set."""
        if self._oController.model.bEditable != oWidget.active:
            self._oController.view.toggle_editable(oWidget.active)
            self._oPaste.set_sensitive(oWidget.active)
            self._oDel.set_sensitive(oWidget.active)

    def force_editable_mode(self, bValue):
        """Toggle the editable state of the card set."""
        self._oEditable.set_active(bValue)
        self._oPaste.set_sensitive(bValue)
        self._oDel.set_sensitive(bValue)

    def _del_selection(self, _oWidget):
        """Delete the current selection"""
        self._oController.view.del_selection()

    def _paste_selection(self, _oWidget):
        """Try to paste the current clipboard contents"""
        self._oController.view.do_paste()

    def _edit_local_profile(self, _oWidget):
        """Open an editor for the local cardset profile."""
        # TODO: arrange for local profile updates to be stored
        oDlg = LocalProfileEditor(self._oMainWindow,
            self._oMainWindow.config_file)
        oDlg.run()

    def _edit_profiles(self, _oWidget):
        """Open an options profiles editing dialog."""
        oDlg = FrameProfileEditor(self._oMainWindow,
            self._oMainWindow.config_file)
        oDlg.run()

        sCardsetProfile = self._oMainWindow.config_file.get_profile(CARDSET,
            self.cardset_id)
        self._update_profile_group(self._oCardsetProfileMenu,
            self._select_cardset_profile, sCardsetProfile)

        sFrameProfile = self._oMainWindow.config_file.get_profile(FRAME,
            self.frame_id)
        self._update_profile_group(self._oFrameProfileMenu,
            self._select_frame_profile, sFrameProfile)

    def _select_cardset_profile(self, oRadio, sProfileKey):
        """Callback to change the profile of the current card set."""
        if oRadio.get_active():
            oConfig = self._oMainWindow.config_file
            oConfig.set_profile(CARDSET, self.cardset_id, sProfileKey)

    def _select_frame_profile(self, oRadio, sProfileKey):
        """Callback to change the profile of the current frame."""
        if oRadio.get_active():
            oConfig = self._oMainWindow.config_file
            oConfig.set_profile(FRAME, self.frame_id, sProfileKey)
