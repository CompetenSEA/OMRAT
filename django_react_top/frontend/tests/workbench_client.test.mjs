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

  const importedLegacy = await client.importLegacyProject({ segment_data: {} });
  assert.deepEqual(importedLegacy.echoed.segment_data, {});

  const exportedLegacy = await client.exportLegacyProject({
    segment_data: [],
    traffic_data: [],
    depths: [],
    objects: [],
    settings: {},
  });
  assert.equal(Array.isArray(exportedLegacy.echoed.segment_data), true);

  const exportedIwrap = await client.exportIwrapXml({
    segment_data: [],
    traffic_data: [],
    depths: [],
    objects: [],
    settings: {},
  });
  assert.equal(Array.isArray(exportedIwrap.echoed.segment_data), true);

  const importedIwrap = await client.importIwrapXml('<xml />');
  assert.equal(importedIwrap.echoed.iwrap_xml, '<xml />');

  const listedRuns = await client.listRuns(5);
  assert.equal(listedRuns.echoed.limit, 5);

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

test('readiness action uses fallback model when offline', async () => {
  const originalFetch = global.fetch;
  global.fetch = async () => {
    throw new Error('offline');
  };

  const client = createWorkbenchClient();
  const readiness = await client.assessProjectReadiness({
    segment_data: [],
    traffic_data: [],
    depths: [],
    objects: [],
    settings: { model_name: 'demo', report_path: '' },
  });

  assert.equal(readiness.ready_for_run, false);
  assert.equal(readiness.counts.blocking_issues > 0, true);
  assert.equal(readiness.counts.warnings > 0, true);

  global.fetch = originalFetch;
});

test('readiness action unwraps server envelope response', async () => {
  const originalFetch = global.fetch;
  global.fetch = async (_url, options) => ({
    ok: true,
    async json() {
      return {
        ok: true,
        data: {
          ready_for_run: true,
          counts: { blocking_issues: 0, warnings: 0 },
          issues: [],
          echoed: JSON.parse(options.body),
        },
      };
    },
  });

  const client = createWorkbenchClient();
  const payload = {
    segment_data: [{ segment_id: 'S1', coords: [[0, 0], [1, 1]] }],
    traffic_data: [{ segment_id: 'S1' }],
    depths: [{ feature_id: 'D1' }],
    objects: [{ feature_id: 'O1' }],
    settings: { model_name: 'demo', report_path: '/tmp/report.md' },
  };
  const readiness = await client.assessProjectReadiness(payload);
  assert.equal(readiness.ready_for_run, true);
  assert.equal(readiness.echoed.settings.model_name, 'demo');

  global.fetch = originalFetch;
});
