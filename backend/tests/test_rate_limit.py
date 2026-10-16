import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException


def test_identity_is_hashed_normalized_and_rotated_daily():
    from app.rate_limit import visitor_key

    first = visitor_key("192.0.2.1", "secret", 1)
    assert len(first) == 64
    assert "192.0.2.1" not in first
    assert first == visitor_key("::ffff:192.0.2.1", "secret", 1)
    assert first != visitor_key("192.0.2.1", "secret", 2)
    assert first != visitor_key("192.0.2.1", "different-secret", 1)
    assert visitor_key("2001:db8::1", "secret", 1) == visitor_key("2001:db8::2", "secret", 1)


def test_invalid_identities_share_one_bucket():
    from app.rate_limit import visitor_key

    assert visitor_key("invented", "secret", 1) == visitor_key("another invented value", "secret", 1)


def test_allowed_request_uses_two_atomic_bounded_counters():
    from app.rate_limit import enforce_rate_limit

    connection = MagicMock()
    cursor = connection.__enter__.return_value.cursor.return_value.__enter__.return_value
    cursor.fetchone.side_effect = [(1,), (1,)]
    with (
        patch.dict(os.environ, {"DATABASE_URL": "postgresql://test"}, clear=True),
        patch("app.rate_limit.psycopg.connect", return_value=connection),
    ):
        enforce_rate_limit("192.0.2.1", now=86410)

    upserts = [call for call in cursor.execute.call_args_list if "ON CONFLICT" in call.args[0]]
    assert len(upserts) == 2
    assert [call.args[1][-1] for call in upserts] == [10, 100]
    assert all("WHERE" in call.args[0] and "RETURNING" in call.args[0] for call in upserts)
    assert all("192.0.2.1" not in str(call.args[1]) for call in upserts)


@pytest.mark.parametrize("rows,retry", [([None], 50), ([(1,), None], 86390)])
def test_exceeded_limit_rolls_back_transaction(rows, retry):
    from app.rate_limit import enforce_rate_limit

    connection = MagicMock()
    cursor = connection.__enter__.return_value.cursor.return_value.__enter__.return_value
    cursor.fetchone.side_effect = rows
    with (
        patch.dict(os.environ, {"DATABASE_URL": "postgresql://test"}, clear=True),
        patch("app.rate_limit.psycopg.connect", return_value=connection),
        pytest.raises(HTTPException) as failure,
    ):
        enforce_rate_limit("192.0.2.1", now=86410)

    assert failure.value.status_code == 429
    assert failure.value.headers["Retry-After"] == str(retry)
    assert connection.__exit__.call_args.args[0] is HTTPException


def test_rate_limit_fails_closed_without_database_configuration():
    from app.rate_limit import enforce_rate_limit

    with patch.dict(os.environ, {}, clear=True), pytest.raises(HTTPException) as failure:
        enforce_rate_limit("192.0.2.1")
    assert failure.value.status_code == 503


def test_rate_limit_storage_errors_do_not_leak_credentials(caplog):
    from app.rate_limit import enforce_rate_limit

    with (
        patch.dict(os.environ, {"DATABASE_URL": "postgresql://test"}, clear=True),
        patch("app.rate_limit.psycopg.connect", side_effect=OSError("secret-database-url")),
        pytest.raises(HTTPException) as failure,
    ):
        enforce_rate_limit("192.0.2.1")

    assert failure.value.status_code == 503
    assert "secret-database-url" not in caplog.text
    assert "192.0.2.1" not in caplog.text