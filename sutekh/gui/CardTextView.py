# CardTextView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Widget for displaying the card text for the given card."""

import gtk
import pango
import logging
from sutekh.core.SutekhObjects import IKeyword
from sutekh.SutekhUtility import format_text
from sqlobject import SQLObjectNotFound


class CardTextViewListener(object):
    """Listens to changes, i.e. .set_card_text(...) to CardListViews."""
    def set_card_text(self, oPhysCard):
        """The CardListView has called set_card_text on the CardText pane"""
        pass


class CardTextBuffer(gtk.TextBuffer):
    """Buffer object which holds the actual card text.

       This is also responsible for nicely formatting the output.
       """

    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    def __init__(self):
        super(CardTextBuffer, self).__init__(None)

        # See http://www.pygtk.org/pygtk2reference/class-gtktexttag.html
        # for some possible properties

        self._oIconTabs = pango.TabArray(1, True)
        # Icons are scaled to 15'ish
        self._oIconTabs.set_tab(0, pango.TAB_LEFT, 15)

        self.create_tag("label", underline=pango.UNDERLINE_SINGLE)

        self.create_tag("card_name", weight=pango.WEIGHT_BOLD)

        # We use add_tag, so each tag has an associated mark, which will be
        # set to immediately after the text inserted with this tag
        self.add_tag('cost')
        self.add_tag('life')
        self.add_tag('capacity')
        self.add_tag('group')
        self.add_tag('level')
        self.add_tag("sect")
        self.add_tag("title")
        self.add_list_tag('keywords')
        self.add_list_tag("card_type")
        self.add_list_tag("clan")
        self.add_list_tag("creed")
        self.add_list_tag("discipline")
        self.add_list_tag("virtue")
        self.add_list_tag("expansion")
        self.create_tag("ruling", left_margin=15, tabs=self._oIconTabs)
        self.create_mark("ruling", self.get_start_iter(), True)
        self.add_tag("card_text")
        self.add_list_tag("artist")
        self._oIter = None

    # pylint: disable-msg=W0142
    # ** magic OK here
    def tag_text(self, *aArgs, **kwargs):
        """Inset the text (possibly with tags) at the current position"""
        self.insert_with_tags_by_name(self._oIter, *aArgs, **kwargs)

    # pylint: enable-msg=W0142

    # Methods for adding new tags to the buffer

    def add_tag(self, sTag):
        """Add a simple tag"""
        self.create_tag(sTag, style=pango.STYLE_ITALIC)
        self.create_mark(sTag, self.get_start_iter(), True)

    def add_list_tag(self, sTag):
        """Add a tag with the list style indents"""
        self.create_tag(sTag, style=pango.STYLE_ITALIC, left_margin=15,
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
                if dIcons.has_key(sValue) and dIcons[sValue]:
                    _insert_line(sValue, sTag, dIcons[sValue])
                elif dIcons.has_key(sValue.lower()) and dIcons[sValue.lower()]:
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


class CardTextView(gtk.TextView):
    """TextView widget which holds the TextBuffer.

       This handles extracting the text from the database for the card,
       and feeding it to the buffer in suitable chunks.
       """

    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    def __init__(self, oController, oIconManager):
        super(CardTextView, self).__init__()
        # Can be styled as frame_name.view
        self.__oController = oController
        self._oBuf = CardTextBuffer()

        self.set_buffer(self._oBuf)
        self.set_editable(False)
        self.set_cursor_visible(False)
        self.set_wrap_mode(gtk.WRAP_WORD)
        self._oIconManager = oIconManager
        oContext = self.get_pango_context()
        logging.info('Pango Language : %s', oContext.get_language())
        logging.info('Pango Font Description : %s',
                oContext.get_font_description())
        self._oBurnOption = None
        self._oAdvanced = None
        self.update_to_new_db()  # lookup burn option
        self.dListeners = {}  # dictionary of CardTextViewListeners

    # pylint: disable-msg=W0212
    # We allow access via these properties

    text_buffer = property(fget=lambda self: self._oBuf,
            doc="Return reference to text buffer")

    # pylint: enable-msg=W0212

    # Listener helper functions

    def add_listener(self, oListener):
        """Add a listener to the list."""
        self.dListeners[oListener] = None

    def remove_listener(self, oListener):
        """Remove a listener from the list."""
        del self.dListeners[oListener]

    def update_to_new_db(self):
        """Cached lookup of the burn option keyword"""
        # Burn option is a special case because of the icon, so we test for it
        # a lot, so we cache the result
        # Likewise, we cache advanced
        # we can't do this during import, because we're not assured that the
        # database exists yet
        try:
            self._oBurnOption = IKeyword('burn option')
        except SQLObjectNotFound:
            # protect against burn option being missing from the database
            self._oBurnOption = None
            logging.warn("Keyword 'burn option' not present in database.")

        try:
            self._oAdvanced = IKeyword('advanced')
        except SQLObjectNotFound:
            # protect against advanced being missing
            self._oAdvanced = None
            logging.warn("Keyword 'advanced' not present in database.")

    def set_card_text(self, oPhysCard):
        """Add the text for oCard to the TextView."""
        oStart, oEnd = self._oBuf.get_bounds()
        self._oBuf.delete(oStart, oEnd)
        self.print_card_to_buffer(oPhysCard.abstractCard)
        for oListener in self.dListeners:
            oListener.set_card_text(oPhysCard)

    # pylint: disable-msg=R0912, R0915
    # We need to consider all cases for oCard, so need the branches
    # and statements
    def print_card_to_buffer(self, oCard):
        """Format the text for the card and add it to the buffer."""
        self._oBuf.reset_iter()

        self._oBuf.tag_text(oCard.name, "card_name")

        if not oCard.cost is None:
            if oCard.cost == -1:
                sCost = "X " + str(oCard.costtype)
            else:
                sCost = str(oCard.cost) + " " + str(oCard.costtype)
            self._oBuf.labelled_value("Cost", sCost, "cost")

        if not oCard.capacity is None:
            self._oBuf.labelled_value("Capacity", str(oCard.capacity),
                    "capacity")

        if not oCard.life is None:
            self._oBuf.labelled_value("Life", str(oCard.life), "life")

        if not oCard.group is None:
            if oCard.group == -1:
                sGroup = 'Any'
            else:
                sGroup = str(oCard.group)
            self._oBuf.labelled_value("Group", sGroup, "group")

        if not oCard.level is None:
            oIcon = self._oIconManager.get_icon_by_name('advanced')
            self._oBuf.labelled_value("Level", str(oCard.level), "level",
                    oIcon)

        if len(oCard.cardtype) == 0:
            aInfo = ["Unknown"]
        else:
            aInfo = [oT.name for oT in oCard.cardtype]
        dIcons = self._oIconManager.get_icon_list(oCard.cardtype)
        self._oBuf.labelled_list("Card Type", aInfo, "card_type", dIcons)

        if len(oCard.keywords) != 0:
            dIcons = {}
            aInfo = []
            for oItem in oCard.keywords:
                if self._oBurnOption == oItem:
                    oIcon = self._oIconManager.get_icon_by_name('burn option')
                elif self._oAdvanced == oItem:
                    oIcon = self._oIconManager.get_icon_by_name('advanced')
                else:
                    oIcon = None
                dIcons[oItem.keyword] = oIcon
                aInfo.append(oItem.keyword)
            self._oBuf.labelled_list("Keywords:", aInfo,
                    "keywords", dIcons)

        if not len(oCard.clan) == 0:
            dIcons = self._oIconManager.get_icon_list(oCard.clan)
            self._oBuf.labelled_list("Clan",
                    [oC.name for oC in oCard.clan], "clan", dIcons)

        if not len(oCard.creed) == 0:
            dIcons = self._oIconManager.get_icon_list(oCard.creed)
            self._oBuf.labelled_list("Creed",
                    [oC.name for oC in oCard.creed], "creed", dIcons)

        if not len(oCard.sect) == 0:
            self._oBuf.labelled_compact_list("Sect",
                    [oC.name for oC in oCard.sect], "sect")

        if not len(oCard.title) == 0:
            self._oBuf.labelled_compact_list("Title",
                    [oC.name for oC in oCard.title], "title")

        if not len(oCard.discipline) == 0:
            aInfo = []
            aInfo.extend(sorted([oP.discipline.name for oP in oCard.discipline
                if oP.level != 'superior']))
            aInfo.extend(sorted([oP.discipline.name.upper() for oP in
                oCard.discipline if oP.level == 'superior']))
            dIcons = self._oIconManager.get_icon_list(oCard.discipline)
            self._oBuf.labelled_list("Disciplines", aInfo, "discipline",
                    dIcons)

        if not len(oCard.virtue) == 0:
            dIcons = self._oIconManager.get_icon_list(oCard.virtue)
            self._oBuf.labelled_list("Virtue",
                    [oC.name for oC in oCard.virtue], "virtue", dIcons)

        self._oBuf.tag_text("\n\n")
        self._oBuf.tag_text(format_text(oCard.text),
                "card_text")

        if not len(oCard.rulings) == 0:
            self._oBuf.tag_text("\n")
            aInfo = [oR.text.replace("\n", " ") + " " + oR.code for oR
                    in oCard.rulings]
            self._oBuf.labelled_list("Rulings", aInfo, "ruling")

        if not len(oCard.rarity) == 0:
            self._oBuf.tag_text("\n")
            dExp = {}
            for oPair in oCard.rarity:
                dExp.setdefault(oPair.expansion.name, [])
                dExp[oPair.expansion.name].append(oPair.rarity.name)
            self._oBuf.labelled_exp_list("Expansions", dExp, "expansion")

        if len(oCard.artists) > 0:
            self._oBuf.tag_text("\n")
            self._oBuf.labelled_list("Artists",
                    [oA.name for oA in oCard.artists], "artist")
