# PreferenceTable.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Table widget for editing a list of options.
# Copyright 2010 Simon Cross <hodgestar+sutekh@gmail.com>
# GPL - see COPYING for details

"""Widget that constructs an interface to manipulate the profile options.

   Used by the various Profile editor dialogs."""

import gtk


class PreferenceTable(gtk.Table):
    """A widget for editing a list of options."""
    # pylint: disable-msg=R0904, R0902
    # R0904 - gtk.Widget, so many public methods

    COLUMNS = 3
    KEY_COL, ENTRY_COL, INHERIT_COL = range(COLUMNS)

    def __init__(self, aOptions, oValidator):
        self._aOptions = []
        for sKey, sConfigSpec, _bInherit in aOptions:
            self._aOptions.append(
                PreferenceOption(sKey, sConfigSpec, oValidator))

        self._aOptions.sort(
            key=lambda oOpt: oOpt.sKey != "name" and oOpt.sKey or "")

        super(PreferenceTable, self).__init__(
            rows=len(self._aOptions), columns=self.COLUMNS)
        self.set_col_spacings(5)
        self.set_row_spacings(5)

        dAttachOpts = {
            "xoptions": gtk.FILL,
            "yoptions": 0,
        }
        for iRow, oOpt in enumerate(self._aOptions):
            # pylint: disable-msg=W0142
            # *args magic OK here
            self.attach(oOpt.oLabel, self.KEY_COL, self.KEY_COL + 1,
                iRow, iRow + 1, **dAttachOpts)
            self.attach(oOpt.oEntry, self.ENTRY_COL, self.ENTRY_COL + 1,
                iRow, iRow + 1, **dAttachOpts)
            self.attach(oOpt.oInherit, self.INHERIT_COL, self.INHERIT_COL + 1,
                iRow, iRow + 1, **dAttachOpts)

    def update_values(self, dNewValues, dInherit, dEditable, dInheritedValues):
        """Update the option values.

           dNewValues is an sKey -> sValue mapping.
           dInherit is an sKey -> bInheritable mapping.
           dEditable is an sKey -> bEditable mapping.
           """
        for oOpt in self._aOptions:
            oInheritedValue = dInheritedValues.get(oOpt.sKey)
            oOpt.set_inheritable(dInherit.get(oOpt.sKey, True))
            oOpt.set_editable(dEditable.get(oOpt.sKey, True))
            oOpt.set_value(dNewValues.get(oOpt.sKey), oInheritedValue)

    def get_values(self):
        """Return a dictionary of option values."""
        return dict((oOpt.sKey, oOpt.get_value()) for oOpt in self._aOptions)


class PreferenceOption(object):
    """An option for a preference table."""

    def __init__(self, sKey, sConfigSpec, oValidator):
        self.sKey = sKey
        self.oSpec = parse_spec(sConfigSpec, oValidator)
        self.oEntry = self.oSpec.oEntry
        self.oLabel = gtk.Label(sKey.capitalize())
        self.oLabel.set_alignment(0, 0)
        self.bInheritable = True
        self.oInherit = gtk.CheckButton("use default")
        self.oInherit.connect("toggled", self._inherit_toggled)
        self.bEditable = True

    def set_inheritable(self, bInheritable):
        """Set whether the values are inherited from the default profile"""
        self.bInheritable = bInheritable
        if bInheritable:
            self.oInherit.set_sensitive(True)
            self.oInherit.show()
        else:
            self.oInherit.set_sensitive(False)
            self.oInherit.hide()

    def set_editable(self, bEditable):
        """Mark the option as editable"""
        self.bEditable = bEditable
        self.oEntry.set_sensitive(bEditable)

    def set_value(self, oValue, oInheritedValue):
        """Update the value of the option."""
        if oValue is None and self.bInheritable:
            self.oEntry.set_sensitive(False)
            self.oInherit.set_active(True)
        else:
            self.oEntry.set_sensitive(self.bEditable)
            self.oInherit.set_active(False)
            self.oSpec.set_value(oValue)
        if hasattr(self.oInherit, 'set_tooltip_markup'):
            sToolTip = "Inherited value:\n%s" % \
                self.oSpec.format_value(oInheritedValue)
            self.oInherit.set_tooltip_markup(sToolTip)

    def get_value(self):
        """Return the value of the option."""
        if self.oInherit.get_active():
            return None
        else:
            return self.oSpec.get_value()

    def _inherit_toggled(self, _oWidget):
        """Update the state after the inherit widget is toggled."""
        if self.oInherit.get_active():
            self.oEntry.set_sensitive(False)
        else:
            self.oEntry.set_sensitive(self.bEditable)


class BaseParsedSpec(object):
    """Object holding the result of parsing a ConfigSpec check."""

    def __init__(self, sType, aArgs, dKwargs, sDefault):
        self.sType, self.aArgs, self.dKwargs, self.sDefault = \
            sType, aArgs, dKwargs, sDefault
        self.oEntry = self.create_widget()

    def format_value(self, oValue):
        """Return a string representation of a value."""
        return str(oValue)

    def create_widget(self):
        """Return a widget for editing this config spec."""
        raise NotImplementedError

    def set_value(self, oValue):
        """Set an editing widget value."""
        raise NotImplementedError

    def get_value(self):
        """Get the value from an editing widget."""
        raise NotImplementedError


