# DeleteCardDialog.py
# Confirm card deletion dialog
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk

class DeleteCardDialog(gtk.Dialog):
    def __init__(self,parent,decklist):
        # In retrospect, A MesgDialog would also work
        super(DeleteCardDialog,self).__init__("Really Delete?", \
              parent,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
              ( gtk.STOCK_YES, gtk.RESPONSE_OK, gtk.STOCK_NO, gtk.RESPONSE_CANCEL))
        Label=gtk.Label()
        text="Card Present in the following decks:\n"
        for deck in decklist:
            text=text+"<span foreground=\"blue\">"+deck+"</span>\n"
        text=text+"<b>Really Delete?</b>"
        Label.set_markup(text)
        Icon=gtk.Image()
        Icon.set_from_stock(gtk.STOCK_DIALOG_QUESTION,gtk.ICON_SIZE_DIALOG)
        HBox=gtk.HBox(False,0)
        HBox.pack_start(Icon,False,False)
        HBox.pack_end(Label,True,False)
        self.vbox.pack_start(HBox)
        self.connect("response", self.buttonResponse)
        self.Data = False
        self.show_all()

    def getResult(self):
        return self.Data

    def buttonResponse(self,widget,response):
       if response ==  gtk.RESPONSE_OK:
          self.Data = True
       self.destroy()
