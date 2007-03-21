# Dialog for handling Card Set Annotations
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>

import gtk

class EditAnnotationsDialog(gtk.Dialog):
    def __init__(self,sTitle,oParent,curName,curAnnotations):
        super(EditAnnotationsDialog,self).__init__(sTitle,oParent,\
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK, \
                        gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.connect("response",self.buttonResponse)
        nameLabel=gtk.Label("Card Set : "+curName)
        annotateLabel=gtk.Label("Annotations : ")
        self.oAnnotations=gtk.Entry()
        self.oAnnotations.set_text(curAnnotations)
        self.vbox.pack_start(nameLabel)
        self.vbox.pack_start(annotateLabel)
        self.vbox.pack_start(self.oAnnotations)
        self.show_all()
        self.sAnnotations=curAnnotations

    def buttonResponse(self,widget,response):
        if response == gtk.RESPONSE_OK:
            self.sAnnotations=self.oAnnotations.get_text()
        self.destroy()

    def getData(self):
        return self.sAnnotations
