'''py2exe build script for CodeCollaborator for UCM'''

# Copyright (c) 2006 by QUALCOMM INCORPORATED  All Rights Reserved.
# Miki Tebeka <mtebeka@qualcomm.com>

from distutils.core import setup
import py2exe

def win(name):
    return {
        "script" : name,
        "icon_resources" : [(1, "ucmcc.ico")]
    }

setup(windows = [win("ucmcc.py"), win("ucmcc_baseline.py")])
