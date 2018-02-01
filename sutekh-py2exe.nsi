; Copyright 2010 Simon Cross <hodgestar@gmail.com>
; GPL - see COPYING for details
; Compile with sutekh-makensis sutekh-py2exe.nsi .
; You'll need to have previously run sutekh-wine-py2exe

  !include "MUI.nsh"

; Application Details

  !define SUTEKH_VERSION "0.0.0" ; set by sutekh-makensis
  !define SUTEKH_UNPACK "sutekh-${SUTEKH_VERSION}-py2exe"
  !define ARTWORK_FOLDER "artwork"
  !define DIST_FOLDER "dist"

; vcredist_x86.exe details
  !define MISC_FOLDER "dist/misc"
  !define VCREDIST "vcredist_x86.exe"
  !define VCREDIST_KEY "{FF66E9F6-83E7-3A3E-AF14-8DE9A809A6A4}"

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
  !define SUTEKH_PY2EXE_ZIP "sutekh-${SUTEKH_VERSION}.zip"
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

; Installer for the vcredist_x86.exe stuff
; TODO: This only 32bit support - Do we need to support the 64bit version?

Section "vcredist"

  SetOutPath "$INSTDIR"
  File "${MISC_FOLDER}\${VCREDIST}"
   ; Check if it's already installed by checking for the uninstall key
   ; Idea and key value to check taken post and comments at:
   ; http://blogs.msdn.com/b/astebner/archive/2009/01/29/9384143.aspx

   ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${VCREDIST_KEY}" UninstallString
   ; NSIS docs say if the key doesn't exist, we get an error and an empty string
   IfErrors install done

install:
   ; Runs install with progress bar and no cancel button
   ; Details taken from
   ; http://blogs.msdn.com/b/astebner/archive/2010/10/18/9513328.aspx

   DetailPrint "Installing required MS runtime libraries"
   ExecWait "$INSTDIR/${VCREDIST} /qb!"

done:

   DetailPrint "MS runtime libraries already installed, skipping"

SectionEnd

; Installer Sections

Section "Sutekh"
  SetOutPath "$INSTDIR"

  WriteUninstaller "$INSTDIR\${UNINSTALLER}"

  File "${DIST_FOLDER}\${SUTEKH_PY2EXE_ZIP}"
  File "${ARTWORK_FOLDER}\${SUTEKH_ICON}"

  ZipDLL::extractall "$INSTDIR\${SUTEKH_PY2EXE_ZIP}" "$INSTDIR"
  Delete "$INSTDIR\${SUTEKH_PY2EXE_ZIP}"

  CreateDirectory "$SMPROGRAMS\Sutekh"

  # link.lnk target.exe
  #   parameters icon.file icon_index_number start_options
  #   keyboard_shortcut description

  CreateShortCut "$SMPROGRAMS\Sutekh\Sutekh ${SUTEKH_VERSION}.lnk" "$INSTDIR\${SUTEKH_UNPACK}\SutekhGui.exe" \
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

  ; Remove py2exe folder
  RMDir /r /REBOOTOK "$INSTDIR\${SUTEKH_UNPACK}"

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
