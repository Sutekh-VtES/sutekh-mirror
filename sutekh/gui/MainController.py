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
from sutekh.core.SutekhObjectCache import SutekhObjectCache
from sutekh.core.SutekhObjects import AbstractCard

class MainController(object):
    def __init__(self,oConfig):
        # Create object cache
        self.__oSutekhObjectCache = SutekhObjectCache()
        self.__oConfig = oConfig
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
        self.__oCSWin = CardSetManagementWindow(self,self.__oAbstractCardWin,oConfig)
        self.__oCardTextWin = CardTextWindow(self)
        self.__oAbstractCards = AbstractCardView(self,self.__oAbstractCardWin,oConfig)
        self.__aPlugins = []
        for cPlugin in self.__oPluginManager.getCardListPlugins():
            self.__aPlugins.append(cPlugin(self.__oAbstractCards,self.__oAbstractCards.getModel(),'AbstractCard'))

        self.__oCardText = CardTextView(self)
        self.__oPhysicalCards = PhysicalCardController(self.__oPhysicalCardWin,self,oConfig)
        self.__oWinGrp.add_window(self.__oAbstractCardWin)
        self.__oWinGrp.add_window(self.__oPhysicalCardWin)
        self.__oWinGrp.add_window(self.__oCSWin)
        self.__oWinGrp.add_window(self.__oCardTextWin)

        self.__oMenu = MainMenu(self, self.__oAbstractCardWin, self.__oConfig, self.__oAbstractCards, self.__oPhysicalCards.getView())
        # Link
        self.__oAbstractCardWin.addParts(self.__oMenu,self.__oAbstractCards)
        self.__oPhysicalCardWin.addParts(self.__oPhysicalCards)
        self.__oCardTextWin.addParts(self.__oCardText)

        # Restore Window Positions
        for oWin in [self.__oAbstractCardWin,self.__oPhysicalCardWin,self.__oCardTextWin,self.__oCSWin]:
            tPos = self.__oConfig.getWinPos(oWin.get_title())
            if tPos is not None:
                oWin.move(tPos[0],tPos[1])

    def run(self):
        gtk.main()

    def saveWindowPos(self):
        # Save window Positions
        self.__oConfig.preSaveClear()
        for oWin in [self.__oAbstractCardWin,self.__oPhysicalCardWin,self.__oCardTextWin,self.__oCSWin]:
            self.__oConfig.addWinPos(oWin.get_title(),oWin.get_position())
        for sName,(oWindow,oController) in self.__oCSWin.aOpenPhysicalCardSets.iteritems():
            self.__oConfig.addWinPos(oWindow.get_title(),oWindow.get_position())
            self.__oConfig.addCardSet('Physical',sName)
        for sName,(oWindow,oController) in self.__oCSWin.aOpenAbstractCardSets.iteritems():
            self.__oConfig.addWinPos(oWindow.get_title(),oWindow.get_position())
            self.__oConfig.addCardSet('Abstract',sName)

    def actionQuit(self):
        if self.__oConfig.getSaveOnExit():
            self.saveWindowPos()
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
        self.__oCSWin.reloadCardSetLists()

    def getFilter(self,widget):
        self.__oAbstractCards.getFilter(self.__oMenu)

    def runFilter(self,widget):
        self.__oAbstractCards.runFilter(self.__oMenu.getApplyFilter())

    def getMenu(self):
        return self.__oMenu

    def showAboutDialog(self,widget):
        oDlg = SutekhAboutDialog()
        oDlg.run()
        oDlg.destroy()

    def getPluginManager(self):
        return self.__oPluginManager

    def getWinGroup(self):
        return self.__oWinGrp

    def getManager(self):
        return self.__oCSWin
