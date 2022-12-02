import inspect
from functools import wraps
from pprint import pprint
import logging

logging.getLogger().setLevel(logging.DEBUG)

class Cache:

    def __init__(self, use_hash=False, primitives=(int, float, bool, str, NoneType)):
        self.user_hash = use_hash
        self.primitives = primitives
        self._cache = {}

    def invalidate(self, fn, *args, **kwargs):
        del self._cache[fn][self.freeze((args, kwargs))]

    def freeze(self, it):
        if it in self.primitives:
            return it
        elif isinstance(it,(list, tuple)):
            return tuple(self.freeze(i) for i in it)
        elif isinstance(it, dict):
            return tuple((i[0], self.freeze(i[1])) for i in sorted(it.items(), key=lambda x: x[0]))
        elif self.use_hash:
            hash(it)
            return it

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
                else:      
                    logging.debug(f"Using cache for {(_fn, hashable)}.")
                    return self._cache[_fn][hashable]

            except Exception as e:
                logging.debug(e)
                return fn(*args, **kwargs)
                
        return wrapper
