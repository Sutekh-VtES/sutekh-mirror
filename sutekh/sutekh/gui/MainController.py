# MainController.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sqlobject import SQLObjectNotFound
from PhysicalCardController import PhysicalCardController
from MainWindow import MainWindow
from PhysicalCardWindow import PhysicalCardWindow
from CardSetWindow import CardSetWindow
from CardSetController import PhysicalCardSetController, AbstractCardSetController
from MainMenu import MainMenu
from CardTextView import CardTextView
from AbstractCardView import AbstractCardView
from PluginManager import PluginManager
from SutekhObjects import *

class MainController(object):
    def __init__(self):
        # Create PluginManager
        self.__oPluginManager = PluginManager()
        self.__oPluginManager.loadPlugins()
        # Create Sub-Controllers
        # Create Views
        self.__oWinGrp = gtk.WindowGroup()
        # Need a group as we'll be adding and removing Card Set View windows,
        # and they should all be blocked by the appropriate dialogs
        self.__oAbstractCardWin = MainWindow(self)
        self.__oPhysicalCardWin = PhysicalCardWindow(self)
        self.__oMenu = MainMenu(self,self.__oAbstractCardWin)
        self.__oCardText = CardTextView(self)
        self.__oAbstractCards = AbstractCardView(self,self.__oAbstractCardWin)
        self.__oPhysicalCards = PhysicalCardController(self.__oPhysicalCardWin,self)
        self.__oWinGrp.add_window(self.__oAbstractCardWin)
        self.__oWinGrp.add_window(self.__oPhysicalCardWin)

        self.openPhysicalCardSets={}
        self.openAbstractCardSets={}

        # Link
        self.__oAbstractCardWin.addParts(self.__oMenu,self.__oCardText, \
                             self.__oAbstractCards)
        self.__oPhysicalCardWin.addParts(self.__oPhysicalCards.getMenu(), \
                             self.__oPhysicalCards.getView())

    def run(self):
        gtk.main()

    def actionQuit(self):
        gtk.main_quit()

    def setCardText(self,sCardName):
        try:
            oCard = AbstractCard.byName(sCardName)
            self.__oCardText.setCardText(oCard)
        except SQLObjectNotFound:
            pass

    def createNewPhysicalCardSetWindow(self,sSetName):
        # name is not already used
        if sSetName not in self.openPhysicalCardSets.keys():
            newPCSWindow = CardSetWindow(self,sSetName,"Physical")
            newPCSController = PhysicalCardSetController(newPCSWindow,self,sSetName)
            self.openPhysicalCardSets[sSetName] = [newPCSWindow, newPCSController]
            newPCSWindow.addParts(newPCSController.getView(),newPCSController.getMenu())
            self.__oMenu.setLoadPhysicalState(self.openPhysicalCardSets)
            self.__oWinGrp.add_window(newPCSWindow)
            return newPCSWindow
        return None

    def createNewAbstractCardSetWindow(self,sSetName):
        # name is not already used
        if sSetName not in self.openAbstractCardSets.keys():
            newACSWindow = CardSetWindow(self,sSetName,"Abstract")
            newACSController = AbstractCardSetController(newACSWindow,self,sSetName)
            self.openAbstractCardSets[sSetName] = [newACSWindow, newACSController]
            newACSWindow.addParts(newACSController.getView(),newACSController.getMenu())
            self.__oMenu.setLoadAbstractState(self.openAbstractCardSets)
            self.__oWinGrp.add_window(newACSWindow)
            return newACSWindow
        return None

    def removeCardSetWindow(self,sSetName,sType):
        # Check Card Set window does exist
        if sType == "Physical":
            openSets=self.openPhysicalCardSets
        else:
            openSets=self.openAbstractCardSets
        if sSetName in openSets.keys():
            self.__oWinGrp.remove_window(openSets[sSetName][0])
            del openSets[sSetName]
            if sType == "Physical":
                self.__oMenu.setLoadPhysicalState(self.openPhysicalCardSets)
            else:
                self.__oMenu.setLoadAbstractState(self.openPhysicalCardSets)

    def reloadAllPhysicalCardSets(self):
        for window, controller in self.openPhysicalCardSets.values():
            controller.getView().load()

    def reloadAllAbstractCardSets(self):
        for window, controller in self.openAbstractCardSets.values():
            controller.getView().load()

    def getFilter(self,widget):
        self.__oAbstractCards.getFilter(self.__oMenu)

    def runFilter(self,widget):
        self.__oAbstractCards.runFilter(self.__oMenu.getApplyFilter())

    def getPluginManager(self):
        return self.__oPluginManager
