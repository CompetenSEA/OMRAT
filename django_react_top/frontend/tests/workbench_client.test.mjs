import test from 'node:test';
import assert from 'node:assert/strict';

import { createWorkbenchClient } from '../src/features/risk-workbench/api/workbenchClient.js';

test('client falls back to local geometry when fetch fails', async () => {
  const originalFetch = global.fetch;
  global.fetch = async () => {
    throw new Error('network unavailable');
  };

  const client = createWorkbenchClient();
  const draft = await client.createRouteSegment({
    start_point: [2, 2],
    end_point: [12, 2],
    segment_id: 7,
    route_id: 3,
    width_m: 10,
    tangent_offset_m: 4,
  });

  assert.equal(draft.label, 'LEG_7_3');
  assert.equal(draft.leg_direction, 'E');

  global.fetch = originalFetch;
});

test('run lifecycle fallback queues and completes task', async () => {
  const originalFetch = global.fetch;
  global.fetch = async () => {
    throw new Error('network unavailable');
  };

  const client = createWorkbenchClient();
  const payload = {
    segment_data: [{ segment_id: 'S1' }],
    traffic_data: [{ segment_id: 'S1' }],
    objects: [{ feature_id: 'O1' }],
    settings: { report_path: '/tmp/fallback.md' },
  };

  const queued = await client.enqueueRun(payload);
  assert.equal(queued.state, 'queued');

  const executed = await client.executeRun(queued.task_id);
  assert.equal(executed.state, 'completed');
  assert.equal(executed.result.status, 'completed');

  const fetched = await client.getTask(queued.task_id);
  assert.equal(fetched.state, 'completed');

  global.fetch = originalFetch;
});

test('client unwraps envelope responses and exposes standalone actions', async () => {
  const originalFetch = global.fetch;
  global.fetch = async (_url, options) => {
    const body = JSON.parse(options.body);
    if (body?.trigger_error) {
      return {
        ok: true,
        async json() {
          return { ok: false, error: { message: 'Synthetic failure' } };
        },
      };
    }

    return {
      ok: true,
      async json() {
        return { ok: true, data: { echoed: body } };
      },
    };
  };

  const client = createWorkbenchClient();
  const syncResult = await client.syncLayers({ segment_data: [{ segment_id: 'S1' }] });
  assert.equal(syncResult.echoed.segment_data[0].segment_id, 'S1');

  const scene = await client.buildOsmScene({ land_features: [], fixed_object_features: [] });
  assert.deepEqual(scene.echoed.osm_context, { land_features: [], fixed_object_features: [] });

  const processed = await client.processQueue();
  assert.equal(processed.echoed && typeof processed.echoed, 'object');

  await assert.rejects(
    () => client.postAction('sync-layers', { trigger_error: true }),
    /Synthetic failure/,
  );

  global.fetch = originalFetch;
});

test('strict-server mode disables local fallback behavior', async () => {
  const originalFetch = global.fetch;
  global.fetch = async () => {
    throw new Error('offline');
  };

  const client = createWorkbenchClient('', { strictServer: true });

  await assert.rejects(
    () => client.createRouteSegment({ start_point: [2, 2], end_point: [12, 2] }),
    /strict-server mode/,
  );
  await assert.rejects(() => client.enqueueRun({}), /strict-server mode/);

  global.fetch = originalFetch;
});

test('client sends bearer auth token when configured', async () => {
  const originalFetch = global.fetch;
  let seenAuthHeader = '';
  global.fetch = async (_url, options) => {
    seenAuthHeader = options.headers.Authorization;
    return {
      ok: true,
      async json() {
        return { ok: true, data: { accepted: true } };
      },
    };
  };

  const client = createWorkbenchClient('', { authToken: 'secret-token' });
  const result = await client.syncLayers({ segment_data: [] });
  assert.equal(result.accepted, true);
  assert.equal(seenAuthHeader, 'Bearer secret-token');

  global.fetch = originalFetch;
});
