# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

# After reading "https://apenwarr.ca/log/20181113" I've
# concluded, that we need to
#  1. create an index of files we care about, with
#   the os.stat result and content hash for every path
#  2. recalculate the content hash if
#   - anything from os.stat changes
#   - mtime is zero
#   - mtime is between now - estimated precision
# The estimated precision is based on the number of
# trailing zeros on the mtime.

# files that are dependencies must have an mtime
#   that is newer than the start time of the build.
#   In other words, dependencies are only considered
#   to be satisfied, if they were created/updated
#   after the build started.
#
#   https://docs.microsoft.com/en-us/windows/desktop/sysinfo/file-times
#   > create time on FAT is 10 milliseconds,
#   > while write time has a resolution of 2 seconds
#
# Better approach:
# - https://github.com/ziglang/zig/issues/2045

import os
import sys
import json
import time
import uuid
import socket
import typing as typ
import hashlib
import logging
import pathlib as pl

logger = logging.getLogger(__name__)


def _machine_id() -> str:
    """Generate machine specific id.

    The index is only valid if it was written by the same machine
    that it was generated on.

    An index might be shared if multiple builds run over an
    NFS file system. Raise an error if this is detected and
    include the path to the index file in the error message,
    so the user can decide if they want to delete it and
    rebuild from scratch.
    """
    node = uuid.getnode()
    if node & 0b10000000 > 0:
        # If all attempts to obtain the hardware address fail, we
        # choose a random 48-bit number with its eighth bit set to 1
        # as recommended in RFC 4122.
        node = 0

    host = socket.gethostname()
    return f"{node}_{host}"


IS_BLAKE2_AVAILABLE = False

try:
    hashlib.new('blake2b')
except ValueError as ex:
    assert "unsupported hash type blake2b" in str(ex)
    IS_BLAKE2_AVAILABLE = False


HexDigest = str


def _file_digest(path: pl.Path) -> HexDigest:
    # https://blake2.net/
    if IS_BLAKE2_AVAILABLE:
        id_sum = hashlib.new('blake2b')
    else:
        id_sum = hashlib.new('sha1')

    with path.open(mode="rb") as fobj:
        while True:
            chunk = fobj.read(65536)
            if chunk:
                id_sum.update(chunk)
            else:
                break
    return id_sum.hexdigest()


class CheckResult(typ.NamedTuple):
    # NOTE: If the digest is set, it is
    #   the fresh from disk, not from the cache.
    #   This is done so we don't have to
    #   calculate the digest twice; once when
    #   checking if an entry is valid, and once
    #   again when updating the entry.
    ok    : bool
    digest: HexDigest


EntryKey = str
Target   = str


def entry_key(path: pl.Path) -> EntryKey:
    return str(path.absolute())


# NOTE: mypy doesn't like the stat_result type :-/, so we
#   convert it to something it knows how to deal with.


class Stat(typ.NamedTuple):

    mode : int
    ino  : int
    dev  : int
    nlink: int
    uid  : int
    gid  : int
    size : int
    atime: float
    mtime: float
    ctime: float


def mk_stat(path: pl.Path) -> Stat:
    stat_result = path.stat()

    # NOTE: getmtime is more precise than stat_result.st_mtime
    mtime: float = os.path.getmtime(str(path))

    return Stat(
        stat_result.st_mode,
        stat_result.st_ino,
        stat_result.st_dev,
        stat_result.st_nlink,
        stat_result.st_uid,
        stat_result.st_gid,
        stat_result.st_size,
        stat_result.st_atime,
        mtime,
        stat_result.st_ctime,
    )


class IndexEntry(typ.NamedTuple):

    path  : pl.Path
    stat  : Stat
    digest: HexDigest


MaybeEntry        = typ.Optional[IndexEntry]
EntryByKey        = typ.Dict[EntryKey, MaybeEntry]
EntryKeysByTarget = typ.Dict[Target  , typ.Set[EntryKey]]


def make_entry(path: pl.Path, check: CheckResult) -> MaybeEntry:
    if path.exists():
        digest_val = check.digest or _file_digest(path)
        return IndexEntry(path=path, stat=mk_stat(path), digest=digest_val)
    else:
        return None


