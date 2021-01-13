# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Widget for displaying the card text for the given card."""

import logging

from gi.repository import Gtk, Pango

from .MessageBus import MessageBus


class BaseCardTextBuffer(Gtk.TextBuffer):
    """Base class for buffer object which holds the actual card text.
       """

    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods
    def __init__(self):
        super().__init__()

        # See http://www.pyGtk.org/pyGtk2reference/class-Gtktexttag.html
        # for some possible properties

        self._oIconTabs = Pango.TabArray(1, True)
        # Icons are scaled to 15'ish
        self._oIconTabs.set_tab(0, Pango.TabAlign.LEFT, 15)

        self.create_tag("label", underline=Pango.Underline.SINGLE)

        self.create_tag("card_name", weight=Pango.Weight.BOLD)

        self._oIter = None

    def tag_text(self, *aArgs, **kwargs):
        """Inset the text (possibly with tags) at the current position"""
        self.insert_with_tags_by_name(self._oIter, *aArgs, **kwargs)

    # Methods for adding new tags to the buffer

    def add_tag(self, sTag):
        """Add a simple tag"""
        self.create_tag(sTag, style=Pango.Style.ITALIC)
        self.create_mark(sTag, self.get_start_iter(), True)

    def add_list_tag(self, sTag):
        """Add a tag with the list style indents"""
        self.create_tag(sTag, style=Pango.Style.ITALIC, left_margin=15,
                        tabs=self._oIconTabs)
        self.create_mark(sTag, self.get_start_iter(), True)

    # Methods for adding data

    def labelled_value(self, sLabel, sValue, sTag, oIcon=None):
        """Add a single value to the buffer."""
        self.tag_text("\n")
        self.tag_text(sLabel, "label")
        self.tag_text(": ")
        if oIcon:
            self.insert_pixbuf(self._oIter, oIcon)
            self.insert(self._oIter, ' ')
        self.tag_text(sValue, sTag)
        self.move_mark(self.get_mark(sTag), self._oIter)

    def labelled_list(self, sLabel, aValues, sTag, dIcons=None):
        """Add a list of values to the Buffer"""
        def _insert_line(sText, sTag, oPixbuf):
            """Insert a line, prefixed by oPixbuf."""
            if oPixbuf:
                self.tag_text('\n', sTag)
                # This is a bit complicated - we need to insert the pixbuf
                # into a region already tagged with the correct tag for
                # the margins + tabs to work. We use a text mark to note
                # where to insert the pixbuf, insert the text, then
                # we backtrack to insert the pixbuf.
                oMark1 = self.create_mark(None, self._oIter, True)
                self.tag_text('\t%s' % sText, sTag)
                oMarkEnd = self.create_mark(None, self._oIter, True)
                self.insert_pixbuf(self.get_iter_at_mark(oMark1), oPixbuf)
                # We've invalidated self._oIter, so restore it
                self._oIter = self.get_iter_at_mark(oMarkEnd)
                self.delete_mark(oMark1)
                self.delete_mark(oMarkEnd)
            else:
                self.tag_text('\n*\t%s' % sText, sTag)
        self.tag_text("\n")
        self.tag_text(sLabel, "label")
        self.tag_text(":")
        for sValue in aValues:
            if dIcons:
                if sValue in dIcons and dIcons[sValue]:
                    _insert_line(sValue, sTag, dIcons[sValue])
                elif sValue.lower() in dIcons and dIcons[sValue.lower()]:
                    _insert_line(sValue, sTag, dIcons[sValue.lower()])
                else:
                    _insert_line(sValue, sTag, None)
            else:
                _insert_line(sValue, sTag, None)
        self.move_mark(self.get_mark(sTag), self._oIter)

    def labelled_compact_list(self, sLabel, aValues, sTag):
        """More compact list for clans, etc."""
        self.labelled_value(sLabel, " / ".join(aValues), sTag)

    def labelled_exp_list(self, sLabel, dValues, sTag):
        """Special case for expansion labels"""
        aValues = []
        for sExp in sorted(dValues):
            aRarities = list(set(dValues[sExp]))
            # Use set to avoid Precon, Precon and other duplicates
            sValue = '%s (%s)' % (sExp, ", ".join(sorted(aRarities)))
            # sort for consistent ordering
            aValues.append(sValue)
        self.labelled_list(sLabel, aValues, sTag)

    def reset_iter(self):
        """Reset the iterator to point at the start of the buffer."""
        self._oIter = self.get_iter_at_offset(0)

    def get_cur_iter(self):
        """Get the current text iter position"""
        return self._oIter

    def set_cur_iter(self, oNewIter):
        """Set the current text iter to the given position"""
        self._oIter = oNewIter

    def set_cur_iter_to_mark(self, sMarkName):
        """Set the iter to the position of the given mark"""
        oMark = self.get_mark(sMarkName)
        if oMark:
            self._oIter = self.get_iter_at_mark(oMark)

    def get_all_text(self):
        """Get everything shown in the buffer"""
        oStart, oEnd = self.get_bounds()
        # This should be unicode
        return self.get_text(oStart, oEnd, False)


