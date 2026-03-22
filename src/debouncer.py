"""
Speaker ID debouncing for stable camera tracking.

Removes rapid speaker-ID bounces that cause jarring crop window snaps.
"""


def debounce_speaker_ids(speaker_track_ids, min_hold_frames=15):
    """
    Remove rapid speaker-ID bounces shorter than min_hold_frames.

    Speaker detection sometimes flickers the active-speaker label during
    crosstalk or brief classification uncertainty, producing 1-10 frame
    segments that cause jarring rapid-fire crop snaps. This pre-filter
    replaces those short segments with the surrounding stable speaker ID
    so the downstream dead-zone tracker never sees them.

    Algorithm:
      1. Run-length encode the raw IDs into (track_id, start, length) runs.
      2. For any run shorter than min_hold_frames, replace it with the
         previous stable run's ID (or the next stable run if it's the first).
      3. Expand back to a per-frame list.

    Args:
        speaker_track_ids: Per-frame list of speaker IDs (int or None).
            None means no speaker detected at that frame.
        min_hold_frames: Minimum frames a speaker must hold to be "stable".

    Returns:
        Same-length list with short flicker runs replaced by nearest stable ID.
        None segments are never modified.

    Examples:
        >>> debounce_speaker_ids([0]*50 + [1]*3 + [0]*50, min_hold_frames=10)
        [0]*103  # The 3-frame speaker-1 segment is replaced by speaker 0

        >>> debounce_speaker_ids([None]*10 + [0]*50, min_hold_frames=15)
        [None]*10 + [0]*50  # None segments are untouched
    """
    if not speaker_track_ids:
        return []

    # Run-length encode
    runs = []  # list of (track_id, length)
    cur_id = speaker_track_ids[0]
    cur_len = 1

    for idx in range(1, len(speaker_track_ids)):
        sid = speaker_track_ids[idx]
        if sid == cur_id:
            cur_len += 1
        else:
            runs.append([cur_id, cur_len])
            cur_id = sid
            cur_len = 1
    runs.append([cur_id, cur_len])

    # Convert short non-None runs to nearest stable speaker ID.
    def is_stable(run):
        rid, length = run
        return rid is not None and length >= min_hold_frames

    for i, (rid, length) in enumerate(runs):
        if rid is None or is_stable((rid, length)):
            continue

        # Prefer previous stable run
        replacement = None
        for j in range(i - 1, -1, -1):
            prev_rid, prev_len = runs[j]
            if prev_rid is not None and prev_len >= min_hold_frames:
                replacement = prev_rid
                break

        # If no previous stable, use next stable
        if replacement is None:
            for j in range(i + 1, len(runs)):
                next_rid, next_len = runs[j]
                if next_rid is not None and next_len >= min_hold_frames:
                    replacement = next_rid
                    break

        if replacement is not None:
            runs[i][0] = replacement

    # Expand back to frame sequence
    output = []
    for rid, length in runs:
        output.extend([rid] * length)
    return output
