from collections import deque
from datetime import datetime


def now():
    q = deque()  # noqa: F841
    return datetime.utcnow()
