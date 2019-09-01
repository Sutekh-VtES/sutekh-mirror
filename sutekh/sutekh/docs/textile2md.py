# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""
Convert Sutekh textile documentation into Markdown pages for the wiki.
"""

import imp
import os

# pylint: disable=invalid-name
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
sUtilPath = os.path.join(os.path.dirname(__file__), '..', 'base',
                         'Utility.py')
DocUtils = imp.load_source('DocUtils', sDocPath)
Utility = imp.load_source('Utility', sUtilPath)
# Import plugins
sPluginPath = os.path.join(os.path.dirname(__file__), '..', 'gui',
                           'PluginManager.py')
PluginManager = imp.load_source('sutekh.gui.PluginManager', sPluginPath)


# pylint: enable=invalid-name


def replace_version(sText):
    """Replace the version marker with the correct text."""
    return sText.replace('!Sutekh Version!',
                         'Sutekh %s' % SutekhInfo.BASE_VERSION_STR)


def main():
    """Actually run the doc generation"""
    Utility.ensure_dir_exists('md')
    oPluginMngr = PluginManager.PluginManager()
    oPluginMngr.load_plugins()
    aPlugins = oPluginMngr.get_all_plugins()
    DocUtils.make_filter_txt('textile', FilterParser.PARSER_FILTERS)
    DocUtils.convert_to_markdown("textile", "md", aPlugins, replace_version)
    DocUtils.cleanup('textile')


if __name__ == "__main__":
    main()
