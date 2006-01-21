import gtk
from SutekhObjects import PhysicalCardSet
        
class LoadDeckDialog(gtk.Dialog):
    def __init__(self):
        super(LoadDeckDialog,self).__init__("Choose Deck to Load",None,0,( gtk.STOCK_OK, gtk.RESPONSE_OK, gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL))
        self.List=gtk.combo_box_new_text()
        # I like explicitly null entries in the list, but I suspect
        # this violates some or other UI style guide
        self.List.append_text('')
        for card in PhysicalCardSet.select():
           self.List.append_text(card.name)
        self.List.show()
        self.vbox.pack_start(self.List)
        self.connect("response", self.buttonResponse)
        self.Data = None

    def getName(self):
        if self.Data=='':
            return None
        return self.Data

    def buttonResponse(self,widget,response):
       if response ==  gtk.RESPONSE_OK:
          self.Data = self.List.get_active_text()
       self.destroy()

