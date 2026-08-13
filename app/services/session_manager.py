"""In-memory session storage with TTL and per-session locking.

The MVP stores active sessions in one backend process. Persistence can be added
later without changing the HTTP contract.
"""
