import sys
import gc
import signal
import collections
from tensorflow.python.keras.layers import LSTM

GLOBAL_VAL = 100
X, Y = 100, 100
A, *B = 10, 10, 10
gc["foo"] = 1008

b: int = 10


class SomeClass(object):
    class NestedClass:
        pass

    def method(self):
        pass


async def async_signal_handler(signum):
    pass


def signal_handler(signum, frame):
    def nested_func():
        foo = 1
        return foo

    foo = collections.deque()
    LSTM()
    foo.append("baz")


signal.signal(signal.SIGKILL, handler=signal_handler)
gc.collect()
sys.exit(1)
