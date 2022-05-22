# -*- coding: utf-8 -*-
# type: ignore
"""Store simple data between multiple executions of a script.

A simple class to store small amounts data between
multiple executions of a script (for one-off scripts).

Copyright: Manuel Barkhau 2020 Dedicated to the public domain.
CC0: https://creativecommons.org/publicdomain/zero/1.0/

Usage:

with SimpleCache(name="mycache") as cache:
    cache['hello'] = "wörld"

# later (in another process)
with SimpleCache(name="mycache", mode="r") as cache:
    assert cache['hello'] == "wörld"
"""
import os
import time
import pickle
import shutil
import hashlib
import inspect
import logging
import tempfile
import functools
from pathlib import Path

logger = logging.getLogger("litprog.simple_cache")

# TODO (mb 2021-07-25):
#   redis backing
#   compression


def _digest(parts) -> str:
    dig = hashlib.sha1()
    for part in parts:
        dig.update(str(part).encode('utf-8'))
    return dig.hexdigest()


class SimpleCache:
    def __init__(
        self,
        *,
        name="default",
        mode="w",
        dumps=pickle.dumps,
        loads=pickle.loads,
        cache_id=None,
    ) -> None:
        if mode not in ("r", "w"):
            msg = f"Invalid value mode='{mode}'. Valid modes are: 'r' and 'w'"
            raise ValueError(msg)

        self._mode  = mode
        self._dumps = dumps
        self._loads = loads

        if cache_id is None:
            frame = inspect.stack()[1]
            parts = []

            for path in Path(frame.filename).glob("*.py"):
                parts.append(path)
                parts.append(path.stat().st_mtime)

            parts.append(frame.lineno)
            cache_id = _digest(parts)

        tmp       = tempfile.gettempdir()
        fname     = cache_id + "_" + name
        self.path = os.path.join(tmp, "_simple_file_cache_" + fname)

        self._in_data  = None
        self._obj      = None
        self._modified = False

    def _load_obj(self) -> None:
        if os.path.exists(self.path):
            with open(self.path, mode="rb") as fobj:
                self._in_data = fobj.read()

            try:
                self._obj = self._loads(self._in_data)
            except UnicodeError:
                self._obj = self._loads(self._in_data.decode("utf-8"))
            except Exception as ex:
                logger.warning(f"invalid cache data (maybe code changed), error: {ex}")

                self._in_data = None
                self._obj     = {}
        else:
            self._obj = {}

    def decorate(self, make_key: callable = None) -> callable:
        def decorator(func: callable) -> callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if make_key is None:
                    key = str(args + tuple(kwargs.items()))
                else:
                    key = make_key(*args, **kwargs)

                if key in self:
                    return self[key]
                else:
                    result = func(*args, **kwargs)
                    self[key] = result
                    return result

            return wrapper

        return decorator

    def __contains__(self, key: str) -> bool:
        if self._obj is None:
            self._load_obj()

        key_data  = key.encode("utf-8")
        cache_key = hashlib.sha1(key_data).hexdigest()
        return cache_key in self._obj

    def __getitem__(self, key: str):
        if self._obj is None:
            self._load_obj()

        cache_key = hashlib.sha1(key.encode("utf-8")).hexdigest()
        return self._obj[cache_key]

    def __setitem__(self, key: str, val: any):
        if self._obj is None:
            self._load_obj()

        self._modified = True

        cache_key = hashlib.sha1(key.encode("utf-8")).hexdigest()
        self._obj[cache_key] = val

    def __enter__(self):
        return self

    def __exit__(self, typ, val, tb):
        if typ or val or tb:
            return

        is_modified = self._obj and self._modified and "w" in self._mode
        if not is_modified:
            return

        output = self._dumps(self._obj)
        if isinstance(output, str):
            out_data = output.encode("utf-8")
        else:
            out_data = output

        assert isinstance(out_data, bytes)

        if self._in_data == out_data:
            return

        nonce    = str(time.time())
        tmp_file = self.path + nonce
        try:
            with open(tmp_file, mode="wb") as fobj:
                fobj.write(out_data)

            shutil.move(tmp_file, self.path)
        finally:
            if os.path.exists(tmp_file):
                os.unlink(tmp_file)


def main():
    with SimpleCache() as cache:
        assert isinstance(cache     , SimpleCache)
        assert isinstance(cache._obj, dict)
        cache._obj['hello'] = "wörld"

    print("cache_path:", cache.path)
    with open(cache.path, mode='r', encoding='utf-8') as fobj:
        print(fobj.read())

    # later
    with SimpleCache(mode="r") as cache:
        assert isinstance(cache._obj, dict)
        assert cache._obj['hello'] == "wörld"


if __name__ == '__main__':
    main()
