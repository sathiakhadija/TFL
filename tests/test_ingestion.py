from unittest.mock import MagicMock

import pytest

from ingestion.line_status import ingest_line_status, validate_line_status


@pytest.fixture
def mock_conn():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return conn, cursor


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.get_line_status.return_value = [
        {
            "id": "central",
            "name": "Central",
            "lineStatuses": [
                {
                    "statusSeverity": 10,
                    "statusSeverityDescription": "Good Service",
                    "reason": None,
                    "disruption": None,
                }
            ],
        }
    ]
    return client


def test_validate_line_status_structure(mock_conn):
    conn, cursor = mock_conn
    cursor.fetchone.side_effect = [
        (5,),   # recent row count
        (0,),   # null line_ids count
        (0,),   # out-of-range severity count
    ]
    result = validate_line_status(conn)
    assert isinstance(result, dict)
    assert "valid" in result
    assert "checks" in result
    assert "row_count" in result


def test_ingest_line_status_returns_int(mock_conn, mock_client):
    conn, cursor = mock_conn
    result = ingest_line_status(conn, mock_client)
    assert isinstance(result, int)
    assert result >= 0
