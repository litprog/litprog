# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

###################################
#    This is a generated file.    #
# This file should not be edited. #
#  Changes will be overwritten!   #
###################################
import litprog.cli as sut


def test_sanity():
    assert sut.log.name == "litprog.cli"