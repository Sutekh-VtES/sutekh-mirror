# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Handle the multi pane UI for Sutkeh
# Copyright 2007, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - See COPYING for details

"""Main window for Sutekh."""

# pylint: disable-msg=C0302
# C0302 - the module is long, but keeping the everything together is the best
# option for now

import pygtk
pygtk.require('2.0')
import gtk
import logging
import socket
# pylint: disable-msg=E0611
# pylint doesn't see resource_stream here, for some reason
from pkg_resources import resource_stream, resource_exists
from itertools import chain
# pylint: enable-msg=E0611
from sqlobject import SQLObjectNotFound
from sutekh.core.SutekhObjectCache import SutekhObjectCache
from sutekh.base.core.BaseObjects import PhysicalCardSet, \
        PhysicalCard, IAbstractCard
from sutekh.base.core.DBUtility import flush_cache
from sutekh.gui.MultiPaneWindow import MultiPaneWindow
from sutekh.gui.PhysicalCardFrame import PhysicalCardFrame
from sutekh.gui.CardTextFrame import CardTextFrame
from sutekh.gui.CardSetFrame import CardSetFrame
from sutekh.gui.AboutDialog import SutekhAboutDialog
from sutekh.gui.MainMenu import MainMenu
from sutekh.gui.GuiCardLookup import GuiLookup
from sutekh.gui.GuiCardSetFunctions import break_existing_loops
from sutekh.gui.CardSetManagementFrame import CardSetManagementFrame
from sutekh.gui.PluginManager import PluginManager
from sutekh.gui.GuiDBManagement import refresh_ww_card_list
from sutekh.gui import SutekhIcon
from sutekh.gui.MessageBus import MessageBus, DATABASE_MSG
from sutekh.gui.HTMLTextView import HTMLViewDialog
from sutekh.gui.GuiIconManager import GuiIconManager
from sutekh.gui.SutekhDialog import do_complaint_error_details, \
        do_exception_complaint, do_complaint


