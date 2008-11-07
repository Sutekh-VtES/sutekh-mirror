; Copyright 2007, 2008 Simon Cross <hodgestar@gmail.com>
; GPL - see COPYING for details
; Compile with makensis sutekh-setup.nsi
; You'll need to have all the files listed under dependencies present

  !include "MUI.nsh"

; Application Details

  !define SUTEKH_VERSION "0.0.0" ; set by sutekh-makensis

  Name "Sutekh"
  OutFile "sutekh-${SUTEKH_VERSION}-upgrade.exe"
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

  !define SUTEKH_FOLDER "sutekh"
  !define DIST_FOLDER "dist"
  !define DEPENDENCIES_FOLDER "." ; set by sutekh-makensis

  !define SUTEKH_EGG "Sutekh-${SUTEKH_VERSION}-py2.5.egg"
  !define SUTEKH_ICON "sutekh.ico"

  !define COMBINED_LICENSE "GPLv2.txt"

; Pages

  !insertmacro MUI_PAGE_LICENSE "${DEPENDENCIES_FOLDER}/${COMBINED_LICENSE}"
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES
  
; Languages

  !insertmacro MUI_LANGUAGE "English"

; Other Stuff

  Icon "${DEPENDENCIES_FOLDER}/${SUTEKH_ICON}"

; Installer Sections

Section "Sutekh"
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  SetOutPath "$INSTDIR"

  File "${DIST_FOLDER}/${SUTEKH_EGG}"
  File "${DEPENDENCIES_FOLDER}/${SUTEKH_ICON}"

  ExecWait '$INSTDIR\Python\Scripts\easy_install.exe --no-deps "$INSTDIR\${SUTEKH_EGG}"'

  delete $INSTDIR\${SUTEKH_EGG}

  CreateDirectory "$SMPROGRAMS\Sutekh"
  # link.lnk target.exe
  #   parameters icon.file icon_index_number start_options 
  #   keyboard_shortcut description
  CreateShortCut "$SMPROGRAMS\Sutekh\SutekhGui ${SUTEKH_VERSION}.lnk" "$INSTDIR\Python\Scripts\SutekhGui.py" \
     "" "$INSTDIR\${SUTEKH_ICON}" "" SW_SHOWNORMAL \
     "" "Sutekh VtES Collection Manager"

SectionEnd

UninstallText "This will uninstall Sutekh ${SUTEKH_VERSION}."
UninstallIcon "${DEPENDENCIES_FOLDER}/${SUTEKH_ICON}"

Section "Uninstall"
  ; TODO: - Test this section

  ; Other things
  Delete "$INSTDIR\${SUTEKH_ICON}"

  ; Final Clean up (no point doing them while the uninstall is incomplete)
  ; Delete "$INSTDIR\Uninstall.exe"
  ; RMDir "$INSTDIR"
SectionEnd
