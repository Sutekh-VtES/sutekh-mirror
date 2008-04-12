# AbstractCardListController.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Controller for the Abstract Card List
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details


"""Controller for the WW Card list"""

from sutekh.gui.AbstractCardView import AbstractCardView

class AbstractCardListController(object):
    """Controller object for the White Wolf cardlist

       Setup options specfic to the Abstract card list,
       and provide needed properties.
       """
    def __init__(self, oFrame, oMainWindow):
        self.__oFrame = oFrame
        self.__oMainWindow = oMainWindow
        self._sFilterType = 'AbstractCard'
        # Create view
        self.__oAbstractCards = AbstractCardView(self, self.__oMainWindow)

    # pylint: disable-msg=W0212
    # we provide read-only access via these properties
    view = property(fget=lambda self: self.__oAbstractCards,
            doc="Associated View")
    frame = property(fget=lambda self: self.__oFrame,
            doc="Associated Frame")
    filtertype = property(fget=lambda self: self._sFilterType,
            doc="Associated Type")
    # pylint: enable-msg=W0212

    def set_card_text(self, sCardName):
        """Set the card text to reflect the selected card."""
        self.__oMainWindow.set_card_text(sCardName)
