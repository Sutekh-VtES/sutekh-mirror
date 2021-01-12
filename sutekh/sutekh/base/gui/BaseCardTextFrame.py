# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# The Card Text Frame
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Frame to hold the CardTextView."""

from .ScrolledFrame import ScrolledFrame
from .MessageBus import MessageBus


class BaseCardTextFrame(ScrolledFrame):
    """ScrolledFrame which adds listeners for the 'set_card_text' signal."""
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so lots of public methods

    _sName = 'Card Text'

    def __init__(self, oView, oMainWindow):
        super().__init__(oView, oMainWindow)
        self._oView.clear_text()

    def frame_setup(self):
        """Subscribe to the set_card_text signal"""
        self._oView.clear_text()
        MessageBus.subscribe(MessageBus.Type.CARD_TEXT_MSG, 'set_card_text',
                             self.set_card_text)
        super().frame_setup()

    def cleanup(self, bQuit=False):
        """Cleanup the listeners"""
        MessageBus.unsubscribe(MessageBus.Type.CARD_TEXT_MSG, 'set_card_text',
                               self.set_card_text)
        super().cleanup(bQuit)

    def set_card_text(self, oCard):
        """Hand off card text update to the view"""
        if oCard:
            # Skip doing anything if None
            self._oView.set_card_text(oCard)
