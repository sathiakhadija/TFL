import logging
import os
import time

import requests

logger = logging.getLogger(__name__)

TFL_BASE_URL = "https://api.tfl.gov.uk"

TFL_LINES = [
    "bakerloo", "central", "circle", "district",
    "hammersmith-city", "jubilee", "metropolitan",
    "northern", "piccadilly", "victoria",
    "waterloo-city", "elizabeth"
]

TFL_MAJOR_STATIONS = [
    "940GZZLUASL",  # Arsenal
    "940GZZLUBKF",  # Blackfriars
    "940GZZLUBLM",  # Balham
    "940GZZLUBND",  # Bond Street
    "940GZZLUBKG",  # Barking
    "940GZZLUCAL",  # Caledonian Road
    "940GZZLUCAM",  # Camden Town
    "940GZZLUCND",  # Canary Wharf
    "940GZZLUCST",  # Cannon Street
    "940GZZLUCHX",  # Charing Cross
    "940GZZLUEUS",  # Euston Square
    "940GZZLUKSX",  # King's Cross St. Pancras
    "940GZZLULVT",  # Liverpool Street
    "940GZZLULBN",  # London Bridge
    "940GZZLUOXC",  # Oxford Circus
    "940GZZLUPAC",  # Paddington
    "940GZZLUSBC",  # Shepherd's Bush Central
    "940GZZLUSTD",  # Stratford
    "940GZZLUTAW",  # Tottenham Court Road
    "940GZZLUVIC",  # Victoria
    "940GZZLUWTA",  # Waterloo
]


class TfLClient:
    """
    HTTP client for the TfL Unified API.
    Handles authentication, rate limiting, retries, and error handling.
    All methods return parsed JSON as Python dicts or lists.
    """

    def __init__(self, api_key: str = None, app_id: str = None):
        """
        Initialise with API credentials from parameters or environment.
        api_key defaults to TFL_API_KEY env var.
        app_id defaults to TFL_APP_ID env var.
        Raises ValueError if api_key is not found.
        """
        self.api_key = api_key or os.environ.get("TFL_API_KEY")
        self.app_id = app_id or os.environ.get("TFL_APP_ID")

        if not self.api_key:
            raise ValueError(
                "TfL API key is required. Set TFL_API_KEY environment variable "
                "or pass api_key to TfLClient()."
            )

        self.session = requests.Session()

    def _make_request(self, endpoint: str, params: dict = None) -> dict | list:
        """
        Make a GET request to the TfL API.
        Appends app_key to all requests.
        Implements exponential backoff retry: 3 attempts, delays 1s, 2s, 4s.
        Raises requests.HTTPError on 4xx/5xx after retries.
        Logs request URL and response time.
        """
        url = f"{TFL_BASE_URL}{endpoint}"
        request_params = {"app_key": self.api_key}
        if self.app_id:
            request_params["app_id"] = self.app_id
        if params:
            request_params.update(params)

        delays = [1, 2, 4]
        last_exception = None

        for attempt, delay in enumerate(delays, start=1):
            try:
                start_time = time.time()
                logger.info("TfL API request: %s (attempt %d)", url, attempt)
                response = self.session.get(url, params=request_params, timeout=30)
                elapsed = time.time() - start_time
                logger.info(
                    "TfL API response: status=%d time=%.2fs url=%s",
                    response.status_code, elapsed, url
                )
                response.raise_for_status()
                return response.json()
            except requests.HTTPError as exc:
                last_exception = exc
                if response.status_code < 500:
                    # 4xx errors are client errors — retrying will not help
                    raise
                logger.warning(
                    "TfL API server error %d on attempt %d, retrying in %ds",
                    response.status_code, attempt, delay
                )
            except requests.RequestException as exc:
                last_exception = exc
                logger.warning(
                    "TfL API request failed on attempt %d: %s, retrying in %ds",
                    attempt, exc, delay
                )

            if attempt < len(delays):
                time.sleep(delay)

        raise last_exception

    def get_line_status(self, line_ids: list = None) -> list:
        """
        GET /Line/{ids}/Status
        line_ids defaults to TFL_LINES.
        Returns list of line status dicts.
        Each dict contains: id, name, lineStatuses list.
        """
        ids = line_ids or TFL_LINES
        ids_str = ",".join(ids)
        endpoint = f"/Line/{ids_str}/Status"
        result = self._make_request(endpoint)
        return result if isinstance(result, list) else [result]

    def get_line_arrivals(self, line_ids: list = None) -> list:
        """
        GET /Line/{ids}/Arrivals
        line_ids defaults to TFL_LINES.
        Returns list of arrival prediction dicts.
        Each dict contains: lineId, stationName, destinationName,
        timeToStation, expectedArrival.
        """
        ids = line_ids or TFL_LINES
        ids_str = ",".join(ids)
        endpoint = f"/Line/{ids_str}/Arrivals"
        result = self._make_request(endpoint)
        return result if isinstance(result, list) else [result]

    def get_station_disruptions(self, station_ids: list = None) -> list:
        """
        GET /StopPoint/{ids}/Disruption
        station_ids defaults to TFL_MAJOR_STATIONS.
        Batches requests into groups of 5 station IDs.
        Returns list of disruption dicts.
        """
        ids = station_ids or TFL_MAJOR_STATIONS
        batch_size = 5
        all_disruptions = []

        for i in range(0, len(ids), batch_size):
            batch = ids[i:i + batch_size]
            ids_str = ",".join(batch)
            endpoint = f"/StopPoint/{ids_str}/Disruption"
            try:
                result = self._make_request(endpoint)
                batch_disruptions = result if isinstance(result, list) else [result]
                all_disruptions.extend(batch_disruptions)
                logger.info(
                    "Fetched %d disruptions for station batch %d-%d",
                    len(batch_disruptions), i, i + len(batch) - 1
                )
            except requests.HTTPError as exc:
                if exc.response is not None and exc.response.status_code == 404:
                    logger.info("No disruptions found for batch %d-%d", i, i + len(batch) - 1)
                else:
                    raise

        return all_disruptions

    def health_check(self) -> bool:
        """
        Check if TfL API is reachable.
        GET /Line/Mode/tube/Status
        Returns True if response is 200, False otherwise.
        Never raises exceptions.
        """
        try:
            url = f"{TFL_BASE_URL}/Line/Mode/tube/Status"
            params = {"app_key": self.api_key}
            response = self.session.get(url, params=params, timeout=10)
            return response.status_code == 200
        except Exception as exc:
            logger.warning("TfL API health check failed: %s", exc)
            return False
