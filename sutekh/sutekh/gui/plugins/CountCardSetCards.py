# CountCardSetCards.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>, Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.core.SutekhObjects import IAbstractCard
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.CardListModel import CardListModelListener

class CountCardSetCards(CardListPlugin,CardListModelListener):
    dTableVersions = {"AbstractCardSet" : [1,2,3],
                      "PhysicalCardSet" : [1,2,3]}
    aModelsSupported = ["AbstractCardSet","PhysicalCardSet","PhysicalCard"]

    def __init__(self,*args,**kwargs):
        super(CountCardSetCards,self).__init__(*args,**kwargs)

        self.__iTot = 0
        self.__iCrypt = 0
        self.__iLibrary = 0

        # We only add listeners to windows we're going to display the toolbar
        # on
        if self.checkVersions() and self.checkModelType():
            self.model.addListener(self)

    def __idCard(self,oCard):
        sType = list(oCard.cardtype)[0].name
        if sType == 'Vampire' or sType == 'Imbued':
            return 'Crypt'
        else:
            return 'Library'

    def getToolbarWidget(self):
        """
        Overrides method from base class.
        """
        if not self.checkVersions() or not self.checkModelType():
            return None

        iHBox = gtk.HBox(False,2)
        wTotalTextLabel = gtk.Label('Total Cards : ')
        wCryptTextLabel = gtk.Label('Crypt Cards : ')
        wLibraryTextLabel = gtk.Label('Library Cards : ')
        self.wTotalLabel = gtk.Label('0')
        self.wCryptLabel = gtk.Label('0')
        self.wLibraryLabel = gtk.Label('0')

        iHBox.pack_start(wTotalTextLabel)
        iHBox.pack_start(self.wTotalLabel)
        iHBox.pack_start(wCryptTextLabel)
        iHBox.pack_start(self.wCryptLabel)
        iHBox.pack_start(wLibraryTextLabel)
        iHBox.pack_start(self.wLibraryLabel)

        self.load()

        return iHBox

    def updateNumbers(self):
        self.wTotalLabel.set_markup('<b>' + str(self.__iTot) + '</b>')
        self.wCryptLabel.set_markup('<b>' + str(self.__iCrypt) + '</b>')
        self.wLibraryLabel.set_markup('<b>' + str(self.__iLibrary) + '</b>')

    def load(self):
        self.__iCrypt = 0
        self.__iLibrary = 0
        aAllCards = list(self.model.getCardIterator(self.model.getSelectFilter()))
        self.__iTot = len(aAllCards)
        for oCard in aAllCards:
            sType = self.__idCard(IAbstractCard(oCard))
            if sType == 'Crypt':
                self.__iCrypt += 1
            else:
                self.__iLibrary += 1
        self.updateNumbers()

    def alterCardCount(self,oCard,iChg):
        self.__iTot += iChg
        if self.__idCard(oCard) == 'Crypt':
            self.__iCrypt += iChg
        else:
            self.__iLibrary += iChg
        self.updateNumbers()

    def addNewCard(self,oCard):
        self.__iTot += 1
        if self.__idCard(oCard) == 'Crypt':
            self.__iCrypt += 1
        else:
            self.__iLibrary += 1
        self.updateNumbers()

plugin = CountCardSetCards
