# setup.py
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

# Be sure that the import will grab the correct version
# of SutekhInfo when building packages.

from setuptools import setup, find_packages
from sutekh.SutekhInfo import SutekhInfo

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
            packages = find_packages(exclude=['sutekh.tests']),
            package_data = {
                # Include XSLT files from all packages
                '': ['*.xsl'],
                # Include LICENSE information for sutekh package
                'sutekh': ['COPYING'],
            },
            scripts = ['sutekh/SutekhCli.py','sutekh/SutekhGui.py']
        )
