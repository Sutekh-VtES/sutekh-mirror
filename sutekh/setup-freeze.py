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
import tempfile

from subprocess import check_call


from setuptools import find_packages
from cx_Freeze import setup, Executable

sys.path.append('sutekh')
SutekhInfo = importlib.import_module("SutekhInfo").SutekhInfo

binary_include_files = []
guibase = None
base = None

build_exe_options = {
    'includes': ['sqlobject.boundattributes', 'sqlobject.declarative',
                 'packaging.specifiers', 'packaging.requirements', 'packaging.version',
                 'plistlib'],
    # We need to exclude DateTime to avoid sqlobject trying (and failing) to import it
    # in col.py
    # We exclude some other unneeded packages to reduce bloat
    'excludes': ['DateTime', 'tkinter', 'test'],
    'include_files': [
         # Include docs
         (os.path.join('sutekh', 'docs', 'html_docs'),
             os.path.join('sutekh', 'docs', 'html_docs')),
         ('artwork', 'artwork'),
    ],
    # Includes doesn't include all the files, so we need to use packages for
    # the plugins
    'packages': ['gi', 'cairo', 'sutekh.base.gui.plugins', 'sutekh.gui.plugins'],
}

build_mac_options = {}


# Heavily based off https://github.com/achadwick/hello-cxfreeze-gtk
if sys.platform == 'win32':
    guibase = "gui"
    sysbase = sys.prefix

    # Include MS redistributable stuff
    build_exe_options['include_msvcr'] = True

    # Find windows dlls and make sure they're in place

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

elif sys.platform == 'darwin':
    # Homebrew uses different prefixes depending on platform, so we need to
    # check both
    opt_path = os.path.join('/', 'opt', 'homebrew')
    usr_path = os.path.join('/', 'usr', 'local')
    if os.path.exists(opt_path):
        sysbase = opt_path
    else:
        sysbase = usr_path
else:
    raise RuntimeError("Our setup-freeze.py currently only supports windows or MacOS")


# Find typelib files
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
     "freetype2-2.0",
]

for ns in required_gi_namespaces:
    subpath = f"lib/girepository-1.0/{ns}.typelib"
    fullpath = os.path.join(sysbase, subpath)
    assert os.path.isfile(fullpath), f"Required file {fullpath} is missing"
    binary_include_files.append((fullpath, subpath))


build_exe_options['include_files'].extend([
    (os.path.join(sysbase, 'share', 'icons', 'Adwaita'),
        os.path.join('share', 'icons', 'Adwaita')),
    (os.path.join(sysbase, 'share', 'icons', 'hicolor'),
        os.path.join('share', 'icons', 'hicolor')),
    (os.path.join(sysbase, 'share', 'glib-2.0', 'schemas'),
        os.path.join('share', 'glib-2.0', 'schemas')),
    (os.path.join(sysbase, 'lib', 'gtk-3.0'),
        os.path.join('lib', 'gtk-3.0')),
    (os.path.join(sysbase, 'lib', 'gdk-pixbuf-2.0', '2.10.0', 'loaders'),
        os.path.join('lib', 'gdk-pixbuf-2.0', '2.10.0', 'loaders')),
])


build_exe_options['include_files'].extend(binary_include_files)

if sys.platform == 'win32':
    # Add loaders cache
    build_exe_options['include_files'].extend([
        (os.path.join(sysbase, 'lib', 'gdk-pixbuf-2.0', '2.10.0', 'loaders.cache'),
            os.path.join('lib', 'gdk-pixbuf-2.0', '2.10.0', 'loaders.cache')),
    ])
else:
    # On MacOS, we need to rewrite the loader to use local paths
    data = open(os.path.join(sysbase, 'lib', 'gdk-pixbuf-2.0', '2.10.0', 'loaders.cache')).read()
    # This is a bit hacky, but we don't want to overwrite the actual loaders.cache file and we
    # need this to stick around until the freeze step has finished
    tempdir = tempfile.mkdtemp()
    new_cache = open(os.path.join(tempdir, 'loaders.cache'), 'w')
    for line in data.splitlines():
        line=line.strip()
        if sysbase in line:
            line = line.replace(sysbase + '/', '@executable_path/')
        new_cache.write(line)
        new_cache.write('\n')
    new_cache.close()
    build_exe_options['include_files'].extend([
        (os.path.join(tempdir, 'loaders.cache'),
            os.path.join('lib', 'gdk-pixbuf-2.0', '2.10.0', 'loaders.cache')),
    ])


# Import ssl for the ssl hook
import ssl
ssl_paths = ssl.get_default_verify_paths()
try:
    # Need to use certifi if it's there, as it overwrites the ssl
    # one
    import certifi
    build_exe_options['include_files'].append(
        (certifi.where(), os.path.join('etc', 'ssl', 'cert.pem')))
except ImportError:
    build_exe_options['include_files'].append(
        (ssl_paths.openssl_cafile, os.path.join('etc', 'ssl', 'cert.pem')))
if os.path.exists(ssl_paths.openssl_capath):
    build_exe_options['include_files'].append(
        (ssl_paths.openssl_capath, os.path.join('etc', 'ssl', 'certs')))


# The logic here is a bit fincky - on MacOS we need to use the shell script to
# launch the actual app in a terminal, but because of how app packages
# work, we need to fiddle with the included file and the Info.plist
# file via the plist_items options
if sys.platform == 'darwin':
    build_exe_options['include_files'].append(('scripts/macos_launcher', 'scripts/macos_launcher'))
    build_exe_options['include_files'].append(('scripts/gui_wrapper', 'scripts/gui_wrapper'))
    build_mac_options['plist_items'] = [('CFBundleExecutable', 'scripts/macos_launcher')]


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
                "bdist_mac": build_mac_options,
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
