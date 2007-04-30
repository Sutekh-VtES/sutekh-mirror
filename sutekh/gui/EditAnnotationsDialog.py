# Dialog for handling Card Set Annotations
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>

import gtk
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

class EditAnnotationsDialog(gtk.Dialog):
    def __init__(self,sTitle,oParent,curName,curAnnotations):
        super(EditAnnotationsDialog,self).__init__(sTitle,oParent,\
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                buttons=(gtk.STOCK_OK, gtk.RESPONSE_OK, \
                        gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.connect("response",self.buttonResponse)
        nameLabel=gtk.Label("Card Set : "+curName)
        annotateLabel=gtk.Label("Annotations : ")
        oTextView=gtk.TextView()
        self.oBuffer=oTextView.get_buffer()
        if curAnnotations is not None:
            self.oBuffer.set_text(curAnnotations)
        self.vbox.pack_start(nameLabel,expand=False)
        self.vbox.pack_start(annotateLabel,expand=False)
        oSW=AutoScrolledWindow(oTextView)
        self.set_default_size(500,500)
        self.vbox.pack_start(oSW,expand=True)
        self.show_all()
        self.sAnnotations=curAnnotations

    def buttonResponse(self,widget,response):
        if response == gtk.RESPONSE_OK:
            self.sAnnotations=self.oBuffer.get_text(self.oBuffer.get_start_iter(),self.oBuffer.get_end_iter())
        self.destroy()

    def getData(self):
        return self.sAnnotations
