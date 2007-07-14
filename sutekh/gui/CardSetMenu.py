# CardSetMenu.py
# Menu for the CardSet View's
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.SutekhObjects import PhysicalCardSet,AbstractCardSet
from sutekh.gui.ExportDialog import ExportDialog
from sutekh.gui.PropDialog import PropDialog
from sutekh.XmlFileHandling import AbstractCardSetXmlFile, PhysicalCardSetXmlFile
from sutekh.gui.EditAnnotationsDialog import EditAnnotationsDialog

class CardSetMenu(gtk.MenuBar,object):
    def __init__(self,oController,oWindow,oView,sName,sType):
        super(CardSetMenu,self).__init__()
        self.__oC = oController
        self.__oWindow = oWindow
        self.__oView = oView
        self.sSetName = sName
        self.__sType=sType
        self.__sMenuType=sType.replace('CardSet','')
        self.__dMenus={}
        self.__createCardSetMenu()
        self.__createFilterMenu()
        self.__createPluginMenu()

    def __createCardSetMenu(self):
        iMenu = gtk.MenuItem(self.__sMenuType+" Card Set Actions")
        wMenu=gtk.Menu()
        self.__dMenus["CardSet"]=wMenu
        iMenu.set_submenu(wMenu)
        self.__iProperties=gtk.MenuItem("Edit Card Set ("+self.sSetName+") properties")
        wMenu.add(self.__iProperties)
        self.__iProperties.connect('activate',self.editProperites)
        self.__iEditAnn= gtk.MenuItem("Edit Annotations for Card Set ("+self.sSetName+")")
        wMenu.add(self.__iEditAnn)
        self.__iEditAnn.connect('activate', self.editAnnotations)
        self.__iExport = gtk.MenuItem("Export Card Set ("+self.sSetName+") to File")
        wMenu.add(self.__iExport)
        self.__iExport.connect('activate', self.doExport)
        self.__iClose=gtk.MenuItem("Close Card Set ("+self.sSetName+")")
        wMenu.add(self.__iClose)
        self.__iClose.connect("activate", self.cardSetClose)
        self.__iDelete=gtk.MenuItem("Delete Card Set ("+self.sSetName+")")
        # Possible enhancement, make card set names italic.
        # Looks like it requires playing with menuitem attributes
        # (or maybe gtk.Action)
        self.__iDelete.connect("activate", self.cardSetDelete)
        wMenu.add(self.__iDelete)
        self.add(iMenu)

    def __updateCardSetMenu(self):
        self.__iProperties.get_child().set_label("Edit Card Set ("+self.sSetName+") properties")
        self.__iExport.get_child().set_label("Export Card Set ("+self.sSetName+") to File")
        self.__iClose.get_child().set_label("Close Card Set ("+self.sSetName+")")
        self.__iDelete.get_child().set_label("Delete Card Set ("+self.sSetName+")")

    def __createFilterMenu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("Filter")
        wMenu = gtk.Menu()
        self.__dMenus["Filter"]=wMenu
        iMenu.set_submenu(wMenu)

        # items
        iFilter = gtk.MenuItem("Specify Filter")
        wMenu.add(iFilter)
        iFilter.connect('activate', self.__oC.getFilter)
        self.iApply=gtk.CheckMenuItem("Apply Filter")
        self.iApply.set_inconsistent(False)
        self.iApply.set_active(False)
        wMenu.add(self.iApply)
        self.iApply.connect('activate', self.__oC.runFilter)
        # Add the Menu
        self.add(iMenu)

    def __createPluginMenu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("Plugins")
        wMenu = gtk.Menu()
        self.__dMenus["Plugins"]=wMenu
        iMenu.set_submenu(wMenu)
        # plugins
        for oPlugin in self.__oC.getPlugins():
            oMI=oPlugin.getMenuItem()
            if oMI is not None:
                sMenu=oPlugin.getDesiredMenu()
                # Add to the requested menu if supplied
                if sMenu in self.__dMenus.keys():
                    self.__dMenus[sMenu].add(oMI)
                else:
                    # Plugins acts as a catchall Menu
                    wMenu.add(oMI)
        self.add(iMenu)
        if len(wMenu.get_children())==0:
            iMenu.set_sensitive(False)

    def editProperites(self,widget):
        if self.__sType=='PhysicalCardSet':
            oCS=PhysicalCardSet.byName(self.sSetName)
        else:
            oCS=AbstractCardSet.byName(self.sSetName)
        oProp=PropDialog("Edit Card Set ("+self.sSetName+") Propeties",\
                self.__oWindow,oCS.name,oCS.author,oCS.comment)
        oProp.run()
        (sName,sAuthor,sComment)=oProp.getData()
        if sName is not None and sName != self.sSetName and len(sName)>0:
            # Check new name is not in use
            if self.__sType=='PhysicalCardSet':
                oNameList=PhysicalCardSet.selectBy(name=sName)
            else:
                oNameList=AbstractCardSet.selectBy(name=sName)
            if oNameList.count()>0:
                Complaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,\
                    gtk.BUTTONS_CLOSE,\
                    "Chosen "+self.__sMenuType+" Card Set name already in use.")
                Complaint.connect("response",lambda dlg, resp: dlg.destroy())
                Complaint.run()
                return
            else:
                oCS.name=sName
                self.__oView.sSetName=sName
                self.sSetName=sName
                self.__updateCardSetMenu()
                self.__oWindow.updateName(self.sSetName)
                oCS.syncUpdate()
        if sAuthor is not None:
            oCS.author=sAuthor
            oCS.syncUpdate()
        if sComment is not None:
            oCS.comment=sComment
            oCS.syncUpdate()

    def editAnnotations(self,widget):
        if self.__sType=='PhysicalCardSet':
            oCS=PhysicalCardSet.byName(self.sSetName)
        else:
            oCS=AbstractCardSet.byName(self.sSetName)
        oEditAnn=EditAnnotationsDialog("Edit Annotations of Card Set ("+self.sSetName+")",\
                self.__oWindow,oCS.name,oCS.annotations)
        oEditAnn.run()
        oCS.annotations=oEditAnn.getData()
        oCS.syncUpdate()

    def doExport(self,widget):
        oFileChooser=ExportDialog("Save "+self.__sMenuType+" Card Set As",self.__oWindow)
        oFileChooser.run()
        sFileName=oFileChooser.getName()
        if sFileName is not None:
            # User has OK'd us overwriting anything
            if self.__sType=='PhysicalCardSet':
                oW=PhysicalCardSetXmlFile(sFileName)
            else:
                oW=AbstractCardSetXmlFile(sFileName)
            oW.write(self.sSetName)

    def cardSetClose(self,widget):
        self.__oWindow.closeCardSet(widget)

    def cardSetDelete(self,widget):
        self.__oWindow.deleteCardSet()

    def getApplyFilter(self):
        return self.iApply.get_active()

    def setApplyFilter(self,state):
        self.iApply.set_active(state)
