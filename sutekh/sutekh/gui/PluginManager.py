# PluginManager.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import plugins
import os
import glob
import logging
from sutekh.DatabaseVersion import DatabaseVersion

class PluginManager(object):
    """
    Plugin modules should be placed in the plugins package directory and contain an attribute
    named 'plugin' which points to the plugin class the module contains.
    """

    def __init__(self):
        self._aCardListPlugins = []

    def loadPlugins(self):
        """
        Load list of Plugin Classes from plugin dir.
        """
        sPluginDir = os.path.dirname(plugins.__file__)

        for sPluginPath in glob.glob(os.path.join(sPluginDir,"*.py")):
            sPluginName = os.path.basename(sPluginPath)[:-len(".py")]

            if sPluginName == "__init__": continue

            # load module
            try:
                mPlugin = __import__("gui.plugins." + sPluginName,None,None,[plugins])
            except ImportError, e:
                logging.warn("Failed to load plugin %s (%s)." % (sPluginName,str(e)))
                continue

            # find plugin class
            try:
                cPlugin = mPlugin.plugin
            except AttributeError, e:
                logging.warn("Plugin module %s appears not to contain a plugin (%s)." % (sPluginName,str(e)))
                continue

            # add to appropriate plugin lists
            if issubclass(cPlugin,CardListPlugin):
                self._aCardListPlugins.append(cPlugin)

    def getCardListPlugins(self):
        return list(self._aCardListPlugins)

class CardListPlugin(object):
    """
    Base class for card list plugins.
    """
    dTableVersions = {}
    aModelsSupported = []

    def __init__(self,oCardListView,oCardListModel,sModelType='Unknown'):
        """
        oCardListModel - card list model for this plugin to operate on.
        """
        self._oView = oCardListView
        self._oModel = oCardListModel
        self._sModelType = sModelType

    view = property(fget=lambda self: self._oView,doc="Associated CardListView object.")
    model = property(fget=lambda self: self._oModel,doc="Associated CardModel object.")

    def getMenuItem(self):
        """
        Return a gtk.MenuItem for the plugin or None if no menu item is needed.
        """
        return None

    def getToolbarWidget(self):
        """
        Return an arbitary gtk.Widget which is added to a VBox between the menu
        and the scrolled display area. Return None is no toolbar Widget is needed
        """
        return None

    def getDesiredMenu(self):
        """
        Return the name of the menu this plugin should be added to, or None
        if no menu item is needed.
        """
        return None

    def checkModelType(self):
        if self._sModelType in self.aModelsSupported:
            return True
        return False

    def checkVersions(self):
        oDBVer = DatabaseVersion()
        for oTableName,aVersions in self.dTableVersions.iteritems():
            iCurVer=oDBVer.getVersion(oTableName)
            if iCurVer not in aVersions:
                return False
        # If nothing is specified, currently we assume everything is A-OK
        return True
