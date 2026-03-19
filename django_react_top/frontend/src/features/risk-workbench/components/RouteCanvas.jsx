import React from 'react';
import { Label } from '../../../components/ui/label';

export function RouteCanvas({ previewStart, previewEnd, onCanvasPoint, snapToGrid, gridSize }) {
  const width = 560;
  const height = 240;

  const snap = (value) => {
    if (!snapToGrid) return value;
    return Math.round(value / gridSize) * gridSize;
  };

  const toDomain = (x, y) => [
    Number(snap((x / width) * 100).toFixed(2)),
    Number(snap(((height - y) / height) * 100).toFixed(2)),
  ];

  const handleClick = (event) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const clickX = event.clientX - bounds.left;
    const clickY = event.clientY - bounds.top;
    onCanvasPoint(toDomain(clickX, clickY));
  };

  const onKeyDown = (event) => {
    if (event.key !== 'Enter') return;
    onCanvasPoint(toDomain(width / 2, height / 2));
  };

  const toSvg = (point) => (point ? { cx: (point[0] / 100) * width, cy: height - (point[1] / 100) * height } : null);
  const startDot = toSvg(previewStart);
  const endDot = toSvg(previewEnd);

  return (
    <div>
      <Label>Route canvas (web map interactions)</Label>
      <svg
        role="button"
        tabIndex={0}
        aria-label="Click to add route points"
        onKeyDown={onKeyDown}
        onClick={handleClick}
        className="mt-1 h-[240px] w-full rounded-md border border-slate-200 bg-slate-50"
        viewBox={`0 0 ${width} ${height}`}
      >
        <rect x="0" y="0" width={width} height={height} fill="#f8fafc" />
        {startDot && <circle cx={startDot.cx} cy={startDot.cy} r="4" fill="#0f172a" />}
        {endDot && <circle cx={endDot.cx} cy={endDot.cy} r="4" fill="#f97316" />}
        {startDot && endDot && (
          <line x1={startDot.cx} y1={startDot.cy} x2={endDot.cx} y2={endDot.cy} stroke="#0f172a" strokeWidth="2" />
        )}
      </svg>
      <p className="mt-1 text-xs text-slate-500">
        Click once to set start and once to set end. Enter key adds a midpoint sample click for keyboard users.
      </p>
    </div>
  );
}
