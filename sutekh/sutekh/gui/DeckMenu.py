import gtk

class DeckMenu(gtk.MenuBar,object):
    def __init__(self,oController,oWindow,Name):
        super(DeckMenu,self).__init__()
        self.__oC = oController
        self.__oWindow = oWindow
        self.deckName=Name
        
        self.__createDeckMenu()
        
    def __createDeckMenu(self):
        iMenu = gtk.MenuItem("Deck Actions")
        wMenu=gtk.Menu()
        iMenu.set_submenu(wMenu)

        iClose=gtk.MenuItem("Close Deck ("+self.deckName+")")
        wMenu.add(iClose)
        iClose.connect("activate", self.deckClose)

        iAnalyze = gtk.MenuItem("Analyze Deck")
        iAnalyze.connect("activate", self.deckAnalyze)
        wMenu.add(iAnalyze)

        iAddConstraint = gtk.MenuItem("Add Constraint")
        wMenu.add(iAddConstraint)

        self.removeConstraint= gtk.Action("RemoveCon","Remove Constraint",None,None)
        wMenu.add(self.removeConstraint.create_menu_item())
        self.removeConstraint.set_sensitive(False)

        iSeperator=gtk.SeparatorMenuItem()
        wMenu.add(iSeperator)
        
        iDelete=gtk.MenuItem("Delete Deck ("+self.deckName+")")
        # Possible enhancement, make deck names italic - looks like it requires
        # playing with menuitem attributes (or maybe gtk.Action)
        iDelete.connect("activate", self.deckDelete)
        wMenu.add(iDelete)

        self.add(iMenu)

    def deckClose(self,widget):
        self.__oWindow.closeDeck(widget)

    def deckAnalyze(self,widget):
        self.__oWindow.analyzeDeck()

    def deckDelete(self,widget):
        self.__oWindow.deleteDeck()
