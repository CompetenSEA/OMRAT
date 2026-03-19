/**
 * Frontend state reducer aligned to legacy plugin tab/workflow transitions
 * with no desktop GIS dependency.
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
  osmContext: {
    land_features: [
      {
        type: 'Feature',
        geometry: {
          type: 'Polygon',
          coordinates: [[[4.4, 57.9], [4.8, 57.9], [4.8, 58.2], [4.4, 58.2], [4.4, 57.9]]],
        },
        properties: { natural: 'coastline', name: 'sample-land' },
      },
    ],
    fixed_object_features: [
      {
        type: 'Feature',
        geometry: {
          type: 'Polygon',
          coordinates: [[[4.95, 57.95], [5.0, 57.95], [5.0, 58.0], [4.95, 58.0], [4.95, 57.95]]],
        },
        properties: { man_made: 'platform', name: 'sample-fixed-object' },
      },
    ],
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
    case 'UPDATE_OSM_CONTEXT':
      return { ...state, osmContext: { ...state.osmContext, ...action.osmContext } };
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
    osm_context: state.osmContext,
  };
}
