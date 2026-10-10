# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['../convimg.py'],
    pathex=[],
    binaries=[],
    datas=[('../LICENSE', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', '_tkinter', 'unittest', 'test', 'email', 'http', 
        'xmlrpc', 'html', 'sqlite3', 'pydoc', 
        'doctest', 'distutils', 'setuptools', 'pkg_resources', 
        'multiprocessing', 'pdb', 'ssl', 'asyncio', 'socket',
        'lib2to3', 'idlelib', 'turtle', 'ensurepip', 'venv', 
        'bz2', 'lzma', 'curses', 'smtplib', 'ftplib', 'poplib', 
        'imaplib', 'wsgiref', 'cgi', 'cgitb'
    ],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='convimg',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='file_version_info.txt',
    icon=['icon.ico'],
)
