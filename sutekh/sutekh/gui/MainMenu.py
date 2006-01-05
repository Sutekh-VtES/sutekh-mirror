import gtk

class MainMenu(gtk.MenuBar,object):
    def __init__(self,oController):
        super(MainMenu,self).__init__()
        self.__oC = oController
        
        self.__createFileMenu()
        self.__createDeckMenu()
        
    def __createFileMenu(self):
        # setup sub menu
        iMenu = gtk.MenuItem("File")
        wMenu = gtk.Menu()
        iMenu.set_submenu(wMenu)
        
        # items
        iQuit = gtk.MenuItem("Quit")
        iQuit.connect('activate', lambda iItem: self.__oC.actionQuit())
        
        wMenu.add(iQuit)
        
        self.add(iMenu)

    def __createDeckMenu(self):
        iMenu = gtk.MenuItem("Deck")
        wMenu=gtk.Menu()
        iMenu.set_submenu(wMenu)

        iCreate=gtk.MenuItem("Create New Deck")
        wMenu.add(iCreate)

        iLoad=gtk.MenuItem("Load an Existing Deck")
        wMenu.add(iLoad)

        iDelete=gtk.MenuItem("Delete Current Deck")
        wMenu.add(iDelete)

        iClose=gtk.MenuItem("Close Deck View")
        wMenu.add(iClose)

        iAnalyze = gtk.MenuItem("Analyze Deck")
        wMenu.add(iAnalyze)

        self.add(iMenu)
