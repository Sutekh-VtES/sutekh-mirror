# AutoScrolledWindow.py
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

import gtk

class AutoScrolledWindow(gtk.ScrolledWindow,object):
    def __init__(self,wWidgetToWrap):
        super(AutoScrolledWindow,self).__init__()
        
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.set_shadow_type(gtk.SHADOW_IN)
   
        self.add(wWidgetToWrap)
