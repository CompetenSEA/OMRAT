/**
 * Geometry helpers for frontend map preview rendering.
 * Produces SVG-friendly structures from canonical payload rows.
 */

export function segmentToSvgPath(segment) {
  const coords = segment.coords || [];
  if (coords.length < 2) return '';
  return coords
    .map(([x, y], idx) => `${idx === 0 ? 'M' : 'L'} ${x} ${-y}`)
    .join(' ');
}

export function objectToSvgPolygon(objectRow) {
  const coords = objectRow.coords || [];
  if (coords.length < 3) return '';
  return coords.map(([x, y]) => `${x},${-y}`).join(' ');
}

export function computeBounds(segmentData = [], objects = []) {
  const points = [];
  segmentData.forEach((s) => (s.coords || []).forEach((p) => points.push(p)));
  objects.forEach((o) => (o.coords || []).forEach((p) => points.push(p)));

  if (!points.length) {
    return { minX: 0, minY: 0, maxX: 1, maxY: 1, width: 1, height: 1 };
  }

  const xs = points.map((p) => p[0]);
  const ys = points.map((p) => p[1]);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);

  return {
    minX,
    minY,
    maxX,
    maxY,
    width: maxX - minX || 1,
    height: maxY - minY || 1,
  };
}
