# textile2html.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""
Convert Sutekh textile documentation into HTML pages.
"""

import glob
import os
import textile

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

# pylint: enable-msg=C0103

# TODO: Pull in version number automatically from SutekhInfo


def textile2html(sText, dContext):
    """Convert a Textile markup string to an HTML file."""
    sHtml = HTML_HEADER % dContext \
        + textile.textile(sText) \
        + HTML_FOOTER % dContext
    sHtml = sHtml.replace('<br />', ' ')  # remove pesky linebreaks
    return sHtml


def convert(sTextileDir, sHtmlDir):
    """Convert all .txt files in sTextileDir to .html files in sHtmlDir."""
    for sTextilePath in glob.glob(os.path.join(sTextileDir, "*.txt")):
        sBasename = os.path.basename(sTextilePath)
        sFilename, _sExt = os.path.splitext(sBasename)
        sHtmlPath = os.path.join(sHtmlDir, sFilename + ".html")

        dContext = {
            'title': "Sutekh " + sFilename,
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

        fHtml.write(textile2html(''.join(aLines), dContext))

        fTextile.close()
        fHtml.close()

        if tidy is not None:
            aErrors = tidy.parse(sHtmlPath).get_errors()
            if aErrors:
                print 'tidy reports the following errors for %s' % sHtmlPath
                print '\n'.join([x.err for x in aErrors])


if __name__ == "__main__":
    convert("textile", "html")
