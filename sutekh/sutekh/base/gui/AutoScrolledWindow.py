# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Utility wrapper around Gtk.ScrolledWindow"""

from gi.repository import Gtk


class AutoScrolledWindow(Gtk.ScrolledWindow):
    # pylint: disable=too-many-public-methods
    # Gtk widget, so many public methods
    """Wrap a widget in a Gtk.ScrolledWindow.

       Set the Scrollbar property to Autmoatic, so scrollbars only so up
       when needed. The widget can also be wrapped in a viewport if needed
       """
    def __init__(self, oWidgetToWrap):
        super().__init__()

        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.set_shadow_type(Gtk.ShadowType.IN)

        self.add(oWidgetToWrap)
