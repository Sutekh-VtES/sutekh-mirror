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

def textile2html(sText, dContext):
    """Convert a Textile markup string to an HTML file."""
    sHtml = HTML_HEADER % dContext \
        + textile.textile(sText) \
        + HTML_FOOTER % dContext
    sHtml = sHtml.replace('<br />',' ') # remove pesky linebreaks
    return sHtml

def convert(sTextileDir, sHtmlDir):
    """Convert all .txt files in sTextileDir to .html files in sHtmlDir."""
    for sTextilePath in glob.glob(os.path.join(sTextileDir, "*.txt")):
        sBasename = os.path.basename(sTextilePath)
        # pylint: disable-msg=W0612
        # sExt is unused
        sFilename, sExt = os.path.splitext(sBasename)
        sHtmlPath = os.path.join(sHtmlDir, sFilename + ".html")

        # pylint: enable-msg=W0612

        dContext = {
            'title': "Sutekh " + sFilename
        }

        fTextile = file(sTextilePath, "rb")
        fHtml = file(sHtmlPath, "wb")

        fHtml.write(textile2html(fTextile.read(), dContext))

        fTextile.close()
        fHtml.close()

if __name__ == "__main__":
    convert("textile", "html")
