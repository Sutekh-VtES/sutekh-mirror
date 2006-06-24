# DeckWindow.py
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from AutoScrolledWindow import AutoScrolledWindow

class DeckWindow(gtk.Window,object):
    def __init__(self,oController,Name):
        super(DeckWindow,self).__init__()
        self.__oC = oController
        self.deckName = Name
        
        self.connect('destroy', self.closeDeck)
        
        self.set_title("Sutekh: Vampire Deck : " + Name)
        self.set_default_size(400, 400)
   
    def addParts(self,oDeckView,oDeckMenu):
        wMbox = gtk.VBox(False, 2)

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

    def load(self):
        # Select all cards from
        self.__oView.load()
