import inspect
import threading
import copy
from functools import wraps
import logging
from typing import Tuple

class CacheException(Exception):
     def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class Cache:

    def __init__(self, immutables: Tuple[type, ...] = (int, float, complex, bool, str, type(None)), allow_hash: bool = True, deep_copy: bool = True):
        self.allow_hash = allow_hash
        self.deep_copy = deep_copy
        self.immutables = immutables
        self._cache = {}
        self._lock = threading.Lock()
        
    def invalidate(self, fn, *args, **kwargs):
        with self._lock:
            del self._cache[fn][self.freeze((args, kwargs))]

    def invalidate_all(self):
        with self._lock:
            self._cache = {}

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
                    # If the first argument is an object and it contains the method `fn` then use the unwrapped method (i.e., the bound function) for the key.
                    # This is necessary because the bound function is the reference that may be used for invalidation.
                    key = getattr(args[0], fn.__name__)            
                else:
                    # If this is not a method call, then use the wrapper for the key.  This is necessary, as referencing the function will return the wrapper.
                    key = wrapper

                hashable = self.freeze((args, kwargs))

                if key in self._cache and hashable in self._cache[key]:
                    logging.debug(f"Using cache for {(key, hashable)}.")
                    self._lock.acquire()
                    result = self._cache[key][hashable]
                    self._lock.release()
                else:
                    result = fn(*args, **kwargs)
                    self._lock.acquire()
                    if key not in self._cache:
                        self._cache[key] = {}
                    if hashable not in self._cache[key]:
                        self._cache[key][hashable] = result
                        logging.debug(f"Cached {(key, hashable)}.")
                    self._lock.release()

                if self.deep_copy:
                    return copy.deepcopy(result)
                else:
                    return result

            except CacheException as e:
                logging.debug(e)
                return fn(*args, **kwargs)
            except BaseException as e:
                if self._lock.locked():
                    self._lock.release()
                raise e

        return wrapper
