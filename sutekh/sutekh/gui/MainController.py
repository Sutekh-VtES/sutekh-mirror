import gtk
from sqlobject import SQLObjectNotFound
from PhysicalCardController import PhysicalCardController
from MainWindow import MainWindow
from MainMenu import MainMenu
from CardTextView import CardTextView
from AbstractCardView import AbstractCardView
from SutekhObjects import *

class MainController(object):
    def __init__(self):
        # Create Sub-Controllers
        self.__oPhysicalCards = PhysicalCardController(self)
    
        # Create Views
        self.__oWin = MainWindow(self)
        self.__oMenu = MainMenu(self)
        self.__oCardText = CardTextView(self)
        self.__oAbstractCards = AbstractCardView(self)
                
        # Link
        self.__oWin.addParts(self.__oMenu,self.__oCardText, \
                             self.__oAbstractCards,self.__oPhysicalCards.getView())
        
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
