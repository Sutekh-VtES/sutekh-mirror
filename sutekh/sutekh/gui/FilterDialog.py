# FilterDialog.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Dialog for setting Filter Parameters
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# Copyright 2006, 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Allow the user to specify a filter."""

from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error, \
                                    do_complaint_buttons
from sutekh.core import FilterParser
from sutekh.gui.ConfigFile import ConfigFileListener
from sutekh.gui.FilterEditor import FilterEditor
import gtk
import gobject


class FilterDialog(SutekhDialog, ConfigFileListener):
    """Dialog which allows the user to select and edit filters.

       This dialog exists per card list view, and keeps state during
       a session by never being destoryed - just hiding itself when
       needed.

       This also listens to Config File events, so the list of available
       filters remains syncronised across the different views.
       """
    # pylint: disable-msg=R0904, R0902
    # R0904 - gtk.Widget, so many public methods
    # R0902 - we keep a lot of internal state, so many instance variables

    RESPONSE_CLEAR = 1
    RESPONSE_REVERT = 2
    RESPONSE_LOAD = 3
    RESPONSE_SAVE = 4
    RESPONSE_DELETE = 5

    DEFAULT_FILTERS = {
        "Default Filter Template": "(Clan in $var0) or (Discipline in $var1)"
            " or (CardType in $var2) or (CardFunction in $var3)",
        "Clan": "Clan in $var0",
        "Discipline": "Discipline in $var0",
        "Card Type": "CardType in $var0",
        "Card Text": "CardText in $var0",
        "Card Name": "CardName in $var0",
        "Card Set Name": "CardSetName in $var0",
        "Physical Expansion": "PhysicalExpansion in $var0",
    }

    INITIAL_FILTER = "Default Filter Template"

    def __init__(self, oParent, oConfig, sFilterType, sDefaultFilter=None):
        super(FilterDialog, self).__init__("Specify Filter",
                oParent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)

        self._oAccelGroup = gtk.AccelGroup()
        self.__oParent = oParent
        self.__bWasCancelled = False
        self.__oParser = FilterParser.FilterParser()
        self.__oConfig = oConfig
        self.__sFilterType = sFilterType
        self.__oFilter = None
        self.__oFilterEditor = FilterEditor(None, self.__sFilterType,
                                            self.__oParser, self)
        self.__oFilterEditor.connect_name_changed(self.__name_changed)

        self.__sOriginalName = None
        self.__sOriginalAST = None

        # Add Listener, so we catch filter changes in future
        # (this is only to set save / delete / revert button sensitivity)
        oConfig.add_listener(self)

        self.set_default_size(700, 550)
        self.connect("response", self.__button_response)

        # Dialog Buttons
        self.add_button("Clear Filter", self.RESPONSE_CLEAR)
        self.add_button("Revert Filter", self.RESPONSE_REVERT)
        self.add_button("Load", self.RESPONSE_LOAD)
        self.add_button("Save", self.RESPONSE_SAVE)
        self.add_button("Delete", self.RESPONSE_DELETE)

        # pylint: disable-msg=E1101
        # vbox, action_area confuse pylint
        self.action_area.pack_start(gtk.VSeparator(), expand=True)

        self.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)

        self.vbox.pack_start(self.__oFilterEditor)

        # set initial filter

        aDefaultFilters = self.__fetch_filters(True)
        aConfigFilters = self.__fetch_filters(False)

        if sDefaultFilter:
            # Ensure filter isn't broken
            # pylint: disable-msg=W0703
            # we do want to catch all exceptions here
            try:
                oAST = self.__oParser.apply(sDefaultFilter)
            except Exception:
                # Fall back to usual behaviour
                sDefaultFilter = None

        if sDefaultFilter:
            sName, sFilter = "", sDefaultFilter
            oAST = self.__oParser.apply(sFilter)
        elif aDefaultFilters:
            sName, sFilter = aDefaultFilters[0]
            oAST = self.__oParser.apply(sFilter)
        elif aConfigFilters:
            sName, sFilter = aConfigFilters[0]
            oAST = self.__oParser.apply(sFilter)
        else:
            sName, oAST = "", None

        self.__load_filter(sName, oAST)

        self.add_accel_group(self._oAccelGroup)

        self.show_all()

    # pylint: disable-msg=W0212
    # explicitly allow access to these values via thesep properties
    accel_group = property(fget=lambda self: self._oAccelGroup,
            doc="Dialog Accelerator group")
    # pylint: enable-msg=W0212

    def __button_response(self, _oWidget, iResponse):
        """Handle the button choices from the user.

           If the operation doesn't close the dialog, such as the
           filter manipulation options, we rerun the main dialog loop,
           waiting for another user button press.
           """
        # calls to self.run() are recursive
        # not sure if that's such a good thing

        if iResponse == gtk.RESPONSE_OK:
            # construct the final filter (may be None)
            self.__bWasCancelled = False
            self.__oFilter = self.__oFilterEditor.get_filter()
        elif iResponse == self.RESPONSE_CLEAR:
            # clear the  filter editor
            self.__clear_filter()
            return self.run()
        elif iResponse == self.RESPONSE_REVERT:
            # revert the filter editor AST to the saved version
            self.__revert_filter()
            return self.run()
        elif iResponse == self.RESPONSE_LOAD:
            # present the load filter dialog and handle result
            self.__run_load_dialog()
            return self.run()
        elif iResponse == self.RESPONSE_SAVE:
            # save the filter editor ast to the config file
            self.__save_filter()
            return self.run()
        elif iResponse == self.RESPONSE_DELETE:
            # delete the copy of the filter in the config file
            # and clear the filter editor
            self.__delete_filter()
            return self.run()
        else:
            self.__bWasCancelled = True
        self.hide()

    def __run_load_dialog(self):
        """Display a dialog for loading a filter."""
        oLoadDialog = SutekhDialog("Load Filter", self.__oParent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)

        oLoadDialog.set_keep_above(True)

        oLoadDialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
        oLoadDialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)

        # default (True or False), filter name (str), query string (str)
        oFilterStore = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING,
                                     gobject.TYPE_STRING)

        def iter_to_text(_oLayout, oCell, oModel, oIter):
            """Convert the model entry at oIter into the correct text"""
            bDefault = oModel.get_value(oIter, 0)
            sName = oModel.get_value(oIter, 1)
            if bDefault:
                oCell.set_property('text', sName + " (built-in)")
            else:
                oCell.set_property('text', sName)

        for bDefault in (True, False):
            for sName, sFilter in self.__fetch_filters(bDefault):
                oIter = oFilterStore.append(None)
                oFilterStore.set(oIter, 0, bDefault, 1, sName, 2, sFilter)

        oFilterSelector = gtk.ComboBox(oFilterStore)

        oCell = gtk.CellRendererText()
        oFilterSelector.pack_start(oCell, True)
        oFilterSelector.set_cell_data_func(oCell, iter_to_text)

        # pylint: disable-msg=E1101
        # vbox confuses pylint
        oLoadDialog.vbox.pack_start(oFilterSelector)
        oLoadDialog.show_all()

        try:
            iResponse = oLoadDialog.run()
            oIter = oFilterSelector.get_active_iter()

            if iResponse == gtk.RESPONSE_OK and oIter:
                sName = oFilterStore.get_value(oIter, 1)
                sFilter = oFilterStore.get_value(oIter, 2)
                oAST = self.__oParser.apply(sFilter)
                self.__load_filter(sName, oAST)
        finally:
            oLoadDialog.destroy()

    def __fetch_filters(self, bDefault):
        """Load filters from config or default list.

           Returns a (sName, sFilter) list.
           """
        if bDefault:
            sSrc = "default filter list"
            oFilterIter = list(self.DEFAULT_FILTERS.items())
        else:
            sSrc = "config file"
            oFilterIter = list(self.__oConfig.get_filter_keys())

        aFilters = []
        aErrMsgs = []

        for sName, sFilter in oFilterIter:
            # pylint: disable-msg=W0703
            # we do want to catch all exceptions here
            try:
                oAST = self.__oParser.apply(sFilter)
                if oAST.get_filter_expression() is None or \
                    self.__sFilterType in oAST.get_type():
                    aFilters.append((sName, sFilter))
            except Exception:
                # remove broken filter
                aErrMsgs.append("%s (filter: '%s')" % (sName, sFilter))
                if not bDefault:
                    self.__oConfig.remove_filter(sFilter, sName)
                else:
                    del self.DEFAULT_FILTERS[sName]

        if aErrMsgs:
            do_complaint_error("The following invalid filters have been" \
                               " removed from the %s:\n" % (sSrc,)\
                               + "\n".join(aErrMsgs))

        def filter_cmp(oFilt1, oFilt2):
            """Sort filters alphabetically by name, but with default
               filter first if it is present"""
            if oFilt1[0] == self.INITIAL_FILTER:
                return -1
            elif oFilt2[0] == self.INITIAL_FILTER:
                return 1
            else:
                return cmp(oFilt1[0], oFilt2[0])

        aFilters.sort(cmp=filter_cmp)

        return aFilters

    def __load_filter(self, sName, oAST):
        """Set the current filter to sName, oAST."""
        self.__sOriginalName = sName
        self.__sOriginalAST = oAST
        self.__oFilterEditor.set_name(sName)
        self.__oFilterEditor.replace_ast(oAST)
        self.__update_sensitivity()

    def __revert_filter(self):
        """Revert the filter to the last one set."""
        self.__oFilterEditor.set_name(self.__sOriginalName)
        self.__oFilterEditor.replace_ast(self.__sOriginalAST)
        self.__update_sensitivity()

    def __clear_filter(self):
        """Clear the filter AST."""
        self.__oFilterEditor.set_name("")
        self.__oFilterEditor.replace_ast(None)
        self.__update_sensitivity()

    def __save_filter(self):
        """Save the filter to the config."""
        sName = self.__oFilterEditor.get_name()
        sFilter = self.__oFilterEditor.get_current_text()
        sConfigFilter = self.__oConfig.get_filter(sName)
        bSaved = False

        if sConfigFilter is not None:
            iResponse = do_complaint_buttons(
                            "Replace existing filter '%s'?" % (sName,),
                            gtk.MESSAGE_QUESTION,
                            (gtk.STOCK_YES, gtk.RESPONSE_YES,
                             gtk.STOCK_NO, gtk.RESPONSE_NO))
            if iResponse == gtk.RESPONSE_YES:
                self.__oConfig.replace_filter(sName, sConfigFilter, sFilter)
                bSaved = True
        else:
            self.__oConfig.add_filter(sName, sFilter)
            bSaved = True

        if bSaved:
            # load saved filter to set everything correctly
            oAST = self.__oParser.apply(sFilter)
            self.__load_filter(sName, oAST)

    def __delete_filter(self):
        """Delete the filter from the config."""
        sName = self.__oFilterEditor.get_name()
        sConfigFilter = self.__oConfig.get_filter(sName)

        if sConfigFilter is not None:
            self.__oConfig.remove_filter(sName, sConfigFilter)

        self.__load_filter("", None)

    def __update_sensitivity(self):
        """Update which responses are available."""
        # clear, revert and load are always available

        sName = self.__oFilterEditor.get_name()
        sConfigFilter = self.__oConfig.get_filter(sName)

        # save is available unless there is no name to save as
        if sName:
            self.set_response_sensitive(self.RESPONSE_SAVE, True)
        else:
            self.set_response_sensitive(self.RESPONSE_SAVE, False)

        # delete is available if the name is unchanged and the
        # original name exists in the config
        if sName == self.__sOriginalName and sConfigFilter is not None:
            self.set_response_sensitive(self.RESPONSE_DELETE, True)
        else:
            self.set_response_sensitive(self.RESPONSE_DELETE, False)

    def __name_changed(self, _oNameEntry):
        """Callback for connecting to filter editor name change events."""
        self.__update_sensitivity()

    # Dialog result retrievel methods

    def get_filter(self):
        """Get the current filter for this dialog."""
        return self.__oFilter

    def was_cancelled(self):
        """Return true if the user cancelled the filter dialog."""
        return self.__bWasCancelled

    # Config File Listener methods
    def replace_filter(self, _sId, _sOldFilter, _sNewFilter):
        """Handle a filter in the config file being replaced."""
        self.__update_sensitivity()

    def add_filter(self, _sId, _sFilter):
        """Handle filter being added to the config file."""
        self.__update_sensitivity()

    def remove_filter(self, _sId, _sFilter):
        """Handle a filter being removed from the config file."""
        self.__update_sensitivity()
