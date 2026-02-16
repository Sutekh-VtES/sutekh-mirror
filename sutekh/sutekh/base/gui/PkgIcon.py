# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Provide a base class for handling the application icon"""

import importlib.resources

from gi.repository import GdkPixbuf


class PkgIcon:
    """Load a Gtk Pixbuf object from a package resource file."""

    def __init__(self, sPkg, sResource):
        oLoader = GdkPixbuf.PixbufLoader.new_with_type('svg')
        oFile = importlib.resources.open_binary(sPkg, sResource)
        oLoader.write(oFile.read())
        oFile.close()
        oLoader.close()
        self._oIcon = oLoader.get_pixbuf()

    def get_pixbuf(self):
        """Return the actual icon"""
        return self._oIcon
