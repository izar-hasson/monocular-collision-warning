"""Source PTS cases independent of decoder installation and processing speed."""

from fractions import Fraction
from types import SimpleNamespace

import pytest

from collision_warning.video import decoded_frames


def raw(pts: int | None) -> SimpleNamespace:
    return SimpleNamespace(
        pts=pts,
        time_base=Fraction(1, 1000),
        width=100,
        height=60,
        to_ndarray=lambda *, format: format,
    )


def test_irregular_source_time_and_nonzero_origin_are_preserved() -> None:
    frames = list(decoded_frames([raw(v) for v in [5000, 5033, 5130]], "clip"))
    assert [f.info.timestamp_s for f in frames] == [5.0, 5.033, 5.13]
    assert [f.info.index for f in frames] == [0, 1, 2]
    assert all(f.image == "bgr24" for f in frames)


@pytest.mark.parametrize("timestamps", [[None], [20, 20], [20, 10]])
def test_missing_duplicate_and_backward_pts_fail(timestamps: list[int | None]) -> None:
    with pytest.raises(ValueError, match="timestamp"):
        list(decoded_frames([raw(v) for v in timestamps], "clip"))


def test_invalid_time_base_fails() -> None:
    value = raw(0)
    value.time_base = Fraction(0)
    with pytest.raises(ValueError, match="timestamp"):
        list(decoded_frames([value], "clip"))
