import React, { useEffect, useMemo, useReducer, useState } from 'react';
import { Alert } from '../../../components/ui/alert';
import { Badge } from '../../../components/ui/badge';
import { Button } from '../../../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Progress } from '../../../components/ui/progress';
import { Separator } from '../../../components/ui/separator';
import { Switch } from '../../../components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs';
import { Textarea } from '../../../components/ui/textarea';
import { createWorkbenchClient } from '../api/workbenchClient';
import { RouteCanvas } from './RouteCanvas';
import { SegmentTable } from './SegmentTable';
import { computeBounds, objectToSvgPolygon, segmentToSvgPath } from '../model/mapPreview';
import { buildCanonicalPayload, initialWorkbenchState, workbenchReducer } from '../model/workbenchState';
import { useRunLifecycle } from '../hooks/useRunLifecycle';

const STORAGE_KEY = 'omrat-risk-workbench-draft-v2';

function parseJsonArray(value, name) {
  const parsed = JSON.parse(value);
  if (!Array.isArray(parsed)) throw new Error(`${name} must be a JSON array.`);
  return parsed;
}

function parsePoint(value) {
  const parts = value.split(',').map((n) => Number(n.trim()));
  if (parts.length !== 2 || Number.isNaN(parts[0]) || Number.isNaN(parts[1])) {
    throw new Error('Point format must be "x,y" (example: 12.4,-3.2).');
  }
  return parts;
}


