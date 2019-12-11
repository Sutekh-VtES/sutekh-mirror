# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2009 Simon Cross <hodgestar@gmail.com>
# Copyright 2009 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

"""Base class for sutekh specific XML parser
   """


from sutekh.base.io.BaseCardSetIO import BaseCardXMLParser


class BaseSutekhXMLParser(BaseCardXMLParser):
    # pylint: disable=abstract-method
    # Doesn't matter that we don't override _convert_tree - subclasses will
    # do that for us
    """Base class for Sutekh XML files.

       Defines typename and version tag as required for the subclasses."""

    # Common elements to all Sutekh card parsers
    sTypeName = "Sutekh"
    sVersionTag = "sutekh_xml_version"
