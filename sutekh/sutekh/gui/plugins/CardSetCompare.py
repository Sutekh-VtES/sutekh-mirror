# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>,
# Copyright 2006, 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Sutekh wrapper for compare plugin."""

from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.base.gui.plugins.BaseCompare import BaseCompare


class CardSetCompare(SutekhPlugin, BaseCompare):
    """Compare Two Card Sets."""


plugin = CardSetCompare
