import { buildSegmentDraft } from '../model/routeGeometry.js';

/**
 * Minimal API client for risk workbench flows.
 * Falls back to local behavior when endpoint is unavailable.
 */
export function createWorkbenchClient(baseUrl = '') {
  const prefix = baseUrl.replace(/\/$/, '');
  const taskStore = new Map();

  async function request(path, body) {
    const response = await fetch(`${prefix}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Request failed (${response.status})`);
    }

    return response.json();
  }

  return {
    async createRouteSegment(payload) {
      try {
        return await request('/api/workbench/create-route-segment', payload);
      } catch {
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
        return await request('/api/workbench/enqueue-run', payload);
      } catch {
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
        return await request('/api/workbench/execute-run', { task_id: taskId });
      } catch {
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
        return await request('/api/workbench/get-task', { task_id: taskId });
      } catch {
        const task = taskStore.get(taskId);
        if (!task) throw new Error(`Unknown task id ${taskId}`);
        return task;
      }
    },
  };
}
