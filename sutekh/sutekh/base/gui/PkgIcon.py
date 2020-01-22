# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Provide a base class for handling the application icon"""

# pylint: disable=no-name-in-module
# pylint doesn't see resource_stream here, for some reason
from pkg_resources import resource_stream
# pylint: enable=no-name-in-module
import gtk


class PkgIcon:
    """Load a gtk Pixbuf object from a package resource file."""

    def __init__(self, sPkg, sResource):
        # FIXME: Work out how to get back to a generic loader after we move away from needing pygtkcompat
        oLoader = gtk.gdk.PixbufLoader('svg')
        oFile = resource_stream(sPkg, sResource)
        oLoader.write(oFile.read())
        oFile.close()
        oLoader.close()
        self._oIcon = oLoader.get_pixbuf()

    def get_pixbuf(self):
        """Return the actual icon"""
        return self._oIcon
