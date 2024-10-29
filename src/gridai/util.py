"""Module to stroe utility functions."""

# standard imports
import time


def timeit(f):
    """Timing decorator."""

    def timed(*args, **kw):
        start_time = time.time()
        result = f(*args, **kw)
        end_time = time.time()
        print(f"func:{f.__name__} took: {(end_time - start_time)} sec")
        return result

    return timed
