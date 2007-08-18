# SutekhInfo.py
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

from pkg_resources import resource_string

class SutekhInfo(object):
    VERSION = (0,4,0)
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
        'SQLObject == 0.9.1', # fetching 0.10dev requires svn (which is a bit crazy as an install requirement)
        'PyProtocols',
        'ply',
    ]

    # Install these manually
    NON_EGG_REQUIREMENTS = [
        'setuptools',
        'pysqlite', # sqlite3 is installed by default in Python >= 2.5
        'PyGTK',
    ]
