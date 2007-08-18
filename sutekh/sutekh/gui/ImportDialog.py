# Dialog for handling File Import Events
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>

import gtk

class ImportDialog(gtk.FileChooserDialog):
    def __init__(self,sTitle,oParent):
        super(ImportDialog,self).__init__(sTitle,oParent,\
                action=gtk.FILE_CHOOSER_ACTION_OPEN,
                buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK, \
                        gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.connect("response",self.buttonResponse)
        self.set_local_only(True)
        self.set_select_multiple(False)
        self.Name = None

    def buttonResponse(self,widget,response):
        if response == gtk.RESPONSE_OK:
            self.Name = self.get_filename()
        self.destroy()

    def getName(self):
        return self.Name
