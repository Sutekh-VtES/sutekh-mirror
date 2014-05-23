# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Converts a filter into a card set"""

from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.base.gui.plugins.BaseFromFilter import BaseFromFilter


class CardSetFromFilter(SutekhPlugin, BaseFromFilter):
    """Converts a filter into a Card Set."""


plugin = CardSetFromFilter
