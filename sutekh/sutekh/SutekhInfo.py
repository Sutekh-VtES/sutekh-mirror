# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

"""Requirements and such for setuptools"""

# pylint doesn't see resource_string for some reason
# pylint: disable=no-name-in-module
from pkg_resources import resource_string

# license constants to simplify things a bit

GPL = 'License :: OSI Approved :: GNU General Public License (GPL)'
LGPL = 'License :: OSI Approved :: GNU Library or Lesser General ' \
    'Public License (LGPL)'
MIT = 'License :: OSI Approved :: MIT License'
PYTHON = 'License :: OSI Approved :: Python Software Foundation License'

# pylint: disable=too-few-public-methods, missing-docstring
class SutekhInfo:
    VERSION = (1, 1, 0, 'final', 1)
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
    # resource_string returns bytes, because reasons
    LICENSE_TEXT = resource_string(__name__, 'COPYING').decode('utf8')

    CLASSIFIERS = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications :: GTK',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        GPL,
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.7',
        'Topic :: Games/Entertainment',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]

    PLATFORMS = [
        'Linux',
        'Windows',
    ]

    INSTALL_REQUIRES = [
        'SQLObject >= 3.0.0',
        'ply',
        'configobj',
        'keyring',  # Needed to store the SecretLibrary password
    ]

    # Install these manually
    NON_EGG_REQUIREMENTS = [
        'setuptools',
        'gobject-introspection',
    ]

    # Currently this allows us license the Windows build (which
    # includes dependencies) under the GPL version 2 (which
    # conveniently is the same license in Sutekh's COPYING
    # file although Sutekh itself also allows later versions
    # of the GPL).
    #
    # dependency -> (
    #   license classifier,
    #   license URL,
    #   license notes - usually license version
    # )
    DEPENDENCY_LICENSES = {
        'SQLObject': (
            LGPL,
            'http://www.gnu.org/copyleft/lesser.html',
            'Version 3'),
        'ply': (
            # Note: ply changed to a BSD license in version 3.2
            # The license doesn't appear to be anywhere other than the readme,
            # so we point to the readme for the 3.11 release.
            'License :: OSI Approved :: BSD License',
            'https://raw.githubusercontent.com/dabeaz/ply/0f398b72618c1564d71f7dc0558e6722b241875a/README.md',
            'New-BSD license'),
        'configobj': (
            'License :: OSI Approved :: BSD License',
            'https://raw.githubusercontent.com/DiffSK/configobj/master/LICENSE',
            'New-BSD license'),
        'keyring': (
            MIT,
            'https://raw.githubusercontent.com/jaraco/keyring/master/LICENSE',
            'MIT license'),
        'setuptools': (
            PYTHON,
            'http://www.python.org/psf/license/',
            'Version 2'),
        'gibject-introspection': (
            LGPL,
            'http://www.gnu.org/copyleft/lesser.html',
            'Version 2 or later'),
        'GTK': (
            LGPL,
            'http://www.gnu.org/copyleft/lesser.html',
            'Version 2 or later'),
        'Python': (
            PYTHON,
            'http://www.python.org/psf/license/',
            'Version 2'),
    }
