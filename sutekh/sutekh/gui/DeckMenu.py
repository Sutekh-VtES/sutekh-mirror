import gtk

class DeckMenu(gtk.MenuBar,object):
    def __init__(self,oController,Name):
        super(DeckMenu,self).__init__()
        self.__oC = oController
        self.deckName=Name
        
        self.__createDeckMenu()
        
    def __createDeckMenu(self):
        iMenu = gtk.MenuItem("Deck Actions")
        wMenu=gtk.Menu()
        iMenu.set_submenu(wMenu)

        iClose=gtk.MenuItem("Close Deck View")
        wMenu.add(iClose)

        iAnalyze = gtk.MenuItem("Analyze Deck")
        wMenu.add(iAnalyze)

        iAddConstraint = gtk.MenuItem("Add Constraint")
        wMenu.add(iAddConstraint)

        self.removeConstraint= gtk.Action("RemoveCon","Remove Constraint",None,None)
        wMenu.add(self.removeConstraint.create_menu_item())
        self.removeConstraint.set_sensitive(False)

        iSeperator=gtk.SeparatorMenuItem()
        wMenu.add(iSeperator)
        
        iDelete=gtk.Action("DeckDelete","Delete Current Deck",None,None)
        wMenu.add(iDelete)

        self.add(iMenu)
