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
        oCardListLabel=gtk.Label("Choose White Wolf cardlist file")
        self.oCardListFile=gtk.FileChooserWidget(gtk.FILE_CHOOSER_ACTION_OPEN)
        oRulingsLabel=gtk.Label("Choose White Wolf Rulings file (optional)")
        self.oRulingsFile=gtk.FileChooserWidget(gtk.FILE_CHOOSER_ACTION_OPEN)
        self.oCardListFile.set_local_only(False)
        self.oRulingsFile.set_local_only(False)
        self.vbox.pack_start(oCardListLabel)
        self.vbox.pack_start(self.oCardListFile)
        self.vbox.pack_start(oRulingsLabel)
        self.vbox.pack_start(self.oRulingsFile)
        self.oRulingsFile.set_select_multiple(False)
        self.oCardListFile.set_select_multiple(False)
        self.connect("response",self.handleResponse)
        self.show_all()
        self.sCLName=None
        self.sRulingsName=None

    def handleResponse(self,oWidget,oResponse):
        if oResponse==gtk.RESPONSE_OK:
            self.sCLName=self.oCardListFile.get_filename()
            self.sRulingsName=self.oRulingsFile.get_filename()

    def getNames(self):
        return (self.sCLName,self.sRulingsName)
