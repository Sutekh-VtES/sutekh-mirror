# CardTextView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Widget for displaying the card text for the given card."""

import gtk
import pango

class CardTextBuffer(gtk.TextBuffer, object):
    """Buffer object which holds the actual card text.

       This is also responsible for nicely formatting the output.
       """
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    def __init__(self):
        super(CardTextBuffer, self).__init__(None)

        # See http://www.pygtk.org/pygtk2reference/class-gtktexttag.html
        # for some possible properties

        oIconTabs = pango.TabArray(1, True)
        oIconTabs.set_tab(0, pango.TAB_LEFT, 15) # Icons are scaled to 15'ish

        self.create_tag("label", underline=pango.UNDERLINE_SINGLE)

        self.create_tag("card_name", weight=pango.WEIGHT_BOLD)
        self.create_tag("cost", style=pango.STYLE_ITALIC)
        self.create_tag("life", style=pango.STYLE_ITALIC)
        self.create_tag("capacity", style=pango.STYLE_ITALIC)
        self.create_tag("group", style=pango.STYLE_ITALIC)
        self.create_tag("level", style=pango.STYLE_ITALIC)
        self.create_tag("burn_option", style=pango.STYLE_ITALIC)
        self.create_tag("card_type", style=pango.STYLE_ITALIC, left_margin=15,
                tabs=oIconTabs)
        self.create_tag("clan", style=pango.STYLE_ITALIC, left_margin=15,
                tabs=oIconTabs)
        self.create_tag("sect", style=pango.STYLE_ITALIC)
        self.create_tag("title", style=pango.STYLE_ITALIC)
        self.create_tag("creed", style=pango.STYLE_ITALIC, left_margin=15,
                tabs=oIconTabs)
        self.create_tag("discipline", style=pango.STYLE_ITALIC, left_margin=15,
                tabs=oIconTabs)
        self.create_tag("virtue", style=pango.STYLE_ITALIC, left_margin=15,
                tabs=oIconTabs)
        self.create_tag("expansion", style=pango.STYLE_ITALIC, left_margin=15,
                tabs=oIconTabs)
        self.create_tag("ruling", left_margin=15,
                tabs=oIconTabs)
        self.create_tag("card_text", style=pango.STYLE_ITALIC)
        self._oIter = None

    # pylint: disable-msg=W0142
    # ** magic OK here
    def tag_text(self, *aArgs, **kwargs):
        """Inset the text (possibly with tags) at the current position"""
        self.insert_with_tags_by_name(self._oIter, *aArgs, **kwargs)

    # pylint: enable-msg=W0142

    def labelled_value(self, sLabel, sValue, sTag, oIcon=None):
        """Add a single value to the buffer."""
        self.tag_text("\n")
        self.tag_text(sLabel, "label")
        self.tag_text(": ")
        if oIcon:
            self.insert_pixbuf(self._oIter, oIcon)
            self.insert(self._oIter, ' ')
        self.tag_text(sValue, sTag)

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


