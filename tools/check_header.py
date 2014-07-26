#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see license file for details

"""Simple script to check that the comment headers are correct.

   This script checks that the headers have a emacs encoding line, a vim
   modeline and a copyright notice.  There are some heuristics to detect
   incorrectly formatted copyright lines and incorrect encoding lines.
   Formerly, we required a filename in the comments, but we've dropped
   that, so this warns about obselete filename comments as well.
   """

import optparse
import sys
import re
import os

# Possible copyright notice (email + possible date), but not in
# right form
COPYRIGHT = re.compile('^# ( )*Copyright [0-9]{4,}(, [0-9]{4,})*'
                       ' \S+?.* <.*@.*>')
# Standardise for other sutekh-derived card set managers
PORTED_LINE = re.compile('^# ( )*(Imported into|Modified for)'
                         ' [A-Z][a-z]+ [0-9]{4,}'
                         '(, [0-9]{4,})* \S+?.* <.*@.*>')
WRONG_COPYRIGHT = re.compile('.*<.*@.*> .*[0-9]*|.*[0-9]*.*<.*@.*>'
                             '|^# Copyright.*')
# encoding lines
VIM_MODELINE = re.compile('^# vim:fileencoding=.* ai ts=4 sts=4 et sw=4')
EMACS_CODING = re.compile('^# -\*- coding: ')
PYCODING = re.compile('^# -\*- coding: |^# vim:fileencoding=')


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
    # pylint: disable-msg=R0912
    # Lot's of cases to consider, so many branches
    sName = sFileName.split(os.path.sep)[-1]
    sCommentHeader = '# %s\n' % sName
    bValidCoding = False
    bValidEmacs = False
    bWrongUTF8 = False
    bScript = False

    for iLineCount, sLine in enumerate(oFile):
        if not sLine.startswith('#'):
            # End of comment block
            break

        if iLineCount == 0 and sLine.startswith('#!'):
            bScript = True

        if sLine == sCommentHeader:
            dScores['filename'] += 1

        if EMACS_CODING.search(sLine) is not None:
            dScores['emacs coding'] += 1
            # Encoding declaration must be one of the 1st
            # two lines (see python docs)
            if (bScript and iLineCount == 1) or iLineCount == 0:
                bValidEmacs = True

        if COPYRIGHT.search(sLine) is not None:
            dScores['copyright'] += 1
        elif PORTED_LINE.search(sLine) is not None:
            # We don't treat this as a copyright line, but
            # we don't want to flag it as an incorrect copyright
            # notice
            dScores['ignored'] += 1
        elif WRONG_COPYRIGHT.search(sLine) is not None:
            aWrongCopyrights.append(sLine)
            dScores['wrong copyright'] += 1

        if sLine.find(' GPL ') != -1:
            dScores['license'] += 1

        if VIM_MODELINE.search(sLine) is not None:
            dScores['modeline'] += 1

        if PYCODING.search(sLine) is not None:
            dScores['python encoding'] += 1
            if (iLineCount < 2):
                bValidCoding = True
            if 'utf8' in sLine:
                bWrongUTF8 = True

    return bValidCoding, bValidEmacs, bWrongUTF8, bScript


def print_search_results(dScores, aWrongCopyrights, tFlags, sFileName):
    """Display any errors found in the file"""
    # pylint: disable-msg=R0912
    # Lot's of cases to consider, so many branches
    bValidCoding, bValidEmacs, bWrongUTF8, bScript = tFlags
    if dScores['filename'] == 1:
        print '%s has an obselete # Name Header' % sFileName
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
        print ('%s has possible copyright notices in the incorrect form '
               % sFileName)
        print '(not "Copyright Years Name <email>")'
        print 'Possibly incorrect line(s) : ', aWrongCopyrights

    if dScores['emacs coding'] < 1:
        print '%s is is missing a -*- emacs coding line' % sFileName
    elif bScript and not bValidEmacs:
        print ('emacs coding line not 2nd line for python script: %s'
               % sFileName)
    elif not bValidEmacs:
        print 'emacs coding line not 1st line for python file: %s' % sFileName

    if dScores['python encoding'] < 2:
        print '%s is missing an encoding line' % sFileName
    elif dScores['python encoding'] > 2:
        print '%s is has too many encoding lines' % sFileName

    if bWrongUTF8:
        print 'Encoding line uses "utf8" instead of "utf-8" in %s' % sFileName

    if not bValidCoding and dScores['python encoding'] > 1:
        print '%s: One of the emacs coding must be in " \
                "the 1st 2 lines of the file' % sFileName


def score_failed(dScores):
    """Test if the file fails the test criteria"""
    return (dScores['emacs coding'] == 1 | dScores['copyright'] == 1 |
            dScores['modeline'] == 1 | dScores['license'] == 1 |
            dScores['filename'] == 0 | dScores['python encoding'] == 2 |
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
        'emacs coding': 0,
        'python encoding': 0,
        'filename': 0,
        'wrong copyright': 0,
        # catchall bucket for lines we note, but skip
        'ignored': 0,
    }
    aWrongCopyrights = []

    tFlags = search_file(oFile, dScores, aWrongCopyrights, sFileName)

    oFile.close()

    print_search_results(dScores, aWrongCopyrights, tFlags, sFileName)

    return not (score_failed(dScores) | tFlags[0])


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
