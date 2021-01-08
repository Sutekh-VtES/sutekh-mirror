# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2007 Simon Cross <hodgestar@gmail.com>
# Copyright 2020 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL - see COPYING for details

# NB, this should be kept in sync with setup.py

"""cx_Freeze setup.py file for Sutekh.

   This exists for windows builds."""

# avoid importing all of Sutkeh and its dependencies
import importlib
import os
import sys

from subprocess import check_call


from setuptools import find_packages
from cx_Freeze import setup, Executable

sys.path.append('sutekh')
SutekhInfo = importlib.import_module("SutekhInfo").SutekhInfo


# Heavily based off https://github.com/achadwick/hello-cxfreeze-gtk
if sys.platform == 'win32':
    binary_include_files = []

    required_dll_search_paths = os.getenv("PATH", os.defpath).split(os.pathsep)
    required_dlls = [
        'libgtk-3-0.dll',
        'libgdk-3-0.dll',
        'libepoxy-0.dll',
        'libgdk_pixbuf-2.0-0.dll',
        'libpango-1.0-0.dll',
        'libpangocairo-1.0-0.dll',
        'libpangoft2-1.0-0.dll',
        'libpangowin32-1.0-0.dll',
        'libatk-1.0-0.dll',
        'librsvg-2-2.dll',
        'libjpeg-8.dll',
        'libpng16-16.dll',
    ]

    for dll in required_dlls:
        dll_path = None
        for p in required_dll_search_paths:
            p = os.path.join(p, dll)
            if os.path.isfile(p):
                dll_path = p
                break
        assert dll_path is not None, \
            f"Unable to locate {dll} in {required_dll_search_paths}"

        binary_include_files.append((dll_path, dll))

    required_gi_namespaces = [
        "Gtk-3.0",
        "Gdk-3.0",
        "cairo-1.0",
        "Pango-1.0",
        "PangoCairo-1.0",
        "PangoFT2-1.0",
        "GObject-2.0",
        "GLib-2.0",
        "Gio-2.0",
        "GdkPixbuf-2.0",
        "GModule-2.0",
        "Atk-1.0",
        "HarfBuzz-0.0",
        "Poppler-0.18",
    ]

    for ns in required_gi_namespaces:
        subpath = f"lib/girepository-1.0/{ns}.typelib"
        fullpath = os.path.join(sys.prefix, subpath)
        assert os.path.isfile(fullpath), f"Required file {fullpath} is missing"
        binary_include_files.append((fullpath, subpath))

    build_exe_options = {
        'includes': ['sqlobject.boundattributes', 'sqlobject.declarative',
                     'packaging.specifiers', 'packaging.requirements', 'packaging.version'],
        # We need to exclude DateTime to avoid sqlobject trying (and failing) to import it
        # in col.py
        # We exclude some other unneeded packages to reduce bloat
        'excludes': ['DateTime', 'tkinter', 'test'],
        'include_files': [
            # We should reduce the number of icons we copy
             (os.path.join(sys.prefix, 'share', 'icons', 'Adwaita'),
                 os.path.join('share', 'icons', 'Adwaita')),
             (os.path.join(sys.prefix, 'share', 'glib-2.0', 'schemas'),
                 os.path.join('share', 'glib-2.0', 'schemas')),
             (os.path.join(sys.prefix, 'lib', 'gtk-3.0'),
                 os.path.join('lib', 'gtk-3.0')),
             (os.path.join(sys.prefix, 'lib', 'gdk-pixbuf-2.0'),
                 os.path.join('lib', 'gdk-pixbuf-2.0')),
             #(os.path.join(sys.platform, 'gtk-3.0', 'gdk-pixbuf.loaders'),
             #    os.path.join('etc', 'gtk-3.0', 'gdk-pixbuf.loaders')),
             # Include docs
             (os.path.join('sutekh', 'docs', 'html_docs'),
                 os.path.join('sutekh', 'docs', 'html_docs')),
             ('artwork', 'artwork'),
        ],
        'include_msvcr': True,
        # Includes doesn't include all the files, so we need to use packages for
        # the plugins
        'packages': ['gi', 'cairo', 'sutekh.base.gui.plugins', 'sutekh.gui.plugins'],
    }

    build_exe_options['include_files'].extend(binary_include_files)

