from src.debouncer import debounce_speaker_ids


def test_debounce_short_flicker():
    raw = [0] * 10 + [1] * 3 + [0] * 10
    out = debounce_speaker_ids(raw, min_hold_frames=5)
    assert out == [0] * 23


def test_debounce_preserves_none_segments():
    raw = [None] * 5 + [0] * 4 + [1] * 6 + [0] * 5
    out = debounce_speaker_ids(raw, min_hold_frames=5)
    # the short 4-frame speaker 0 is replaced with following stable speaker 1
    assert out[:5] == [None] * 5
    assert out[5:5 + 4] == [1] * 4
    assert out[5 + 4 : 5 + 4 + 6] == [1] * 6
    assert out[-5:] == [0] * 5
