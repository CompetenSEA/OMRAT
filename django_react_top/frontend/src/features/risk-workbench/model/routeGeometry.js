/**
 * Route editing helpers for standalone web map behavior.
 */

export function isValidPointPair(start, end) {
  const [sx, sy] = start;
  const [ex, ey] = end;
  const nearOrigin = ([x, y]) => x >= -1 && x <= 1 && y >= -1 && y <= 1;
  if (nearOrigin(start) || nearOrigin(end)) return false;
  return !(sx === ex && sy === ey);
}

export function calculateTangentLine(mid, start, end, offset) {
  const [mx, my] = mid;
  const [sx, sy] = start;
  const [ex, ey] = end;

  const dx = ex - sx;
  const dy = ey - sy;
  const length = Math.hypot(dx, dy);

  if (!length) {
    throw new Error('Start and end points cannot be identical');
  }

  const unitDx = dx / length;
  const unitDy = dy / length;
  const perpDx = -unitDy;
  const perpDy = unitDx;

  return {
    start: [mx - perpDx * offset, my - perpDy * offset],
    end: [mx + perpDx * offset, my + perpDy * offset],
  };
}

export function calculateBearing(start, end) {
  const [sx, sy] = start;
  const [ex, ey] = end;
  const dx = ex - sx;
  const dy = ey - sy;
  if (!dx && !dy) {
    throw new Error('Cannot compute bearing for identical points');
  }
  return (Math.atan2(dx, dy) * 180 / Math.PI + 360) % 360;
}

export function directionLabelFromBearing(bearingDeg) {
  const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
  const idx = Math.floor((bearingDeg + 22.5) / 45) % 8;
  return directions[idx];
}

export function buildCorridorPolygon(startPoint, endPoint, widthM) {
  const [sx, sy] = startPoint;
  const [ex, ey] = endPoint;
  const dx = ex - sx;
  const dy = ey - sy;
  const length = Math.hypot(dx, dy);

  if (!length) {
    throw new Error('Cannot build corridor for identical points');
  }

  const halfWidth = widthM / 2;
  const unitDx = dx / length;
  const unitDy = dy / length;
  const perpDx = -unitDy;
  const perpDy = unitDx;

  const sLeft = [sx + perpDx * halfWidth, sy + perpDy * halfWidth];
  const sRight = [sx - perpDx * halfWidth, sy - perpDy * halfWidth];
  const eRight = [ex - perpDx * halfWidth, ey - perpDy * halfWidth];
  const eLeft = [ex + perpDx * halfWidth, ey + perpDy * halfWidth];

  return [sLeft, sRight, eRight, eLeft, sLeft];
}

export function buildSegmentDraft({
  startPoint,
  endPoint,
  segmentId = 1,
  routeId = 1,
  widthM = 2500,
  tangentOffsetM = 2500,
}) {
  if (!isValidPointPair(startPoint, endPoint)) {
    throw new Error('Invalid route points. Both points must be non-origin and distinct.');
  }

  const mid = [(startPoint[0] + endPoint[0]) / 2, (startPoint[1] + endPoint[1]) / 2];
  const tangent = calculateTangentLine(mid, startPoint, endPoint, tangentOffsetM);
  const bearing = calculateBearing(startPoint, endPoint);

  return {
    segment_id: String(segmentId),
    route_id: String(routeId),
    label: `LEG_${segmentId}_${routeId}`,
    leg_direction: directionLabelFromBearing(bearing),
    bearing_deg: Number(bearing.toFixed(2)),
    coords: [startPoint, endPoint],
    width_m: widthM,
    start_point: startPoint,
    end_point: endPoint,
    tangent_line: tangent,
    corridor_polygon: buildCorridorPolygon(startPoint, endPoint, widthM),
  };
}
