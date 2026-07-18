from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'packages': ['tkinterdnd2'],
    'iconfile': 'icon.icns',
    'plist': {
        'CFBundleName': 'DPI DOCTOR',
        'CFBundleDisplayName': 'DPI DOCTOR',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
    },
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
