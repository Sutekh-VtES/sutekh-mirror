# SutekhIcon.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

from pkg_resources import resource_stream
import gtk

class PkgIcon(object):
    """Load a gtk Pixbuf object from a package resource file."""

    def __init__(self,sPkg,sResource):
        oLoader = gtk.gdk.PixbufLoader()
        oFile = resource_stream(sPkg,sResource)
        oLoader.write(oFile.read())
        oFile.close()
        oLoader.close()
        self._oIcon = oLoader.get_pixbuf()

    def get_pixbuf(self):
        return self._oIcon

SUTEKH_ICON = PkgIcon(__name__,"sutekh-icon.svg").get_pixbuf()
