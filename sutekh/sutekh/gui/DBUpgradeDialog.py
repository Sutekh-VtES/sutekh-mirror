# DBUpgradeDialog.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.gui.SutekhDialog import SutekhDialog

class DBUpgradeDialog(SutekhDialog):
    def __init__(self, aMessages):
        # Create Dialog
        super(DBUpgradeDialog, self).__init__("Memory Copy Created", None,
                gtk.DIALOG_MODAL, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                    gtk.STOCK_OK, gtk.RESPONSE_OK))
        oHBox = gtk.HBox(False, 0)
        oIcon = gtk.Image()
        oIcon.set_from_stock(gtk.STOCK_DIALOG_INFO, gtk.ICON_SIZE_DIALOG)
        oHBox.pack_start(oIcon)
        sLabel = "Memory Copy successfully created. Commit Changes?"
        oLabel = gtk.Label(sLabel)
        oHBox.pack_start(oLabel)
        if len(aMessages) > 0:
            sLabelInfo = "The following messages were reported in creating the copy:\n"
            for sStr in aMessages:
                sLabelInfo += '<b>' + sStr + "</b>\n"
            oInfolabel = gtk.Label()
            oInfolabel.set_markup(sLabelInfo)
            self.vbox.pack_start(oInfolabel)
        self.add_button("Test upgraded database?\n" \
                "(No changes are committed)", 1)
        self.set_default_response(gtk.RESPONSE_OK)
        self.vbox.pack_start(oHBox)
        self.show_all()
