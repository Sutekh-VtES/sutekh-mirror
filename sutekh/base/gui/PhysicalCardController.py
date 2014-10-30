# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Controller for the Physical Card Collection"""

from .PhysicalCardView import PhysicalCardView
from .MessageBus import MessageBus, CARD_TEXT_MSG


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
        self.__oModel = self.__oView.get_model()
        self._sFilterType = 'PhysicalCard'
        self.model.set_controller(self)

    # pylint: disable=W0212
    # We provide read access to these items via these properties
    view = property(fget=lambda self: self.__oView, doc="Associated View")
    model = property(fget=lambda self: self.__oModel,
                     doc="View's Model")
    frame = property(fget=lambda self: self.__oFrame, doc="Associated Frame")
    filtertype = property(fget=lambda self: self._sFilterType,
                          doc="Associated Type")
    # pylint: enable=W0212

    def cleanup(self):
        """Remove the signal handlers."""
        self.model.cleanup()

    # pylint: disable=R0201
    # making this a function would not be convenient
    def set_card_text(self, oCard):
        """Set the card text to reflect the selected card."""
        MessageBus.publish(CARD_TEXT_MSG, 'set_card_text', oCard)

    # pylint: enable=R0201

    def toggle_expansion(self, oWidget):
        """Toggle whether the expansion information is shown."""
        self.__oModel.bExpansions = oWidget.active
        self.__oView.reload_keep_expanded()

    def toggle_icons(self, oWidget):
        """Toggle the icons display"""
        self.__oModel.bUseIcons = oWidget.active
        self.__oView.reload_keep_expanded()
