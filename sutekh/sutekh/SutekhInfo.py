# SutekhInfo.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Requirements and such for setuptools"""

# pylint doesn't see resource_string for some reason
# pylint: disable-msg=E0611
from pkg_resources import resource_string

# pylint: disable-msg=R0903,C0111
class SutekhInfo(object):
    VERSION = (0, 7, 0, 'alpha', 0)
    BASE_VERSION_STR = '.'.join([str(x) for x in VERSION[:3]])
    VERSION_STR = {
        'final': BASE_VERSION_STR,
        'alpha': BASE_VERSION_STR + 'a' + str(VERSION[4]),
        'rc': BASE_VERSION_STR + 'rc' + str(VERSION[4]),
    }[VERSION[3]]

    NAME = 'Sutekh'
    DESCRIPTION = 'VtES Card Collection Manager'

    PEOPLE = {
        'Simon': ('Simon Cross', 'hodgestar+sutekh@gmail.com'),
        'Neil': ('Neil Muller', 'drnmuller+sutekh@gmail.com'),
        'Adrianna': ('Adrianna Pinska', 'adrianna.pinska+sutekh@gmail.com'),
    }

    AUTHORS = [
        PEOPLE['Simon'],
        PEOPLE['Neil'],
    ]

    AUTHOR_NAME = AUTHORS[0][0]
    AUTHOR_EMAIL = AUTHORS[0][1]

    MAINTAINERS = AUTHORS

    MAINTAINER_NAME = MAINTAINERS[0][0]
    MAINTAINER_EMAIL = MAINTAINERS[0][1]

    ARTISTS = [
        PEOPLE['Simon'],
    ]

    DOCUMENTERS = [
        PEOPLE['Neil'],
        PEOPLE['Adrianna'],
    ]

    SOURCEFORGE_URL = 'http://sourceforge.net/projects/sutekh/'
    PYPI_URL = 'http://pypi.python.org/pypi/Sutekh/'

    LICENSE = 'GPL'
    LICENSE_TEXT = resource_string(__name__, 'COPYING')

    CLASSIFIERS = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications :: GTK',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.5',
        'Topic :: Games/Entertainment',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]

    PLATFORMS = [
        'Linux',
        'Windows',
    ]

    INSTALL_REQUIRES = [
        'SQLObject >= 0.9.0, < 0.11', # fetching 0.10dev requires svn
                           # (which is a bit crazy as an install requirement)
        'PyProtocols',
        'ply',
        'xlrd',
    ]

    # Install these manually
    NON_EGG_REQUIREMENTS = [
        'setuptools',
        'pysqlite', # sqlite3 is installed by default in Python >= 2.5
        'PyGTK',
    ]