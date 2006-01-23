import gtk
from AutoScrolledWindow import AutoScrolledWindow
from DeckMenu import DeckMenu
from AnalyzeDialog import AnalyzeDialog

class DeckWindow(gtk.Window,object):
    def __init__(self,oController,Name):
        super(DeckWindow,self).__init__()
        self.__oC = oController
        self.deckName = Name
        
        self.connect('destroy', self.closeDeck)
        
        self.set_title("Sutekh: Vampire Deck : "+Name)
        self.set_default_size(300, 400)
   
    def addParts(self,oDeckView):
        wMbox = gtk.VBox(False, 2)

        oDeckMenu = DeckMenu(self.__oC,self,self.deckName)

        wMbox.pack_start(oDeckMenu, False, False)
        wMbox.pack_end(AutoScrolledWindow(oDeckView), expand=True)
        self.__oView = oDeckView
        
        self.add(wMbox)
        self.show_all()
        
    def closeDeck(self,widget=None):
        self.__oC.removeDeckWindow(self.deckName)
        self.destroy()

    def deleteDeck(self):
        if self.__oView.deleteDeck():
           # Deck was deleted, so close up
           self.closeDeck()

    def analyzeDeck(self):
        Dialog=AnalyzeDialog(self,self.deckName)
        Dialog.run()

    def load(self):
        # Select all cards from
        self.__oView.load()
