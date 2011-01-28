# PluginManager.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Classes for managing and creating plugins for Sutekh."""

import os
import glob
import logging
import sutekh.gui.plugins as plugins
from gobject import markup_escape_text
import gtk
import zipimport
import zipfile
import re
from sutekh.core.DatabaseVersion import DatabaseVersion
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.gui.ConfigFile import ConfigFileListener, CARDSET, WW_CARDLIST, \
        CARDSET_LIST, FRAME
from sutekh.gui.SutekhDialog import do_complaint_warning


def submodules(oPackage):
    """List all the submodules in a package."""
    oLoader = getattr(oPackage, "__loader__", None)
    aModules = set()

    if type(oLoader) is zipimport.zipimporter:
        # look inside the zip
        oPackageZip = zipfile.ZipFile(oLoader.archive)
        sPrefix = "/".join(oPackage.__name__.split('.')) + "/"
        oModRe = re.compile(r"(?P<mod>[^/]*)\.py[^/]*")

        for sFile in oPackageZip.namelist():
            if sFile.startswith(sPrefix):
                sFile = sFile[len(sPrefix):]
                oMatch = oModRe.match(sFile)
                if oMatch and oMatch.group('mod') != '__init__':
                    aModules.add(oMatch.group('mod'))
    else:
        # try the filesystem
        sPackageDir = os.path.dirname(oPackage.__file__)
        for sModuleFile in glob.glob(os.path.join(sPackageDir, "*.py*")):
            sModule = os.path.basename(sModuleFile)
            sModule = os.path.splitext(sModule)[0]
            if sModule != "__init__":
                aModules.add(sModule)

    return list(aModules)


class PluginManager(object):
    """Manages plugins for Sutekh

       Plugin modules should be placed in the plugins package directory and
       contain an attribute named 'plugin' which points to the plugin class the
       module contains.
       """

    def __init__(self):
        self._aPlugins = []

    def load_plugins(self):
        """Load list of Plugin Classes from plugin dir."""
        for sPluginName in submodules(plugins):
            # load module
            # pylint: disable-msg=C0103
            # mPlugin is legal name here
            try:
                mPlugin = __import__("sutekh.gui.plugins.%s" % sPluginName,
                        None, None, [plugins])
            except ImportError, oExp:
                logging.warn("Failed to load plugin %s (%s).",
                        sPluginName, oExp, exc_info=1)
                continue

            # find plugin class
            try:
                cPlugin = mPlugin.plugin
            except AttributeError, oExp:
                logging.warn("Plugin module %s appears not to contain a"
                        " plugin (%s).", sPluginName, oExp, exc_info=1)
                continue

            # add to appropriate plugin lists
            if issubclass(cPlugin, SutekhPlugin):
                self._aPlugins.append(cPlugin)

    def get_card_list_plugins(self):
        """Get all the plugins loaded"""
        return list(self._aPlugins)


class PluginConfigFileListener(ConfigFileListener):
    """ConfigListener tailored to inform plugins when their config changes."""

    # pylint: disable-msg=W0231
    # no point in calling __init__, since it doesn't exist
    def __init__(self, oPlugin):
        self._oPlugin = oPlugin

    def profile_option_changed(self, sType, sProfile, sKey):
        """One of the per-deck configuration items changed."""
        if sType == CARDSET or sType == FRAME:
            dConfig = self._oPlugin.dPerPaneConfig
        elif sType == WW_CARDLIST:
            dConfig = self._oPlugin.dCardListConfig
        elif sType == CARDSET_LIST:
            dConfig = self._oPlugin.dCardSetListConfig
        else:
            dConfig = {}
        if sKey in dConfig:
            oConfig = self._oPlugin.config
            if sType == CARDSET or sType == FRAME:
                # Handle the cardset_profile, frame_profile case
                tProfiles = (
                        oConfig.get_profile(FRAME,
                            self._oPlugin.model.frame_id),
                        oConfig.get_profile(CARDSET,
                            self._oPlugin.model.cardset_id),
                        )
            else:
                tProfiles = (oConfig.get_profile(sType,
                    self._oPlugin.model.cardset_id),)
            if sProfile in tProfiles:
                self._oPlugin.perpane_config_updated()

    def profile_changed(self, sType, sId):
        """The profile associated with a frame changed."""
        if sType == FRAME and self._oPlugin.model.frame_id == sId:
            self._oPlugin.perpane_config_updated()
        elif sType in (CARDSET, WW_CARDLIST, CARDSET_LIST) and \
                self._oPlugin.model.cardset_id == sId:
            self._oPlugin.perpane_config_updated()


