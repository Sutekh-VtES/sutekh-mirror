# DeleteCardDialog.py
# Confirm card deletion dialog
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk

class DeleteCardDialog(gtk.Dialog):
    def __init__(self, oParent, aPCSlist):
        # In retrospect, A MesgDialog would also work
        super(DeleteCardDialog, self).__init__("Really Delete?",
            oParent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_YES, gtk.RESPONSE_OK, gtk.STOCK_NO, gtk.RESPONSE_CANCEL))
        oLabel = gtk.Label()
        sText = "Card Present in the following Physical Card Sets:\n"
        for sPCS in aPCSlist:
            sText += "<span foreground = \"blue\">" + sPCS + "</span>\n"
        sText += "<b>Really Delete?</b>"
        oLabel.set_markup(sText)
        oIcon = gtk.Image()
        oIcon.set_from_stock(gtk.STOCK_DIALOG_QUESTION, gtk.ICON_SIZE_DIALOG)
        oHBox = gtk.HBox(False, 0)
        oHBox.pack_start(oIcon, False, False)
        oHBox.pack_end(oLabel, True, False)
        self.vbox.pack_start(oHBox)
        self.connect("response", self.buttonResponse)
        self.bData = False
        self.show_all()

    def getResult(self):
        return self.bData

    def buttonResponse(self, oWidget, iResponse):
        if iResponse ==  gtk.RESPONSE_OK:
            self.bData = True
        self.destroy()
