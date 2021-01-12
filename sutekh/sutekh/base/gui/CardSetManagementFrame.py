# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Window for Managing Physical and Abstract Card Sets
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Pane for a list of card sets"""

from gi.repository import Gtk
from ..core.BaseTables import PhysicalCardSet
from .BasicFrame import BasicFrame, pack_resizable
from .CardSetManagementController import CardSetManagementController
from .CardSetManagementMenu import CardSetManagementMenu
from .AutoScrolledWindow import AutoScrolledWindow


class CardSetManagementFrame(BasicFrame):
    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods
    """Pane for the List of card sets.

       Provides the actions associated with this Pane - creating new
       card sets, filtering, etc.
       """
    _sName = 'Card Set List'
    _oSetClass = PhysicalCardSet

    _cModelType = "Card Set List"

    def __init__(self, oMainWindow):
        super().__init__(oMainWindow)
        self._oMenu = None
        self._oScrolledWindow = None
        self._oController = CardSetManagementController(oMainWindow, self)
        self.set_name("card sets list")

        self.init_plugins()
        self._oMenu = CardSetManagementMenu(self, self._oMainWindow,
                                            self._oController)

        self.add_parts()

    # pylint: disable=protected-access
    # We allow access via these properties
    type = property(fget=lambda self: self._sName, doc="Frame Type")
    menu = property(fget=lambda self: self._oMenu, doc="Frame Menu")
    view = property(fget=lambda self: self._oController.view,
                    doc="Associated View Object")
    # pylint: enable=protected-access

    def add_parts(self):
        """Add a list object to the frame"""
        oMbox = Gtk.VBox(homogeneous=False, spacing=2)

        self.set_title(self._sName)
        pack_resizable(oMbox, self._oTitle)
        pack_resizable(oMbox, self._oMenu)

        self._oScrolledWindow = AutoScrolledWindow(self._oController.view)
        oMbox.pack_start(self._oScrolledWindow, True, True, 0)

        # setup default targets

        self.add(oMbox)
        self.show_all()

        self.set_drag_handler(self._oMenu)
        self.set_drop_handler(self._oMenu)

    def reload(self):
        """Reload the frame contents"""
        # get the scroll widget position
        oVertAdj = self._oScrolledWindow.get_vadjustment()
        oHorzAdj = self._oScrolledWindow.get_hadjustment()
        tVertVals = oVertAdj.get_value(), oVertAdj.get_page_size()
        tHorzVals = oHorzAdj.get_value(), oHorzAdj.get_page_size()
        self.view.reload_keep_expanded(True)
        oVertAdj.set_value(tVertVals[0])
        oVertAdj.set_page_size(tVertVals[1])
        oHorzAdj.set_value(tHorzVals[0])
        oHorzAdj.set_page_size(tHorzVals[1])

    def get_menu_name(self):
        """Get the menu key"""
        return self._sName
