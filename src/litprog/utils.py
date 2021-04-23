# This file is part of the litprog project
# https://github.com/litprog/litprog
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import typing as typ

Function  = typ.TypeVar('Function', bound=typ.Callable[..., typ.Any])
Decorator = typ.Callable[[Function], Function]


def memo(*, nargs: int, keep_signature: bool, maxsize: int = 0) -> Decorator:
    """Memoization for pure functions to enable code that is fast, lazy and functional.

    Currently functions MUST:
     - have 0 or 1 arguments
     - no kwargs
     - no cache clearing
     - max_size=0 (unbound cache size)
     - function signature is not preserved

    Specialized decorators may be implemented based on knowledge
    about the semantics of the memoized function and its users.

    see adm_common.tuple_memoize
    """

    # NOTE (mb 2021-03-09): We might also inspect nargs
    #   from the function signature. Special care must be
    #   taken when dealing with methods though.
    if nargs > 1:
        raise NotImplementedError("memo(nargs>1)")

    if keep_signature:
        raise NotImplementedError("memo(keep_signature=True)")

    if maxsize > 0:
        raise NotImplementedError("memo(maxsize>0)")

    if maxsize == 0 and nargs == 0:

        def decorator_nargs0_unbounded_cache(func: Function) -> Function:
            cache = []  # type: ignore

            def wrapper():
                if len(cache) == 0:
                    ret = func()
                    cache.append(ret)
                return cache[0]

            return wrapper  # type: ignore

        return decorator_nargs0_unbounded_cache
    elif maxsize == 0 and nargs == 1:

        def decorator_nargs1_unbounded_cache(func: Function) -> Function:
            class UnboundedCache(dict):
                def __missing__(self, key):
                    ret = self[key] = func(key)
                    return ret

            cache = UnboundedCache()
            return cache.__getitem__  # type: ignore

        return decorator_nargs1_unbounded_cache
    else:
        errmsg = f"memo(nargs={nargs}, keep_signature={keep_signature}, maxsize={maxsize})"
        raise NotImplementedError(errmsg)
