# AbstractCardListController.py
# Controller for the Abstract Card List
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.gui.AbstractCardView import AbstractCardView
from sutekh.gui.PluginManager import PluginManager
from sutekh.core.SutekhObjects import AbstractCard

class AbstractCardListController(object):
    def __init__(self, oFrame, oConfig, oMainWindow):
        self.__oConfig = oConfig
        self.__oFrame = oFrame
        self.__oMainWindow = oMainWindow
        # Create PluginManager
        #self.__oPluginManager = PluginManager()
        #self.__oPluginManager.loadPlugins()
        # Create Sub-Controllers
        # Create Views
        # Need a group as we'll be adding and removing Card Set View windows,
        # and they should all be blocked by the appropriate dialogs
        self.__oAbstractCards = AbstractCardView(self, self.__oMainWindow, self.__oConfig)
        #self.__aPlugins = []
        #for cPlugin in self.__oPluginManager.getCardListPlugins():
        #    self.__aPlugins.append(cPlugin(self.__oAbstractCards,self.__oAbstractCards.getModel(),'AbstractCard'))
        self.__oFrame.addParts(self.__oAbstractCards)

    view = property(fget=lambda self: self.__oAbstractCards, doc="Associated View")
    frame = property(fget=lambda self: self.__oFrame, doc="Associated Frame")

    def getPlugins(self):
        return self.__aPlugins

    def setCardText(self, sCardName):
        self.__oMainWindow.set_card_text(sCardName)
        
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
