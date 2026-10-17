"""Characterize the pinned real CPU backend before introducing our tracker adapter.

Optional imports happen in fixtures/helpers: default CPU collection needs no
tracking packages, but explicitly selecting this suite fails if they are absent.
"""

import subprocess
import sys

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.tracking]


@pytest.fixture
def tracker():
    from trackers import ByteTrackTracker

    return ByteTrackTracker(
        frame_rate=10.0,
        lost_track_buffer=30,  # One second, including in timestamped mode.
        minimum_consecutive_frames=2,
        track_activation_threshold=0.6,
        high_conf_det_threshold=0.5,
        minimum_iou_threshold=0.3,
    )


def detections(*items):
    """Items are (original index, x position, confidence, class ID)."""
    import numpy as np
    import supervision as sv

    return sv.Detections(
        xyxy=np.array(
            [[x, 10, x + 40, 50] for _, x, _, _ in items], dtype=float
        ).reshape(-1, 4),
        confidence=np.array([score for _, _, score, _ in items], dtype=float),
        class_id=np.array([class_id for _, _, _, class_id in items], dtype=int),
        data={"observation_index": np.array([index for index, _, _, _ in items])},
    )


def associations(result):
    return dict(
        zip(
            result.data["observation_index"].tolist(),
            result.tracker_id.tolist(),
            strict=True,
        )
    )


def confirm(tracker):
    first = tracker.update(detections((0, 10, 0.9, 2)), timestamp=5.0)
    assert associations(first) == {0: -1}
    second = tracker.update(detections((0, 11, 0.9, 2)), timestamp=5.1)
    identity = associations(second)[0]
    assert identity >= 0
    return identity


def test_import_requires_no_inference_framework_or_network():
    # A new interpreter also catches eager optional imports masked by other tests.
    code = """
import socket
import sys
def forbid_network(*args, **kwargs):
    raise AssertionError('backend import attempted network access')
socket.socket.connect = forbid_network
socket.create_connection = forbid_network
from trackers import ByteTrackTracker
ByteTrackTracker()
assert not {'torch', 'torchvision', 'ultralytics'} & sys.modules.keys()
"""
    subprocess.run([sys.executable, "-I", "-c", code], check=True, timeout=30)


def test_confirmation_and_low_confidence_recovery(tracker):
    identity = confirm(tracker)
    low = tracker.update(detections((0, 12, 0.18, 2)), timestamp=5.2)
    assert associations(low) == {0: identity}
    high = tracker.update(detections((0, 13, 0.9, 2)), timestamp=5.3)
    assert associations(high) == {0: identity}


def test_high_score_stage_takes_priority_over_overlapping_low_score_box(tracker):
    identity = confirm(tracker)
    result = tracker.update(
        detections((10, 12, 0.18, 2), (20, 12, 0.5, 2)), timestamp=5.2
    )
    assert associations(result) == {20: identity, 10: -1}


@pytest.mark.parametrize("score", [0.18, 0.5, 0.59])
def test_unmatched_boxes_below_activation_do_not_spawn_tracks(tracker, score):
    for timestamp in [5.0, 5.1, 5.2]:
        result = tracker.update(detections((0, 10, score, 2)), timestamp=timestamp)
        assert associations(result) == {0: -1}
        assert len(tracker.tracked_objects) == 0
    # Low-only boxes did not seed a hidden track: high evidence starts tentative.
    high = tracker.update(detections((0, 10, 0.9, 2)), timestamp=5.3)
    assert associations(high) == {0: -1}


def test_activation_threshold_is_inclusive(tracker):
    tracker.update(detections((0, 10, 0.6, 2)), timestamp=5.0)
    result = tracker.update(detections((0, 10, 0.6, 2)), timestamp=5.1)
    assert associations(result)[0] >= 0


def test_backend_has_no_lower_confidence_floor(tracker):
    # The future adapter must apply its explicit low floor before this backend.
    identity = confirm(tracker)
    result = tracker.update(detections((0, 12, 0.0, 2)), timestamp=5.2)
    assert associations(result) == {0: identity}


