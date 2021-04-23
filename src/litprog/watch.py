# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

"""Asynchronos polling based file system watching."""
import os
import sys
import glob
import time
import typing as typ
import logging
import pathlib as pl
import threading

logger = logging.getLogger("litprog.watch")


# Can be files, directories or glob strings
PathStrings = typ.Sequence[str]


def unix_ms() -> int:
    return int(round(time.time() * 1000))


def _iter_parent_dirs(path_strs: PathStrings) -> typ.Iterable[pl.Path]:
    for path_str in path_strs:
        path = pl.Path(path_str)
        if path.is_file():
            yield path.parent.absolute()
        elif path.is_dir():
            yield path.absolute()
        else:
            glob_path_strs = glob.glob(path_str)
            if glob_path_strs:
                for glob_path_str in glob_path_strs:
                    glob_path = pl.Path(glob_path_str)
                    if glob_path.is_dir():
                        yield glob_path.absolute()
                    else:
                        yield glob_path.parent.absolute()
            else:
                logger.warning(f"Invalid path: '{path_str}'")


# Debounce will delay invocation of the callback
# until the changes have settled.
DEBOUNCE_DELAY = 500

MIN_SLEEP_DURATION = 20
MAX_SLEEP_DURATION = 500


Change  = typ.Any
Changes = typ.Set[Change]


class Watcher:

    _watch_dirs : typ.List[str]
    _file_mtimes: typ.Dict[str, float]

    def __init__(self, path_strs: PathStrings) -> None:
        self._watch_dirs  = sorted({str(p) for p in _iter_parent_dirs(path_strs)})
        self._file_mtimes = {}
        self.refresh_mtimes()

    def _watch_file(self, path: str, new_changes: typ.Set[Change]) -> None:
        stat      = os.stat(path)
        mtime     = stat.st_mtime
        old_mtime = self._file_mtimes.get(path)
        self._file_mtimes[path] = mtime

        if old_mtime is None:
            new_changes.add(('added', path, stat))
        elif old_mtime != mtime:
            new_changes.add(('modified', path, stat))

    def _walk_dir(self, dirpath: str, new_changes: typ.Set[Change]) -> None:
        for entry in os.scandir(dirpath):
            if entry.is_dir():
                self._walk_dir(entry.path, new_changes)
            else:
                self._watch_file(entry.path, new_changes)

    def refresh_mtimes(self) -> None:
        for watch_dir in self._watch_dirs:
            self._walk_dir(watch_dir, set())

    def watch(self, callback: typ.Callable) -> None:
        def _watch_loop() -> None:
            sleep_duration = MIN_SLEEP_DURATION
            last_change    = unix_ms()
            changes: typ.Set[Change] = set()

            while True:
                new_changes: typ.Set[Change] = set()
                for watch_dir in self._watch_dirs:
                    self._walk_dir(watch_dir, new_changes)

                changes.update(new_changes)

                if changes:
                    now = unix_ms()
                    if now - last_change > DEBOUNCE_DELAY:
                        callback(changes)
                        changes.clear()

                    if new_changes:
                        last_change = now
                    sleep_duration = MIN_SLEEP_DURATION
                else:
                    sleep_duration = min(sleep_duration * 2, MAX_SLEEP_DURATION)

                time.sleep(sleep_duration / 1000)

        try:
            thread        = threading.Thread(target=_watch_loop)
            thread.daemon = True
            thread.start()
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            return


def main() -> None:
    watcher = Watcher(sys.argv)
    watcher.watch(print)


if __name__ == '__main__':
    main()
