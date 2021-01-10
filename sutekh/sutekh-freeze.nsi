; Copyright 2010 Simon Cross <hodgestar@gmail.com>
; GPL - see COPYING for details
; Compile with sutekh-makensis sutekh-freeze.nsi .
; You'll need to have previously run setup-freeze.py build_exe

  !include "MUI.nsh"

; Application Details

  !define SUTEKH_VERSION "0.0.0" ; set by sutekh-makensis
  !define ARTWORK_FOLDER "artwork"
  !define DIST_FOLDER "dist"

  Name "Sutekh"
  OutFile "${DIST_FOLDER}\sutekh-${SUTEKH_VERSION}.exe"
  InstallDir "$PROGRAMFILES\Sutekh-${SUTEKH_VERSION}"

; Interface Settings

  !define MUI_ABORTWARNING

  !define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\arrow-install.ico"
  !define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\arrow-uninstall.ico"

  !define MUI_HEADERIMAGE
  !define MUI_HEADERIMAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Header\orange.bmp"
  !define MUI_HEADERIMAGE_UNBITMAP "${NSISDIR}\Contrib\Graphics\Header\orange-uninstall.bmp"

; Dependencies

  !define COMBINED_LICENSE "sutekh\COPYING"
  !define SUTEKH_ICON "sutekh-icon-inkscape.ico"
  !define SUTEKH_FREEZE_ZIP "sutekh-${SUTEKH_VERSION}.zip"
  !define UNINSTALLER "Uninstaller.exe"

; Pages

  !insertmacro MUI_PAGE_LICENSE "${COMBINED_LICENSE}"
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES

  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES

; Languages

  !insertmacro MUI_LANGUAGE "English"

; Other Stuff

  Icon "${ARTWORK_FOLDER}\${SUTEKH_ICON}"
  SetCompress off ; all the big stuff is already compressed

; Installer Sections

Section "Sutekh"
  SetOutPath "$INSTDIR"

  WriteUninstaller "$INSTDIR\${UNINSTALLER}"

  File "${DIST_FOLDER}\${SUTEKH_FREEZE_ZIP}"
  File "${ARTWORK_FOLDER}\${SUTEKH_ICON}"

  ZipDLL::extractall "$INSTDIR\${SUTEKH_FREEZE_ZIP}" "$INSTDIR"
  Delete "$INSTDIR\${SUTEKH_FREEZE_ZIP}"

  CreateDirectory "$SMPROGRAMS\Sutekh"

  # link.lnk target.exe
  #   parameters icon.file icon_index_number start_options
  #   keyboard_shortcut description

  CreateShortCut "$SMPROGRAMS\Sutekh\Sutekh ${SUTEKH_VERSION}.lnk" "$INSTDIR\SutekhGui.exe" \
     "" "$INSTDIR\${SUTEKH_ICON}" "" SW_SHOWNORMAL \
     "" "Sutekh VtES Collection Manager"

  CreateShortCut "$SMPROGRAMS\Sutekh\Uninstall Sutekh ${SUTEKH_VERSION}.lnk" "$INSTDIR\${UNINSTALLER}" \
     "" "" "" SW_SHOWNORMAL \
     "" "Uninstall Sutekh"

SectionEnd

UninstallText "This will uninstall Sutekh ${SUTEKH_VERSION}."
UninstallIcon "${ARTWORK_FOLDER}\${SUTEKH_ICON}"

Section "Uninstall"
  ; Delete files not deleted during install
  Delete "$INSTDIR\${SUTEKH_ICON}"

  ; Remove folder
  RMDir /r /REBOOTOK "$INSTDIR"

  ; Remove shortcut links
  Delete "$SMPROGRAMS\Sutekh\Sutekh ${SUTEKH_VERSION}.lnk"
  Delete "$SMPROGRAMS\Sutekh\Uninstall Sutekh ${SUTEKH_VERSION}.lnk"

  ; Remove shortcut folder if no links left
  IfFileExists "$SMPROGRAMS\Sutekh\*.lnk" shortcuts_exist 0
    RMDir /REBOOTOK "$SMPROGRAMS\Sutekh"
  shortcuts_exist:

  ; Final Clean up (no point doing this while the uninstall is incomplete)
  RMDir /r /REBOOTOK $INSTDIR

  ; Offer to reboot if needed
  IfRebootFlag 0 noreboot
    MessageBox MB_YESNO "A reboot is required to finish the uninstallation. Do you wish to reboot now?" IDNO noreboot
    Reboot
  noreboot:

  ; TODO: We don't touch the vcredist stuff, since we can't tell a) if we were
  ; the ones who installed it and b) if anything else needs it. This may cause
  ; cruft on the users system, so should we tell the user?

SectionEnd
