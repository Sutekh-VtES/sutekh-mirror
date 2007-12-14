# AbstractCardListController.py
# Controller for the Abstract Card List
# Copyright 2005,2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from sutekh.gui.AbstractCardView import AbstractCardView

class AbstractCardListController(object):
    def __init__(self, oFrame, oConfig, oMainWindow):
        self.__oConfig = oConfig
        self.__oFrame = oFrame
        self.__oMainWindow = oMainWindow
        self._sFilterType = 'AbstractCard'
        # Create view
        self.__oAbstractCards = AbstractCardView(self, self.__oMainWindow, self.__oConfig)

    view = property(fget=lambda self: self.__oAbstractCards, doc="Associated View")
    frame = property(fget=lambda self: self.__oFrame, doc="Associated Frame")
    filtertype = property(fget=lambda self: self._sFilterType, doc="Associated Type")

    def set_card_text(self, sCardName):
        self.__oMainWindow.set_card_text(sCardName)
