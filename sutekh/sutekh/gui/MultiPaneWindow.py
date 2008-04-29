# MultiPaneWindow.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Handle the multi pane UI for Sutkeh
# Copyright 2007, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - See COPYING for details

"""Main window for Sutekh."""

import pygtk
pygtk.require('2.0')
import gtk
# pylint: disable-msg=E0611
# pylint doesn't see resource_stream here, for some reason
from pkg_resources import resource_stream
# pylint: enable-msg=E0611
from sqlobject import SQLObjectNotFound
from sutekh.core.SutekhObjectCache import SutekhObjectCache
from sutekh.core.SutekhObjects import AbstractCard, PhysicalCardSet, \
        PhysicalCard
from sutekh.gui.BasicFrame import BasicFrame
from sutekh.gui.PhysicalCardFrame import PhysicalCardFrame
from sutekh.gui.CardTextFrame import CardTextFrame
from sutekh.gui.CardSetFrame import PhysicalCardSetFrame
from sutekh.gui.AboutDialog import SutekhAboutDialog
from sutekh.gui.MainMenu import MainMenu
from sutekh.gui.GuiCardLookup import GuiLookup
from sutekh.gui.CardSetManagementFrame import PhysicalCardSetListFrame
from sutekh.gui.PluginManager import PluginManager
from sutekh.gui import SutekhIcon
from sutekh.gui.HTMLTextView import HTMLViewDialog
from sutekh.gui.IconManager import IconManager

