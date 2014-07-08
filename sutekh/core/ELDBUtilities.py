# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Utility functions for importing from & exporting to FELDB"""

import unicodedata
from sutekh.base.core.BaseObjects import AbstractCard
from sutekh.base.Utility import move_articles_to_back
from sutekh.SutekhUtility import is_crypt_card

SINGLE_QUOTE_NAMES = [
        "Al-Muntathir, God's Witness",
        "Crypt's Sons",
        "Poacher's Hunting Ground",
        "World's a Canvas, The",
        "Joumlon's Axe",
        "Mole's Tunneling",
        "Three's a Crowd",
        "Unleash Hell's Fury",
        ]


def type_of_card(oCard):
    """Return either Crypt or Library as required."""
    if is_crypt_card(oCard):
        return "Crypt"
    else:
        return "Library"


def norm_name(oCard):
    """Transform a card name to the ELDB equivalent"""
    sName = oCard.name
    sType = oCard.cardtype[0].name
    if oCard.level is not None:
        sName = sName.replace("(Advanced)", "(ADV)")
    # Handle annoying ELDB special cases
    if sName != "The Kikiyaon":
        sName = move_articles_to_back(sName)
    if sType == 'Imbued' or sName == 'Ondine "Boudicca" Sinclair':
        # These are quoted differently from other ELDB names
        sName = sName.replace('"', "'")
    elif sName not in SINGLE_QUOTE_NAMES:
        # usual ELDB quoting
        sName = sName.replace('"', "`")
        sName = sName.replace("'", "`")
    return unicodedata.normalize('NFKD', sName).encode('ascii', 'ignore')


def gen_name_lookups():
    """Create a lookup table to map ELDB names to Sutekh names -
       reduces the number of user queries"""
    dNameCache = {}
    for oCard in AbstractCard.select():
        sSutekhName = oCard.name
        sELDBName = norm_name(oCard)
        if sELDBName != sSutekhName:
            # Since we will need to check wether a card is in the dictionary
            # anyway (missed cases, etc), there's no point in having the
            # identity entries
            dNameCache[sELDBName] = sSutekhName
    return dNameCache
