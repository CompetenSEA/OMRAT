import test from 'node:test';
import assert from 'node:assert/strict';

import { buildOsmTileViewport, isLikelyLonLatBounds, lonLatToPixel } from '../src/features/risk-workbench/model/osmBasemap.js';
import { buildCanonicalPayload, initialWorkbenchState } from '../src/features/risk-workbench/model/workbenchState.js';

test('OSM helpers identify lon/lat bounds and tile viewport', () => {
  const bounds = { minX: 4.4, minY: 57.9, maxX: 5.0, maxY: 58.2 };
  assert.equal(isLikelyLonLatBounds(bounds), true);

  const viewport = buildOsmTileViewport(bounds, 7, 64);
  assert.equal(viewport.tiles.length > 0, true);
  assert.equal(viewport.width > 0, true);
  assert.equal(viewport.height > 0, true);

  const px = lonLatToPixel(4.8, 58.0, 7);
  assert.equal(Number.isFinite(px.x), true);
  assert.equal(Number.isFinite(px.y), true);
});

test('canonical payload includes osm_context for run orchestration', () => {
  const payload = buildCanonicalPayload({ ...initialWorkbenchState, segmentData: [{ segment_id: 'S1', coords: [[4.6, 58.0], [4.9, 58.0]] }] });
  assert.equal(typeof payload.osm_context, 'object');
  assert.equal(Array.isArray(payload.osm_context.land_features), true);
  assert.equal(Array.isArray(payload.osm_context.fixed_object_features), true);
});
