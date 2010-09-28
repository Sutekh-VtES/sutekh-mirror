#!/usr/bin/env python
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# check_header.py
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see license file for details

"""Simple script to check that the comment headers are correct.

   This script checks that the headers have a encoding line, a
   vim modeline, a copyright notice, and a comment mentioning
   the correct filename. There are some heuristics to detect
   incorrectly formatted copyright lines.
   """

import optparse
import sys
import re
import os


def parse_options(aArgs):
    """Parse aArgs for the options to the script"""
    oParser = optparse.OptionParser(usage="usage %prog [options]",
            version="%prog 0.1")
    oParser.add_option('-f', '--file',
            type="string", dest="sFileName", default=None,
            help="File to check")
    return oParser, oParser.parse_args(aArgs)


def search_file(oFile, dScores, aWrongCopyrights, sFileName):
    """Loop through the comments header and assign the scores."""

    # Setup test expressions
    sName = sFileName.split(os.path.sep)[-1]
    oCopyright = re.compile('^# Copyright [0-9]{4,}(, [0-9]{4,})*'
            ' \S+?.* <.*@.*>')
    oWrongCopyright = re.compile('.*<.*@.*> .*[0-9]*|.*[0-9]*.*<.*@.*>'
            '|^# Copyright.*')
    # Possible copyright notice (email + possible date), but not in
    # right form
    oVimModeline = re.compile('^# vim:fileencoding=.* ai ts=4 sts=4 et sw=4')
    oCodingLine = re.compile('^# -\*- coding: ')
    oEnCodingLine = re.compile('^# -\*- coding: |^# vim:fileencoding=')
    sCommentHeader = '# %s\n' % sName
    bValidCoding = False

    iLineCount = 0
    for sLine in oFile:
        if not sLine.startswith('#'):
            # End of comment block
            break

        iLineCount += 1

        if sLine == sCommentHeader:
            dScores['filename'] += 1

        if oCodingLine.search(sLine) is not None:
            dScores['coding lines'] += 1
            # Encoding declaration must be one of the 1st
            # two lines (see python docs)
            if (iLineCount < 3):
                bValidCoding = True

        if oCopyright.search(sLine) is not None:
            dScores['copyright'] += 1
        elif oWrongCopyright.search(sLine) is not None:
            aWrongCopyrights.append(sLine)
            dScores['wrong copyright'] += 1

        if sLine.find(' GPL ') != -1:
            dScores['license'] += 1

        if oVimModeline.search(sLine) is not None:
            dScores['modeline'] += 1
            if (iLineCount < 3):
                bValidCoding = True

        if oEnCodingLine.search(sLine) is not None:
            dScores['encoding'] += 1

    return bValidCoding


def print_search_results(dScores, aWrongCopyrights, bValidCoding, sFileName):
    """Display any errors found in the file"""
    if dScores['filename'] < 1:
        print '%s is missing # Name Header' % sFileName
    elif dScores['filename'] > 1:
        print '%s has multiple # Name Headers' % sFileName

    if dScores['license'] < 1:
        print '%s is missing reference to the license' % sFileName
    elif dScores['license'] > 1:
        print '%s has multiple reference to the license' % sFileName

    if dScores['modeline'] < 1:
        print '%s is missing the vim modeline' % sFileName
    elif dScores['modeline'] > 1:
        print '%s has multiple modelines' % sFileName

    if dScores['copyright'] < 1:
        print '%s is missing a copyright statement' % sFileName

    if dScores['wrong copyright'] > 0:
        print '%s has possible copyright notices in the incorrect form ' \
                % sFileName
        print '(not "Copyright Years Name <email>")'
        print 'Possibly incorrect line(s) : ', aWrongCopyrights

    if dScores['coding lines'] < 1:
        print '%s is is missing a -*- coding lines' % sFileName

    if dScores['encoding'] < 2:
        print '%s is missing an encoding line' % sFileName
    elif dScores['encoding'] > 2:
        print '%s is has multiple a -*- coding lines' % sFileName

    if not bValidCoding and dScores['encoding'] > 1:
        print '%s: One of the coding lines must be in " \
                "the 1st 2 lines of the file' % sFileName


def score_failed(dScores):
    """Test if the file fails the test criteria"""
    return (dScores['coding lines'] == 1 | dScores['copyright'] == 1 |
            dScores['modeline'] == 1 | dScores['license'] == 1 |
            dScores['filename'] == 1 | dScores['encoding'] == 2 |
            dScores['wrong copyright'] == 0)


def file_check(sFileName):
    """Actully do the checks. sFileName is the file to check."""
    try:
        oFile = file(sFileName, 'r')
    except IOError:
        print 'Unable to open file %s ' % sFileName
        return False

    dScores = {
            'copyright': 0,
            'license': 0,
            'modeline': 0,
            'coding lines': 0,
            'encoding': 0,
            'filename': 0,
            'wrong copyright': 0,
            }
    aWrongCopyrights = []

    bValidCoding = search_file(oFile, dScores, aWrongCopyrights, sFileName)

    oFile.close()

    print_search_results(dScores, aWrongCopyrights, bValidCoding, sFileName)

    return not (score_failed(dScores) | bValidCoding)


def main(aArgs):
    """Main function. Parse aArgs for the filename, and call file_check."""
    oOptParser, (oOpts, aArgs) = parse_options(aArgs)

    if len(aArgs) != 1 or oOpts.sFileName is None:
        oOptParser.print_help()
        return 1
    if not file_check(oOpts.sFileName):
        return 1  # fail

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
