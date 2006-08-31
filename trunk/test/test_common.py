# Test common module

# Copyright (c) 2006 by QUALCOMM INCORPORATED  All Rights Reserved.
# Miki Tebeka <mtebeka@qualcomm.com>

import support
from unittest import TestCase, main
from sys import path

import common

class TestCommon(TestCase):
    def test_get_views(self):
        '''Test get_views'''
        views = common.get_views()
        if views != VIEWS:
            self.fail("didn't get expected views")

    def test_APPDIR(self):
        '''Test APPDIR'''
        if common.APPDIR != path[0]:
            self.fail("bad value for APPDIR (%s)" % common.APPDIR)



if __name__ == "__main__":
    main()
