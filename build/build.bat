@echo off
REM %USERPROFILE%\convimg_env\Scripts\activate
REM python -OO -m PyInstaller --onefile --version-file=file_version_info.txt --clean --icon=icon.ico --name=convimg ..\convimg.py --add-data="../LICENSE;." --noupx
pyinstaller convimg.spec
rmdir /s /q build
pause