# MainController.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sqlobject import SQLObjectNotFound
from PhysicalCardController import PhysicalCardController
from MainWindow import MainWindow
from PhysicalCardWindow import PhysicalCardWindow
from DeckWindow import DeckWindow
from DeckController import DeckController
from MainMenu import MainMenu
from CardTextView import CardTextView
from AbstractCardView import AbstractCardView
from SutekhObjects import *

class MainController(object):
    def __init__(self):
        # Create Sub-Controllers
    
        # Create Views
        self.__oWinGrp = gtk.WindowGroup()
        # Need a group as we'll be adding and removing Deck View windows,
        # and they should all be blocked by the appropriate dialogs
        self.__oAbstractCardWin = MainWindow(self)
        self.__oPhysicalCardWin = PhysicalCardWindow(self)
        self.__oMenu = MainMenu(self,self.__oAbstractCardWin)
        self.__oCardText = CardTextView(self)
        self.__oAbstractCards = AbstractCardView(self,self.__oAbstractCardWin)
        self.__oPhysicalCards = PhysicalCardController(self.__oPhysicalCardWin,self)
        self.__oWinGrp.add_window(self.__oAbstractCardWin)
        self.__oWinGrp.add_window(self.__oPhysicalCardWin)

        self.deckWinCount = 0
        # In place as I want to limit the maximum number of deck views open
        # to 3 (should change this later as arbitary restrictions not good)
        self.openDecks={}
                
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

    def createNewDeckWindow(self,deckName):
        if (self.deckWinCount < 3):
            # name is not already used
            if deckName not in self.openDecks:
                self.deckWinCount+=1
                newDeckWindow = DeckWindow(self,deckName)
                newDeckController = DeckController(newDeckWindow,self,deckName)
                self.openDecks[deckName] = [newDeckWindow, newDeckController]
                newDeckWindow.addParts(newDeckController.getView(),newDeckController.getMenu())
                self.__oMenu.setLoadDeckState(self.openDecks)
                self.__oWinGrp.add_window(newDeckWindow)
                return newDeckWindow
        return None

    def removeDeckWindow(self,deckName):
        # Check deck window does exist
        if deckName in self.openDecks:
            self.deckWinCount-=1
            self.__oWinGrp.remove_window(self.openDecks[deckName][0])
            del self.openDecks[deckName] 
            self.__oMenu.setLoadDeckState(self.openDecks)

    def reloadAllDecks(self):
        # Reload all deck Views
        # Needed if we delete a card both from Physical cards
        # and the decks
        for name in self.openDecks:
            controller = self.openDecks[name][1]
            controller.getView().load()

    def getFilter(self,widget):
        self.__oAbstractCards.getFilter(self.__oMenu)

    def runFilter(self,widget):
        self.__oAbstractCards.runFilter(self.__oMenu.getApplyFilter())
