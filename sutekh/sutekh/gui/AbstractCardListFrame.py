# AbstractCardListFrame.py
# Display the Abstract Card List
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from sutekh.core.SutekhObjects import AbstractCard
from sutekh.gui.CardListFrame import CardListFrame
from sutekh.gui.AbstractCardListController import AbstractCardListController
from sutekh.gui.AbstractCardListMenu import AbstractCardListMenu

class AbstractCardListFrame(CardListFrame):
    def __init__(self, oMainWindow, oConfig):
        super(AbstractCardListFrame, self).__init__(oMainWindow, oConfig)

        self._sName = "White Wolf CardList"
        self.set_title(self._sName)
        self.set_name("abstract card list")

        self._oC = AbstractCardListController(self, oConfig, oMainWindow)

        self._cModelType = AbstractCard

        self.init_plugins()

        self._oMenu = AbstractCardListMenu(self, self._oC, oMainWindow)

        self.add_parts()
