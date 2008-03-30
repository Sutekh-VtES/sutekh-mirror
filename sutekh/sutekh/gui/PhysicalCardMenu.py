# PhysicalCardMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Menu for the Physical Card View
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.gui.ExportDialog import ExportDialog
from sutekh.gui.EditPhysicalCardMappingDialog import EditPhysicalCardMappingDialog
from sutekh.io.XmlFileHandling import PhysicalCardXmlFile

class PhysicalCardMenu(gtk.MenuBar, object):
    def __init__(self, oFrame, oController, oWindow):
        super(PhysicalCardMenu, self).__init__()
        self.__oC = oController
        self.__oWindow = oWindow
        self.__oFrame = oFrame

        self.__dMenus = {}
        self.__create_PCL_menu()
        self.__create_filter_menu()
        self.__create_plugin_menu()

    def __create_PCL_menu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("Actions")
        wMenu = gtk.Menu()
        self.__dMenus["Actions"] = wMenu
        iMenu.set_submenu(wMenu)
        # items
        iExport = gtk.MenuItem("Export Collection to File")
        wMenu.add(iExport)
        iExport.connect('activate', self.do_export)


        self.iViewAllAbstractCards = gtk.CheckMenuItem("Show cards with a count of 0")
        self.iViewAllAbstractCards.set_inconsistent(False)
        self.iViewAllAbstractCards.set_active(self.__oC.model.bAddAllAbstractCards)
        self.iViewAllAbstractCards.connect('toggled', self.toggle_all_abstract_cards)
        wMenu.add(self.iViewAllAbstractCards)

        self.iViewExpansions = gtk.CheckMenuItem('Show Card Expansions')
        self.iViewExpansions.set_inconsistent(False)
        self.iViewExpansions.set_active(True)
        self.iViewExpansions.connect('toggled', self.toggle_expansion)
        wMenu.add(self.iViewExpansions)

        self.iEditable = gtk.CheckMenuItem('Collection is Editable')
        self.iEditable.set_inconsistent(False)
        self.iEditable.set_active(False)
        self.iEditable.connect('toggled', self.toggle_editable)
        self.__oC.view.set_edit_menu_item(self.iEditable)
        wMenu.add(self.iEditable)

        iExpand = gtk.MenuItem("Expand All (Ctrl+)")
        wMenu.add(iExpand)
        iExpand.connect("activate", self.expand_all)

        iCollapse = gtk.MenuItem("Collapse All (Ctrl-)")
        wMenu.add(iCollapse)
        iCollapse.connect("activate", self.collapse_all)

        iClose = gtk.MenuItem("Remove This Pane")
        wMenu.add(iClose)
        iClose.connect("activate", self.__oFrame.close_menu_item)

        iEditAllocation = gtk.MenuItem('Edit allocation of cards to PCS')
        wMenu.add(iEditAllocation)
        iEditAllocation.connect('activate', self.do_edit_card_set_allocation)

        self.add(iMenu)

    def __create_filter_menu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("Filter")
        wMenu = gtk.Menu()
        iMenu.set_submenu(wMenu)
        self.__dMenus["Filter"] = wMenu
        # items
        iFilter = gtk.MenuItem("Specify Filter")
        wMenu.add(iFilter)
        iFilter.connect('activate', self.setFilter)

        self.iApply = gtk.CheckMenuItem("Apply Filter")
        self.iApply.set_inconsistent(False)
        self.iApply.set_active(False)
        wMenu.add(self.iApply)
        self.iApply.connect('toggled', self.toggleApply)
        self.add(iMenu)

    def __create_plugin_menu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("Plugins")
        wMenu = gtk.Menu()
        self.__dMenus["Plugins"] = wMenu
        iMenu.set_submenu(wMenu)
        # plugins
        for oPlugin in self.__oFrame._aPlugins:
            oPlugin.add_to_menu(self.__dMenus, wMenu)
        self.add(iMenu)
        if len(wMenu.get_children()) == 0:
            iMenu.set_sensitive(False)

    def do_export(self, oWidget):
        oFileChooser = ExportDialog("Save Collection As", self.__oWindow)
        oFileChooser.run()
        sFileName = oFileChooser.getName()
        if sFileName is not None:
            oW = PhysicalCardXmlFile(sFileName)
            oW.write()

    def setApplyFilter(self, bState):
        self.iApply.set_active(bState)

    def do_edit_card_set_allocation(self, oWidget):
        """Popup the edit allocation dialog"""
        dSelectedCards = self.__oC.view.process_selection()
        if len(dSelectedCards) == 0:
            return
        oEditAllocation = EditPhysicalCardMappingDialog(self.__oWindow,
                dSelectedCards)
        oEditAllocation.run()

    def toggleApply(self, oWidget):
        self.__oC.view.runFilter(oWidget.active)

    def toggle_expansion(self, oWidget):
        self.__oC.model.bExpansions = oWidget.active
        self.__oC.view.reload_keep_expanded()

    def toggle_editable(self, oWidget):
        if self.__oC.model.bEditable != oWidget.active:
            self.__oC.view.toggle_editable(oWidget.active)

    def toggle_all_abstract_cards(self, oWidget):
        self.__oC.model.bAddAllAbstractCards = oWidget.active
        self.__oC.config_file.set_show_zero_count_cards(oWidget.active)
        self.__oC.view.reload_keep_expanded()

    def setFilter(self, oWidget):
        self.__oC.view.getFilter(self)

    def expand_all(self, oWidget):
        self.__oC.view.expand_all()

    def collapse_all(self, oWidget):
        self.__oC.view.collapse_all()
