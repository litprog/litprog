###################################
#    This is a generated file.    #
# This file should not be edited. #
#  Changes will be overwritten!   #
###################################
import pathlib2 as pl
import litprog.cli
import litprog.parse as sut


def test_fs_scanning():
    lit_paths = list(litprog.cli._iter_markdown_filepaths(["lit/"]))

    assert len(lit_paths) > 0
    assert all(isinstance(p, pl.Path) for p in lit_paths)
    assert all(p.suffix == ".md" for p in lit_paths)