class BaseCardTextView(Gtk.TextView):
    """Base class for TextView widget which holds the TextBuffer."""

    # pylint: disable=too-many-public-methods
    # Gtk.Widget, so many public methods
    def __init__(self, oBuffer, oIconManager, oMainWindow):
        super().__init__()
        # Can be styled as frame_name.view
        self._oBuf = oBuffer
        # Reference to top level so we can get config info and so on
        self._oMainWindow = oMainWindow
        self._oNameOffset = None
        # Allow easy reparsing of the card if needed
        self._oLastCard = None

        self.set_buffer(self._oBuf)
        self.set_editable(False)
        self.set_cursor_visible(False)
        self.set_wrap_mode(Gtk.WrapMode.WORD)
        self._oIconManager = oIconManager
        oContext = self.get_pango_context()
        logging.info('Pango Language : %s',
                     oContext.get_language().to_string())
        logging.info('Pango Font Description : %s',
                     oContext.get_font_description().to_string())

    # pylint: disable=protected-access
    # We allow access via these properties

    text_buffer = property(fget=lambda self: self._oBuf,
                           doc="Return reference to text buffer")

    # pylint: enable=protected-access

    def update_to_new_db(self):
        """Handle any database changes as required"""
        # The default is to do nothing.
        # Subclasses will implement logic as needed

    def set_card_text(self, oPhysCard):
        """Add the text for oCard to the TextView."""
        self._oLastCard = oPhysCard
        self._reload_card()

    def _reload_card(self):
        if self._oLastCard:
            self.clear_text()
            self.print_card_to_buffer(self._oLastCard.abstractCard)
            # Signal plugins that want to do something after text has been
            # updated
            MessageBus.publish(MessageBus.Type.CARD_TEXT_MSG, 'post_set_text',
                               self._oLastCard)

    def add_button_to_text(self, oButton, sPrefix='\n'):
        """Adds a button to the text view."""
        if oButton in self.get_children():
            return
        # We insert buttons after the card name
        oPos = self._oBuf.get_iter_at_line_offset(0, self._oNameOffset)
        self._oBuf.insert(oPos, sPrefix)
        oAnchor = self._oBuf.create_child_anchor(oPos)
        self.add_child_at_anchor(oButton, oAnchor)
        oButton.show()

    def clear_text(self):
        """Clear the text buffer."""
        # This is available as sometimes needed to ensure the state
        # of the text frame is sane (adding / removing from main window,
        # etc.)
        for oChild in self.get_children():
            self.remove(oChild)
        oStart, oEnd = self._oBuf.get_bounds()
        self._oBuf.delete(oStart, oEnd)

    def print_card_to_buffer(self, oCard):
        """Format the text for the card and add it to the buffer."""
        self._oBuf.reset_iter()

        self._oBuf.tag_text(oCard.name, "card_name")

        self._oNameOffset = self._oBuf.get_end_iter().get_offset()

        # subclasses will do the rest
