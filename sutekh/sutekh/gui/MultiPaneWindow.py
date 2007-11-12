# MultiPaneWindow.py
# Handle the multi pane UI for Sutkeh
# Copyright 2007, Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - See COPYING for details

import pygtk
pygtk.require('2.0')
import gtk
from sqlobject import SQLObjectNotFound
from sutekh.core.SutekhObjectCache import SutekhObjectCache
from sutekh.core.SutekhObjects import AbstractCard, PhysicalCardSet, \
        AbstractCardSet, PhysicalCard
from sutekh.gui.AbstractCardListFrame import AbstractCardListFrame
from sutekh.gui.PhysicalCardFrame import PhysicalCardFrame
from sutekh.gui.CardTextFrame import CardTextFrame
from sutekh.gui.CardSetFrame import AbstractCardSetFrame, PhysicalCardSetFrame
from sutekh.gui.AboutDialog import SutekhAboutDialog
from sutekh.gui.MainMenu import MainMenu
from sutekh.gui.GuiCardLookup import GuiLookup
from sutekh.gui.CardSetManagementFrame import PhysicalCardSetListFrame, \
        AbstractCardSetListFrame
from sutekh.gui.PluginManager import PluginManager

class MultiPaneWindow(gtk.Window):
    """Window that has a configurable number of panes."""
    def __init__(self, oConfig):
        super(MultiPaneWindow, self).__init__(gtk.WINDOW_TOPLEVEL)
        self._oFocussed = None
        self._oConfig = oConfig
        # Create object cache
        self.__oSutekhObjectCache = SutekhObjectCache()
        self.set_title("Sutekh")
        self.connect("destroy", self.action_quit)
        self.set_border_width(2)
        # We can shrink the window quite small
        self.set_size_request(100, 100)
        # But we start at a reasonable size
        self.set_default_size(700, 500)
        self.oVBox = gtk.VBox(False, 1)
        self._aPanes = []
        self._aFrames = []
        self.__oMenu = MainMenu(self, oConfig)
        self.iPaneNum = 0
        self.oVBox.show()
        self.oVBox.pack_start(self.__oMenu, False, False)
        self.add(self.oVBox)
        self.show_all()
        self._iNumOpenPanes = 0
        self._oPluginManager = PluginManager()
        self._oPluginManager.load_plugins()
        # Need to keep track of open card sets globally
        self.dOpenPanes = {}
        # CardText frame is special, and there is only ever one of it
        self._bCardTextShown = False
        self._oCardTextPane = CardTextFrame(self)
        self._oPCSListPane = None
        self._oACSListPane = None
        for iNumber, sType, sName in self._oConfig.getAllPanes():
            if sType == PhysicalCardSet.sqlmeta.table:
                self.add_physical_card_set(sName)
            elif sType == AbstractCardSet.sqlmeta.table:
                self.add_abstract_card_set(sName)
            elif sType == AbstractCard.sqlmeta.table:
                self.add_abstract_card_list(None)
            elif sType == 'Card Text':
                self.add_card_text(None)
            elif sType == PhysicalCard.sqlmeta.table:
                self.add_physical_card_list(None)
            elif sType == 'Abstract Card Set List':
                self.add_acs_list(None)
            elif sType == 'Physical Card Set List':
                self.add_pcs_list(None)
        self._oCardLookup = GuiLookup()

    # Needed for Backup plugin
    cardLookup = property(fget=lambda self: self._oCardLookup)
    # Needed for plugins
    plugin_manager = property(fget=lambda self: self._oPluginManager)

    def find_pane_by_name(self, sName):
        try:
            iIndex = self.dOpenPanes.values().index(sName)
            oPane = self.dOpenPanes.keys()[iIndex]
            return oPane
        except ValueError:
            return None

    def add_physical_card_set(self, sName):
        sMenuFlag = "PCS:" + sName
        if sMenuFlag not in self.dOpenPanes.values():
            try:
                oPane = PhysicalCardSetFrame(self, sName, self._oConfig)
                self.add_pane(oPane, sMenuFlag)
                self.reload_pcs_list()
            except RuntimeError, e:
                # add warning dialog?
                pass
        else:
            oPane = self.find_pane_by_name(sMenuFlag)
            oPane.reload()

    def add_abstract_card_set(self, sName):
        sMenuFlag = "ACS:" + sName
        if sMenuFlag not in self.dOpenPanes.values():
            try:
               oPane = AbstractCardSetFrame(self, sName, self._oConfig)
               self.add_pane(oPane, sMenuFlag)
               self.reload_acs_list()
            except RuntimeError, e:
                # add warning dialog?
                pass
        else:
            oPane = self.find_pane_by_name(sMenuFlag)
            oPane.reload()

    def add_pcs_list(self, oWidget):
        sMenuFlag = "PCS List"
        if sMenuFlag not in self.dOpenPanes.values():
            oPane = PhysicalCardSetListFrame(self, self._oConfig)
            self.add_pane(oPane, sMenuFlag)
            self._oPCSListPane = oPane
            self.__oMenu.pcs_list_pane_set_sensitive(False)

    def add_acs_list(self, oWidget):
        sMenuFlag = "ACS List"
        if sMenuFlag not in self.dOpenPanes.values():
            oPane = AbstractCardSetListFrame(self, self._oConfig)
            self.add_pane(oPane, sMenuFlag)
            self._oACSListPane = oPane
            self.__oMenu.acs_list_pane_set_sensitive(False)

    def add_abstract_card_list(self, oWidget):
        sMenuFlag = "Abstract Card List"
        if sMenuFlag not in self.dOpenPanes.values():
            oPane = AbstractCardListFrame(self, self._oConfig)
            self.add_pane(oPane, sMenuFlag)
            self.__oMenu.abstract_card_list_set_sensitive(False)

    def add_physical_card_list(self, oWidget):
        sMenuFlag = "Physical Card List"
        if sMenuFlag not in self.dOpenPanes.values():
            oPane = PhysicalCardFrame(self, self._oConfig)
            self.add_pane(oPane, sMenuFlag)
            self.__oMenu.physical_card_list_set_sensitive(False)

    def add_card_text(self, oWidget):
        sMenuFlag = "Card Text"
        if sMenuFlag not in self.dOpenPanes.values():
            self.add_pane(self._oCardTextPane, sMenuFlag)
            self.__oMenu.add_card_text_set_sensitive(False)

    def reload_pcs_list(self):
        if self._oPCSListPane is not None:
            self._oPCSListPane.reload()

    def reload_acs_list(self):
        if self._oACSListPane is not None:
            self._oACSListPane.reload()

    def reload_all(self):
        for oPane in self.dOpenPanes:
            oPane.reload()

    def win_focus(self, oWidget, oEvent, oFrame):
        if self._oFocussed is not None:
            self._oFocussed.set_unfocussed_title()
        self._oFocussed = oFrame
        self._oFocussed.set_focussed_title()

    def run(self):
        gtk.main()

    def action_quit(self, oWidget):
        if self._oConfig.getSaveOnExit():
            self.save_panes()
        gtk.main_quit()

    def save_panes(self):
        self._oConfig.preSaveClear()
        iNum = 1
        for oWidget in self._aFrames:
            self._oConfig.addPane(iNum, oWidget.type, oWidget.name)
            iNum += 1

    def set_card_text(self, sCardName):
        try:
            oCard = AbstractCard.byCanonicalName(sCardName.lower())
            self._oCardTextPane.view.set_card_text(oCard)
        except SQLObjectNotFound:
            pass

    def add_pane(self, oWidget, sMenuFlag):
        oWidget.show_all()
        oWidget.view.connect('focus-in-event', self.win_focus, oWidget)
        self._aFrames.append(oWidget)
        self.dOpenPanes[oWidget] = sMenuFlag
        if self._iNumOpenPanes < 1:
            # We have a blank space to fill, so just plonk in the widget
            self.oVBox.pack_start(oWidget)
        else:
            # We already have a widget, so we add a pane
            oNewPane = gtk.HPaned()
            if len(self._aPanes)>0:
                # We pop out the current pane, and plonk it in the left of a
                # new hpane - we add data to the right HS
                oPart1 = self._aPanes[-1] # Last & thus top pane
            else:
                # This is the first pane, so vbox has 2 children 
                # The menu, and the one we want
                oPart1 = [x for x in self.oVBox.get_children() if x != self.__oMenu][0]
            self.oVBox.remove(oPart1)
            oNewPane.add1(oPart1)
            oNewPane.add2(oWidget)
            oPart1.show()
            oNewPane.show()
            self.oVBox.pack_start(oNewPane)
            self._aPanes.append(oNewPane)
        self._iNumOpenPanes += 1
        self.oVBox.show()
        self.__oMenu.del_pane_set_sensitive(True)

    def menu_remove_pane(self, oMenuWidget):
        self.remove_pane(self._oFocussed)

    def remove_pane_by_name(self, sName):
        oPane = self.find_pane_by_name(sName)
        if oPane is not None:
            self.remove_pane(oPane)

    def remove_pane(self, oFrame):
        if oFrame is not None:
            oRect = oFrame.get_allocation()
            oCur = self.get_allocation()
            self.resize(oCur.width-oRect.width, oCur.height)
            if self._iNumOpenPanes == 1:
                # Removing last widget, so just clear the vbox
                oWidget = [x for x in self.oVBox.get_children() if x != self.__oMenu][0]
                self.oVBox.remove(oWidget)
            elif self._iNumOpenPanes == 2:
                # Removing from the only pane, so keep the unfocussed pane
                oThisPane = self._aPanes[0] # Only pane
                self._aPanes.remove(oThisPane)
                oKept = [x for x in oThisPane.get_children() if x != oFrame][0]
                # clear out pane
                oThisPane.remove(oFrame)
                oThisPane.remove(oKept)
                self.oVBox.remove(oThisPane)
                self.oVBox.pack_start(oKept)
            else:
                oFocussedPane = [x for x in self._aPanes if oFrame in x.get_children()][0]
                if oFocussedPane == self._aPanes[-1]:
                    # Removing last Pane, and thus last Window
                    self.oVBox.remove(oFocussedPane)
                    oFocussedPane.remove(self._aPanes[-2]) # Clear from window
                    self.oVBox.pack_start(self._aPanes[-2])  # safe due to num checks
                    self.oVBox.show()
                else:
                    # Removing First pane, need to check which child to keep
                    oKept = [x for x in oFocussedPane.get_children() if x != oFrame][0]
                    iIndex = self._aPanes.index(oFocussedPane)
                    self._aPanes[iIndex+1].remove(oFocussedPane) # Safe, since this is not the last pane
                    oFocussedPane.remove(oKept)
                    self._aPanes[iIndex+1].add1(oKept)
                # Housekeeping
                oFocussedPane.remove(oFrame)
                self._aPanes.remove(oFocussedPane)

            self.oVBox.show()
            self._iNumOpenPanes -= 1
            if self._iNumOpenPanes == 0:
                self.__oMenu.del_pane_set_sensitive(False)
            self._aFrames.remove(oFrame)
            # Remove from dictionary of open panes
            sMenuFlag = self.dOpenPanes[oFrame]
            del self.dOpenPanes[oFrame]
            if sMenuFlag == "PCS List":
                self.__oMenu.pcs_list_pane_set_sensitive(True)
                self._oPCSListPane = None
            elif sMenuFlag == "ACS List":
                self.__oMenu.acs_list_pane_set_sensitive(True)
                self._oACSListPane = None
            elif sMenuFlag == "Card Text":
                self.__oMenu.add_card_text_set_sensitive(True)
            elif sMenuFlag == "Abstract Card List":
                self.__oMenu.abstract_card_list_set_sensitive(True)
            elif sMenuFlag == "Physical Card List":
                self.__oMenu.physical_card_list_set_sensitive(True)
            # Any cleanup events we need?
            oFrame.cleanup()
            if oFrame == self._oFocussed:
                self._oFocussed = None

    def show_about_dialog(self, oWidget):
        oDlg = SutekhAboutDialog()
        oDlg.run()
        oDlg.destroy()
