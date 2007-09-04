# DeleteCardSetDialog.py
# Confirm card set deletion dialog
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk

class DeleteCardSetDialog(gtk.Dialog):
    def __init__(self, oParent, sName, sType):
        super(DeleteCardSetDialog, self).__init__("Really Delete?",
            oParent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_YES, gtk.RESPONSE_OK, gtk.STOCK_NO, gtk.RESPONSE_CANCEL))
        oLabel = gtk.Label(sType + " Card Set " + sName + \
                " Not Empty - Really Delete?")
        oLabel.show()
        oIcon = gtk.Image()
        oIcon.set_from_stock(gtk.STOCK_DIALOG_QUESTION, gtk.ICON_SIZE_DIALOG)
        oIcon.show()
        oHBox = gtk.HBox(False, 0)
        oHBox.pack_start(oIcon, False, False)
        oHBox.pack_end(oLabel, True, False)
        oHBox.show()
        self.vbox.pack_start(oHBox)
        self.connect("response", self.buttonResponse)
        self.bData = False

    def getResult(self):
        return self.bData

    def buttonResponse(self, oWidget, iResponse):
        if iResponse ==  gtk.RESPONSE_OK:
            self.bData = True
        self.destroy()
