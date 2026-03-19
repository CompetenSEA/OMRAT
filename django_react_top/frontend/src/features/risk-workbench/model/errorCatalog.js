/**
 * Localizable user-facing fallback messages keyed by backend message_id.
 * Current production locales: EN/GB and SE/SWE.
 */

export const WORKBENCH_ERROR_CATALOG = {
  'en-GB': {
    WB_ACTION_NOT_FOUND: 'Requested workbench action was not found.',
    WB_HTTP_METHOD_NOT_ALLOWED: 'Only POST requests are supported for this endpoint.',
    WB_HTTP_INVALID_JSON: 'Request body is not valid JSON.',
    WB_SYNC_LAYERS_VALIDATION_ERROR: 'Layer sync payload is incomplete. Include segments, depths, and objects.',
    WB_START_ANALYSIS_VALIDATION_ERROR: 'Run payload is incomplete. Add settings, routes, traffic, depths, and objects.',
    WB_PREVIEW_CORRIDOR_OVERLAPS_VALIDATION_ERROR: 'Overlap preview requires both segment and object geometry.',
    WB_CREATE_ROUTE_SEGMENT_VALIDATION_ERROR: 'Route segment creation requires both start and end points.',
  },
  'sv-SE': {
    WB_ACTION_NOT_FOUND: 'Den begärda Workbench-åtgärden kunde inte hittas.',
    WB_HTTP_METHOD_NOT_ALLOWED: 'Endast POST-begäranden stöds för denna endpoint.',
    WB_HTTP_INVALID_JSON: 'Begärans innehåll är inte giltig JSON.',
    WB_SYNC_LAYERS_VALIDATION_ERROR: 'Lagersynkronisering saknar data. Inkludera segment, djup och objekt.',
    WB_START_ANALYSIS_VALIDATION_ERROR: 'Körningsdata är ofullständiga. Lägg till inställningar, rutter, trafik, djup och objekt.',
    WB_PREVIEW_CORRIDOR_OVERLAPS_VALIDATION_ERROR: 'Förhandsvisning av överlapp kräver både segment- och objektgeometri.',
    WB_CREATE_ROUTE_SEGMENT_VALIDATION_ERROR: 'Skapande av ruttsegment kräver både start- och slutpunkt.',
  },
};

export function resolveWorkbenchErrorMessage(errorPayload, locale = 'en-GB') {
  if (!errorPayload || typeof errorPayload !== 'object') return 'Workbench request failed';
  const localeCatalog = WORKBENCH_ERROR_CATALOG[locale] || WORKBENCH_ERROR_CATALOG['en-GB'];
  const mapped = localeCatalog[errorPayload.message_id || ''];
  if (mapped) return mapped;
  return errorPayload.user_message || errorPayload.message || 'Workbench request failed';
}
