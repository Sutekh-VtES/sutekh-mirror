import gtk

class DeleteCardDialog(gtk.Dialog):
    def __init__(self,decklist):
        # In retrosepc, A MesgDialog should be used here
        super(DeleteCardPopup,self).__init__("Really Delete?",None,0,( gtk.STOCK_YES, gtk.RESPONSE_OK, gtk.STOCK_NO, gtk.RESPONSE_CANCEL))
        Label=gtk.Label()
        text="Card Present in the following decks:\n"
        for deck in decklist:
            text=text+"<span foreground=\"blue\">"+deck+"</span>\n"
        text=text+"<b>Really Delete?</b>"
        Label.set_markup(text)
        Label.show()
        Icon=gtk.Image()
        Icon.set_from_stock(gtk.STOCK_DIALOG_QUESTION,gtk.ICON_SIZE_DIALOG)
        Icon.show()
        HBox=gtk.HBox(False,0)
        HBox.pack_start(Icon,False,False)
        HBox.pack_end(Label,True,False)
        HBox.show()
        self.vbox.pack_start(HBox)
        self.connect("response", self.buttonResponse)
        self.Data = False

    def getResult(self):
        return self.Data

    def buttonResponse(self,widget,response):
       if response ==  gtk.RESPONSE_OK:
          self.Data = True
       self.destroy()
