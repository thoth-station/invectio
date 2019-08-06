from collections import deque
from datetime import datetime


def now():
    q = deque()
    return datetime.utcnow()
