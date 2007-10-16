# CardSetManagementFrame.py
# Window for Managing Physical and Abstract Card Sets
# Copyright 2007 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
from sqlobject.events import listen
from sutekh.core.SutekhObjects import AbstractCardSet, PhysicalCardSet
from sutekh.gui.ScrolledList import ScrolledList
from sutekh.gui.SQLObjectEvents import RowDestroySignal, RowUpdateSignal, \
        RowCreatedSignal, CardSetOpenedSignal, CardSetClosedSignal

class CardSetManagementFrame(gtk.Frame, object):
    def __init__(self, oMainWindow):
        super(CardSetManagementFrame, self).__init__()
        self._oMainWin = oMainWindow
        self._sSetType = None
        self._sName = 'Card Set List'
        self._oView = None
        self._dOpenCardSets = {}

    name = property(fget=lambda self: self._sName, doc="Frame Name")
    view = property(fget=lambda self: self._oView, doc="Associated View Object")
    open_card_sets = property(fget=lambda self: self._dOpenCardSets,
            doc="Dictionary of currently open card sets")
    type = property(fget=lambda self: self._sName, doc="Frame Type")

    def cleanup(self):
        pass

    def add_parts(self):
        """Add a list object to the frame"""
        self._oScrolledList = ScrolledList(self._sName,'')
        self._oView = self._oScrolledList.TreeView
        self._oScrolledList.set_select_single()
        self._oView.connect('row_activated',self.row_clicked)
        self.add(self._oScrolledList)
        self.reload_card_set_list()
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
        for oCS in self._oSetClass.select().orderBy('name'):
            if oCS.name not in self._dOpenCardSets.keys():
                iter = oThisList.append(None)
            else:
                iter = oThisList.insert_before(self._oAvailIter)
            oThisList.set(iter,0,oCS.name)

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
    def __init__(self, oMainWindow):
        super(PhysicalCardSetListFrame, self).__init__(oMainWindow)
        self._sSetType = 'Physical Card Set'
        self._sName = 'Physical Card Set List'
        self._oSetClass = PhysicalCardSet
        self._dOpenCardSets = oMainWindow.dOpenPCS
        self.add_parts()

class AbstractCardSetListFrame(CardSetManagementFrame):
    def __init__(self, oMainWindow):
        super(AbstractCardSetListFrame, self).__init__(oMainWindow)
        self._sSetType = 'Abstract Card Set'
        self._sName = 'Abstract Card Set List'
        self._oSetClass = AbstractCardSet
        self._dOpenCardSets = oMainWindow.dOpenACS
        self.add_parts()


