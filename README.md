# Memoiz

Memoiz is a memoization decorator that makes resonable assumptions about how and if to cache the return value of a function or method based on the arguments passed to it.  The decorator can be used on both free and bound functions.

## Usage

```py
from memoiz.cache import Cache

cache = Cache()

class Example:

    def __init__(self):
        self.n = 1

    @cache
    def test(self, a, b):
        return (self.n, a, b)

example = Example()

example.test(1, 2)

cache.invalidate(example.test, example, 1, 2)

@cache
def test(a):
    return a

test(1)

cache.invalidate(test, 1)

```
## Install
```bash
pip install memoiz
```