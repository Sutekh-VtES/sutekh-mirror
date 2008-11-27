# setup.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

# Be sure that the import will grab the correct version
# of SutekhInfo when building packages.

"""Setuptools setup.py file for Sutekh."""

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
            download_url = SutekhInfo.PYPI_URL,

            license = SutekhInfo.LICENSE,

            classifiers = SutekhInfo.CLASSIFIERS,

            platforms = SutekhInfo.PLATFORMS,

            # Dependencies
            install_requires = SutekhInfo.INSTALL_REQUIRES,

            # Files
            packages = find_packages(exclude=['sutekh.tests']),
            package_data = {
                # Include SVG files from all packages
                '': ['*.svg'],
                # Include LICENSE information for sutekh package
                # Include everything under the docs directory
                'sutekh': ['COPYING', 'docs/html/*'],
            },
            scripts = ['sutekh/SutekhCli.py','sutekh/SutekhGui.py']
        )
