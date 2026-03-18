from omrat_api.services.osm_scene_service import OSMSceneService


def _osm_context():
    return {
        "land_features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[(0, 0), (5, 0), (5, 5), (0, 5), (0, 0)]],
                },
                "properties": {"natural": "coastline"},
            }
        ],
        "fixed_object_features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[(7, 0), (9, 0), (9, 2), (7, 2), (7, 0)]],
                },
                "properties": {"man_made": "breakwater"},
            }
        ],
    }


def test_scene_build_and_merge_objects():
    scene = OSMSceneService.build_scene(_osm_context())
    merged = OSMSceneService.merge_objects_with_scene(
        {
            "objects": [{"feature_id": "manual-1", "object_type": "Turbine", "coords": [(10,0), (11,0), (11,1), (10,1)]}],
            "segment_data": [],
        },
        _osm_context(),
    )

    assert len(scene["land_areas"]) == 1
    assert len(scene["fixed_objects"]) == 1
    assert len(merged["objects"]) == 2


def test_land_crossings_count():
    payload = {"segment_data": [{"segment_id": "S1", "coords": [(-1, 2), (6, 2)]}]}
    crossings = OSMSceneService.compute_land_crossings(payload, _osm_context())

    assert crossings["count"] == 1
    assert crossings["land_crossings"][0]["segment_id"] == "S1"
