# This file is part of the pycalver project
# https://github.com/mbarkhau/pycalver
#
# Copyright (c) 2018-2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
#
# bumpver/vcs.py (this file) is based on code from the
# bumpversion project: https://github.com/peritus/bumpversion
# Copyright (c) 2013-2014 Filip Noetzel - MIT License

"""Minimal Git and Mercirial API.

If terminology for similar concepts differs between git and
mercurial, then the git terms are used. For example "fetch"
(git) instead of "pull" (hg) .
"""

import os
import sys
import shlex
import typing as typ
import logging
import subprocess as sp

logger = logging.getLogger("litprog.vcs")


VCS_SUBCOMMANDS_BY_NAME = {
    'git': {
        'is_usable'   : "git rev-parse --git-dir",
        'status'      : "git status --porcelain",
        'head_rev'    : "git rev-parse HEAD",
    },
    'hg': {
        'is_usable'   : "hg root",
        'status'      : "hg status -umard",
        'head_rev'    : "hg --debug id -i",
    },
}


Env = typ.Dict[str, str]


class VCSAPI:
    """Absraction for git and mercurial."""

    def __init__(self, name: str, subcommands: typ.Dict[str, str] = None):
        self.name = name
        if subcommands is None:
            self.subcommands = VCS_SUBCOMMANDS_BY_NAME[name]
        else:
            self.subcommands = subcommands

    def __call__(self, cmd_name: str, env: Env = None, **kwargs: str) -> str:
        """Invoke subcommand and return output."""
        cmd_tmpl = self.subcommands[cmd_name]
        cmd_str  = cmd_tmpl.format(**kwargs)
        cmd_parts = shlex.split(cmd_str)
        output_data: bytes = sp.check_output(cmd_parts, env=env, stderr=sp.STDOUT)

        return output_data.decode("utf-8")

    def is_usable(self) -> bool:
        """Detect availability of subcommand."""
        if not os.path.exists(f".{self.name}"):
            return False

        cmd = self.subcommands['is_usable'].split()

        try:
            retcode = sp.call(cmd, stderr=sp.PIPE, stdout=sp.PIPE)
            return retcode == 0
        except OSError as err:
            if err.errno == 2:
                # git/mercurial is not installed.
                return False
            else:
                raise

    def status(self) -> typ.List[str]:
        """Get status lines."""
        status_output = self('status')
        status_items  = [line.split(" ", 1) for line in status_output.splitlines()]

        return [
            filepath.strip().split(" ", 1)[-1]
            for status, filepath in status_items
            if status != "??"
        ]

    def head_rev(self) -> str:
        output = self('head_rev')
        return output.strip()

    def __repr__(self) -> str:
        """Generate string representation."""
        return f"VCSAPI(name='{self.name}')"


def get_vcs_api() -> typ.Optional[VCSAPI]:
    """Detect the appropriate VCS for a repository.

    raises OSError if the directory doesn't use a supported VCS.
    """
    for vcs_name in VCS_SUBCOMMANDS_BY_NAME:
        vcs_api = VCSAPI(name=vcs_name)
        if vcs_api.is_usable():
            return vcs_api

    return None


def main() -> int:
    vcs_api = get_vcs_api()
    if vcs_api is None:
        print("no vcs")
    else:
        print("HEAD:", vcs_api.head_rev())
        for fpath in vcs_api.status():
            print("    ", repr(fpath))
    return 0


if __name__ == '__main__':
    sys.exit(main())