def test_reordered_output_preserves_original_measurements_and_indices(tracker):
    import numpy as np

    for timestamp in [5.0, 5.1]:
        previous = tracker.update(
            detections((100, 10, 0.9, 2), (200, 150, 0.9, 2)), timestamp=timestamp
        )
    identities = associations(previous)
    assert len(set(identities.values())) == 2
    assert all(identity >= 0 for identity in identities.values())
    # Low first, high second: the backend emits first-stage high matches first.
    original = detections((100, 12, 0.18, 2), (200, 152, 0.9, 2))
    boxes = original.xyxy.copy()
    scores = original.confidence.copy()
    classes = original.class_id.copy()
    result = tracker.update(original, timestamp=5.2)
    assert result.data["observation_index"].tolist() == [200, 100]
    assert associations(result) == identities
    for observation_index, box, score in zip(
        result.data["observation_index"], result.xyxy, result.confidence, strict=True
    ):
        source_index = (
            original.data["observation_index"].tolist().index(observation_index)
        )
        np.testing.assert_array_equal(box, original.xyxy[source_index])
        assert score == scores[source_index]
    np.testing.assert_array_equal(original.xyxy, boxes)
    np.testing.assert_array_equal(original.confidence, scores)
    np.testing.assert_array_equal(original.class_id, classes)
    assert original.tracker_id is None


def test_empty_update_emits_no_measurement_and_short_gap_keeps_identity(tracker):
    identity = confirm(tracker)
    empty = tracker.update(detections(), timestamp=5.2)
    assert len(empty) == 0
    assert empty.tracker_id.tolist() == []
    # This separate API contains a prediction; it is not a detector measurement.
    assert tracker.tracked_objects.tracker_id.tolist() == [identity]
    recovered = tracker.update(detections((0, 12, 0.9, 2)), timestamp=5.4)
    assert associations(recovered) == {0: identity}


def test_empty_frames_expire_tracks(tracker):
    confirm(tracker)
    for timestamp in [5.4, 5.8, 6.2]:
        assert len(tracker.update(detections(), timestamp=timestamp)) == 0
    assert len(tracker.tracked_objects) == 0


def test_long_source_gap_expires_before_reassociation(tracker):
    identity = confirm(tracker)
    # No intervening calls: elapsed source time must expire the old association.
    first = tracker.update(detections((0, 11, 0.9, 2)), timestamp=6.2)
    assert associations(first) == {0: -1}
    confirmed = tracker.update(detections((0, 11, 0.9, 2)), timestamp=6.3)
    assert associations(confirmed)[0] >= 0
    assert associations(confirmed)[0] != identity


def test_irregular_intervals_keep_identity_without_using_timestamp_origin(tracker):
    for origin in [5.0, 5000.0]:
        tracker.reset()
        identities = []
        for delta, x in [(0, 10), (0.06, 11), (0.23, 12), (0.41, 13)]:
            result = tracker.update(
                detections((0, x, 0.9, 2)), timestamp=origin + delta
            )
            identities.append(associations(result)[0])
        assert identities[0] == -1
        assert identities[1] >= 0
        assert identities[1:] == [identities[1]] * 3


def test_class_labels_do_not_gate_backend_association(tracker):
    # The later adapter must partition by class to prevent this association.
    identity = confirm(tracker)
    result = tracker.update(detections((0, 12, 0.9, 7)), timestamp=5.2)
    assert associations(result) == {0: identity}
    assert result.class_id.tolist() == [7]


def test_reset_clears_tracks_and_reuses_numeric_ids(tracker):
    first_identity = confirm(tracker)
    tracker.reset()
    assert len(tracker.tracked_objects) == 0
    assert confirm(tracker) == first_identity


@pytest.mark.parametrize("timestamp", [4.0, float("nan"), float("inf")])
def test_invalid_timestamp_warns_and_skips_instead_of_failing(tracker, timestamp):
    identity = confirm(tracker)
    with pytest.warns(UserWarning, match="timestamp"):
        result = tracker.update(detections((0, 150, 0.9, 2)), timestamp=timestamp)
    assert associations(result) == {0: -1}
    following = tracker.update(detections((0, 12, 0.9, 2)), timestamp=5.2)
    assert associations(following) == {0: identity}


def test_duplicate_timestamp_warns_but_still_associates(tracker):
    identity = confirm(tracker)
    with pytest.warns(UserWarning, match="duplicate timestamp"):
        result = tracker.update(detections((0, 12, 0.9, 2)), timestamp=5.1)
    assert associations(result) == {0: identity}