class UneditableSpec(BaseParsedSpec):
    """Class for a spec entry that can't be edited"""

    # pylint: disable-msg=W0201
    # we define _oOrigValue outside __init__, but it's OK because create_widget
    # is called in init
    def create_widget(self):
        """Create a suitable widget (gtk.Label)"""
        self._oOrigValue = None
        return gtk.Label()

    def set_value(self, oValue):
        """Set the label value"""
        self._oOrigValue = oValue
        self.oEntry.set_text(str(oValue))

    def get_value(self):
        """Get the label value"""
        return self._oOrigValue


class StringParsedSpec(BaseParsedSpec):
    """Class for a option taking an arbitrary string"""

    def create_widget(self):
        """Create suitable widget (gtk.Entry)"""
        return gtk.Entry()

    def set_value(self, oValue):
        """Set the entry widget value"""
        if oValue is None:
            oValue = ""
        self.oEntry.set_text(str(oValue))

    def get_value(self):
        """Get the entry widget value"""
        return self.oEntry.get_text()


class BooleanParsedSpec(BaseParsedSpec):
    """Class for a Boolean option in the spec"""

    def create_widget(self):
        """Create a a suitable widget (gtk.CheckBox)"""
        return gtk.CheckButton()

    def set_value(self, oValue):
        """Set the checkbox correctly for the given value"""
        if oValue:
            self.oEntry.set_active(True)
        else:
            self.oEntry.set_active(False)

    def get_value(self):
        """Get the checkbox value"""
        return self.oEntry.get_active()


class OptionParsedSpec(BaseParsedSpec):
    """Widget for dealing with a list of exclusive options"""

    def create_widget(self):
        """Create a suitable widget (gtk.ComboBox)"""
        oCombo = gtk.combo_box_new_text()
        for sValue in self.aArgs:
            oCombo.append_text(sValue)
        return oCombo

    def set_value(self, oValue):
        """Set the values on the combo box"""
        try:
            iIndex = self.aArgs.index(oValue)
        except ValueError:
            iIndex = -1
        self.oEntry.set_active(iIndex)

    def get_value(self):
        """Get the combo box value"""
        iIndex = self.oEntry.get_active()
        if iIndex < 0 or iIndex >= len(self.aArgs):
            return None
        return self.aArgs[iIndex]


class OptionListParsedSpec(BaseParsedSpec):
    """Class for dealing with a list of non-exclusive options"""

    def create_widget(self):
        """Create suitable widget (list of gtk.CheckBoxes)"""
        oContainer = gtk.VBox()
        for sValue in self.aArgs:
            oContainer.pack_start(gtk.CheckButton(sValue))
        return oContainer

    def format_value(self, oValue):
        """Return a string representation of the value."""
        if not oValue:
            return "None"
        else:
            return ", ".join(oValue)

    def set_value(self, oValue):
        """Set the selected list correctly"""
        oValSet = set(oValue)
        for oButton in self.oEntry.get_children():
            oButton.set_active(oButton.get_label() in oValSet)

    def get_value(self):
        """Get the current list of selected items"""
        return [oButton.get_label() for oButton in self.oEntry.get_children()
            if oButton.get_active()]


class IntegerParsedSpec(BaseParsedSpec):
    """Class for dealing with integer valued options"""

    def create_widget(self):
        """Create suitable widget (gtk.Adjustment)"""
        iMin = self.dKwargs.get("min", 0)
        iMax = self.dKwargs.get("max", 100)

        oAdj = gtk.Adjustment(iMin, iMin, iMax, 1.0, 5.0, 0.0)
        oSpin = gtk.SpinButton(oAdj, 0, 0)
        oSpin.set_numeric(True)
        return oSpin

    def set_value(self, oValue):
        """Set the adjustment value, ignoring errornous input"""
        try:
            oValue = int(oValue)
        except ValueError:
            pass
        else:
            self.oEntry.set_value(oValue)

    def get_value(self):
        """Get the value form the gtk.Adjustment"""
        return self.oEntry.get_value_as_int()


SPEC_TYPE_MAP = {
    "string": StringParsedSpec,
    "boolean": BooleanParsedSpec,
    "option": OptionParsedSpec,
    "option_list": OptionListParsedSpec,
    "integer": IntegerParsedSpec,
}


def parse_spec(sConfigSpec, oValidator):
    """Parse a configobj spec into a parsed spec."""
    # TODO: is it okay to use an _ method from the validator?
    # pylint: disable-msg=W0212
    # We know we're accessing a protected member, and pylint flags our
    # note above, so don't flag this twice
    sType, aArgs, dKwargs, sDefault = \
        oValidator._parse_with_caching(sConfigSpec)
    cParsedSpec = SPEC_TYPE_MAP.get(sType, UneditableSpec)
    return cParsedSpec(sType, aArgs, dKwargs, sDefault)
