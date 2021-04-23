# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import os
import re
import uuid
import shlex
import shelve
import typing as typ
import hashlib
import logging
import pathlib as pl
import datetime as dt

from . import parse
from . import common
from . import config
from . import session

# import zlib
# import zstandard


logger = logging.getLogger(__name__)


MarkdownFiles = typ.Iterable[parse.MarkdownFile]

SERIAL_VERSION_ID = 1

CaptureData = bytes


class ManifestEntry(typ.NamedTuple):
    created       : str
    runtime_ms    : int
    capture_size  : int
    capture_digest: str
    task_key      : str
    md_path       : str
    task_info     : str


def init_manifest_entry(
    task: common.BlockTask, task_key: str, capture: session.Capture
) -> typ.Tuple[ManifestEntry, CaptureData]:
    created     = dt.datetime.utcnow().isoformat()
    md_filename = str(task.md_path)
    runtime_ms  = round(capture.runtime * 1000)

    capture_data   = session.dumps_capture(capture)
    capture_size   = len(capture_data)
    capture_digest = hashlib.sha1(capture_data).hexdigest()

    blk       = task.block
    task_info = f"@{blk.first_line:>6}"
    if blk.info_string:
        task_info += " - " + blk.info_string.ljust(9)

    content_lines = blk.inner_content.strip().splitlines()
    if content_lines:
        firstline = content_lines[0]
        task_info += " - " + firstline

    entry = ManifestEntry(
        created,
        runtime_ms,
        capture_size,
        capture_digest,
        task_key,
        md_filename,
        task_info,
    )
    return entry, capture_data


def _manifest_lines(manifest_entries: typ.List[ManifestEntry]) -> typ.Iterable[str]:
    manifest_entries.sort()

    colwidths = [0] * len(ManifestEntry._fields)
    for entry in manifest_entries:
        for i, colwidth in enumerate(colwidths):
            colwidths[i] = max(colwidth, len(str(entry[i])))

    for entry in manifest_entries:
        line = "".join(
            f"{val:<{colwidths[i]}}  " if isinstance(val, str) else f"{val:>{colwidths[i]}}  "
            for i, val in enumerate(entry)
        )
        yield line.rstrip()


def dumps_manifest(manifest_entries: typ.List[ManifestEntry]) -> str:
    if manifest_entries:
        return "\n".join(_manifest_lines(manifest_entries))
    else:
        return ""


def parse_manifest(manifest_text: str) -> typ.Iterable[ManifestEntry]:
    max_split = len(ManifestEntry._fields) - 1
    assert max_split == 6
    for manifest_entry in manifest_text.splitlines():
        (
            created,
            runtime_ms,
            capture_size,
            capture_digest,
            task_key,
            md_path,
            task_info,
        ) = re.split(r"\s+", manifest_entry, max_split)

        yield ManifestEntry(
            created,
            int(runtime_ms),
            int(capture_size),
            capture_digest,
            task_key,
            md_path,
            task_info,
        )


class ResultCache:

    task_keys_by_provide_id: typ.Dict[str, str]

    # used for invalidation (whoever provides must invalidate all requires)
    requires_by_provide_id: typ.Dict[str, typ.List[str]]
    manifest              : typ.List[ManifestEntry]

    def __init__(self, manifest_text: str) -> None:
        self.task_keys_by_provide_id = {}
        self.requires_by_provide_id  = {}

        self.manifest = list(parse_manifest(manifest_text))

        for entry in self.manifest:
            self.task_keys_by_provide_id[entry.task_key] = entry.task_key

    def task_key(self, task: common.BlockTask) -> str:
        requires_digest = hashlib.sha1()

        requires_digest.update(task.block.namespace.encode("utf-8"))
        if task.opts.directive == 'run':
            requires_digest.update(task.command.encode("utf-8"))
            for maybe_path in shlex.split(task.command):
                if os.path.exists(maybe_path):
                    mtime = os.stat(maybe_path).st_mtime
                    requires_digest.update(str(mtime).encode("utf-8"))
        else:
            requires_digest.update(task.block.content.encode("utf-8"))

        for require_id in sorted(task.opts.requires_ids):
            requires_digest.update(require_id.encode("utf-8"))
            # For any require, there MUST have previously have been a
            #   call of ResultCache._reset_task_keys for the
            #   corresponding block with the def/provide. This means
            #   that task_keys_by_provide_id must be populated.
            task_key = self.task_keys_by_provide_id[require_id]
            requires_digest.update(task_key.encode("utf-8"))

        return requires_digest.hexdigest()

    def invalidate_requires(self, provides_id: str) -> None:
        self.task_keys_by_provide_id.pop(provides_id, None)

        for requires_id in self.requires_by_provide_id.get(provides_id, []):
            self.invalidate_requires(requires_id)

    def _reset_task_keys(
        self,
        task : common.BlockTask,
        entry: ManifestEntry,
    ) -> None:
        provides_id = task.opts.provides_id
        if provides_id is None:
            return

        prev_capture_digest = self.task_keys_by_provide_id.get(provides_id)
        if entry.capture_digest != prev_capture_digest:
            self.invalidate_requires(provides_id)
            self.task_keys_by_provide_id[provides_id] = entry.task_key

    def update(self, task: common.BlockTask, capture: session.Capture) -> None:
        task_key = self.task_key(task)
        entry, capture_data = init_manifest_entry(task, task_key, capture)
        self.write_capture(entry, capture_data)
        self._reset_task_keys(task, entry)

    def write_capture(self, entry: ManifestEntry, capture_data: CaptureData) -> None:
        raise NotImplementedError("MUST be implemented by subclass.")

    def read_capture(self, entry: ManifestEntry) -> typ.Optional[CaptureData]:
        raise NotImplementedError("MUST be implemented by subclass.")

    def get_entry(self, task: common.BlockTask) -> typ.Optional[ManifestEntry]:
        task_key = self.task_key(task)
        for entry in reversed(self.manifest):
            if entry.task_key == task_key:
                return entry

        return None

    def get_capture(self, task: common.BlockTask) -> typ.Optional[session.Capture]:
        entry = self.get_entry(task)
        if entry is None:
            return None

        capture_data = self.read_capture(entry)
        if capture_data is None:
            return None

        self._reset_task_keys(task, entry)
        return session.loads_capture(capture_data)

    def flush(self) -> None:
        raise NotImplementedError("MUST be implemented by subclass.")


