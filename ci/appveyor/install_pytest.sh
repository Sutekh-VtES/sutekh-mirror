# Install a ve and sutekh's dependencies for the tests

set -e

# We use the explicit path, as, in addition to the multiple
# msys python versions, appveyor installs several official python
# installers as well, so `pip` is likely something different
# from what we want.
/mingw64/bin/pip install keyring ply sqlobject configobj pytest mock