class Index:

    machine_id: str
    index_file: pl.Path
    # The index_stat serves two purposes:
    #   1. To detect a concurrent build
    #   2. To invalidate cached digest of recently
    #       updated files.
    index_stat: Stat

    entries: EntryByKey
    targets: EntryKeysByTarget

    def __init__(self, index_file: pl.Path) -> None:
        self.index_file = index_file
        self.machine_id = _machine_id()
        self.entries    = {}
        self.targets    = {}

        try:
            if self.index_file.exists():
                self.load_index()
        except (IOError, ValueError, KeyError):
            warn_msg = f"Ignoring invalid/corrupted index file " f"'{self.index_file}'"
            logger.warning(warn_msg, exc_info=True)

        self.index_file.touch()
        self.index_stat = mk_stat(self.index_file)

    def load_index(self) -> None:
        with self.index_file.open(mode="rb") as fobj:
            data = json.loads(fobj.read().decode('utf-8'))

        if data['machine_id'] != self.machine_id:
            err_msg = (
                f"Index file '{self.index_file}' possibly "
                "created on different machine. Aborting to"
                "avoid concurrent build from different hosts."
                "If you know this is not an issue, delete "
                "the file and try again."
            )
            raise ValueError(err_msg)

        entries: EntryByKey = {}
        for key, entry in data['entries'].items():
            if entry is None:
                entries[key] = entry
            else:
                entries[key] = IndexEntry(pl.Path(entry['path']), Stat(*entry['stat']), entry['digest'])

        targets: EntryKeysByTarget = {}
        for target, deps in data['targets'].items():
            targets[target] = set(deps)

        self.entries = entries
        self.targets = targets

    def dump_index(self) -> None:
        EntryData = typ.Optional[typ.Dict[str, typ.Any]]
        entries: typ.Dict[str, EntryData] = {}

        for key, entry in self.entries.items():
            if entry:
                entries[key] = {
                    'path'  : str(entry.path),
                    'stat'  : list(entry.stat),
                    'digest': entry.digest,
                }
            else:
                entries[key] = None

        targets = {target: list(deps) for target, deps in self.targets.items()}
        data    = {'machine_id': self.machine_id, 'entries': entries, 'targets': targets}

        nonce    = time.time()
        tmp_name = self.index_file.name + f".{nonce}.tmp"
        tmp_file = self.index_file.parent / tmp_name
        with tmp_file.open(mode="wb") as fobj:
            text = json.dumps(data, indent=2)
            fobj.write(text.encode("utf-8"))

        if self.has_index_changed():
            tmp_file.unlink()
            err_msg = "WARNING: Concurrent update of index detected. This may result in a corrupted build."
            raise Exception(err_msg)
        else:
            tmp_file.rename(self.index_file)

    def has_index_changed(self) -> bool:
        if not self.index_file.exists():
            return True
        elif self.index_stat != mk_stat(self.index_file):
            return True
        else:
            return False

    def add_files(self, paths: typ.Iterable[pl.Path]) -> None:
        for path in paths:
            self.add_file(path)

    def add_file(self, path: pl.Path) -> None:
        check = self.check_path(path)
        if check.ok:
            return

        entry = make_entry(path, check)
        self.entries[entry_key(path)] = entry

    def check_path(self, path: pl.Path) -> CheckResult:
        # NOTE: There could be different levels of
        #   dirtyness.
        #   strict: hash and mtime must be unchanged
        #   hash: hash must be unchanged
        if entry_key(path) not in self.entries:
            return CheckResult(False, "")

        entry = self.entries[entry_key(path)]
        if entry is None:
            return CheckResult(False, "")
        elif not entry.path.exists():
            return CheckResult(False, "")
        elif entry.stat != mk_stat(path):
            return CheckResult(False, "")
        elif entry.stat.mtime <= self.index_stat.mtime - 2:
            # If mtime is very new, then it can't be trusted.
            return CheckResult(True, entry.digest)
        else:
            # fallback to digest check
            new_digest = _file_digest(path)
            check_ok   = new_digest == entry.digest
            return CheckResult(check_ok, new_digest)

    def is_target_done(self, target: Target, deps: typ.Set[pl.Path]) -> bool:
        for dep in deps:
            digest = self.check_path(dep)
            if not digest.ok:
                return False

        new_deps  = {entry_key(dep) for dep in deps}
        prev_deps = self.targets.get(target)
        return new_deps == prev_deps

    def mark_target_done(self, target: Target, deps: typ.Set[pl.Path]) -> None:
        for dep in deps:
            self.add_file(dep)

        self.targets[target] = {entry_key(dep) for dep in deps}


def _iter_paths(dirpath: pl.Path) -> typ.Iterable[pl.Path]:
    for root, _dirnames, filenames in os.walk(dirpath):
        for filename in filenames:
            yield pl.Path(root) / filename


ExitStatus = int


def selftest() -> ExitStatus:
    dirpaths = [
        pl.Path("src"),
        pl.Path("src_v2"),
        pl.Path("lit_v2"),
        pl.Path("lit_v3"),
        pl.Path("fonts"),
    ]
    filepaths: typ.List[pl.Path] = []
    for dirpath in dirpaths:
        filepaths.extend(_iter_paths(dirpath))

    idx  = Index(pl.Path(".litprog.index"))
    deps = set(_iter_paths(pl.Path("lit_v3")))
    print("done?", idx.is_target_done('moep', deps))

    idx.mark_target_done('moep', deps)
    for dep in deps:
        dep.touch()
    print("done?", idx.is_target_done('moep', deps))
    assert not idx.is_target_done('moep', deps)
    idx.mark_target_done('moep', deps)

    idx.add_files(filepaths)
    idx.dump_index()
    return 0


if __name__ == '__main__':
    sys.exit(selftest())
