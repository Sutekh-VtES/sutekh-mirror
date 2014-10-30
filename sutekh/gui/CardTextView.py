# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2005, 2006, 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Widget for displaying the card text for the given card."""

from sutekh.SutekhUtility import format_text
from sutekh.base.gui.BaseCardTextView import (BaseCardTextBuffer,
                                              BaseCardTextView)


class CardTextBuffer(BaseCardTextBuffer):
    """Buffer object which holds the actual card text.

       This is also responsible for nicely formatting the output.
       """

    # pylint: disable=R0904
    # gtk.Widget, so many public methods
    def __init__(self):
        super(CardTextBuffer, self).__init__()

        # See http://www.pygtk.org/pygtk2reference/class-gtktexttag.html
        # for some possible properties

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


class CardTextView(BaseCardTextView):
    """TextView widget which holds the TextBuffer.

       This handles extracting the text from the database for the card,
       and feeding it to the buffer in suitable chunks.
       """

    # pylint: disable=R0904
    # gtk.Widget, so many public methods
    def __init__(self, oIconManager):
        oBuffer = CardTextBuffer()
        super(CardTextView, self).__init__(oBuffer, oIconManager)

    # pylint: disable=R0912, R0915
    # We need to consider all cases for oCard, so need the branches
    # and statements
    def print_card_to_buffer(self, oCard):
        """Format the text for the card and add it to the buffer."""
        super(CardTextView, self).print_card_to_buffer(oCard)

        if oCard.cost is not None:
            if oCard.cost == -1:
                sCost = "X " + str(oCard.costtype)
            else:
                sCost = str(oCard.cost) + " " + str(oCard.costtype)
            self._oBuf.labelled_value("Cost", sCost, "cost")

        if oCard.capacity is not None:
            self._oBuf.labelled_value("Capacity", str(oCard.capacity),
                                      "capacity")

        if oCard.life is not None:
            self._oBuf.labelled_value("Life", str(oCard.life), "life")

        if oCard.group is not None:
            if oCard.group == -1:
                sGroup = 'Any'
            else:
                sGroup = str(oCard.group)
            self._oBuf.labelled_value("Group", sGroup, "group")

        if oCard.level is not None:
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
                oIcon = self._oIconManager.get_icon_by_name(oItem.keyword)
                dIcons[oItem.keyword] = oIcon
                aInfo.append(oItem.keyword)
            self._oBuf.labelled_list("Keywords:", aInfo,
                                     "keywords", dIcons)

        if not len(oCard.clan) == 0:
            dIcons = self._oIconManager.get_icon_list(oCard.clan)
            self._oBuf.labelled_list("Clan",
                                     [oC.name for oC in oCard.clan],
                                     "clan", dIcons)

        if not len(oCard.creed) == 0:
            dIcons = self._oIconManager.get_icon_list(oCard.creed)
            self._oBuf.labelled_list("Creed",
                                     [oC.name for oC in oCard.creed],
                                     "creed", dIcons)

        if not len(oCard.sect) == 0:
            self._oBuf.labelled_compact_list("Sect",
                                             [oC.name for oC in oCard.sect],
                                             "sect")

        if not len(oCard.title) == 0:
            self._oBuf.labelled_compact_list("Title",
                                             [oC.name for oC in oCard.title],
                                             "title")

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
                                     [oC.name for oC in oCard.virtue],
                                     "virtue", dIcons)

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
                                     [oA.name for oA in oCard.artists],
                                     "artist")
