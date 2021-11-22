# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Adds an option to hide the (Group X) suffix when it doesn't cause confusion."""

from gi.repository import Gtk

from sutekh.base.gui.CardListModel import NameTransformer
from sutekh.base.gui.MessageBus import MessageBus
from sutekh.base.core.BaseTables import (PhysicalCardSet, PhysicalCard,
                                         AbstractCard)

from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.core.SutekhTables import CRYPT_TYPES
from sutekh.SutekhUtility import strip_group_from_name, is_crypt_card



class SuffixTransformer(NameTransformer):

    CONFIG_KEY = 'hide group suffix'

    def __init__(self, oConfig, **kwargs):
        super().__init__(oConfig, **kwargs)
        self._oPlugin = kwargs.pop('oPlugin')
        self.bHideGroup = self._oPlugin.get_config_item(self.CONFIG_KEY)
        self._aStrippable = set()
        # Load the cache
        self.database_updated()

    def database_updated(self):
        self._dNameCache = {}
        self._aStrippable = set()
        dCount = {}

        for oCard in AbstractCard.select():
            if not is_crypt_card(oCard):
                continue
            sStrippedName = strip_group_from_name(oCard.name)
            dCount.setdefault(sStrippedName, [0, None])
            dCount[sStrippedName][0] += 1
            dCount[sStrippedName][1] = oCard

        # We only add the lookup if it's unique
        for sName, (iCnt, oCard) in dCount.items():
            if iCnt == 1:
                if '(Advanced)' not in sName:
                    self._aStrippable.add(oCard)
                else:
                    # For advanced vampires, we also need to check if the
                    # non-advanced version is unique
                    sNonAdv = sName.replace(' (Advanced)', '')
                    if sNonAdv not in dCount:
                        # Can happen with reduced testing cardlists / playtest cards / etc.
                        self._aStrippable.add(oCard)
                    elif dCount[sNonAdv][0] == 1:
                        self._aStrippable.add(oCard)

    def config_changed(self, oConfig):
        self.bHideGroup = self._oPlugin.get_config_item(self.CONFIG_KEY)

    def transform(self, sCardName, oAbsCard):
        if self.bHideGroup:
            if oAbsCard in self._aStrippable:
                # Because the name might be changed by another transfrom,
                # we need to call strip_group on the current text
                return strip_group_from_name(sCardName)
        return sCardName


class HideGroupSuffixPlugin(SutekhPlugin):
    """Plugin to hide the suffix, available via the perferences menu."""
    # We do this as a plugin to keep logic all in one place.

    aModelsSupported = ("MainWindow", PhysicalCardSet, PhysicalCard)

    dGlobalConfig = {
        SuffixTransformer.CONFIG_KEY : 'boolean(default=False)',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only try register on the actual card set frames
        if self.model:
            self.model.register_transformer(SuffixTransformer, oPlugin=self)

    def get_menu_item(self):
        """Overrides method from base class.

           Adds the menu item on the MainWindow.
           """
        if self.model is None:
            # On main window
            oConfigMenuItem = Gtk.CheckMenuItem(label="Hide group suffix on names")
            oConfigMenuItem.connect("activate", self.config_activate)
            oConfigMenuItem.set_active(self.get_config_item(SuffixTransformer.CONFIG_KEY))
            return ('Preferences', oConfigMenuItem)
        return None

    def config_activate(self, oMenuWidget):
        """Launch the configuration dialog."""
        bValue = oMenuWidget.get_active()
        self.set_config_item(SuffixTransformer.CONFIG_KEY, bValue)
        MessageBus.publish(MessageBus.Type.CONFIG_MSG, SuffixTransformer.CONFIG_KEY, bValue)


plugin = HideGroupSuffixPlugin
