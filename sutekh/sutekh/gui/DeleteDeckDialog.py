import gtk

class DeleteDeckDialog(gtk.Dialog):
    def __init__(self,parent,name):
        super(DeleteDeckDialog,self).__init__("Really Delete?", \
              parent,gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, \
              ( gtk.STOCK_YES, gtk.RESPONSE_OK, gtk.STOCK_NO, gtk.RESPONSE_CANCEL))
        Label=gtk.Label("Deck " + name + " Not Empty - Really Delete?")
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

