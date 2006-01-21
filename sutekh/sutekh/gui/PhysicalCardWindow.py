import gtk
from AutoScrolledWindow import AutoScrolledWindow

class PhysicalCardWindow(gtk.Window,object):
    def __init__(self,oController):
        super(PhysicalCardWindow,self).__init__()
        self.__oC = oController
        
        self.connect('destroy', lambda wWin: self.__oC.actionQuit())
        
        self.set_title("Sutekh: Card Collection")
        self.set_default_size(300, 400)
   
    def addParts(self,oMenu,oPhysicalCards):
        wMbox = gtk.VBox(False, 2)
                
        wMbox.pack_start(AutoScrolledWindow(oPhysicalCards), expand=True)
        
        self.add(wMbox)
        self.show_all()
