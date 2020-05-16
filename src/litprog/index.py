# This file is part of the litprog project
# https://gitlab.com/mbarkhau/litprog
#
# Copyright (c) 2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
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

import pathlib2 as pl

log = logging.getLogger(__name__)


def machine_id() -> str:
    """The index is only valid if it was written by the same machine
    that we're running on.

    This might happen if multiple buils run over an NFS file system.
    Raise an error if this is detected and include the path to the
    index file in the error message, so the user can decide if they
    want to delete it and rebuild from scratch.
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


def new_digest() -> hashlib._Hash:
    # https://blake2.net/
    if IS_BLAKE2_AVAILABLE:
        return hashlib.new('blake2b')
    else:
        return hashlib.new('sha1')


def file_digest(path: pl.Path) -> str:
    id_sum = new_digest()
    with path.open(mode="rb") as fh:
        while True:
            chunk = fh.read(65536)
            if chunk:
                id_sum.update(chunk)
            else:
                break
    return id_sum.hexdigest()


def file_id(path: pl.Path) -> str:
    st     = mk_stat(path)
    st_str = f"{st.ino}_{st.size}_{st.mtime}"
    id_sum = new_digest()
    id_sum.update(st_str.encode("ascii"))
    return id_sum.hexdigest()


HexDigest = str


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


def key(path: pl.Path) -> EntryKey:
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
    s = path.stat()

    # NOTE: getmtime is more precise than s.st_mtime
    mtime: float = os.path.getmtime(str(path))

    return Stat(
        s.st_mode,
        s.st_ino,
        s.st_dev,
        s.st_nlink,
        s.st_uid,
        s.st_gid,
        s.st_size,
        s.st_atime,
        mtime,
        s.st_ctime,
    )


class IndexEntry(typ.NamedTuple):

    path  : pl.Path
    stat  : Stat
    digest: HexDigest


MaybeEntry        = typ.Optional[IndexEntry]
EntryByKey        = typ.Dict[EntryKey, MaybeEntry]
EntryKeysByTarget = typ.Dict[Target  , typ.Set[EntryKey]]


def make_entry(path: pl.Path, check: CheckResult) -> MaybeEntry:
    if not path.exists():
        return None

    digest_val = check.digest or file_digest(path)

    return IndexEntry(path=path, stat=mk_stat(path), digest=digest_val)


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
        self.machine_id = machine_id()
        self.entries    = {}
        self.targets    = {}

        try:
            if self.index_file.exists():
                self.load_index()
        except Exception:
            warn_msg = f"Ignoring invalid/corrupted index file " f"'{self.index_file}'"
            log.warning(warn_msg, exc_info=True)

        self.index_file.touch()
        self.index_stat = mk_stat(self.index_file)

    def load_index(self) -> None:
        with self.index_file.open(mode="rb") as fh:
            data = json.loads(fh.read().decode('utf-8'))

        if data['machine_id'] != self.machine_id:
            err_msg = (
                f"Index file '{self.index_file}' possibly "
                "created on different machine. Aborting to"
                "avoid concurrent build from different hosts."
                "If you know this is not an issue, delete "
                "the file and try again."
            )
            raise Exception(err_msg)

        entries: EntryByKey = {}
        for key, entry in data['entries'].items():
            if entry is None:
                entries[key] = entry
            else:
                entries[key] = IndexEntry(
                    pl.Path(entry['path']), Stat(*entry['stat']), entry['digest']
                )

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
        with tmp_file.open(mode="wb") as fh:
            text = json.dumps(data, indent=2)
            fh.write(text.encode("utf-8"))

        if self.has_index_changed():
            tmp_file.unlink()
            err_msg = (
                "WARNING: Concurrent update of index "
                "detected. This may result in a corrupted "
                "build."
            )
            raise Exception(err_msg)
        else:
            tmp_file.rename(self.index_file)

    def has_index_changed(self) -> bool:
        if not self.index_file.exists():
            return True

        if self.index_stat != mk_stat(self.index_file):
            return True

        return False

    def add_files(self, paths: typ.Iterable[pl.Path]) -> None:
        for path in paths:
            self.add_file(path)

    def add_file(self, path: pl.Path) -> None:
        check = self.check_path(path)
        if check.ok:
            return

        entry = make_entry(path, check)
        self.entries[key(path)] = entry

    def check_path(self, path: pl.Path) -> CheckResult:
        # NOTE: There could be different levels of
        #   dirtyness.
        #   strict: hash and mtime must be unchanged
        #   hash: hash must be unchanged
        if key(path) not in self.entries:
            return CheckResult(False, "")

        entry = self.entries[key(path)]
        if entry is None:
            return CheckResult(False, "")

        if not entry.path.exists():
            return CheckResult(False, "")

        if entry.stat != mk_stat(path):
            return CheckResult(False, "")

        # If mtime is very new, then it can't be trusted.
        if entry.stat.mtime <= self.index_stat.mtime - 2:
            return CheckResult(True, entry.digest)

        # fallback to digest check
        new_digest = file_digest(path)
        ok         = new_digest == entry.digest
        return CheckResult(ok, new_digest)

    def is_target_done(self, target: Target, deps: typ.Set[pl.Path]) -> bool:
        for dep in deps:
            digest = self.check_path(dep)
            if not digest.ok:
                return False

        new_deps  = {key(dep) for dep in deps}
        prev_deps = self.targets.get(target)
        return new_deps == prev_deps

    def mark_target_done(self, target: Target, deps: typ.Set[pl.Path]) -> None:
        for dep in deps:
            self.add_file(dep)

        self.targets[target] = {key(dep) for dep in deps}


def _iter_paths(dirpath: pl.Path) -> typ.Iterable[pl.Path]:
    for root, dirnames, filenames in os.walk(dirpath):
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
