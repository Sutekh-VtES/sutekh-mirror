# AbstractCardListFrame.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Display the Abstract Card List
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Frame for the WW Card List"""

from sutekh.core.SutekhObjects import AbstractCard
from sutekh.gui.CardListFrame import CardListFrame
from sutekh.gui.AbstractCardListController import AbstractCardListController
from sutekh.gui.AbstractCardListMenu import AbstractCardListMenu

class AbstractCardListFrame(CardListFrame):
    """Frame for the WW Card List."""
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    def __init__(self, oMainWindow):
        super(AbstractCardListFrame, self).__init__(oMainWindow)

        self._sName = "White Wolf Card List"
        self.set_title(self._sName)
        self.set_name("abstract card list")

        self._oController = AbstractCardListController(self,
                oMainWindow)

        self._cModelType = AbstractCard

        self.init_plugins()

        self._oMenu = AbstractCardListMenu(self, self._oController,
                oMainWindow)

        self.add_parts()
