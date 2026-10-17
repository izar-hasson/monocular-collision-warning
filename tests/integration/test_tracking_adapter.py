"""Exercise domain lifecycle and history contracts against real CPU ByteTrack."""

from dataclasses import replace

import pytest

from collision_warning.domain import Detection, FrameInfo
from collision_warning.tracking import ByteTrackAdapter, TrackingConfig

pytestmark = [pytest.mark.integration, pytest.mark.tracking]


def frame(index, timestamp=None, **options):
    return FrameInfo(
        options.get("source", "road"),
        index,
        5 + index / 10 if timestamp is None else timestamp,
        options.get("width", 320),
        100,
    )


def detected(info, *, x=10, score=0.9, category=2):
    return Detection(
        info, category, "car" if category == 2 else "truck", score, (x, 10, x + 40, 50)
    )


def observe(adapter, info, **options):
    return adapter.update(info, [detected(info, **options)])


def confirmed(adapter):
    first = observe(adapter, frame(0))
    assert first.observations[0].identity is None
    assert first.tracks == ()
    second = observe(adapter, frame(1))
    assert second.observations[0].identity is not None
    return second


def test_reordering_preserves_original_measurements_and_separate_histories():
    adapter = ByteTrackAdapter()
    for i in (0, 1):
        info = frame(i)
        result = adapter.update(info, [detected(info), detected(info, x=150)])
    identities = [o.identity for o in result.observations]
    assert len(set(identities)) == 2
    info = frame(2)
    originals = [
        detected(info, score=0.18),
        detected(info, x=150),
        detected(info, x=90, score=0.05),
    ]
    result = adapter.update(info, originals)
    assert [o.identity for o in result.observations[:2]] == identities
    assert result.observations[2].status == "below_floor"
    for index, association in enumerate(result.observations):
        assert association.observation_index == index
        assert association.detection is originals[index]
    for track, original in zip(result.tracks, originals[:2], strict=True):
        assert track.history[-1] is original
        assert len(track.history) == 2
        assert track.observations_seen == track.consecutive_observations == 2
        assert track.state == "observed"


def test_empty_and_unassigned_updates_are_gaps_and_reacquisition_starts_a_new_segment():
    adapter = ByteTrackAdapter()
    initial = confirmed(adapter)
    identity = initial.tracks[0].identity
    low = observe(adapter, frame(2), score=0.1)
    assert low.tracks[0].identity == identity
    before_gap = low.tracks[0]
    assert len(before_gap.history) == 2
    missing = adapter.update(frame(3), [])
    assert missing.observations == ()
    lost = missing.tracks[0]
    assert lost.state == "lost"
    assert lost.history == before_gap.history
    assert lost.consecutive_observations == 0
    assert lost.time_since_observed_s == pytest.approx(0.1)
    recovered = observe(adapter, frame(4))
    track = recovered.tracks[0]
    assert track.identity == identity
    assert track.segment_id == recovered.observations[0].segment_id == 1
    assert [d.frame.index for d in track.history] == [4]
    assert track.consecutive_observations == 1
    assert track.observations_seen == 3
    assert track.age_s == pytest.approx(0.3)
    assert len(before_gap.history) == 2  # Previous snapshot did not change.
    assert observe(adapter, frame(5)).tracks[0].consecutive_observations == 2


def test_far_unassigned_detection_does_not_enter_the_lost_tracks_history():
    adapter = ByteTrackAdapter()
    previous = confirmed(adapter).tracks[0]
    result = observe(adapter, frame(2), x=200)
    assert result.observations[0].identity is None
    assert result.tracks[0].state == "lost"
    assert result.tracks[0].history == previous.history


def test_expiration_ends_track_without_waiting_for_another_detection():
    adapter = ByteTrackAdapter(TrackingConfig(lost_seconds=0.5, max_gap_seconds=2))
    old = confirmed(adapter).tracks[0].identity
    assert adapter.update(frame(2, 5.5), []).tracks[0].state == "lost"
    ended = adapter.update(frame(3, 5.7), [])
    assert ended.tracks == ()
    assert [(t.identity, t.reason) for t in ended.ended_tracks] == [(old, "expired")]
    assert observe(adapter, frame(4, 5.8)).observations[0].identity is None
    new = observe(adapter, frame(5, 5.9)).tracks[0]
    assert new.identity != old
    assert new.identity.epoch == old.epoch
    assert len(new.history) == 1


@pytest.mark.parametrize(
    "boundary,reason",
    [
        ({"index": 0, "timestamp": 0, "source": "other"}, "source_changed"),
        ({"index": 2, "width": 640}, "resolution_changed"),
        ({"index": 4, "timestamp": 5.2}, "frame_gap"),
        ({"index": 2, "timestamp": 6.3}, "time_gap"),
    ],
)
def test_discontinuities_end_old_tracks_and_namespace_reused_backend_ids(
    boundary, reason
):
    adapter = ByteTrackAdapter()
    old = confirmed(adapter).tracks[0].identity
    info = frame(**boundary)
    result = observe(adapter, info)
    assert result.reset_reason == reason
    assert [(t.identity, t.reason) for t in result.ended_tracks] == [(old, reason)]
    assert result.tracks == ()
    next_frame = replace(info, index=info.index + 1, timestamp_s=info.timestamp_s + 0.1)
    new = observe(adapter, next_frame).tracks[0]
    assert new.identity.backend_id == old.backend_id == 0
    assert new.identity.epoch == old.epoch + 1
    assert new.identity.source_id == info.source_id
    assert new.identity.value != old.value
    assert len(new.history) == 1


