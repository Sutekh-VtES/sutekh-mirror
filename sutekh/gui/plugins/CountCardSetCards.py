# CountCardSetCards.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Display a running total of the cards in a card set"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet, IAbstractCard
from sutekh.gui.PluginManager import CardListPlugin
from sutekh.gui.CardListModel import CardListModelListener
from sutekh.SutekhUtility import is_crypt_card

TOT_FORMAT = 'Tot: <b>%(tot)d</b> L: <b>%(lib)d</b> C: <b>%(crypt)d</b>'
TOT_TOOLTIP = 'Total Cards: <b>%(tot)d</b> (Library: <b>%(lib)d</b>' \
        ' Crypt: <b>%(crypt)d</b>)'


class CountCardSetCards(CardListPlugin, CardListModelListener):
    """Listen to changes on the card list views, and display a toolbar
       containing a label with a running count of the cards in the card
       set, the library cards and the crypt cards
       """
    dTableVersions = {PhysicalCardSet : [5, 6]}
    aModelsSupported = [PhysicalCardSet]


    # pylint: disable-msg=W0142
    # **magic OK here
    def __init__(self, *args, **kwargs):
        super(CountCardSetCards, self).__init__(*args, **kwargs)

        self.__iTot = 0
        self.__iCrypt = 0
        self.__iLibrary = 0
        self.__oTextLabel = None

        # We only add listeners to windows we're going to display the toolbar
        # on
        if self.check_versions() and self.check_model_type():
            self.model.add_listener(self)
    # pylint: enable-msg=W0142

    def get_toolbar_widget(self):
        """Overrides method from base class."""
        if not self.check_versions() or not self.check_model_type():
            return None

        self.__oTextLabel = gtk.Label(TOT_FORMAT % {'tot' : 0,
            'crypt' : 0, 'lib' : 0})
        if hasattr(self.__oTextLabel, 'set_tooltip_markup'):
            self.__oTextLabel.set_tooltip_markup(TOT_TOOLTIP % {
            'tot' : 0, 'crypt' : 0, 'lib' : 0})

        self.__oTextLabel.show()
        return self.__oTextLabel

    def update_numbers(self):
        """Update the label"""
        # Timing issues mean that this can be called before text label has
        # been properly realised, so we need this guard case
        if self.__oTextLabel:
            self.__oTextLabel.set_markup(TOT_FORMAT % {'tot' : self.__iTot,
                'crypt' : self.__iCrypt, 'lib' : self.__iLibrary})
            if hasattr(self.__oTextLabel, 'set_tooltip_markup'):
                self.__oTextLabel.set_tooltip_markup(TOT_TOOLTIP % {
                'tot' : self.__iTot, 'crypt' : self.__iCrypt,
                'lib' : self.__iLibrary})

    def load(self, aCards):
        """Listen on load events & update counts"""
        self.__iCrypt = 0
        self.__iLibrary = 0
        self.__iTot = len(aCards)
        for oCard in aCards:
            oAbsCard = IAbstractCard(oCard)
            if is_crypt_card(oAbsCard):
                self.__iCrypt += 1
            else:
                self.__iLibrary += 1
        self.update_numbers()

    def alter_card_count(self, oCard, iChg):
        """respond to alter_card_count events"""
        self.__iTot += iChg
        oAbsCard = IAbstractCard(oCard)
        if is_crypt_card(oAbsCard):
            self.__iCrypt += iChg
        else:
            self.__iLibrary += iChg
        self.update_numbers()

    def add_new_card(self, oCard, iCnt):
        """response to add_new_card events"""
        self.__iTot += iCnt
        oAbsCard = IAbstractCard(oCard)
        if is_crypt_card(oAbsCard):
            self.__iCrypt += iCnt
        else:
            self.__iLibrary += iCnt
        self.update_numbers()

plugin = CountCardSetCards
