# setup.py
# Copyright 2007 Simon Cross <hodgestar@gmail.com>

from setuptools import setup, find_packages

class SutekhInfo(object):
    VERSION = (0,3,1)
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

    INSTALL_REQUIRES = [
        'SQLObject',
        'PyProtocols'
    ]

    # Install these manually
    NON_EGG_REQUIREMENTS = [
        'pysqlite',
        'PyGTK',
        'PyXML'
    ]

setup   (   # Metadata
            name = SutekhInfo.NAME,
            version = SutekhInfo.VERSION_STR,
            description = SutekhInfo.DESCRIPTION,

            author = SutekhInfo.AUTHOR_NAME,
            author_email = SutekhInfo.AUTHOR_EMAIL,

            maintainer = SutekhInfo.MAINTAINER_NAME,
            maintainer_email = SutekhInfo.MAINTAINER_EMAIL,

            url = SutekhInfo.SOURCEFORGE_URL,

            license = SutekhInfo.LICENSE,

            # Dependencies
            install_requires = SutekhInfo.INSTALL_REQUIRES,

            # Files
            packages = find_packages(),
            package_data = {
                # Include XSLT files from all packages
                '': ['*.xsl']
            },
            scripts = ['sutekh/SutekhCli.py','sutekh/SutekhGui.py']
        )
