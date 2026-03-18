/**
 * Frontend state reducer that mimics QGIS plugin tab/workflow transitions
 * without relying on QGIS APIs.
 */

export const initialWorkbenchState = {
  activeTab: 'routes',
  segmentData: [],
  trafficData: [],
  depths: [],
  objects: [],
  settings: {
    model_name: 'omrat-model',
    report_path: '',
    causation_version: 'v1',
  },
  runTask: null,
  runSummary: null,
};

export function workbenchReducer(state, action) {
  switch (action.type) {
    case 'SET_TAB':
      return { ...state, activeTab: action.tab };
    case 'UPSERT_SEGMENTS':
      return { ...state, segmentData: action.segmentData };
    case 'UPSERT_TRAFFIC':
      return { ...state, trafficData: action.trafficData };
    case 'UPSERT_DEPTHS':
      return { ...state, depths: action.depths };
    case 'UPSERT_OBJECTS':
      return { ...state, objects: action.objects };
    case 'UPDATE_SETTINGS':
      return { ...state, settings: { ...state.settings, ...action.settings } };
    case 'RUN_QUEUED':
      return { ...state, runTask: action.task, runSummary: null, activeTab: 'run-analysis' };
    case 'RUN_PROGRESS':
      return { ...state, runTask: action.task };
    case 'RUN_COMPLETED':
      return { ...state, runTask: action.task, runSummary: action.task.result, activeTab: 'results' };
    default:
      return state;
  }
}

export function buildCanonicalPayload(state) {
  return {
    segment_data: state.segmentData,
    traffic_data: state.trafficData,
    depths: state.depths,
    objects: state.objects,
    settings: state.settings,
  };
}
