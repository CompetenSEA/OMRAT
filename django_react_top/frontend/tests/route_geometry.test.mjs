import test from 'node:test';
import assert from 'node:assert/strict';

import {
  buildSegmentDraft,
  calculateBearing,
  buildCorridorPolygon,
  directionLabelFromBearing,
} from '../src/features/risk-workbench/model/routeGeometry.js';

test('calculateBearing returns east as 90 degrees', () => {
  assert.equal(calculateBearing([2, 2], [12, 2]), 90);
  assert.equal(directionLabelFromBearing(90), 'E');
});

test('buildCorridorPolygon closes polygon ring', () => {
  const polygon = buildCorridorPolygon([2, 2], [12, 2], 10);
  assert.equal(polygon.length, 5);
  assert.deepEqual(polygon[0], polygon[polygon.length - 1]);
});

test('buildSegmentDraft includes standalone route metadata', () => {
  const draft = buildSegmentDraft({
    startPoint: [2, 2],
    endPoint: [12, 2],
    segmentId: 2,
    routeId: 5,
    widthM: 10,
    tangentOffsetM: 3,
  });

  assert.equal(draft.label, 'LEG_2_5');
  assert.equal(draft.leg_direction, 'E');
  assert.equal(draft.bearing_deg, 90);
  assert.equal(draft.corridor_polygon.length, 5);
});
