#!/usr/bin/env python
# coding: utf-8
from cx_Freeze import setup, Executable

options = {
    'build_exe': {
        'packages': [
            'atexit',
        ],
        'excludes': [
            # 'tkinter',
        ],
    },
    'bdist_mac': {
        'bundle_name': 'sc_downloader',
        'iconfile': 'build-files/icon.icns',
        'custom_info_plist': 'build-files/Info.plist',
    },
    'bdist_dmg': {
        'volume_label': 'sc_downloader',
    },
}

setup(
    name='sc_downloader',
    version='0.1.0',
    description='Downloads music from Soundcloud.',
    options=options,
    executables=[Executable('soundcloud-dl')],
)
