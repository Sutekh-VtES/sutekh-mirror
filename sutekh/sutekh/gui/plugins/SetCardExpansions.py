# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Force all cards which can only belong to 1 expansion to that expansion"""

from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.base.gui.plugins.BaseSetExpansion import BaseSetExpansion


class SetCardExpansions(SutekhPlugin, BaseSetExpansion):
    """Set al the selected cards in the card list to a single expansion."""


plugin = SetCardExpansions
