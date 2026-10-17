"""Domain/history contracts run without any optional tracking packages."""

import subprocess
import sys
from dataclasses import FrozenInstanceError, replace

import pytest

from collision_warning.domain import Detection, FrameInfo
from collision_warning.tracking import ObservationHistory, TrackingConfig


def observation(index, timestamp, *, source="road", category=2):
    return Detection(
        FrameInfo(source, index, timestamp, 100, 80),
        category,
        "car",
        0.8,
        (10, 10, 40, 50),
    )


def test_domain_and_tracking_import_without_optional_packages():
    code = """
import sys
from collision_warning.domain import Track, TrackingResult
from collision_warning.tracking import ObservationHistory, Tracker, TrackingConfig
ObservationHistory(TrackingConfig())
optional = {'numpy', 'supervision', 'trackers', 'cv2', 'av', 'torch', 'ultralytics'}
assert not optional & sys.modules.keys()
"""
    subprocess.run([sys.executable, "-I", "-c", code], check=True, timeout=10)


def test_history_obeys_count_and_time_limits_and_old_snapshots_are_immutable():
    history = ObservationHistory(
        TrackingConfig(history_max_observations=3, history_max_seconds=10)
    )
    items = [observation(i, float(i)) for i in range(5)]
    for item in items[:3]:
        history.append(item)
    before = history.observations
    for item in items[3:]:
        history.append(item)
    assert before == tuple(items[:3])
    assert history.observations == tuple(items[2:])
    assert history.observations[-1] is items[-1]
    timed = ObservationHistory(
        TrackingConfig(
            history_max_observations=10,
            history_max_seconds=2,
        )
    )
    for item in items:
        timed.append(item)
    assert timed.observations == tuple(items[2:])
    timed.prune(5.5)
    assert timed.observations == (items[4],)
    timed.prune(7)
    assert timed.observations == ()
    with pytest.raises(FrozenInstanceError):
        before[0].score = 0.1


@pytest.mark.parametrize(
    "change",
    [
        {"source": "another"},
        {"category": 7},
        {"index": 0},
        {"timestamp": 0},
    ],
)
def test_history_rejects_incompatible_measurements_without_changes(change):
    history = ObservationHistory(TrackingConfig())
    first = observation(0, 0)
    history.append(first)
    options = {"index": 1, "timestamp": 1}
    options.update(change)
    with pytest.raises(ValueError):
        history.append(observation(**options))
    assert history.observations == (first,)


def test_pruning_cannot_move_backwards_or_let_expired_history_accept_old_data():
    history = ObservationHistory(TrackingConfig(history_max_seconds=0.5))
    history.append(observation(0, 1))
    history.prune(2)
    assert history.observations == ()
    for timestamp in (1, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            history.prune(timestamp)
    with pytest.raises(ValueError):
        history.append(observation(1, 1.5))
    with pytest.raises(ValueError):
        history.append(observation(1, 2, source="another"))
    history.clear()
    new = observation(0, 0, source="another")
    history.append(new)
    assert history.observations == (new,)


@pytest.mark.parametrize(
    "options",
    [
        {"frame_rate": 0},
        {"max_gap_seconds": 0},
        {"history_max_observations": 0},
        {"history_max_observations": 1.5},
        {"history_max_observations": True},
        {"history_max_seconds": 0},
        {"history_max_seconds": float("nan")},
        {"max_gap_seconds": float("inf")},
    ],
)
def test_invalid_history_and_clock_configuration(options):
    with pytest.raises(ValueError):
        TrackingConfig(**options)


def test_lost_buffer_records_effective_source_time_not_source_frame_count():
    config = TrackingConfig(lost_seconds=1.02)
    assert config.lost_track_buffer == 31
    assert config.effective_lost_seconds == 31 / 30
    assert (
        replace(config, frame_rate=60).effective_lost_seconds
        == config.effective_lost_seconds
    )


def test_history_does_not_retain_a_mutable_coordinate_container():
    history = ObservationHistory(TrackingConfig())
    with pytest.raises(ValueError, match="immutable"):
        history.append(replace(observation(0, 0), xyxy=[10, 10, 40, 50]))
    assert history.observations == ()
