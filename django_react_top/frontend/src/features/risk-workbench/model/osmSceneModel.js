/**
 * Frontend OSM scene mapper for map visualization assumptions.
 * Uses backend OSM scene responses to produce layer-ready view models.
 */

export function mapOsmSceneToLayers(scene) {
  const landAreas = scene.land_areas || [];
  const fixedObjects = scene.fixed_objects || [];

  return {
    landLayer: landAreas.map((land) => ({
      id: land.land_id,
      kind: 'land',
      coords: land.coords,
      style: { fill: '#d8d4c8', stroke: '#a59f8f' },
    })),
    fixedObjectLayer: fixedObjects.map((obj) => ({
      id: obj.feature_id,
      kind: obj.object_type,
      source: obj.source || 'osm',
      coords: obj.coords,
      style: { fill: '#5b6d7d', stroke: '#2f3b46' },
    })),
  };
}

export function mergeManualAndOsmObjects(manualObjects = [], osmFixedObjects = []) {
  return [
    ...manualObjects.map((obj) => ({ ...obj, source: obj.source || 'manual' })),
    ...osmFixedObjects.map((obj) => ({ ...obj, source: obj.source || 'osm' })),
  ];
}
