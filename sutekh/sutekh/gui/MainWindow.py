import gtk
from AutoScrolledWindow import AutoScrolledWindow

class MainWindow(gtk.Window,object):
    def __init__(self,oController):
        super(MainWindow,self).__init__()
        self.__oC = oController
        
        self.connect('destroy', lambda wWin: self.__oC.actionQuit())
        
        self.set_title("Sutekh")
        self.set_default_size(600, 400)
   
    def addParts(self,oMenu,oCardText,oAbstractCards,oPhysicalCards):
        wMbox = gtk.VBox(False, 2)
        wHbox = gtk.HBox(False, 2)
        wVbox = gtk.VBox(False, 2)
        
        wMbox.pack_start(oMenu, False, False)
        wMbox.pack_start(wHbox, expand=True)
        
        wHbox.pack_start(AutoScrolledWindow(oAbstractCards), False, False)
        wHbox.pack_start(wVbox)
                
        wVbox.pack_start(AutoScrolledWindow(oPhysicalCards), expand=True)
        wVbox.pack_start(AutoScrolledWindow(oCardText), False, False)
        
        self.add(wMbox)
        self.show_all()
