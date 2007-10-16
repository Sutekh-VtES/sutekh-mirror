# CardSetFrame.py
# Frame holding a CardSet 
# Copyright 2006,2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet, AbstractCardSet
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.CardSetController import PhysicalCardSetController, \
        AbstractCardSetController
from sutekh.gui.SQLObjectEvents import CardSetOpenedSignal, CardSetClosedSignal

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
            self.oSignalClass = PhysicalCardSet
            self._dOpenCardSets = oMainWindow.dOpenPCS
        elif self.sSetType == self.sACSType:
            self._oC = AbstractCardSetController(sName, oConfig,
                    oMainWindow, self)
            self.oSignalClass = AbstractCardSet
            self._dOpenCardSets = oMainWindow.dOpenACS
        else:
            raise RuntimeError("Unknown Card Set type %s" % sType)

        self.updateName(sName)

        if self.sSetName not in self._dOpenCardSets:
            self._dOpenCardSets[self.sSetName] = 1
        else:
            self._dOpenCardSets[self.sSetName] += 1

        self._aPlugins = []
        for cPlugin in self._oMainWindow.plugin_manager.getCardListPlugins():
            self._aPlugins.append(cPlugin(self._oC.view,
                self._oC.view.getModel(),self.sSetType))

        self.oSignalClass.sqlmeta.send(CardSetOpenedSignal, self.sSetName)
        self.addParts(self._oC.view)

    view = property(fget=lambda self: self._oView, doc="Associated View Object")
    name = property(fget=lambda self: self.sSetName, doc="Frame Name")
    type = property(fget=lambda self: self.sSetType, doc="Frame Type")

    def cleanup(self):
        """Cleanup function called before pane is removed by the
           Main Window"""
        if self._dOpenCardSets[self.sSetName] == 1:
            del self._dOpenCardSets[self.sSetName]
        else:
            self._dOpenCardSets[self.sSetName] -= 1
        self.oSignalClass.sqlmeta.send(CardSetClosedSignal, self.sSetName)

    def updateName(self, sNewName):
        self.sSetName = sNewName
        self.set_label(self.sSetType + ": " + self.sSetName)

    def addParts(self, oCardSetView):
        wMbox = gtk.VBox(False, 2)

        oToolbar = gtk.VBox(False,2)
        bInsertToolbar = False
        for oPlugin in self._aPlugins:
            oW = oPlugin.getToolbarWidget()
            if oW is not None:
                oToolbar.pack_start(oW)
                bInsertToolbar = True
        if bInsertToolbar:
            wMbox.pack_start(oToolbar, False, False)

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
