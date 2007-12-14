; Copyright 2007 Simon Cross <hodgestar@gmail.com>
; GPL - see COPYING for details
; Compile with makensis sutekh-setup.nsi
; You'll need to have all the files listed under dependencies present

  !include "MUI.nsh"

; Application Details

  !define SUTEKH_VERSION "0.5.0"

  Name "Sutekh"
  OutFile "sutekh-${SUTEKH_VERSION}-setup.exe"
  InstallDir "$PROGRAMFILES\Sutekh"
  
; Interface Settings

  !define MUI_ABORTWARNING

  !define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\arrow-install.ico"
  !define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\arrow-uninstall.ico"

  !define MUI_HEADERIMAGE
  !define MUI_HEADERIMAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Header\orange.bmp"
  !define MUI_HEADERIMAGE_UNBITMAP "${NSISDIR}\Contrib\Graphics\Header\orange-uninstall.bmp"

; Dependencies 

  ; These files should be on the same directory as
  ; this script

  !define GTK_INSTALLER "gtk-dev-2.10.11-win32-1.exe"
  !define PYTHON_INSTALLER "python-2.5.msi"
  !define PYGTK_INSTALLER "pygtk-2.10.4-1.win32-py2.5.exe"
  !define PYCAIRO_INSTALLER "pycairo-1.2.6-1.win32-py2.5.exe"
  !define PYGOBJECT_INSTALLER "pygobject-2.12.3-1.win32-py2.5.exe"
  !define LIBXML_INSTALLER "libxml2-python-2.6.27.win32-py2.5.exe"
  !define PYXML_INSTALLER "PyXML-0.8.4.win32-py2.5.exe"
  !define SETUPTOOLS_INSTALLER "setuptools-0.6c7.win32-py2.5.exe"
  !define PYPROTOCOLS_EGG "PyProtocols-1.0a0-py2.5-win32.egg"
  !define PLY_EGG "ply-2.3-py2.5.egg"
  !define FORMENCODE_EGG "FormEncode-0.7.1-py2.5.egg"
  !define SQLOBJECT_EGG "SQLObject-0.9.1-py2.5.egg"
  !define SUTEKH_EGG "Sutekh-0.5.0-py2.5.egg"

  !define COMBINED_LICENSE GPLv2.txt

; Pages

  !insertmacro MUI_PAGE_LICENSE ${COMBINED_LICENSE} 
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES
  
; Languages

  !insertmacro MUI_LANGUAGE "English"

; Other Stuff

  SetCompress off ; all the big stuff is already compressed 

; Installer Sections

