# PhysicalCardController.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Controller for the Physical Card Collection"""

import gtk
from sqlobject import SQLObjectNotFound
from sutekh.gui.DBSignals import send_reload_signal
from sutekh.gui.SutekhDialog import do_complaint
from sutekh.gui.PhysicalCardView import PhysicalCardView
from sutekh.core.SutekhObjects import PhysicalCard, AbstractCard, \
        IExpansion, MapPhysicalCardToPhysicalCardSet

class PhysicalCardController(object):
    """Controller for the Physical Card Collection.

       Provide settings needed for the Physical Card List,
       and suitable card manipulation methods.
       """
    def __init__(self, oFrame, oMainWindow):
        self.__oMainWin = oMainWindow
        self.__oFrame = oFrame
        self.__oView = PhysicalCardView(self, oMainWindow,
                oMainWindow.config_file)
        self._sFilterType = 'PhysicalCard'

    # pylint: disable-msg=W0212
    # We provide read access to these items via these properties
    view = property(fget=lambda self: self.__oView, doc="Associated View")
    model = property(fget=lambda self: self.__oView._oModel,
            doc="View's Model")
    frame = property(fget=lambda self: self.__oFrame, doc="Associated Frame")
    filtertype = property(fget=lambda self: self._sFilterType,
            doc="Associated Type")
    # pylint: enable-msg=W0212

    def set_card_text(self, sCardName):
        """Set the card text to reflect the selected card."""
        self.__oMainWin.set_card_text(sCardName)
