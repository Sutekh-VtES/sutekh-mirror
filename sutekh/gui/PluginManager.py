# PluginManager.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Classes for mangaging and creating plugins for Sutekh."""

import os
import glob
import logging
import sutekh.gui.plugins as plugins
import zipimport
import zipfile
import re
from sutekh.core.DatabaseVersion import DatabaseVersion
from sutekh.core.SutekhObjects import PhysicalCardSet

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
                oM = oModRe.match(sFile)
                if oM and oM.group('mod') != '__init__':
                    aModules.add(oM.group('mod'))
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
        self._aCardListPlugins = []

    def load_plugins(self, bVerbose):
        """Load list of Plugin Classes from plugin dir."""
        for sPluginName in submodules(plugins):
            # load module
            # pylint: disable-msg=C0103
            # mPlugin is legal name here
            try:
                mPlugin = __import__("sutekh.gui.plugins.%s" % sPluginName,
                        None, None, [plugins])
            except ImportError, oExp:
                if bVerbose:
                    logging.warn("Failed to load plugin %s (%s)." % (
                        sPluginName, oExp))
                continue

            # find plugin class
            try:
                cPlugin = mPlugin.plugin
            except AttributeError, oExp:
                if bVerbose:
                    logging.warn("Plugin module %s appears not to contain a"
                            " plugin (%s)." % (sPluginName, oExp))
                continue

            # add to appropriate plugin lists
            if issubclass(cPlugin, CardListPlugin):
                self._aCardListPlugins.append(cPlugin)

    def get_card_list_plugins(self):
        """Get all the plugins loaded"""
        return list(self._aCardListPlugins)

class CardListPlugin(object):
    """Base class for card list plugins."""
    dTableVersions = {}
    aModelsSupported = []

    def __init__(self, oCardListView, oCardListModel, cModelType=None):
        """oCardListModel - card list model for this plugin to operate on."""
        self._oView = oCardListView
        self._oModel = oCardListModel
        self._cModelType = cModelType

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
    # pylint: enable-msg=W0212

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

    def get_toolbar_widget(self):
        """Return an arbitary gtk.Widget which is added to a VBox between the
           menu and the scrolled display area.

           Return None is no toolbar Widget is needed
           """
        return None

    # pylint: disable-msg=W0613
    # sType can be used by children of this class
    def get_frame_from_config(self, sType):
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

    def open_cs(self, sPCS):
        """Open a physical card set in the GUI."""
        self.parent.add_new_physical_card_set(sPCS)

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

