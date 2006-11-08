# LoadCardSetDialog.py
# Allow the loading of different card sets
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from SutekhObjects import PhysicalCardSet, AbstractCardSet

class LoadCardSetDialog(gtk.Dialog):
    def __init__(self,parent,sType):
        # I suspect subclassing this to handle the different types
        # would be more "proper", but I'm too lazy to bother
        super(LoadCardSetDialog,self).__init__( \
              "Choose "+sType+" Card Set to Load", \
              parent,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
              ( gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.List=gtk.combo_box_new_text()
        # I like explicitly null entries in the list, but I suspect
        # this violates some or other UI style guide
        self.List.append_text('')
        if sType == "Physical":
            for card in PhysicalCardSet.select().orderBy('name'):
                self.List.append_text(card.name)
        else:
            for card in AbstractCardSet.select().orderBy('name'):
                self.List.append_text(card.name)
        self.vbox.pack_start(self.List)
        self.connect("response", self.buttonResponse)
        self.Data = None
        self.show_all()

    def getName(self):
        if self.Data=='':
            return None
        return self.Data

    def buttonResponse(self,widget,response):
       if response ==  gtk.RESPONSE_OK:
          self.Data = self.List.get_active_text()
       self.destroy()

