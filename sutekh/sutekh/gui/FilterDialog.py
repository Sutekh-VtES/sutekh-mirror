# FilterDialog.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Dialog for setting Filter Parameters
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006, 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Allow the user to specify a filter."""

import gtk
from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
from sutekh.core import FilterParser
from sutekh.gui.ConfigFile import ConfigFileListener
from sutekh.gui.FilterEditor import FilterEditor

DEFAULT_FILTERS = (
        "Clan in $var0",
        "Discipline in $var0",
        "CardType in $var0",
        "CardText in $var0",
        "CardName in $var0",
        "AbstractCardSetName in $var0",
        "PhysicalCardSetName in $var0",
        "PhysicalExpansion in $var0"
        )

class FilterDialog(SutekhDialog, ConfigFileListener):
    """Dialog which allows the user to select and edit filters.

       This dialog exists per card list view, and keeps state during
       a session by never being destoryed - just hiding itself when
       needed.
       This also listens to Config File events, so the list of available
       filters remains syncronised across the different views.
       """
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods

    __iAddButtonResponse = 1
    __iCopyButtonResponse = 2
    __iRevertButtonResponse = 3
    __iSaveButtonResponse = 4
    __iDeleteButtonResponse = 5

    def __init__(self, oParent, oConfig, sFilterType):
        super(FilterDialog, self).__init__("Specify Filter",
                oParent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)

        self.__oParent = oParent

        # Dialog Buttons
        self.add_button("New Filter", self.__iAddButtonResponse)
        self.add_button("Copy Filter", self.__iCopyButtonResponse)
        self.add_button("Revert", self.__iRevertButtonResponse)
        # Want a reference to these button, so we can fiddle active state
        self.__oSaveButton = self.add_button("Save Filter",
                self.__iSaveButtonResponse)
        self.__oDeleteButton = self.add_button("Delete Filter",
                self.__iDeleteButtonResponse)
        # pylint: disable-msg=E1101
        # vbox, action_area confuse pylint
        self.action_area.pack_start(gtk.VSeparator(), expand=True)
        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.oCancelButton = self.add_button(gtk.STOCK_CANCEL,
                gtk.RESPONSE_CANCEL)
        self.connect("response", self.__button_response)

        self.__oParser = FilterParser.FilterParser()
        self.__oConfig = oConfig
        self.__sFilterType = sFilterType
        self.__dButtons = {}
        self.__oFilter = None
        self.__bWasCancelled = False
        self.__oRadioGroup = None

        self.set_default_size(700, 550)
        self.__oExpandedArea = gtk.HBox(spacing=5)
        self.__oRadioArea = gtk.VBox()
        self.__sExpanded = None
        oHScrolledWindow = AutoScrolledWindow(self.__oExpandedArea, True)
        oHScrolledWindow.set_size_request(680, 450)
        self.vbox.pack_start(oHScrolledWindow)
        self.vbox.pack_start(AutoScrolledWindow(self.__oRadioArea, True))
        self.vbox.set_homogeneous(False)

        self.__dFilterList = {} # id -> filter string
        self.__dFilterEditors = {} # id -> filter editor
        self.__aDefaultFilterIds = []

        # Setup default filters
        # First filter is expanded by default
        for sFilter in DEFAULT_FILTERS:
            # Parse the filter into the seperate bits needed
            try:
                oAST = self.__oParser.apply(sFilter)
            except ValueError, oExcep:
                do_complaint_error("Invalid Filter: %s\n Error: %s" % (sFilter,
                    oExcep))
                continue
            sId = self.__add_filter_to_dialog(oAST, sFilter)
            self.__aDefaultFilterIds.append(sId)
        self.__expand_filter(self.__oRadioGroup, self.__aDefaultFilterIds[0])

        # Load other filters from config file
        aAllFilters = oConfig.get_filter_keys()
        sMessages = ''
        for sId, sFilter in aAllFilters:
            try:
                oAST = self.__oParser.apply(sFilter)
                self.__add_filter_to_dialog(oAST, sFilter, sId)
            except ValueError:
                sMessages += sFilter + "\n"
                self.__oConfig.remove_filter(sFilter, sId)
        if sMessages != '':
            do_complaint_error("The Following Invalid filters have been"
                    " removed from the config file:\n " + sMessages)
        self.show_all()

        # Add Listener, so we catch changes in future
        oConfig.add_listener(self)

    def __add_filter_to_dialog(self, oAST, sFilter, sId=''):
        """
        Register a filter with the dialog, creating necessary components.

        Don't inform the ConfigFile.
        """
        if sId == '' or sId in self.__dFilterEditors:
            # ensure we have a unique key here
            iNum = len(self.__dFilterEditors)
            sId = 'Filter '+str(iNum)
            while sId in self.__dFilterEditors:
                iNum += 1
                sId = 'Filter '+str(iNum)

        self.__dFilterList[sId] = sFilter
        if oAST.get_filter_expression() is not None and \
                self.__sFilterType not in oAST.get_type():
            return sId
        self.__dFilterEditors[sId] = FilterEditor(oAST,
                self.__sFilterType, self.__oParser, self)

        oRadioButton = gtk.RadioButton(self.__oRadioGroup)
        if self.__oRadioGroup is None:
            self.__oRadioGroup = oRadioButton
        oRadioButton.set_label(sFilter)
        self.__dButtons[sId] = oRadioButton
        oRadioButton.connect("toggled", self.__expand_filter, sId)
        self.__oRadioArea.pack_start(oRadioButton)

        return sId

    def __expand_filter(self, oRadioButton, sId):
        """
        When the user selects a radio button, expand
        the options
        """
        if sId != self.__sExpanded and sId in self.__dFilterEditors:
            # Remove the previous filter
            for oChild in self.__oExpandedArea.get_children():
                self.__oExpandedArea.remove(oChild)
            self.__sExpanded = sId
            self.__oExpandedArea.pack_start(self.__dFilterEditors[sId])
            self.__oExpandedArea.show_all()
            if sId not in self.__aDefaultFilterIds:
                # User defined filter, can be deleted & edited
                self.__oSaveButton.set_sensitive(True)
                self.__oDeleteButton.set_sensitive(True)
            else:
                self.__oSaveButton.set_sensitive(False)
                self.__oDeleteButton.set_sensitive(False)

    def __button_response(self, oWidget, iResponse):
        """Handle the button choices from the user.

           If the operation doesn't close the dialog, such as the
           filter manipulation options, we rerun the main dialog loop,
           waiting for another user button press.
           """
        sId = self.__sExpanded
        sOld = self.__dFilterList[sId]

        # calls to self.run() are recursive
        # not sure if that's such a good thing

        if iResponse ==  gtk.RESPONSE_OK:
            self.__bWasCancelled = False
            # Construct the Final filter (may be None)
            self.__oFilter = self.__dFilterEditors[sId].get_filter()
            if self.__oFilter is None:
                return self.run()
        elif iResponse == self.__iAddButtonResponse:
            # Add a blank filter
            self.__oConfig.add_filter('')
            return self.run()
        elif iResponse == self.__iCopyButtonResponse:
            sCurr = self.__dFilterEditors[sId].get_current_text()
            self.__oConfig.add_filter(sCurr)
            return self.run()
        elif iResponse == self.__iRevertButtonResponse:
            if sId in self.__aDefaultFilterIds:
                # TODO: Do other filter dialogs need to be notified somehow?
                self.replace_filter(sOld, sOld, sId)
            else:
                self.__oConfig.replace_filter(sOld, sOld, sId)
            self.__expand_filter(None, sId)
            return self.run()
        elif iResponse == self.__iSaveButtonResponse:
            sCurr = self.__dFilterEditors[sId].get_current_text()
            self.__oConfig.replace_filter(sOld, sCurr, sId)
            self.__expand_filter(None, sId)
            return self.run()
        elif iResponse == self.__iDeleteButtonResponse:
            self.__oConfig.remove_filter(self.__dFilterList[sId], sId)
            return self.run()
        else:
            self.__bWasCancelled = True
        self.hide()

    def forced_cancel(self):
        """Emulate Cancelling button press."""
        self.__bWasCancelled = True
        self.hide()

    def __replace_filter_in_dialog(self, oAST, sOldFilter, sNewFilter, sId):
        """
        Replace an existing filter with the new one
        Preserve selections if possible
        """
        self.__dFilterList[sId] = sNewFilter
        oOldEditor, oNewEditor = None, None

        if sId not in self.__dFilterEditors:
            # wasn't in editors before, might be okay now, try add it
            self.__add_filter_to_dialog(self, oAST, sNewFilter, sId)
            self.__oRadioGroup.show_all()
        elif oAST.get_type() and self.__sFilterType not in oAST.get_type():
            # was in editors before, but shouldn't be now, remove it
            del self.__dFilterEditors[sId]
            oRadioButton = self.__dButtons[sId]
            self.__oRadioArea.remove(oRadioButton)
            del self.__dButtons[sId]
            self.__oRadioGroup.clicked()
            self.__oRadioArea.show_all()
        else:
            # was in editors before and should still be there, replace it
            # We treat oAST.get_type() is None as a catch-all type
            dOldVars = self.__dFilterEditors[sId].get_current_values()
            self.__dFilterEditors[sId] = FilterEditor(oAST,
                    self.__sFilterType, self.__oParser, self)
            self.__dFilterEditors[sId].set_current_values(dOldVars)

            self.__dButtons[sId].set_label(sNewFilter)
            self.__oRadioArea.show_all()
            self.__sExpanded = None
            self.__expand_filter(None, sId)

    # Dialog result retrievel methods

    def get_filter(self):
        """Get the current filter for this dialog."""
        return self.__oFilter

    def was_cancelled(self):
        """Return true if the user cancelled the filter dialog."""
        return self.__bWasCancelled

    # Cancel button query for multiselect combo

    # Config File Listener methods

    def replace_filter(self, sOldFilter, sNewFilter, sId):
        """Replace sOldFilter with the new filter sNewFilter."""
        try:
            # Should be safe, but just in case
            oAST = self.__oParser.apply(sNewFilter)
        except ValueError, oExcep:
            do_complaint_error("Invalid Filter: %s\n Error: %s" % (sNewFilter,
                oExcep))
            return
        self.__replace_filter_in_dialog(oAST, sOldFilter, sNewFilter, sId)
        self.__oRadioArea.show_all()

    def add_filter(self, sFilter, sId):
        """Add a filter to the dialog."""
        try:
            # Should be safe, but just in case
            oAST = self.__oParser.apply(sFilter)
        except ValueError, oExcep:
            do_complaint_error("Invalid Filter: %s\n Error: %s" % (sFilter,
                oExcep))
            return
        self.__add_filter_to_dialog(oAST, sFilter, sId)
        self.__oRadioArea.show_all()

    def remove_filter(self, sFilter, sId):
        """Remove a filter from the dialog."""
        del self.__dFilterList[sId]
        if sId in self.__dFilterEditors:
            del self.__dFilterEditors[sId]
            oRadioButton = self.__dButtons[sId]
            self.__oRadioArea.remove(oRadioButton)
            del self.__dButtons[sId]
            self.__oRadioGroup.clicked()
            self.__oRadioArea.show_all()
