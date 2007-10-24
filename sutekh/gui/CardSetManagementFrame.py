# CardSetManagementFrame.py
# Window for Managing Physical and Abstract Card Sets
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sqlobject.events import listen
from sutekh.core.SutekhObjects import AbstractCardSet, PhysicalCardSet
from sutekh.core.Filters import NullFilter
from sutekh.gui.ScrolledList import ScrolledList
from sutekh.gui.FilterDialog import FilterDialog
from sutekh.gui.SQLObjectEvents import RowDestroySignal, RowUpdateSignal, \
        RowCreatedSignal, CardSetOpenedSignal, CardSetClosedSignal

class CardSetManagementFrame(gtk.Frame, object):
    def __init__(self, oMainWindow, oConfig):
        super(CardSetManagementFrame, self).__init__()
        self._oMainWin = oMainWindow
        self._oConfig = oConfig
        self._sSetType = None
        self._sName = 'Card Set List'
        self._oView = None
        self._dOpenCardSets = {}
        self._oMenu = gtk.MenuBar()
        self._oFilter = NullFilter()
        self._oFilterDialog = None
        self._sFilterType = None
        iMenu = gtk.MenuItem('Filter')
        wMenu = gtk.Menu()
        iMenu.set_submenu(wMenu)
        iFilter = gtk.MenuItem('Specify Filter')
        wMenu.add(iFilter)
        iFilter.connect('activate', self.set_filter)
        self.iApply = gtk.CheckMenuItem('Apply Filter')
        self.iApply.set_inconsistent(False)
        self.iApply.set_active(False)
        wMenu.add(self.iApply)
        self.iApply.connect('toggled', self.toggle_apply)
        self._oMenu.add(iMenu)

    name = property(fget=lambda self: self._sName, doc="Frame Name")
    view = property(fget=lambda self: self._oView, doc="Associated View Object")
    open_card_sets = property(fget=lambda self: self._dOpenCardSets,
            doc="Dictionary of currently open card sets")
    type = property(fget=lambda self: self._sName, doc="Frame Type")
    menu = property(fget=lambda self: self._oMenu, doc="Frame Menu")

    def cleanup(self):
        pass

    def add_parts(self):
        """Add a list object to the frame"""
        wMbox = gtk.VBox(False, 2)

        wMbox.pack_start(self._oMenu, False, False)

        self._oScrolledList = ScrolledList(self._sName,'')
        self._oView = self._oScrolledList.TreeView
        self._oScrolledList.set_select_single()
        self._oView.connect('row_activated',self.row_clicked)
        self.reload_card_set_list()
        wMbox.pack_start(self._oScrolledList, expand=True)
        self.add(wMbox)
        self.show_all()
        listen(self.listenOpened, self._oSetClass, CardSetOpenedSignal)
        listen(self.listenClosed, self._oSetClass, CardSetClosedSignal)
        listen(self.listenChanged, self._oSetClass, RowUpdateSignal)
        listen(self.listenDestroy, self._oSetClass, RowDestroySignal)
        listen(self.listenCreated, self._oSetClass, RowCreatedSignal)

    def listenOpened(self, sSetName):
        self.reload_card_set_list()

    def listenClosed(self, sSetName):
        self.reload_card_set_list()

    def listenChanged(self, args, **kw):
        print "Changed signal", args
        print "kw", kw

    def listenDestroy(self, kw):
        print "Destroy", kw

    def listenCreated(self, args, **kw):
        print "Created",args
        print "kw", kw

    def reload_card_set_list(self):
        oThisList = self._oScrolledList.get_list()
        oThisList.clear()
        self._oOpenIter=oThisList.append(None)
        oThisList.set(self._oOpenIter,0, '<b>Opened</b>')
        self._oAvailIter=oThisList.append(None)
        oThisList.set(self._oAvailIter,0,'<b>Available</b>')
        if self.iApply.active:
            oSelectFilter = self._oFilter
        else:
            oSelectFilter = NullFilter()
        for oCS in oSelectFilter.select(self._oSetClass).orderBy('name'):
            if oCS.name not in self._dOpenCardSets.keys():
                iter = oThisList.append(None)
            else:
                iter = oThisList.insert_before(self._oAvailIter)
            oThisList.set(iter,0,oCS.name)

    def set_filter(self, oWidget):
        if self._oFilterDialog is None:
            self._oFilterDialog = FilterDialog(self._oMainWin, self._oConfig, self._sFilterType)

        self._oFilterDialog.run()

        if self._oFilterDialog.Cancelled():
            return # Change nothing

        oFilter = self._oFilterDialog.getFilter()
        if oFilter != None:
            self._oFilter = oFilter
            if self.iApply.active:
                self.reload_card_set_list()
            else:
                # Let toggle reload for us
                self.set_apply_filter(True)
        else:
            self._oFilter = NullFilter()
            # Filter is set to blank, so we treat this as disabling
            # Filter
            if not self.iApply.active:
                self.reload_card_set_list()
            else:
                # Let toggle reload for us
                self.set_apply_filter(False)

    def set_apply_filter(self, bState):
        self.iApply.set_active(bState)

    def toggle_apply(self, oWidget):
        self.reload_card_set_list()

    def row_clicked(self, oTreeView, oPath, oColumn):
        oM = oTreeView.get_model()
        # We are pointing to a ListStore, so the iters should always be valid
        # Need to dereference to the actual path though, as iters not unique
        if oPath == oM.get_path(self._oOpenIter) or \
                oPath == oM.get_path(self._oAvailIter):
           return
        oIter = oM.get_iter(oPath)
        sName = oM.get_value(oIter,0)
        if self._sSetType == 'Physical Card Set':
            self._oMainWin.add_physical_card_set(sName)
        elif self._sSetType == 'Abstract Card Set':
            self._oMainWin.add_abstract_card_set(sName)

class PhysicalCardSetListFrame(CardSetManagementFrame):
    def __init__(self, oMainWindow, oConfig):
        super(PhysicalCardSetListFrame, self).__init__(oMainWindow, oConfig)
        self._sSetType = 'Physical Card Set'
        self._sFilterType = 'PhysicalCardSet'
        self._sName = 'Physical Card Set List'
        self._oSetClass = PhysicalCardSet
        self._dOpenCardSets = oMainWindow.dOpenPCS
        self.add_parts()

class AbstractCardSetListFrame(CardSetManagementFrame):
    def __init__(self, oMainWindow, oConfig):
        super(AbstractCardSetListFrame, self).__init__(oMainWindow, oConfig)
        self._sSetType = 'Abstract Card Set'
        self._sFilterType = 'AbstractCardSet'
        self._sName = 'Abstract Card Set List'
        self._oSetClass = AbstractCardSet
        self._dOpenCardSets = oMainWindow.dOpenACS
        self.add_parts()


