# PhysicalCardMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Menu for the Physical Card View
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Menu for the Physical card collection."""

from sutekh.gui.ExportDialog import ExportDialog
from sutekh.gui.PaneMenu import PaneMenu
from sutekh.gui.EditPhysicalCardMappingDialog import \
        EditPhysicalCardMappingDialog
from sutekh.io.XmlFileHandling import PhysicalCardXmlFile

class PhysicalCardMenu(PaneMenu, object):
    """Menu for the Physical card collection.

       Enables actions specific to the physical card collection (export to
       file, etc), filtering and plugins.
       """
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    def __init__(self, oFrame, oController, oWindow):
        super(PhysicalCardMenu, self).__init__(oFrame, oWindow)
        self.__oController = oController
        self.__create_physical_cl_menu()
        self.__create_edit_menu()
        self.create_filter_menu()
        self.create_plugins_menu()

    # pylint: disable-msg=W0201
    # called from __init__, so OK
    def __create_physical_cl_menu(self):
        """Create the Actions menu for the card list."""
        # setup sub menu
        oMenu = self.create_submenu("Actions")
        # items
        self.create_menu_item("Export Collection to File", oMenu,
                self._do_export)
        self.create_check_menu_item("Show cards with a count of 0", oMenu,
                self._toggle_all_abstract_cards,
                self.__oController.model.bAddAllAbstractCards)

        self.create_check_menu_item('Show Card Expansions', oMenu,
                self._toggle_expansion, True)

        self.create_menu_item("Expand All", oMenu, self._expand_all,
                '<Ctrl>plus')
        self.create_menu_item("Collapse All", oMenu, self._collapse_all,
                '<Ctrl>minus')
        self.create_menu_item("Remove This Pane", oMenu,
                self._oFrame.close_menu_item)
        self.create_menu_item('Edit allocation of cards to PCS', oMenu,
                self._do_edit_card_set_allocation)

    def __create_edit_menu(self):
        """Create the Edit Menu."""
        oMenu = self.create_submenu("Edit")

        oEditable = self.create_check_menu_item('Collection is Editable',
                oMenu, self._toggle_editable, False, '<Ctrl>E')
        self.__oController.view.set_edit_menu_item(oEditable)

        self.create_menu_item('Copy selection', oMenu, self._copy_selection,
                '<Ctrl>c')
        self.create_menu_item('Paste', oMenu, self._paste_selection,
                '<Ctrl>v')
        self.create_menu_item('Delete selection', oMenu, self._del_selection,
                'Delete')

    # pylint: enable-msg=W0201

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def _do_export(self, oWidget):
        """Handling exporting the card list to file."""
        oFileChooser = ExportDialog("Save Collection As", self._oMainWinow)
        oFileChooser.run()
        sFileName = oFileChooser.get_name()
        if sFileName is not None:
            oWriter = PhysicalCardXmlFile(sFileName)
            oWriter.write()

    def _do_edit_card_set_allocation(self, oWidget):
        """Popup the edit allocation dialog"""
        dSelectedCards = self.__oController.view.process_selection()
        if len(dSelectedCards) == 0:
            return
        oEditAllocation = EditPhysicalCardMappingDialog(self._oMainWinow,
                dSelectedCards)
        oEditAllocation.run()

    def toggle_apply_filter(self, oWidget):
        """Toggle the applied state of the filter."""
        self.__oController.view.run_filter(oWidget.active)

    def _toggle_expansion(self, oWidget):
        """Toggle whether the expansion information is shown."""
        self.__oController.model.bExpansions = oWidget.active
        self.__oController.view.reload_keep_expanded()

    def _toggle_editable(self, oWidget):
        """Toggle the editable state of the model."""
        if self.__oController.model.bEditable != oWidget.active:
            self.__oController.view.toggle_editable(oWidget.active)

    def _toggle_all_abstract_cards(self, oWidget):
        """Toggle the display of cards with a count of 0 in the card list."""
        self.__oController.model.bAddAllAbstractCards = oWidget.active
        self._oMainWinow.config_file.set_show_zero_count_cards(
                oWidget.active)
        self.__oController.view.reload_keep_expanded()

    def set_active_filter(self, oWidget):
        """Set the active filter for the TreeView."""
        self.__oController.view.get_filter(self)

    def _expand_all(self, oWidget):
        """Expand all rows in the TreeView."""
        self.__oController.view.expand_all()

    def _collapse_all(self, oWidget):
        """Collapse all rows in the TreeView."""
        self.__oController.view.collapse_all()

    def _del_selection(self, oWidget):
        """Delete the current selection"""
        self.__oController.view.del_selection()

    def _copy_selection(self, oWidget):
        """Copy the current selection to the application clipboard."""
        self.__oController.view.copy_selection()
        print 'copy selection'

    def _paste_selection(self, oWidget):
        """Try to paste the current clipbaord contents"""
        self.__oController.view.do_paste()

    # pylint: enable-msg=W0613
