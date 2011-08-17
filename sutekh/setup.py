# setup.py
# -*- coding: utf8 -*-
# vim:fileencoding=utf8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# GPL - see COPYING for details

# Be sure that the import will grab the correct version
# of SutekhInfo when building packages.

"""Setuptools setup.py file for Sutekh."""

from setuptools import setup, find_packages

# avoid importing all of Sutkeh and its dependencies
import imp
import os
import sys
import types
sys.modules['sutekh'] = types.ModuleType('sutekh')
SutekhInfoMod = imp.load_source("sutekh.SutekhInfo",
                                os.path.join(os.path.dirname(__file__),
                                             "sutekh", "SutekhInfo.py"))
SutekhInfo = SutekhInfoMod.SutekhInfo


try:
    # pylint: disable-msg=F0401, W0611
    # F0401 - OK to fail to import these here
    # W0611 - py2exe is unused, since the import is just a check
    import py2exe
    from py2exe.build_exe import py2exe as builder
    import os
    import glob
    # pylint: enable-msg=F0401, W0611

    class PkgResourceBuilder(builder):
        """Extend to builder class to override copy_extensions"""
        # pylint: disable-msg=E1101, C0103, W0232
        # E1101: missed imports leave pylint confused here
        # C0103: not using our naming conventions here
        # W0232: we don't need an __init__ method for our goals

        def copy_extensions(self, extensions):
            """Hack the py2exe C extension copier
               to put pkg_resources into the
               library.zip file.
               """
            builder.copy_extensions(self, extensions)
            package_data = self.distribution.package_data.copy()

            for package, patterns in self.distribution.package_data.items():
                package_dir = os.path.join(*package.split('.'))
                collect_dir = os.path.join(self.collect_dir, package_dir)

                # create sub-dirs in py2exe collection area
                # Copy the media files to the collection dir.
                # Also add the copied file to the list of compiled
                # files so it will be included in zipfile.
                for pattern in patterns:
                    pattern = os.path.join(*pattern.split('/'))
                    for f in glob.glob(os.path.join(package_dir, pattern)):
                        name = os.path.basename(f)
                        folder = os.path.join(collect_dir, os.path.dirname(f))
                        if not os.path.exists(folder):
                            self.mkpath(folder)
                        self.copy_file(f, os.path.join(collect_dir, name))
                        self.compiled_files.append(os.path.join(package_dir,
                            name))

except ImportError:
    # pylint: disable-msg=C0103
    # pylint thinks this is a const, which it isn't
    PkgResourceBuilder = None

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
            packages = find_packages(exclude=['sutekh.tests.*',
                'sutekh.tests']),
            package_data = {
                # NOTE: PkgResourceBuilder cannot handle the
                #   catch-all empty package ''.
                # Include SVG and INI files from sutekh.gui package
                'sutekh.gui': ['*.svg', '*.ini'],
                # Include LICENSE information for sutekh package
                # Include everything under the docs directory
                'sutekh': ['COPYING'],
                'sutekh.docs.html': ['*'],
            },
            entry_points = {
                'console_scripts' : ['sutekh-cli = sutekh.SutekhCli:main'],
                'gui_scripts' : ['sutekh = sutekh.SutekhGui:main'],
                },

            # py2exe
            console = ['sutekh/SutekhCli.py', 'sutekh/TestConsole.py'],
            windows = [{
                'script': 'sutekh/SutekhGui.py',
                'icon_resources': [(0, "artwork/sutekh-icon-inkscape.ico")],
            }],
            cmdclass = {
                'py2exe': PkgResourceBuilder,
            },
            options = { 'py2exe': {
                'dist_dir': 'build/sutekh-%s-py2exe' % SutekhInfo.VERSION_STR,
                'packages': [
                    'logging', 'encodings', 'sqlite3',
                ],
                'includes': [
                    # gtk
                    'cairo', 'pango', 'gobject', 'atk', 'pangocairo', 'gio',
                    # configobj
                    'configobj', 'validate',
                    # plugin only dependencies
                    'webbrowser', 'csv',
                    # plugins
                    'sutekh.gui.plugins.*',
                ],
                'excludes': [
                ],
                'ignores': [
                    # all database modules except sqlite3
                    'pgdb', 'Sybase', 'adodbapi',
                    'kinterbasdb', 'psycopg', 'psycopg2', 'pymssql',
                    'sapdb', 'pysqlite2', 'sqlite',
                    'MySQLdb', 'MySQLdb.connections',
                    'MySQLdb.constants.CR', 'MySQLdb.constants.ER',
                    # old datetime equivalents
                    'DateTime', 'DateTime.ISO',
                    'mx', 'mx.DateTime', 'mx.DateTime.ISO',
                    # email modules
                    'email.Generator', 'email.Iterators', 'email.Utils',
                    # GDK related imports we can ignore
                    'gdk', 'ltihooks',
                    # ignore things include in Python >= 2.5
                    'elementtree.ElementTree',
                ],
            }},
            data_files = [
                ('share/doc/python-sutekh', [
                    'COPYRIGHT',
                    'sutekh/COPYING',
                ]),
            ],
        )