class CardTextView(gtk.TextView, object):
    """TextView widget which holds the TextBuffer.

       This handles extracting the text from the database for the card,
       and feeding it to the buffer in suitable chunks.
       """
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    def __init__(self, oController, oIconManager, bVerbose):
        super(CardTextView, self).__init__()
        # Can be styled as frame_name.view
        self.__oController = oController
        self.__oBuf = CardTextBuffer()

        self.set_buffer(self.__oBuf)
        self.set_editable(False)
        self.set_cursor_visible(False)
        self.set_wrap_mode(gtk.WRAP_WORD)
        self._oIconManager = oIconManager
        if bVerbose:
            oContext = self.get_pango_context()
            print 'Pango Language : ', oContext.get_language()
            print 'Pango Font Description : ', oContext.get_font_description()

    def set_card_text(self, oCard):
        """Add the text for oCard to the TextView."""
        oStart, oEnd = self.__oBuf.get_bounds()
        self.__oBuf.delete(oStart, oEnd)
        self.print_card_to_buffer(oCard)

    # pylint: disable-msg=R0912, R0915
    # We need to consider all cases for oCard, so need the branches
    # and statements
    def print_card_to_buffer(self, oCard):
        """Format the text for the card and add it to the buffer."""
        self.__oBuf.reset_iter()

        self.__oBuf.tag_text(oCard.name, "card_name")

        if not oCard.cost is None:
            if oCard.cost == -1:
                sCost = "X " + str(oCard.costtype)
            else:
                sCost = str(oCard.cost) + " " + str(oCard.costtype)
            self.__oBuf.labelled_value("Cost", sCost, "cost")

        if not oCard.capacity is None:
            self.__oBuf.labelled_value("Capacity", str(oCard.capacity),
                    "capacity")

        if not oCard.life is None:
            self.__oBuf.labelled_value("Life", str(oCard.life), "life")

        if not oCard.group is None:
            if oCard.group == -1:
                sGroup = 'Any'
            else:
                sGroup = str(oCard.group)
            self.__oBuf.labelled_value("Group", sGroup, "group")

        if not oCard.level is None:
            oIcon = self._oIconManager.get_icon_by_name('advanced')
            self.__oBuf.labelled_value("Level", str(oCard.level), "level",
                    oIcon)

        if len(oCard.cardtype) == 0:
            aTypes = ["Unknown"]
        else:
            aTypes = [oT.name for oT in oCard.cardtype]
        dIcons = self._oIconManager.get_icon_list(oCard.cardtype)
        self.__oBuf.labelled_list("Card Type", aTypes, "card_type", dIcons)

        if oCard.burnoption:
            oIcon = self._oIconManager.get_icon_by_name('burn option')
            self.__oBuf.labelled_value("Burn Option:", "Yes", "burn_option",
                    oIcon)

        if not len(oCard.clan) == 0:
            dIcons = self._oIconManager.get_icon_list(oCard.clan)
            self.__oBuf.labelled_list("Clan",
                    [oC.name for oC in oCard.clan], "clan", dIcons)

        if not len(oCard.creed) == 0:
            dIcons = self._oIconManager.get_icon_list(oCard.creed)
            self.__oBuf.labelled_list("Creed",
                    [oC.name for oC in oCard.creed], "creed", dIcons)

        if not len(oCard.sect) == 0:
            self.__oBuf.labelled_compact_list("Sect",
                    [oC.name for oC in oCard.sect], "sect")

        if not len(oCard.title) == 0:
            self.__oBuf.labelled_compact_list("Title",
                    [oC.name for oC in oCard.title], "title")

        if not len(oCard.discipline) == 0:
            aDis = []
            aDis.extend(sorted([oP.discipline.name.upper() for oP in
                oCard.discipline if oP.level == 'superior']))
            aDis.extend(sorted([oP.discipline.name for oP in oCard.discipline
                if oP.level != 'superior']))
            dIcons = self._oIconManager.get_icon_list(oCard.discipline)
            self.__oBuf.labelled_list("Disciplines", aDis, "discipline",
                    dIcons)

        if not len(oCard.virtue) == 0:
            dIcons = self._oIconManager.get_icon_list(oCard.virtue)
            self.__oBuf.labelled_list("Virtue",
                    [oC.name for oC in oCard.virtue], "virtue", dIcons)

        if not len(oCard.rarity) == 0:
            dExp = {}
            for oPair in oCard.rarity:
                dExp.setdefault(oPair.expansion.name, [])
                dExp[oPair.expansion.name].append(oPair.rarity.name)
            self.__oBuf.labelled_exp_list("Expansions", dExp, "expansion")

        if not len(oCard.rulings) == 0:
            aRulings = [oR.text.replace("\n", " ") + " " + oR.code for oR
                    in oCard.rulings]
            self.__oBuf.labelled_list("Rulings", aRulings, "ruling")

        self.__oBuf.tag_text("\n\n")
        self.__oBuf.tag_text(oCard.text.replace("\n", " "),
                "card_text")
