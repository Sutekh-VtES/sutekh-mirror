# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details
"""Plugin to wrap zipfile backup and restore methods"""

from sutekh.gui.PluginManager import SutekhPlugin
from sutekh.base.gui.plugins.BaseBackup import BaseBackup
from sutekh.io.ZipFileWrapper import ZipFileWrapper


class FullBackup(SutekhPlugin, BaseBackup):
    """Provide access to ZipFileWrapper's backup and restore methods."""
    cZipWrapper = ZipFileWrapper


plugin = FullBackup
