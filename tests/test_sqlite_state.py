"""Tests for the domain entity and the SQLite state repository."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from telegram_integration.domain import ListenerState, ListenerStateRepository
from telegram_integration.infrastructure import (
    STATE_DB_FILENAME,
    SqliteStateError,
    SqliteStateRepository,
    get_data_dir,
)


class TestListenerState:
    """The entity is a plain, validated dataclass."""

    def test_exposes_its_fields(self) -> None:
        moment = datetime(2026, 1, 1, tzinfo=UTC)

        state = ListenerState(last_offset=10, last_update_date=moment)

        assert state.last_offset == 10
        assert state.last_update_date == moment

    def test_rejects_negative_offset(self) -> None:
        with pytest.raises(ValueError, match="last_offset"):
            ListenerState(
                last_offset=-1,
                last_update_date=datetime.now(UTC),
            )


class TestDefaultLocation:
    """The repository resolves its path through the XDG data directory."""

    def test_uses_xdg_data_dir(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))

        with SqliteStateRepository() as repository:
            expected = get_data_dir() / STATE_DB_FILENAME
            assert repository.db_path == expected
            assert expected.name == "state.db"


class TestRepositoryIsolation:
    """The repository works on its own, creating the XDG directory if needed."""

    def test_creates_missing_directories(self, tmp_path: Path) -> None:
        db_path = tmp_path / "missing" / "nested" / "state.db"

        with SqliteStateRepository(db_path) as repository:
            assert repository.db_path == db_path

        assert db_path.parent.is_dir()
        assert db_path.is_file()

    def test_get_offset_returns_none_when_empty(self, tmp_path: Path) -> None:
        with SqliteStateRepository(tmp_path / "state.db") as repository:
            assert repository.get_offset() is None
            assert repository.get_state() is None

    def test_save_and_get_offset(self, tmp_path: Path) -> None:
        with SqliteStateRepository(tmp_path / "state.db") as repository:
            repository.save_offset(1234)

            assert repository.get_offset() == 1234

    def test_save_overwrites_previous_offset(self, tmp_path: Path) -> None:
        with SqliteStateRepository(tmp_path / "state.db") as repository:
            repository.save_offset(1)
            repository.save_offset(99)

            assert repository.get_offset() == 99

    def test_persists_across_reopen(self, tmp_path: Path) -> None:
        db_path = tmp_path / "state.db"

        with SqliteStateRepository(db_path) as repository:
            repository.save_offset(555)

        with SqliteStateRepository(db_path) as reopened:
            assert reopened.get_offset() == 555

    def test_get_state_returns_entity(self, tmp_path: Path) -> None:
        moment = datetime(2026, 6, 30, 12, 0, tzinfo=UTC)

        with SqliteStateRepository(tmp_path / "state.db") as repository:
            repository.save_offset(7, updated_at=moment)

            state = repository.get_state()

        assert state is not None
        assert state.last_offset == 7
        assert state.last_update_date == moment

    def test_get_state_defaults_timestamp_to_epoch(self, tmp_path: Path) -> None:
        db_path = tmp_path / "state.db"

        with SqliteStateRepository(db_path) as repository:
            repository.save_offset(3)

        # Remove the timestamp to simulate a partial legacy database.
        connection = sqlite3.connect(db_path)
        try:
            with connection:
                connection.execute(
                    "DELETE FROM state WHERE key = ?", ("last_update_date",)
                )
        finally:
            connection.close()

        with SqliteStateRepository(db_path) as repository:
            state = repository.get_state()

        assert state is not None
        assert state.last_update_date == datetime.fromtimestamp(0, tz=UTC)

    def test_saves_a_fresh_timestamp_by_default(self, tmp_path: Path) -> None:
        before = datetime.now(UTC)

        with SqliteStateRepository(tmp_path / "state.db") as repository:
            repository.save_offset(1)
            state = repository.get_state()

        assert state is not None
        assert before - timedelta(seconds=5) <= state.last_update_date
        assert state.last_update_date <= datetime.now(UTC) + timedelta(seconds=5)

    def test_creates_expected_table_schema(self, tmp_path: Path) -> None:
        db_path = tmp_path / "state.db"

        with SqliteStateRepository(db_path):
            pass

        connection = sqlite3.connect(db_path)
        try:
            columns = connection.execute("PRAGMA table_info(state)").fetchall()
        finally:
            connection.close()

        assert [column[1] for column in columns] == ["key", "value"]
        assert [column[2].upper() for column in columns] == ["TEXT", "TEXT"]
        assert any(column[5] for column in columns)  # primary key present

    def test_satisfies_the_domain_protocol(self, tmp_path: Path) -> None:
        with SqliteStateRepository(tmp_path / "state.db") as repository:
            assert isinstance(repository, ListenerStateRepository)
        assert not isinstance(object(), ListenerStateRepository)


class TestErrorHandling:
    """SQLite failures are wrapped in a single, meaningful exception."""

    def test_negative_offset_raises_value_error(self, tmp_path: Path) -> None:
        with (
            SqliteStateRepository(tmp_path / "state.db") as repository,
            pytest.raises(ValueError, match="offset"),
        ):
            repository.save_offset(-5)

    def test_operations_after_close_raise_sqlite_state_error(
        self, tmp_path: Path
    ) -> None:
        repository = SqliteStateRepository(tmp_path / "state.db")
        repository.close()
        # `close` is idempotent.
        repository.close()

        with pytest.raises(SqliteStateError):
            repository.get_offset()

        with pytest.raises(SqliteStateError):
            repository.save_offset(1)

    def test_corrupt_offset_raises_sqlite_state_error(self, tmp_path: Path) -> None:
        db_path = tmp_path / "state.db"

        with SqliteStateRepository(db_path):
            pass

        connection = sqlite3.connect(db_path)
        try:
            with connection:
                connection.execute(
                    "INSERT INTO state (key, value) VALUES (?, ?)",
                    ("last_offset", "not-an-integer"),
                )
        finally:
            connection.close()

        with (
            SqliteStateRepository(db_path) as repository,
            pytest.raises(SqliteStateError, match="Invalid offset"),
        ):
            repository.get_offset()
