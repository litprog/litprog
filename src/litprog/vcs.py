# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
#
# Originally based on bumpver/vcs.py of https://github.com/mbarkhau/bumpver
# bumpversion project: https://github.com/peritus/bumpversion
# Copyright (c) 2013-2014 Filip Noetzel - MIT License

"""Minimal Git and Mercirial API.

If terminology for similar concepts differs between git and
mercurial, then the git terms are used. For example "fetch"
(git) instead of "pull" (hg) .
"""

import os
import re
import sys
import json
import shlex
import typing as typ
import logging
import pathlib as pl
import tempfile
import subprocess as sp

logger = logging.getLogger("litprog.vcs")


VCS_SUBCOMMANDS_BY_NAME = {
    'git': {
        'is_usable' : "git rev-parse --git-dir",
        'status'    : "git status --porcelain",
        'head_rev'  : "git rev-parse HEAD",
        'logs'      : "git log --format=fuller --date iso --stat",
        'logs_since': "git log --format=fuller --date iso --stat '{latest_sha}..HEAD'",
    },
    'hg': {
        'is_usable' : "hg root",
        'status'    : "hg status -umard",
        'head_rev'  : "hg --debug id -i",
        'logs'      : "NOT_IMPLEMENTED",
        'logs_since': "NOT_IMPLEMENTED",
    },
}


# commit parsing regexps

COMMIT_RE = re.compile(r"commit ([0-9a-f]*)")
AUTHOR_RE = re.compile(r"Author: (.*) <(.*)>")
DATE_RE   = re.compile(r"AuthorDate: (\d\d\d\d-[0-2][0-9]-[0-3][0-9]) (.*)")

# https://regex101.com/r/Xt8Ua3/1
#
# times_log.png        |     Bin 0 -> 4511 bytes
# stats.txt            |       0
# times.csv            |     170 +
# litprog/__init__.py  |       0
# README.md            |      23 ++++++++---------------
FILE_PAT = r"""
    [ ](.*?)
    [ ]+\|[ ]+
    (\d+|Bin)
    [ ]?
    ([+]+)?
    ([-]+)?
"""
FILE_RE = re.compile(FILE_PAT, re.VERBOSE)


SUMMARY_PAT = r"""
    [ ]
    (\d+[ ]files?[ ]changed)?
    (,[ ]\d+[ ]insertions?\(\+\))?
    (,[ ]\d+[ ]deletions?\(\-\))?
"""
SUMMARY_RE = re.compile(SUMMARY_PAT, re.VERBOSE)


# types

Env = typ.Dict[str, str]


class Change(typ.NamedTuple):
    filename     : str
    changed_lines: int
    added_rel    : int
    deleted_rel  : int


class Commit(typ.NamedTuple):
    commit : str  # sha hex hash
    author : str
    email  : str
    date   : str  # YYYY-MM-DD
    changes: typ.Tuple[Change, ...]


CommitKW = typ.Dict[str, typ.Any]


def dump_commits(commits: typ.Iterable[Commit]) -> typ.Iterable[CommitKW]:
    for commit in commits:
        commit_kw = commit._asdict()
        commit_kw['changes'] = [change._asdict() for change in commit.changes]
        yield commit_kw


def load_commits(commit_kws: typ.Iterable[CommitKW]) -> typ.Iterable[Commit]:
    for commit_kw in commit_kws:
        commit_kw['changes'] = tuple(Change(**change_kw) for change_kw in commit_kw['changes'])
        yield Commit(**commit_kw)


def _is_valid_commit_line(line: str) -> bool:
    return (
        # ignore empty lines
        bool(line.strip())
        # ignore commit message (4 empty spaces)
        and not line.startswith("    ")
        # Merge: xxxx xxxx
        and not line.startswith('Merge')
        and not line.startswith("Commit:")
        and not line.startswith("CommitDate:")
    )


def _parse_change(change_args: typ.Sequence[str]) -> Change:
    if change_args[1] == 'Bin':
        changed_lines = 0
        add_rel       = 0
        del_rel       = 0
    else:
        changed_lines = int(change_args[1])
        add_rel       = len(change_args[2] or "")
        del_rel       = len(change_args[3] or "")

    # TODO (mb 2021-01-21): better parsing of changed filename
    #    '{static => src/litprog/static}/pdf_modal.css',
    return Change(
        filename=change_args[1],
        changed_lines=changed_lines,
        added_rel=add_rel,
        deleted_rel=del_rel,
    )


