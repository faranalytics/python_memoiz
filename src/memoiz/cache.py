import inspect
from functools import wraps
import logging
from typing import Tuple

class CacheException(Exception):
     def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class Cache:

    def __init__(self, immutables: Tuple[type, ...] = (int, float, complex, bool, str, type(None)), allow_hash: bool = True):
        self.allow_hash = allow_hash
        self.immutables = immutables
        self._cache = {}

    def invalidate(self, fn, *args, **kwargs):
        del self._cache[fn][self.freeze((args, kwargs))]

    def freeze(self, it):
        if type(it) in self.immutables:
            return it
        elif isinstance(it, (list, tuple)):
            return tuple(self.freeze(i) for i in it)
        elif isinstance(it, dict):
            return tuple((i[0], self.freeze(i[1])) for i in sorted(it.items(), key=lambda x: x[0]))
        elif self.allow_hash:
            try:
                hash(it)
            except Exception as e:
                raise CacheException(f"Cannot freeze {it}.")
            return it
        else:
            raise CacheException(f"Cannot freeze {it}.")

    def __call__(self, fn):

        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                if hasattr(args[0], fn.__name__) and inspect.unwrap(getattr(args[0], fn.__name__)) is fn:
                    _fn = getattr(args[0], fn.__name__)
                else:
                    _fn = wrapper

                hashable = self.freeze((args, kwargs))

                if _fn not in self._cache:
                    self._cache[_fn] = {}

                if hashable not in self._cache[_fn]:
                    self._cache[_fn][hashable] = fn(*args, **kwargs)
                    logging.debug(f"Cached {(_fn, hashable)}.")

                logging.debug(f"Using cache for {(_fn, hashable)}.")
                return self._cache[_fn][hashable]

            except CacheException as e:
                logging.debug(e)
                return fn(*args, **kwargs)

        return wrapper
