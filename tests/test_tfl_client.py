import pytest
import responses as responses_lib

from ingestion.tfl_client import TFL_BASE_URL, TfLClient


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    monkeypatch.setenv("TFL_API_KEY", "test-api-key")
    monkeypatch.setenv("TFL_APP_ID", "test-app-id")


@responses_lib.activate
def test_health_check_success():
    responses_lib.add(
        responses_lib.GET,
        f"{TFL_BASE_URL}/Line/Mode/tube/Status",
        json=[{"id": "central", "name": "Central"}],
        status=200,
    )
    client = TfLClient()
    assert client.health_check() is True


@responses_lib.activate
def test_health_check_failure():
    responses_lib.add(
        responses_lib.GET,
        f"{TFL_BASE_URL}/Line/Mode/tube/Status",
        json={"message": "Service Unavailable"},
        status=500,
    )
    client = TfLClient()
    assert client.health_check() is False


@responses_lib.activate
def test_get_line_status_returns_list():
    mock_response = [
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
        },
        {
            "id": "jubilee",
            "name": "Jubilee",
            "lineStatuses": [
                {
                    "statusSeverity": 9,
                    "statusSeverityDescription": "Minor Delays",
                    "reason": "Engineering works",
                    "disruption": {
                        "category": "PlannedWork",
                        "description": "Minor delays due to engineering works",
                    },
                }
            ],
        },
    ]
    responses_lib.add(
        responses_lib.GET,
        f"{TFL_BASE_URL}/Line/central,jubilee/Status",
        json=mock_response,
        status=200,
    )
    client = TfLClient()
    result = client.get_line_status(line_ids=["central", "jubilee"])
    assert isinstance(result, list)
    assert len(result) >= 1
    assert result[0]["id"] == "central"


def test_client_raises_on_missing_api_key(monkeypatch):
    monkeypatch.delenv("TFL_API_KEY", raising=False)
    monkeypatch.delenv("TFL_APP_ID", raising=False)
    with pytest.raises(ValueError, match="TfL API key is required"):
        TfLClient(api_key=None, app_id=None)
