# PluginManager.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import plugins
import os
import glob
import logging
from sutekh.core.DatabaseVersion import DatabaseVersion

class PluginManager(object):
    """
    Plugin modules should be placed in the plugins package directory and contain an attribute
    named 'plugin' which points to the plugin class the module contains.
    """

    def __init__(self):
        self._aCardListPlugins = []

    def load_plugins(self):
        """
        Load list of Plugin Classes from plugin dir.
        """
        sPluginDir = os.path.dirname(plugins.__file__)

        for sPluginPath in glob.glob(os.path.join(sPluginDir, "*.py")):
            sPluginName = os.path.basename(sPluginPath)[:-len(".py")]

            if sPluginName == "__init__": continue

            # load module
            try:
                mPlugin = __import__("sutekh.gui.plugins." + sPluginName, None, None, [plugins])
            except ImportError, e:
                logging.warn("Failed to load plugin %s (%s)." % (sPluginName, str(e)))
                continue

            # find plugin class
            try:
                cPlugin = mPlugin.plugin
            except AttributeError, e:
                logging.warn("Plugin module %s appears not to contain a plugin (%s)." % (sPluginName, str(e)))
                continue

            # add to appropriate plugin lists
            if issubclass(cPlugin, CardListPlugin):
                self._aCardListPlugins.append(cPlugin)

    def get_card_list_plugins(self):
        return list(self._aCardListPlugins)

class CardListPlugin(object):
    """
    Base class for card list plugins.
    """
    dTableVersions = {}
    aModelsSupported = []

    def __init__(self, oCardListView, oCardListModel, cModelType=None):
        """
        oCardListModel - card list model for this plugin to operate on.
        """
        self._oView = oCardListView
        self._oModel = oCardListModel
        self._cModelType = cModelType

    parent = property(fget=lambda self: self._oView.getWindow(), doc="Parent window to use when creating dialogs.")
    view = property(fget=lambda self: self._oView, doc="Associated CardListView object.")
    model = property(fget=lambda self: self._oModel, doc="Associated CardModel object.")
    cardlookup = property(fget=lambda self: self.parent.cardLookup, doc="GUI CardLookup.")

    def get_menu_item(self):
        """
        Return a list of gtk.MenuItems for the plugin or None if 
        no menu item is needed.
        """
        return None

    def add_to_menu(self, dAllMenus, oCatchAllMenu):
        "Grunt work of adding menu item to the frame"
        aMenuItems = self.get_menu_item()
        if aMenuItems is not None:
            sMenu = self.get_desired_menu()
            # Add to the requested menu if supplied
            if not hasattr(aMenuItems, '__getitem__'):
                # Not an iterable object, so turn it into a list
                aMenuItems=[aMenuItems]
            for oMenuItem in aMenuItems:
                if sMenu in dAllMenus:
                    dAllMenus[sMenu].add(oMenuItem)
                else:
                    # Plugins acts as a catchall Menu
                    oCatchAllMenu.add(oMenuItem)

    def get_toolbar_widget(self):
        """
        Return an arbitary gtk.Widget which is added to a VBox between the menu
        and the scrolled display area. Return None is no toolbar Widget is needed
        """
        return None

    def get_desired_menu(self):
        """
        Return the name of the menu this plugin should be added to, or None
        if no menu item is needed.
        """
        return None

    def get_frame_from_config(self, sType):
        """
        Hook for plugins which supply a frame in the Main window.
        Allows them to restore from the config file properly
        """
        return None

    # Utility Functions / Plugin API

    def check_model_type(self):
        if self._cModelType in self.aModelsSupported:
            return True
        return False

    def check_versions(self):
        oDBVer = DatabaseVersion()
        for sTableName, aVersions in self.dTableVersions.iteritems():
            iCurVer = oDBVer.getVersion(sTableName)
            if iCurVer not in aVersions:
                return False
        # If nothing is specified, currently we assume everything is A-OK
        return True

    def open_acs(self, sACS):
        """
        Open an abstract card set in the GUI.
        """
        oF = self.parent.add_pane()
        self.parent.replace_with_abstract_card_set(sACS, oF)

    def open_pcs(self, sPCS):
        """
        Open a physical card set in the GUI.
        """
        oF = self.parent.add_pane()
        self.parent.replace_with_physical_card_set(sPCS, oF)

    def reload_acs_list(self):
        """
        Refresh the abstract card set list if it is visible.
        """
        self.parent.reload_acs_list()

    def reload_pcs_list(self):
        """
        Refresh the physical card set list if it is visible.
        """
        self.parent.reload_pcs_list()

    def reload_all(self):
        """
        Reload all views.
        """
        self.parent.reload_all()
