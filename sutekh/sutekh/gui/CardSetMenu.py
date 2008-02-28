# CardSetMenu.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Menu for the CardSet View's
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet, AbstractCardSet
from sutekh.gui.SutekhDialog import do_complaint_error
from sutekh.gui.ExportDialog import ExportDialog
from sutekh.gui.PropDialog import PropDialog
from sutekh.io.XmlFileHandling import AbstractCardSetXmlFile, PhysicalCardSetXmlFile
from sutekh.gui.EditAnnotationsDialog import EditAnnotationsDialog

class CardSetMenu(gtk.MenuBar, object):
    def __init__(self, oFrame, oController, oWindow, oView, sName, cType):
        super(CardSetMenu, self).__init__()
        self.__oC = oController
        self.__oWindow = oWindow
        self.__oView = oView
        self.__oFrame = oFrame
        self.sSetName = sName
        self.__cSetType = cType
        if cType is AbstractCardSet:
            self.__sMenuType = 'Abstract'
        else:
            self.__sMenuType = 'Physical'
        self.__dMenus = {}
        self.__create_card_set_menu()
        self.__create_filter_menu()
        self.__create_plugin_menu()

    def __create_card_set_menu(self):
        iMenu = gtk.MenuItem("Actions")
        wMenu = gtk.Menu()
        self.__dMenus["Actions"] = wMenu
        self.__iProperties = gtk.MenuItem("Edit Card Set ("+self.sSetName+") properties")
        wMenu.add(self.__iProperties)
        self.__iProperties.connect('activate',self.editProperites)
        self.__iEditAnn = gtk.MenuItem("Edit Annotations for Card Set ("+self.sSetName+")")
        wMenu.add(self.__iEditAnn)
        self.__iEditAnn.connect('activate', self.editAnnotations)
        self.__iExport = gtk.MenuItem("Export Card Set ("+self.sSetName+") to File")
        wMenu.add(self.__iExport)
        self.__iExport.connect('activate', self.doExport)

        iExpand = gtk.MenuItem("Expand All (Ctrl+)")
        wMenu.add(iExpand)
        iExpand.connect("activate", self.expand_all)

        iCollapse = gtk.MenuItem("Collapse All (Ctrl-)")
        wMenu.add(iCollapse)
        iCollapse.connect("activate", self.collapse_all)

        self.__iClose = gtk.MenuItem("Remove This Pane")
        wMenu.add(self.__iClose)
        self.__iClose.connect("activate", self.__oFrame.close_menu_item)
        self.__iDelete = gtk.MenuItem("Delete Card Set ("+self.sSetName+")")
        # Possible enhancement, make card set names italic.
        # Looks like it requires playing with menuitem attributes
        # (or maybe gtk.Action)
        if self.__cSetType is PhysicalCardSet:
            oSep = gtk.SeparatorMenuItem()
            wMenu.add(oSep)
            self.iViewExpansions = gtk.CheckMenuItem('Show Card Expansions in the Pane')
            self.iViewExpansions.set_inconsistent(False)
            self.iViewExpansions.set_active(True)
            self.iViewExpansions.connect('toggled', self.toggleExpansion)
            wMenu.add(self.iViewExpansions)

        self.iEditable = gtk.CheckMenuItem('Card Set is Editable')
        self.iEditable.set_inconsistent(False)
        self.iEditable.set_active(False)
        self.iEditable.connect('toggled', self.toggleEditable)
        wMenu.add(self.iEditable)

        oSep = gtk.SeparatorMenuItem()
        wMenu.add(oSep)
        self.__iDelete.connect("activate", self.cardSetDelete)
        wMenu.add(self.__iDelete)

        iMenu.set_submenu(wMenu)
        self.add(iMenu)

    def __updateCardSetMenu(self):
        self.__iProperties.get_child().set_label("Edit Card Set ("+self.sSetName+") properties")
        self.__iExport.get_child().set_label("Export Card Set ("+self.sSetName+") to File")
        self.__iDelete.get_child().set_label("Delete Card Set ("+self.sSetName+")")

    def __create_filter_menu(self):
        # setup sub menun
        iMenu = gtk.MenuItem("Filter")
        wMenu = gtk.Menu()
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
        # Add the Menu
        iMenu.set_submenu(wMenu)
        self.add(iMenu)

    def __create_plugin_menu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("Plugins")
        wMenu = gtk.Menu()
        self.__dMenus["Plugins"] = wMenu
        # plugins
        for oPlugin in self.__oFrame._aPlugins:
            oMI = oPlugin.get_menu_item()
            if oMI is not None:
                sMenu = oPlugin.get_desired_menu()
                # Add to the requested menu if supplied
                if sMenu in self.__dMenus.keys():
                    self.__dMenus[sMenu].add(oMI)
                else:
                    # Plugins acts as a catchall Menu
                    wMenu.add(oMI)
        iMenu.set_submenu(wMenu)
        self.add(iMenu)
        if len(wMenu.get_children()) == 0:
            iMenu.set_sensitive(False)

    def editProperites(self,widget):
        oCS = self.__cSetType.byName(self.sSetName)
        oProp = PropDialog("Edit Card Set (" + self.sSetName + ") Propeties",
                         self.__oWindow,oCS.name,oCS.author,oCS.comment)
        oProp.run()
        (sName,sAuthor,sComment) = oProp.getData()
        if sName is not None and sName != self.sSetName and len(sName)>0:
            # Check new name is not in use
            oNameList = self.__cSetType.selectBy(name=sName)
            if oNameList.count()>0:
                do_complaint_error("Chosen " + self.__sMenuType + " Card Set name already in use.")
                return
            else:
                oCS.name = sName
                self.__oView.sSetName = sName
                self.sSetName = sName
                self.__oFrame.update_name(self.sSetName)
                self.__updateCardSetMenu()
                oCS.syncUpdate()
        if sAuthor is not None:
            oCS.author = sAuthor
            oCS.syncUpdate()
        if sComment is not None:
            oCS.comment = sComment
            oCS.syncUpdate()

    def editAnnotations(self,widget):
        oCS = self.__cSetType.byName(self.sSetName)
        oEditAnn = EditAnnotationsDialog("Edit Annotations of Card Set ("+self.sSetName+")",
                                         self.__oWindow,oCS.name,oCS.annotations)
        oEditAnn.run()
        oCS.annotations = oEditAnn.getData()
        oCS.syncUpdate()

    def doExport(self,widget):
        oFileChooser = ExportDialog("Save " + self.__sMenuType + " Card Set As",self.__oWindow)
        oFileChooser.run()
        sFileName = oFileChooser.getName()
        if sFileName is not None:
            # User has OK'd us overwriting anything
            if self.__cSetType is PhysicalCardSet:
                oW = PhysicalCardSetXmlFile(sFileName)
            else:
                oW = AbstractCardSetXmlFile(sFileName)
            oW.write(self.sSetName)

    def cardSetDelete(self,widget):
        self.__oFrame.deleteCardSet()

    def setApplyFilter(self,state):
        self.iApply.set_active(state)

    def toggleApply(self, oWidget):
        self.__oC.view.runFilter(oWidget.active)

    def toggleExpansion(self, oWidget):
        self.__oC.model.bExpansions = oWidget.active
        self.__oC.view.reload_keep_expanded()

    def toggleEditable(self, oWidget):
        self.__oC.model.bEditable = oWidget.active
        self.__oC.view.reload_keep_expanded()
        if oWidget.active:
            self.__oC.view.set_color_edit_cue()
        else:
            self.__oC.view.set_color_normal()

    def setFilter(self, oWidget):
        self.__oC.view.getFilter(self)

    def expand_all(self, oWidget):
        self.__oC.view.expand_all()

    def collapse_all(self, oWidget):
        self.__oC.view.collapse_all()
