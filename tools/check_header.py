#!/usr/bin/env python
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# check_header.py
# Copyright 2008 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see license file for details

"""
Simple script to check that the comment headers are correct.
This script checks that the headers have a encoding line, a 
vim modeline, a copyright notice, and a comment mentioning 
the correct filename. There are some heuristics to detect
incorrectly formatted copyright lines
"""
   

import optparse
import sys
import re
import os

def parse_options(aArgs):
    'Parse aArgs for the options to the script'
    oParser = optparse.OptionParser(usage="usage %prog [options]",
            version="%prog 0.1")
    oParser.add_option('-f', '--file',
            type="string", dest="sFileName", default=None,
            help="File to check")
    return oParser, oParser.parse_args(aArgs)

def file_check(sFileName):
    """
    Actully do the checks. sFileName is the file to check
    """
    try:
        oFile = file(sFileName, 'r')
    except IOError:
        print 'Unable to open file %s ' % sFileName
        return False
    sName = sFileName.split(os.path.sep)[-1]

    oCopyright = re.compile('^# Copyright [0-9]{4,}(, [0-9]{4,})*'
            ' \S+?.* <.*@.*>')
    oWrongCopyright = re.compile('.*<.*@.*> .*[0-9]*|.*[0-9]*.*<.*@.*>'
            '|^# Copyright.*')
    oVimModeline = re.compile('^# vim:fileencoding=.* ai ts=4 sts=4 et sw=4')
    oCodingLine = re.compile('^# -\*- coding: ')
    oEnCodingLine = re.compile('^# -\*- coding: |^# vim:fileencoding=')
    # Possible copyright notice (email + possible date), but not in
    # right form
    sCommentHeader = '# %s\n' % sName
    iCopyright = 0
    iLicense = 0
    iModeline = 0
    iCodingLine = 0
    iEnCodingLine = 0
    iNameHeader = 0
    iWrongCopyright = 0
    aWrongCopyrights = []
    bValidCoding = False

    iLineCount = 0
    for sLine in oFile:
        if not sLine.startswith('#'):
            # End of comment block
            break

        iLineCount += 1

        if sLine == sCommentHeader:
            iNameHeader += 1

        if oCodingLine.search(sLine) is not None:
            iCodingLine += 1
            # Encoding declaration must be one of the 1st
            # two lines (see python docs)
            if (iLineCount < 3):
                bValidCoding = True

        if oCopyright.search(sLine) is not None:
            iCopyright += 1
        elif oWrongCopyright.search(sLine) is not None:
            aWrongCopyrights.append(sLine)
            iWrongCopyright += 1

        if sLine.find(' GPL ') != -1:
            iLicense += 1

        if oVimModeline.search(sLine) is not None:
            iModeline += 1
            if (iLineCount < 3):
                bValidCoding = True

        if oEnCodingLine.search(sLine) is not None:
            iEnCodingLine += 1

    oFile.close()
    if iNameHeader < 1:
        print '%s is missing # Name Header' % sFileName
    elif iNameHeader > 1:
        print '%s has multiple # Name Headers' % sFileName

    if iLicense < 1:
        print '%s is missing reference to the license' % sFileName
    elif iLicense > 1:
        print '%s has multiple reference to the license' % sFileName

    if iModeline < 1:
        print '%s is missing the vim modeline' % sFileName
    elif iModeline > 1:
        print '%s has multiple modelines' % sFileName

    if iCopyright < 1:
        print '%s is missing a copyright statement' % sFileName

    if iWrongCopyright > 0:
        print '%s has possible copyright notices in the incorrect form ' \
                % sFileName
        print '(not "Copyright Years Name <email>")'
        print 'Possibly incorrect line(s) : ', aWrongCopyrights

    if iCodingLine < 1:
        print '%s is is missing a -*- coding lines' % sFileName

    if iEnCodingLine < 2:
        print '%s is missing an encoding line' % sFileName
    elif iEnCodingLine > 2:
        print '%s is has multiple a -*- coding lines' % sFileName

    if not bValidCoding and iEnCodingLine > 1:
        print '%s: One of the coding lines must be in " \
                "the 1st 2 lines of the file' % sFileName

    return not (iCodingLine == 1 | iCopyright == 1 | 
            iModeline == 1 | iLicense == 1 | 
            iNameHeader == 1 | iEnCodingLine == 2 |
            iWrongCopyright == 0 | bValidCoding)

def main(aArgs):
    """
    Main function. Parse aArgs for the filename, and call 
    file_check
    """
    oOptParser, (oOpts, aArgs) = parse_options(aArgs)

    if len(aArgs) != 1 or oOpts.sFileName is None:
        oOptParser.print_help()
        return 1
    if not file_check(oOpts.sFileName):
        return 1 # fail

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))

