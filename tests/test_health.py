from pathlib import Path

from worldcup_tracker.health import load_health, record_failure, record_success


def test_health_alert_fires_on_fifth_failure(tmp_path: Path) -> None:
    for i in range(4):
        _, alert = record_failure(tmp_path, "Test", f"error {i}", alert_after=5)
        assert alert is None

    state, alert = record_failure(tmp_path, "Test", "error 5", alert_after=5)
    assert state.consecutive_failures == 5
    assert alert is not None
    assert alert.consecutive_failures == 5

    _, alert_again = record_failure(tmp_path, "Test", "error 6", alert_after=5)
    assert alert_again is None


def test_health_recovery_clears_state(tmp_path: Path) -> None:
    for _ in range(5):
        record_failure(tmp_path, "Test", "broken", alert_after=5)
    assert load_health(tmp_path, "Test").health_alert_sent

    recovered = record_success(tmp_path, "Test")
    assert recovered is True
    assert load_health(tmp_path, "Test").consecutive_failures == 0


def test_health_repeat_every(tmp_path: Path) -> None:
    for i in range(9):
        record_failure(tmp_path, "Test", f"e{i}", alert_after=5, repeat_every=5)
    _, alert_at_10 = record_failure(tmp_path, "Test", "e10", alert_after=5, repeat_every=5)
    assert alert_at_10 is not None
    assert alert_at_10.consecutive_failures == 10
