# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
"""Plugin to import selected card sets from a zip file"""

from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.io.ZipFileWrapper import ZipFileWrapper
from sutekh.base.gui.plugins.BaseZipImport import BaseZipImport


class ImportFromZipFile(SutekhPlugin, BaseZipImport):
    """Extract selected card sets from a zip file."""

    cZipWrapper = ZipFileWrapper


plugin = ImportFromZipFile
