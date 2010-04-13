# FrameProfileEditor.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Dialog for editing per-frame/per-deck profiles.
# Copyright 2010 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details


from sutekh.gui.SutekhDialog import SutekhDialog, do_complaint_error, \
                                    do_complaint_buttons
from sutekh.gui.AutoScrolledWindow import AutoScrolledWindow
import gtk
import gobject

class FrameProfileEditor(SutekhDialog):
    """Dialog which allows the user to per-deck option profiles.
       """
    # pylint: disable-msg=R0904, R0902
    # R0904 - gtk.Widget, so many public methods

    NEW_PROFILE_TEXT = "New Profile ..."

    RESPONSE_CLOSE = 1

    def __init__(self, oParent, oConfig):
        super(FrameProfileEditor, self).__init__("Edit Per-Deck Profiles",
                oParent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)

        self.__oConfig = oConfig

        self.__dOptionWidgets = {}
        for sKey in self.__oConfig.deck_options():
            self.__dOptionWidgets[sKey] = self.widget_for_option(sKey)

        oTopBox = gtk.VBox()
        self.vbox.pack_start(oTopBox)

        self.__oSelectorBox = gtk.VBox()
        oTopBox.pack_start(self.__oSelectorBox, expand=False)

        self.__oOptionsBox = gtk.VBox()
        self.__oOptionsBox.set_spacing(5)
        oTopBox.pack_start(AutoScrolledWindow(self.__oOptionsBox,
            bUseViewport=True), expand=True, fill=True)
        self.__oProfileLabel = gtk.Label("")
        self.__oOptionsBox.pack_start(self.__oProfileLabel, expand=False)
        for sKey in sorted(self.__oConfig.deck_options()):
            self.__oOptionsBox.pack_start(self.__dOptionWidgets[sKey], expand=False)
        self.__oOptionsBox.show_all()

        self.set_default_size(600, 550)
        self.connect("response", self._button_response)
        self.add_button("Close", self.RESPONSE_CLOSE)

        self._repopulate_selector("default")
        self._repopulate_options("default")

        self.show_all()

    def widget_for_option(self, sKey):
        """Create a option widget for the given config key."""
        return BaseOptionWidget(sKey,
            self.__oConfig.get_deck_option_spec(sKey),
            self.__oConfig.get_validator())

    def _button_response(self, _oWidget, _iResponse):
        """Handle dialog response"""
        self.destroy()

    def _repopulate_selector(self, sActiveProfile=None):
        """Refresh the contents of the selector box."""
        for child in self.__oSelectorBox.get_children():
            self.__oSelectorBox.remove(child)

        oModel = gtk.ListStore(gobject.TYPE_STRING)
        oActiveIter = None
        for sProfile in ["default"] + list(sorted(self.__oConfig.profiles())):
            oIter = oModel.append((sProfile,))
            if sProfile == sActiveProfile:
                oActiveIter = oIter
        oIter = oModel.append((self.NEW_PROFILE_TEXT,))
        if oActiveIter is None:
            oActiveIter = oIter

        oComboBox = gtk.ComboBox(oModel)
        oCell = gtk.CellRendererText()
        oComboBox.pack_start(oCell, True)
        oComboBox.add_attribute(oCell, 'text', 0)
        oComboBox.set_active_iter(oActiveIter)
        oComboBox.connect("changed", self._selector_changed)

        self.__oSelectorBox.pack_start(oComboBox, expand=False)
        self.__oSelectorBox.show_all()

    def _selector_changed(self, oSelectorCombo):
        """Callback for changes to selected combo."""
        oModel = oSelectorCombo.get_model()
        oActiveIter = oSelectorCombo.get_active_iter()
        if oActiveIter is None:
            sActiveProfile = None
        else:
            sActiveProfile = oModel.get_value(oActiveIter, 0)
            if sActiveProfile == self.NEW_PROFILE_TEXT:
                sActiveProfile = None

        self._repopulate_options(sActiveProfile)

    def _repopulate_options(self, sActiveProfile=None):
        """Refresh the contents of the options box."""
        if sActiveProfile is None:
            self.__oProfileLabel.set_markup("<b>New profile</b>")
        else:
            self.__oProfileLabel.set_markup("<b>%s</b>" % sActiveProfile.capitalize())

        for sKey in self.__oConfig.deck_options():
            if sActiveProfile is not None:
                oValue = self.__oConfig.get_deck_profile_option(sActiveProfile, sKey)
            else:
                oValue = None
            self.__dOptionWidgets[sKey].update_value(oValue)


class BaseOptionWidget(gtk.HBox):
    """Widget representing a config option.
       """
    # pylint: disable-msg=R0904, R0902
    # R0904 - gtk.Widget, so many public methods

    def __init__(self, sKey, sConfigSpec, oValidator):
        super(BaseOptionWidget, self).__init__()
        self.__oValidator = oValidator
        self.__sConfigSpec = sConfigSpec
        self.__sFuncName, _aArgs, _dKwargs, _sDefault = \
            oValidator._parse_with_caching(sConfigSpec)

        self.pack_start(gtk.Label(sKey.capitalize()), expand=False)

        self.__oValueEntry = self.create_value_widget()
        if hasattr(self.__oValueEntry, 'set_tooltip_markup'):
            self.__oValueEntry.set_tooltip_markup(sConfigSpec)

        self.pack_start(self.__oValueEntry, expand=False)
        self.show_all()

    def create_value_widget(self):
        """Create an appropriate value widget."""
        if self.__sFuncName == "boolean":
            return gtk.CheckButton()
        else:
            return gtk.Entry()

    def update_value(self, oValue):
        """Update the config key value. None indicates a value not present."""
        if self.__sFuncName == "boolean":
            if oValue:
                self.__oValueEntry.set_active(True)
            else:
                self.__oValueEntry.set_active(False)
        else:
            if oValue is None:
                self.__oValueEntry.set_text("")
            else:
                self.__oValueEntry.set_text(str(oValue))
