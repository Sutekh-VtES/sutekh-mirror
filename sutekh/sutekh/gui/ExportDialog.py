# Dialog for handling File Export Events
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>

import gtk

class ExportDialog(gtk.FileChooserDialog):
    def __init__(self,sTitle,oParent):
        super(ExportDialog,self).__init__(sTitle,oParent,\
                action=gtk.FILE_CHOOSER_ACTION_SAVE,
                buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK, \
                        gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.connect("response",self.buttonResponse)
        self.set_local_only(True)
        self.set_do_overwrite_confirmation(True)
        self.Name=None

    def buttonResponse(self,widget,response):
        if response == gtk.RESPONSE_OK:
            self.Name=self.get_filename()
        self.destroy()

    def getName(self):
        return self.Name
