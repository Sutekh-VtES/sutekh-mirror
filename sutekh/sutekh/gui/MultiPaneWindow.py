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
from sutekh.gui.BasicFrame import BasicFrame
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
        self.set_default_size(800, 600)
        self.oVBox = gtk.VBox(False, 1)
        self._aHPanes = []
        self.__oMenu = MainMenu(self, oConfig)
        self.oVBox.show()
        self.oVBox.pack_start(self.__oMenu, False, False)
        self.add(self.oVBox)
        # Need this so allocations happen properly in add_pane
        self._iNumberOpenFrames = 0
        self._oPluginManager = PluginManager()
        self._oPluginManager.load_plugins()
        self._iCount = 0
        # Need to keep track of open card sets globally
        self.dOpenFrames = {}
        # CardText frame is special, and there is only ever one of it
        self._bCardTextShown = False
        self._oCardTextPane = CardTextFrame(self)
        self._oPCSListPane = None
        self._oACSListPane = None

        self.show_all()

        self.__dMenus = {
                "Physical Card List" : self.__oMenu.physical_card_list_set_sensitive,
                "White Wolf CardList" : self.__oMenu.abstract_card_list_set_sensitive,
                "Physical Card Set List" : self.__oMenu.pcs_list_pane_set_sensitive,
                "Abstract Card Set List" : self.__oMenu.acs_list_pane_set_sensitive,
                "Card Text" : self.__oMenu.add_card_text_set_sensitive
                }
        self._oCardLookup = GuiLookup(self._oConfig)
        self.restore_from_config()


    # Needed for Backup plugin
    cardLookup = property(fget=lambda self: self._oCardLookup)
    # Needed for plugins
    plugin_manager = property(fget=lambda self: self._oPluginManager)

    def restore_from_config(self):
        for iNumber, sType, sName, bVert, iPos in self._oConfig.getAllPanes():
            if sType == PhysicalCardSet.sqlmeta.table:
                oF = self.add_pane(bVert)
                self.replace_with_physical_card_set(sName, oF)
            elif sType == AbstractCardSet.sqlmeta.table:
                oF = self.add_pane(bVert)
                self.replace_with_abstract_card_set(sName, oF)
            elif sType == AbstractCard.sqlmeta.table:
                self._oFocussed = self.add_pane(bVert)
                self.replace_with_abstract_card_list(None)
            elif sType == 'Card Text':
                self._oFocussed = self.add_pane(bVert)
                self.replace_with_card_text(None)
            elif sType == PhysicalCard.sqlmeta.table:
                self._oFocussed = self.add_pane(bVert)
                self.replace_with_physical_card_list(None)
            elif sType == 'Abstract Card Set List':
                self._oFocussed = self.add_pane(bVert)
                self.replace_with_acs_list(None)
            elif sType == 'Physical Card Set List':
                self._oFocussed = self.add_pane(bVert)
                self.replace_with_pcs_list(None)
            elif sType == 'Blank Frame':
                self.add_pane(bVert)
        if self._iNumberOpenFrames == 0:
            # We always have at least one pane
            self.add_pane()

    def find_pane_by_name(self, sName):
        try:
            iIndex = self.dOpenFrames.values().index(sName)
            oPane = self.dOpenFrames.keys()[iIndex]
            return oPane
        except ValueError:
            return None

    def replace_with_physical_card_set(self, sName, oFrame):
        sMenuFlag = "PCS:" + sName
        if sMenuFlag not in self.dOpenFrames.values() and oFrame:
            try:
                oPane = PhysicalCardSetFrame(self, sName, self._oConfig)
                self.replace_frame(oFrame, oPane, sMenuFlag)
            except RuntimeError, e:
                # add warning dialog?
                pass
        else:
            oPane = self.find_pane_by_name(sMenuFlag)
            if oPane:
                oPane.reload()

    def replace_with_abstract_card_set(self, sName, oFrame):
        sMenuFlag = "ACS:" + sName
        if sMenuFlag not in self.dOpenFrames.values() and oFrame:
            try:
                oPane = AbstractCardSetFrame(self, sName, self._oConfig)
                self.replace_frame(oFrame, oPane, sMenuFlag)
            except RuntimeError, e:
                # add warning dialog?
                pass
        else:
            oPane = self.find_pane_by_name(sMenuFlag)
            if oPane:
                oPane.reload()

    def replace_with_pcs_list(self, oWidget):
        sMenuFlag = "Physical Card Set List"
        if sMenuFlag not in self.dOpenFrames.values() and self._oFocussed:
            oPane = PhysicalCardSetListFrame(self, self._oConfig)
            self.replace_frame(self._oFocussed, oPane, sMenuFlag)
            self._oPCSListPane = oPane

    def replace_with_acs_list(self, oWidget):
        sMenuFlag = "Abstract Card Set List"
        if sMenuFlag not in self.dOpenFrames.values() and self._oFocussed:
            oPane = AbstractCardSetListFrame(self, self._oConfig)
            self.replace_frame(self._oFocussed, oPane, sMenuFlag)
            self._oACSListPane = oPane

    def replace_with_abstract_card_list(self, oWidget):
        sMenuFlag = "White Wolf CardList"
        if sMenuFlag not in self.dOpenFrames.values() and self._oFocussed:
            oPane = AbstractCardListFrame(self, self._oConfig)
            self.replace_frame(self._oFocussed, oPane, sMenuFlag)

    def replace_with_physical_card_list(self, oWidget):
        sMenuFlag = "Physical Card List"
        if sMenuFlag not in self.dOpenFrames.values() and self._oFocussed:
            oPane = PhysicalCardFrame(self, self._oConfig)
            self.replace_frame(self._oFocussed, oPane, sMenuFlag)

    def replace_with_card_text(self, oWidget):
        sMenuFlag = "Card Text"
        if sMenuFlag not in self.dOpenFrames.values() and self._oFocussed:
            self.replace_frame(self._oFocussed, self._oCardTextPane, sMenuFlag)

    def reload_pcs_list(self):
        if self._oPCSListPane is not None:
            self._oPCSListPane.reload()

    def reload_acs_list(self):
        if self._oACSListPane is not None:
            self._oACSListPane.reload()

    def reload_all(self):
        for oPane in self.dOpenFrames:
            oPane.reload()

    def win_focus(self, oWidget, oEvent, oFrame):
        if self._oFocussed is not None:
            self._oFocussed.set_unfocussed_title()
        self._oFocussed = oFrame
        self._oFocussed.set_focussed_title()
        self.reset_menu()
 
    def run(self):
        gtk.main()

    def action_quit(self, oWidget):
        if self._oConfig.getSaveOnExit():
            self.save_frames()
        gtk.main_quit()

    def save_frames(self):
        self._oConfig.preSaveClear()

        def save_children(oPane, oConfig, bVert, iNum):
            if type(oPane) is gtk.HPaned or type(oPane) is gtk.VPaned:
                oChild1 = oPane.get_child1()
                oChild2 = oPane.get_child2()
                iNum = save_children(oChild1, oConfig, False, iNum)
                if type(oPane) is gtk.HPaned:
                    iNum = save_children(oChild2, oConfig, False, iNum)
                else:
                    iNum = save_children(oChild2, oConfig, True, iNum)
            else:
                oConfig.add_frame(iNum, oPane.type, oPane.name, bVert, -1)
                iNum += 1
            return iNum

        aTopLevelPane = [x for x in self.oVBox.get_children() if x != self.__oMenu]
        for oPane in aTopLevelPane:
            save_children(oPane, self._oConfig, False, 1)



    def set_card_text(self, sCardName):
        try:
            oCard = AbstractCard.byCanonicalName(sCardName.lower())
            self._oCardTextPane.view.set_card_text(oCard)
        except SQLObjectNotFound:
            pass

    def replace_frame(self, oOldFrame, oNewFrame, sMenuFlag):
        oNewFrame.show_all()
        oNewFrame.view.connect('focus-in-event', self.win_focus, oNewFrame)
        oParent = oOldFrame.get_parent()
        oParent.remove(oOldFrame)
        oParent.add(oNewFrame)
        del self.dOpenFrames[oOldFrame]
        self.dOpenFrames[oNewFrame] = sMenuFlag
        if self._oFocussed == oOldFrame:
            self._oFocussed = None
        self.reset_menu()
        # Open card lists may have changed because of the frame we've kicked out
        self.reload_pcs_list()
        self.reload_acs_list()

    def swap_frames(self, oFrame1, oFrame2):
        if oFrame1 != oFrame2:
            oParent1 = oFrame1.get_parent()
            oParent2 = oFrame2.get_parent()
            if oParent1 == oParent2:
                # Special logic to ensure that we get them swapped
                if oFrame1 == oParent1.get_child1():
                    oParent1.remove(oFrame1)
                    oParent1.remove(oFrame2)
                    oParent1.add1(oFrame2)
                    oParent1.add2(oFrame1)
                else:
                    oParent1.remove(oFrame1)
                    oParent1.remove(oFrame2)
                    oParent1.add1(oFrame1)
                    oParent1.add2(oFrame2)
            else:
                oParent2.remove(oFrame2)
                oParent1.remove(oFrame1)
                oParent2.add(oFrame1)
                oParent1.add(oFrame2)
            oParent1.show_all()
            oParent2.show_all()
            self.reset_menu()

    def get_current_pane(self):
        if self._oFocussed:
            oParent = self._oFocussed.get_parent()
            if type(oParent) is gtk.VPaned:
                # Get the HPane this belongs to
                oParent = oParent.get_parent()
            return oParent
        else:
            # Return the last added pane
            return self._aHPanes[-1]

    def add_pane(self, bVertical=False):
        oWidget = BasicFrame(self)
        oWidget.add_parts()
        oWidget.view.connect('focus-in-event', self.win_focus, oWidget)
        self._iCount += 1
        sKey = 'Blank Pane:' + str(self._iCount)
        oWidget.set_title(sKey)
        self.dOpenFrames[oWidget] = sKey
        if self._iNumberOpenFrames < 1:
            # We have a blank space to fill, so just plonk in the widget
            self.oVBox.pack_start(oWidget)
        else:
            # We already have a widget, so we add a pane
            if bVertical:
                oNewPane = gtk.VPaned()
                oCurAlloc = self.oVBox.get_allocation()
                oMenuAlloc = self.__oMenu.get_allocation()
                iPos = (oCurAlloc.height - oMenuAlloc.height) / 2
            else:
                oNewPane = gtk.HPaned()
            if len(self._aHPanes) > 0:
                # We pop out the current frame, and plonk it in 
                # the new pane - we add the new widget to the other 
                # part
                oParent = self.get_current_pane()
                # Must be a hpane, by construction
                if self._oFocussed:
                    oPart1 = self._oFocussed
                    if type(oPart1.get_parent()) is gtk.VPaned:
                        # Veritical pane, so we need to use the pane, not the Frame
                        oPart1 = oPart1.get_parent()
                else:
                    # Replace right child of last added pane when no obvious option
                    oPart1 = oParent.get_child2()
                if oPart1 == oParent.get_child1():
                    oParent.remove(oPart1)
                    oParent.add1(oNewPane)
                    # Going to the left of the current pane,
                    if not bVertical:
                        iPos = oParent.get_position()/2
                else:
                    oParent.remove(oPart1)
                    oParent.add2(oNewPane)
                    oCur = oParent.get_allocation()
                    if not bVertical:
                        if oCur.width == 1 and oParent.get_position() > 1:
                            # we are in early startup, so we can move the
                            # Parent as well
                            # We want to split ourselves into equally sized
                            # sections
                            oCur = self.oVBox.get_allocation()
                            iPos = oCur.width / (len(self._aHPanes) + 2)
                            self.set_pos_for_all_hpanes(iPos)
                        else:
                            iPos = (oCur.width - oParent.get_position())/2
            else:
                # This is the first HPane, or the 1st VPane we add, so 
                # vbox has 2 children 
                # The menu, and the one we want
                oPart1 = [x for x in self.oVBox.get_children() if x != self.__oMenu][0]
                oParent = self.oVBox
                # Just split the window
                oCur = oParent.get_allocation()
                if not bVertical:
                    iPos = oCur.width/2
                oParent.remove(oPart1)
                oParent.pack_start(oNewPane)
            oNewPane.add1(oPart1)
            oNewPane.add2(oWidget)
            oPart1.show()
            oNewPane.show()
            oParent.show()
            if not bVertical:
                self._aHPanes.append(oNewPane)
            oNewPane.set_position(iPos)
        self._iNumberOpenFrames += 1
        self.oVBox.show_all()
        self.reset_menu()
        return oWidget

    def menu_remove_frame(self, oMenuWidget):
        self.remove_frame(self._oFocussed)

    def remove_frame_by_name(self, sName):
        oPane = self.find_pane_by_name(sName)
        if oPane is not None:
            self.remove_frame(oPane)

    def remove_frame(self, oFrame):
        if oFrame is not None:
            if self._iNumberOpenFrames == 1:
                # Removing last widget, so just clear the vbox
                oWidget = [x for x in self.oVBox.get_children() if x != self.__oMenu][0]
                self.oVBox.remove(oWidget)
            elif type(oFrame.get_parent()) is gtk.VPaned:
                # Removing a vertical frame, keep the correct child
                oParent = oFrame.get_parent()
                oKept = [x for x in oParent.get_children() if x != oFrame][0]
                oHPane = oParent.get_parent()
                oHPane.remove(oParent)
                oParent.remove(oFrame)
                oParent.remove(oKept)
                oHPane.add(oKept)
            elif len(self._aHPanes) == 1:
                # Removing from the only pane, so keep the unfocussed pane
                oThisPane = self._aHPanes[0] # Only pane
                self._aHPanes.remove(oThisPane)
                oKept = [x for x in oThisPane.get_children() if x != oFrame][0]
                # clear out pane
                oThisPane.remove(oFrame)
                oThisPane.remove(oKept)
                self.oVBox.remove(oThisPane)
                self.oVBox.pack_start(oKept)
            else:
                oFocussedPane = [x for x in self._aHPanes if oFrame in x.get_children()][0]
                oKept = [x for x in oFocussedPane.get_children() if x != oFrame][0]
                oParent = oFocussedPane.get_parent()
                oParent.remove(oFocussedPane)
                oFocussedPane.remove(oKept)
                oParent.add(oKept)
                # Housekeeping
                oFocussedPane.remove(oFrame)
                self._aHPanes.remove(oFocussedPane)
            self.oVBox.show()
            self._iNumberOpenFrames -= 1
            # Remove from dictionary of open panes
            sMenuFlag = self.dOpenFrames[oFrame]
            del self.dOpenFrames[oFrame]
            # Any cleanup events we need?
            oFrame.cleanup()
            if oFrame == self._oFocussed:
                self._oFocussed = None
            if self._iNumberOpenFrames == 0:
                # Always have one to replace
                self.add_pane()
            self.reset_menu()

    def reset_menu(self):
        for sMenu, fSetSensitiveFunc in self.__dMenus.iteritems():
            if sMenu in self.dOpenFrames.values():
                fSetSensitiveFunc(False)
            else:
                fSetSensitiveFunc(True)
        if self._oFocussed:
            self.__oMenu.del_pane_set_sensitive(True)
            # Can always split horizontally
            self.__oMenu.set_split_horizontal_active(True)
            # But we can't split vertically more than once
            if type(self._oFocussed.get_parent()) is gtk.VPaned:
                self.__oMenu.set_split_vertical_active(False)
            else:
                self.__oMenu.set_split_vertical_active(True)
        else:
            # Can't split when no pane chosen
            self.__oMenu.set_split_vertical_active(False)
            self.__oMenu.set_split_horizontal_active(False)
            # Can't delete either
            self.__oMenu.del_pane_set_sensitive(False)

    def show_about_dialog(self, oWidget):
        oDlg = SutekhAboutDialog()
        oDlg.run()
        oDlg.destroy()

    def set_all_panes_equal(self):
        oCurAlloc = self.oVBox.get_allocation()
        iNewPos = oCurAlloc.width / (len(self._aHPanes) + 1)
        self.set_pos_for_all_hpanes(iNewPos)
    
    def set_pos_for_all_hpanes(self, iNewPos):
        """Set all the panes to the same Position value"""
        oCurAlloc = self.oVBox.get_allocation()
        oMenuAlloc = self.__oMenu.get_allocation()
        iVertPos = (oCurAlloc.height - oMenuAlloc.height) / 2
        def set_pos_children(oPane, iPos, iVertPos):
            oChild1 = oPane.get_child1()
            oChild2 = oPane.get_child2()
            if type(oChild1) is gtk.HPaned:
                iMyPos = iPos + set_pos_children(oChild1, iPos, iVertPos)
            else:
                if type(oChild1) is gtk.VPaned:
                    oChild1.set_position(iVertPos)
                iMyPos = iPos
            oPane.set_position(iMyPos)
            if type(oChild2) is gtk.HPaned:
                iMyPos += set_pos_children(oChild2, iPos, iVertPos)
            elif type(oChild2) is gtk.VPaned:
                oChild2.set_position(iVertPos)
            return iMyPos

        aTopLevelPane = [x for x in self.oVBox.get_children() if x != self.__oMenu]
        for oPane in aTopLevelPane:
            # Should only be 1 here
            if type(oPane) is gtk.HPaned:
                set_pos_children(oPane, iNewPos, iVertPos)
            elif type(oPane) is gtk.VPaned:
                # Do something sensible for single VPane case
                oPane.set_position(iVertPos)
