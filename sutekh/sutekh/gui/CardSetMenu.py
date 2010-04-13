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
from sutekh.gui.CardSetListModel import PARENT_COUNT, IGNORE_PARENT
from sutekh.gui.FrameProfileEditor import FrameProfileEditor

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
        self.__oController = oController
        self.__create_card_set_menu()
        self.create_edit_menu()
        self.create_filter_menu()
        self.create_plugins_menu('_Plugins', self._oFrame)
        self.sort_menu(self._dMenus['Export Card Set'])

    # pylint: disable-msg=W0212
    # We allow access via these properties
    name = property(fget=lambda self: self._oController.view.sSetName,
            doc="Associated Card Set Name")

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
        self.create_check_menu_item('Show icons for the grouping',
                oMenu, self.__oController.toggle_icons, True)

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
        self.create_menu_item('Edit _Profiles', oMenu, self._edit_profiles)
        self.add_edit_menu_actions(oMenu)

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

    def check_parent_count_column(self, oOldParent, oNewParent):
        """Check that the parent column values are set correctly
           when the parent changes.
           """
        # FIXME: Make code do the right thing for the changed
        # preferences system. For now, we just return so reparenting at
        # least works.
        return
        # pylint: disable-msg=E1101
        # SQLObject confuses pylint
        # We rely on signal handler to cause reload
        if oNewParent:
            self._oParentCol.set_sensitive(True)
            if not oOldParent:
                # Parent has changed from none, so set to default
                self._change_parent_count_mode(None, PARENT_COUNT, True)
                # Check below will force reload anyway
                self._oDefaultParentCount.set_active(True)
        else:
            self._oParentCol.set_sensitive(False)
            self._change_parent_count_mode(None, IGNORE_PARENT, True)

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

    def _edit_profiles(self, _oWidget):
        oDlg = FrameProfileEditor(self._oMainWindow,
            self._oMainWindow.config_file)
        oDlg.run()