class DummyCache(ResultCache):
    def __init__(self) -> None:
        super().__init__(manifest_text="")

    def read_capture(self, entry: ManifestEntry) -> typ.Optional[CaptureData]:
        pass

    def write_capture(self, entry: ManifestEntry, capture_data: CaptureData) -> None:
        pass

    def flush(self) -> None:
        pass


# TODO (mb 2021-03-05):

# dctx = zstandard.ZstdDecompressor()
# capture_bytes = dctx.decompress(capture_zstd)

# cctx = zstandard.ZstdCompressor()
# capture_zstd = cctx.compress(capture_bytes)


def _compress(data: bytes) -> bytes:
    return data


def _decompress(data: bytes) -> bytes:
    return data


def parse_cache_id(md_files: MarkdownFiles) -> str:
    """Parse identifier that is unique to the project of the md_files.

    Special consideration is be given to
    derived the cache_id in a machine independent way.

    This leaves open the option of using redis to reuse
    cache results built on other machines.
    """

    prefix          = "unknown_project"
    project_id_data = b"unknown_project"

    for md_file in md_files:
        meta = md_file.parse_front_matter_meta()
        if 'repo_url' in meta:
            url             = meta['repo_url']
            prefix          = url.replace("/", "_").replace(":", "_")
            project_id_data = url.encode("utf-8")
        elif prefix == "unknown_project" and 'title' in meta:
            prefix          = meta['title'].lower().replace(" ", "_")
            project_id_data = meta['title'].encode("utf-8")

    project_id_hash = hashlib.sha1(project_id_data).hexdigest()
    return prefix + "_" + project_id_hash


class LocalResultCache(ResultCache):

    _manifest_file: pl.Path
    _data_file    : pl.Path
    _entry_buffer : typ.List[ManifestEntry]

    def __init__(
        self,
        orig_files: MarkdownFiles,
    ) -> None:
        cache_subdir = parse_cache_id(orig_files)
        cache_dir    = config.CACHE_DIR / cache_subdir

        if not cache_dir.exists():
            cache_dir.mkdir()

        self._manifest_file = cache_dir / f"build_cache.manifest_v{SERIAL_VERSION_ID}"
        self._data_file     = cache_dir / "build_cache.db"

        self._db = shelve.open(str(self._data_file))

        if self._manifest_file.exists():
            with self._manifest_file.open() as fobj:
                manifest_text = fobj.read()
        else:
            manifest_text = ""

        super().__init__(manifest_text)

    def write_capture(self, entry: ManifestEntry, capture_data: CaptureData) -> None:
        self.manifest.append(entry)
        self._db[entry.capture_digest] = _compress(capture_data)

    def read_capture(self, entry: ManifestEntry) -> typ.Optional[CaptureData]:
        raw_capture_data = self._db.get(entry.capture_digest)
        if raw_capture_data:
            return _decompress(raw_capture_data)
        else:
            return None

    def flush(self) -> None:
        self.manifest.sort()
        manifest_text = dumps_manifest(self.manifest)

        # verify round trip
        manifest = list(parse_manifest(manifest_text))
        assert manifest == self.manifest

        tmp_file = str(self._manifest_file) + ".tmp_" + uuid.uuid4().hex
        with open(tmp_file, mode="w") as fobj:
            fobj.write(manifest_text)

        os.rename(tmp_file, self._manifest_file)

        self._db.close()


# class RedisResultCache(ResultCache):
#     pass
