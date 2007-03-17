# WWFilesDialog.py
# Dialog for handling loading of WW cardlist and rulings
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>

import gtk

class WWFilesDialog(gtk.Dialog):
    def __init__(self,oParent):
        super(WWFilesDialog,self).__init__("Choose White Wolf Files",oParent,\
                      gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,\
                      (gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL,\
                      gtk.RESPONSE_CANCEL))
        oCardListLabel=gtk.Label("White Wolf CardList")
        self.oCardListFileButton=gtk.FileChooserButton("White Wolf cardlist")
        oRulingsLabel=gtk.Label("White Wolf Rulings File (optional)")
        self.oRulingsFileButton=gtk.FileChooserButton("White Wolf rulings file")
        self.vbox.pack_start(oCardListLabel)
        self.vbox.pack_start(self.oCardListFileButton)
        self.vbox.pack_start(oRulingsLabel)
        self.vbox.pack_start(self.oRulingsFileButton)
        self.connect("response",self.handleResponse)
        self.show_all()
        self.sCLName=None
        self.sRulingsName=None

    def handleResponse(self,oWidget,oResponse):
        if oResponse==gtk.RESPONSE_OK:
            self.sCLName=self.oCardListFileButton.get_filename()
            self.sRulingsName=self.oRulingsFileButton.get_filename()

    def getNames(self):
        return (self.sCLName,self.sRulingsName)
