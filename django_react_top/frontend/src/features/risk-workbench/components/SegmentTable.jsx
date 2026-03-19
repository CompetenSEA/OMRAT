import React, { useEffect, useState } from 'react';
import { Alert } from '../../../components/ui/alert';
import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../components/ui/table';

function parsePoint(value) {
  const parts = value.split(',').map((n) => Number(n.trim()));
  if (parts.length !== 2 || Number.isNaN(parts[0]) || Number.isNaN(parts[1])) {
    throw new Error('Point format must be "x,y" (example: 12.4,-3.2).');
  }
  return parts;
}

function formatPoint(point) {
  return `${Number(point[0]).toFixed(2)}, ${Number(point[1]).toFixed(2)}`;
}

export function SegmentTable({ state, dispatch, client, onError }) {
  const [draftRows, setDraftRows] = useState({});

  useEffect(() => {
    const next = {};
    state.segmentData.forEach((segment, idx) => {
      next[idx] = {
        start: formatPoint(segment.start_point),
        end: formatPoint(segment.end_point),
        width: String(segment.width_m),
      };
    });
    setDraftRows(next);
  }, [state.segmentData]);

  const updateRow = (idx, field, value) => {
    setDraftRows((prev) => ({ ...prev, [idx]: { ...(prev[idx] || {}), [field]: value } }));
  };

  const recalcRow = async (idx) => {
    try {
      const row = draftRows[idx];
      if (!row) return;
      const original = state.segmentData[idx];
      const updated = await client.createRouteSegment({
        start_point: parsePoint(row.start),
        end_point: parsePoint(row.end),
        segment_id: original.segment_id,
        route_id: original.route_id,
        width_m: Number(row.width),
        tangent_offset_m: Number(row.width) / 2,
      });

      const nextRows = [...state.segmentData];
      nextRows[idx] = updated;
      dispatch({ type: 'UPSERT_SEGMENTS', segmentData: nextRows });
      onError('');
    } catch (error) {
      onError(error.message);
    }
  };

  const removeRow = (idx) => {
    dispatch({ type: 'UPSERT_SEGMENTS', segmentData: state.segmentData.filter((_, i) => i !== idx) });
  };

  if (!state.segmentData.length) {
    return <Alert variant="warning">No segments yet. Add legs from the canvas or form below.</Alert>;
  }

  return (
    <div className="rounded-md border border-slate-200">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Label</TableHead>
            <TableHead>Start</TableHead>
            <TableHead>End</TableHead>
            <TableHead>Direction</TableHead>
            <TableHead>Width (m)</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {state.segmentData.map((segment, idx) => (
            <TableRow key={`${segment.label}-${idx}`}>
              <TableCell className="font-medium">{segment.label}</TableCell>
              <TableCell>
                <Input value={draftRows[idx]?.start || ''} onChange={(e) => updateRow(idx, 'start', e.target.value)} onBlur={() => recalcRow(idx)} />
              </TableCell>
              <TableCell>
                <Input value={draftRows[idx]?.end || ''} onChange={(e) => updateRow(idx, 'end', e.target.value)} onBlur={() => recalcRow(idx)} />
              </TableCell>
              <TableCell>
                <Badge variant="secondary">{segment.leg_direction}</Badge>
                <span className="ml-2 text-xs text-slate-500">{segment.bearing_deg}°</span>
              </TableCell>
              <TableCell>
                <Input value={draftRows[idx]?.width || ''} onChange={(e) => updateRow(idx, 'width', e.target.value)} onBlur={() => recalcRow(idx)} />
              </TableCell>
              <TableCell>
                <Button variant="ghost" onClick={() => removeRow(idx)}>Remove</Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
