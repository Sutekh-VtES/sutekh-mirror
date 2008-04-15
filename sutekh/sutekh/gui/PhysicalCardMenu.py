# PhysicalCardMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Menu for the Physical Card View
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Menu for the Physical card collection."""

import gtk
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
        oExport = gtk.MenuItem("Export Collection to File")
        oMenu.add(oExport)
        oExport.connect('activate', self._do_export)

        oViewAllAbstractCards = gtk.CheckMenuItem("Show cards with a"
                " count of 0")
        oViewAllAbstractCards.set_inconsistent(False)
        oViewAllAbstractCards.set_active(
                self.__oController.model.bAddAllAbstractCards)
        oViewAllAbstractCards.connect('toggled',
                self._toggle_all_abstract_cards)
        oMenu.add(oViewAllAbstractCards)

        oViewExpansions = gtk.CheckMenuItem('Show Card Expansions')
        oViewExpansions.set_inconsistent(False)
        oViewExpansions.set_active(True)
        oViewExpansions.connect('toggled', self._toggle_expansion)
        oMenu.add(oViewExpansions)


        oExpand = gtk.MenuItem("Expand All")
        oMenu.add(oExpand)
        oExpand.connect("activate", self._expand_all)
        oExpand.add_accelerator('activate', self._oAccelGroup,
                gtk.gdk.keyval_from_name('plus'), gtk.gdk.CONTROL_MASK,
                gtk.ACCEL_VISIBLE)

        oCollapse = gtk.MenuItem("Collapse All")
        oMenu.add(oCollapse)
        oCollapse.connect("activate", self._collapse_all)
        oCollapse.add_accelerator('activate', self._oAccelGroup,
                gtk.gdk.keyval_from_name('minus'), gtk.gdk.CONTROL_MASK,
                gtk.ACCEL_VISIBLE)

        oClose = gtk.MenuItem("Remove This Pane")
        oMenu.add(oClose)
        oClose.connect("activate", self._oFrame.close_menu_item)

        oEditAllocation = gtk.MenuItem('Edit allocation of cards to PCS')
        oMenu.add(oEditAllocation)
        oEditAllocation.connect('activate', self._do_edit_card_set_allocation)

    def __create_edit_menu(self):
        """Create the Edit Menu."""
        oMenu = self.create_submenu("Edit")

        oEditable = gtk.CheckMenuItem('Collection is Editable')
        oEditable.set_inconsistent(False)
        oEditable.set_active(False)
        oEditable.connect('toggled', self._toggle_editable)
        self.__oController.view.set_edit_menu_item(oEditable)
        oEditable.add_accelerator('activate', self._oAccelGroup,
                ord('E'), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)
        oMenu.add(oEditable)

        oCopy = gtk.MenuItem('Copy selection')
        oCopy.connect('activate', self._copy_selection)
        oMenu.add(oCopy)
        oCopy.add_accelerator('activate', self._oAccelGroup,
                ord('C'), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)

        oPaste = gtk.MenuItem('Paste')
        oPaste.connect('activate', self._paste_selection)
        oMenu.add(oPaste)
        oPaste.add_accelerator('activate', self._oAccelGroup,
                ord('V'), gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE)

        oDelete = gtk.MenuItem('Delete selection')
        oDelete.connect('activate', self._del_selection)
        oMenu.add(oDelete)
        oDelete.add_accelerator('activate', self._oAccelGroup,
                gtk.gdk.keyval_from_name('Delete') , 0, gtk.ACCEL_VISIBLE)

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
