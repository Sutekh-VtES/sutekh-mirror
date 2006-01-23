import gtk

class CreateDeckDialog(gtk.Dialog):
    def __init__(self,parent):
        super(CreateDeckDialog,self).__init__("Choose Deck Name", \
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
          # We use _ as a deliminator for dragging (see DeckView)
          # so change any _'s to spaces
          self.Data=self.Data.replace("_"," ")
          
       self.destroy()
