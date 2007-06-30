# MainController.py
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sqlobject import SQLObjectNotFound
from sutekh.gui.PhysicalCardController import PhysicalCardController
from sutekh.gui.MainWindow import MainWindow
from sutekh.gui.CardTextWindow import CardTextWindow
from sutekh.gui.PhysicalCardWindow import PhysicalCardWindow
from sutekh.gui.MainMenu import MainMenu
from sutekh.gui.CardTextView import CardTextView
from sutekh.gui.AbstractCardView import AbstractCardView
from sutekh.gui.PluginManager import PluginManager
from sutekh.gui.AboutDialog import SutekhAboutDialog
from sutekh.gui.CardSetManagementWindow import CardSetManagementWindow
from sutekh.SutekhObjectCache import SutekhObjectCache
from sutekh.SutekhObjects import AbstractCard

class MainController(object):
    def __init__(self):
        # Create object cache
        self.__oSutekhObjectCache = SutekhObjectCache()
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
        self.__oCSWin = CardSetManagementWindow(self,self.__oAbstractCardWin)
        self.__oCardTextWin = CardTextWindow(self)
        self.__oAbstractCards = AbstractCardView(self,self.__oAbstractCardWin)
        self.__aPlugins = []
        for cPlugin in self.__oPluginManager.getCardListPlugins():
            self.__aPlugins.append(cPlugin(self.__oAbstractCards,self.__oAbstractCards.getModel(),'AbstractCard'))

        self.__oMenu = MainMenu(self,self.__oAbstractCardWin)
        self.__oCardText = CardTextView(self)
        self.__oPhysicalCards = PhysicalCardController(self.__oPhysicalCardWin,self)
        self.__oWinGrp.add_window(self.__oAbstractCardWin)
        self.__oWinGrp.add_window(self.__oPhysicalCardWin)
        self.__oWinGrp.add_window(self.__oCSWin)
        self.__oWinGrp.add_window(self.__oCardTextWin)

        # Link
        self.__oAbstractCardWin.addParts(self.__oMenu,self.__oAbstractCards)
        self.__oPhysicalCardWin.addParts(self.__oPhysicalCards)
        self.__oCardTextWin.addParts(self.__oCardText)

    def run(self):
        gtk.main()

    def actionQuit(self):
        gtk.main_quit()

    def getPlugins(self):
        return self.__aPlugins

    def setCardText(self,sCardName):
        try:
            oCard = AbstractCard.byCanonicalName(sCardName.lower())
            self.__oCardText.setCardText(oCard)
        except SQLObjectNotFound:
            pass

    def reloadAll(self):
        self.__oAbstractCards.load()
        self.__oPhysicalCards.getView().load()
        self.__oCSWin.reloadAll()

    def getFilter(self,widget):
        self.__oAbstractCards.getFilter(self.__oMenu)

    def runFilter(self,widget):
        self.__oAbstractCards.runFilter(self.__oMenu.getApplyFilter())

    def showAboutDialog(self,widget):
        oDlg = SutekhAboutDialog()
        oDlg.run()
        oDlg.destroy()

    def getPluginManager(self):
        return self.__oPluginManager

    def getWinGroup(self):
        return self.__oWinGrp

    def getCSManWin(self):
        return self.__oCSWin
