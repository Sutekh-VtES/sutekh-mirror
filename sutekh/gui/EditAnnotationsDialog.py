# Dialog for handling Card Set Annotations
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>

import gtk
from sutekh.gui.SutekhDialog import SutekhDialog
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

class EditAnnotationsDialog(SutekhDialog):
    def __init__(self, sTitle, oParent, sCurName, sCurAnnotations):
        super(EditAnnotationsDialog, self).__init__(sTitle, oParent,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_OK, gtk.RESPONSE_OK,
                        gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.connect("response", self.buttonResponse)
        oNameLabel = gtk.Label("Card Set : " + sCurName)
        oAnnotateLabel = gtk.Label("Annotations : ")
        oTextView = gtk.TextView()
        self.oBuffer = oTextView.get_buffer()
        if sCurAnnotations is not None:
            self.oBuffer.set_text(sCurAnnotations)
        self.vbox.pack_start(oNameLabel, expand=False)
        self.vbox.pack_start(oAnnotateLabel, expand=False)
        oScrolledWin = AutoScrolledWindow(oTextView)
        self.set_default_size(500, 500)
        self.vbox.pack_start(oScrolledWin, expand=True)
        self.show_all()
        self.sAnnotations = sCurAnnotations

    def buttonResponse(self, oWidget, iResponse):
        if iResponse == gtk.RESPONSE_OK:
            self.sAnnotations = self.oBuffer.get_text(self.oBuffer.get_start_iter(),
                    self.oBuffer.get_end_iter())
        self.destroy()

    def getData(self):
        return self.sAnnotations
