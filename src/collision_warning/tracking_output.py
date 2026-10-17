"""Tracking records shared by live inference and saved-observation replay."""

from dataclasses import asdict
from typing import Any

from collision_warning.domain import Track, TrackingResult


def track_summary(track: Track) -> dict[str, Any]:
    """Persist retention metadata without duplicating history on every frame."""
    return {
        "track_id": track.identity.value,
        "class_id": track.identity.class_id,
        "state": track.state,
        "segment_id": track.segment_id,
        "age_s": track.age_s,
        "time_since_observed_s": track.time_since_observed_s,
        "observations_seen": track.observations_seen,
        "consecutive_observations": track.consecutive_observations,
        "history_size": len(track.history),
        "history_first_timestamp_s": track.history[0].frame.timestamp_s
        if track.history
        else None,
        "history_last_timestamp_s": track.history[-1].frame.timestamp_s
        if track.history
        else None,
    }


def tracking_record(result: TrackingResult) -> dict[str, Any]:
    return {
        "frame": asdict(result.frame),
        "observations": [
            {
                "observation_index": observation.observation_index,
                "detection": asdict(observation.detection),
                "backend_id": observation.identity.backend_id
                if observation.identity
                else None,
                "track_id": observation.identity.value
                if observation.identity
                else None,
                "segment_id": observation.segment_id,
                "status": observation.status,
            }
            for observation in result.observations
        ],
        "tracks": [track_summary(track) for track in result.tracks],
        "ended_tracks": [
            {"track_id": ended.identity.value, "reason": ended.reason}
            for ended in result.ended_tracks
        ],
        "reset_reason": result.reset_reason,
    }
