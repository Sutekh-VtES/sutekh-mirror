# CardSetFrame.py
# Frame holding a CardSet 
# Copyright 2006,2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.CardSetController import PhysicalCardSetController, \
        AbstractCardSetController

class CardSetFrame(gtk.Frame, object):
    sPCSType = "Physical Card Set"
    sACSType = "Abstract Card Set"

    def __init__(self, oMainWindow, sName, sType, oConfig):
        super(CardSetFrame, self).__init__()
        self._oMainWindow = oMainWindow
        self.sSetType = sType
        self._oConfig = oConfig
        self._oView = None
        if self.sSetType == self.sPCSType:
            self._oC = PhysicalCardSetController(sName, oConfig,
                    oMainWindow, self)
        elif self.sSetType == self.sACSType:
            self._oC = AbstractCardSetController(sName, oConfig,
                    oMainWindow, self)
        else:
            raise RuntimeError("Unknown Card Set type %s" % sType)

        self.updateName(sName)
        self.addParts(self._oC.view)

    view = property(fget=lambda self: self._oView, doc="Associated View Object")
    name = property(fget=lambda self: self._sName, doc="Frame Name")

    def updateName(self, sNewName):
        self.sSetName = sNewName
        self.set_label(self.sSetType + " Card Set : " + self.sSetName)
        self._sName = self.sSetType + " Card Set : " + self.sSetName

    def addParts(self, oCardSetView):
        wMbox = gtk.VBox(False, 2)

        #oToolbar = gtk.VBox(False,2)
        #bInsertToolbar = False
        #for oPlugin in oCardSetView.getController().getPlugins():
        #    oW = oPlugin.getToolbarWidget()
        #    if oW is not None:
        #        oToolbar.pack_start(oW)
        #        bInsertToolbar = True
        #if bInsertToolbar:
        #    wMbox.pack_start(oToolbar, False, False)

        wMbox.pack_end(AutoScrolledWindow(oCardSetView), expand=True)
        self._oView = oCardSetView


        self.add(wMbox)
        self.show_all()

    def closeCardSet(self,widget=None):
        self.__oC.removeCardSetWindow(self.sSetName,self.sSetType)
        self.__oC.reloadCardSetLists()
        self.destroy()

    def deleteCardSet(self):
        if self.__oView.deleteCardSet():
            # Card Set was deleted, so close up
            self.closeCardSet()

    def load(self):
        # Select all cards from
        self.__oView.load()
