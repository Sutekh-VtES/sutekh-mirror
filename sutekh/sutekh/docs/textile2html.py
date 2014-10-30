# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""
Convert Sutekh textile documentation into HTML pages.
"""

import imp
import os

# pylint: disable=C0103
# We ignore our usual conventions for all the import fiddling, since
# we want to end up with global module names for consistency elsewhere in the
# code base
sInfoPath = os.path.join(os.path.dirname(__file__), '..', 'SutekhInfo.py')
SutekhInfo = imp.load_source("SutekhInfo", sInfoPath).SutekhInfo

# Import filter info
sModPath = os.path.join(os.path.dirname(__file__), '..', '..')
oFile, sModname, oDescription = imp.find_module('sutekh', [sModPath])
sutekh_package = imp.load_module('sutekh', oFile, sModname, oDescription)
Filters = sutekh_package.core.Filters
FilterParser = sutekh_package.base.core.FilterParser
sDocPath = os.path.join(os.path.dirname(__file__), '..', 'base', 'docs',
                        'DocUtils.py')
DocUtils = imp.load_source('DocUtils', sDocPath)

# pylint: enable=C0103


def replace_version(sText):
    """Replace the version marker with the correct text."""
    return sText.replace('!Sutekh Version!',
                         'Sutekh %s' % SutekhInfo.BASE_VERSION_STR)


if __name__ == "__main__":
    DocUtils.make_filter_txt('textile', FilterParser.PARSER_FILTERS)
    DocUtils.convert("textile", "html", SutekhInfo, replace_version)
    DocUtils.cleanup('textile')
