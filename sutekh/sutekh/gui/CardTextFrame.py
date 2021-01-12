# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# The Card Text Frame
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006, 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Frame to hold the CardTextView."""

from sutekh.gui.CardTextView import CardTextView
from sutekh.base.gui.BaseCardTextFrame import BaseCardTextFrame


class CardTextFrame(BaseCardTextFrame):
    """Frame which holds the CardTextView."""
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so lots of public methods
    def __init__(self, oMainWindow, oIconManager):
        oView = CardTextView(oIconManager, oMainWindow)
        super().__init__(oView, oMainWindow)
