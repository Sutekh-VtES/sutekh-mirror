# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2006 Simon Cross <hodgestar@gmail.com>
# Copyright 2006 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details
# Misc Useful functions needed in several places. Mainly to do with database
# management. Seperated out from SutekhCli and other places, NM, 2006

"""Misc functions needed in various places in Sutekh."""

import re

from sutekh.base.Utility import move_articles_to_back, gen_app_temp_dir
from sutekh.base.io.IOBase import safe_parser
from sutekh.base.io.LookupCSVParser import LookupCSVParser

from sutekh.core.SutekhObjects import CRYPT_TYPES

from sutekh.io.WhiteWolfTextParser import WhiteWolfTextParser
from sutekh.io.RulingParser import RulingParser
from sutekh.io.ExpDateCSVParser import ExpDateCSVParser


def read_white_wolf_list(oFile, oLogHandler=None):
    """Parse in a new White Wolf cardlist

       oFile is an object with a .open() method (e.g.
       sutekh.base.io.EncodedFile.EncodedFile)
       """
    oParser = WhiteWolfTextParser(oLogHandler)
    safe_parser(oFile, oParser)


def read_rulings(oFile, oLogHandler=None):
    """Parse a new White Wolf rulings file

       oFil is an object with a .open() method (e.g. a
       sutekh.base.io.EncodedFile.EncodedFile)
       """
    oParser = RulingParser(oLogHandler)
    safe_parser(oFile, oParser)


def read_exp_date_list(oFile, oLogHandler=None):
    """Read the expansion date information from the given file.

       oFile is an object with a .open() method (e.g. a
       sutekh.base.io.EncodedFile.EncodedFile)
       """
    oParser = ExpDateCSVParser(oLogHandler)
    safe_parser(oFile, oParser)


def read_lookup_data(oFile, oLogHandler=None):
    """Read the lookup data information from the given file.

       oFile is an object with a .open() method (e.g. a
       sutekh.base.io.EncodedFile.EncodedFile)
       """
    oParser = LookupCSVParser(oLogHandler)
    safe_parser(oFile, oParser)


def gen_temp_dir():
    """Create a temporary directory using mkdtemp"""
    return gen_app_temp_dir('sutekh')


def format_text(sCardText):
    """Ensure card text is formatted properly"""
    # We want to split the . [dis] pattern into .\n[dis] again
    sResult = re.sub(r'(\.|\.\)) (\[...\])', '\\1\n\\2', sCardText)
    # But don't split the 'is not a discpline'
    return re.sub(r'\n(\[...\] is not a Dis)', ' \\1', sResult)


# Utility test for crypt cards
def is_crypt_card(oAbsCard):
    """Test if a card is a crypt card or not"""
    # Vampires and Imbued have exactly one card type (we hope that WW
    # don't change that)
    return oAbsCard.cardtype[0].name in CRYPT_TYPES


def is_vampire(oAbsCard):
    """Test if a card is a vampire or not"""
    return oAbsCard.cardtype[0].name == 'Vampire'


# Utility tests for other cards
def is_trifle(oAbsCard):
    """Test if a card is a trifle master card"""
    if oAbsCard.cardtype[0].name == "Master":
        for oKeyword in oAbsCard.keywords:
            if oKeyword.keyword == 'trifle':
                return True
    return False


# Helper functions for the io routines
def monger_url(oCard, bVamp):
    """Return a monger url for the given AbstractCard"""
    sName = move_articles_to_back(oCard.name)
    if bVamp:
        if oCard.level is not None:
            sName = sName.replace(' (Advanced)', '')
            sMongerURL = "http://monger.vekn.org/showvamp.html?NAME=%s ADV" \
                         % sName
        else:
            sMongerURL = "http://monger.vekn.org/showvamp.html?NAME=%s" % sName
    else:
        sMongerURL = "http://monger.vekn.org/showcard.html?NAME=%s" % sName
    # May not need this, but play safe
    sMongerURL = sMongerURL.replace(' ', '%20')
    return sMongerURL


def secret_library_url(oCard, bVamp):
    """Return a Secret Library url for the given AbstractCard"""
    sName = move_articles_to_back(oCard.name)
    if bVamp:
        if oCard.level is not None:
            sName = sName.replace(' (Advanced)', '')
            sURL = "http://www.secretlibrary.info/?crypt=%s+Adv" \
                   % sName
        else:
            sURL = "http://www.secretlibrary.info/?crypt=%s" \
                   % sName
    else:
        sURL = "http://www.secretlibrary.info/?lib=%s" \
               % sName
    sURL = sURL.replace(' ', '+')
    # ET will replace " with &quot;, which can lead to issues with SL, so we
    # drop double quotes entirely
    sURL = sURL.replace('"', '')
    return sURL
