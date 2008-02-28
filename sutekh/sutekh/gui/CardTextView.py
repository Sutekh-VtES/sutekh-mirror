# CardTextView.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

import gtk
import pango

class CardTextBuffer(gtk.TextBuffer, object):
    def __init__(self):
        super(CardTextBuffer, self).__init__(None)
        tags = []

        # See http://www.pygtk.org/pygtk2reference/class-gtktexttag.html
        # for some possible properties

        tags.append(self.create_tag("label", underline=pango.UNDERLINE_SINGLE))

        tags.append(self.create_tag("card_name", weight=pango.WEIGHT_BOLD))
        tags.append(self.create_tag("cost", style=pango.STYLE_ITALIC))
        tags.append(self.create_tag("life", style=pango.STYLE_ITALIC))
        tags.append(self.create_tag("capacity", style=pango.STYLE_ITALIC))
        tags.append(self.create_tag("group", style=pango.STYLE_ITALIC))
        tags.append(self.create_tag("level", style=pango.STYLE_ITALIC))
        tags.append(self.create_tag("burn_option", style=pango.STYLE_ITALIC))
        tags.append(self.create_tag("card_type", style=pango.STYLE_ITALIC))
        tags.append(self.create_tag("clan", style=pango.STYLE_ITALIC))
        tags.append(self.create_tag("sect", style=pango.STYLE_ITALIC))
        tags.append(self.create_tag("title", style=pango.STYLE_ITALIC))
        tags.append(self.create_tag("creed", style=pango.STYLE_ITALIC))
        tags.append(self.create_tag("discipline", style=pango.STYLE_ITALIC))
        tags.append(self.create_tag("virtue", style=pango.STYLE_ITALIC))
        tags.append(self.create_tag("expansion", style=pango.STYLE_ITALIC))
        tags.append(self.create_tag("ruling"))
        tags.append(self.create_tag("card_text", style=pango.STYLE_ITALIC))

    def tagText(self, *args, **kwargs):
        self.insert_with_tags_by_name(self._oIter, *args, **kwargs)

    def labelledValue(self, sLabel, sValue, sTag):
        self.tagText("\n")
        self.tagText(sLabel, "label")
        self.tagText(": ")
        self.tagText(sValue, sTag)

    def labelledList(self, sLabel, aValues, sTag):
        self.tagText("\n")
        self.tagText(sLabel, "label")
        self.tagText(":")
        for sValue in aValues:
            self.tagText("\n\t* ")
            self.tagText(sValue, sTag)

    def resetIter(self):
        self._oIter = self.get_iter_at_offset(0)

class CardTextView(gtk.TextView, object):
    def __init__(self, oController):
        super(CardTextView, self).__init__()
        # Can be styled as frame_name.view
        self.__oC = oController
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

        oBuf.tagText(oCard.name, "card_name")

        if not oCard.cost is None:
            if oCard.cost == -1:
                sCost = "X " + str(oCard.costtype)
            else:
                sCost = str(oCard.cost) + " " + str(oCard.costtype)
            oBuf.labelledValue("Cost", sCost, "cost")

        if not oCard.capacity is None:
            oBuf.labelledValue("Capacity", str(oCard.capacity), "capacity")

        if not oCard.life is None:
            oBuf.labelledValue("Life", str(oCard.life), "life")

        if not oCard.group is None:
            oBuf.labelledValue("Group", str(oCard.group), "group")

        if not oCard.level is None:
            oBuf.labelledValue("Level", str(oCard.level), "level")

        if len(oCard.cardtype) == 0:
            aTypes = ["Unknown"]
        else:
            aTypes = [oT.name for oT in oCard.cardtype]
        oBuf.labelledList("Card Type", aTypes, "card_type")

        if oCard.burnoption:
            oBuf.labelledValue("Burn Option:", "Yes", "burn_option")

        if not len(oCard.clan) == 0:
            aClans = [oC.name for oC in oCard.clan]
            oBuf.labelledList("Clan", aClans, "clan")

        if not len(oCard.creed) == 0:
            aCreeds = [oC.name for oC in oCard.creed]
            oBuf.labelledList("Creed", aCreeds, "creed")

        if not len(oCard.sect) == 0:
            aSects = [oC.name for oC in oCard.sect]
            oBuf.labelledList("Sect", aSects, "sect")

        if not len(oCard.title) == 0:
            aTitles = [oC.name for oC in oCard.title]
            oBuf.labelledList("Title", aTitles, "title")

        if not len(oCard.discipline) == 0:
            aDis = []
            aDis.extend([oP.discipline.name.upper() for oP in oCard.discipline if oP.level == 'superior'])
            aDis.extend([oP.discipline.name for oP in oCard.discipline if oP.level != 'superior'])
            oBuf.labelledList("Disciplines", aDis, "discipline")

        if not len(oCard.virtue) == 0:
            aVirtues = [oC.name for oC in oCard.virtue]
            oBuf.labelledList("Virtue", aVirtues, "virtue")

        if not len(oCard.rarity) == 0:
            aExp = [oP.expansion.name + " (" + oP.rarity.name + ")" for oP in oCard.rarity]
            oBuf.labelledList("Expansions", aExp, "expansion")

        if not len(oCard.rulings) == 0:
            aRulings = [oR.text.replace("\n", " ") + " " + oR.code for oR in oCard.rulings]
            oBuf.labelledList("Rulings", aRulings, "ruling")

        oBuf.tagText("\n\n")
        oBuf.tagText(oCard.text.replace("\n", " "), "card_text")
