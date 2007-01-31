# CardSetWindow.py
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from AutoScrolledWindow import AutoScrolledWindow

class CardSetWindow(gtk.Window,object):
    def __init__(self,oController,sName,sType):
        super(CardSetWindow,self).__init__()
        self.__oC = oController
        self.sSetName = sName
        self.sSetType = sType

        self.connect('destroy', self.closeCardSet)

        self.set_title("Sutekh:" + sType + " Card Set : " + sName)
        self.set_default_size(400, 400)

    def updateName(self,sNewName):
        self.sSetName=sNewName
        self.set_title("Sutekh:" + self.sSetType + " Card Set : " + self.sSetName)

    def addParts(self,oCardSetView,oCardSetMenu):
        wMbox = gtk.VBox(False, 2)

        wMbox.pack_start(oCardSetMenu, False, False)
        wMbox.pack_end(AutoScrolledWindow(oCardSetView), expand=True)
        self.__oView = oCardSetView

        self.add(wMbox)
        self.show_all()

    def closeCardSet(self,widget=None):
        self.__oC.removeCardSetWindow(self.sSetName,self.sSetType)
        self.destroy()

    def deleteCardSet(self):
        if self.__oView.deleteCardSet():
           # Card Set was deleted, so close up
           self.closeCardSet()

    def load(self):
        # Select all cards from
        self.__oView.load()
