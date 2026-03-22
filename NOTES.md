## Task 1: Bug Finding and Fixing

The following changes were made to `src/tracker.py`
1. Fix dead-zone checks

Initially, in `track_face_crop`, `need_move_x = abs(dx) > 0` and `need_move_y = abs(dy) > 0`. This implemention meant any face motion, even within the dead-zone, triggers smoothing, which renders the deadzone unused. The deadzone tracking never uses `dz_half_w` and `dz_half_h`, only in target computation.

Change the checks to:   
`need_move_x = abs(dx) > dz_half_w`.  
`need_move_y = abs(dy) > dz_half_y`.  

Just by implementing this change, there is a difference in the results of clip_a.json

2. Fix scene cut snapping

Initially, `should_snap` only logged the frame in `scene_cut_frames` but did not actually reposition the crop center. The crop continued with smoothing, not hard snapping.

We change to: when `should_snap`, compute snap target based on dead-zone edge, clamp it, and set `crop_cx, crop_cy` immediately, then `continue` to skip smoothing.

3. Add bbox validation

In `bbox_center`, added check: if `x2 < x1` or `y2 < y1`, return `None` (treat as no face).

## Task 2: Feature Implementation

In this task, we implemented `debounce_speaker_ids` in `src/debouncer.py`, in which we:
- Run-length encode speaker IDs
- Replace short runs (< min_hold_frames) with nearest stable speaker ID
- Preserve `None` segments
- Expand back to per-frame list

This reduces jittery crop snaps from transient speaker flickers.

## Task 3: Tests

We added regression tests to both `src/tracker.py` and `src/debouncer.py`.

In `tests/test_tracker.py`:
- `test_deadzone_blocks_small_motion`: ensures small moves inside dead zone don't split segments
- `test_scene_cut_forces_instant_snap`: verifies hard snap at scene boundaries
- `test_invalid_bbox_treated_as_no_face`: checks invalid bboxes are handled as no face

In `tests/test_debouncer.py`, we made tests for short flicker removal and None preservation.

## Results Comparison: Improvement Demonstrated

### clip_a.json (Single speaker with natural head movement)

**Before fixes (dead-zone bug present):**
```
Total frames processed:    500
Compressed segments:       54
Compression ratio:         9.3x
Scene cuts detected:       0
```

**After fixes (dead-zone corrected, debouncer implemented):**
```
Total frames processed:    500
Compressed segments:       20
Compression ratio:         25.0x
Scene cuts detected:       0
```

**Improvement:**
- Segments reduced from 54 to 20 (62% fewer)
- Compression ratio increased from 9.3x to 25.0x (169% better)
- More stable output: longer segments (e.g., 106 frames vs. max 54 before) indicate dead zone now prevents unnecessary movements

### clip_b.json (Single speaker transitioning to two-person shot and back)

**Before debouncer:**
```
Total frames processed:    425
Compressed segments:       8
Compression ratio:         53.1x
Scene cuts detected:       8
```

**After debouncer:**
```
Total frames processed:    425
Compressed segments:       6
Compression ratio:         70.8x
Scene cuts detected:       2
```

**Improvement:**
- Segments reduced from 8 to 6 (25% fewer)
- Compression ratio increased from 53.1x to 70.8x (33% better)
- Scene cuts reduced from 8 to 2: debouncer eliminated false speaker switches from noise

## Edge Cases Addressed

- Invalid face bboxes: now treated as no face
- Speaker IDs: added type checks to ensure int/None (in debouncer)
- Other potential: video dims too small, extreme params, etc. (not implemented due to time)

## Design Decisions

- Debouncer: prefers previous stable speaker for replacement, falls back to next if none previous
- Bbox validation: treat invalid as no face to avoid crashes
- Tests: focused on regression for core bugs

## Future Improvements

- Add more edge case validation (e.g., overlapping scenes, extreme deadzone/smoothing)
- Optimize RLE for very long sequences
- Add logging for invalid inputs