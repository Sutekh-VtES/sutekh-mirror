# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Classes for managing and creating plugins for Sutekh."""

import sutekh.gui.plugins as plugins
from sutekh.base.gui.BasePluginManager import BasePluginManager, BasePlugin


class SutekhPlugin(BasePlugin):
    """Class for Sutekh plugins."""
    pass


class PluginManager(BasePluginManager):
    """Manages plugins for Sutekh."""

    cAppPlugin = SutekhPlugin
    sPluginDir = "sutekh.gui.plugins"

    def load_plugins(self):
        """Load list of Plugin Classes from plugin dir."""
        self._do_load_plugins(plugins)
