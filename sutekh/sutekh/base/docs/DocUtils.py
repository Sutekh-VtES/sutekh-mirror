# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# Copyright 2014 Neil Muller <drnlmuller+sutekh@gmail.com>
# Reowkred from textile2html.py
# GPL - see COPYING for details

"""Useful utilities for generating HTML documentation"""

import textile
import os
import glob

# pylint: disable-msg=C0103
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

# pylint: enable-msg=C0103


class FilterGroup(object):
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


def convert(sTextileDir, sHtmlDir, cAppInfo, fProcessText):
    """Convert all .txt files in sTextileDir to .html files in sHtmlDir."""
    for sTextilePath in glob.glob(os.path.join(sTextileDir, "*.txt")):
        sBasename = os.path.basename(sTextilePath)
        sFilename, _sExt = os.path.splitext(sBasename)
        sHtmlPath = os.path.join(sHtmlDir, sFilename + ".html")

        dContext = {
            'title': "%s %s" % (cAppInfo.NAME, sFilename.replace('_', ' ')),
        }

        fTextile = file(sTextilePath, "rb")
        fHtml = file(sHtmlPath, "wb")

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
            elif aCurLine:
                aCurLine.append(sLine)
                aLines.append(''.join(aCurLine))
                aCurLine = []
            else:
                aLines.append(sLine)

        fHtml.write(textile2html(''.join(aLines), dContext, fProcessText))

        fTextile.close()
        fHtml.close()

        if tidy is not None:
            aErrors = tidy.parse(sHtmlPath).get_errors()
            if aErrors:
                print 'tidy reports the following errors for %s' % sHtmlPath
                print '\n'.join([x.err for x in aErrors])


def make_filter_txt(sDir, aFilters):
    """Convert base filters into the approriate textile files"""

    dSections = {
        'Usage': FILTER_USAGE,
        'Elements': FILTER_ELEMENTS,
        'Navigation': FILTER_NAVIGATION,
    }

    dFilters = {}
    dFilters['Filter_Group'] = FilterGroup
    for oFilter in aFilters:
        dFilters[oFilter.keyword] = oFilter

    for sTemplatePath in glob.glob(os.path.join(sDir, "*.tmpl")):
        sBasename = os.path.basename(sTemplatePath)
        sFilename, _sExt = os.path.splitext(sBasename)
        sTextilePath = os.path.join(sDir, sFilename + ".txt")
        aOutput = []
        iTocIndex = 0

        fTemplate = file(sTemplatePath, "rb")
        fTextile = file(sTextilePath, "wb")

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
            elif sKeyword in dFilters:
                oFilter = dFilters[sKeyword]

                # Generate toc entry
                sDesc = oFilter.description
                sLink = sKeyword.lower()

                aOutput.insert(iTocIndex, '## "%s":#%s\n' %
                               (sDesc, sLink))
                iTocIndex += 1

                aOutput.append('h3(#%s). %s\n\n' % (sLink, sDesc))

                try:
                    sInput, sRest = oFilter.helptext.split('\n', 1)
                except ValueError:
                    print 'Failed to extract filter details'
                    print oFilter.keyword, oFilter.helptext

                aOutput.append('*Parameters:* %s\n\n' % sInput)
                aOutput.append(sRest)
                aOutput.append('\n')
                if sKeyword != 'Filter_Group':
                    del dFilters[sKeyword]
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
                print 'Unrecognised Keyword in template %s: %s' % (sBasename,
                                                                   sKeyword)

        fTextile.write(''.join(aOutput))

    if 'Filter_Group' in dFilters:
        del dFilters['Filter_Group']
    if dFilters:
        print 'The following filters have no entry in the templates.'
        print dFilters.keys()


def cleanup(sDir):
    """Remove the autogenerated textile files"""
    for sTemplatePath in glob.glob(os.path.join(sDir, "*.tmpl")):
        sBasename = os.path.basename(sTemplatePath)
        sFilename, _sExt = os.path.splitext(sBasename)
        sTextilePath = os.path.join(sDir, sFilename + ".txt")

        os.remove(sTextilePath)
