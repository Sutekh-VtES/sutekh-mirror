# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Handle the multi pane UI for Sutkeh
# Copyright 2007, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - See COPYING for details

"""Base class for the application main window."""

import logging
import socket
from itertools import chain

from gi.repository import Gtk

# pylint: disable=no-name-in-module
# pylint doesn't see resource_stream here, for some reason
from pkg_resources import resource_stream, resource_exists
# pylint: enable=no-name-in-module

from ..Utility import is_memory_db
from ..core.BaseTables import PhysicalCardSet, PhysicalCard, VersionTable
from ..core.DatabaseVersion import DatabaseVersion
from .MultiPaneWindow import MultiPaneWindow
from .PhysicalCardFrame import PhysicalCardFrame
from .CardSetFrame import CardSetFrame
from .LogViewFrame import LogViewFrame
from .GuiCardLookup import GuiLookup
from .GuiCardSetFunctions import break_existing_loops
from .CardSetManagementFrame import CardSetManagementFrame
from .MessageBus import MessageBus
from .HTMLTextView import HTMLViewDialog
from .SutekhDialog import (do_complaint_error_details, do_exception_complaint,
                           do_complaint)
from .UpdateDialog import UpdateDialog
from .DataFilesDialog import Result
from .QueueLogHandler import QueueLogHandler
# pylint: enable=wrong-import-position


