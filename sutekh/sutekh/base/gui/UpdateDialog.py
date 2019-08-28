# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Database to prompt for datapack updates and so forth."""

import gtk
from .SutekhDialog import SutekhDialog


class UpdateDialog(SutekhDialog):
    # pylint: disable=too-many-public-methods
    # gtk.Widget, so many public methods
    """Dialog which prompts the user if datapack or other updates
       are available."""
    def __init__(self, aMessages):
        # Create Dialog
        super(UpdateDialog, self).__init__(
            "Updates available", None,
            gtk.DIALOG_MODAL, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                               gtk.STOCK_OK, gtk.RESPONSE_OK))
        oHBox = gtk.HBox(False, 0)
        oIcon = gtk.Image()
        oIcon.set_from_stock(gtk.STOCK_DIALOG_INFO, gtk.ICON_SIZE_DIALOG)
        oHBox.pack_start(oIcon)
        self.vbox.pack_start(oHBox)
        sLabel = "Updates are available. Download now?"
        oLabel = gtk.Label(sLabel)
        oHBox.pack_start(oLabel)
        sLabelInfo = "The following updates are available:\n\n"
        sLabelInfo += "\n".join(aMessages)
        oInfolabel = gtk.Label()
        oInfolabel.set_markup(sLabelInfo)
        self.vbox.pack_start(oInfolabel)
        self.set_default_response(gtk.RESPONSE_OK)
        self.show_all()
