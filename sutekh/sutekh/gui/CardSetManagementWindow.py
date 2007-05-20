# FilterDialog.py
# Dialog for setting Filter Parameters
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.SutekhObjects import AbstractCardSet, PhysicalCardSet
from sutekh.gui.ScrolledList import ScrolledList
from sutekh.gui.CreateCardSetDialog import CreateCardSetDialog
from sutekh.gui.DeleteCardSetDialog import DeleteCardSetDialog
from sutekh.gui.CardSetWindow import CardSetWindow
from sutekh.gui.CardSetController import PhysicalCardSetController, AbstractCardSetController

class CardSetManagementWindow(gtk.Window):
    def __init__(self,oMainController,oWindow):
        super(CardSetManagementWindow,self).__init__()
        self.__oMC = oMainController
        self.__oWin = oWindow
        self.set_title("Card Set Management")
        self.bRep = False
        self.set_default_size(600,350)
        oAbsFrame = gtk.Frame('')
        oPhysFrame = gtk.Frame('')
        self.oAbsCardSets = ScrolledList('Abstract Card Sets','')
        self.oPhysCardSets = ScrolledList('Physical Card Sets','')
        self.oAbsCardSets.set_select_single()
        self.oPhysCardSets.set_select_single()
        self.oAbsCardSets.TreeView.get_selection().connect('changed',self.cardSetSelected,'Abstract')
        self.oPhysCardSets.TreeView.get_selection().connect('changed',self.cardSetSelected,'Physical')
        self.oAbsCardSets.TreeView.connect('row_activated',self.rowClicked,'Abstract')
        self.oPhysCardSets.TreeView.connect('row_activated',self.rowClicked,'Physical')
        oAbsFrame.add(self.oAbsCardSets)
        oPhysFrame.add(self.oPhysCardSets)
        oWindowVBox = gtk.VBox(False,0)
        oListsHBox = gtk.HBox(False,0)
        oButtonBox = gtk.HButtonBox()
        oWindowVBox.pack_start(oListsHBox,True)
        oWindowVBox.pack_start(oButtonBox,False)
        oListsHBox.pack_start(oAbsFrame)
        oListsHBox.pack_start(oPhysFrame)
        oLoadButton = gtk.Button('Load Card Set')
        oCloseButton = gtk.Button('Close Card Set')
        oDeleteButton = gtk.Button('Delete Selected Card Set')
        oNewAbstractCS = gtk.Button('New Abstract Card Set')
        oNewPhysicalCS = gtk.Button('New Physical Card Set')
        oButtonBox.pack_start(oLoadButton)
        oButtonBox.pack_start(oCloseButton)
        oButtonBox.pack_start(oDeleteButton)
        oButtonBox.pack_start(oNewAbstractCS)
        oButtonBox.pack_start(oNewPhysicalCS)
        oLoadButton.connect("clicked",self.loadClicked)
        oCloseButton.connect("clicked",self.closeClicked)
        oDeleteButton.connect("clicked",self.deleteClicked)
        oNewAbstractCS.connect("clicked",self.newClicked,'Abstract')
        oNewPhysicalCS.connect("clicked",self.newClicked,'Physical')
        self.add(oWindowVBox)
        self.aOpenPhysicalCardSets={}
        self.aOpenAbstractCardSets={}
        self.reloadCardSetLists()
        self.show_all()

    def reloadCardSetLists(self):
        self.oAbsCardSets.get_list().clear()
        self.oPhysCardSets.get_list().clear()
        self.oAbsOpenedIter=self.oAbsCardSets.get_list().append(None)
        self.oAbsCardSets.get_list().set(self.oAbsOpenedIter,0, '<b>Opened Abstract Card Sets</b>')
        self.oAbsAvailIter=self.oAbsCardSets.get_list().append(None)
        self.oAbsCardSets.get_list().set(self.oAbsAvailIter,0,'<b>Available Abstract Card Sets</b>')
        self.oPhysOpenedIter=self.oPhysCardSets.get_list().append(None)
        self.oPhysCardSets.get_list().set(self.oPhysOpenedIter,0, '<b>Opened Physical Card Sets</b>')
        self.oPhysAvailIter=self.oPhysCardSets.get_list().append(None)
        self.oPhysCardSets.get_list().set(self.oPhysAvailIter,0,'<b>Available Physical Card Sets</b>')
        for oCS in AbstractCardSet.select().orderBy('name'):
            if oCS.name not in self.aOpenAbstractCardSets.keys():
                iter = self.oAbsCardSets.get_list().append(None)
            else:
                iter = self.oAbsCardSets.get_list().insert_before(self.oAbsAvailIter)
            self.oAbsCardSets.get_list().set(iter,0,oCS.name)
        for oCS in PhysicalCardSet.select().orderBy('name'):
            if oCS.name not in self.aOpenPhysicalCardSets.keys():
                iter = self.oPhysCardSets.get_list().append(None)
            else:
                iter = self.oPhysCardSets.get_list().insert_before(self.oPhysAvailIter)
            self.oPhysCardSets.get_list().set(iter,0,oCS.name)

    def cardSetSelected(self,selection,type):
        if self.bRep:
            return False
        try:
            self.bRep= True
            if type == 'Abstract':
                self.oPhysCardSets.TreeView.get_selection().unselect_all()
            else:
                self.oAbsCardSets.TreeView.get_selection().unselect_all()
        finally:
            self.bRep= False

    def rowClicked(self, oTreeView, oPath, oColumn, sType):
        oM = oTreeView.get_model()
        # We are pointing to a ListStore, so the iters should always be valid
        # Need to dereference to the actual path though, as iters not unique
        if sType == 'Abstract':
            if oPath == oM.get_path(self.oAbsOpenedIter) or oPath == oM.get_path(self.oAbsAvailIter):
                return
        elif sType == 'Physical':
            if oPath == oM.get_path(self.oPhysOpenedIter) or oPath == oM.get_path(self.oPhysAvailIter):
                return
        oIter = oM.get_iter(oPath)
        sName = oM.get_value(oIter,0)
        self.createNewCardSetWindow(sName,sType)

    def getSelectedRow(self):
        oPhysSelection=self.oPhysCardSets.TreeView.get_selection()
        oAbsSelection=self.oAbsCardSets.TreeView.get_selection()
        if oAbsSelection.count_selected_rows()>0:
            sType = 'Abstract'
            (oM,oIter)=oAbsSelection.get_selected()
            oTestIter1=self.oAbsOpenedIter
            oTestIter2=self.oAbsAvailIter
        elif oPhysSelection.count_selected_rows()>0:
            sType = 'Physical'
            (oM,oIter)=oPhysSelection.get_selected()
            oTestIter1=self.oPhysOpenedIter
            oTestIter2=self.oPhysAvailIter
        else:
            return (None, None)
        oPath = oM.get_path(oIter)
        sName=oM.get_value(oIter,0)
        if oPath == oM.get_path(oTestIter1) or \
                oPath == oM.get_path(oTestIter2):
            return (None, None)
        return (sName, sType)

    def loadClicked(self,button):
        (sName, sType) = self.getSelectedRow()
        if sName is None:
            return
        self.createNewCardSetWindow(sName,sType)

    def closeClicked(self,button):
        (sName, sType) = self.getSelectedRow()
        if sName is None:
            return
        if sType == 'Abstract' and sName in self.aOpenAbstractCardSets.keys():
            oWindow = self.aOpenAbstractCardSets[sName][0]
        elif sType == 'Physical' and sName in self.aOpenPhysicalCardSets.keys():
            oWindow = self.aOpenPhysicalCardSets[sName][0]
        else:
            return
        oWindow.closeCardSet()

    def deleteClicked(self,button):
        (sName, sType) = self.getSelectedRow()
        if sName is None:
            return
        oWindow = self.getCardSetWindow(sName, sType)
        if oWindow is not None:
            oWindow.deleteCardSet()
        else:
            if sType == "Physical":
                oCS = PhysicalCardSet.byName(sName)
                sSetType='PhysicalCardSet'
            else:
                oCS = AbstractCardSet.byName(sName)
                sSetType='AbstractCardSet'
            if len(oCS.cards)>0:
                # Not empty, ask user if we should delete it
                Dialog = DeleteCardSetDialog(self,sName,sSetType)
                Dialog.run()
                if not Dialog.getResult():
                    return # not deleting

                # User agreed, so clear the CardSet
                if sType == "Physical":
                    for oC in oCS.cards:
                        oCS.removePhysicalCard(oC)
                else:
                    for oC in oCS.cards:
                        oCS.removeAbstractCard(oC)


            # Card Set now empty
            if sType == "Physical":
                cardSet = PhysicalCardSet.byName(sName)
                PhysicalCardSet.delete(cardSet.id)
            else:
                cardSet = AbstractCardSet.byName(sName)
                AbstractCardSet.delete(cardSet.id)
            self.reloadCardSetLists()

    def newClicked(self,button,type):
        if type=='Abstract':
            Dialog=CreateCardSetDialog(self.__oWin,"AbstractCardSet")
        else:
            Dialog=CreateCardSetDialog(self.__oWin,"PhysicalCardSet")
        Dialog.run()
        (Name,sAuthor,sDesc)=Dialog.getName()
        if Name!=None:
            # Check Name isn't in use
            if type == 'Absttract':
                NameList = AbstractCardSet.selectBy(name=Name)
            else:
                NameList = PhysicalCardSet.selectBy(name=Name)
            if NameList.count() != 0:
                # Complain about duplicate name
                Complaint = gtk.MessageDialog(None,0,gtk.MESSAGE_ERROR,
                                              gtk.BUTTONS_CLOSE,"Chosen "+type+" Card Set name already in use.")
                Complaint.connect("response",lambda dlg, resp: dlg.destroy())
                Complaint.run()
                return
        else:
            return
        if type == 'Abstract':
            AbstractCardSet(name = Name,author = sAuthor,comment = sDesc) # Create New Abstract Card Set
            self.createNewCardSetWindow(Name,'Abstract')
        else:
            PhysicalCardSet(name = Name,author = sAuthor,comment = sDesc) # Create PhysicalCardSet
            self.createNewCardSetWindow(Name,'Physical')

    def createNewCardSetWindow(self,sSetName,sType):
        newController=None
        if sType == 'Physical' or sType == 'PhysicalCardSet':
            if sSetName not in self.aOpenPhysicalCardSets.keys():
                newWindow = CardSetWindow(self,sSetName,"PhysicalCardSet")
                newController = PhysicalCardSetController(newWindow,self.__oMC,sSetName)
                self.aOpenPhysicalCardSets[sSetName] = [newWindow, newController]
            else:
                # raise the window
                self.aOpenPhysicalCardSets[sSetName][0].present()
                return
        elif sType == 'Abstract' or sType == 'AbstractCardSet':
            if sSetName not in self.aOpenAbstractCardSets.keys():
                newWindow = CardSetWindow(self,sSetName,"AbstractCardSet")
                newController = AbstractCardSetController(newWindow,self.__oMC,sSetName)
                self.aOpenAbstractCardSets[sSetName] = [newWindow, newController]
            else:
                # raise the window
                self.aOpenAbstractCardSets[sSetName][0].present()
                return
        if newController is not None:
            newWindow.addParts(newController.getView(),newController.getMenu())
            self.__oMC.getWinGroup().add_window(newWindow)
            self.reloadCardSetLists()
            return newWindow
        return None

    def getCardSetWindow(self,sSetName,sType):
        if sType == "PhysicalCardSet" or sType == 'Physical':
            openSets=self.aOpenPhysicalCardSets
        elif sType == 'AbstractCardSet' or sType == 'Abstract':
            openSets=self.aOpenAbstractCardSets
        if sSetName in openSets.keys():
            window, controller = openSets[sSetName]
            return window
        return None
 
    def removeCardSetWindow(self,sSetName,sType):
        # Check Card Set window does exist
        if sType == "PhysicalCardSet" or sType == 'Physical':
            openSets=self.aOpenPhysicalCardSets
        elif sType == 'AbstractCardSet' or sType == 'Abstract':
            openSets=self.aOpenAbstractCardSets
        if sSetName in openSets.keys():
            self.__oMC.getWinGroup().remove_window(openSets[sSetName][0])
            del openSets[sSetName]

    def reloadACS(self,sName):
        if sName in self.aOpenAbstractCardSets.keys():
            window, controller = self.aOpenAbstractCardSets[sName]
            controller.getView().load()

    def reloadCS(self,sName,sSetType):
        if sSetType == 'AbstractCardSet' or sSetType == 'Abstract':
            self.reloadACS(sName)
        elif sSetType == 'PhysicalCardSet' or sSetType == 'Physical':
            self.reloadPCS(sName)

    def reloadPCS(self,sName):
        if sName in self.aOpenPhysicalCardSets.keys():
            window, controller = self.aOpenPhysicalCardSets[sName]
            controller.getView().load()

    def reloadAll(self):
        self.reloadAllPhysicalCardSets()
        self.reloadAllAbstractCardSets()

    def reloadAllPhysicalCardSets(self):
        for window, controller in self.aOpenPhysicalCardSets.values():
            controller.getView().load()

    def reloadAllAbstractCardSets(self):
        for window, controller in self.aOpenAbstractCardSets.values():
            controller.getView().load()

