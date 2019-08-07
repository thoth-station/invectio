import sys
import gc
import signal
import collections
from tensorflow.python.keras.layers import LSTM


def signal_handler(signum, frame):
    foo = collections.deque()
    LSTM()
    foo.append("baz")


signal.signal(signal.SIGKILL, handler=signal_handler)
gc.collect()
sys.exit(1)
