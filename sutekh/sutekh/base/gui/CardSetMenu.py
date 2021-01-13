# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Menu for the CardSet View's
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Menu for the card set pane"""

from gi.repository import Gtk
from .FilteredViewMenu import CardListMenu
from .FrameProfileEditor import FrameProfileEditor
from .LocalProfileEditor import LocalProfileEditor
from .BaseConfigFile import CARDSET, FRAME
from .MessageBus import MessageBus
from .GuiCardSetFunctions import export_cs


class CardSetMenu(CardListMenu):
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods
    """Card Set Menu.

       Provide the usual menu options, and implement several of the
       card set specific actions - editing card set properties, editng
       annotations, exporting to file, and so on.
       """
    # pylint: disable=too-many-instance-attributes
    # we are keeping a lot of state, so many instance variables
    def __init__(self, oFrame, oController, oWindow, cPCSWriter):
        super().__init__(oFrame, oWindow, oController)
        # Reference to the card set writer
        self._cPCSWriter = cPCSWriter
        self._create_card_set_menu()
        self.create_edit_menu()
        self.create_filter_menu()
        self.create_analyze_menu()
        self.add_plugins_to_menus(self._oFrame)
        self.sort_menu(self._dMenus['Export Card Set'])
        self.sort_menu(self._dMenus['Analyze'])
        MessageBus.subscribe(MessageBus.Type.CONFIG_MSG,
                             'remove_profile',
                             self.remove_profile)
        MessageBus.subscribe(MessageBus.Type.CONFIG_MSG,
                             'profile_option_changed',
                             self.profile_option_changed)
        MessageBus.subscribe(MessageBus.Type.CONFIG_MSG, 'profile_changed',
                             self.profile_changed)

    # pylint: disable=protected-access, invalid-name
    # We allow access via these properties
    # different convention for property names
    name = property(fget=lambda self: self._oController.view.sSetName,
                    doc="Associated Card Set Name")

    frame_id = property(fget=lambda self: self._oController.model.frame_id,
                        doc="Frame ID of associated card set "
                            "(for selecting profiles)")

    cardset_id = property(fget=lambda self: self._oController.model.cardset_id,
                          doc="Cardset ID of associated card set "
                              "(for selecting profiles)")

    # pylint: enable=protected-access, invalid-name

    # pylint: disable=attribute-defined-outside-init
    # these methods are called from __init__, so it's OK
    def _create_card_set_menu(self):
        """Create the Actions menu for Card Sets."""
        oMenu = self.create_submenu(self, '_Actions')
        self.create_menu_item("Edit Card Set _Properties", oMenu,
                              self._edit_properties)
        self.create_menu_item("_Save Card Set to File", oMenu,
                              self._do_export)
        # Submenu for plugins
        self.create_submenu(oMenu, "_Export Card Set")

        oMenu.add(Gtk.SeparatorMenuItem())
        self.add_common_actions(oMenu)

        oMenu.add(Gtk.SeparatorMenuItem())
        self.create_menu_item("Delete Card Set", oMenu, self._card_set_delete)

    def create_edit_menu(self):
        """Create the 'Edit' menu, and populate it."""
        oMenu = self.create_submenu(self, "_Edit")
        self._oEditable = self.create_check_menu_item('Card Set is Editable',
                                                      oMenu,
                                                      self.toggle_editable,
                                                      False, '<Ctrl>e')
        self._oController.view.set_menu(self)
        self.create_menu_item('Copy selection', oMenu, self.copy_selection,
                              '<Ctrl>c')
        self._oPaste = self.create_menu_item('Paste', oMenu,
                                             self._paste_selection,
                                             '<Ctrl>v')
        self._oDel = self.create_menu_item('Delete selection', oMenu,
                                           self._del_selection, 'Delete')
        self._oPaste.set_sensitive(False)
        self._oDel.set_sensitive(False)

        self._oUndo = self.create_menu_item('Undo', oMenu,
                                            self._undo_edit, '<Ctrl>z')
        self._oRedo = self.create_menu_item('Redo', oMenu,
                                            self._redo_edit, '<Ctrl>y')
        self.set_redo_sensitive(False)
        self.set_undo_sensitive(False)

        self.create_menu_item('Edit _Local Profile', oMenu,
                              self._edit_local_profile)
        self.create_menu_item('Edit _Profiles', oMenu, self._edit_profiles)

        sCardsetProfile = self._oMainWindow.config_file.get_profile(
            CARDSET, self.cardset_id)
        self._oCardsetProfileMenu = self._create_profile_menu(
            oMenu, "Cardset Profile", CARDSET, self._select_cardset_profile,
            sCardsetProfile)

        sFrameProfiles = self._oMainWindow.config_file.get_profile(
            FRAME, self.frame_id)
        self._oFrameProfileMenu = self._create_profile_menu(
            oMenu, "Pane Profile", FRAME, self._select_frame_profile,
            sFrameProfiles)

        self.add_edit_menu_actions(oMenu)

    # pylint: enable=attribute-defined-outside-init

    def cleanup(self):
        """Remove the menu listener"""
        MessageBus.unsubscribe(MessageBus.Type.CONFIG_MSG, 'remove_profile',
                               self.remove_profile)
        MessageBus.unsubscribe(MessageBus.Type.CONFIG_MSG,
                               'profile_option_changed',
                               self.profile_option_changed)
        MessageBus.unsubscribe(MessageBus.Type.CONFIG_MSG, 'profile_changed',
                               self.profile_changed)

    def _edit_properties(self, _oWidget):
        """Popup the Edit Properties dialog to change card set properties."""
        self._oController.edit_properties(self)

    def update_card_set_menu(self, oCardSet):
        """Update the menu to reflect changes in the card set name."""
        sNewName = oCardSet.name
        self._oFrame.update_name(sNewName)
        self._oController.view.update_name(sNewName)

    def _do_export(self, _oWidget):
        """Export the card set to the chosen filename."""
        export_cs(self._oController.model.cardset,
                  self._cPCSWriter, self._oMainWindow,
                  'xml', [('XML Files', ['*.xml'])])

    def _card_set_delete(self, _oWidget):
        """Delete the card set."""
        self._oController.delete_card_set()

    def toggle_editable(self, oWidget):
        """Toggle the editable state of the card set."""
        if self._oController.model.bEditable != oWidget.get_active():
            self._oController.view.toggle_editable(oWidget.get_active())
            self._oPaste.set_sensitive(oWidget.get_active())
            self._oDel.set_sensitive(oWidget.get_active())

    def force_editable_mode(self, bValue):
        """Toggle the editable state of the card set."""
        self._oEditable.set_active(bValue)
        self._oPaste.set_sensitive(bValue)
        self._oDel.set_sensitive(bValue)

    def _del_selection(self, _oWidget):
        """Delete the current selection"""
        self._oController.view.del_selection()

    def _undo_edit(self, _oWidget):
        """Undo last edit"""
        self._oController.undo_edit()

    def _redo_edit(self, _oWidget):
        """Redo the last edit"""
        self._oController.redo_edit()

    def set_undo_sensitive(self, bValue):
        """Toggle the undo menu item state."""
        self._oUndo.set_sensitive(bValue)

    def set_redo_sensitive(self, bValue):
        """Toggle the redo menu item state."""
        self._oRedo.set_sensitive(bValue)

    def _paste_selection(self, _oWidget):
        """Try to paste the current clipboard contents"""
        self._oController.view.do_paste()

    def _edit_local_profile(self, _oWidget):
        """Open an editor for the local cardset profile."""
        oDlg = LocalProfileEditor(self._oMainWindow,
                                  self._oMainWindow.config_file,
                                  self.frame_id, self.cardset_id)
        oDlg.run()

    def _edit_profiles(self, _oWidget):
        """Open an options profiles editing dialog."""
        oDlg = FrameProfileEditor(self._oMainWindow,
                                  self._oMainWindow.config_file, CARDSET)
        sCurProfile = self._oMainWindow.config_file.get_profile(
            FRAME, self.frame_id)
        if not sCurProfile:
            # We're using the card set profile instead
            sCurProfile = self._oMainWindow.config_file.get_profile(
                CARDSET, self.cardset_id)
        oDlg.set_selected_profile(sCurProfile)
        oDlg.run()

    def _fix_profile_menu(self):
        """Update the profile menu properly"""
        sCardsetProfile = self._oMainWindow.config_file.get_profile(
            CARDSET, self.cardset_id)
        self._update_profile_group(self._oCardsetProfileMenu, CARDSET,
                                   self._select_cardset_profile,
                                   sCardsetProfile)
        sFrameProfile = self._oMainWindow.config_file.get_profile(
            FRAME, self.frame_id)
        self._update_profile_group(self._oFrameProfileMenu, FRAME,
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

    # Respond to profile changes

    def remove_profile(self, sType, _sProfile):
        """A profile has been removed"""
        if sType in (CARDSET, FRAME):
            self._fix_profile_menu()

    def profile_option_changed(self, sType, _sProfile, sKey):
        """Update menu if profiles are renamed."""
        if sType in (CARDSET, FRAME) and sKey == 'name':
            self._fix_profile_menu()

    def profile_changed(self, sType, sId):
        """Update the menu if the profile in use has changed"""
        if sType == FRAME and sId == self.frame_id:
            self._fix_profile_menu()
        elif sType == CARDSET and sId == self.cardset_id:
            # Relevant when we have multiple copies of the cardset open
            self._fix_profile_menu()
