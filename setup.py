#!/usr/bin/env python3
from setuptools import setup

import pyrenamer

version = pyrenamer.anidb_client_version

setup(
    name='pyrenamer',
    version=str(version),
    description="Renamer for AniDB files",
    author="pzimmer",
    author_email="pz<at>ggdns.de",
    platforms=['any'],
    license="GPLv3",
    packages=['pyrenamer']
)
