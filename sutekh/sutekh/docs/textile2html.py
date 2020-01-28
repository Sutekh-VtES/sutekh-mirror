# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""
Convert Sutekh textile documentation into HTML pages.
"""

import importlib
import os
import sys

# pylint: disable=invalid-name
# We ignore our usual conventions for all the import fiddling, since
# we want to end up with global module names for consistency elsewhere in the
# code base
sInfoPath = os.path.join(os.path.dirname(__file__), '..')
sModPath = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.append(sInfoPath)
sys.path.append(sModPath)
SutekhInfo = importlib.import_module("SutekhInfo").SutekhInfo
sutekh_package = importlib.import_module("sutekh")

# Import filter info
Filters = sutekh_package.core.Filters
FilterParser = sutekh_package.base.core.FilterParser
# Import docutils
DocUtils = importlib.import_module('.base.docs.DocUtils', 'sutekh')

# Import plugins
PluginManager = importlib.import_module('.gui.PluginManager', 'sutekh')


# pylint: enable=invalid-name


def replace_version(sText):
    """Replace the version marker with the correct text."""
    return sText.replace('!Sutekh Version!',
                         'Sutekh %s' % SutekhInfo.BASE_VERSION_STR)


def main():
    """Actually run the doc generation"""
    oPluginMngr = PluginManager.PluginManager()
    oPluginMngr.load_plugins()
    aPlugins = oPluginMngr.get_all_plugins()
    DocUtils.make_filter_txt('textile_docs', FilterParser.PARSER_FILTERS)
    DocUtils.convert("textile_docs", "html_docs", SutekhInfo, aPlugins,
                     replace_version)
    DocUtils.cleanup('textile_docs')


if __name__ == "__main__":
    main()
