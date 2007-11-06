# CardSetFrame.py
# Frame holding a CardSet 
# Copyright 2006,2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet, AbstractCardSet
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.gui.CardSetMenu import CardSetMenu
from sutekh.gui.CardSetController import PhysicalCardSetController, \
        AbstractCardSetController

class CardSetFrame(gtk.Frame, object):
    def __init__(self, oMainWindow, sName, cType, oConfig):
        super(CardSetFrame, self).__init__()
        self._oMainWindow = oMainWindow
        self.cSetType = cType
        self._oConfig = oConfig
        if self.cSetType is PhysicalCardSet:
            self._oC = PhysicalCardSetController(sName, oConfig,
                    oMainWindow, self)
        elif self.cSetType is AbstractCardSet:
            self._oC = AbstractCardSetController(sName, oConfig,
                    oMainWindow, self)
        else:
            raise RuntimeError("Unknown Card Set type %s" % str(cType))

        self._aPlugins = []
        for cPlugin in self._oMainWindow.plugin_manager.getCardListPlugins():
            self._aPlugins.append(cPlugin(self._oC.view,
                self._oC.view.getModel(), self.cSetType))

        self._oMenu = CardSetMenu(self, self._oC, self._oMainWindow, self._oC.view,
                sName, self.cSetType)
        self.add_parts()
        self.updateName(sName)

        self.__oBaseStyle = self.__oTitle.get_style().copy()
        self.__oFocStyle = self.__oTitle.get_style().copy()
        oMap = self.__oTitle.get_colormap()
        oGreen = oMap.alloc_color("purple")
        self.__oFocStyle.fg[gtk.STATE_NORMAL] = oGreen

    view = property(fget=lambda self: self._oC.view, doc="Associated View Object")
    name = property(fget=lambda self: self.sSetName, doc="Frame Name")
    type = property(fget=lambda self: self.cSetType.sqlmeta.table, doc="Frame Type")
    menu = property(fget=lambda self: self._oMenu, doc="Frame Menu")

    def cleanup(self):
        """Cleanup function called before pane is removed by the
           Main Window"""
        if self.cSetType is PhysicalCardSet:
            self._oMainWindow.reload_pcs_list()
        else:
            self._oMainWindow.reload_acs_list()

    def updateName(self, sNewName):
        self.sSetName = sNewName
        if self.cSetType is PhysicalCardSet:
            self.__oTitle.set_text('PCS:' + self.sSetName)
        else:
            self.__oTitle.set_text('ACS:' + self.sSetName)

    def add_parts(self):
        wMbox = gtk.VBox(False, 2)

        self.__oTitle = gtk.Label()
        wMbox.pack_start(self.__oTitle, False, False)

        wMbox.pack_start(self._oMenu, False, False)

        oToolbar = gtk.VBox(False,2)
        bInsertToolbar = False
        for oPlugin in self._aPlugins:
            oW = oPlugin.getToolbarWidget()
            if oW is not None:
                oToolbar.pack_start(oW, False, False)
                bInsertToolbar = True
        if bInsertToolbar:
            wMbox.pack_start(oToolbar, False, False)

        wMbox.pack_end(AutoScrolledWindow(self._oC.view), expand=True)

        self.add(wMbox)
        self.show_all()

    def set_focussed_title(self):
        self.__oTitle.set_style(self.__oFocStyle)

    def set_unfocussed_title(self):
        self.__oTitle.set_style(self.__oBaseStyle)

    def closeCardSet(self, widget=None):
        # FIXME: Update to frame based stuff
        self._oMainWindow.remove_pane(self)
        if self.cSetType is PhysicalCardSet:
            self._oMainWindow.reload_pcs_list()
        else:
            self._oMainWindow.reload_acs_list()
        self.destroy()

    def deleteCardSet(self):
        if self._oC.view.deleteCardSet():
            # Card Set was deleted, so close up
            self.closeCardSet()

class AbstractCardSetFrame(CardSetFrame):
    def __init__(self, oMainWindow, sName, oConfig):
        super(AbstractCardSetFrame, self).__init__(oMainWindow, sName, 
                AbstractCardSet, oConfig)

class PhysicalCardSetFrame(CardSetFrame):
    def __init__(self, oMainWindow, sName, oConfig):
        super(PhysicalCardSetFrame, self).__init__(oMainWindow, sName, 
                PhysicalCardSet, oConfig)
