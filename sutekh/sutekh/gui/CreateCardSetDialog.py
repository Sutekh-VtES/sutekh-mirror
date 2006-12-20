# CreateCardSetDialog.py
# Dialog to create a new PhysicalCardSet or AbstrctCardSet
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk

class CreateCardSetDialog(gtk.Dialog):
    def __init__(self,parent,sType):
        super(CreateCardSetDialog,self).__init__(sType+" Card Set Details", \
              parent,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
              ( gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.Entry=gtk.Entry(50)
        oNameLabel = gtk.Label("Card Set Name : ")
        self.vbox.pack_start(oNameLabel)
        self.vbox.pack_start(self.Entry)
        self.connect("response", self.buttonResponse)
        self.Entry.connect("activate", self.buttonResponse,1)
        oAuthorLabel = gtk.Label("Author : ")
        oDescriptionLabel = gtk.Label("Description : ")
        self.Author = gtk.Entry(50)
        self.Desc = gtk.Entry(50)
        self.vbox.pack_start(oAuthorLabel)
        self.vbox.pack_start(self.Author)
        self.vbox.pack_start(oDescriptionLabel)
        self.vbox.pack_end(self.Desc)
        self.sName= None
        self.sAuthor = None
        self.sDesc = None
        self.show_all()

    def getName(self):
        return (self.sName, self.sAuthor, self.sDesc)

    def buttonResponse(self,widget,response):
       if response == 1 or response ==  gtk.RESPONSE_OK:
          self.sName = self.Entry.get_text()
          if len(self.sName)>0:
              self.sAuthor = self.Author.get_text()
              self.sDesc = self.Desc.get_text()
              # We use _ as a deliminator for dragging (see CardSetView)
              # so change any _'s to spaces
              self.sName=self.sName.replace("_"," ")
          else:
              # We don't allow empty names
              self.sName=None

       self.destroy()
