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
