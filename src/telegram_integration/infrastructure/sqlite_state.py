"""SQLite implementation of the listener state repository.

This adapter persists the listener offset in a small SQLite database stored in
the XDG data directory (``~/.local/share/telegram-send/state.db``). It uses the
standard library :mod:`sqlite3` module so it stays consistent with the
synchronous Telegram client, and it satisfies the
:class:`~telegram_integration.domain.repositories.ListenerStateRepository`
protocol defined in the domain layer.
"""

from __future__ import annotations

import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path

from ..domain.entities import ListenerState
from .xdg_config import get_data_dir

STATE_DB_FILENAME: str = "state.db"
"""Name of the SQLite document stored inside the XDG data directory."""

_STATE_TABLE: str = "state"
_OFFSET_KEY: str = "last_offset"
_UPDATED_AT_KEY: str = "last_update_date"

_CREATE_TABLE_SQL: str = (
    f"CREATE TABLE IF NOT EXISTS {_STATE_TABLE} (key TEXT PRIMARY KEY, value TEXT)"
)
_UPSERT_SQL: str = (
    f"INSERT INTO {_STATE_TABLE} (key, value) VALUES (?, ?) "
    f"ON CONFLICT(key) DO UPDATE SET value = excluded.value"
)
_SELECT_SQL: str = f"SELECT value FROM {_STATE_TABLE} WHERE key = ?"


class SqliteStateError(RuntimeError):
    """Raised when the SQLite state store cannot be opened, read or written."""


class SqliteStateRepository:
    """Persist :class:`ListenerState` in a SQLite database.

    Args:
        db_path: Optional explicit database path. When omitted, the XDG data
            directory is used, i.e.
            ``~/.local/share/telegram-send/state.db``.

    Raises:
        SqliteStateError: If the directory cannot be created, the database
            cannot be opened or the schema cannot be initialised.
    """

    def __init__(self, db_path: Path | str | None = None) -> None:
        self._db_path = (
            Path(db_path) if db_path is not None else get_data_dir() / STATE_DB_FILENAME
        )
        self._lock = threading.RLock()
        self._ensure_directory()
        self._connection = self._connect()
        self._initialize_schema()

    @property
    def db_path(self) -> Path:
        """Return the path of the underlying SQLite database file."""
        return self._db_path

    def close(self) -> None:
        """Close the underlying database connection.

        The method is idempotent, so calling it more than once is safe.

        Raises:
            SqliteStateError: If the connection cannot be closed.
        """
        with self._lock:
            try:
                self._connection.close()
            except sqlite3.Error as exc:  # pragma: no cover - defensive
                raise SqliteStateError(
                    f"Could not close the state database {self._db_path}: {exc}"
                ) from exc

    def __enter__(self) -> SqliteStateRepository:
        """Enter the runtime context and return the repository."""
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Leave the runtime context, closing the connection."""
        self.close()

    def get_offset(self) -> int | None:
        """Return the persisted offset.

        Returns:
            The stored offset, or ``None`` when nothing has been persisted yet.

        Raises:
            SqliteStateError: If the value cannot be read or is not a valid
                integer.
        """
        value = self._fetch(_OFFSET_KEY)
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise SqliteStateError(
                f"Invalid offset stored in the state database: {value!r}"
            ) from exc

    def get_state(self) -> ListenerState | None:
        """Return the full persisted listener state.

        Returns:
            The stored :class:`ListenerState`, or ``None`` when nothing has
            been persisted yet.

        Raises:
            SqliteStateError: If the stored data cannot be read or parsed.
        """
        offset = self.get_offset()
        if offset is None:
            return None
        return ListenerState(
            last_offset=offset,
            last_update_date=self._get_last_update_date(),
        )

    def save_offset(self, offset: int, updated_at: datetime | None = None) -> None:
        """Persist the listener offset.

        Args:
            offset: Offset to consume next (``update_id + 1``). Must be
                greater than or equal to zero.
            updated_at: Timestamp of the update. When omitted, the current UTC
                time is used.

        Raises:
            ValueError: If ``offset`` is negative.
            SqliteStateError: If the value cannot be written.
        """
        if offset < 0:
            raise ValueError("offset must be greater than or equal to 0")

        timestamp = updated_at if updated_at is not None else datetime.now(UTC)
        with self._lock:
            try:
                with self._connection:
                    self._connection.execute(_UPSERT_SQL, (_OFFSET_KEY, str(offset)))
                    self._connection.execute(
                        _UPSERT_SQL, (_UPDATED_AT_KEY, timestamp.isoformat())
                    )
            except sqlite3.Error as exc:
                raise SqliteStateError(
                    f"Could not persist the offset to {self._db_path}: {exc}"
                ) from exc

    def _ensure_directory(self) -> None:
        """Create the parent directory of the database if it is missing."""
        try:
            self._db_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        except OSError as exc:
            raise SqliteStateError(
                f"Could not create the state directory {self._db_path.parent}: {exc}"
            ) from exc

    def _connect(self) -> sqlite3.Connection:
        """Open the SQLite connection.

        Returns:
            An open connection configured with row access by column name.

        Raises:
            SqliteStateError: If the database cannot be opened.
        """
        try:
            connection = sqlite3.connect(self._db_path, check_same_thread=False)
            connection.row_factory = sqlite3.Row
            return connection
        except sqlite3.Error as exc:
            raise SqliteStateError(
                f"Could not open the state database {self._db_path}: {exc}"
            ) from exc

    def _initialize_schema(self) -> None:
        """Create the ``state`` table if it does not exist yet."""
        with self._lock:
            try:
                with self._connection:
                    self._connection.execute(_CREATE_TABLE_SQL)
            except sqlite3.Error as exc:
                raise SqliteStateError(
                    f"Could not initialise the state schema in {self._db_path}: {exc}"
                ) from exc

    def _fetch(self, key: str) -> str | None:
        """Read a single value from the ``state`` table.

        Args:
            key: Primary key of the row to read.

        Returns:
            The stored value, or ``None`` when the key is absent.

        Raises:
            SqliteStateError: If the query fails.
        """
        with self._lock:
            try:
                row = self._connection.execute(_SELECT_SQL, (key,)).fetchone()
            except sqlite3.Error as exc:
                raise SqliteStateError(
                    f"Could not read {key!r} from the state database: {exc}"
                ) from exc
        if row is None:
            return None
        return str(row["value"])

    def _get_last_update_date(self) -> datetime:
        """Return the persisted timestamp, falling back to the Unix epoch.

        Returns:
            The stored UTC timestamp, or ``1970-01-01T00:00:00+00:00`` when the
            database only contains an offset.

        Raises:
            SqliteStateError: If the stored timestamp is not a valid ISO 8601
                string.
        """
        value = self._fetch(_UPDATED_AT_KEY)
        if value is None:
            return datetime.fromtimestamp(0, tz=UTC)
        try:
            return datetime.fromisoformat(value)
        except ValueError as exc:
            raise SqliteStateError(
                f"Invalid timestamp stored in the state database: {value!r}"
            ) from exc
