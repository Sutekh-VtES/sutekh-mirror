# SutekhIcon.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Provide a class for handling the application icon"""

# pylint: disable-msg=E0611
# pylint doesn't see resource_stream here, for some reason
from pkg_resources import resource_stream
# pylint: enable-msg=E0611
import gtk


class PkgIcon(object):
    """Load a gtk Pixbuf object from a package resource file."""

    def __init__(self, sPkg, sResource):
        oLoader = gtk.gdk.PixbufLoader()
        oFile = resource_stream(sPkg, sResource)
        oLoader.write(oFile.read())
        oFile.close()
        oLoader.close()
        self._oIcon = oLoader.get_pixbuf()

    def get_pixbuf(self):
        """Return the actual icon"""
        return self._oIcon

# pylint: disable-msg=C0103
# special case, so convention doesn't apply
SUTEKH_ICON = PkgIcon(__name__, "sutekh-icon.svg").get_pixbuf()
