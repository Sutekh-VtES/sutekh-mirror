# MultiPaneWindow.py
# Handle the multi pane UI for Sutkeh
# Copyright 2007, Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - See COPYING for details

import pygtk
pygtk.require('2.0')
import gtk, gobject
from sutekh.gui.AbstractCardListFrame import AbstractCardListFrame
from sutekh.gui.PhysicalCardFrame import PhysicalCardFrame
from sutekh.gui.CardTextFrame import CardTextFrame
from sutekh.gui.CardSetFrame import CardSetFrame
from sutekh.gui.AboutDialog import SutekhAboutDialog
from sutekh.core.SutekhObjectCache import SutekhObjectCache

class MultiPaneWindow(gtk.Window):
    """Window that has a configurable number of panes."""
    def __init__(self, oConfig):
        super(MultiPaneWindow,self).__init__(gtk.WINDOW_TOPLEVEL)
        self._oFocussed = None
        self._oConfig = oConfig
        # Create object cache
        self.__oSutekhObjectCache = SutekhObjectCache()
        self.set_title("Sutekh")
        self.connect("destroy", self.action_quit)
        self.set_border_width(5)
        self.set_default_size(450, 400)
        self.set_size_request(-1,-1)
        self.oVBox = gtk.VBox()
        self._aPanes = []
        self.iPaneNum = 0
        self.oVBox.show()
        self.add(self.oVBox)
        self.show()
        self._iNumOpenPanes = 0
        # CardText frame is special, and there is only ever one of it
        self._bCardTextShown = False
        self._oCardTextPane = CardTextFrame(self)
        for iNumber, sType, sName in self._oConfig.getAllPanes():
            if sType == 'Physical Card Set':
                self.add_physical_card_set(sName)
            elif sType == 'Abstract Card Set':
                self.add_abstract_card_set(sName)
            elif sType == 'Abstract Cards':
                self.add_abstract_card_list()
            elif sType == 'Card Text':
                self.add_card_text()
            elif sType == 'Physical Cards':
                self.add_physical_card_list()

    def add_physical_card_set(self,sName):
        pass

    def add_abstract_card_set(self,sName):
        pass

    def add_abstract_card_list(self):
        oWidget = AbstractCardListFrame(self, self._oConfig)
        self.add_pane(oWidget)

    def add_physical_card_list(self):
        oWidget = PhysicalCardFrame(self)
        self.add_pane(oWidget)

    def add_card_text(self):
        if not self._bCardTextShown:
            self.add_pane(self._oCardTextPane)
            self._bCardTextShown = True

    def win_focus(self, oWidget, oEvent, oFrame):
        self._oFocussed = oFrame

    def run(self):
        gtk.main()

    def action_quit(self, oWidget):
        if self._oConfig.getSaveOnExit():
            self.save_panes()
        gtk.main_quit()

    def save_panes(self):
        pass

    def set_card_text(self, oCard):
        self._oCardTextPane.textview.setCardText(oCard)

    def add_pane(self, oWidget):
        oWidget.show_all()
        oWidget.connect('focus-in-event', self.win_focus, oWidget)
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
                # This is the first pane, so vbox has 1 child
                oPart1 = self.oVBox.get_children()[0]
            self.oVBox.remove(oPart1)
            oNewPane.add1(oPart1)
            oNewPane.add2(oWidget)
            oPart1.show()
            oNewPane.show()
            self.oVBox.pack_start(oNewPane)
            self._aPanes.append(oNewPane)
        self._iNumOpenPanes += 1
        self.oVBox.show()
        #self.delMenuItem.set_sensitive(True)
        width, height = self.get_size()
        self._oFocussed = None

    def remove_pane(self, oWidget):
        if self._oFocussed is not None:
            if self._iNumOpenPanes == 1:
                # Removing last widget, so just clear the vbox
                oWidget = self.oVBox.get_children()[0]
                self.oVBox.remove(oWidget)
            elif self._iNumOpenPanes == 2:
                # Removing from the only pane, so keep the unfocussed pane
                oPane = self._aPanes[0] # Only pane
                self._aPanes.remove(oPane)
                oKept = [x for x in oPane.get_children() if x != self._oFocussed][0]
                # clear out pane
                oPane.remove(self._oFocussed)
                oPane.remove(oKept)
                self.oVBox.remove(oPane)
                self.oVBox.pack_start(oKept)
            else:
                oFocussedPane = [x for x in self._aPanes if self._oFocussed in x.get_children()][0]
                if oFocussedPane == self._aPanes[-1]:
                    # Removing last Pane, and thus last Window
                    self.oVBox.remove(oFocussedPane)
                    oFocussedPane.remove(self._aPanes[-2]) # Clear from window
                    self.oVBox.pack_start(self._aPanes[-2])  # safe due to num checks
                    self.oVBox.show()
                else:
                    # Removing First pane, need to check which child to keep
                    oKept = [x for x in oFocussedPane.get_children() if x != self._oFocussed][0]
                    iIndex = self._aPanes.index(oFocussedPane)
                    self._aPanes[iIndex+1].remove(oFocussedPane) # Safe, since this is not the last pane
                    oFocussedPane.remove(oKept)
                    self._aPanes[iIndex+1].add1(oKept)
                # Housekeeping
                oFocussedPane.remove(self._oFocussed)
                self._aPanes.remove(oFocussedPane)

            self.oVBox.show()
            self._iNumOpenPanes -= 1
            #if self._iNumOpenPanes == 0:
            #    self.delMenuItem.set_sensitive(False)
            if self._oFocussed == self._oCardTextPane:
                self._bCardTextShown = False
            self._oFocussed = None
