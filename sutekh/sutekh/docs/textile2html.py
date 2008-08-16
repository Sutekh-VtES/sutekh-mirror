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

def textile2html(sText):
    """Convert a Textile markup string to an HTML file."""
    return textile.textile(sText)

def convert(sTextileDir, sHtmlDir):
    """Convert all .txt files in sTextileDir to .html files in sHtmlDir."""
    for sTextilePath in glob.glob(os.path.join(sTextileDir, "*.txt")):
        sBasename = os.path.basename(sTextilePath)
        sFilename, sExt = os.path.splitext(sBasename)
        sHtmlPath = os.path.join(sHtmlDir, sFilename + ".html")

        fTextile = file(sTextilePath, "rb")
        fHtml = file(sHtmlPath, "wb")

        fHtml.write(textile2html(fTextile.read()))

        fTextile.close()
        fHtml.close()

if __name__ == "__main__":
    convert("textile", "html")
