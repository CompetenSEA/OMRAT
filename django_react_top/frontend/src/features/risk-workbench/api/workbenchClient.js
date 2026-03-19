import { buildSegmentDraft } from '../model/routeGeometry.js';

/**
 * Minimal API client for risk workbench flows.
 * Falls back to local behavior when endpoint is unavailable.
 */
export function createWorkbenchClient(baseUrl = '', options = {}) {
  const prefix = baseUrl.replace(/\/$/, '');
  const authToken = options.authToken || '';
  const strictServer = Boolean(options.strictServer);
  const taskStore = new Map();

  async function request(path, body) {
    const headers = { 'Content-Type': 'application/json' };
    if (authToken) {
      headers.Authorization = `Bearer ${authToken}`;
    }
    const response = await fetch(`${prefix}${path}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Request failed (${response.status})`);
    }

    const payload = await response.json();
    if (payload && typeof payload === 'object' && Object.prototype.hasOwnProperty.call(payload, 'ok')) {
      if (!payload.ok) {
        const message = payload.error?.message || 'Workbench request failed';
        throw new Error(message);
      }
      return payload.data;
    }
    return payload;
  }

  async function postAction(action, body = {}) {
    return request(`/api/workbench/${action}`, body);
  }

  return {
    postAction,

    async createRouteSegment(payload) {
      try {
        return await postAction('create-route-segment', payload);
      } catch {
        if (strictServer) throw new Error('Route segment API unavailable in strict-server mode');
        return buildSegmentDraft({
          startPoint: payload.start_point,
          endPoint: payload.end_point,
          segmentId: payload.segment_id,
          routeId: payload.route_id,
          widthM: payload.width_m,
          tangentOffsetM: payload.tangent_offset_m,
        });
      }
    },

    async enqueueRun(payload) {
      try {
        return await postAction('enqueue-run', payload);
      } catch {
        if (strictServer) throw new Error('Run queue API unavailable in strict-server mode');
        const task = {
          task_id: `fallback-${Date.now()}`,
          state: 'queued',
          progress: 0,
          message: 'Run queued (fallback mode)',
          payload,
        };
        taskStore.set(task.task_id, task);
        return task;
      }
    },

    async executeRun(taskId) {
      try {
        return await postAction('execute-run', { task_id: taskId });
      } catch {
        if (strictServer) throw new Error('Run execution API unavailable in strict-server mode');
        const task = taskStore.get(taskId);
        if (!task) throw new Error(`Unknown task id ${taskId}`);

        const running = { ...task, state: 'running', progress: 50, message: 'Computing overlaps (fallback mode)' };
        taskStore.set(taskId, running);

        const payload = task.payload || {};
        const completed = {
          ...running,
          state: 'completed',
          progress: 100,
          message: 'Run completed (fallback mode)',
          result: {
            status: 'completed',
            report_path: payload.settings?.report_path || '/tmp/omrat-report.md',
            powered_summary: {
              segments: (payload.segment_data || []).length,
              traffic_rows: (payload.traffic_data || []).length,
            },
            drifting_summary: {
              objects: (payload.objects || []).length,
              overlap_hits: Math.min((payload.segment_data || []).length, (payload.objects || []).length),
              overlap_area_m2: Math.min((payload.segment_data || []).length, (payload.objects || []).length) * 125.5,
            },
          },
        };

        taskStore.set(taskId, completed);
        return completed;
      }
    },

    async getTask(taskId) {
      try {
        return await postAction('get-task', { task_id: taskId });
      } catch {
        if (strictServer) throw new Error('Task polling API unavailable in strict-server mode');
        const task = taskStore.get(taskId);
        if (!task) throw new Error(`Unknown task id ${taskId}`);
        return task;
      }
    },

    async syncLayers(payload) {
      return postAction('sync-layers', payload);
    },

    async previewCorridorOverlaps(payload) {
      return postAction('preview-corridor-overlaps', payload);
    },

    async loadProject(payload) {
      return postAction('load-project', payload);
    },

    async importProject(currentState, incomingPayload, merge = true) {
      return postAction('import-project', {
        current_state: currentState,
        incoming_payload: incomingPayload,
        merge,
      });
    },

    async ingestAis(rows) {
      return postAction('ingest-ais', { rows });
    },

    async buildOsmScene(osmContext) {
      return postAction('build-osm-scene', { osm_context: osmContext });
    },

    async evaluateLandCrossings(payload, osmContext) {
      return postAction('evaluate-land-crossings', { payload, osm_context: osmContext });
    },

    async executeRunAsync(taskId) {
      return postAction('execute-run-async', { task_id: taskId });
    },

    async processQueue() {
      return postAction('process-queue', {});
    },
  };
}
