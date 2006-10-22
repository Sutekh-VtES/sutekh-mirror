# CreateCardSetDialog.py
# Dialog to create a new PhysicalCardSet or AbstrctCardSet
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk

class CreateCardSetDialog(gtk.Dialog):
    def __init__(self,parent,sType):
        super(CreateCardSetDialog,self).__init__("Choose "+sType+" Card Set Name", \
              parent,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
              ( gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.Entry=gtk.Entry(50)
        self.vbox.pack_start(self.Entry)
        self.connect("response", self.buttonResponse)
        self.Entry.connect("activate", self.buttonResponse,1)
        self.Data = None
        self.show_all()

    def getName(self):
        return self.Data

    def buttonResponse(self,widget,response):
       if response == 1 or response ==  gtk.RESPONSE_OK:
          self.Data = self.Entry.get_text()
          # We use _ as a deliminator for dragging (see CardSetView)
          # so change any _'s to spaces
          self.Data=self.Data.replace("_"," ")

       self.destroy()