class SutekhPlugin(object):
    """Base class for card list plugins."""
    dTableVersions = {}
    aModelsSupported = ()

    # ConfigObj validation specs as dictionaries
    dGlobalConfig = {}
    dPerPaneConfig = {}
    dCardListConfig = {}
    dCardSetListConfig = {}

    def __init__(self, oCardListView, oCardListModel, cModelType=None):
        """oCardListModel - card list model for this plugin to operate on."""
        self._oView = oCardListView
        self._oModel = oCardListModel
        self._cModelType = cModelType
        self._oListener = None
        if self._oModel is not None and hasattr(self._oModel, "frame_id"):
            self._oListener = PluginConfigFileListener(self)
            # listener automatically removed when plugin is garbage collected
            # since the config only maintains a weakref to it.
            self.config.add_listener(self._oListener)

    # pylint: disable-msg=W0212
    # we allow access to the members via these properties
    parent = property(fget=lambda self: self._oView.mainwindow,
            doc="Parent window to use when creating dialogs.")
    view = property(fget=lambda self: self._oView,
            doc="Associated CardListView object.")
    model = property(fget=lambda self: self._oModel,
            doc="Associated CardModel object.")
    cardlookup = property(fget=lambda self: self.parent.cardLookup,
            doc="GUI CardLookup.")
    icon_manager = property(fget=lambda self: self.parent.icon_manager,
            doc="Icon manager.")
    config = property(fget=lambda self: self._oView.mainwindow.config_file,
            doc="Configuration object.")
    # pylint: enable-msg=W0212

    @classmethod
    def register_with_config(cls, oConfig):
        """Register this config class with the given config."""
        oConfig.add_plugin_specs(cls.__name__, cls.dGlobalConfig)
        oConfig.add_deck_specs(cls.__name__, cls.dPerPaneConfig)
        oConfig.add_cardlist_specs(cls.__name__, cls.dCardListConfig)
        oConfig.add_cardset_list_specs(cls.__name__, cls.dCardSetListConfig)

    def add_to_menu(self, dAllMenus, oCatchAllMenu):
        """Grunt work of adding menu item to the frame"""
        aMenuItems = self.get_menu_item()
        if aMenuItems is not None:
            if not isinstance(aMenuItems, list):
                if not isinstance(aMenuItems, tuple):
                    # Just straight menu item
                    aMenuItems = [('Plugins', aMenuItems)]
                else:
                    # Wrap tuple in a list
                    aMenuItems = [aMenuItems]
            for sMenu, oMenuItem in aMenuItems:
                if sMenu in dAllMenus:
                    dAllMenus[sMenu].add(oMenuItem)
                else:
                    # Plugins acts as a catchall Menu
                    oCatchAllMenu.add(oMenuItem)

    # pylint: disable-msg=R0201
    # We expect children to override these when needed
    def get_menu_item(self):
        """Return a list of ('Menu', gtk.MenuItems) pairs for the plugin or
           None if no menu item is needed."""
        return None

    def setup(self):
        """Handle any setup needed for the plugin after the main window has
           been initialised.

           Currently used to prompt for downloads, etc.
           """
        return None

    def cleanup(self):
        """Handle any cleanup needed by the plugin when the window or
           pane it's attached to goes away.

           Used for things like database signal cleanup, etc."""
        if self._oListener:
            self.config.remove_listener(self._oListener)
            self._oListener = None
        return None

    def get_toolbar_widget(self):
        """Return an arbitary gtk.Widget which is added to a VBox between the
           menu and the scrolled display area.

           Return None is no toolbar Widget is needed
           """
        return None

    def get_frame_from_config(self, _sType):
        """Hook for plugins which supply a frame in the Main window.

           Allows them to restore from the config file properly.
           """
        return None

    # pylint: enable-msg=R0201

    # Utility Functions / Plugin API

    def check_model_type(self):
        """Check whether the plugin should register on this frame."""
        if self._cModelType in self.aModelsSupported:
            return True
        return False

    def check_versions(self):
        """Check whether the plugin supports the current version of
           the Sutekh database tables."""
        oDBVer = DatabaseVersion()
        for oTable, aVersions in self.dTableVersions.iteritems():
            if not oDBVer.check_table_in_versions(oTable, aVersions):
                return False
        # If nothing is specified, currently we assume everything is A-OK
        return True

    def open_cs(self, sPCS, bStartEditable=False):
        """Open a physical card set in the GUI."""
        self.parent.add_new_physical_card_set(sPCS, bStartEditable)

    def reload_pcs_list(self):
        """Refresh the physical card set list if it is visible."""
        self.parent.reload_pcs_list()

    def reload_all(self):
        """Reload all views."""
        self.parent.reload_all()

    def get_card_set(self):
        """Get the Card Set for this view."""
        oCardSet = None
        if self._cModelType is PhysicalCardSet:
            # pylint: disable-msg=E1101
            # sqlobject confuses pylint
            oCardSet = PhysicalCardSet.byName(self.view.sSetName)
        return oCardSet

    def get_all_cards(self):
        """Get the cards from the card set."""
        if self._cModelType is PhysicalCardSet:
            return self.model.get_card_iterator(None)
        return []

    def check_cs_size(self, sName, iLimit):
        """Check that the card set isn't considerably larger than we
           expect to deal with and warn the user if it is"""
        iCards = 0
        aCards = self.get_all_cards()
        if aCards:
            iCards = aCards.count()
        if iCards > iLimit:
            iRes = do_complaint_warning("This card set is very large"
                    " (%d cards), and so using the %s plugin doesn't seem"
                    " sensible.\nAre you sure you want to continue?" %
                    (iCards, sName))
            if iRes == gtk.RESPONSE_CANCEL:
                return False  # fail
        return True  # A-OK

    def get_config_item(self, sKey):
        """Return the value of a plugin global config key."""
        return self.config.get_plugin_key(self.__class__.__name__, sKey)

    def set_config_item(self, sKey, sValue):
        """Set the value of a plugin global config key."""
        self.config.set_plugin_key(self.__class__.__name__, sKey, sValue)

    def get_perpane_item(self, sKey):
        """Return the value of a per-pane config key."""
        oModel = self.model
        if oModel is None or not hasattr(oModel, "cardset_id"):
            return None
        if oModel.cardset_id == WW_CARDLIST or \
                oModel.cardset_id == CARDSET_LIST:
            sProfile = self.config.get_profile(oModel.cardset_id,
                    oModel.cardset_id)
            return self.config.get_profile_option(oModel.cardset_id,
                    sProfile, sKey)
        return self.config.get_deck_option(oModel.frame_id, oModel.cardset_id,
            sKey)

    def perpane_config_updated(self, bDoReload=True):
        """Plugins should override this to be informed of config changes."""
        pass

    # pylint: disable-msg=R0201
    # utilty function for plugins
    def escape(self, sInput):
        """Escape strings so that markup and special characters don't break
           things."""
        if sInput:
            return markup_escape_text(sInput)
        else:
            return sInput  # pass None straight through
