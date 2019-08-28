# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Requirements and such for setuptools"""

# pylint doesn't see resource_string for some reason
# pylint: disable=no-name-in-module
from pkg_resources import resource_string


# pylint: disable=R0903,missing-docstring
class SutekhInfo(object):
    VERSION = (0, 9, 5, 'alpha', 0)
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
        'Neil': ('Neil Muller', 'drnlmuller+sutekh@gmail.com'),
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

    SOURCEFORGE_URL = 'https://sourceforge.net/projects/sutekh/'
    PYPI_URL = 'https://pypi.python.org/pypi/Sutekh/'

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
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Games/Entertainment',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]

    PLATFORMS = [
        'Linux',
        'Windows',
    ]

    INSTALL_REQUIRES = [
        'SQLObject >= 0.9.0, < 3.8',  # fetching the dev version requires svn
                           # (which is a bit crazy as an install requirement)
        'singledispatch',
        'ply',
        'configobj',
        'keyring',  # Needed to store the SecretLibrary password
    ]

    # Install these manually
    NON_EGG_REQUIREMENTS = [
        'setuptools',
        'pysqlite',  # sqlite3 is installed by default in Python >= 2.5
        'PyGTK',
    ]

    # Currently this allows us license the Windows build (which
    # includes dependencies) under the GPL version 2 (which
    # conveniently is the same license in Sutekh's COPYING
    # file although Sutekh itself also later versions of the
    # GPL).
    #
    # dependency -> (
    #   license classifier,
    #   license URL,
    #   license notes - usually license version
    # )
    DEPENDENCY_LICENSES = {
        'SQLObject': (
            'License :: OSI Approved :: GNU Library or Lesser '
                'General Public License (LGPL)',
            'http://www.gnu.org/copyleft/lesser.html',
            'Version 3'),
        'singledispath': (
            # While the functools.singledispatch part of the
            # python 3 is under the Python license, the
            # python 2 backport is relicensed to MIT
            'License :: OSI Approved :: MIT License',
            'https://bitbucket.org/ambv/singledispatch',
            'MIT License'),
        'ply': (
            # Note: ply changes to BSD license in version 3.2
            'License :: OSI Approved :: GNU Library or Lesser '
                'General Public License (LGPL)',
            'http://www.gnu.org/licenses/lgpl-2.1.html',
            'Version 2.1'),
        'configobj': (
            'License :: OSI Approved :: BSD License',
            'http://www.voidspace.org.uk/python/configobj.html#license',
            'New-BSD license'),
        'keyring': (
            'License :: OSI Approved :: MIT License',
            'https://bitbucket.org/kang/python-keyring-lib/raw/tip/README.rst',
            'MIT license'),
        'setuptools': (
            'License :: OSI Approved :: Python Software Foundation License',
            'http://www.python.org/psf/license/',
            'Version 2'),
        'PyGTK': (
            'License :: OSI Approved :: GNU Library or Lesser '
                'General Public License (LGPL)',
            'http://www.gnu.org/copyleft/lesser.html',
            'Version 2 or later'),
        'GTK': (
            'License :: OSI Approved :: GNU Library or Lesser '
                'General Public License (LGPL)',
            'http://www.gnu.org/copyleft/lesser.html',
            'Version 2 or later'),
        'Python': (
            'License :: OSI Approved :: Python Software Foundation License',
            'http://www.python.org/psf/license/',
            'Version 2'),
        'ZipDLL': (  # NSIS Plugin
            'License :: OSI Approved :: GNU General Public License (GPL)',
            'http://www.gnu.org/copyleft/gpl.html',
            'Version 2 or later'),
    }
