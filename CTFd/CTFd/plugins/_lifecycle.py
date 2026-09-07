"""Process-safe locks for plugin lifecycle transitions (not cache leases).

MySQL/PostgreSQL locks live on a dedicated connection and are released on process
failure. SQLite uses a database-scoped file lock for local multi-worker installs.
Callers own their ORM transaction; this module never commits application data.
"""
import fcntl
import hashlib
import os
import tempfile
import time
from contextlib import contextmanager
from contextvars import ContextVar

from sqlalchemy import text
from CTFd.models import db

_held = ContextVar("plugin_lifecycle_locks", default=())


@contextmanager
def lifecycle_lock(name, timeout=30):
    scope = hashlib.sha256(str(db.engine.url).encode()).hexdigest()[:20]
    key = "ctfd:" + scope + ":" + name
    key = hashlib.sha256(key.encode()).hexdigest()[:60]
    if key in _held.get():
        yield
        return
    dialect = db.engine.dialect.name
    connection = handle = None
    acquired = False
    token = None
    try:
        if dialect in ("mysql", "mariadb", "postgresql"):
            connection = db.engine.connect()
            if dialect in ("mysql", "mariadb"):
                acquired = connection.execute(text("SELECT GET_LOCK(:key, :timeout)"),
                                              key=key, timeout=timeout).scalar() == 1
            else:
                number = int(key[:15], 16)
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    acquired = connection.execute(text("SELECT pg_try_advisory_lock(:key)"), key=number).scalar()
                    if acquired:
                        break
                    time.sleep(0.05)
        elif dialect == "sqlite":
            database = db.engine.url.database
            directory = os.path.dirname(os.path.abspath(database)) if database and database != ":memory:" else tempfile.gettempdir()
            handle = open(os.path.join(directory, ".ctfd-lock-" + key), "a")
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                try:
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                    break
                except BlockingIOError:
                    time.sleep(0.05)
        else:
            raise RuntimeError("Unsupported lifecycle-lock database: " + dialect)
        if not acquired:
            raise TimeoutError("Plugin operation busy; retry shortly")
        token = _held.set(_held.get() + (key,))
        yield
    finally:
        if token is not None:
            _held.reset(token)
        if connection is not None:
            try:
                if acquired:
                    if dialect in ("mysql", "mariadb"):
                        connection.execute(text("SELECT RELEASE_LOCK(:key)"), key=key)
                    else:
                        connection.execute(text("SELECT pg_advisory_unlock(:key)"), key=number)
            finally:
                connection.close()
        if handle is not None:
            handle.close()


def additive_upgrade(plugin, revision, upgrade):
    """Run an idempotent additive revision, including on existing SQLite tables.

    CTFd's stock plugin migration runner skips ALTERs on SQLite. Use Alembic
    Operations directly here; each revision inspects columns before adding them,
    so an interrupted MySQL DDL operation can safely be retried.
    """
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from CTFd.utils import set_config
    with lifecycle_lock("plugin-schema"):
        db.create_all()
        with db.engine.begin() as connection:
            upgrade(Operations(MigrationContext.configure(connection)))
        set_config(plugin + "_alembic_version", revision)
