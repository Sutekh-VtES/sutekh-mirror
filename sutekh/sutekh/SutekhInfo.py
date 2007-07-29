# SutekhInfo.py
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

from pkg_resources import resource_string

class SutekhInfo(object):
    VERSION = (0,3,2)
    VERSION_STR = '.'.join([str(x) for x in VERSION])

    NAME = 'Sutekh'
    DESCRIPTION = 'VtES Card Collection Manager'

    AUTHORS = [ ('Simon Cross','hodgestar+sutekh@gmail.com'),
                ('Neil Muller','drnmuller+sutekh@gmail.com') ]

    AUTHOR_NAME = AUTHORS[0][0]
    AUTHOR_EMAIL = AUTHORS[0][1]

    MAINTAINERS = AUTHORS

    MAINTAINER_NAME = MAINTAINERS[0][0]
    MAINTAINER_EMAIL = MAINTAINERS[0][1]

    SOURCEFORGE_URL = 'http://sourceforge.net/projects/sutekh/'

    LICENSE = 'GPL'
    LICENSE_TEXT = resource_string(__name__,'COPYING')

    INSTALL_REQUIRES = [
        'SQLObject',
        'PyProtocols',
        'Ply'
    ]

    # Install these manually
    NON_EGG_REQUIREMENTS = [
        'pysqlite',
        'PyGTK',
        'PyXML'
    ]