function SummaryTiles({ state }) {
  const tiles = [
    { label: 'Segments', value: state.segmentData.length },
    { label: 'Traffic rows', value: state.trafficData.length },
    { label: 'Objects', value: state.objects.length },
    { label: 'Depths', value: state.depths.length },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {tiles.map((tile) => (
        <Card key={tile.label}>
          <CardContent className="p-3">
            <p className="text-xs text-slate-500">{tile.label}</p>
            <p className="text-2xl font-semibold text-slate-900">{tile.value}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}



function RouteEditor({ state, dispatch, onError, client }) {
  const [startPoint, setStartPoint] = useState('2,2');
  const [endPoint, setEndPoint] = useState('12,2');
  const [segmentId, setSegmentId] = useState(state.segmentData.length + 1);
  const [routeId, setRouteId] = useState(1);
  const [widthM, setWidthM] = useState(2500);
  const [tangentOffsetM, setTangentOffsetM] = useState(1250);
  const [canvasStartPoint, setCanvasStartPoint] = useState(null);
  const [chainMode, setChainMode] = useState(true);
  const [snapToGrid, setSnapToGrid] = useState(true);
  const [gridSize, setGridSize] = useState(2);

  const createDraft = async (fromPoint, toPoint) => {
    const draft = await client.createRouteSegment({
      start_point: fromPoint,
      end_point: toPoint,
      segment_id: segmentId,
      route_id: routeId,
      width_m: Number(widthM),
      tangent_offset_m: Number(tangentOffsetM),
    });

    dispatch({ type: 'UPSERT_SEGMENTS', segmentData: [...state.segmentData, draft] });
    setSegmentId((v) => Number(v) + 1);

    if (chainMode) {
      setStartPoint(toPoint.join(','));
      setCanvasStartPoint(toPoint);
    }
  };

  const addFromInputs = async () => {
    try {
      await createDraft(parsePoint(startPoint), parsePoint(endPoint));
      onError('');
    } catch (error) {
      onError(error.message);
    }
  };

  const addFromCanvas = async (point) => {
    if (!canvasStartPoint) {
      setCanvasStartPoint(point);
      if (!chainMode) setStartPoint(point.join(','));
      return;
    }

    try {
      await createDraft(canvasStartPoint, point);
      if (!chainMode) setCanvasStartPoint(null);
      onError('');
    } catch (error) {
      onError(error.message);
    }
  };

  const previewEndPoint = (() => {
    try {
      return parsePoint(endPoint);
    } catch {
      return null;
    }
  })();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Route editor</CardTitle>
        <CardDescription>
          Web-native leg drawing with map clicks, chained continuation, snapping, and inline segment re-editing.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-center gap-4 rounded-md border border-slate-200 p-3">
          <div className="flex items-center gap-2">
            <Switch checked={chainMode} onCheckedChange={setChainMode} />
            <Label>Chain mode</Label>
          </div>
          <div className="flex items-center gap-2">
            <Switch checked={snapToGrid} onCheckedChange={setSnapToGrid} />
            <Label>Snap to grid</Label>
          </div>
          <div className="flex items-center gap-2">
            <Label>Grid size</Label>
            <Input value={gridSize} onChange={(e) => setGridSize(Number(e.target.value) || 1)} className="w-20" />
          </div>
        </div>

        <RouteCanvas
          previewStart={canvasStartPoint}
          previewEnd={previewEndPoint}
          onCanvasPoint={addFromCanvas}
          snapToGrid={snapToGrid}
          gridSize={gridSize}
        />

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
          <div className="space-y-1">
            <Label htmlFor="start-point">Start point</Label>
            <Input id="start-point" value={startPoint} onChange={(e) => setStartPoint(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="end-point">End point</Label>
            <Input id="end-point" value={endPoint} onChange={(e) => setEndPoint(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="segment-id">Segment ID</Label>
            <Input id="segment-id" value={segmentId} onChange={(e) => setSegmentId(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="route-id">Route ID</Label>
            <Input id="route-id" value={routeId} onChange={(e) => setRouteId(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="width-m">Corridor width (m)</Label>
            <Input id="width-m" value={widthM} onChange={(e) => setWidthM(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="offset-m">Tangent offset (m)</Label>
            <Input id="offset-m" value={tangentOffsetM} onChange={(e) => setTangentOffsetM(e.target.value)} />
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button onClick={addFromInputs}>Add segment from inputs</Button>
          <Button variant="outline" onClick={() => dispatch({ type: 'UPSERT_SEGMENTS', segmentData: state.segmentData.slice(0, -1) })}>
            Undo last
          </Button>
          <Button variant="outline" onClick={() => dispatch({ type: 'UPSERT_SEGMENTS', segmentData: [] })}>
            Clear all
          </Button>
          <Button variant="outline" onClick={() => setCanvasStartPoint(null)}>Reset canvas start</Button>
        </div>

        <SegmentTable state={state} dispatch={dispatch} client={client} onError={onError} />
      </CardContent>
    </Card>
  );
}

function DataEditor({ dispatch, onError }) {
  const [trafficJson, setTrafficJson] = useState('[{"segment_id":"1","ship_category":"Cargo","annual_transits":12}]');
  const [depthsJson, setDepthsJson] = useState('[{"feature_id":"D1","depth_m":-15}]');
  const [objectsJson, setObjectsJson] = useState('[{"feature_id":"O1","object_type":"Platform","coords":[[4,-1],[6,-1],[6,1],[4,1]]}]');

  const applyData = (content, type, name) => {
    try {
      const rows = parseJsonArray(content, name);
      const key = type === 'UPSERT_TRAFFIC' ? 'trafficData' : type === 'UPSERT_DEPTHS' ? 'depths' : 'objects';
      dispatch({ type, [key]: rows });
      onError('');
    } catch (error) {
      onError(error.message);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Traffic, depths, and objects</CardTitle>
        <CardDescription>Paste JSON arrays to emulate API ingestion and layer sync behavior.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="space-y-2">
          <Label>Traffic rows JSON</Label>
          <Textarea value={trafficJson} onChange={(e) => setTrafficJson(e.target.value)} />
          <Button variant="secondary" onClick={() => applyData(trafficJson, 'UPSERT_TRAFFIC', 'Traffic rows')}>Apply traffic</Button>
        </div>
        <Separator />
        <div className="space-y-2">
          <Label>Depth rows JSON</Label>
          <Textarea value={depthsJson} onChange={(e) => setDepthsJson(e.target.value)} />
          <Button variant="secondary" onClick={() => applyData(depthsJson, 'UPSERT_DEPTHS', 'Depth rows')}>Apply depths</Button>
        </div>
        <Separator />
        <div className="space-y-2">
          <Label>Object rows JSON</Label>
          <Textarea value={objectsJson} onChange={(e) => setObjectsJson(e.target.value)} />
          <Button variant="secondary" onClick={() => applyData(objectsJson, 'UPSERT_OBJECTS', 'Object rows')}>Apply objects</Button>
        </div>
      </CardContent>
    </Card>
  );
}

function SettingsEditor({ state, dispatch }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Run settings</CardTitle>
        <CardDescription>Prepare model metadata before analysis.</CardDescription>
      </CardHeader>
      <CardContent className="grid grid-cols-1 gap-3 md:grid-cols-3">
        <div className="space-y-1">
          <Label>Model name</Label>
          <Input value={state.settings.model_name} onChange={(e) => dispatch({ type: 'UPDATE_SETTINGS', settings: { model_name: e.target.value } })} />
        </div>
        <div className="space-y-1">
          <Label>Report path</Label>
          <Input value={state.settings.report_path} onChange={(e) => dispatch({ type: 'UPDATE_SETTINGS', settings: { report_path: e.target.value } })} />
        </div>
        <div className="space-y-1">
          <Label>Causation version</Label>
          <Input value={state.settings.causation_version} onChange={(e) => dispatch({ type: 'UPDATE_SETTINGS', settings: { causation_version: e.target.value } })} />
        </div>
      </CardContent>
    </Card>
  );
}

function MapPreviewPanel({ state }) {
  const bounds = useMemo(() => computeBounds(state.segmentData, state.objects), [state.segmentData, state.objects]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Map preview</CardTitle>
        <CardDescription>Live corridor polygons, route centerlines, and object overlays.</CardDescription>
      </CardHeader>
      <CardContent>
        <svg viewBox={`${bounds.minX} ${-bounds.maxY} ${bounds.width} ${bounds.height}`} className="h-80 w-full rounded border border-slate-200 bg-slate-50">
          {state.segmentData.map((segment, index) => (
            <g key={`${segment.label}-${index}`}>
              {segment.corridor_polygon?.length > 3 && (
                <polygon points={segment.corridor_polygon.map(([x, y]) => `${x},${-y}`).join(' ')} fill="#93c5fd" opacity="0.35" />
              )}
              <path d={segmentToSvgPath(segment)} stroke="#0f172a" strokeWidth="0.5" fill="none" />
            </g>
          ))}
          {state.objects.map((objectRow, index) => (
            <polygon key={`${objectRow.feature_id}-${index}`} points={objectToSvgPolygon(objectRow)} fill="#fb7185" opacity="0.35" />
          ))}
        </svg>
      </CardContent>
    </Card>
  );
}

function RunPanel({ state, dispatch, client }) {
  const { running, startRun } = useRunLifecycle(client, dispatch);
  const [readiness, setReadiness] = useState(null);
  const [checkingReadiness, setCheckingReadiness] = useState(false);

  const checkReadiness = async () => {
    setCheckingReadiness(true);
    try {
      const payload = buildCanonicalPayload(state);
      const result = await client.assessProjectReadiness(payload);
      setReadiness(result);
      return result;
    } finally {
      setCheckingReadiness(false);
    }
  };

  const onRun = async () => {
    const readinessResult = await checkReadiness();
    if (!readinessResult.ready_for_run) {
      return;
    }
    const payload = buildCanonicalPayload(state);
    await startRun(payload);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Run analysis</CardTitle>
        <CardDescription>Task-like progress UX mirrors backend enqueue/execute/poll behavior with readiness gating.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={checkReadiness} disabled={running || checkingReadiness}>
            {checkingReadiness ? 'Checking...' : 'Check readiness'}
          </Button>
          <Button onClick={onRun} disabled={running || checkingReadiness || !state.segmentData.length || (readiness && !readiness.ready_for_run)}>
            {running ? 'Running...' : 'Start analysis'}
          </Button>
        </div>
        {!state.segmentData.length && <Alert variant="warning">Add at least one route segment before running.</Alert>}
        {readiness && (
          <div className="rounded-md border border-slate-200 p-3 space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant={readiness.ready_for_run ? 'success' : 'warning'}>
                {readiness.ready_for_run ? 'Ready for run' : 'Action needed'}
              </Badge>
              <span className="text-xs text-slate-500">
                {readiness.counts.blocking_issues} blocking / {readiness.counts.warnings} warnings
              </span>
            </div>
            {readiness.issues.length > 0 && (
              <ul className="list-disc pl-5 text-sm text-slate-700 space-y-1">
                {readiness.issues.map((issue) => (
                  <li key={issue.id}>
                    <span className="font-medium">{issue.area}:</span> {issue.message}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
        {state.runTask && (
          <div className="rounded-md border border-slate-200 p-3">
            <div className="mb-2 flex items-center justify-between">
              <Badge variant={state.runTask.state === 'completed' ? 'success' : 'secondary'}>{state.runTask.state}</Badge>
              <span className="text-xs text-slate-500">{state.runTask.message}</span>
            </div>
            <Progress value={state.runTask.progress} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ResultsPanel({ state, client, onError }) {
  const [recentRuns, setRecentRuns] = useState([]);
  const [loadingRuns, setLoadingRuns] = useState(false);

  const refreshRuns = async () => {
    setLoadingRuns(true);
    try {
      const response = await client.listRuns(10);
      setRecentRuns(response.runs || []);
      onError('');
    } catch (error) {
      onError(error.message);
    } finally {
      setLoadingRuns(false);
    }
  };

  if (!state.runSummary) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Results</CardTitle>
          <CardDescription>No run completed yet.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Button variant="outline" onClick={refreshRuns} disabled={loadingRuns}>
            {loadingRuns ? 'Refreshing…' : 'Load recent runs'}
          </Button>
          {recentRuns.length > 0 && (
            <div className="space-y-2 rounded-md border border-slate-200 p-3">
              <p className="text-sm font-medium text-slate-900">Recent completed runs</p>
              <ul className="space-y-1 text-xs text-slate-600">
                {recentRuns.map((run) => (
                  <li key={run.task_id}>
                    <span className="font-medium">{run.task_id}</span> · {run.status} · {run.report_path || 'no report path'}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Results</CardTitle>
        <CardDescription>Snapshot of latest run summary and report metadata.</CardDescription>
      </CardHeader>
      <CardContent>
        <pre className="overflow-auto rounded-md bg-slate-950 p-4 text-xs text-slate-100">{JSON.stringify(state.runSummary, null, 2)}</pre>
        <div className="mt-4 space-y-3">
          <Button variant="outline" onClick={refreshRuns} disabled={loadingRuns}>
            {loadingRuns ? 'Refreshing…' : 'Refresh recent runs'}
          </Button>
          {recentRuns.length > 0 && (
            <div className="space-y-2 rounded-md border border-slate-200 p-3">
              <p className="text-sm font-medium text-slate-900">Recent completed runs</p>
              <ul className="space-y-1 text-xs text-slate-600">
                {recentRuns.map((run) => (
                  <li key={run.task_id}>
                    <span className="font-medium">{run.task_id}</span> · {run.status} · {run.report_path || 'no report path'}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function RiskWorkbench() {
  const [state, dispatch] = useReducer(workbenchReducer, initialWorkbenchState);
  const [errorMessage, setErrorMessage] = useState('');
  const client = useMemo(() => createWorkbenchClient(), []);

  useEffect(() => {
    try {
      const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
      if (!parsed) return;
      if (Array.isArray(parsed.segmentData)) dispatch({ type: 'UPSERT_SEGMENTS', segmentData: parsed.segmentData });
      if (Array.isArray(parsed.trafficData)) dispatch({ type: 'UPSERT_TRAFFIC', trafficData: parsed.trafficData });
      if (Array.isArray(parsed.depths)) dispatch({ type: 'UPSERT_DEPTHS', depths: parsed.depths });
      if (Array.isArray(parsed.objects)) dispatch({ type: 'UPSERT_OBJECTS', objects: parsed.objects });
      if (parsed.settings) dispatch({ type: 'UPDATE_SETTINGS', settings: parsed.settings });
    } catch {
      // ignore invalid state
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        segmentData: state.segmentData,
        trafficData: state.trafficData,
        depths: state.depths,
        objects: state.objects,
        settings: state.settings,
      }),
    );
  }, [state.segmentData, state.trafficData, state.depths, state.objects, state.settings]);

  return (
    <div className="mx-auto max-w-7xl space-y-4 p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">OMRAT Risk Workbench</h1>
          <p className="text-sm text-slate-500">Standalone React + Django workflow with shadcn/ui patterns.</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary">{state.activeTab}</Badge>
          <Button variant="outline" onClick={() => localStorage.removeItem(STORAGE_KEY)}>Clear saved draft</Button>
        </div>
      </div>

      <SummaryTiles state={state} />
      {errorMessage && <Alert variant="danger">{errorMessage}</Alert>}

      <Tabs value={state.activeTab} onValueChange={(tab) => dispatch({ type: 'SET_TAB', tab })}>
        <TabsList className="w-full flex-wrap gap-1 md:w-auto">
          <TabsTrigger tabValue="routes">Routes</TabsTrigger>
          <TabsTrigger tabValue="traffic">Data</TabsTrigger>
          <TabsTrigger tabValue="map">Map</TabsTrigger>
          <TabsTrigger tabValue="run-analysis">Run</TabsTrigger>
          <TabsTrigger tabValue="results">Results</TabsTrigger>
        </TabsList>

        <TabsContent tabValue="routes" className="space-y-4">
          <RouteEditor state={state} dispatch={dispatch} onError={setErrorMessage} client={client} />
          <SettingsEditor state={state} dispatch={dispatch} />
        </TabsContent>
        <TabsContent tabValue="traffic">
          <DataEditor dispatch={dispatch} onError={setErrorMessage} />
        </TabsContent>
        <TabsContent tabValue="map">
          <MapPreviewPanel state={state} />
        </TabsContent>
        <TabsContent tabValue="run-analysis">
          <RunPanel state={state} dispatch={dispatch} client={client} />
        </TabsContent>
        <TabsContent tabValue="results">
          <ResultsPanel state={state} client={client} onError={setErrorMessage} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