def test_manual_resets_and_independent_adapters_cannot_reuse_old_ids():
    adapter = ByteTrackAdapter()
    old = confirmed(adapter).tracks[0].identity
    assert adapter.reset()[0].reason == "manual_reset"
    new = confirmed(adapter).tracks[0].identity
    assert old.backend_id == new.backend_id == 0
    assert old.value != new.value
    other = confirmed(ByteTrackAdapter()).tracks[0].identity
    assert other.value != old.value and other.value != new.value
    adapter.reset()
    assert adapter.reset() == ()


@pytest.mark.parametrize(
    "invalid",
    [
        "duplicate_index",
        "backward_index",
        "duplicate_time",
        "backward_time",
        "wrong_observation",
        "fractional_class",
        "fractional_index",
        "resolution_with_old_time",
    ],
)
def test_rejected_inputs_do_not_advance_or_reset_backend_state(invalid):
    adapter = ByteTrackAdapter()
    before = confirmed(adapter).tracks[0]
    info = frame(2)
    if invalid == "duplicate_index":
        info = replace(info, index=1)
    elif invalid == "backward_index":
        info = replace(info, index=0)
    elif invalid == "duplicate_time":
        info = replace(info, timestamp_s=5.1)
    elif invalid == "backward_time":
        info = replace(info, timestamp_s=5.0)
    elif invalid == "fractional_index":
        info = replace(info, index=2.5)
    elif invalid == "resolution_with_old_time":
        info = replace(info, width=640, timestamp_s=5.0)
    item = detected(info)
    if invalid == "wrong_observation":
        item = detected(frame(2, source="wrong"))
    elif invalid == "fractional_class":
        item = replace(item, class_id=2.5)
    with pytest.raises(ValueError):
        adapter.update(info, [item])
    after = observe(adapter, frame(2)).tracks[0]
    assert after.identity == before.identity
    assert [d.frame.index for d in after.history] == [1, 2]


def test_time_pruning_applies_during_loss_and_retention_count_stays_bounded():
    adapter = ByteTrackAdapter(
        TrackingConfig(history_max_observations=3, history_max_seconds=0.15)
    )
    confirmed(adapter)
    for index in range(2, 100):
        result = observe(adapter, frame(index))
        track = result.tracks[0]
        assert len(track.history) <= 3
        assert all(
            result.frame.timestamp_s - d.frame.timestamp_s <= 0.15
            for d in track.history
        )
    assert track.observations_seen == 99
    assert track.history[-1].frame.index == 99
    lost = adapter.update(frame(100, 15.1), []).tracks[0]
    assert lost.state == "lost"
    assert lost.history == ()
    assert lost.observations_seen == 99


def test_class_changes_never_join_histories_even_when_backend_numbers_match():
    adapter = ByteTrackAdapter()
    old = confirmed(adapter).tracks[0]
    assert observe(adapter, frame(2), category=7).observations[0].identity is None
    result = observe(adapter, frame(3), category=7)
    new = next(t for t in result.tracks if t.state == "observed")
    assert old.identity.backend_id == new.identity.backend_id == 0
    assert old.identity.value != new.identity.value
    assert new.identity.class_id == 7
    assert [d.class_id for d in new.history] == [7]
    assert next(t for t in result.tracks if t.identity == old.identity).state == "lost"


def test_partial_backend_failure_discards_epoch_before_next_update(monkeypatch):
    adapter = ByteTrackAdapter()
    old = confirmed(adapter).tracks[0]
    original = adapter._associate

    def failing(info, detections):
        original(info, detections)
        raise RuntimeError("Partial update failed")

    with monkeypatch.context() as scoped:
        scoped.setattr(adapter, "_associate", failing)
        with pytest.raises(RuntimeError, match="Partial"):
            observe(adapter, frame(2))
    new = confirmed(adapter).tracks[0]
    assert new.identity.value != old.identity.value
    assert len(new.history) == 1


@pytest.mark.parametrize("origin", [5, 5000])
@pytest.mark.parametrize("reference_fps", [10, 60])
def test_irregular_source_intervals_control_history_independently_of_origin_and_fps(
    origin, reference_fps
):
    adapter = ByteTrackAdapter(
        TrackingConfig(
            frame_rate=reference_fps,
            history_max_seconds=0.2,
        )
    )
    for index, delta in enumerate([0, 0.06, 0.23, 0.41]):
        result = observe(adapter, frame(index, origin + delta))
    assert [d.frame.index for d in result.tracks[0].history] == [2, 3]
    assert result.tracks[0].observations_seen == 3
    assert result.tracks[0].segment_id == 0


def test_floor_filtered_observations_remain_visible_but_never_enter_history():
    adapter = ByteTrackAdapter()
    identity = confirmed(adapter).tracks[0].identity
    below = observe(adapter, frame(2), score=0)
    assert below.observations[0].status == "below_floor"
    assert below.observations[0].detection.score == 0
    assert below.tracks[0].state == "lost"
    assert [d.frame.index for d in below.tracks[0].history] == [1]
    recovered = observe(adapter, frame(3), score=0.1)
    assert recovered.tracks[0].identity == identity
    assert recovered.tracks[0].segment_id == 1
    assert [d.score for d in recovered.tracks[0].history] == [0.1]
