# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Plugin for exporting to CSV format"""

from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.base.gui.plugins.BaseExportCSV import BaseExportCSV


class CardSetExportCSV(SutekhPlugin, BaseExportCSV):
    """Sutekh wrapper for CSV Export plugin."""


plugin = CardSetExportCSV
