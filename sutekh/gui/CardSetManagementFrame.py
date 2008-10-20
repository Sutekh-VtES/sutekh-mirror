# CardSetManagementFrame.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Window for Managing Physical and Abstract Card Sets
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Pane for a list of card sets"""

import gtk
from sutekh.core.SutekhObjects import PhysicalCardSet
from sutekh.gui.BasicFrame import BasicFrame
from sutekh.gui.CardSetManagementController import CardSetManagementController
from sutekh.gui.CardSetManagementMenu import CardSetManagementMenu
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow

class CardSetManagementFrame(BasicFrame):
    # pylint: disable-msg=R0904
    # gtk.Widget, so lots of public methods
    """Pane for the List of card sets.

       Provides the actions associated with this Pane - creating new
       card sets, filtering, etc.
       """
    _sFilterType = 'PhysicalCardSet'
    _sName = 'Card Set List'
    _oSetClass = PhysicalCardSet

    def __init__(self, oMainWindow):
        super(CardSetManagementFrame, self).__init__(oMainWindow)
        self._oMenu = None
        self._oController = CardSetManagementController(oMainWindow, self)
        self.set_name("card sets list")
        self.add_parts()

    # pylint: disable-msg=W0212
    # We allow access via these properties
    type = property(fget=lambda self: self._sName, doc="Frame Type")
    menu = property(fget=lambda self: self._oMenu, doc="Frame Menu")
    view = property(fget=lambda self: self._oController.view,
                        doc="Associated View Object")
    # pylint: enable-msg=W0212

    def add_parts(self):
        """Add a list object to the frame"""
        oMbox = gtk.VBox(False, 2)

        self.set_title(self._sName)
        oMbox.pack_start(self._oTitle, False, False)

        self._oMenu = CardSetManagementMenu(self, self._oMainWindow,
                self._oController)

        oMbox.pack_start(self._oMenu, False, False)

        oMbox.pack_start(AutoScrolledWindow(self._oController.view),
                expand=True)

        # setup default targets

        self.add(oMbox)
        self.show_all()

    def reload(self):
        """Reload the frame contents"""
        self._oController.reload_keep_expanded(True)
