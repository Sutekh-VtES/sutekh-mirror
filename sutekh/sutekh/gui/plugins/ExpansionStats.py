# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2010 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for analysing all expansions and reporting the number of cards
   of each rarity."""

from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.base.gui.plugins.BaseExpansionStats import BaseExpansionStats
from sutekh.core.Groupings import ExpansionRarityGrouping


class ExpansionStats(SutekhPlugin, BaseExpansionStats):
    """Display card counts and stats for each expansion, rarity grouping."""

    GROUPING = ExpansionRarityGrouping


plugin = ExpansionStats
