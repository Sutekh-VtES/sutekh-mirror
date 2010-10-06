# AutoScrolledWindow.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Utility wrapper around gtk.ScrolledWindow"""

import gtk


class AutoScrolledWindow(gtk.ScrolledWindow):
    # pylint: disable-msg=R0904
    # gtk widget, so many public methods
    """Wrap a widget in a gtk.ScrolledWindow.

       Set the Scrollbar property to Autmoatic, so scrollbars only so up
       when needed. The widget can also be wrapped in a viewport if needed
       """
    def __init__(self, oWidgetToWrap, bUseViewport=False):
        super(AutoScrolledWindow, self).__init__()

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_IN)

        if bUseViewport:
            self.add_with_viewport(oWidgetToWrap)
        else:
            self.add(oWidgetToWrap)