class AppMainWindow(MultiPaneWindow):
    """Window that has a configurable number of panes."""
    # pylint: disable=too-many-instance-attributes, too-many-public-methods
    # we need to keep a lot of state, so many instance attributes
    # Gtk.Widget, so many public methods
    def __init__(self):
        super().__init__()
        self.set_border_width(2)

        # make sure we can quit
        self.connect("destroy", self.action_quit)
        self.connect("delete-event", self.action_close)

        # common current directory for file dialogs
        self._sWorkingDir = ''

        self._sCardSelection = ''  # copy + paste selection
        self._aPlugins = []
        self._dMenus = {}

        # CardText frame is special, and there is only ever one of it
        # but we will set it up later
        self._bCardTextShown = False
        self._oPCSListPane = None
        self._oHelpDlg = None
        self._oIconManager = None
        self._oPluginManager = None
        self._oCardTextPane = None  # So we can call get_pane_ids
        # Class for the card set writer - should be set by subclasses
        self._cPCSWriter = None
        # Class for the database manager (for upgrades, etc)
        self._cDBManager = None
        # Name to use for resource lookups
        self._sResourceName = None
        # Log Handler for the Gui Queue Logger
        self._oGuiLogHandler = QueueLogHandler()
        logging.getLogger().addHandler(self._oGuiLogHandler)

    def _verify_database(self):
        """Verify that the database is correctly populated"""
        # Subclasses will implement this
        raise NotImplementedError

    def do_db_checks(self, oConn, oConfig, bIgnoreVersionCheck=False):
        """Test basic database sanity and version status"""
        # Test on some tables where we specify the table name
        # pylint: disable=not-callable
        # subclasses will provide a callable cDBManager
        oDBManager = self._cDBManager(self)
        if not oConn.tableExists('abstract_card') or \
                not oConn.tableExists('physical_map'):
            if not oDBManager.initialize_db(oConfig):
                return False

        aTables = [VersionTable] + oDBManager.aTables
        aVersions = []

        for oTable in aTables:
            aVersions.append(oTable.tableversion)

        oVer = DatabaseVersion()

        if not oVer.check_tables_and_versions(aTables, aVersions) and \
                not bIgnoreVersionCheck:
            aLowerTables, aHigherTables = oVer.get_bad_tables(aTables,
                                                              aVersions)
            if not oDBManager.do_db_upgrade(aLowerTables, aHigherTables):
                return False
        return True

    def do_refresh_card_list(self, oUpdateDate=None, dFiles=None):
        """Handle reloading the card list via the database manager object."""
        # pylint: disable=not-callable
        # subclasses will provide a callable cDBManager
        self._block_reload()
        oDBManager = self._cDBManager(self)
        bRet = oDBManager.refresh_card_list(oUpdateDate, dFiles)
        self._unblock_reload()
        return bRet

    def do_refresh_from_zip_url(self, oUpdateDate, sUrl, sHash=None):
        """Refresh the card list from the given zip file url"""
        # pylint: disable=not-callable
        # subclasses will provide a callable cDBManager
        oDBManager = self._cDBManager(self)
        oZipDetails = Result(sName=sUrl, bIsUrl=True)
        self._block_reload()
        dFiles = oDBManager.read_zip_file(oZipDetails, sHash)
        bRet = oDBManager.refresh_card_list(oUpdateDate, dFiles)
        self._unblock_reload()
        return bRet

    # pylint: disable=attribute-defined-outside-init
    # We define attributes here, since this is called after database checks
    def setup(self, oConfig):
        """Entry point for setting up the application window"""
        # subclasses will need to implement this to call _do_app_setup
        # with the correct input and handle any other setup tasks needed
        raise NotImplementedError

    def _do_app_setup(self, oConfig, oCardTextFrame,
                      oIconManager, oPluginManager):
        """Check the database and setup what we need to display
           data from the database."""
        self._oConfig = oConfig
        self._oIconManager = oIconManager
        self._oCardTextPane = oCardTextFrame

        self._oCardLookup = GuiLookup(self._oConfig)

        # Check database is correctly populated
        self._verify_database()

        # Load plugins
        self._oPluginManager = oPluginManager
        self._oPluginManager.load_plugins()
        for cPlugin in self._oPluginManager.get_all_plugins():
            # Fixup config to accomodate the plugins
            cPlugin.update_config()
            cPlugin.register_with_config(oConfig)

        # Initiliase plugins that will work on the Main Window
        for cPlugin in self._oPluginManager.get_plugins_for('MainWindow'):
            self._aPlugins.append(cPlugin(self, None,
                                          "MainWindow"))

        # Re-validate config after adding plugin specs
        oValidationResults = oConfig.validate()
        aErrors = oConfig.validation_errors(oValidationResults)
        if aErrors:
            logging.warning('Configuration file validation errors:\n%s',
                            "\n".join(aErrors))
            do_complaint_error_details(
                "The configuration file validation failed:",
                "\n".join(aErrors))
        oConfig.sanitize()

        self._create_app_menu()

        # setup the global socket timeout to the config default
        iTimeout = oConfig.get_socket_timeout()
        socket.setdefaulttimeout(iTimeout)

        # Display initial window and check for cardlist updates
        # We need to do this before we update plugins, so we avoid
        # problems with plugin data that assumes a recent cardlist
        self._setup_vbox()
        self.check_for_updates()

        # Do setup - prompt for downloads, etc. if needed
        self._oIconManager.setup()
        # plugins as well
        for oPlugin in self._aPlugins:
            oPlugin.setup()

        # Break any loops in the database
        break_existing_loops()
        # Process config file settings
        self.restore_from_config()

        # Now we can check for any plugins that have updated data
        self.check_for_plugin_updates()

    def run_plugin_checks(self):
        """Call the run_checks hook for all imported plugins."""
        for oPlugin in self._aPlugins:
            sMsg = oPlugin.run_checks()

    def _create_app_menu(self):
        """Hook for creating the main application menu."""
        # We need to do this after plugin setup, but before
        # we create the application layout, so it needs it's
        # own hook
        # Subclasses will implement this
        raise NotImplementedError

    # pylint: enable=attribute-defined-outside-init

    # pylint: disable=protected-access
    # We allow access via these properties
    # Needed for Backup plugin
    cardLookup = property(fget=lambda self: self._oCardLookup,
                          doc="Used if user assistance is needed to"
                              " identify card names.")
    # Needed for plugins
    plugin_manager = property(fget=lambda self: self._oPluginManager,
                              doc="The plugin manager for the application")
    plugins = property(fget=lambda self: self._aPlugins,
                       doc="Plugins enabled for the main window.")
    config_file = property(fget=lambda self: self._oConfig,
                           doc="The config file")
    icon_manager = property(fget=lambda self: self._oIconManager,
                            doc="Used to lookup icons for the card list"
                                " and card text frames.")
    card_text_pane = property(fget=lambda self: self._oCardTextPane,
                              doc="Return reference to the card text pane")
    gui_log_handler = property(fget=lambda self: self._oGuiLogHandler,
                               doc="Return reference to the log handler")
    # pylint: enable=protected-access

    def add_to_menu_list(self, sMenuFlag, oMenuActiveFunc):
        """Add a key to the list of menu items to manage."""
        if sMenuFlag not in self._dMenus:
            self._dMenus[sMenuFlag] = oMenuActiveFunc

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
        # pylint: disable=too-many-branches, too-many-locals
        # Need to consider all these cases, so many branches
        # Consequently, many local variables
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
            while Gtk.events_pending():
                Gtk.main_iteration()
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
                                                                oNewFrame,
                                                                False)
                bReloadPCS = True
            elif sType == 'Card Text':
                oRestored = self.replace_with_card_text(None)
            elif sType == PhysicalCard.sqlmeta.table:
                oRestored = self.replace_with_physical_card_list(None)
            elif sType == 'Card Set List':
                oRestored = self.replace_with_pcs_list(None)
            elif sType == 'Log View Frame':
                oRestored = self.replace_with_log_view_frame(None)
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

    def check_for_updates(self):
        """Check for updated cardlists and so forth."""
        # Check for cardlist updates before other updates, to avoid
        # ordering issues
        if self._oConfig.get_check_for_updates():
            if is_memory_db():
                # Don't check for updates with an in_memory database, because
                # We need to copy the database for this to work
                do_complaint(
                    "You are running on an temporary test database.\n"
                    "Updates have been disabled as a result.",
                    Gtk.MessageType.WARNING, Gtk.ButtonsType.OK)
                return
            # Check for updated card list
            self.check_updated_cardlist()

    def check_for_plugin_updates(self):
        """Check for any plugins that have updated data"""
        # FIXME: We should probably add a config option so people can
        # skip this if desirable.
        if is_memory_db():
            # Don't check for updates with an in_memory database,
            # because we can't have handled any cardlist updates
            return
        aMessages = []
        aUpdatePlugins = []
        for oPlugin in self._aPlugins:
            sMsg = oPlugin.check_for_updates()
            if sMsg:
                aMessages.append(sMsg)
                aUpdatePlugins.append(oPlugin)
        if aMessages:
            # prompt the user
            oDialog = UpdateDialog(aMessages)
            iResponse = oDialog.run()
            oDialog.destroy()
            if iResponse != Gtk.ResponseType.OK:
                return
            for oPlugin in aUpdatePlugins:
                oPlugin.do_update()

    # Pane manipulation functions

    def get_pane_ids(self):
        """Return a list of all relevant pane ids"""
        aIds = super().get_pane_ids()
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

    def replace_with_log_view_frame(self, _oWidget, oOldFrame=None):
        """Add a log view frame to the window"""
        if self.is_open_by_menu_name("Log View Frame"):
            return None
        if oOldFrame is None:
            oOldFrame = self._oFocussed
        oPane = LogViewFrame(self)
        self.replace_frame(oOldFrame, oPane)
        return oPane

    def add_new_log_view_frame(self, oMenuWidget):
        """Add a new pane and replace it with the log view frame."""
        oNewPane = self.add_pane_end()
        return self.replace_with_log_view_frame(oMenuWidget, oNewPane)

    def replace_with_physical_card_set(self, sName, oFrame, bDoReloadPCS=True,
                                       bStartEditable=False):
        """Replace the pane oFrame with the physical card set sName"""
        if oFrame:
            try:
                oPane = CardSetFrame(self, sName, bStartEditable,
                                     self._cPCSWriter)
                self.replace_frame(oFrame, oPane)
                # Open card lists may have changed because of the frame we've
                # kicked out
                if bDoReloadPCS:
                    self.reload_pcs_list()
                return oPane
            except RuntimeError as oExp:
                do_exception_complaint("Unable to open Card Set %s\n"
                                       "Error: %s" % (sName, oExp))
        return None

    def add_new_physical_card_set(self, sName, bStartEditable=False):
        """Create a new pane and replace with the PCS sName"""
        oFrame = self.add_pane_end()
        return self.replace_with_physical_card_set(
            sName, oFrame, bStartEditable=bStartEditable)

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
        if self.is_open_by_menu_name("Full Card List"):
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

    # pylint: disable=no-self-use
    # Making these functions would not be convenient
    def update_to_new_db(self):
        """Resync panes against the database."""
        # Subclasses will need to implement the details
        MessageBus.publish(MessageBus.Type.DATABASE_MSG, "update_to_new_db")

    def prepare_for_db_update(self):
        """Handle any preparation for the database upgrade"""
        MessageBus.publish(MessageBus.Type.DATABASE_MSG,
                           "prepare_for_db_update")

    def clear_cache(self):
        """Clear any cached objects."""
        # Subclasses should provide this if needed
        pass

    # pylint: enable=no-self-use

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
        for fSetSensitiveFunc in self._dMenus.values():
            fSetSensitiveFunc(True)
        for oPane in chain(self.aOpenFrames, self.aClosedFrames):
            sMenuName = oPane.get_menu_name()
            if sMenuName in self._dMenus:
                self._dMenus[sMenuName](False)
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
            if isinstance(self._oFocussed.get_parent(), Gtk.VPaned):
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

    # pylint: disable=no-self-use
    # making this a function would not be convient
    def run(self):
        """Gtk entry point"""
        Gtk.main()

    def action_quit(self, _oWidget):
        """Exit the app"""
        # ensure we cleanup all signals (needed for tests)
        for oFrame in chain(self.aOpenFrames, self.aClosedFrames):
            oFrame.cleanup(True)
        for oPlugin in self._aPlugins:
            oPlugin.cleanup()
        # don't hold references to plugins here either
        self._aPlugins = []
        # Don't call Gtk.main_quit when the main loop isn't running (true in
        # the tests)
        if Gtk.main_level() > 0:
            Gtk.main_quit()

    def _link_resource(self, sLocalUrl):
        """Return a file-like object which sLocalUrl can be read from."""
        # Subclasses need to provide self._sResourceName
        sResource = '/docs/html_docs/%s' % sLocalUrl
        if resource_exists(self._sResourceName, sResource):
            return resource_stream(self._sResourceName, sResource)
        raise ValueError("Unknown resource %s" % sLocalUrl)

    # pylint: enable=no-self-use

    def action_close(self, _oWidget, _oEvent):
        """Close the app (menu or window manager) and save the settings"""
        if self._oConfig.get_save_on_exit():
            self.save_frames()
        if self._oConfig.get_save_window_size():
            self.save_window_size()
        # cue app exit
        self.destroy()

    def show_last_help(self, _oMenuWidget):
        """Reshow the help dialog with the last shown page"""
        if self._oHelpDlg is not None:
            self._oHelpDlg.show()

    def menu_remove_frame(self, _oMenuWidget):
        """Handle the remove pane request from the menu"""
        # Closing the pane via the menu, so remove any existing pane profiles
        self._oConfig.clear_frame_profile(self._oFocussed.config_frame_id)
        self.remove_frame(self._oFocussed)

    def _do_html_dialog(self, sPage):
        """Popup and run HTML Dialog widget with the given page"""
        fPage = self._link_resource(sPage)
        self._oMenu.set_show_last_help()
        if self._oHelpDlg is None:
            self._oHelpDlg = HTMLViewDialog(self, fPage, self._link_resource)
        else:
            self._oHelpDlg.show_page(fPage)
        self._oHelpDlg.show()

    def show_card_filter_help(self):
        """Popup a help entry for the card filters."""
        self._do_html_dialog("Card_Filters.html")

    def show_card_set_filter_help(self):
        """Popup a help entry for the card set filters."""
        self._do_html_dialog("Card_Set_Filters.html")

    # window setup saving functions

    def save_window_size(self):
        """Write the current window size to the config file"""
        self._oConfig.set_window_size(self.get_size())

    def save_frames(self):
        # pylint: disable=too-many-branches
        # lots of decisions, so many branches
        """save the current frame layout"""
        self._oConfig.clear_open_frames()

        # pylint: disable=too-many-arguments
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

    def check_updated_cardlist(self):
        """Check for cardlist updates if supported."""
        # Subclasses will implement this
        raise NotImplementedError("Implement check_updated_cardlist")
