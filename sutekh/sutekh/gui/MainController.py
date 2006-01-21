import gtk
from sqlobject import SQLObjectNotFound
from PhysicalCardController import PhysicalCardController
from MainWindow import MainWindow
from PhysicalCardWindow import PhysicalCardWindow
from MainMenu import MainMenu
from CardTextView import CardTextView
from AbstractCardView import AbstractCardView
from SutekhObjects import *

class MainController(object):
    def __init__(self):
        # Create Sub-Controllers
        self.__oPhysicalCards = PhysicalCardController(self)
    
        # Create Views
        self.__oWinGrp = gtk.WindowGroup()
        # Need a group as we'll be adding and removing Deck View windows,
        # and they should all be blocked by the appropriate dialogs
        self.__oAbstractCardWin = MainWindow(self)
        self.__oPhysicalCardWin = PhysicalCardWindow(self)
        self.__oMenu = MainMenu(self)
        self.__oCardText = CardTextView(self)
        self.__oAbstractCards = AbstractCardView(self)
        self.__oWinGrp.add_window(self.__oAbstractCardWin)
        self.__oWinGrp.add_window(self.__oPhysicalCardWin)

        self.DeckWinCount = 0
        # In place as I want to limit the maximum number of deck views open
        # to 3 (should change this later as arbitary restrictions not good)
                
        # Link
        self.__oAbstractCardWin.addParts(self.__oMenu,self.__oCardText, \
                             self.__oAbstractCards)
        self.__oPhysicalCardWin.addParts(self.__oMenu, \
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


           

