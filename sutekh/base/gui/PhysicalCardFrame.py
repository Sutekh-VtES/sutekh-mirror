# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Frame holding the Physical Card List
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Frame which holds the PhysicalCardView"""

from ..core.BaseObjects import PhysicalCard
from .CardListFrame import CardListFrame
from .PhysicalCardController import PhysicalCardController
from .PhysicalCardMenu import PhysicalCardMenu


class PhysicalCardFrame(CardListFrame):
    # pylint: disable=R0904
    # gtk.Widget, so many public methods
    """Frame which holds the Physical Card Collection View.

       Set the title, and menus as needed for the card collection.
       """
    _cModelType = PhysicalCard
    _sName = "Full Card List"

    def __init__(self, oMainWindow):
        super(PhysicalCardFrame, self).__init__(oMainWindow)
        self.set_title(self._sName)
        self.set_name("physical card list")

        self._oController = PhysicalCardController(self, oMainWindow)

        self.init_plugins()

        self._oMenu = PhysicalCardMenu(self, self._oController, oMainWindow)
        self.add_parts()

    def get_menu_name(self):
        """Get the menu key"""
        return self._sName

    def cleanup(self, bQuit=False):
        """Cleanup function called before pane is removed by the Main Window"""
        super(PhysicalCardFrame, self).cleanup(bQuit)
        self._oController.cleanup()
