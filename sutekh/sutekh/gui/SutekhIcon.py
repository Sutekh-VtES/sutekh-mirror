# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2008 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Specifiy the Sutekh icon"""

from sutekh.base.gui.PkgIcon import PkgIcon

# pylint: disable=invalid-name
# special case, so convention doesn't apply
SUTEKH_ICON = PkgIcon(__name__, "sutekh-icon.svg").get_pixbuf()
