# AutoScrolledWindow.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk

class AutoScrolledWindow(gtk.ScrolledWindow, object):
    def __init__(self, wWidgetToWrap, bUseViewport=False):
        super(AutoScrolledWindow, self).__init__()

        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_IN)

        if bUseViewport:
            self.add_with_viewport(wWidgetToWrap)
        else:
            self.add(wWidgetToWrap)