Section "GTK" 
  ;TODO: Check if already installed; Check upgrade.
  ;The Gaim installer has interesting bits (http://gaim.sf.net)

  SetOutPath "$INSTDIR"
  File ${GTK_INSTALLER}

  ;Installing
  ExecWait '"$INSTDIR\${GTK_INSTALLER}" /S /D=$INSTDIR\GTK'
  delete "$INSTDIR\${GTK_INSTALLER}"

  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Python"
  ; TODO: - Check if Python is already installed
  ;       - Somehow obtain path to Python/Scripts if it is
  ;       - Check if msiexec exists and point the user to the
  ;         appropriate URLs if it isn't:
  ;          Win 95, 98, Me: http://www.microsoft.com/downloads/details.aspx?FamilyID=cebbacd8-c094-4255-b702-de3bb768148f&displaylang=en
  ;          Win NT, 2000: http://www.microsoft.com/downloads/details.aspx?FamilyID=4b6140f9-2d36-4977-8fa1-6f8a0f5dca8f&DisplayLang=en

  SetOutPath "$INSTDIR"
  File "${PYTHON_INSTALLER}"

  ExecWait 'msiexec /package "$INSTDIR\${PYTHON_INSTALLER}" /passive /norestart TARGETDIR="$INSTDIR\Python\"'

  delete "$INSTDIR\${PYTHON_INSTALLER}"
SectionEnd

Section "PyGTK, PyCairo and PyGObject"
  ; TODO: - Make installation non-interactive

  SetOutPath "$INSTDIR"

  File ${PYGTK_INSTALLER}
  File ${PYCAIRO_INSTALLER}
  File ${PYGOBJECT_INSTALLER}

  ExecWait $INSTDIR\${PYGTK_INSTALLER}
  ExecWait $INSTDIR\${PYCAIRO_INSTALLER}
  ExecWait $INSTDIR\${PYGOBJECT_INSTALLER}

  delete $INSTDIR\${PYGTK_INSTALLER}
  delete $INSTDIR\${PYCAIRO_INSTALLER}
  delete $INSTDIR\${PYGOBJECT_INSTALLER}
SectionEnd

Section "LibXML2"
  SetOutPath "$INSTDIR"
 
  File ${LIBXML_INSTALLER}

  ExecWait $INSTDIR\${LIBXML_INSTALLER}

  delete $INSTDIR\${LIBXML_INSTALLER}
SectionEnd

Section "PyXML"
  SetOutPath "$INSTDIR"
 
  File ${PYXML_INSTALLER}

  ExecWait $INSTDIR\${PYXML_INSTALLER}

  delete $INSTDIR\${PYXML_INSTALLER}
SectionEnd

Section "Setuptools"
  SetOutPath "$INSTDIR"
 
  File ${SETUPTOOLS_INSTALLER}

  ExecWait $INSTDIR\${SETUPTOOLS_INSTALLER}

  delete $INSTDIR\${SETUPTOOLS_INSTALLER}
SectionEnd

Section "PyProtocols"
  SetOutPath "$INSTDIR"

  File ${PYPROTOCOLS_EGG}

  ExecWait '$INSTDIR\Python\Scripts\easy_install.exe --no-deps "$INSTDIR\${PYPROTOCOLS_EGG}"'

  delete $INSTDIR\${PYPROTOCOLS_EGG}
SectionEnd

Section "Ply"
  SetOutPath "$INSTDIR"

  File ${PLY_EGG}

  ExecWait '$INSTDIR\Python\Scripts\easy_install.exe --no-deps "$INSTDIR\${PLY_EGG}"'

  delete $INSTDIR\${PLY_EGG}
SectionEnd

Section "FORMEncode"
  SetOutPath "$INSTDIR"

  File ${FORMENCODE_EGG}

  ExecWait '$INSTDIR\Python\Scripts\easy_install.exe --no-deps "$INSTDIR\${FORMENCODE_EGG}"'

  delete $INSTDIR\${FORMENCODE_EGG}
SectionEnd

Section "SQLObject"
  SetOutPath "$INSTDIR"

  File ${SQLOBJECT_EGG}

  ExecWait '$INSTDIR\Python\Scripts\easy_install.exe --no-deps "$INSTDIR\${SQLOBJECT_EGG}"'

  delete $INSTDIR\${SQLOBJECT_EGG}
SectionEnd

Section "Sutekh"
  SetOutPath "$INSTDIR"

  File ${SUTEKH_EGG}

  ExecWait '$INSTDIR\Python\Scripts\easy_install.exe --no-deps "$INSTDIR\${SUTEKH_EGG}"'

  delete $INSTDIR\${SUTEKH_EGG}

  CreateDirectory "$SMPROGRAMS\Sutekh"
  # link.lnk target.exe
  #   parameters icon.file icon_index_number start_options 
  #   keyboard_shortcut description
  CreateShortCut "$SMPROGRAMS\Sutekh\SutekhGui ${SUTEKH_VERSION}.lnk" "$INSTDIR\Python\Scripts\SutekhGui.py" \
     "" "$INSTDIR\Python\Scripts\SutekhGui.py" 2 SW_SHOWNORMAL \
     "" "Sutekh VtES Collection Manager"

SectionEnd

Section "Uninstall"
  ; TODO: - Unistall Python
  ;       - Test this section

  ; GTK Runtime
  ExecWait '"$INSTDIR\GTK\Uninstall.exe" /S'
  RMDir "$INSTDIR\GTK"

  ; PyGTK modules
  ExecWait '"$INSTDIR\Python\Removepygtk.exe"'
  ExecWait '"$INSTDIR\Python\Removepycairo.exe"'
  ExecWait '"$INSTDIR\Python\Removepygobject.exe"'

  ; Final Clean up (no point doing them while the uninstall is incomplete
  ; Delete "$INSTDIR\Uninstall.exe"
  ; RMDir "$INSTDIR"
SectionEnd