def parse_commits(lines: typ.Iterable[str]) -> typ.Iterable[Commit]:
    commit_kw: typ.Dict[str, str] = {}
    changes  : typ.List[Change] = []

    for line in lines:
        if _is_valid_commit_line(line):
            match = SUMMARY_RE.match(line)
            if match and any(match.groups()):
                continue

            match = COMMIT_RE.match(line)
            if match:
                if commit_kw:
                    # reached next commit, previous one can be yielded
                    yield Commit(changes=tuple(changes), **commit_kw)

                commit_kw = {'commit': match.group(1)}
                changes   = []
                continue

            match = AUTHOR_RE.match(line)
            # Author: Xxxx Yyyy <xxxx@xxxx.com>
            if match:
                commit_kw['author'] = match.group(1)
                commit_kw['email' ] = match.group(2)
                continue

            match = DATE_RE.match(line)
            if match:
                date = match.group(1)
                commit_kw['date'] = date
                continue

            match = FILE_RE.match(line)
            if match:
                changes.append(_parse_change(match.groups()))
                continue

            logger.warning("Unexpected Line: " + repr(line))

    if commit_kw:
        yield Commit(changes=tuple(changes), **commit_kw)


class VCSAPI:
    """Absraction for git and mercurial."""

    def __init__(self, name: str, subcommands: typ.Dict[str, str] = None):
        self.name = name
        # TODO (mb 2021-01-28): Check if project path should be parameterized.
        self.project_path = pl.Path(os.getcwd()).absolute()

        if subcommands is None:
            self.subcommands = VCS_SUBCOMMANDS_BY_NAME[name]
        else:
            self.subcommands = subcommands

    def __call__(self, cmd_name: str, env: Env = None, **kwargs: str) -> str:
        """Invoke subcommand and return output."""
        prev_cwd = pl.Path(os.getcwd()).absolute()
        try:
            if prev_cwd != self.project_path:
                os.chdir(str(self.project_path))

            cmd_tmpl  = self.subcommands[cmd_name]
            cmd_str   = cmd_tmpl.format(**kwargs)
            cmd_parts = shlex.split(cmd_str)
            output_data: bytes = sp.check_output(cmd_parts, env=env, stderr=sp.STDOUT)
            return output_data.decode("utf-8")
        finally:
            if prev_cwd != self.project_path:
                os.chdir(str(prev_cwd))

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
        return [filepath.strip().split(" ", 1)[-1] for status, filepath in status_items if status != "??"]

    def head_rev(self) -> str:
        output = self('head_rev')
        return output.strip()

    def _tmp_filepath(self) -> pl.Path:
        cache_dir = "litprog_tmp_20210114t2006"  # change this if the cache format changes
        cache_id, _ = re.subn(r"[^\w]", "_", str(self.project_path))
        cache_filename = "commits_cache_" + cache_id + ".json"
        cache_dirpath  = pl.Path(tempfile.gettempdir()) / cache_dir
        if not cache_dirpath.exists():
            cache_dirpath.mkdir()
        return cache_dirpath / cache_filename

    def _write_commits(self, commits: typ.List[Commit]) -> None:
        cache_data = json.dumps(list(dump_commits(commits)))
        with self._tmp_filepath().open(mode="w") as fobj:
            fobj.write(cache_data)

    def commits(self) -> typ.List[Commit]:
        if self._tmp_filepath().exists():
            with self._tmp_filepath().open(mode="r") as fobj:
                commits = list(load_commits(json.load(fobj)))
            output      = self('logs_since', latest_sha=commits[0].commit)
            log_lines   = output.splitlines()
            new_commits = list(parse_commits(log_lines))
            if new_commits:
                commits = new_commits + commits
                self._write_commits(commits)
            return commits
        else:
            output    = self('logs')
            log_lines = output.splitlines()
            commits   = list(parse_commits(log_lines))
            self._write_commits(commits)
            return commits

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
    import pretty_traceback

    pretty_traceback.install(envvar='ENABLE_PRETTY_TRACEBACK')
    sys.exit(main())
