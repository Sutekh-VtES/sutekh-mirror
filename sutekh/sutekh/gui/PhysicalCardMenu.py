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
from sutekh.gui.EditPhysicalCardMappingDialog import \
        EditPhysicalCardMappingDialog
from sutekh.io.XmlFileHandling import PhysicalCardXmlFile

class PhysicalCardMenu(gtk.MenuBar, object):
    """Menu for the Physical card collection.

       Enables actions specific to the physical card collection (export to
       file, etc), filtering and plugins.
       """
    # pylint: disable-msg=R0904
    # gtk.Widget, so menu public methods
    def __init__(self, oFrame, oController, oWindow):
        super(PhysicalCardMenu, self).__init__()
        self.__oController = oController
        self.__oWindow = oWindow
        self.__oFrame = oFrame

        self.__dMenus = {}
        self.__create_physical_cl_menu()
        self.__create_filter_menu()
        self.__create_plugin_menu()

    # pylint: disable-msg=W0201
    # called from __init__, so OK
    def __create_physical_cl_menu(self):
        """Create the Actions menu for the card list."""
        # setup sub menu
        oMenuItem = gtk.MenuItem("Actions")
        oMenu = gtk.Menu()
        self.__dMenus["Actions"] = oMenu
        oMenuItem.set_submenu(oMenu)
        # items
        iExport = gtk.MenuItem("Export Collection to File")
        oMenu.add(iExport)
        iExport.connect('activate', self._do_export)


        self.iViewAllAbstractCards = gtk.CheckMenuItem("Show cards with a"
                " count of 0")
        self.iViewAllAbstractCards.set_inconsistent(False)
        self.iViewAllAbstractCards.set_active(
                self.__oController.model.bAddAllAbstractCards)
        self.iViewAllAbstractCards.connect('toggled',
                self._toggle_all_abstract_cards)
        oMenu.add(self.iViewAllAbstractCards)

        self.iViewExpansions = gtk.CheckMenuItem('Show Card Expansions')
        self.iViewExpansions.set_inconsistent(False)
        self.iViewExpansions.set_active(True)
        self.iViewExpansions.connect('toggled', self._toggle_expansion)
        oMenu.add(self.iViewExpansions)

        self.iEditable = gtk.CheckMenuItem('Collection is Editable')
        self.iEditable.set_inconsistent(False)
        self.iEditable.set_active(False)
        self.iEditable.connect('toggled', self._toggle_editable)
        self.__oController.view.set_edit_menu_item(self.iEditable)
        oMenu.add(self.iEditable)

        iExpand = gtk.MenuItem("Expand All (Ctrl+)")
        oMenu.add(iExpand)
        iExpand.connect("activate", self._expand_all)

        iCollapse = gtk.MenuItem("Collapse All (Ctrl-)")
        oMenu.add(iCollapse)
        iCollapse.connect("activate", self._collapse_all)

        iClose = gtk.MenuItem("Remove This Pane")
        oMenu.add(iClose)
        iClose.connect("activate", self.__oFrame.close_menu_item)

        iEditAllocation = gtk.MenuItem('Edit allocation of cards to PCS')
        oMenu.add(iEditAllocation)
        iEditAllocation.connect('activate', self._do_edit_card_set_allocation)

        self.add(oMenuItem)

    def __create_filter_menu(self):
        """Create the filter menu."""
        # setup sub menu
        oMenuItem = gtk.MenuItem("Filter")
        oMenu = gtk.Menu()
        oMenuItem.set_submenu(oMenu)
        self.__dMenus["Filter"] = oMenu
        # items
        iFilter = gtk.MenuItem("Specify Filter")
        oMenu.add(iFilter)
        iFilter.connect('activate', self._set_active_filter)

        self.iApply = gtk.CheckMenuItem("Apply Filter")
        self.iApply.set_inconsistent(False)
        self.iApply.set_active(False)
        oMenu.add(self.iApply)
        self.iApply.connect('toggled', self._toggle_apply)
        self.add(oMenuItem)

    def __create_plugin_menu(self):
        """Create the plugin menu."""
        # setup sub menu
        oMenuItem = gtk.MenuItem("Plugins")
        oMenu = gtk.Menu()
        self.__dMenus["Plugins"] = oMenu
        oMenuItem.set_submenu(oMenu)
        # plugins
        for oPlugin in self.__oFrame._aPlugins:
            oPlugin.add_to_menu(self.__dMenus, oMenu)
        self.add(oMenuItem)
        if len(oMenu.get_children()) == 0:
            oMenuItem.set_sensitive(False)
    # pylint: enable-msg=W0201

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def _do_export(self, oWidget):
        """Handling exporting the card list to file."""
        oFileChooser = ExportDialog("Save Collection As", self.__oWindow)
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
        oEditAllocation = EditPhysicalCardMappingDialog(self.__oWindow,
                dSelectedCards)
        oEditAllocation.run()

    def _toggle_apply(self, oWidget):
        """Toggle the applied state of the filter."""
        self.__oController.view.runFilter(oWidget.active)

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
        self.__oController.config_file.set_show_zero_count_cards(
                oWidget.active)
        self.__oController.view.reload_keep_expanded()

    def _set_active_filter(self, oWidget):
        """Set the active filter for the TreeView."""
        self.__oController.view.getFilter(self)

    def _expand_all(self, oWidget):
        """Expand all rows in the TreeView."""
        self.__oController.view.expand_all()

    def _collapse_all(self, oWidget):
        """Collapse all rows in the TreeView."""
        self.__oController.view.collapse_all()

    # pylint: enable-msg=W0613

    def setApplyFilter(self, bState):
        """Set the applied filter state to bState."""
        self.iApply.set_active(bState)

