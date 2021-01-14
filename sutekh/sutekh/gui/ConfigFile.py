# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Config handling object
# Wrapper around configobj and validate with some hooks for Sutekh purposes
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2010 Simon Cross <hodgestar+sutekh@gmail.com>
# License: GPL - See COPYRIGHT file for details

"""Configuration handling for the Sutekh GUI."""

import pkg_resources

from sutekh.base.gui.BaseConfigFile import BaseConfigFile
from sutekh.base.gui.MessageBus import MessageBus


class ConfigFile(BaseConfigFile):
    """Application overrides for the ConfigFile

       Provides application overrides and the default setup.
       """

    # pylint: disable=too-many-public-methods
    # Extends ConfigFile, which needs a lot of methods to manage
    # all the state

    DEFAULT_FILTERS = {
        "Default Filter Template": "(Clan in $var0) or (Discipline in $var1)"
                                   " or (CardType in $var2) or "
                                   "(CardFunction in $var3)",
        "Clan": "Clan in $var0",
        "Discipline": "Discipline in $var0",
        "Card Type": "CardType in $var0",
        "Card Text": "CardText in $var0",
        "Card Name": "CardName in $var0",
        "Card Set Name": "CardSetName in $var0",
        "Physical Expansion": "PhysicalExpansion in $var0",
    }

    def _get_app_configspec_file(self):
        """Get the application specific config file"""
        # pylint: disable=no-member
        # pkg_resources confuses pylint
        fConfigSpec = pkg_resources.resource_stream(__name__, "configspec.ini")
        return fConfigSpec

    def get_show_errata_markers(self):
        """Query the 'show errata markers' option."""
        return self._oConfig['main']['show errata markers']

    def set_show_errata_markers(self, bShowErrata):
        """Set the 'show errata markers' option."""
        self._oConfig['main']['show errata markers'] = bShowErrata
        MessageBus.publish(MessageBus.Type.CONFIG_MSG, 'show_errata_markers')

    def sanitize(self):
        """Called after validation to clean up a valid config.

           Currently clean-up consists of adding some open panes if none
           are listed.
           """
        if not self._oConfig['open_frames']:
            # No panes information, so we set 'sensible' defaults
            self.add_frame(1, 'physical_card', 'Full Card List', False,
                           False, -1, None)
            self.add_frame(2, 'Card Text', 'Card Text', False, False, -1, None)
            self.add_frame(3, 'Card Set List', 'Card Set List', False, False,
                           -1, None)
            self.add_frame(4, 'physical_card_set', 'My Collection', False,
                           False, -1, None)
        # Remove the old 'last cardlist update' setting from the config file
        if 'last cardlist update' in self._oConfig['main']:
            # We don't test this since this is for old config files
            # pylint: disable: line-too-long
            # formatting this to fit the line length doesn't improve clarity
            self._oConfig['main'].pop('last cardlist update')  # pragma: no cover
