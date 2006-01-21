import gtk
from SutekhObjects import PhysicalCardSet

class MainMenu(gtk.MenuBar,object):
    def __init__(self,oController):
        super(MainMenu,self).__init__()
        self.__oC = oController
        
        self.__createFileMenu()
        
    def __createFileMenu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("File")
        wMenu = gtk.Menu()
        iMenu.set_submenu(wMenu)
        
        # items
        iCreate = gtk.MenuItem("Create New Deck")
        wMenu.add(iCreate)

        self.deckLoad=gtk.Action("DeckLoad","Load an Existing Deck",None,None)
        wMenu.add(self.deckLoad.create_menu_item())
        self.deckLoad.set_sensitive(False)

        iSeperator=gtk.SeparatorMenuItem()
        wMenu.add(iSeperator)
        
        iQuit = gtk.MenuItem("Quit")
        iQuit.connect('activate', lambda iItem: self.__oC.actionQuit())
        
        wMenu.add(iQuit)
        
        self.add(iMenu)
        self.setLoadDeckState({}) # Call with an explicitly empty dict

    def setLoadDeckState(self,openDecks):
        # Determine if loadDeck should be greyed out or not
        # loadDeck is greyed if a deck exists that isn't open
        # placeholder at the moment - NM
        state = False
        self.deckLoad.set_sensitive(state)