class MultiPaneWindow(gtk.Window):
    """Window that has a configurable number of panes."""
    # pylint: disable-msg=R0904, R0902
    # R0904 - gtk.Widget, so many public methods
    # R0902 - we need to keep a lot of state, so many instance attributes
    def __init__(self):
        super(MultiPaneWindow, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.set_name("Sutekh")
        self.set_title("Sutekh")
        self.set_border_width(2)

        # make sure we can quit
        self.connect("destroy", self.action_quit)
        # We can shrink the window quite small
        self.set_size_request(100, 100)
        # But we start at a reasonable size
        self.set_default_size(800, 600)

        # Set Default Window Icon for all Windows
        gtk.window_set_default_icon(SutekhIcon.SUTEKH_ICON)

        # common current directory for file dialogs
        self._sWorkingDir = ''

        # Need this so allocations happen properly in add_pane
        self._iNumberOpenFrames = 0
        self._iCount = 0

        # Need to keep track of open card sets globally
        self.dOpenFrames = {}

        self._sCardSelection = '' # copy + paste selection
        self._aHPanes = []
        self._aPlugins = []
        self.__dMenus = {}

        self._oFocussed = None

        # CardText frame is special, and there is only ever one of it
        # but we will set it up later
        self._bCardTextShown = False
        self._oCardTextPane = None
        self._oPCSListPane = None
        self._oACSListPane = None
        self._oHelpDlg = None
        # Global icon manager
        self._oIconManager = None

    # pylint: disable-msg=W0201
    # We define attributes here, since this is called after database checks
    def setup(self, oConfig, bVerbose=False):
        """After database checks are passed, setup what we need to display
           data from the database."""
        self._oConfig = oConfig
        self._oCardLookup = GuiLookup(self._oConfig)

        # Create object cache
        self.__oSutekhObjectCache = SutekhObjectCache()

        # Create global icon manager
        self._oIconManager = IconManager(oConfig)
        # Create card text pane
        self._oCardTextPane = CardTextFrame(self, self._oIconManager)

        # Load plugins
        self._oPluginManager = PluginManager()
        self._oPluginManager.load_plugins(bVerbose)
        for cPlugin in self._oPluginManager.get_card_list_plugins():
            # Find plugins that will work on the Main Window
            self._aPlugins.append(cPlugin(self, None,
                "MainWindow"))

        self.__oMenu = MainMenu(self, oConfig)

        self.oVBox = gtk.VBox(False, 1)
        self.oVBox.pack_start(self.__oMenu, False, False)
        self.oVBox.show()
        self.add(self.oVBox)

        self.show_all()
        self.restore_from_config()

    # pylint: enable-msg=W0201

    # pylint: disable-msg=W0212
    # We allow access via these properties
    # Needed for Backup plugin
    cardLookup = property(fget=lambda self: self._oCardLookup)

    # Needed for plugins
    plugin_manager = property(fget=lambda self: self._oPluginManager,
            doc="The plugin manager for the application")
    plugins = property(fget=lambda self: self._aPlugins,
            doc="Plugins enabled for the main window.")
    config_file = property(fget=lambda self: self._oConfig,
            doc="The confi file")
    focussed_pane = property(fget=lambda self: self._oFocussed,
            doc="The currently focussed pane.")
    mainwindow = property(fget=lambda self: self,
            doc="Return reference to the window")
    icon_manager = property(fget=lambda self: self._oIconManager,
            doc="Return reference to the window")

    # pylint: enable-msg=W0212

    def add_to_menu_list(self, sMenuFlag, oMenuActiveFunc):
        """Add a key to the list of menu items to manage."""
        if not self.__dMenus.has_key(sMenuFlag):
            self.__dMenus[sMenuFlag] = oMenuActiveFunc

    # working directory methods

    def get_working_dir(self):
        """Get the current working dir for file chooser widgets"""
        return self._sWorkingDir

    def set_working_dir(self, sNewDir):
        """Set the working dir to sNewDir."""
        self._sWorkingDir = sNewDir

    # Config file handling

    def restore_from_config(self):
        """Restore all the frame form the config file."""
        # pylint: disable-msg=R0912
        # Need to consider all these cases, so many branches
        if self._iNumberOpenFrames > 0:
            # Clear out all existing frames
            # pylint: disable-msg=W9967
            # Need to use keys(), since we remove items from the dictionary
            # in remove_frame
            for oFrame in self.dOpenFrames.keys():
                self.remove_frame(oFrame, True)
        iWidth, iHeight = self._oConfig.get_window_size()
        if iWidth > 0 and iHeight > 0:
            self.resize(iWidth, iHeight)
        # pylint: disable-msg=W0612
        # iNumber is not used here, but returned from the config file
        for iNumber, sType, sName, bVert, iPos in \
                self._oConfig.get_all_panes():
            oNewFrame = self.add_pane(bVert, iPos)
            self._oFocussed = oNewFrame
            if sType == PhysicalCardSet.sqlmeta.table:
                self.replace_with_physical_card_set(sName, oNewFrame)
            elif sType == 'Card Text':
                self.replace_with_card_text(None)
            elif sType == PhysicalCard.sqlmeta.table:
                self.replace_with_physical_card_list(None)
            elif sType == 'Physical Card Set List':
                self.replace_with_pcs_list(None)
            else:
                # See if one of the plugins claims this type
                for oPlugin in self._aPlugins:
                    tResult = oPlugin.get_frame_from_config(sType)
                    if tResult:
                        oFrame, sMenuFlag = tResult
                        self.replace_frame(oNewFrame, oFrame, sMenuFlag)
        if self._iNumberOpenFrames == 0:
            # We always have at least one pane
            self.add_pane()

    # Pane manipulation functions

    def find_pane_by_name(self, sName):
        """Return the gtk widget corresponding to the given pane name"""
        # pylint: disable-msg=W0704
        # not doing anything for ValueError is the right thing here
        try:
            iIndex = self.dOpenFrames.values().index(sName)
            oPane = self.dOpenFrames.keys()[iIndex]
            return oPane
        except ValueError:
            return None

    def replace_with_physical_card_set(self, sName, oFrame):
        """Replace the pane oFrame with the physical card set sName"""
        sMenuFlag = "PCS:" + sName
        if sMenuFlag not in self.dOpenFrames.values() and oFrame:
            # pylint: disable-msg=W0704
            # not doing anything for errors right now
            try:
                oPane = PhysicalCardSetFrame(self, sName)
                self.replace_frame(oFrame, oPane, sMenuFlag)
            except RuntimeError:
                # add warning dialog?
                pass
        else:
            oPane = self.find_pane_by_name(sMenuFlag)
            if oPane:
                oPane.reload()

    def add_new_physical_card_set(self, sName):
        """Create a new pane and replace with the PCS sName"""
        oFrame = self.add_pane_end()
        self.replace_with_physical_card_set(sName, oFrame)

    # pylint: disable-msg=W0613
    # oWidget needed so this can be called from the menu
    def replace_with_pcs_list(self, oWidget):
        """Replace the focussed pane with the physical card set list."""
        sMenuFlag = "Physical Card Set List"
        if sMenuFlag not in self.dOpenFrames.values() and self._oFocussed:
            oPane = PhysicalCardSetListFrame(self)
            self.replace_frame(self._oFocussed, oPane, sMenuFlag)
            self._oPCSListPane = oPane

    def add_new_pcs_list(self, oMenuWidget):
        """Add a new pane and replace it with the physical card set list."""
        oCurFocus = self._oFocussed
        self._oFocussed = self.add_pane_end()
        self.replace_with_pcs_list(oMenuWidget)
        self._oFocussed = oCurFocus

    def replace_with_physical_card_list(self, oWidget):
        """Replace the currently focussed pane with the physical card list."""
        sMenuFlag = "White Wolf Card List"
        if sMenuFlag not in self.dOpenFrames.values() and self._oFocussed:
            oPane = PhysicalCardFrame(self)
            self.replace_frame(self._oFocussed, oPane, sMenuFlag)

    def add_new_physical_card_list(self, oMenuWidget):
        """Add a new pane and replace it with the physical card list."""
        oCurFocus = self._oFocussed
        self._oFocussed = self.add_pane_end()
        self.replace_with_physical_card_list(oMenuWidget)
        self._oFocussed = oCurFocus

    def replace_with_card_text(self, oWidget):
        """Replace the current pane with the card set pane."""
        sMenuFlag = "Card Text"
        if sMenuFlag not in self.dOpenFrames.values() and self._oFocussed:
            self.replace_frame(self._oFocussed, self._oCardTextPane, sMenuFlag)

    def add_new_card_text(self, oMenuWidget):
        """Add a new pane and replace it with the card set pane."""
        oCurFocus = self._oFocussed
        self._oFocussed = self.add_pane_end()
        self.replace_with_card_text(oMenuWidget)
        self._oFocussed = oCurFocus

    # pylint: enable-msg=W0613

    # state manipulation
    def reload_pcs_list(self):
        """Reload the list of physical card sets."""
        if self._oPCSListPane is not None:
            self._oPCSListPane.reload()

    def reload_acs_list(self):
        """Reload the list of abstract card sets."""
        if self._oACSListPane is not None:
            self._oACSListPane.reload()

    def reload_all(self):
        """Reload all open frames. Useful for major DB changes"""
        for oPane in self.dOpenFrames:
            oPane.reload()

    def get_editable_panes(self):
        """Get a list of panes, which are currently editable.

           Used by the WW import code, and backup restores to correct
           for the zero card list state setting the cardlist's to editable.
           """
        aEditable = []
        for oPane in self.dOpenFrames:
            if hasattr(oPane.view, 'toggle_editable'):
                if oPane.view.get_model().bEditable:
                    aEditable.append(oPane)
        return aEditable

    def restore_editable_panes(self, aEditable):
        """Restore the editable state so only the panes in aEditable are
           editable."""
        for oPane in self.dOpenFrames:
            if hasattr(oPane.view, 'toggle_editable'):
                if oPane in aEditable:
                    oPane.view.toggle_editable(True)
                else:
                    oPane.view.toggle_editable(False)
                    # Empty panes still need to be editable, though
                    oPane.view.check_editable()

    # pylint: disable-msg=W0613
    # oWidget, oEvent needed by function signature
    def win_focus(self, oWidget, oEvent, oFrame):
        """Responsd to focus change events.

           Keep track of focussed pane, update menus and handle highlighting.
           """
        if self._oFocussed is not None:
            self._oFocussed.set_unfocussed_title()
        self._oFocussed = oFrame
        self._oFocussed.set_focussed_title()
        self._oFocussed.view.grab_focus()
        self.reset_menu()

    # pylint: enable-msg=W0613

    def set_card_text(self, sCardName):
        """Update the card text frame to the currently selected card."""
        # pylint: disable-msg=E1101, W0704
        # E1101 - SQLObject confuse pylint
        # W0704 - not doing anything is the right thing here
        try:
            oCard = AbstractCard.byCanonicalName(sCardName.lower())
            self._oCardTextPane.view.set_card_text(oCard)
        except SQLObjectNotFound:
            pass

    def reset_menu(self):
        """Ensure menu state is correct."""
        for sMenu, fSetSensitiveFunc in self.__dMenus.iteritems():
            if sMenu in self.dOpenFrames.values():
                fSetSensitiveFunc(False)
            else:
                fSetSensitiveFunc(True)
        if self._oFocussed:
            # Can always split horizontally
            self.__oMenu.set_split_horizontal_active(True)
            # But we can't split vertically more than once
            if type(self._oFocussed.get_parent()) is gtk.VPaned:
                self.__oMenu.set_split_vertical_active(False)
            else:
                self.__oMenu.set_split_vertical_active(True)
            if self._iNumberOpenFrames > 1:
                self.__oMenu.del_pane_set_sensitive(True)
            else:
                self.__oMenu.del_pane_set_sensitive(False)
        else:
            # Can't split when no pane chosen
            self.__oMenu.set_split_vertical_active(False)
            self.__oMenu.set_split_horizontal_active(False)
            # Can't delete either
            self.__oMenu.del_pane_set_sensitive(False)
        # Enable / disable the menu's
        for oFrame in self.dOpenFrames:
            if not hasattr(oFrame,'menu'):
                continue
            elif self._oFocussed == oFrame:
                if hasattr(oFrame.menu, 'activate_accels'):
                    oFrame.menu.activate_accels()
            else:
                if hasattr(oFrame.menu, 'remove_accels'):
                    oFrame.menu.remove_accels()

    def set_selection_text(self, sText):
        """Set the current selection text for copy+paste."""
        self._sCardSelection = sText

    def get_selection_text(self):
        """Get the current selection for copy+paste."""
        return self._sCardSelection

    # startup, exit and other misc functions

    # pylint: disable-msg=R0201
    # making this a function would not be convient
    def run(self):
        """gtk entry point"""
        gtk.main()

    # pylint: enable-msg=R0201

    # pylint: disable-msg=W0613
    # oWidget, oEvent needed by function signature
    def action_quit(self, oWidget):
        """Exit the app, saving infoin config file if needed."""
        if self._oConfig.get_save_on_exit():
            self.save_frames()
        if self._oConfig.get_save_window_size():
            self.save_window_size()
        gtk.main_quit()

    # pylint: enable-msg=W0613

    def save_window_size(self):
        """Write the current window size to the config file"""
        self._oConfig.save_window_size(self.get_size())

    def save_frames(self):
        """save the current frame layout"""
        self._oConfig.pre_save_clear()

        def save_children(oPane, oConfig, bVert, iNum, iPos):
            """Walk the tree of HPanes + VPanes, and save their info."""
            # oPane.get_position() gives us the position relative to the paned
            # we're contained in. However, when we recreate the layout, we
            # don't split panes in the same order, hence the fancy
            # score-keeping work to convert the obtained positions to those
            # needed for restoring
            if type(oPane) is gtk.HPaned:
                oChild1 = oPane.get_child1()
                oChild2 = oPane.get_child2()
                iNum, iChildPos = save_children(oChild1, oConfig, False,
                        iNum, iPos)
                iMyPos = oPane.get_position()
                if type(oChild1) is gtk.HPaned:
                    iMyPos = iMyPos - iChildPos
                    iChildPos = oPane.get_position()
                else:
                    iChildPos = iMyPos
                if iMyPos < 1:
                    # Setting pos to < 1 doesn't do what we want
                    iMyPos = 1
                iNum, iChild2Pos = save_children(oChild2, oConfig, False,
                        iNum, iMyPos)
                if type(oChild2) is gtk.HPaned:
                    iChildPos += iChild2Pos
            elif type(oPane) is gtk.VPaned:
                oChild1 = oPane.get_child1()
                oChild2 = oPane.get_child2()
                iMyPos = oPane.get_position()
                # pylint: disable-msg=W0612
                # iTemp is unused
                iNum, iTemp = save_children(oChild1, oConfig, False, iNum,
                        iPos)
                iNum, iTemp = save_children(oChild2, oConfig, True, iNum,
                        iMyPos)
                iChildPos = iPos
            else:
                oConfig.add_frame(iNum, oPane.type, oPane.name, bVert, iPos)
                iNum += 1
                iChildPos = iPos
            return iNum, iChildPos

        aTopLevelPane = [x for x in self.oVBox.get_children() if
                x != self.__oMenu]
        for oPane in aTopLevelPane:
            save_children(oPane, self._oConfig, False, 1, -1)


    # pylint: disable-msg=W0613
    # oWidget needed by function signature

    # pylint: disable-msg=R0201
    # making this a function would not be convient
    def show_about_dialog(self, oWidget):
        """Display the about dialog"""
        oDlg = SutekhAboutDialog()
        oDlg.run()
        oDlg.destroy()

    # pylint: enable-msg=R0201

    def show_tutorial(self, oMenuWidget, oHelpLast):
        """Show the HTML Tutorial"""
        fTutorial = resource_stream('sutekh', '/docs/Tutorial.html')
        oHelpLast.set_sensitive(True)
        self._do_html_dialog(fTutorial)

    def show_manual(self, oMenuWidget, oHelpLast):
        """Show the HTML Manual"""
        fManual = resource_stream('sutekh', '/docs/Manual.html')
        oHelpLast.set_sensitive(True)
        self._do_html_dialog(fManual)

    def show_last_help(self, oMenuWidget):
        """Reshow the help dialog with the last shown page"""
        if self._oHelpDlg is not None:
            self._oHelpDlg.show()

    # pylint: enable-msg=W0613

    def _do_html_dialog(self, fInput):
        """Popup and run HTML Dialog widget"""
        if self._oHelpDlg is None:
            self._oHelpDlg = HTMLViewDialog(self, fInput)
        else:
            self._oHelpDlg.show_page(fInput)
        self._oHelpDlg.show()

    # frame management functions

    def replace_frame(self, oOldFrame, oNewFrame, sMenuFlag):
        """Replace oOldFrame with oNewFrame + update menus"""
        oNewFrame.show_all()
        oNewFrame.set_focus_handler(self.win_focus)
        oParent = oOldFrame.get_parent()
        oParent.remove(oOldFrame)
        oParent.add(oNewFrame)
        del self.dOpenFrames[oOldFrame]
        self.dOpenFrames[oNewFrame] = sMenuFlag
        if self._oFocussed == oOldFrame:
            self._oFocussed = None
        self.reset_menu()
        # Open card lists may have changed because of the frame we've
        # kicked out
        self.reload_pcs_list()
        self.reload_acs_list()

    def swap_frames(self, oFrame1, oFrame2):
        """swap two frames - used by drag-n-drop code"""
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
        """Get the parent HPane of the focussed pane.

           If there's no Focussed Pane, return the last added pane,
           which does the right thing for restore_from_config.
           """
        if self._oFocussed:
            oParent = self._oFocussed.get_parent()
            if type(oParent) is gtk.VPaned:
                # Get the HPane this belongs to
                oParent = oParent.get_parent()
            return oParent
        else:
            # Return the last added pane, for automatic adds
            return self._aHPanes[-1]

    def add_pane_end(self, oWidget=None):
        """Add a pane to the right edge of the window.

           Used for the add pane menu items and double clicking on card set
           names
           """
        if self._iNumberOpenFrames < 1:
            oPane = None
        else:
            # Descend the right child of the panes, until we get a
            # non-paned item
            oPane = [x for x in self.oVBox.get_children() if
                    x != self.__oMenu][0]
            while type(oPane) is gtk.HPaned or type(oPane) is gtk.VPaned:
                oPane = oPane.get_child2()
        self._oFocussed = oPane
        return self.add_pane()

    def add_pane(self, bVertical=False, iConfigPos=-1):
        """Add a blank frame to the window.

           bVertical -> set True to split the current pane vertically
           iConfigPos -> Layout parameter for restoring positions.
           if iConfigPos == -1, the currently focussed frame is
           halved in size.
           """
        # this is a complex function (argulably too complex). Simplifying
        # it is non trivial, but I'm leaving the R0915 + R0912 wanring for
        # now
        oWidget = BasicFrame(self)
        oWidget.add_parts()
        oWidget.set_focus_handler(self.win_focus)
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
                        # Veritical pane, so we need to use the pane, not
                        # the Frame
                        oPart1 = oPart1.get_parent()
                else:
                    # Replace right child of last added pane when no
                    # obvious option
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
                        if oCur.width == 1 and oParent.get_position() > 1 and \
                                iConfigPos == -1:
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
                oPart1 = [x for x in self.oVBox.get_children() if
                        x != self.__oMenu][0]
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
            if iConfigPos == -1:
                oNewPane.set_position(iPos)
            else:
                oNewPane.set_position(iConfigPos)
        self._iNumberOpenFrames += 1
        self.oVBox.show_all()
        self.reset_menu()
        return oWidget

    def menu_remove_frame(self, oMenuWidget):
        """Handle the remove pane request from the menu"""
        self.remove_frame(self._oFocussed)

    def remove_frame_by_name(self, sName):
        """Remove the pane with the given name"""
        oPane = self.find_pane_by_name(sName)
        if oPane is not None:
            self.remove_frame(oPane)

    def remove_frame(self, oFrame, bForceZero=False):
        """Remove the Frame oFrame from the window.

           bForceZero is used to force the removal of the last widget in
           the window.
           """
        if oFrame is not None:
            if self._iNumberOpenFrames == 1:
                if not bForceZero:
                    # Break out, as we do nothing
                    return
                # Removing last widget, so just clear the vbox
                oWidget = [x for x in self.oVBox.get_children() if
                        x != self.__oMenu][0]
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
                oFocussedPane = [x for x in self._aHPanes if oFrame in
                        x.get_children()][0]
                oKept = [x for x in oFocussedPane.get_children() if
                        x != oFrame][0]
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
            del self.dOpenFrames[oFrame]
            # Any cleanup events we need?
            oFrame.cleanup()
            if oFrame == self._oFocussed:
                self._oFocussed = None
            self.reset_menu()

    def set_all_panes_equal(self):
        """Evenly distribute the space between all the frames."""
        oCurAlloc = self.oVBox.get_allocation()
        iNewPos = oCurAlloc.width / (len(self._aHPanes) + 1)
        self.set_pos_for_all_hpanes(iNewPos)

    def set_pos_for_all_hpanes(self, iNewPos):
        """Set all the panes to the same Position value"""
        oCurAlloc = self.oVBox.get_allocation()
        oMenuAlloc = self.__oMenu.get_allocation()
        iVertPos = (oCurAlloc.height - oMenuAlloc.height) / 2
        def set_pos_children(oPane, iPos, iVertPos):
            """Walk the tree in display order, setting positions accordingly"""
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

        aTopLevelPane = [x for x in self.oVBox.get_children() if
                x != self.__oMenu]
        for oPane in aTopLevelPane:
            # Should only be 1 here
            if type(oPane) is gtk.HPaned:
                set_pos_children(oPane, iNewPos, iVertPos)
            elif type(oPane) is gtk.VPaned:
                # Do something sensible for single VPane case
                oPane.set_position(iVertPos)
