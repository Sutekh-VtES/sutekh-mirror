# Run the tests using the created ve

set -e

# We need to use -l when calling the script to get all the correct msys environment
# variables set, but that also changes the directory away from appveyors checkout
# location, and the mapping of windows paths into msys means we can't us %CD%
# to get the correct path without further munging, so we hardcode the path for now
#
# Is this entirely static? Don't know, but seems to work.
cd /c/projects/sutekh-mirror/sutekh

# Finally we can try run the tests - same explicit path requirements apply as
# for pip
/mingw64/bin/pytest