elif sys.platform == 'darwin':
    binary_include_files = []

    required_gi_namespaces = [
        "Gtk-3.0",
        "Gdk-3.0",
        "cairo-1.0",
        "Pango-1.0",
        "PangoCairo-1.0",
        "PangoFT2-1.0",
        "GObject-2.0",
        "GLib-2.0",
        "Gio-2.0",
        "GdkPixbuf-2.0",
        "GModule-2.0",
        "Atk-1.0",
        "Poppler-0.18",
    ]

    for ns in required_gi_namespaces:
        subpath = f"lib/girepository-1.0/{ns}.typelib"
        fullpath = os.path.join('/', 'usr', 'local', subpath)
        assert os.path.isfile(fullpath), f"Required file {fullpath} is missing"
        binary_include_files.append((fullpath, subpath))

    build_exe_options = {
        'includes': ['sqlobject.boundattributes', 'sqlobject.declarative',
                     'packaging.specifiers', 'packaging.requirements', 'packaging.version'],
        # We need to exclude DateTime to avoid sqlobject trying (and failing) to import it
        # in col.py
        # We exclude some other unneeded packages to reduce bloat
        'excludes': ['DateTime', 'tkinter', 'test'],
        'include_files': [
            # We should reduce the number of icons we copy
             (os.path.join('/', 'usr', 'local', 'share', 'icons', 'Adwaita'),
                 os.path.join('share', 'icons', 'Adwaita')),
             (os.path.join('/', 'usr', 'local', 'lib', 'gtk-3.0'),
                 os.path.join('lib', 'gtk-3.0')),
             (os.path.join('/', 'usr', 'local', 'lib', 'gdk-pixbuf-2.0'),
                 os.path.join('lib', 'gdk-pixbuf-2.0')),
             # Include docs
             (os.path.join('sutekh', 'docs', 'html_docs'),
                 os.path.join('sutekh', 'docs', 'html_docs')),
             #(os.path.join(sys.platform, 'gtk-3.0', 'gdk-pixbuf.loaders'),
             #    os.path.join('etc', 'gtk-3.0', 'gdk-pixbuf.loaders')),
             ('artwork', 'artwork'),
        ],
        # Includes doesn't include all the files, so we need to use packages for
        # the plugins
        'packages': ['gi', 'cairo', 'sutekh.base.gui.plugins', 'sutekh.gui.plugins'],
    }

    build_exe_options['include_files'].extend(binary_include_files)


guibase = None
# We'll probably need most of this for MacOS as well
if sys.platform == "win32":
    guibase = "Win32GUI"

if sys.platform in ['win32', 'darwin']:
    # Copy in ssl certs from msys2 installation
    import ssl
    ssl_paths = ssl.get_default_verify_paths()
    build_exe_options['include_files'].append(
            (ssl_paths.openssl_cafile, os.path.join('etc', 'ssl', 'cert.pem')))
    if os.path.exists(ssl_paths.openssl_capath):
        build_exe_options['include_files'].append(
                (ssl_paths.openssl_capath, os.path.join('etc', 'ssl', 'certs')))



setup   (   # Metadata
            name = SutekhInfo.NAME,
            version = SutekhInfo.VERSION_STR,
            description = SutekhInfo.DESCRIPTION,
            long_description = open('README', 'r').read(),

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
            python_requires = '>=3',

            # Files
            packages = find_packages(exclude=['sutekh.tests.*',
                'sutekh.tests', 'sutekh.base.tests']),
            package_data = {
                #   catch-all empty package ''.
                # Include SVG and INI files from sutekh.gui package
                'sutekh.gui': ['*.svg', '*.ini'],
                # need baseconfigspec.ini from sutekh.base.gui
                'sutekh.base.gui': ['*.ini'],
                # Include LICENSE information for sutekh package
                # Include everything under the docs directory
                'sutekh': ['COPYING'],
                'sutekh.docs.html_docs': ['*'],
            },
            entry_points = {
                'console_scripts' : ['sutekh-cli = sutekh.SutekhCli:main'],
                'gui_scripts' : ['sutekh = sutekh.SutekhGui:main'],
            },
            options = {
                "build_exe": build_exe_options,
            },
            executables = [Executable("sutekh/SutekhGui.py", icon="artwork/sutekh-icon-inkscape.ico",
                                      base=guibase),
                           Executable("sutekh/SutekhCli.py", base=None)],
            data_files = [
                ('share/doc/python-sutekh', [
                    'COPYRIGHT',
                    'sutekh/COPYING',
                ]),
            ],
        )
