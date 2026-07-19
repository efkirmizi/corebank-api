"""Database access: connection pooling and the unit-of-work boundary.

This package is the only place that opens connections. Repositories receive a
connection; they never reach into the pool themselves.
"""

from .pool import get_connection, init_pool, ping, reset_pool
from .uow import read_only, unit_of_work

__all__ = ["get_connection", "init_pool", "ping", "reset_pool", "read_only", "unit_of_work"]
