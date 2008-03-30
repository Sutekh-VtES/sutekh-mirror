# PhysicalCardFrame.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Frame holding the Physical Card List
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

from sutekh.core.SutekhObjects import PhysicalCard
from sutekh.gui.CardListFrame import CardListFrame
from sutekh.gui.PhysicalCardController import PhysicalCardController
from sutekh.gui.PhysicalCardMenu import PhysicalCardMenu

class PhysicalCardFrame(CardListFrame):
    def __init__(self, oMainWindow, oConfig):
        super(PhysicalCardFrame, self).__init__(oMainWindow, oConfig)
        self._sName = "My Collection"
        self.set_title(self._sName)
        self.set_name("physical card list")

        self._oC = PhysicalCardController(self, oConfig, oMainWindow)

        self._cModelType = PhysicalCard

        self.init_plugins()

        self._oMenu = PhysicalCardMenu(self, self._oC, oMainWindow)
        self.add_parts()
        self._oC.view.check_editable()

