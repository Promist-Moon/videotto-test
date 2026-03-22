"""Basic tests for the face tracking module."""

from src.tracker import track_face_crop


class TestTrackFaceCropBasics:
    """Basic sanity tests for track_face_crop."""

    def test_empty_input(self):
        """Empty bbox list returns empty output."""
        compressed, scene_cuts = track_face_crop([])
        assert compressed == []
        assert scene_cuts == []

    def test_single_frame_with_face(self):
        """One frame with a face returns one crop position."""
        # Face centered at (320, 180) in a 640x360 frame
        bboxes = [(300, 160, 340, 200)]
        compressed, scene_cuts = track_face_crop(bboxes, video_width=640, video_height=360)

        assert len(compressed) == 1
        assert compressed[0][2] == 1  # frame count
        assert compressed[0][0] > 0   # valid x coordinate
        assert compressed[0][1] > 0   # valid y coordinate
        assert scene_cuts == []

    def test_no_face_before_first_detection(self):
        """Frames with None bbox before first face return (-1, -1) sentinel."""
        bboxes = [None, None, None, (300, 160, 340, 200), (300, 160, 340, 200)]
        compressed, scene_cuts = track_face_crop(bboxes, video_width=640, video_height=360)

        # First segment should be the no-face sentinel
        assert compressed[0][0] == -1
        assert compressed[0][1] == -1
        assert compressed[0][2] == 3  # 3 no-face frames

    def test_deadzone_blocks_small_motion(self):
        """Small offsets inside dead zone should not create segment splits."""
        # First frame set crop center; second frame moves only 4px (inside 10.1px dead zone)
        bboxes = [
            (310, 160, 330, 200),
            (314, 160, 334, 200),
        ]
        compressed, scene_cuts = track_face_crop(bboxes, video_width=640, video_height=360, deadzone_ratio=0.10)

        assert scene_cuts == []
        assert len(compressed) == 1
        assert compressed[0][2] == 2

    def test_scene_cut_forces_instant_snap(self):
        """A scene boundary should generate a scene_cut and immediate crop jump."""
        bboxes = [
            (200, 160, 240, 200),
            (420, 160, 460, 200),
        ]
        compressed, scene_cuts = track_face_crop(bboxes, video_width=640, video_height=360, face_scenes=[(1, 2)])

        assert scene_cuts == [1]
        assert len(compressed) == 2
        assert compressed[0][2] == 1
        assert compressed[1][2] == 1

    def test_invalid_bbox_treated_as_no_face(self):
        """Invalid bbox (x2 < x1 or y2 < y1) should be treated as no face."""
        # Invalid bbox: x2 < x1
        bboxes = [(340, 160, 300, 200), (300, 160, 340, 200)]
        compressed, scene_cuts = track_face_crop(bboxes, video_width=640, video_height=360)

        # First frame invalid (no face), second valid
        assert len(compressed) == 2
        assert compressed[0][0] == -1  # no-face sentinel
        assert compressed[0][1] == -1
        assert compressed[0][2] == 1
        assert compressed[1][2] == 1  # valid face

    def test_invalid_scene_ranges_skipped(self):
        bboxes = [(300,160,340,200)] * 10
        # Invalid: start > end; overlap
        compressed, scene_cuts = track_face_crop(bboxes, face_scenes=[(5,3), (7,9)])  # invalid + valid
        assert scene_cuts == [7]  # Only valid start marked
