import gtk

class CreateDeckDialog(gtk.Dialog):
    def __init__(self):
        super(CreateDeckDialog,self).__init__("Choose Deck Name",None,0,( gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.Entry=gtk.Entry(50)
        self.Entry.show()
        self.vbox.pack_start(self.Entry)
        self.connect("response", self.buttonResponse)
        self.Entry.connect("activate", self.buttonResponse,1)
        self.Data = None

    def getName(self):
        return self.Data

    def buttonResponse(self,widget,response):
       if response == 1 or response ==  gtk.RESPONSE_OK:
          self.Data = self.Entry.get_text()
       self.destroy()
