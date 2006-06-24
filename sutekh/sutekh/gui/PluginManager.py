# PluginManager.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import plugins
import os
import glob
import logging

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
    def __init__(self,oCardListView,oCardListModel):
        """
        oCardListModel - card list model for this plugin to operate on.
        """
        self._oView = oCardListView
        self._oModel = oCardListModel

    view = property(fget=lambda self: self._oView,doc="Associated CardListView object.")
    model = property(fget=lambda self: self._oModel,doc="Associated CardModel object.")

    def getMenuItem(self):
        """
        Return a gtk.MenuItem for the plugin or None if no menu item is need.
        """
        return None
