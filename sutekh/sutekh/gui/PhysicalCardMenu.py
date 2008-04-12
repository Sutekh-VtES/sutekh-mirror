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
    # gtk.Widget, so many public methods
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

        oEditable = gtk.CheckMenuItem('Collection is Editable')
        oEditable.set_inconsistent(False)
        oEditable.set_active(False)
        oEditable.connect('toggled', self._toggle_editable)
        self.__oController.view.set_edit_menu_item(oEditable)
        oMenu.add(oEditable)

        oExpand = gtk.MenuItem("Expand All (Ctrl+)")
        oMenu.add(oExpand)
        oExpand.connect("activate", self._expand_all)

        oCollapse = gtk.MenuItem("Collapse All (Ctrl-)")
        oMenu.add(oCollapse)
        oCollapse.connect("activate", self._collapse_all)

        oClose = gtk.MenuItem("Remove This Pane")
        oMenu.add(oClose)
        oClose.connect("activate", self.__oFrame.close_menu_item)

        oEditAllocation = gtk.MenuItem('Edit allocation of cards to PCS')
        oMenu.add(oEditAllocation)
        oEditAllocation.connect('activate', self._do_edit_card_set_allocation)

        self.add(oMenuItem)

    def __create_filter_menu(self):
        """Create the filter menu."""
        # setup sub menu
        oMenuItem = gtk.MenuItem("Filter")
        oMenu = gtk.Menu()
        oMenuItem.set_submenu(oMenu)
        self.__dMenus["Filter"] = oMenu
        # items
        oFilter = gtk.MenuItem("Specify Filter")
        oMenu.add(oFilter)
        oFilter.connect('activate', self._set_active_filter)

        self.oApply = gtk.CheckMenuItem("Apply Filter")
        self.oApply.set_inconsistent(False)
        self.oApply.set_active(False)
        oMenu.add(self.oApply)
        self.oApply.connect('toggled', self._toggle_apply)
        self.add(oMenuItem)

    def __create_plugin_menu(self):
        """Create the plugin menu."""
        # setup sub menu
        oMenuItem = gtk.MenuItem("Plugins")
        oMenu = gtk.Menu()
        self.__dMenus["Plugins"] = oMenu
        oMenuItem.set_submenu(oMenu)
        # plugins
        for oPlugin in self.__oFrame.plugins:
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
        self.__oWindow.config_file.set_show_zero_count_cards(
                oWidget.active)
        self.__oController.view.reload_keep_expanded()

    def _set_active_filter(self, oWidget):
        """Set the active filter for the TreeView."""
        self.__oController.view.get_filter(self)

    def _expand_all(self, oWidget):
        """Expand all rows in the TreeView."""
        self.__oController.view.expand_all()

    def _collapse_all(self, oWidget):
        """Collapse all rows in the TreeView."""
        self.__oController.view.collapse_all()

    # pylint: enable-msg=W0613

    def set_apply_filter(self, bState):
        """Set the applied filter state to bState."""
        self.oApply.set_active(bState)

