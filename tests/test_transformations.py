def _health_score(avg_severity: float) -> float:
    """Mirror of the mart_line_performance health_score formula."""
    raw = 100.0 - (avg_severity * 5.0)
    return max(0.0, min(100.0, raw))


def _disruption_rate(disrupted_readings: int, total_readings: int) -> float:
    """Mirror of the disruption_rate_pct formula."""
    if total_readings == 0:
        return 0.0
    return round(100.0 * disrupted_readings / total_readings, 1)


def test_health_score_good_service():
    assert _health_score(0) == 100.0


def test_health_score_suspended():
    assert _health_score(20) == 0.0


def test_health_score_good_service_typical():
    score = _health_score(6)
    assert score == 70.0


def test_health_score_minor_delays():
    score = _health_score(9)
    assert score == 55.0


def test_health_score_clamped_at_zero():
    score = _health_score(25)
    assert score == 0.0


def test_health_score_clamped_at_hundred():
    score = _health_score(-5)
    assert score == 100.0


def test_disruption_rate_ten_percent():
    rate = _disruption_rate(10, 100)
    assert rate == 10.0


def test_disruption_rate_zero_disruptions():
    rate = _disruption_rate(0, 100)
    assert rate == 0.0


def test_disruption_rate_all_disrupted():
    rate = _disruption_rate(50, 50)
    assert rate == 100.0


def test_disruption_rate_zero_total():
    rate = _disruption_rate(0, 0)
    assert rate == 0.0
