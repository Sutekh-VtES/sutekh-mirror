# CountCardSetCards.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>, Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.core.SutekhObjects import IAbstractCard, AbstractCardSet, \
                                      PhysicalCard, PhysicalCardSet
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.CardListModel import CardListModelListener

class CountCardSetCards(CardListPlugin,CardListModelListener):
    dTableVersions = {PhysicalCardSet : [1,2,3,4],
                      AbstractCardSet : [1,2,3]}
    aModelsSupported = [AbstractCardSet, PhysicalCardSet,
            PhysicalCard]

    def __init__(self,*args,**kwargs):
        super(CountCardSetCards,self).__init__(*args,**kwargs)

        self.__iTot = 0
        self.__iCrypt = 0
        self.__iLibrary = 0

        # We only add listeners to windows we're going to display the toolbar
        # on
        if self.check_versions() and self.check_model_type():
            self.model.addListener(self)

    def __id_card(self,oCard):
        sType = list(oCard.cardtype)[0].name
        if sType == 'Vampire' or sType == 'Imbued':
            return 'Crypt'
        else:
            return 'Library'

    def get_toolbar_widget(self):
        """
        Overrides method from base class.
        """
        if not self.check_versions() or not self.check_model_type():
            return None

        self.oTextLabel = gtk.Label('Total Cards : 0 Crypt Cards : 0 Library Cards : 0')

        aAbsCards = [IAbstractCard(x) for x in
                self.model.getCardIterator(self.model.getCurrentFilter())]
        self.load(aAbsCards)

        return self.oTextLabel

    def update_numbers(self):
        self.oTextLabel.set_markup('Total Cards : <b>' + str(self.__iTot) +
                '</b>  Crypt Cards : <b>' + str(self.__iCrypt) +
                '</b> Library Cards : <b>' + str(self.__iLibrary) + '</b>')

    def load(self, aAbsCards):
        self.__iCrypt = 0
        self.__iLibrary = 0
        self.__iTot = len(aAbsCards)
        for oAbsCard in aAbsCards:
            if self.__id_card(oAbsCard) == 'Crypt':
                self.__iCrypt += 1
            else:
                self.__iLibrary += 1
        self.update_numbers()

    def alterCardCount(self, oCard, iChg):
        self.__iTot += iChg
        if self.__id_card(oCard) == 'Crypt':
            self.__iCrypt += iChg
        else:
            self.__iLibrary += iChg
        self.update_numbers()

    def addNewCard(self, oCard):
        self.__iTot += 1
        if self.__id_card(oCard) == 'Crypt':
            self.__iCrypt += 1
        else:
            self.__iLibrary += 1
        self.update_numbers()

plugin = CountCardSetCards
