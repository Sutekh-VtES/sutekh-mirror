# EditAnnotationsDialog.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Dialog for handling Card Set Annotations"""

import gtk
from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

class EditAnnotationsDialog(SutekhDialog):
    """Actaul dialog"""
    # pylint: disable-msg=R0904
    # gtk class, so many pulic methods
    def __init__(self, sTitle, oParent, sCurName, sCurAnnotations):
        super(EditAnnotationsDialog, self).__init__(sTitle, oParent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                        gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.connect("response", self.button_response)
        oNameLabel = gtk.Label("Card Set : " + sCurName)
        oAnnotateLabel = gtk.Label("Annotations : ")
        oTextView = gtk.TextView()
        self.oBuffer = oTextView.get_buffer()
        if sCurAnnotations is not None:
            self.oBuffer.set_text(sCurAnnotations)
        # pylint: disable-msg=E1101
        # vbox confuses pylint
        self.vbox.pack_start(oNameLabel, expand=False)
        self.vbox.pack_start(oAnnotateLabel, expand=False)
        oScrolledWin = AutoScrolledWindow(oTextView)
        self.set_default_size(500, 500)
        self.vbox.pack_start(oScrolledWin, expand=True)
        self.show_all()
        self.sAnnotations = sCurAnnotations

    # pylint: disable-msg=W0613
    # oWidget required by function signature
    def button_response(self, oWidget, iResponse):
        """Process the response to the dialog."""
        if iResponse == gtk.RESPONSE_OK:
            self.sAnnotations = self.oBuffer.get_text(
                    self.oBuffer.get_start_iter(), self.oBuffer.get_end_iter())
        self.destroy()

    def get_data(self):
        """Return the contents of the text buffer"""
        return self.sAnnotations
