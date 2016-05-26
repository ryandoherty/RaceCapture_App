# -*- mode: python -*-
# RaceCapture PyInstaller spec file. This builds a folder with the necessary files to
# run RaceCapture - it also includes *all* kv files and *all* ttf files from the
# RaceCapture folder and children. If we add kv or ttf files which are not to go in the distribution
# (or add any other file types that are required) then these will need to be manually
# enumerated in this file. CLR 2014-05-26
import os
import sys
from kivy.deps import sdl2, glew

def addDataFiles():
    allFiles = Tree('..//')
    extraDatas = []
    for file in allFiles:
        if file[0].endswith('.kv') | file[0].endswith('.ttf') | file[0].startswith('resource/') | file[0].startswith('resource\\') | (file[0] == 'LICENSE') | (file[0] == 'CHANGELOG.txt'):
            print "Adding datafile: " + file[0]
            extraDatas.append(file)
    return extraDatas

a = Analysis(['..//main.py'],
    pathex=['..//'],
    hiddenimports=['pygments.lexers.python.PythonLexer'],
    runtime_hooks=None)
a.datas += addDataFiles()
pyz = PYZ(a.pure)
exe = EXE(pyz,
    a.scripts,
    #[('v', None, 'OPTION')],
    exclude_binaries=True,
    name='racecapture' + ('.exe' if sys.platform == 'win32' else ''),
    icon='..//resource//images//app_icon_128x128.ico',
    version='temp_win_versioninfo.txt',
    debug=False,
    strip=None,
    upx=True,
    console=False )

coll = COLLECT(exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    strip=None,
    upx=True,
    name='racecapture')

if sys.platform == 'darwin':
    app = BUNDLE(coll,
        name='racecapture.app',
        icon='resource//race_capture_icon_large.icns')
