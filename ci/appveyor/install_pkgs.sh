# Install the required packages

# Do any pending updates
#pacman -Syu --needed --noconfirm
#pacman -Su --noconfirm
# Note that we install pip for the mingw 64bit python, not the msys64 one, since that's
# the only one for which python-gobject is available
pacman -S --noconfirm mingw-w64-x86_64-gtk3 mingw-w64-x86_64-python-pip mingw-w64-x86_64-python-gobject
