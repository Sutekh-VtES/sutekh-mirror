# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>,
# GPL - see COPYING for details

"""plugin for managing CSV file imports"""

from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.base.gui.plugins.BaseCSVImport import BaseCSVImport


class CSVImporter(SutekhPlugin, BaseCSVImport):
    """CSV Import plugin."""


plugin = CSVImporter
