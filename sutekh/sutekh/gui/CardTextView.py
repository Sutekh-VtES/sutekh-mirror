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

        self.create_tag("label", underline=pango.UNDERLINE_SINGLE)

        self.create_tag("card_name", weight=pango.WEIGHT_BOLD)
        self.create_tag("cost", style=pango.STYLE_ITALIC)
        self.create_tag("life", style=pango.STYLE_ITALIC)
        self.create_tag("capacity", style=pango.STYLE_ITALIC)
        self.create_tag("group", style=pango.STYLE_ITALIC)
        self.create_tag("level", style=pango.STYLE_ITALIC)
        self.create_tag("burn_option", style=pango.STYLE_ITALIC)
        self.create_tag("card_type", style=pango.STYLE_ITALIC)
        self.create_tag("clan", style=pango.STYLE_ITALIC)
        self.create_tag("sect", style=pango.STYLE_ITALIC)
        self.create_tag("title", style=pango.STYLE_ITALIC)
        self.create_tag("creed", style=pango.STYLE_ITALIC)
        self.create_tag("discipline", style=pango.STYLE_ITALIC)
        self.create_tag("virtue", style=pango.STYLE_ITALIC)
        self.create_tag("expansion", style=pango.STYLE_ITALIC)
        self.create_tag("ruling")
        self.create_tag("card_text", style=pango.STYLE_ITALIC)

    # pylint: disable-msg=W0142
    # ** magic K here
    def tag_text(self, *aArgs, **kwargs):
        """Inset the text (possibly with tags) at the current position"""
        self.insert_with_tags_by_name(self._oIter, *aArgs, **kwargs)

    # pylint: enable-msg=W0142

    def labelled_value(self, sLabel, sValue, sTag):
        """Add a single value to the buffer."""
        self.tag_text("\n")
        self.tag_text(sLabel, "label")
        self.tag_text(": ")
        self.tag_text(sValue, sTag)

    def labelled_list(self, sLabel, aValues, sTag):
        """Add a list of values to the Buffer"""
        self.tag_text("\n")
        self.tag_text(sLabel, "label")
        self.tag_text(":")
        for sValue in aValues:
            self.tag_text("\n\t* ")
            self.tag_text(sValue, sTag)

    def resetIter(self):
        self._oIter = self.get_iter_at_offset(0)

class CardTextView(gtk.TextView, object):
    """TextView widget which holds the TextBuffer.

       This handles extracting the text from the database for the card,
       and feeding it to the buffer in suitable chunks.
       """
    # pylint: disable-msg=R0904
    # gtk.Widget, so many public methods
    def __init__(self, oController):
        super(CardTextView, self).__init__()
        # Can be styled as frame_name.view
        self.__oController = oController
        self.__oBuf = CardTextBuffer()

        self.set_buffer(self.__oBuf)
        self.set_editable(False)
        self.set_cursor_visible(False)
        self.set_wrap_mode(gtk.WRAP_WORD)

    def set_card_text(self, oCard):
        oStart, oEnd = self.__oBuf.get_bounds()
        self.__oBuf.delete(oStart, oEnd)
        self.printCardToBuffer(oCard, self.__oBuf)

    def printCardToBuffer(self, oCard, oBuf):
        oBuf.resetIter()

        oBuf.tag_text(oCard.name, "card_name")

        if not oCard.cost is None:
            if oCard.cost == -1:
                sCost = "X " + str(oCard.costtype)
            else:
                sCost = str(oCard.cost) + " " + str(oCard.costtype)
            oBuf.labelled_value("Cost", sCost, "cost")

        if not oCard.capacity is None:
            oBuf.labelled_value("Capacity", str(oCard.capacity), "capacity")

        if not oCard.life is None:
            oBuf.labelled_value("Life", str(oCard.life), "life")

        if not oCard.group is None:
            oBuf.labelled_value("Group", str(oCard.group), "group")

        if not oCard.level is None:
            oBuf.labelled_value("Level", str(oCard.level), "level")

        if len(oCard.cardtype) == 0:
            aTypes = ["Unknown"]
        else:
            aTypes = [oT.name for oT in oCard.cardtype]
        oBuf.labelled_list("Card Type", aTypes, "card_type")

        if oCard.burnoption:
            oBuf.labelled_value("Burn Option:", "Yes", "burn_option")

        if not len(oCard.clan) == 0:
            aClans = [oC.name for oC in oCard.clan]
            oBuf.labelled_list("Clan", aClans, "clan")

        if not len(oCard.creed) == 0:
            aCreeds = [oC.name for oC in oCard.creed]
            oBuf.labelled_list("Creed", aCreeds, "creed")

        if not len(oCard.sect) == 0:
            aSects = [oC.name for oC in oCard.sect]
            oBuf.labelled_list("Sect", aSects, "sect")

        if not len(oCard.title) == 0:
            aTitles = [oC.name for oC in oCard.title]
            oBuf.labelled_list("Title", aTitles, "title")

        if not len(oCard.discipline) == 0:
            aDis = []
            aDis.extend([oP.discipline.name.upper() for oP in oCard.discipline
                if oP.level == 'superior'])
            aDis.extend([oP.discipline.name for oP in oCard.discipline if
                oP.level != 'superior'])
            oBuf.labelled_list("Disciplines", aDis, "discipline")

        if not len(oCard.virtue) == 0:
            aVirtues = [oC.name for oC in oCard.virtue]
            oBuf.labelled_list("Virtue", aVirtues, "virtue")

        if not len(oCard.rarity) == 0:
            aExp = [oP.expansion.name + " (" + oP.rarity.name + ")" for oP
                    in oCard.rarity]
            oBuf.labelled_list("Expansions", aExp, "expansion")

        if not len(oCard.rulings) == 0:
            aRulings = [oR.text.replace("\n", " ") + " " + oR.code for oR
                    in oCard.rulings]
            oBuf.labelled_list("Rulings", aRulings, "ruling")

        oBuf.tag_text("\n\n")
        oBuf.tag_text(oCard.text.replace("\n", " "), "card_text")
