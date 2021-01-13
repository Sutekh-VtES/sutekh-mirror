# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Controller for the Physical Card Collection"""

from .PhysicalCardView import PhysicalCardView
from .MessageBus import MessageBus


class PhysicalCardController:
    """Controller for the Physical Card Collection.

       Provide settings needed for the Physical Card List,
       and suitable card manipulation methods.
       """
    def __init__(self, oFrame, oMainWindow):
        self.__oMainWin = oMainWindow
        self.__oFrame = oFrame
        self.__oView = PhysicalCardView(self, oMainWindow,
                                        oMainWindow.config_file)
        self.__oModel = self.__oView.get_model()
        self._sFilterType = 'PhysicalCard'
        self.model.set_controller(self)

    # pylint: disable=protected-access
    # We provide read access to these items via these properties
    view = property(fget=lambda self: self.__oView, doc="Associated View")
    model = property(fget=lambda self: self.__oModel,
                     doc="View's Model")
    frame = property(fget=lambda self: self.__oFrame, doc="Associated Frame")
    filtertype = property(fget=lambda self: self._sFilterType,
                          doc="Associated Type")
    # pylint: enable=protected-access

    def cleanup(self):
        """Remove the signal handlers."""
        self.model.cleanup()

    # pylint: disable=no-self-use
    # making this a function would not be convenient
    def set_card_text(self, oCard):
        """Set the card text to reflect the selected card."""
        MessageBus.publish(MessageBus.Type.CARD_TEXT_MSG,
                           'set_card_text', oCard)

    # pylint: enable=no-self-use
