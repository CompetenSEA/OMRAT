from omrat_api.engine.geometry_engine import GeometryEngine


def test_compute_corridor_overlaps_handles_empty_and_valid_shapes():
    segments = GeometryEngine.parse_segments(
        [
            {"segment_id": "S_empty", "coords": [(0, 0)], "width_m": 3},
            {"segment_id": "S1", "coords": [(0, 0), (8, 0)], "width_m": 4},
        ]
    )
    objects = GeometryEngine.parse_objects(
        [
            {"feature_id": "bad", "coords": [(0, 0), (1, 1)]},
            {
                "feature_id": "O1",
                "object_type": "Foundation",
                "coords": [(3, -1), (5, -1), (5, 1), (3, 1)],
            },
        ]
    )

    overlaps = GeometryEngine.compute_corridor_overlaps(segments, objects)

    assert len(segments) == 1
    assert len(objects) == 1
    assert len(overlaps) == 1
    assert overlaps[0].feature_id == "O1"
    assert overlaps[0].overlap_area_m2 > 0
