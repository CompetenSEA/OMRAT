from omrat_api.services.route_editing_service import RouteEditingService


def test_is_valid_point_pair_matches_plugin_semantics():
    assert RouteEditingService.is_valid_point_pair((5, 2), (8, 2))
    assert not RouteEditingService.is_valid_point_pair((0.2, 0.1), (8, 2))
    assert not RouteEditingService.is_valid_point_pair((5, 2), (5, 2))


def test_calculate_tangent_line_perpendicular_and_offset():
    tangent_start, tangent_end = RouteEditingService.calculate_tangent_line(
        mid=(5, 0),
        start=(0, 0),
        end=(10, 0),
        offset=2,
    )

    assert tangent_start.as_tuple() == (5.0, -2.0)
    assert tangent_end.as_tuple() == (5.0, 2.0)


def test_build_segment_draft_returns_canonical_shape():
    draft = RouteEditingService.build_segment_draft(
        start=(2, 2),
        end=(12, 2),
        segment_id=4,
        route_id=9,
        width_m=100,
        tangent_offset_m=3,
    )

    assert draft.label == "LEG_4_9"
    assert draft.segment_id == "4"
    assert draft.route_id == "9"
    assert draft.coords == [(2.0, 2.0), (12.0, 2.0)]
    assert draft.leg_direction == "E"
    assert draft.bearing_deg == 90.0
    assert draft.tangent_line["start"] == (7.0, -1.0)
    assert draft.tangent_line["end"] == (7.0, 5.0)
    assert draft.corridor_polygon == [(2.0, 52.0), (2.0, -48.0), (12.0, -48.0), (12.0, 52.0), (2.0, 52.0)]
