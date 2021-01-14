# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# Copyright 2014 Neil Muller <drnlmuller+sutekh@gmail.com>
# Reowkred from textile2html.py
# GPL - see COPYING for details

"""Useful utilities for generating HTML documentation"""

from __future__ import print_function

import os
import glob
import re

import textile

# pylint: disable=invalid-name
# we ignore our usual naming conventions here

try:
    import tidy
except ImportError:
    tidy = None


HTML_HEADER = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html lang="en" xml:lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>%(title)s</title>
</head>
<body>
"""

HTML_FOOTER = """
</body>
</html>
"""

# Sections for the filter help files

FILTER_USAGE = """h2(#usage). Usage

Filter elements and values for the filters can be dragged from the right
hand pane to the filter to add them to the filter, and dragged from the filter
to the right hand pane to remove them from the filter. Disabled filter
elements or filter elements with no values set are ignored.
"""

FILTER_NAVIGATION = """h2(#navigation). Keyboard Navigation

You can switch between the different filter lists using
*&lt;Alt&gt;--&lt;Left&gt;* and *&lt;Alt&gt;--&lt;Right&gt;*.
*&lt;Ctrl&gt;--&lt;Enter&gt;* will paste the currently selected list of values
into the filter.  *&lt;Del&gt;* will delete a value or filter part from the
filter *&lt;Ctrl&gt;--&lt;Space&gt;* will disable a filter part, while
*&lt;Alt&gt;--&lt;Space&gt;* will negate it.
"""

FILTER_ELEMENTS = """h2(#elements). Filter Elements

The available filtering options are listed below.  The first line of each item
shows the description you'll see in the filter editor in bold.  The rest of the
description describes the arguments the filter takes and the results it
produces.
"""

# pylint: enable=invalid-name


def _make_link(sName):
    """Helper function to generate a sensible html link
       from the menu name."""
    sLinkTag = sName.lower()
    for sChar in [',', '(', ')', ' ', '-']:
        sLinkTag = sLinkTag.replace(sChar, '')
    return sLinkTag


class FilterGroup:
    """Fake filter for Filter Group help."""

    description = "Filter Group"
    keyword = "filter_group"
    helptext = ("A list of other filter elements.\nFilter element with holds"
                " other filter elements. The result of the filter group is "
                " the combination of all the filter elements as specified by"
                " the Filter Group type.\n\n"
                "The 4 Group types are:\n\n"
                "* _All of_: This filter matches only if every filter in"
                " the group matches.\n"
                "* _Any of_: This filter matches if at least one of the"
                " filters in the group matches.\n"
                "* _Not all of_: This filter matches if at least one of the"
                " filters in the group doesn't match.\n"
                "* _Not any of_: This filter matches only if none of the"
                " filters in the group match.\n")


def textile2html(sText, dContext, fProcessText):
    """Convert a Textile markup string to an HTML file."""
    sHtml = ''.join([HTML_HEADER % dContext,
                     textile.textile(fProcessText(sText)),
                     HTML_FOOTER % dContext])
    sHtml = sHtml.replace('<br />', ' ')  # remove pesky linebreaks
    return sHtml


def textile2markdown(aLines, fProcessText):
    """Convert textile content to markdown.

       This is rule-based, and doesn't cover the full textile syntax.
       We aim to convert to the markdown variant supported by the
       sourceforge wiki."""
    # pylint: disable=too-many-locals
    # We use a bunch of local variables as psuedo-constants to
    # keep this self-contained

    # pylint: disable=invalid-name
    # we break the naming convention for these pseudo-constants
    HEADER = re.compile(r'h([0-9])\(#(.*)\)\. (.*)$')
    NUM_LINK = re.compile(r'^(#*) "([^:]*)":(#.*)$')
    LINK_TEXT = re.compile(r'"([^"]*)":([^ ]*)\b')
    # we want to match starting *'s that aren't meant to be starting
    # list items. Because of our textile conventions, this is currently
    # good enough
    LIST_ITEM = re.compile(r'^(\*+)([^\*]+$|[^\*]+\*[^\*]+\*[^\*]*)+$')
    EMP_ITEM = re.compile(r'\*([^\*]+)\*')
    # pylint: enable=invalid-name

    aOutput = []
    for sLine in aLines:
        sLine = fProcessText(sLine).strip()
        # We need to remove single line breaks in paragraphs, because
        # sf turns those into <br> elements, but we need to keep
        # \n\n sequences to create paragraph breaks
        # This differs from traditional markdown, which is annoying
        if not sLine:
            sLine = '\n\n'
        elif sLine.startswith('h1.'):
            sLine = sLine.replace('h1.', '#')
        elif sLine.startswith('h2.'):
            sLine = sLine.replace('h2.', '##')
        elif sLine.startswith('h3.'):
            sLine = sLine.replace('h3.', '###')
        elif sLine.startswith('h4.'):
            sLine = sLine.replace('h4.', '####')
        else:
            oMatch = HEADER.search(sLine)
            if oMatch:
                sDepth, sLabel, sHeader = oMatch.groups()
                sLine = '%s <a name="%s"></a> %s' % ('#' * int(sDepth),
                                                     sLabel, sHeader)
            oMatch = NUM_LINK.search(sLine)
            # List items need to end with a line break
            if oMatch:
                sHash, sText, sLink = oMatch.groups()
                sIndent = '  ' * len(sHash)
                sLine = '%s 1. [%s](%s)\n' % (sIndent, sText, sLink)
            # fix links
            sLine = re.sub(LINK_TEXT, r'[\1](\2)', sLine)
            oMatch = LIST_ITEM.search(sLine)
            if oMatch:
                # markdown docs say 4 space indents, although
                # sourceforge seems happier with less
                # We change to '-' for lists to make the emphasis
                # match easier
                sIndent = '    ' * (len(oMatch.groups()[0]) - 1) + '-\\2'
                sLine = re.sub(LIST_ITEM, sIndent, sLine)
                sLine += '\n'
            sLine = re.sub(EMP_ITEM, r'**\1**', sLine)
        if not sLine.endswith('\n'):
            sLine += ' '
        aOutput.append(sLine)
    return ''.join(aOutput)


def _load_textile(sTextilePath):
    """Load lines from the textile file."""
    fTextile = open(sTextilePath, "r")

    # NB: Late night fast 'n dirty hack alert
    # Annoyingly, python-textile 2.1 doesn't handle list elements split
    # over multiple lines the way python-textile 2.0 does [1], so we need
    # to manually join lines before feeding them to textile
    # We use the tradional trailing \ to indicate continuation
    # [1] Note that the 2.10 version in karmic is a misnumbered 2.0.10
    aLines = []
    aCurLine = []
    for sLine in fTextile.readlines():
        if sLine.endswith("\\\n"):
            if aCurLine:
                aCurLine.append(sLine[:-2])
            else:
                aCurLine = [sLine[:-2]]
            continue
        if aCurLine:
            aCurLine.append(sLine)
            aLines.append(''.join(aCurLine))
            aCurLine = []
        else:
            aLines.append(sLine)

    fTextile.close()
    return aLines


def _process_plugins(aLines, aPlugins):
    """Add help text for plugins to the textile data."""
    # Find all the possible tags
    dTags = {}
    for sLine in aLines:
        if sLine.startswith(':'):
            # check type
            if ':list:' in sLine or ':numbered:' in sLine or ':text:' in sLine:
                sTag = sLine.split(':', 3)[3].strip()
                if sTag not in dTags:
                    dTags[sTag] = {':list:': [], ':numbered:': [],
                                   ':text:': []}
            else:
                print("Unknown Tag type %s" % sLine)
    if dTags:
        # Only replace stuff if we have tags, otherwise silently skip all this
        for cPlugin in aPlugins:
            sPluginCat = cPlugin.get_help_category()
            if sPluginCat is None:
                # No docs, so skip
                continue
            if sPluginCat not in dTags:
                print("%s has unrecognised plugin help category: %s" % (
                    cPlugin, sPluginCat))
                continue
            # Construct the tags
            sName = cPlugin.get_help_menu_entry()
            if not sName:
                print("%s has no Help menu entry - Skipped" % cPlugin)
                continue
            sLinkTag = _make_link(sName)
            sText = cPlugin.get_help_list_text()
            dTags[sPluginCat][':list:'].append(
                '*listlevel* "%s":#%s %s' % (sName, sLinkTag, sText))
            sText = cPlugin.get_help_numbered_text()
            dTags[sPluginCat][':numbered:'].append(
                '#numlevel# "%s":#%s %s' % (sName, sLinkTag, sText))
            sText = cPlugin.get_help_text()
            dTags[sPluginCat][':text:'].append(
                'hlevel(#%s). %s\n\n%s\n\n' % (sLinkTag, sName, sText))
        # replace tags
        for iCnt, sLine in enumerate(aLines):
            if sLine.startswith(':') and (':list:' in sLine
                                          or ':numbered:' in sLine
                                          or ':text:' in sLine):
                _sHead, _sSkipType, sLevel, sTag = sLine.split(':', 3)
                sTag = sTag.strip()
                iLevel = int(sLevel)
                # XXX: Should we sort here to ensure predictable ordering,
                # rather than relying on import order?
                for sType, aData in dTags[sTag].items():
                    sFullTag = '%s%d:%s' % (sType, iLevel, sTag)
                    if sType in sLine:
                        sData = '\n'.join(aData)
                        if sType == ':list:':
                            sData = sData.replace('*listlevel*',
                                                  '*' * iLevel)
                        elif sType == ':numbered:':
                            sData = sData.replace('#numlevel#',
                                                  '#' * iLevel)
                        elif sType == ':text:':
                            sData = sData.replace('hlevel(',
                                                  'h%d(' % iLevel)
                        aLines[iCnt] = sLine.replace(sFullTag, sData)
                if not aLines[iCnt].strip():
                    # Empty line, to avoid textile trying to turn it into
                    # an element
                    # Note that we only want to strip empty lines, since the
                    # whitespace around non-empty lines matters.
                    aLines[iCnt] = ''
                    # XXX: Should there be a way to silence this?
                    print('Unused tag %s' % sTag)
    # This is a terrible idea, but works
    sText = ''.join(aLines)
    return sText.split('\n')


def convert(sTextileDir, sHtmlDir, cAppInfo, aPlugins, fProcessText):
    """Convert all .txt files in sTextileDir to .html files in sHtmlDir."""
    # pylint: disable=too-many-locals
    # Reducing the number of variables won't help clarity
    for sTextilePath in glob.glob(os.path.join(sTextileDir, "*.txt")):
        sBasename = os.path.basename(sTextilePath)
        sFilename, _sExt = os.path.splitext(sBasename)
        sHtmlPath = os.path.join(sHtmlDir, sFilename + ".html")

        dContext = {
            'title': "%s %s" % (cAppInfo.NAME, sFilename.replace('_', ' ')),
        }

        fHtml = open(sHtmlPath, "w")

        aLines = _load_textile(sTextilePath)

        aLines = _process_plugins(aLines, aPlugins)

        fHtml.write(textile2html('\n'.join(aLines), dContext, fProcessText))

        fHtml.close()

        if tidy is not None:
            aErrors = tidy.parse(sHtmlPath).get_errors()
            if aErrors:
                print('tidy reports the following errors for %s' % sHtmlPath)
                print('\n'.join([x.err for x in aErrors]))


def convert_to_markdown(sTextileDir, sMarkdownDir, aPlugins, fProcessText):
    """Convert textile files to markdown syntax."""
    for sTextilePath in glob.glob(os.path.join(sTextileDir, "*.txt")):
        sBasename = os.path.basename(sTextilePath)
        sFilename, _sExt = os.path.splitext(sBasename)
        sMarkdownPath = os.path.join(sMarkdownDir, sFilename + ".md")

        fMarkdown = open(sMarkdownPath, "w")

        aLines = _load_textile(sTextilePath)

        aLines = _process_plugins(aLines, aPlugins)

        fMarkdown.write(textile2markdown(aLines, fProcessText))

        fMarkdown.close()


def add_single_filter(aOutput, iTocIndex, sKeyword, oFilter):
    """Add a single filter's help text to the file"""
    sDesc = oFilter.description
    sLink = sKeyword.lower()

    aOutput.insert(iTocIndex, '## "%s":#%s\n' %
                   (sDesc, sLink))
    iTocIndex += 1

    aOutput.append('h3(#%s). %s\n\n' % (sLink, sDesc))

    try:
        sInput, sRest = oFilter.helptext.split('\n', 1)
        aOutput.append('*Parameters:* %s\n\n' % sInput)
        aOutput.append(sRest)
    except ValueError:
        print('Failed to extract filter details')
        print(oFilter.keyword, oFilter.helptext)

    aOutput.append('\n\n')
    return iTocIndex


def add_filters(aOutput, iTocIndex, dFilters):
    """Add the appropriate list of filters"""
    for sKeyword in sorted(dFilters):
        # Generate toc entry
        oFilter = dFilters[sKeyword]
        iTocIndex = add_single_filter(aOutput, iTocIndex, sKeyword, oFilter)
    return iTocIndex


def make_filter_txt(sDir, aFilters):
    """Convert base filters into the approriate textile files"""
    # pylint: disable=too-many-locals, too-many-statements, too-many-branches
    # Reducing the number of variables won't help clarity
    # We choose not to split this into subfuctions to
    # reduce line count and branches since the logic isn't reused
    # elsewhere and it's simpler to keep it all in one place.

    dSections = {
        'Usage': FILTER_USAGE,
        'Elements': FILTER_ELEMENTS,
        'Navigation': FILTER_NAVIGATION,
    }

    dCardSetFilters = {}
    dCardFilters = {}
    for oFilter in aFilters:
        if 'PhysicalCardSet' in oFilter.types:
            dCardSetFilters[oFilter.keyword] = oFilter
        else:
            dCardFilters[oFilter.keyword] = oFilter

    for sTemplatePath in glob.glob(os.path.join(sDir, "*.tmpl")):
        sBasename = os.path.basename(sTemplatePath)
        sFilename, _sExt = os.path.splitext(sBasename)
        sTextilePath = os.path.join(sDir, sFilename + ".txt")
        aOutput = []
        iTocIndex = 0

        fTemplate = open(sTemplatePath, "r")
        fTextile = open(sTextilePath, "w")

        for sLine in fTemplate.readlines():
            sKeyword = sLine.strip()
            if sKeyword.startswith('!') and sKeyword.endswith('!'):
                sKeyword = sKeyword.replace('!', '')
            else:
                # Not flagged as template relevant, so continue
                aOutput.append(sLine)
                continue
            if sKeyword == '#toc':
                # We're going to insert new toc entries here
                iTocIndex = len(aOutput)
                continue
            if sKeyword == 'Filter_Group':
                iTocIndex = add_single_filter(aOutput, iTocIndex,
                                              sKeyword, FilterGroup)
            elif sKeyword == 'card_filters_long':
                iTocIndex = add_filters(aOutput, iTocIndex, dCardFilters)
            elif sKeyword == 'card_set_filters_long':
                iTocIndex = add_filters(aOutput, iTocIndex, dCardSetFilters)
            elif sKeyword in dSections:
                sText = dSections[sKeyword]
                # Generate toc entry
                sLink = sKeyword.lower()
                sDesc = sText.split('\n', 1)[0]  # extract first line
                sDesc = sDesc.split('). ', 1)[1]  # extract description
                aOutput.insert(iTocIndex, '# "%s":#%s\n' %
                               (sDesc, sLink))
                iTocIndex += 1
                aOutput.append(sText)
                aOutput.append('\n')
            else:
                print('Unrecognised Keyword in template %s: %s' % (sBasename,
                                                                   sKeyword))

        fTextile.write(''.join(aOutput))


def cleanup(sDir):
    """Remove the autogenerated textile files"""
    for sTemplatePath in glob.glob(os.path.join(sDir, "*.tmpl")):
        sBasename = os.path.basename(sTemplatePath)
        sFilename, _sExt = os.path.splitext(sBasename)
        sTextilePath = os.path.join(sDir, sFilename + ".txt")

        os.remove(sTextilePath)