class SutekhMainWindow(MultiPaneWindow):
    """Window that has a configurable number of panes."""
    # pylint: disable-msg=R0904, R0902
    # R0904 - gtk.Widget, so many public methods
    # R0902 - we need to keep a lot of state, so many instance attributes
    def __init__(self):
        super(SutekhMainWindow, self).__init__()
        self.set_border_width(2)

        # make sure we can quit
        self.connect("destroy", self.action_quit)
        self.connect("delete-event", self.action_close)
        # We can shrink the window quite small
        self.set_size_request(100, 100)
        # But we start at a reasonable size
        self.set_default_size(800, 600)

        # Set Default Window Icon for all Windows
        gtk.window_set_default_icon(SutekhIcon.SUTEKH_ICON)

        # common current directory for file dialogs
        self._sWorkingDir = ''

        self._sCardSelection = ''  # copy + paste selection
        self._aPlugins = []
        self.__dMenus = {}

        # CardText frame is special, and there is only ever one of it
        # but we will set it up later
        self._bCardTextShown = False
        self._oCardTextPane = None
        self._oPCSListPane = None
        self._oHelpDlg = None
        # Global icon manager
        self._oIconManager = None
        # Sutekh lookuo cache
        self.__oSutekhObjectCache = None

    # pylint: disable-msg=W0201
    # We define attributes here, since this is called after database checks
    def setup(self, oConfig):
        """After database checks are passed, setup what we need to display
           data from the database."""
        self._oConfig = oConfig
        self._oCardLookup = GuiLookup(self._oConfig)

        # Check database is correctly populated

        try:
            _oCard = IAbstractCard('Ossian')
        except SQLObjectNotFound:
            # Log error so verbose picks it up
            logging.warn('Ossian not found in the database')
            # Inform the user
            iResponse = do_complaint(
                    'Database is missing cards. Try import the cardlist now?',
                    gtk.MESSAGE_ERROR, gtk.BUTTONS_YES_NO, False)
            if iResponse == gtk.RESPONSE_YES:
                refresh_ww_card_list(self)

        # Load plugins
        self._oPluginManager = PluginManager()
        self._oPluginManager.load_plugins()
        for cPlugin in self._oPluginManager.get_card_list_plugins():
            # Find plugins that will work on the Main Window
            self._aPlugins.append(cPlugin(self, None,
                "MainWindow"))
            cPlugin.register_with_config(oConfig)

        # Re-validate config after adding plugin specs
        oValidationResults = oConfig.validate()
        aErrors = oConfig.validation_errors(oValidationResults)
        if aErrors:
            logging.warn('Configuration file validation errors:\n%s',
                    "\n".join(aErrors))
            do_complaint_error_details(
                    "The configuration file validation failed:",
                    "\n".join(aErrors))
        oConfig.sanitize()

        # Create object cache
        self.__oSutekhObjectCache = SutekhObjectCache()

        # Create global icon manager
        self._oIconManager = GuiIconManager(oConfig.get_icon_path())
        # Create card text pane
        self._oCardTextPane = None  # So we can call get_pane_ids
        self._oCardTextPane = CardTextFrame(self, self._oIconManager)

        self._oMenu = MainMenu(self, oConfig)

        # setup the global socket timeout to the config default
        iTimeout = oConfig.get_socket_timeout()
        socket.setdefaulttimeout(iTimeout)

        # Do setup - prompt for downloads, etc. if needed
        self._oIconManager.setup()
        # plugins as well
        for oPlugin in self._aPlugins:
            oPlugin.setup()

        # Break any loops in the database
        break_existing_loops()

        self._setup_vbox()
        self.restore_from_config()

    # pylint: enable-msg=W0201

    # pylint: disable-msg=W0212
    # We allow access via these properties
    # Needed for Backup plugin
    cardLookup = property(fget=lambda self: self._oCardLookup,
        doc="Used if user instance is needed to identify card names.")
    # Needed for plugins
    plugin_manager = property(fget=lambda self: self._oPluginManager,
            doc="The plugin manager for the application")
    plugins = property(fget=lambda self: self._aPlugins,
            doc="Plugins enabled for the main window.")
    config_file = property(fget=lambda self: self._oConfig,
            doc="The config file")
    icon_manager = property(fget=lambda self: self._oIconManager,
            doc="Used to lookup icons for disciplines, clans, etc.")
    card_text_pane = property(fget=lambda self: self._oCardTextPane,
            doc="Return reference to the card text pane")

    # pylint: enable-msg=W0212

    def add_to_menu_list(self, sMenuFlag, oMenuActiveFunc):
        """Add a key to the list of menu items to manage."""
        if sMenuFlag not in self.__dMenus:
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
        # pylint: disable-msg=R0912, R0914, W9967
        # R0912: Need to consider all these cases, so many branches
        # R0914: Consequently, many local variables
        self._clear_frames()
        # Flag to delay reloading pcs card list until after everything else
        # has loaded
        bReloadPCS = False

        aClosedFrames = []

        iWidth, iHeight = self._oConfig.get_window_size()
        if iWidth > 0 and iHeight > 0:
            self.resize(iWidth, iHeight)
            # Process the resize event before continuing,
            # otherwise the size may be wrong in the following code
            while gtk.events_pending():
                gtk.main_iteration()
        # Reset the pane number count, since we're starting afresh
        self._iCount = 0
        dPaneMap = {}
        for _iNumber, sType, sName, sOldId, bVert, bClosed, iPos in \
                self._oConfig.open_frames():
            oNewFrame = self.add_pane(bVert, iPos)
            oRestored = None
            self.win_focus(None, None, oNewFrame)
            if sType == PhysicalCardSet.sqlmeta.table:
                oRestored = self.replace_with_physical_card_set(sName,
                        oNewFrame, False)
                bReloadPCS = True
            elif sType == 'Card Text':
                oRestored = self.replace_with_card_text(None)
            elif sType == PhysicalCard.sqlmeta.table:
                oRestored = self.replace_with_physical_card_list(None)
            elif sType == 'Card Set List':
                oRestored = self.replace_with_pcs_list(None)
            else:
                # See if one of the plugins claims this type
                for oPlugin in self._aPlugins:
                    oFrame = oPlugin.get_frame_from_config(sType)
                    if oFrame:
                        self.replace_frame(oNewFrame, oFrame)
                        oRestored = oFrame
            if bClosed and oRestored:
                # Hold off minimizing until all frames are added to avoid
                # corner cases around the 1st restored frame needing to be
                # minimised
                aClosedFrames.append(oRestored)
            if oRestored and sOldId:
                dPaneMap[sOldId] = oRestored.config_frame_id
        for oFrame in aClosedFrames:
            self.minimize_to_toolbar(oFrame)
        if dPaneMap:
            self._oConfig.update_pane_numbers(dPaneMap)
        if bReloadPCS:
            self.reload_pcs_list()
        if not self.aOpenFrames:
            # We always have at least one pane
            self.add_pane()

    # Pane manipulation functions

    def get_pane_ids(self):
        """Return a list of all relevant pane ids"""
        aIds = super(SutekhMainWindow, self).get_pane_ids()
        if self._oCardTextPane:
            aIds.append(self._oCardTextPane.pane_id)
        return aIds

    def is_open_by_menu_name(self, sMenuFlag):
        """Check if a frame with the given menu name is open"""
        for oPane in chain(self.aOpenFrames, self.aClosedFrames):
            if oPane.get_menu_name() == sMenuFlag:
                return True
        return False

    def find_cs_pane_by_set_name(self, sSetName):
        """Find all the panes that correspond to the same card set"""
        aPanes = []
        for oPane in chain(self.aOpenFrames, self.aClosedFrames):
            if oPane.is_card_set(sSetName):
                aPanes.append(oPane)
        return aPanes

    def replace_with_physical_card_set(self, sName, oFrame, bDoReloadPCS=True,
            bStartEditable=False):
        """Replace the pane oFrame with the physical card set sName"""
        if oFrame:
            # pylint: disable-msg=W0704
            # not doing anything for errors right now
            try:
                oPane = CardSetFrame(self, sName, bStartEditable)
                self.replace_frame(oFrame, oPane)
                # Open card lists may have changed because of the frame we've
                # kicked out
                if bDoReloadPCS:
                    self.reload_pcs_list()
                return oPane
            except RuntimeError, oExp:
                do_exception_complaint("Unable to open Card Set %s\n"
                        "Error: %s" % (sName, oExp))
        return None

    def add_new_physical_card_set(self, sName, bStartEditable=False):
        """Create a new pane and replace with the PCS sName"""
        oFrame = self.add_pane_end()
        return self.replace_with_physical_card_set(sName, oFrame,
                bStartEditable=bStartEditable)

    def replace_with_pcs_list(self, _oWidget, oOldFrame=None):
        """Replace the focussed or given pane with the physical card set
           list."""
        if self.is_open_by_menu_name("Card Set List"):
            return None
        if oOldFrame is None:
            oOldFrame = self._oFocussed
        oPane = CardSetManagementFrame(self)
        self.replace_frame(oOldFrame, oPane)
        self._oPCSListPane = oPane
        return oPane

    def add_new_pcs_list(self, oMenuWidget):
        """Add a new pane and replace it with the physical card set list."""
        oNewPane = self.add_pane_end()
        return self.replace_with_pcs_list(oMenuWidget, oNewPane)

    def replace_with_physical_card_list(self, _oWidget, oOldFrame=None):
        """Replace the currently focussed or given pane with the physical
           card list."""
        if self.is_open_by_menu_name("White Wolf Card List"):
            return None
        if oOldFrame is None:
            oOldFrame = self._oFocussed
        oPane = PhysicalCardFrame(self)
        self.replace_frame(oOldFrame, oPane)
        return oPane

    def add_new_physical_card_list(self, oMenuWidget):
        """Add a new pane and replace it with the physical card list."""
        oNewPane = self.add_pane_end()
        return self.replace_with_physical_card_list(oMenuWidget, oNewPane)

    def replace_with_card_text(self, _oWidget, oOldFrame=None):
        """Replace the current or given pane with the card set pane."""
        if self.is_open_by_menu_name("Card Text"):
            return None
        if oOldFrame is None:
            oOldFrame = self._oFocussed
        self.replace_frame(oOldFrame, self._oCardTextPane)
        return self._oCardTextPane

    def add_new_card_text(self, oMenuWidget):
        """Add a new pane and replace it with the card set pane."""
        oNewPane = self.add_pane_end()
        return self.replace_with_card_text(oMenuWidget, oNewPane)

    # state manipulation
    def reload_pcs_list(self):
        """Reload the list of physical card sets."""
        if self._oPCSListPane is not None:
            self._oPCSListPane.reload()

    def update_to_new_db(self):
        """Resync panes against the database.

           Needed because ids aren't kept across re-reading the WW
           cardlist, since card sets with children are always created
           before there children are added.
           """
        # Flush the caches, so we don't hit stale lookups
        flush_cache()
        # Reset the lookup cache holder
        self.__oSutekhObjectCache = SutekhObjectCache()
        # We publish here, after we've cleared the caches
        MessageBus.publish(DATABASE_MSG, "update_to_new_db")

    # pylint: disable-msg=R0201
    # making this a function would not be convenient
    def prepare_for_db_update(self):
        """Handle any preparation for the database upgrade"""
        MessageBus.publish(DATABASE_MSG, "prepare_for_db_update")

    # pylint: enable-msg=R0201

    def clear_cache(self):
        """Remove the cached set of objects, for card list reloads, etc."""
        del self.__oSutekhObjectCache

    def get_editable_panes(self):
        """Get a list of panes, which are currently editable.

           Used by the WW import code, and backup restores to correct
           for the zero card list state setting the cardlist's to editable.
           """
        aEditable = []
        for oPane in chain(self.aOpenFrames, self.aClosedFrames):
            if hasattr(oPane.view, 'toggle_editable'):
                if oPane.view.get_model().bEditable:
                    aEditable.append(oPane)
        return aEditable

    def restore_editable_panes(self, aEditable):
        """Restore the editable state so only the panes in aEditable are
           editable."""
        for oPane in chain(self.aOpenFrames, self.aClosedFrames):
            if hasattr(oPane.view, 'toggle_editable'):
                if oPane in aEditable:
                    oPane.view.toggle_editable(True)
                else:
                    oPane.view.toggle_editable(False)

    def reset_menu(self):
        """Ensure menu state is correct."""
        for fSetSensitiveFunc in self.__dMenus.values():
            fSetSensitiveFunc(True)
        for oPane in chain(self.aOpenFrames, self.aClosedFrames):
            sMenuName = oPane.get_menu_name()
            if sMenuName in self.__dMenus:
                self.__dMenus[sMenuName](False)
        # Disable the menu accelerators for unfocussed panes
        for oFrame in chain(self.aOpenFrames, self.aClosedFrames):
            if self._oFocussed != oFrame and hasattr(oFrame, 'menu') and \
                    hasattr(oFrame.menu, 'remove_accels'):
                oFrame.menu.remove_accels()
        # Handle focussed pane stuff
        if self._oFocussed:
            # Can always split horizontally
            self._oMenu.set_split_horizontal_active(True)
            self._oMenu.replace_pane_set_sensitive(True)
            # But we can't split vertically more than once
            if isinstance(self._oFocussed.get_parent(), gtk.VPaned):
                self._oMenu.set_split_vertical_active(False)
            else:
                self._oMenu.set_split_vertical_active(True)
            # can't delete the last pane
            if len(self.aOpenFrames) > 1:
                self._oMenu.del_pane_set_sensitive(True)
            else:
                self._oMenu.del_pane_set_sensitive(False)
            # Ensure accelerators are active
            if hasattr(self._oFocussed, 'menu') and \
                    hasattr(self._oFocussed.menu, 'activate_accels'):
                self._oFocussed.menu.activate_accels()
        else:
            # Can't split when no pane chosen
            self._oMenu.set_split_vertical_active(False)
            self._oMenu.set_split_horizontal_active(False)
            # Can't delete either
            self._oMenu.del_pane_set_sensitive(False)
            self._oMenu.replace_pane_set_sensitive(False)

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

    def action_quit(self, _oWidget):
        """Exit the app"""
        # ensure we cleanup all signals (needed for tests)
        for oFrame in chain(self.aOpenFrames, self.aClosedFrames):
            oFrame.cleanup(True)
        for oPlugin in self._aPlugins:
            oPlugin.cleanup()
        # don't hold references to plugins here either
        self._aPlugins = []
        # Don't call gtk.main_quit when the main loop isn't running (true in
        # the tests)
        if gtk.main_level() > 0:
            gtk.main_quit()

    def show_about_dialog(self, _oWidget):
        """Display the about dialog"""
        oDlg = SutekhAboutDialog()
        oDlg.run()
        oDlg.destroy()

    def _link_resource(self, sLocalUrl):
        """Return a file-like object which sLocalUrl can be read from."""
        sResource = '/docs/html/%s' % sLocalUrl
        if resource_exists('sutekh', sResource):
            return resource_stream('sutekh', sResource)
        else:
            raise ValueError("Unknown resource %s" % sLocalUrl)

    # pylint: enable-msg=R0201

    def action_close(self, _oWidget, _oEvent):
        """Close the app (menu or window manager) and save the settings"""
        if self._oConfig.get_save_on_exit():
            self.save_frames()
        if self._oConfig.get_save_window_size():
            self.save_window_size()
        # cue app exit
        self.destroy()

    def show_tutorial(self, _oMenuWidget, oHelpLast):
        """Show the HTML Tutorial"""
        fTutorial = self._link_resource('Tutorial.html')
        oHelpLast.set_sensitive(True)
        self._do_html_dialog(fTutorial)

    def show_manual(self, _oMenuWidget, oHelpLast):
        """Show the HTML Manual"""
        fManual = self._link_resource('Manual.html')
        oHelpLast.set_sensitive(True)
        self._do_html_dialog(fManual)

    def show_last_help(self, _oMenuWidget):
        """Reshow the help dialog with the last shown page"""
        if self._oHelpDlg is not None:
            self._oHelpDlg.show()

    def menu_remove_frame(self, _oMenuWidget):
        """Handle the remove pane request from the menu"""
        # Closing the pane via the menu, so remove any existing pane profiles
        self._oConfig.clear_frame_profile(self._oFocussed.config_frame_id)
        self.remove_frame(self._oFocussed)

    def _do_html_dialog(self, fInput):
        """Popup and run HTML Dialog widget"""
        if self._oHelpDlg is None:
            self._oHelpDlg = HTMLViewDialog(self, fInput, self._link_resource)
        else:
            self._oHelpDlg.show_page(fInput)
        self._oHelpDlg.show()

    # window setup saving functions

    def save_window_size(self):
        """Write the current window size to the config file"""
        self._oConfig.set_window_size(self.get_size())

    def save_frames(self):
        # pylint:disable-msg=R0912
        # lots of decisions, so many branches
        """save the current frame layout"""
        self._oConfig.clear_open_frames()

        # pylint: disable-msg=R0913
        # we need all these arguments
        def save_pane_to_config(iNum, oPane, oConfig, bVert, bClosed, iPos):
            """Save a pane to the config file, dealing with card set panes
               correctly"""
            if oPane.type != PhysicalCardSet.sqlmeta.table:
                oConfig.add_frame(iNum, oPane.type, oPane.name, bVert,
                        bClosed, iPos, oPane.config_frame_id)
            else:
                oConfig.add_frame(iNum, oPane.type, oPane.cardset_name, bVert,
                        bClosed, iPos, oPane.config_frame_id)

        iNum = 1
        for oPane, bVert, iPos in self._get_open_pane_pos():
            save_pane_to_config(iNum, oPane, self._oConfig, bVert, False, iPos)
            iNum += 1
        for oPane in self.aClosedFrames:
            save_pane_to_config(iNum, oPane, self._oConfig, False, True, -1)
            iNum += 1
